# FitRL Input Enums - Visual Quick Card

Print this out or bookmark it! 📋

---

## **MORNING: FitnessAction**

### WorkoutType ❌→✅
```
❌ "Strength"  →  ✅ "strength"
❌ "CARDIO"    →  ✅ "cardio"
❌ "YOGA"      →  ✅ "yoga"
❌ "REST"      →  ✅ "rest"
```

### IntensityLevel ❌→✅
```
❌ "LOW"       →  ✅ "low"
❌ "MEDIUM"    →  ✅ "medium"
❌ "HIGH"      →  ✅ "high"
```

### Duration ❌→✅
```
❌ 35.5        →  ✅ 35
❌ -10         →  ✅ 30
❌ 150         →  ✅ 120
✅ 0 to 120 (whole numbers only)
```

---

## **AFTERNOON: WorkAction**

### TaskType ❌→✅
```
❌ "DeepWork"  →  ✅ "deep_work"
❌ "EMAIL"     →  ✅ "email"
❌ "SUPPORT"   →  ✅ "support"
❌ "SCHED"     →  ✅ "scheduling"
❌ "REST"      →  ✅ "rest"
```

### EffortLevel ❌→✅
```
❌ "LOW"       →  ✅ "low"
❌ "MEDIUM"    →  ✅ "medium"
❌ "HIGH"      →  ✅ "high"
```

---

## **EVENING: No Input**

```
❌ FitnessAction(...)     → Ignored
❌ WorkAction(...)        → Ignored
✅ LifeOptimizationAction() → Correct!
```

---

## **Payload Cheatsheet**

### 🏋️ Morning
```json
{
  "fitness_action": {
    "workout_type": "strength",
    "intensity": "medium",
    "duration": 35
  }
}
```

### 💼 Afternoon
```json
{
  "work_action": {
    "task_type": "deep_work",
    "effort_level": "high"
  }
}
```

### 😴 Evening
```json
{}
```

---

## **Decision Tree**

### Morning Decision
```
                START (Morning Phase)
                        |
        How's your energy/recovery?
                    /       \
                High         Low
                /             \
        Do strength!      Try yoga
        (or cardio)       (or rest)
            |                 |
        High effort?      Low effort
        (duration 40+)    (duration 15-25)
```

### Afternoon Decision
```
                START (Afternoon Phase)
                        |
        How's your energy/focus?
                    /       \
                High         Low
                /             \
        Deep work!        Email or
        (effort high)      support
                |          (effort low)
            Productivity    Quick wins
            boost!          without drain
```

### Evening Decision
```
                START (Evening Phase)
                        |
                        |
        DO NOTHING! 😴
        (Automatic recovery)
                        |
        Energy restored ✅
        Fatigue reduced ✅
        Day incremented ✅
```

---

## **String Values (Copy-Paste Ready)**

### Workout Types
```
"strength"
"cardio"
"yoga"
"rest"
```

### Intensity Levels
```
"low"
"medium"
"high"
```

### Task Types
```
"deep_work"
"email"
"support"
"scheduling"
"rest"
```

### Effort Levels
```
"low"
"medium"
"high"
```

### Duration
```
0, 15, 20, 25, 30, 35, 40, 45, 50, 60, 90, 120
(Any integer 0-120)
```

---

## **Common Patterns**

### Peak Energy Day
```json
{
  "fitness_action": {
    "workout_type": "strength",
    "intensity": "high",
    "duration": 45
  }
}
```
Then...
```json
{
  "work_action": {
    "task_type": "deep_work",
    "effort_level": "high"
  }
}
```

### Recovery Day
```json
{
  "fitness_action": {
    "workout_type": "yoga",
    "intensity": "low",
    "duration": 20
  }
}
```
Then...
```json
{
  "work_action": {
    "task_type": "email",
    "effort_level": "low"
  }
}
```

### Light Day
```json
{
  "fitness_action": {
    "workout_type": "rest",
    "intensity": "low",
    "duration": 0
  }
}
```
Then...
```json
{
  "work_action": {
    "task_type": "support",
    "effort_level": "medium"
  }
}
```

---

## **Enum Value Count**

| Category | Count | Values |
|----------|-------|--------|
| WorkoutType | 4 | strength, cardio, yoga, rest |
| IntensityLevel | 3 | low, medium, high |
| Duration | ∞ | 0-120 (any integer) |
| TaskType | 5 | deep_work, email, support, scheduling, rest |
| EffortLevel | 3 | low, medium, high |

**Total possible morning actions:** 4 × 3 × 121 = 1,452
**Total possible afternoon actions:** 5 × 3 = 15
**Total possible per day:** 1,452 + 15 + 1 = 1,468

---

## **Validation Errors & Fixes**

### ❌ Error: Invalid enum value
```
"Input should be a valid enumeration" 
for WorkoutType='Strength'

Fix: Use lowercase → "strength"
```

### ❌ Error: Duration out of range
```
"Input should be less than or equal to 120" 
for duration=150

Fix: Use value ≤ 120 → 120
```

### ❌ Error: Duration not integer
```
"Input should be a valid integer"
for duration=35.5

Fix: Use integer → 35
```

### ❌ Error: Task type typo
```
"Input should be 'deep_work' not 'deepwork'"
for task_type='deepwork'

Fix: Add underscore → "deep_work"
```

---

## **One-Liner Examples**

**Python:**
```python
# Morning
FitnessAction(workout_type="strength", intensity="high", duration=45)

# Afternoon
WorkAction(task_type="deep_work", effort_level="high")

# Evening
LifeOptimizationAction()
```

**JSON:**
```json
// Morning
{"fitness_action": {"workout_type": "strength", "intensity": "high", "duration": 45}}

// Afternoon
{"work_action": {"task_type": "deep_work", "effort_level": "high"}}

// Evening
{}
```

---

## **Test Values**

Use these for testing:

```python
# Simple valid action
FitnessAction(workout_type="rest", intensity="low", duration=0)

# Complex valid action
FitnessAction(workout_type="strength", intensity="high", duration=120)

# Medium action
FitnessAction(workout_type="cardio", intensity="medium", duration=30)

# Work
WorkAction(task_type="deep_work", effort_level="medium")
```

---

## **Remember! 🧠**

✅ **All lowercase**
```
"strength" ✅  not "Strength" or "STRENGTH"
"deep_work" ✅ not "DeepWork" or "DEEP_WORK"
```

✅ **Use underscore for multi-word enums**
```
"deep_work" ✅  not "deepwork"
"deep-work" ❌  wrong
```

✅ **Duration is integer**
```
30 ✅  not 30.0 or "30"
```

✅ **Evening is empty**
```
{} ✅  not {"fitness_action": null}
```

---

**Bookmark this page! You'll reference it often!** 🔖
