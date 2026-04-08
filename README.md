---
title: Knowledge Worker Planning Environment
emoji: 🏃
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
---

# Life Optimization Environment

This project simulates a real planning problem humans actually do: deciding how to allocate workouts, focused work, and recovery across a busy week without burning out or letting task backlog pile up.

The environment models a knowledge worker who has to:
- decide a morning fitness action
- allocate afternoon work effort across deep work and lighter operational tasks
- absorb the downstream effect on energy, fatigue, soreness, consistency, and pending work

The episode lasts 7 days with 3 phases per day:
- **Morning**: choose a fitness action
- **Afternoon**: choose a work action
- **Evening**: automatic recovery and next-day rollover

### How Phases Work

Each day follows this flow:

**Step 1: Morning (Agent Acts)**
```
Agent decides: FitnessAction(workout_type, intensity, duration)
Environment applies:
  - Fitness score increased (based on workout)
  - Fatigue increased (based on intensity)
  - Energy decreased (based on effort)
  - Soreness increased (especially for strength)
  - Consistency improved (for any non-rest workout)
Observation returned with updated state
```

**Step 2: Afternoon (Agent Acts)**
```
Agent decides: WorkAction(task_type, effort_level)
Environment applies:
  - Productivity increased (based on task & energy)
  - Pending tasks decreased (1-2 tasks cleared)
  - Energy decreased (based on effort)
  - Fatigue increased (based on effort)
  - Focus possibly affected
  - Consistency updated (based on backlog)
Observation returned with updated state
```

**Step 3: Evening (Automatic - Agent Sends Empty Action)**
```
Agent sends: LifeOptimizationAction() [empty - no fitness or work]
Environment applies AUTOMATICALLY:
  - Sleep hours calculated from fatigue & backlog
  - Energy restored (based on sleep)
  - Fatigue reduced (based on sleep quality)
  - Soreness reduced (fixed daily recovery)
  - Focus slightly improved
  - Consistency affected by remaining backlog
  - Day incremented (next day begins)
  - New tasks added (1-2 new pending tasks)
Observation returned with reset state for next day
```

### Example 7-Day Flow

```
Day 1:
├─ Step 1 (Morning):   [Fitness] → state updates → reward
├─ Step 2 (Afternoon): [Work]    → state updates → reward
└─ Step 3 (Evening):   [Recovery]→ state updates → reward → Day becomes 2

Day 2:
├─ Step 4 (Morning):   [Fitness] → state updates → reward
├─ Step 5 (Afternoon): [Work]    → state updates → reward
└─ Step 6 (Evening):   [Recovery]→ state updates → reward → Day becomes 3

...

Day 7:
├─ Step 19 (Morning):   [Fitness] → state updates → reward
├─ Step 20 (Afternoon): [Work]    → state updates → reward
└─ Step 21 (Evening):   [Recovery]→ state updates → reward → EPISODE ENDS (done=true)
```

### Total Steps Per Episode
- 7 days × 3 phases = **21 steps total**
- Agent makes **14 decisions** (morning + afternoon)
- Environment makes **7 automatic recovery phases**

This makes the environment useful for evaluating agents that need to trade off:
- short-term throughput vs sustainable performance
- exercise consistency vs overtraining
- deep-work focus vs operational maintenance

## Why This Is A Real-World Task

This is not a game environment. It is a compact simulation of weekly planning under energy constraints, which appears in:
- personal productivity assistants
- wellness coaching tools
- energy-aware scheduling systems
- AI copilots for hybrid workers and founders

The environment is intentionally small enough for fast agent evaluation while still exposing realistic tradeoffs:
- training improves fitness but can raise fatigue and soreness
- deep work clears more backlog when energy is high
- avoiding admin forever hurts task mix quality
- recovery restores capacity but can still be affected by backlog

## Tasks

The environment includes 3 graded tasks with deterministic scorers from `0.0` to `1.0`.

| Task | Difficulty | Objective | What the grader rewards |
|---|---|---|---|
| `fitness-progression` | Easy | Improve weekly fitness without letting fatigue spike | workout frequency, strength sessions, low fatigue, routine consistency |
| `work-allocation` | Medium | Clear meaningful work while preserving enough capacity to sustain output | productivity, deep work, admin coverage, low backlog, controlled fatigue |
| `life-optimization` | Hard | Balance work throughput, physical training, and recovery over the whole week | balance, backlog control, consistency, workout variety, recovery choices, sustainable fatigue |

## Reward Design

The environment emits dense per-step reward with partial progress signals:

`0.30 * productivity + 0.20 * fitness_gain + 0.20 * task_progress + 0.15 * consistency + 0.10 * recovery_gain - 0.15 * fatigue - 0.05 * backlog_penalty`

This gives agents useful feedback throughout the episode instead of only at the end. It rewards:
- improving productivity
- improving fitness
- reducing pending tasks
- maintaining routine consistency
- recovering from fatigue

It penalizes:
- high fatigue
- carrying too much unfinished work

## Action Space

### `LifeOptimizationAction`

Morning uses `fitness_action`:
- `workout_type`: `strength | cardio | yoga | rest`
- `intensity`: `low | medium | high`
- `duration`: `0-120`

Afternoon uses `work_action`:
- `task_type`: `email | deep_work | support | scheduling | rest`
- `effort_level`: `low | medium | high`

Evening requires no action.

## Observation Space

### `LifeOptimizationObservation`

| Field | Range | Description |
|---|---|---|
| `day` | 1-7 | Current day in the episode |
| `time_of_day` | morning/afternoon/evening | Active phase |
| `energy` | 0-1 | Current energy available for work/training |
| `fatigue` | 0-1 | Accumulated fatigue |
| `focus` | 0-1 | Mental focus for deep work |
| `soreness` | 0-1 | Residual physical soreness |
| `sleep_hours` | 5.5-8.5 | Simulated sleep affecting recovery |
| `last_workout` | string or null | Most recent workout type |
| `pending_tasks` | 0-10 | Remaining work backlog |
| `consistency` | 0-1 | Routine adherence over the week |
| `productivity` | 0-1 | Accumulated work output |
| `fitness_score` | 0-1 | Accumulated fitness progression |

## Quick Start

```python
from fitrl import FitrlEnv, LifeOptimizationAction, FitnessAction, WorkAction

with FitrlEnv(base_url="http://localhost:8000") as env:
    result = env.reset()

    result = env.step(LifeOptimizationAction(
        fitness_action=FitnessAction(workout_type="strength", intensity="medium", duration=30)
    ))
    print(result.observation.energy, result.reward)

    result = env.step(LifeOptimizationAction(
        work_action=WorkAction(task_type="deep_work", effort_level="medium")
    ))

    result = env.step(LifeOptimizationAction())
```

## JSON Payload Examples

### Morning Action (Fitness)

```json
{
  "fitness_action": {
    "workout_type": "strength",
    "intensity": "medium",
    "duration": 45
  }
}
```

### Afternoon Action (Work)

```json
{
  "work_action": {
    "task_type": "deep_work",
    "effort_level": "high"
  }
}
```

### Evening Action (Recovery - Empty)

```json
{}
```

### Complete Day Sequence (HTTP POST to `/step`)

**Morning Step:**
```bash
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "fitness_action": {
      "workout_type": "cardio",
      "intensity": "medium",
      "duration": 30
    }
  }'
```

**Afternoon Step:**
```bash
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "work_action": {
      "task_type": "deep_work",
      "effort_level": "medium"
    }
  }'
```

**Evening Step:**
```bash
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Local Setup

```bash
cd fitrl
uv sync
../.venv/bin/openenv validate
```

Validation currently passes:

```bash
[OK] fitrl: Ready for multi-mode deployment
```

## Run The Environment Server

```bash
cd fitrl
../.venv/bin/uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
```

## Run The Baseline Inference Script

Deterministic local baseline, reproducible without a server:

```bash
cd fitrl
USE_LOCAL_ENV=1 POLICY_MODE=baseline ../.venv/bin/python inference.py
```

OpenAI-backed benchmark run:

```bash
cd fitrl
OPENAI_API_KEY=your_key \
API_BASE_URL=https://api.openai.com/v1 \
MODEL_NAME=gpt-4.1-mini \
POLICY_MODE=openai \
../.venv/bin/python inference.py
```

Backward-compatible aliases are also supported:
- `API_KEY`
- `HF_TOKEN`

## Baseline Scores

The current deterministic baseline policy produces these reproducible scores with:
`USE_LOCAL_ENV=1 POLICY_MODE=baseline ../.venv/bin/python inference.py`

| Task | Difficulty | Score |
|---|---|---|
| `fitness-progression` | Easy | `0.959` |
| `work-allocation` | Medium | `0.925` |
| `life-optimization` | Hard | `0.678` |

These scores are intentionally non-uniform: the hard task requires a more varied and recovery-aware policy than the baseline rule set.

## Gradio UI

```bash
cd fitrl
../.venv/bin/python app_ui.py
```

Notes:
- leave the API key blank to run the deterministic baseline policy
- provide `OPENAI_API_KEY` plus `API_BASE_URL` and `MODEL_NAME` to run an OpenAI-backed policy
- by default the UI targets `ENV_BASE_URL=http://localhost:8000`

## Docker

Build:

```bash
cd fitrl
docker build -t life-opt-env:latest -f Dockerfile .
```

Run:

```bash
docker run --rm -p 8000:8000 life-opt-env:latest
```

## Hugging Face Space Deployment

```bash
cd fitrl
openenv push
```

Or deploy to a named Space:

```bash
cd fitrl
openenv push --repo-id my-org/life-optimization --private
```

## Project Structure

```
fitrl/
├── __init__.py
├── README.md
├── openenv.yaml
├── pyproject.toml
├── models.py
├── client.py
├── inference.py
├── app_ui.py
├── Dockerfile
└── server/
    ├── __init__.py
    ├── app.py
    └── fitrl_environment.py
```
