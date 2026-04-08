# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Life Optimization Environment Implementation.

A 7-day life optimization environment with three daily phases:
  morning  → fitness action
  afternoon → work action
  evening  → automatic recovery (no action needed)
"""

from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import (
        LifeOptimizationAction, LifeOptimizationObservation,
        FitnessAction, WorkAction,
        WorkoutType, IntensityLevel, TaskType, EffortLevel,
    )
except ImportError:
    from models import (
        LifeOptimizationAction, LifeOptimizationObservation,
        FitnessAction, WorkAction,
        WorkoutType, IntensityLevel, TaskType, EffortLevel,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _duration_factor(minutes: int, cap: int = 60) -> float:
    return min(max(minutes, 0), cap) / cap


_INTENSITY_DELTA = {
    IntensityLevel.low: 0.1,
    IntensityLevel.medium: 0.2,
    IntensityLevel.high: 0.3,
}

_PHASE_ORDER = ["morning", "afternoon", "evening"]


def _next_phase(phase: str) -> str:
    return _PHASE_ORDER[(_PHASE_ORDER.index(phase) + 1) % 3]


# ---------------------------------------------------------------------------
# State dataclass (plain dict-based to avoid circular imports)
# ---------------------------------------------------------------------------

def _default_state() -> dict:
    return dict(
        day=1, time_of_day="morning",
        energy=0.8, fatigue=0.1, focus=0.7, soreness=0.0,
        sleep_hours=7.0, last_workout=None, pending_tasks=5,
        consistency=0.5, productivity=0.5, fitness_score=0.5,
    )


# ---------------------------------------------------------------------------
# Transition functions (mirrors simulator.py)
# ---------------------------------------------------------------------------

def _apply_fitness(s: dict, action: LifeOptimizationAction) -> dict:
    fa = action.fitness_action
    d = _INTENSITY_DELTA[fa.intensity]
    duration_factor = _duration_factor(fa.duration)
    if fa.workout_type == WorkoutType.strength:
        s["fitness_score"] = _clamp(s["fitness_score"] + d * (0.7 + 0.3 * duration_factor))
        s["fatigue"] = _clamp(s["fatigue"] + d * (0.35 + 0.45 * duration_factor))
        s["energy"] = _clamp(s["energy"] - d * (0.2 + 0.25 * duration_factor))
        s["soreness"] = _clamp(s["soreness"] + d * 0.45)
        s["consistency"] = _clamp(s["consistency"] + 0.05)
        s["focus"] = _clamp(s["focus"] + 0.02)
    elif fa.workout_type == WorkoutType.cardio:
        s["fitness_score"] = _clamp(s["fitness_score"] + d * (0.55 + 0.25 * duration_factor))
        s["fatigue"] = _clamp(s["fatigue"] + d * (0.25 + 0.25 * duration_factor))
        s["energy"] = _clamp(s["energy"] - d * (0.15 + 0.2 * duration_factor))
        s["focus"] = _clamp(s["focus"] + 0.04)
        s["consistency"] = _clamp(s["consistency"] + 0.04)
    elif fa.workout_type == WorkoutType.yoga:
        s["fatigue"] = _clamp(s["fatigue"] - (0.08 + 0.06 * duration_factor))
        s["focus"] = _clamp(s["focus"] + (0.08 + 0.05 * duration_factor))
        s["soreness"] = _clamp(s["soreness"] - (0.04 + 0.05 * duration_factor))
        s["energy"] = _clamp(s["energy"] + 0.03)
        s["consistency"] = _clamp(s["consistency"] + 0.03)
    else:  # rest
        s["energy"] = _clamp(s["energy"] + 0.08)
        s["fatigue"] = _clamp(s["fatigue"] - 0.04)
        if s["fatigue"] < 0.45:
            s["consistency"] = _clamp(s["consistency"] - 0.03)
    s["last_workout"] = fa.workout_type.value
    return s


def _apply_work(s: dict, action: LifeOptimizationAction) -> dict:
    wa = action.work_action
    effort_scale = {
        EffortLevel.low: 0.8,
        EffortLevel.medium: 1.0,
        EffortLevel.high: 1.2,
    }[wa.effort_level]
    if wa.task_type == TaskType.deep_work:
        if s["energy"] >= 0.7 and s["focus"] >= 0.6:
            s["productivity"] = _clamp(s["productivity"] + 0.24 * effort_scale)
            s["pending_tasks"] = max(0, s["pending_tasks"] - (2 if wa.effort_level != EffortLevel.low else 1))
        else:
            s["productivity"] = _clamp(s["productivity"] + 0.12 * effort_scale)
            s["pending_tasks"] = max(0, s["pending_tasks"] - 1)
        s["energy"] = _clamp(s["energy"] - 0.16 * effort_scale)
        s["focus"] = _clamp(s["focus"] - 0.08 * effort_scale)
        s["fatigue"] = _clamp(s["fatigue"] + 0.05 * effort_scale)
        s["consistency"] = _clamp(s["consistency"] + 0.04)
    elif wa.task_type in (TaskType.email, TaskType.scheduling):
        base_gain = 0.08 if wa.task_type == TaskType.email else 0.10
        s["productivity"] = _clamp(s["productivity"] + base_gain * effort_scale)
        s["pending_tasks"] = max(0, s["pending_tasks"] - 1)
        s["energy"] = _clamp(s["energy"] - 0.05 * effort_scale)
        s["consistency"] = _clamp(s["consistency"] + 0.02)
    elif wa.task_type == TaskType.support:
        s["productivity"] = _clamp(s["productivity"] + 0.14 * effort_scale)
        s["pending_tasks"] = max(0, s["pending_tasks"] - 1)
        s["energy"] = _clamp(s["energy"] - 0.08 * effort_scale)
        s["fatigue"] = _clamp(s["fatigue"] + 0.03 * effort_scale)
        s["consistency"] = _clamp(s["consistency"] + 0.03)
    else:  # rest
        s["energy"] = _clamp(s["energy"] + 0.05)
        s["focus"] = _clamp(s["focus"] + 0.05)
        if s["pending_tasks"] > 1:
            s["consistency"] = _clamp(s["consistency"] - 0.02)
    return s


def _apply_recovery(s: dict) -> dict:
    sleep_bonus = 0.5 if s["fatigue"] > 0.6 else 0.0
    backlog_penalty = 0.4 if s["pending_tasks"] > 4 else 0.0
    s["sleep_hours"] = max(5.5, min(8.5, 7.0 + sleep_bonus - backlog_penalty))
    s["energy"] = _clamp(0.5 + s["sleep_hours"] / 10.0 - s["fatigue"] * 0.15)
    s["fatigue"] = _clamp(s["fatigue"] - (0.2 + s["sleep_hours"] * 0.04))
    s["soreness"] = _clamp(s["soreness"] - 0.12)
    s["focus"] = _clamp(s["focus"] + 0.08)
    s["consistency"] = _clamp(s["consistency"] - 0.01 * min(s["pending_tasks"], 4))
    return s


def _compute_reward(prev: dict, nxt: dict) -> float:
    fitness_gain = max(0.0, nxt["fitness_score"] - prev["fitness_score"])
    task_progress = max(0, prev["pending_tasks"] - nxt["pending_tasks"]) / 2.0
    recovery_gain = max(0.0, prev["fatigue"] - nxt["fatigue"])
    backlog_penalty = nxt["pending_tasks"] / 10.0
    return (
        0.30 * nxt["productivity"]
        + 0.20 * fitness_gain
        + 0.20 * task_progress
        + 0.15 * nxt["consistency"]
        + 0.10 * recovery_gain
        - 0.15 * nxt["fatigue"]
        - 0.05 * backlog_penalty
    )


def _obs_from_state(s: dict) -> LifeOptimizationObservation:
    return LifeOptimizationObservation(**{k: v for k, v in s.items()})


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class FitrlEnvironment(Environment):
    """Life Optimization environment — 7-day episode, 3 phases per day."""

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    MAX_DAYS: int = 7

    def __init__(self):
        self._openenv_state = State(episode_id=str(uuid4()), step_count=0)
        self._sim: dict = _default_state()
        self._done: bool = False

    def reset(self) -> LifeOptimizationObservation:
        self._openenv_state = State(episode_id=str(uuid4()), step_count=0)
        self._sim = _default_state()
        self._done = False
        return _obs_from_state(self._sim)

    def step(self, action: LifeOptimizationAction) -> LifeOptimizationObservation:
        self._openenv_state.step_count += 1
        prev = dict(self._sim)
        phase = self._sim["time_of_day"]

        if phase == "morning":
            if action.fitness_action is None:
                action = LifeOptimizationAction(
                    fitness_action=FitnessAction(
                        workout_type=WorkoutType.rest,
                        intensity=IntensityLevel.low,
                        duration=0,
                    )
                )
            self._sim = _apply_fitness(dict(self._sim), action)
        elif phase == "afternoon":
            if action.work_action is None:
                action = LifeOptimizationAction(
                    work_action=WorkAction(
                        task_type=TaskType.rest,
                        effort_level=EffortLevel.low,
                    )
                )
            self._sim = _apply_work(dict(self._sim), action)
        else:  # evening
            self._sim = _apply_recovery(dict(self._sim))

        reward = _compute_reward(prev, self._sim)

        # Advance phase / day
        next_phase = _next_phase(phase)
        done = prev["day"] >= self.MAX_DAYS and phase == "evening"
        if phase == "evening":
            self._sim["day"] += 1
            if not done:
                new_tasks = 1
                if self._sim["productivity"] < 0.65:
                    new_tasks += 1
                self._sim["pending_tasks"] = min(self._sim["pending_tasks"] + new_tasks, 10)
        self._sim["time_of_day"] = next_phase

        self._done = done

        obs = _obs_from_state(self._sim)
        obs.reward = reward
        obs.done = done
        return obs

    @property
    def state(self) -> State:
        return self._openenv_state
