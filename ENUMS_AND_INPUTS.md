# FitRL Input Enums & Lists

Complete reference for all valid input values for FitRL actions.

---

## **Morning Phase: Fitness Action Enums**

### `WorkoutType` (Required)
Choose ONE type of workout:

```python
class WorkoutType(str, Enum):
    strength = "strength"      # Build muscle, high fatigue
    cardio = "cardio"          # Improve endurance, moderate fatigue
    yoga = "yoga"              # Recovery-focused, reduces fatigue
    rest = "rest"              # Complete rest day
```

**Valid Values:**
```
✅ "strength"
✅ "cardio"
✅ "yoga"
✅ "rest"
```

**Impact Comparison:**

| Workout | Fitness Gain | Fatigue | Energy Cost | Soreness | Best For |
|---------|--------------|---------|------------|----------|----------|
| **strength** | High (+0.21 med) | High (+0.25) | High (-0.25) | High (+0.35) | Building fitness |
| **cardio** | Medium (+0.13 med) | Medium (+0.2) | Medium (-0.2) | None | Endurance |
| **yoga** | None | Reduction (-0.08) | Minimal (+0.03) | Reduction (-0.04) | Recovery |
| **rest** | None | Reduction (-0.04) | Gain (+0.08) | None | Light day |

---

### `IntensityLevel` (Required)
Choose intensity for the workout:

```python
class IntensityLevel(str, Enum):
    low = "low"              # Easy, less fatigue
    medium = "medium"        # Balanced effort
    high = "high"            # Intense, more fatigue
```

**Valid Values:**
```
✅ "low"
✅ "medium"
✅ "high"
```

**Effect Multiplier:**

| Intensity | Fatigue Multiplier | Energy Cost | When to Use |
|-----------|-------------------|------------|-----------|
| **low** | 0.6× base | 0.8× base | After tired days |
| **medium** | 1.0× base | 1.0× base | Standard days |
| **high** | 1.4× base | 1.2× base | Well-rested days |

**Example:**
- Strength + Low = moderate gains, low fatigue
- Strength + High = high gains, high fatigue
- Yoga + High = same recovery, just faster

---

### `Duration` (Required, Integer)
Workout duration in minutes:

```python
duration: int  # Range: 0-120 minutes
```

**Valid Values:**
```
✅ 0 to 120 (inclusive)
✅ Must be an integer (no decimals)
```

**Typical Ranges:**

| Duration | Intensity | Type | Example |
|----------|-----------|------|---------|
| 0-15 min | Any | Quick session | Yoga stretch (10 min) |
| 15-30 min | Low-Med | Standard | Jog (25 min) |
| 30-60 min | Medium-High | Full session | Strength training (45 min) |
| 60-120 min | High | Intensive | Long cardio (90 min) |

---

## **Afternoon Phase: Work Action Enums**

### `TaskType` (Required)
Choose ONE type of work task:

```python
class TaskType(str, Enum):
    deep_work = "deep_work"        # Complex, focused work (highest value)
    email = "email"                # Email management (quick, low effort)
    support = "support"            # Helping others, support tasks
    scheduling = "scheduling"      # Planning, admin work
    rest = "rest"                  # No work, mental break
```

**Valid Values:**
```
✅ "deep_work"
✅ "email"
✅ "support"
✅ "scheduling"
✅ "rest"
```

**Task Characteristics:**

| Task Type | Tasks Cleared | Productivity Gain | Energy Cost | When to Use |
|-----------|---------------|-------------------|------------|-----------|
| **deep_work** | 1-2 | Highest (+0.29 high) | Highest (-0.19) | Peak energy/focus |
| **email** | 1 | Low (+0.08) | Lowest (-0.05) | Energy low |
| **support** | 1 | Medium (+0.17 high) | Medium (-0.08) | Help needed |
| **scheduling** | 1 | Medium (+0.12) | Low (-0.05) | Planning time |
| **rest** | 0 | 0 | +0.05 | Recovery needed |

---

### `EffortLevel` (Required)
Choose effort level for the work:

```python
class EffortLevel(str, Enum):
    low = "low"              # Minimal effort
    medium = "medium"        # Normal effort
    high = "high"            # Maximum effort
```

**Valid Values:**
```
✅ "low"
✅ "medium"
✅ "high"
```

**Effect Multiplier:**

| Effort | Productivity Multiplier | Energy Cost | When to Use |
|--------|------------------------|------------|-----------|
| **low** | 0.8× base | 0.8× base | Energy depleted |
| **medium** | 1.0× base | 1.0× base | Normal days |
| **high** | 1.2× base | 1.2× base | Well-rested |

**Combined with Task Type:**

| Task | Low Effort | Medium Effort | High Effort |
|------|-----------|--------------|-----------|
| **deep_work** | +0.19 prod | +0.24 prod | +0.29 prod |
| **email** | +0.08 prod | +0.08 prod | +0.08 prod |
| **support** | +0.11 prod | +0.14 prod | +0.17 prod |
| **scheduling** | +0.08 prod | +0.10 prod | +0.12 prod |

---

## **Complete Input Examples**

### Morning Examples

**Strong training day (well-rested):**
```python
FitnessAction(
    workout_type="strength",
    intensity="high",
    duration=45
)
```

**Light recovery day (tired):**
```python
FitnessAction(
    workout_type="yoga",
    intensity="low",
    duration=20
)
```

**Quick jog (moderate):**
```python
FitnessAction(
    workout_type="cardio",
    intensity="medium",
    duration=30
)
```

**Complete rest:**
```python
FitnessAction(
    workout_type="rest",
    intensity="low",
    duration=0
)
```

---

### Afternoon Examples

**Focused work (peak energy):**
```python
WorkAction(
    task_type="deep_work",
    effort_level="high"
)
```

**Email management (low energy):**
```python
WorkAction(
    task_type="email",
    effort_level="low"
)
```

**Support others (moderate):**
```python
WorkAction(
    task_type="support",
    effort_level="medium"
)
```

**Planning (light load):**
```python
WorkAction(
    task_type="scheduling",
    effort_level="low"
)
```

**Mental break:**
```python
WorkAction(
    task_type="rest",
    effort_level="low"
)
```

---

## **Quick Lookup Table**

### All Enums at a Glance

```
MORNING ENUMS:
├─ WorkoutType:   strength | cardio | yoga | rest
├─ IntensityLevel: low | medium | high
└─ Duration:      0-120 (integer)

AFTERNOON ENUMS:
├─ TaskType:      deep_work | email | support | scheduling | rest
└─ EffortLevel:   low | medium | high

EVENING:
└─ No enums needed (automatic)
```

---

## **Valid Combinations (Examples)**

### Morning - All Valid Combinations (24 total)

**Strength workouts (3 intensity × 1 type):**
- `strength + low + 30`
- `strength + medium + 35`
- `strength + high + 45`

**Cardio workouts (3 intensity × 1 type):**
- `cardio + low + 20`
- `cardio + medium + 30`
- `cardio + high + 40`

**Yoga workouts (3 intensity × 1 type):**
- `yoga + low + 15`
- `yoga + medium + 20`
- `yoga + high + 25`

**Rest (fixed):**
- `rest + low + 0`

---

### Afternoon - All Valid Combinations (15 total)

**Deep work (3 effort levels):**
- `deep_work + low`
- `deep_work + medium`
- `deep_work + high`

**Email (3 effort levels):**
- `email + low`
- `email + medium`
- `email + high`

**Support (3 effort levels):**
- `support + low`
- `support + medium`
- `support + high`

**Scheduling (3 effort levels):**
- `scheduling + low`
- `scheduling + medium`
- `scheduling + high`

**Rest (fixed):**
- `rest + low`

---

## **JSON Payload Reference**

### Morning Payload Structure
```json
{
  "fitness_action": {
    "workout_type": "strength",
    "intensity": "medium",
    "duration": 35
  }
}
```

### Afternoon Payload Structure
```json
{
  "work_action": {
    "task_type": "deep_work",
    "effort_level": "high"
  }
}
```

### Evening Payload Structure
```json
{}
```

---

## **Python Code Reference**

### How to Create Actions

```python
from fitrl.models import (
    LifeOptimizationAction,
    FitnessAction,
    WorkAction,
    WorkoutType,
    IntensityLevel,
    TaskType,
    EffortLevel
)

# Morning Action
morning_action = LifeOptimizationAction(
    fitness_action=FitnessAction(
        workout_type=WorkoutType.strength,      # or "strength"
        intensity=IntensityLevel.medium,        # or "medium"
        duration=35
    )
)

# Afternoon Action
afternoon_action = LifeOptimizationAction(
    work_action=WorkAction(
        task_type=TaskType.deep_work,           # or "deep_work"
        effort_level=EffortLevel.high           # or "high"
    )
)

# Evening Action
evening_action = LifeOptimizationAction()  # Empty

# Using Enum values
env.step(morning_action)

# Or using strings directly
env.step(LifeOptimizationAction(
    fitness_action=FitnessAction(
        workout_type="strength",
        intensity="medium",
        duration=35
    )
))
```

---

## **CLI/REST Examples**

### Using HTTP/API

**Morning request:**
```bash
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "fitness_action": {
      "workout_type": "strength",
      "intensity": "medium",
      "duration": 35
    }
  }'
```

**Afternoon request:**
```bash
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{
    "work_action": {
      "task_type": "deep_work",
      "effort_level": "high"
    }
  }'
```

**Evening request:**
```bash
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## **Validation Rules**

### What Gets Validated

✅ **Valid:**
```python
FitnessAction(workout_type="strength", intensity="medium", duration=45)
FitnessAction(workout_type="cardio", intensity="low", duration=20)
```

❌ **Invalid (typo):**
```python
FitnessAction(workout_type="strenth", intensity="medium", duration=45)
# Error: "strenth" is not a valid WorkoutType
```

❌ **Invalid (case sensitive):**
```python
FitnessAction(workout_type="Strength", intensity="medium", duration=45)
# Error: "Strength" must be lowercase "strength"
```

❌ **Invalid (duration out of range):**
```python
FitnessAction(workout_type="strength", intensity="medium", duration=150)
# Error: duration must be 0-120
```

❌ **Invalid (decimal duration):**
```python
FitnessAction(workout_type="strength", intensity="medium", duration=35.5)
# Error: duration must be integer
```

---

## **Summary Checklist**

### Morning Action Checklist
- [ ] Choose `WorkoutType`: strength, cardio, yoga, or rest
- [ ] Choose `IntensityLevel`: low, medium, or high
- [ ] Choose `Duration`: 0-120 minutes (integer)
- [ ] Wrap in `FitnessAction`
- [ ] Wrap in `LifeOptimizationAction`
- [ ] Send to environment

### Afternoon Action Checklist
- [ ] Choose `TaskType`: deep_work, email, support, scheduling, or rest
- [ ] Choose `EffortLevel`: low, medium, or high
- [ ] Wrap in `WorkAction`
- [ ] Wrap in `LifeOptimizationAction`
- [ ] Send to environment

### Evening Action Checklist
- [ ] Send empty `LifeOptimizationAction()`
- [ ] No other choices needed
- [ ] Let environment handle recovery automatically

---

**All valid FitRL inputs documented!** 🎯
