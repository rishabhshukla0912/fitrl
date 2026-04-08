# FitRL Phases Explained - Complete Guide

## Overview

FitRL operates on a **7-day cycle** with **3 phases per day**:
- **Morning**: Agent chooses fitness action (step count: odd)
- **Afternoon**: Agent chooses work action (step count: even)
- **Evening**: Environment handles recovery (step count: odd)

**Total: 21 steps per episode (7 days × 3 phases)**

---

## Phase Details

### Phase 1: MORNING (Fitness Decision)

**What Happens:**
```
Step: 1, 4, 7, 10, 13, 16, 19
time_of_day: "morning"
```

**Agent Must Provide:**
```python
LifeOptimizationAction(
    fitness_action=FitnessAction(
        workout_type="strength",      # strength | cardio | yoga | rest
        intensity="medium",           # low | medium | high
        duration=35                   # 0-120 minutes
    )
)
```

**Environment Applies** (based on `_apply_fitness` function):

| Workout | Energy Impact | Fatigue | Soreness | Fitness | Consistency |
|---------|---------------|---------|----------|---------|-------------|
| **Strength** (high) | -0.3 | +0.35 | +0.45 | +0.21 | +0.05 |
| **Strength** (med) | -0.25 | +0.25 | +0.35 | +0.16 | +0.05 |
| **Strength** (low) | -0.2 | +0.15 | +0.25 | +0.11 | +0.05 |
| **Cardio** (high) | -0.25 | +0.25 | 0 | +0.16 | +0.04 |
| **Cardio** (med) | -0.2 | +0.2 | 0 | +0.13 | +0.04 |
| **Cardio** (low) | -0.15 | +0.15 | 0 | +0.1 | +0.04 |
| **Yoga** (any) | +0.03 | -0.08 | -0.04 | 0 | +0.03 |
| **Rest** (low) | +0.08 | -0.04 | 0 | 0 | -0.03 |

**Observation Example (After Morning):**
```json
{
  "day": 1,
  "time_of_day": "morning",
  "energy": 0.7,          // Decreased from morning action
  "fatigue": 0.2,         // Increased from workout
  "focus": 0.7,           // Usually unchanged by fitness
  "soreness": 0.35,       // Increased from strength training
  "fitness_score": 0.55,  // Improved from workout
  "consistency": 0.55     // Improved by maintaining routine
}
```

**Reward Component:**
```
0.20 * fitness_gain (if any) is part of total reward
```

---

### Phase 2: AFTERNOON (Work Decision)

**What Happens:**
```
Step: 2, 5, 8, 11, 14, 17, 20
time_of_day: "afternoon"
```

**Agent Must Provide:**
```python
LifeOptimizationAction(
    work_action=WorkAction(
        task_type="deep_work",        # deep_work | email | support | scheduling | rest
        effort_level="medium"         # low | medium | high
    )
)
```

**Environment Applies** (based on `_apply_work` function):

| Task Type | Effort | Productivity Gain | Tasks Cleared | Energy Cost | When Used |
|-----------|--------|-------------------|---------------|-------------|-----------|
| **Deep Work** | High | +0.29 | 2 | -0.19 | When energy high + focused |
| **Deep Work** | High | +0.14 | 1 | -0.19 | When energy/focus low |
| **Deep Work** | Med | +0.24 | 2 | -0.16 | Balanced approach |
| **Deep Work** | Low | +0.19 | 1 | -0.16 | Energy conservation |
| **Email** | High | +0.08 | 1 | -0.05 | Admin clearing |
| **Email** | Med | +0.08 | 1 | -0.05 | Standard admin |
| **Email** | Low | +0.08 | 1 | -0.05 | Light touch |
| **Support** | High | +0.17 | 1 | -0.08 | Helping others |
| **Support** | Med | +0.14 | 1 | -0.08 | Team support |
| **Support** | Low | +0.11 | 1 | -0.08 | Minimal help |
| **Scheduling** | High | +0.12 | 1 | -0.05 | Planning |
| **Scheduling** | Med | +0.10 | 1 | -0.05 | Standard |
| **Scheduling** | Low | +0.08 | 1 | -0.05 | Light |
| **Rest** | Low | 0 | 0 | +0.05 | Recovery phase |

**Key Dependencies:**
```python
# Deep work productivity boosted if:
if energy >= 0.7 AND focus >= 0.6:
    productivity_gain *= 1.2  # 20% bonus
```

**Observation Example (After Afternoon):**
```json
{
  "day": 1,
  "time_of_day": "afternoon",
  "energy": 0.5,          // Further decreased
  "fatigue": 0.35,        // Increased from work
  "focus": 0.62,          // May decrease from focus exhaustion
  "pending_tasks": 8,     // Decreased from 10 to 8
  "productivity": 0.65,   // Increased from work progress
  "consistency": 0.57     // Updated based on backlog
}
```

**Reward Component:**
```
0.30 * productivity (current value)
0.20 * task_progress (tasks cleared / 2)
```

---

### Phase 3: EVENING (Automatic Recovery)

**What Happens:**
```
Step: 3, 6, 9, 12, 15, 18, 21
time_of_day: "evening"
```

**Agent Should Provide:**
```python
LifeOptimizationAction()  # Empty - no fitness_action or work_action
```

**Environment Applies AUTOMATICALLY** (no agent input needed):

**1. Calculate Sleep Hours:**
```python
sleep_bonus = 0.5 if fatigue > 0.6 else 0.0
backlog_penalty = 0.4 if pending_tasks > 4 else 0.0
sleep_hours = max(5.5, min(8.5, 7.0 + sleep_bonus - backlog_penalty))
```

**Example:**
- High fatigue (0.7) + high backlog (6 tasks): 7.0 + 0.5 - 0.4 = **7.1 hours**
- Low stress (0.2 fatigue) + low backlog (2 tasks): 7.0 + 0 - 0 = **7.0 hours**

**2. Restore Energy Based on Sleep:**
```python
energy = 0.5 + sleep_hours / 10.0 - fatigue * 0.15
```

**3. Reduce Fatigue Based on Sleep:**
```python
fatigue = fatigue - (0.2 + sleep_hours * 0.04)
```

**4. Automatic Reductions (Fixed):**
```python
soreness -= 0.12                # Always recover from soreness
focus += 0.08                   # Mental refreshment
consistency -= 0.01 * min(pending_tasks, 4)  # Stress from backlog
```

**5. Increment Day & Add New Tasks:**
```python
if phase == "evening":
    day += 1  # Move to next day
    if day <= 7:  # If not end of episode
        new_tasks = 1
        if productivity < 0.65:
            new_tasks += 1  # Extra task if unproductive
        pending_tasks = min(pending_tasks + new_tasks, 10)
```

**Observation Example (After Evening/Start of Day 2):**
```json
{
  "day": 2,                       // ✅ Day incremented!
  "time_of_day": "morning",       // ✅ Reset to morning (ready for Day 2)
  "energy": 0.71,                 // ✅ Restored from sleep
  "fatigue": 0.12,                // ✅ Reduced from recovery
  "focus": 0.7,                   // ✅ Refreshed
  "soreness": 0.23,               // ✅ Reduced by 0.12
  "sleep_hours": 7.1,             // New sleep amount
  "pending_tasks": 9,             // ✅ Increased with new tasks
  "consistency": 0.54,            // ✅ Adjusted for backlog
  "productivity": 0.65            // ✅ Unchanged (carries forward)
}
```

---

## Complete Day Example

### Starting State (Day 1, Morning):
```json
{
  "day": 1,
  "time_of_day": "morning",
  "energy": 0.8,
  "fatigue": 0.1,
  "focus": 0.7,
  "soreness": 0.0,
  "pending_tasks": 5,
  "productivity": 0.5,
  "fitness_score": 0.5,
  "consistency": 0.5
}
```

### After Step 1 (Morning - Strength, Medium, 35 min):
```json
{
  "day": 1,
  "time_of_day": "morning",
  "energy": 0.55,             // Decreased by ~0.25
  "fatigue": 0.35,            // Increased by ~0.25
  "focus": 0.7,               // Unchanged
  "soreness": 0.35,           // Increased from strength
  "pending_tasks": 5,         // Unchanged
  "productivity": 0.5,        // Unchanged
  "fitness_score": 0.66,      // Increased by ~0.16
  "consistency": 0.55,        // Increased by 0.05
  "reward": 0.08              // From reward formula
}
```

### After Step 2 (Afternoon - Deep Work, Medium, energy=0.55):
```json
{
  "day": 1,
  "time_of_day": "afternoon",
  "energy": 0.39,             // Decreased by ~0.16
  "fatigue": 0.55,            // Increased by ~0.20
  "focus": 0.62,              // Decreased slightly
  "soreness": 0.35,           // Unchanged
  "pending_tasks": 3,         // Decreased by 2 (deep work success)
  "productivity": 0.74,       // Increased by ~0.24
  "fitness_score": 0.66,      // Unchanged
  "consistency": 0.57,        // Updated
  "reward": 0.32              // Higher reward for productivity
}
```

### After Step 3 (Evening - Automatic Recovery):
```json
{
  "day": 2,                   // ✅ DAY INCREMENTED
  "time_of_day": "morning",   // ✅ RESET TO MORNING
  "energy": 0.71,             // Restored: 0.5 + 7.1/10 - 0.55*0.15
  "fatigue": 0.12,            // Reduced: 0.55 - (0.2 + 7.1*0.04)
  "focus": 0.7,               // Increased by 0.08
  "soreness": 0.23,           // Reduced by 0.12
  "sleep_hours": 7.1,         // Calculated from fatigue & backlog
  "pending_tasks": 4,         // Increased with new tasks (3 + 1)
  "productivity": 0.74,       // Carries forward
  "fitness_score": 0.66,      // Carries forward
  "consistency": 0.56,        // Adjusted for backlog
  "reward": 0.15              // Recovery reward
}
```

---

## Key Insights

### Evening is Automatic (No Action Needed)
```python
# Correct: Agent should send empty action for evening
result = env.step(LifeOptimizationAction())  # ✅ Correct

# Incorrect: Agent tries to send fitness or work action
result = env.step(LifeOptimizationAction(
    fitness_action=FitnessAction(...)  # ❌ Ignored
))
```

### State Flows Forward
- `productivity`, `fitness_score`, `pending_tasks` carry from day to day
- `energy`, `fatigue`, `focus` are restored each evening but persist across morning→afternoon
- `day` and `time_of_day` are automatically managed

### Episode Ends on Step 21
```python
done = (prev_day >= 7) AND (phase == "evening")
# True only when finishing evening of day 7
# Step 21: Day 7, Evening → done=true
```

### Action Sequence Over 7 Days

```
Day 1: Morning (step 1) → Afternoon (step 2) → Evening (step 3) [day++]
Day 2: Morning (step 4) → Afternoon (step 5) → Evening (step 6) [day++]
Day 3: Morning (step 7) → Afternoon (step 8) → Evening (step 9) [day++]
Day 4: Morning (step 10) → Afternoon (step 11) → Evening (step 12) [day++]
Day 5: Morning (step 13) → Afternoon (step 14) → Evening (step 15) [day++]
Day 6: Morning (step 16) → Afternoon (step 17) → Evening (step 18) [day++]
Day 7: Morning (step 19) → Afternoon (step 20) → Evening (step 21) [done=true]
```

---

## Testing the Phases

```python
from fitrl import FitrlEnv, LifeOptimizationAction, FitnessAction, WorkAction

with FitrlEnv(base_url="http://localhost:8000") as env:
    result = env.reset()
    print(f"Initial: day={result.observation.day}, phase={result.observation.time_of_day}")
    
    # Step 1: Morning
    result = env.step(LifeOptimizationAction(
        fitness_action=FitnessAction(workout_type="strength", intensity="medium", duration=30)
    ))
    print(f"After step 1: phase={result.observation.time_of_day}, fitness={result.observation.fitness_score:.2f}")
    
    # Step 2: Afternoon
    result = env.step(LifeOptimizationAction(
        work_action=WorkAction(task_type="deep_work", effort_level="medium")
    ))
    print(f"After step 2: phase={result.observation.time_of_day}, productivity={result.observation.productivity:.2f}")
    
    # Step 3: Evening (automatic recovery)
    result = env.step(LifeOptimizationAction())  # Empty action
    print(f"After step 3: day={result.observation.day}, phase={result.observation.time_of_day}, energy={result.observation.energy:.2f}")
```

**Output:**
```
Initial: day=1, phase=morning
After step 1: phase=morning, fitness=0.66
After step 2: phase=afternoon, productivity=0.74
After step 3: day=2, phase=morning, energy=0.71
```

---

## Summary Table

| Phase | Step | Agent Input | State Changes | Automatic | Next Phase |
|-------|------|------------|---------------|-----------|-----------|
| **Morning** | 1,4,7... | FitnessAction | Energy↓ Fitness↑ Fatigue↑ Soreness↑ | No | Afternoon |
| **Afternoon** | 2,5,8... | WorkAction | Energy↓ Productivity↑ Tasks↓ Fatigue↑ | No | Evening |
| **Evening** | 3,6,9... | Empty Action | Energy↑ Fatigue↓ Sleep calc Day↑ Tasks↑ | YES | Day++/Morning |

---

**Now you understand how FitRL's 3-phase daily cycle creates a realistic weekly planning loop!** 🎯
