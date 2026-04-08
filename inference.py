"""
inference.py — LLM-based inference script for the Life Optimization Environment.

STDOUT FORMAT (mandatory):
  [START] task=<task_name> env=<benchmark> model=<model_name>
  [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
  [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>

Environment variables:
  OPENAI_API_KEY       Preferred OpenAI API key
  API_KEY              Generic provider API key
  HF_TOKEN             Backward-compatible alias for API_KEY
  API_BASE_URL         LLM API endpoint
  MODEL_NAME           Model identifier
  POLICY_MODE          openai | baseline (default: openai when a key is set, else baseline)
  LOCAL_IMAGE_NAME     Docker image name (if using from_docker_image)
  ENV_BASE_URL         Running env server URL (default: http://localhost:8000)
"""

import asyncio
import json
import os
import textwrap
from dataclasses import dataclass
from types import SimpleNamespace
from typing import List, Optional

from openai import OpenAI

from client import FitrlEnv
from models import (
    LifeOptimizationAction,
    FitnessAction,
    WorkAction,
    WorkoutType,
    IntensityLevel,
    TaskType,
    EffortLevel,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_HF_BASE_URL = "https://router.huggingface.co/v1"
DEFAULT_HF_MODEL = "Qwen/Qwen2.5-72B-Instruct"


def _get_api_key() -> Optional[str]:
    return os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY") or os.getenv("HF_TOKEN")


def _get_api_base_url() -> str:
    explicit = os.getenv("API_BASE_URL")
    if explicit:
        return explicit
    if os.getenv("OPENAI_API_KEY"):
        return DEFAULT_OPENAI_BASE_URL
    return DEFAULT_HF_BASE_URL


def _get_model_name(api_base_url: str) -> str:
    explicit = os.getenv("MODEL_NAME")
    if explicit:
        return explicit
    if api_base_url.rstrip("/") == DEFAULT_OPENAI_BASE_URL:
        return DEFAULT_OPENAI_MODEL
    return DEFAULT_HF_MODEL


def _get_policy_mode(api_key: Optional[str]) -> str:
    explicit = (os.getenv("POLICY_MODE") or "").strip().lower()
    if explicit:
        return explicit
    return "openai" if api_key else "baseline"


IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME") or os.getenv("IMAGE_NAME")
API_KEY = _get_api_key()
API_BASE_URL = _get_api_base_url()
MODEL_NAME = _get_model_name(API_BASE_URL)
POLICY_MODE = _get_policy_mode(API_KEY)
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000")
USE_LOCAL_ENV = os.getenv("USE_LOCAL_ENV", "").strip().lower() in {"1", "true", "yes"} or ENV_BASE_URL == "local"
BENCHMARK = "life-optimization"

MAX_STEPS = 21           # 7 days × 3 phases
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
MAX_TOKENS = 200
SUCCESS_SCORE_THRESHOLD = 0.5


@dataclass(frozen=True)
class TaskSpec:
    name: str
    difficulty: str
    objective: str
    rubric: str
    real_world_outcome: str


@dataclass
class EpisodeResult:
    steps_taken: int
    rewards: List[float]
    score: float
    success: bool


TASK_SPECS = [
    TaskSpec(
        name="fitness-progression",
        difficulty="easy",
        objective="Increase long-term fitness while keeping fatigue under control.",
        rubric="Favor sustainable training volume, recovery when needed, and steady fitness gains.",
        real_world_outcome="Produce a recovery-safe workout plan for a busy knowledge worker.",
    ),
    TaskSpec(
        name="work-allocation",
        difficulty="medium",
        objective="Maximize productive work output without fully draining energy.",
        rubric="Preserve enough energy for repeated deep-work sessions and avoid unnecessary fatigue spikes.",
        real_world_outcome="Sequence work blocks so important tasks are completed without burnout.",
    ),
    TaskSpec(
        name="life-optimization",
        difficulty="hard",
        objective="Balance fitness, productivity, and recovery across the full week.",
        rubric="Trade off training and work so both fitness and productivity finish strong.",
        real_world_outcome="Plan a realistic week that keeps work throughput and personal recovery aligned.",
    ),
]
TASK_SPEC_BY_NAME = {task.name: task for task in TASK_SPECS}

SYSTEM_PROMPT = textwrap.dedent("""
    You are a life optimization agent managing a 7-day schedule.
    Each day has three phases: morning (fitness), afternoon (work), evening (auto-recovery).
    Your goal is to maximize productivity and fitness while managing fatigue.
    Respond with ONLY valid JSON — no explanation, no markdown.
""").strip()


class LocalEnvAdapter:
    """Async wrapper around the in-process environment for reproducible local runs."""

    def __init__(self):
        from server.fitrl_environment import FitrlEnvironment

        self._env = FitrlEnvironment()

    async def reset(self):
        observation = self._env.reset()
        return SimpleNamespace(
            observation=observation,
            reward=getattr(observation, "reward", 0.0),
            done=getattr(observation, "done", False),
        )

    async def step(self, action: LifeOptimizationAction):
        observation = self._env.step(action)
        return SimpleNamespace(
            observation=observation,
            reward=getattr(observation, "reward", 0.0),
            done=getattr(observation, "done", False),
        )

    async def close(self):
        return None

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    success_val = str(success).lower()
    print(f"[END] success={success_val} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)


def _strip_metadata(value):
    if isinstance(value, dict):
        return {k: _strip_metadata(v) for k, v in value.items() if k != "metadata"}
    if isinstance(value, list):
        return [_strip_metadata(item) for item in value]
    return value


def _action_to_log_string(action: LifeOptimizationAction) -> str:
    payload = _strip_metadata(action.model_dump(exclude_none=True))
    return json.dumps(payload, separators=(",", ":"))

# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def build_prompt(obs: dict, step: int, task_name: str) -> str:
    task = TASK_SPEC_BY_NAME[task_name]
    time_of_day = obs.get("time_of_day", "morning")
    state_json = json.dumps(obs, indent=2)

    if time_of_day == "morning":
        schema = ('{"fitness_action": {"workout_type": "<strength|cardio|yoga|rest>", '
                  '"intensity": "<low|medium|high>", "duration": <0-120>}}')
        hint = "Choose a morning fitness action."
    elif time_of_day == "afternoon":
        schema = ('{"work_action": {"task_type": "<email|deep_work|support|scheduling|rest>", '
                  '"effort_level": "<low|medium|high>"}}')
        hint = "Choose an afternoon work action."
    else:
        schema = "{}"
        hint = "Evening recovery — no action needed, return empty JSON {}."

    return (
        f"You are solving task '{task.name}'. Step {step}.\n"
        f"Difficulty: {task.difficulty}\n"
        f"Objective: {task.objective}\n"
        f"Rubric: {task.rubric}\n"
        f"Real-world outcome: {task.real_world_outcome}\n\n"
        f"Current state:\n```json\n{state_json}\n```\n\n"
        f"{hint}\n\nRespond with ONLY valid JSON:\n{schema}"
    )

# ---------------------------------------------------------------------------
# Action parsing + baseline fallback
# ---------------------------------------------------------------------------

def _baseline_action(obs: dict, task_name: str) -> LifeOptimizationAction:
    """Rule-based fallback tuned for each task rubric."""
    time_of_day = obs.get("time_of_day", "morning")
    day = obs.get("day", 1)
    energy = obs.get("energy", 0.8)
    fatigue = obs.get("fatigue", 0.1)
    focus = obs.get("focus", 0.7)

    if time_of_day == "morning":
        if task_name == "fitness-progression":
            if fatigue > 0.7:
                fa = FitnessAction(workout_type=WorkoutType.rest, intensity=IntensityLevel.low, duration=0)
            elif fatigue > 0.5:
                fa = FitnessAction(workout_type=WorkoutType.yoga, intensity=IntensityLevel.low, duration=25)
            elif day in (1, 3, 5):
                fa = FitnessAction(workout_type=WorkoutType.strength, intensity=IntensityLevel.medium, duration=35)
            elif day in (2, 4):
                fa = FitnessAction(workout_type=WorkoutType.cardio, intensity=IntensityLevel.medium, duration=30)
            else:
                fa = FitnessAction(workout_type=WorkoutType.yoga, intensity=IntensityLevel.low, duration=20)
        elif task_name == "work-allocation":
            if fatigue > 0.65:
                fa = FitnessAction(workout_type=WorkoutType.yoga, intensity=IntensityLevel.low, duration=20)
            elif energy > 0.75 and day in (2, 5):
                fa = FitnessAction(workout_type=WorkoutType.cardio, intensity=IntensityLevel.low, duration=20)
            else:
                fa = FitnessAction(workout_type=WorkoutType.rest, intensity=IntensityLevel.low, duration=0)
        elif energy < 0.4 or fatigue > 0.7:
            fa = FitnessAction(workout_type=WorkoutType.rest, intensity=IntensityLevel.low, duration=0)
        elif fatigue > 0.5:
            fa = FitnessAction(workout_type=WorkoutType.cardio, intensity=IntensityLevel.low, duration=20)
        else:
            fa = FitnessAction(workout_type=WorkoutType.strength, intensity=IntensityLevel.medium, duration=30)
        return LifeOptimizationAction(fitness_action=fa)

    elif time_of_day == "afternoon":
        if task_name == "fitness-progression":
            if energy < 0.45 or fatigue > 0.65:
                wa = WorkAction(task_type=TaskType.rest, effort_level=EffortLevel.low)
            else:
                wa = WorkAction(task_type=TaskType.email, effort_level=EffortLevel.low)
        elif task_name == "work-allocation":
            if energy > 0.7 and focus > 0.55:
                wa = WorkAction(task_type=TaskType.deep_work, effort_level=EffortLevel.medium)
            elif energy > 0.45:
                wa = WorkAction(task_type=TaskType.support, effort_level=EffortLevel.medium)
            else:
                wa = WorkAction(task_type=TaskType.email, effort_level=EffortLevel.low)
        elif energy < 0.4:
            wa = WorkAction(task_type=TaskType.rest, effort_level=EffortLevel.low)
        elif fatigue > 0.7:
            wa = WorkAction(task_type=TaskType.email, effort_level=EffortLevel.low)
        elif energy > 0.7 and focus > 0.6:
            wa = WorkAction(task_type=TaskType.deep_work, effort_level=EffortLevel.medium)
        else:
            wa = WorkAction(task_type=TaskType.email, effort_level=EffortLevel.medium)
        return LifeOptimizationAction(work_action=wa)

    else:  # evening
        return LifeOptimizationAction()


def parse_action(text: str, time_of_day: str) -> Optional[LifeOptimizationAction]:
    """Parse LLM JSON response into a LifeOptimizationAction. Returns None on failure."""
    try:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        data = json.loads(text)
        
        # Only process if data is a dictionary
        if not isinstance(data, dict):
            return None
        
        fa_data = data.get("fitness_action")
        wa_data = data.get("work_action")
        
        # Ensure data is a dict before unpacking; reject if it's a string or other type
        # If either is a string, the LLM returned malformed JSON, so reject the parse
        if fa_data is not None and not isinstance(fa_data, dict):
            return None
        if wa_data is not None and not isinstance(wa_data, dict):
            return None
        
        fa = FitnessAction(**fa_data) if fa_data else None
        wa = WorkAction(**wa_data) if wa_data else None
        return LifeOptimizationAction(fitness_action=fa, work_action=wa)
    except Exception:
        return None


def _clamp_score(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def _score_ratio(count: int, target: int) -> float:
    if target <= 0:
        return 1.0
    return min(count / target, 1.0)


def _grade_fitness_progression(trace: List[dict], final_obs: dict) -> float:
    fitness_steps = [step for step in trace if step["phase"] == "morning"]
    workout_steps = [
        step for step in fitness_steps
        if step["action"].get("fitness_action", {}).get("workout_type") not in (None, "rest")
    ]
    strength_steps = [
        step for step in fitness_steps
        if step["action"].get("fitness_action", {}).get("workout_type") == "strength"
    ]
    avg_fatigue = (
        sum(step["observation"].get("fatigue", 0.0) for step in trace) / len(trace)
        if trace else final_obs.get("fatigue", 1.0)
    )
    score = (
        0.45 * final_obs.get("fitness_score", 0.0)
        + 0.20 * _score_ratio(len(workout_steps), 5)
        + 0.15 * _score_ratio(len(strength_steps), 3)
        + 0.10 * final_obs.get("consistency", 0.0)
        + 0.10 * (1.0 - avg_fatigue)
    )
    return _clamp_score(score)


def _grade_work_allocation(trace: List[dict], final_obs: dict) -> float:
    work_steps = [step for step in trace if step["phase"] == "afternoon"]
    deep_work_steps = [
        step for step in work_steps
        if step["action"].get("work_action", {}).get("task_type") == "deep_work"
    ]
    productive_steps = [
        step for step in work_steps
        if step["action"].get("work_action", {}).get("task_type") in {"deep_work", "support", "email", "scheduling"}
    ]
    admin_steps = [
        step for step in work_steps
        if step["action"].get("work_action", {}).get("task_type") in {"support", "email", "scheduling"}
    ]
    avg_energy = (
        sum(step["observation"].get("energy", 0.0) for step in work_steps) / len(work_steps)
        if work_steps else final_obs.get("energy", 0.0)
    )
    avg_fatigue = (
        sum(step["observation"].get("fatigue", 0.0) for step in work_steps) / len(work_steps)
        if work_steps else final_obs.get("fatigue", 1.0)
    )
    backlog_score = 1.0 - min(final_obs.get("pending_tasks", 8) / 8.0, 1.0)
    score = (
        0.35 * final_obs.get("productivity", 0.0)
        + 0.20 * _score_ratio(len(deep_work_steps), 4)
        + 0.10 * _score_ratio(len(productive_steps), 6)
        + 0.15 * _score_ratio(len(admin_steps), 2)
        + 0.10 * avg_energy
        + 0.10 * backlog_score
        + 0.10 * (1.0 - avg_fatigue)
    )
    return _clamp_score(score)


def _grade_life_optimization(trace: List[dict], final_obs: dict) -> float:
    fitness_steps = [step for step in trace if step["phase"] == "morning"]
    work_steps = [step for step in trace if step["phase"] == "afternoon"]
    productivity = final_obs.get("productivity", 0.0)
    fitness = final_obs.get("fitness_score", 0.0)
    fatigue = final_obs.get("fatigue", 1.0)
    consistency = final_obs.get("consistency", 0.0)
    backlog_score = 1.0 - min(final_obs.get("pending_tasks", 8) / 8.0, 1.0)
    recovery_steps = [
        step for step in fitness_steps
        if step["action"].get("fitness_action", {}).get("workout_type") in {"rest", "yoga"}
    ]
    workout_types = {
        step["action"].get("fitness_action", {}).get("workout_type")
        for step in fitness_steps
        if step["action"].get("fitness_action", {}).get("workout_type")
    }
    admin_steps = [
        step for step in work_steps
        if step["action"].get("work_action", {}).get("task_type") in {"support", "email", "scheduling"}
    ]
    avg_fatigue = (
        sum(step["observation"].get("fatigue", 0.0) for step in trace) / len(trace)
        if trace else fatigue
    )
    balance = 1.0 - abs(productivity - fitness)
    score = (
        0.15 * productivity
        + 0.15 * fitness
        + 0.10 * balance
        + 0.10 * backlog_score
        + 0.10 * consistency
        + 0.15 * _score_ratio(len(recovery_steps), 2)
        + 0.10 * _score_ratio(len(workout_types), 3)
        + 0.10 * _score_ratio(len(admin_steps), 2)
        + 0.05 * (1.0 - avg_fatigue)
    )
    return _clamp_score(score)


def grade_episode(task_name: str, trace: List[dict], final_obs: dict) -> float:
    graders = {
        "fitness-progression": _grade_fitness_progression,
        "work-allocation": _grade_work_allocation,
        "life-optimization": _grade_life_optimization,
    }
    return graders[task_name](trace, final_obs)


def get_llm_action(client: Optional[OpenAI], obs: dict, step: int, task_name: str) -> LifeOptimizationAction:
    """Call LLM and return a parsed action, falling back to baseline on any failure."""
    time_of_day = obs.get("time_of_day", "morning")
    if time_of_day == "evening":
        return LifeOptimizationAction()
    if client is None:
        return _baseline_action(obs, task_name)

    prompt = build_prompt(obs, step, task_name)
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        text = (resp.choices[0].message.content or "").strip()
        action = parse_action(text, time_of_day)
        if action is not None:
            return action
    except Exception:
        pass

    return _baseline_action(obs, task_name)

# ---------------------------------------------------------------------------
# Single episode runner
# ---------------------------------------------------------------------------

async def run_episode(env: FitrlEnv, client: Optional[OpenAI], task_name: str) -> EpisodeResult:
    """Run one full episode, emit [START]/[STEP], and return a bounded task score."""
    model_label = MODEL_NAME if client is not None else "baseline-rule-policy"
    log_start(task=task_name, env=BENCHMARK, model=model_label)

    rewards: List[float] = []
    trace: List[dict] = []
    steps_taken = 0
    score = 0.0
    success = False
    obs = None

    try:
        result = await env.reset()
        obs = result.observation.model_dump()

        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break

            prev_obs = dict(obs)
            action = get_llm_action(client, prev_obs, step, task_name)
            action_payload = _strip_metadata(action.model_dump(exclude_none=True))
            action_str = _action_to_log_string(action)

            result = await env.step(action)
            obs = result.observation.model_dump()
            reward = result.reward or 0.0
            done = result.done
            steps_taken = step

            rewards.append(reward)
            trace.append({
                "step": step,
                "phase": prev_obs.get("time_of_day", "morning"),
                "action": action_payload,
                "observation": dict(obs),
                "reward": reward,
            })
            log_step(step=step, action=action_str, reward=reward, done=done, error=None)

            if done:
                break

        score = grade_episode(task_name, trace, obs)
        success = score >= SUCCESS_SCORE_THRESHOLD
    except Exception:
        pass

    return EpisodeResult(
        steps_taken=steps_taken,
        rewards=rewards,
        score=score,
        success=success,
    )

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    if POLICY_MODE not in {"openai", "baseline"}:
        raise RuntimeError("POLICY_MODE must be either 'openai' or 'baseline'")

    client: Optional[OpenAI] = None
    if POLICY_MODE == "openai":
        if not API_KEY:
            raise RuntimeError("Set OPENAI_API_KEY, API_KEY, or HF_TOKEN before running inference.py")
        client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    for task in TASK_SPECS:
        episode_result = EpisodeResult(steps_taken=0, rewards=[], score=0.0, success=False)
        if USE_LOCAL_ENV:
            env = LocalEnvAdapter()
        elif IMAGE_NAME:
            env = await FitrlEnv.from_docker_image(IMAGE_NAME)
        else:
            env = FitrlEnv(base_url=ENV_BASE_URL)

        try:
            episode_result = await run_episode(env, client, task.name)
        finally:
            try:
                await env.close()
            except Exception:
                pass
            log_end(
                success=episode_result.success,
                steps=episode_result.steps_taken,
                score=episode_result.score,
                rewards=episode_result.rewards,
            )


if __name__ == "__main__":
    asyncio.run(main())
