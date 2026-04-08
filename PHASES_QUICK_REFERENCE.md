# FitRL Phases - Quick Reference

## TL;DR (Too Long; Didn't Read)

**Each day has 3 phases:**

1. **Morning** (Agent chooses fitness) → Energy/Fatigue change
2. **Afternoon** (Agent chooses work) → Productivity/Backlog change  
3. **Evening** (Automatic recovery) → Energy restored, Day incremented

**Total: 21 steps = 7 days × 3 phases**

---

## Visual Timeline

```
┌─────────────────────────────────────────────────────┐
│                    EPISODE (7 DAYS)                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  DAY 1          DAY 2          ...        DAY 7     │
│  ┌───────────┐  ┌───────────┐          ┌───────────┐
│  │ M A E     │  │ M A E     │          │ M A E     │
│  │ o f v     │  │ o f v     │    ...   │ o f v     │
│  │ r n e     │  │ r n e     │          │ r n e     │
│  │ n i n     │  │ n i n     │          │ n i n     │
│  │ i t g     │  │ i t g     │          │ i t g     │
│  │ n . .     │  │ n . .     │          │ n . .     │
│  └───────────┘  └───────────┘          └───────────┘
│  St:1 2 3      St:4 5 6                St:19 20 21 │
│  ↓             ↓                        ↓            │
│  Reward        Reward                  done=true    │
│                                                     │
└─────────────────────────────────────────────────────┘

M = Morning (Fitness)
A = Afternoon (Work)
E = Evening (Recovery)
St = Step number
```

---

## Agent Inputs by Phase

### Morning (Steps 1, 4, 7, 10, 13, 16, 19)

**What Agent Sends:**
```python
LifeOptimizationAction(
    fitness_action=FitnessAction(
        workout_type="strength|cardio|yoga|rest",
        intensity="low|medium|high",
        duration=0-120  # minutes
    )
)
```

**What Changes:**
- Fitness ↑ (if not rest)
- Fatigue ↑ (proportional to intensity)
- Energy ↓ (proportional to effort)
- Soreness ↑ (especially strength)
- Consistency ↑ (if workout chosen)

---

### Afternoon (Steps 2, 5, 8, 11, 14, 17, 20)

**What Agent Sends:**
```python
LifeOptimizationAction(
    work_action=WorkAction(
        task_type="deep_work|email|support|scheduling|rest",
        effort_level="low|medium|high"
    )
)
```

**What Changes:**
- Productivity ↑ (especially deep work)
- Pending tasks ↓ (1-2 cleared)
- Energy ↓ (proportional to effort)
- Fatigue ↑ (proportional to effort)
- Focus ↓ (slight decrease)

---

### Evening (Steps 3, 6, 9, 12, 15, 18, 21)

**What Agent Sends:**
```python
LifeOptimizationAction()  # Empty! No input needed!
```

**What Changes AUTOMATICALLY:**
- Sleep hours ← calculated
- Energy ↑ (restored from sleep)
- Fatigue ↓ (recovery)
- Soreness ↓ (fixed -0.12)
- Focus ↑ (fixed +0.08)
- Day ↑ (incremented)
- Time of day → morning (ready for next day)
- Pending tasks ↑ (1-2 new tasks added)
- ✅ Episode ends when Day > 7

---

## Payload Examples

### Morning Request
```json
{
  "fitness_action": {
    "workout_type": "strength",
    "intensity": "medium",
    "duration": 35
  }
}
```

### Afternoon Request
```json
{
  "work_action": {
    "task_type": "deep_work",
    "effort_level": "high"
  }
}
```

### Evening Request
```json
{}
```

---

## Response Example (All Phases Same Format)

```json
{
  "observation": {
    "day": 1,
    "time_of_day": "morning",
    "energy": 0.70,
    "fatigue": 0.20,
    "focus": 0.75,
    "soreness": 0.10,
    "sleep_hours": 7.2,
    "last_workout": "cardio",
    "pending_tasks": 7,
    "consistency": 0.60,
    "productivity": 0.55,
    "fitness_score": 0.60
  },
  "reward": 0.18,
  "done": false
}
```

---

## Phase State Tracking

### Carries Forward (Day to Day)
- `productivity` - cumulative work output
- `fitness_score` - cumulative fitness gains
- `pending_tasks` - work backlog
- `consistency` - routine adherence

### Resets Each Day (Evening → Morning)
- `time_of_day` → "morning"
- `day` → incremented
- New tasks added to pending_tasks

### Restored Each Evening
- `energy` → calculated from sleep
- `fatigue` → reduced via sleep
- `focus` → increased (+0.08)
- `soreness` → reduced (-0.12)

---

## Complete 21-Step Sequence

```
Step  1: Day 1, Morning   → Fitness action required
Step  2: Day 1, Afternoon → Work action required
Step  3: Day 1, Evening   → Empty action (automatic)
         ↓ Day increments to 2, new tasks added

Step  4: Day 2, Morning   → Fitness action required
Step  5: Day 2, Afternoon → Work action required
Step  6: Day 2, Evening   → Empty action (automatic)
         ↓ Day increments to 3, new tasks added

Step  7: Day 3, Morning   → Fitness action required
Step  8: Day 3, Afternoon → Work action required
Step  9: Day 3, Evening   → Empty action (automatic)
         ↓ Day increments to 4, new tasks added

Step 10: Day 4, Morning   → Fitness action required
Step 11: Day 4, Afternoon → Work action required
Step 12: Day 4, Evening   → Empty action (automatic)
         ↓ Day increments to 5, new tasks added

Step 13: Day 5, Morning   → Fitness action required
Step 14: Day 5, Afternoon → Work action required
Step 15: Day 5, Evening   → Empty action (automatic)
         ↓ Day increments to 6, new tasks added

Step 16: Day 6, Morning   → Fitness action required
Step 17: Day 6, Afternoon → Work action required
Step 18: Day 6, Evening   → Empty action (automatic)
         ↓ Day increments to 7, new tasks added

Step 19: Day 7, Morning   → Fitness action required
Step 20: Day 7, Afternoon → Work action required
Step 21: Day 7, Evening   → Empty action (automatic)
         ↓ Episode ends (done=true)
```

---

## Key Rules

| Rule | Impact |
|------|--------|
| **Evening is automatic** | No agent input needed, send empty action |
| **Day increments in evening** | After step 3, 6, 9, 12, 15, 18, 21 |
| **New tasks added daily** | +1 to +2 tasks in evening depending on productivity |
| **Episode lasts exactly 21 steps** | done=true after step 21 (Day 7, Evening) |
| **State carries forward** | Productivity, fitness, pending tasks persist |
| **Energy restored daily** | Evening recovery replenishes energy based on sleep |

---

## Common Mistakes

❌ **Mistake 1**: Sending action for evening recovery
```python
env.step(LifeOptimizationAction(
    fitness_action=FitnessAction(...)  # ❌ Won't be processed
))
```

✅ **Correct**: Empty action for evening
```python
env.step(LifeOptimizationAction())  # ✅ Correct
```

---

❌ **Mistake 2**: Forgetting night recovery exists
```python
# Confused: Only counts Morning + Afternoon = 14 steps?
# Forget about evening = 21 steps total!
```

✅ **Correct**: Include evening in step count
```python
# 7 days × 3 phases = 21 steps total
# 7 mornings + 7 afternoons + 7 evenings
```

---

❌ **Mistake 3**: Expecting afternoon state to be morning state
```python
# Morning energy = 0.8
# After fitness action, energy = 0.55
# Afternoon observation shows energy = 0.55 (NOT 0.8!)
```

---

## Testing Locally

```python
from fitrl import FitrlEnv, LifeOptimizationAction, FitnessAction, WorkAction

env = FitrlEnv(base_url="http://localhost:8000")
obs = env.reset().observation

for day in range(1, 8):
    # Morning
    obs = env.step(LifeOptimizationAction(
        fitness_action=FitnessAction(
            workout_type="strength", 
            intensity="medium", 
            duration=30
        )
    )).observation
    print(f"Day {day} Morning: energy={obs.energy:.2f}, fitness={obs.fitness_score:.2f}")
    
    # Afternoon
    obs = env.step(LifeOptimizationAction(
        work_action=WorkAction(
            task_type="deep_work",
            effort_level="medium"
        )
    )).observation
    print(f"Day {day} Afternoon: energy={obs.energy:.2f}, tasks={obs.pending_tasks}")
    
    # Evening (automatic recovery)
    obs = env.step(LifeOptimizationAction()).observation
    print(f"Day {day} Evening: energy={obs.energy:.2f}, day={obs.day}, done={obs.done}")

env.close()
```

**Expected Output:**
```
Day 1 Morning: energy=0.55, fitness=0.66
Day 1 Afternoon: energy=0.39, tasks=3
Day 1 Evening: energy=0.71, day=2, done=False
Day 2 Morning: energy=0.55, fitness=0.82
Day 2 Afternoon: energy=0.39, tasks=1
Day 2 Evening: energy=0.71, day=3, done=False
...
Day 7 Evening: energy=0.71, day=8, done=True
```

---

**Now you're ready to work with FitRL phases!** 🚀
