# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Life Optimization Environment Client."""

from typing import Dict, Optional

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

try:
    from .models import LifeOptimizationAction, LifeOptimizationObservation
except ImportError:
    from models import LifeOptimizationAction, LifeOptimizationObservation


class FitrlEnv(EnvClient[LifeOptimizationAction, LifeOptimizationObservation, State]):
    """
    Client for the Life Optimization Environment.

    Maintains a persistent WebSocket connection for efficient multi-step rollouts.

    Example:
        >>> with FitrlEnv(base_url="http://localhost:8000") as env:
        ...     result = env.reset()
        ...     result = env.step(LifeOptimizationAction(
        ...         fitness_action={"workout_type": "strength", "intensity": "medium", "duration": 30}
        ...     ))
        ...     print(result.observation.energy, result.reward)
    """

    def _step_payload(self, action: LifeOptimizationAction) -> Dict:
        payload = {}
        if action.fitness_action is not None:
            payload["fitness_action"] = action.fitness_action.model_dump()
        if action.work_action is not None:
            payload["work_action"] = action.work_action.model_dump()
        return payload

    def _parse_result(self, payload: Dict) -> StepResult[LifeOptimizationObservation]:
        obs_data = payload.get("observation", {})
        observation = LifeOptimizationObservation(
            day=obs_data.get("day", 1),
            time_of_day=obs_data.get("time_of_day", "morning"),
            energy=obs_data.get("energy", 0.8),
            fatigue=obs_data.get("fatigue", 0.1),
            focus=obs_data.get("focus", 0.7),
            soreness=obs_data.get("soreness", 0.0),
            sleep_hours=obs_data.get("sleep_hours", 7.0),
            last_workout=obs_data.get("last_workout"),
            pending_tasks=obs_data.get("pending_tasks", 3),
            consistency=obs_data.get("consistency", 0.5),
            productivity=obs_data.get("productivity", 0.5),
            fitness_score=obs_data.get("fitness_score", 0.5),
            done=payload.get("done", False),
            reward=payload.get("reward"),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
