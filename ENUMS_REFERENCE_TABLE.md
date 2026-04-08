# FitRL Enums - Complete Reference Table

## **Enum 1: WorkoutType (Morning)**

```
┌────────────┬──────────────┬────────────┬────────────┬────────────┐
│ Value      │ Fitness Gain │ Fatigue↑   │ Energy↓    │ Soreness↑  │
├────────────┼──────────────┼────────────┼────────────┼────────────┤
│ "strength" │ Highest      │ Highest    │ Highest    │ Highest    │
│ "cardio"   │ Medium       │ Medium     │ Medium     │ None       │
│ "yoga"     │ None         │ Reduces    │ +Gain      │ Reduces    │
│ "rest"     │ None         │ Reduces    │ +Gain      │ None       │
└────────────┴──────────────┴────────────┴────────────┴────────────┘
```

**Examples:**
- `"strength"` → Build muscle, highest gains but exhausting
- `"cardio"` → Endurance, balanced effort
- `"yoga"` → Recovery-focused, reduces fatigue
- `"rest"` → Complete rest day

---

## **Enum 2: IntensityLevel (Morning)**

```
┌──────────┬──────────────────┬──────────────┬──────────────────┐
│ Value    │ Fatigue Impact   │ Energy Cost  │ Recommendation   │
├──────────┼──────────────────┼──────────────┼──────────────────┤
│ "low"    │ 0.6× base        │ 0.8× base    │ After tired days │
│ "medium" │ 1.0× base        │ 1.0× base    │ Standard days    │
│ "high"   │ 1.4× base        │ 1.2× base    │ Well-rested      │
└──────────┴──────────────────┴──────────────┴──────────────────┘
```

**Examples:**
- `"low"` + strength → Light strength training
- `"medium"` + cardio → Standard run
- `"high"` + yoga → Intense yoga session

---

## **Enum 3: Duration (Morning)**

```
┌───────────────┬─────────────┬──────────────┐
│ Duration (min)│ Intensity   │ Example      │
├───────────────┼─────────────┼──────────────┤
│ 0             │ N/A         │ Rest day     │
│ 5-15          │ Any         │ Quick yoga   │
│ 15-30         │ Low-Med     │ Light jog    │
│ 30-45         │ Med-High    │ Full session │
│ 45-60         │ High        │ Intense      │
│ 60-120        │ High        │ Very long    │
└───────────────┴─────────────┴──────────────┘
```

**Rules:**
- Must be integer (whole number)
- Range: 0 to 120
- No decimals (35 ✅, 35.5 ❌)

---

## **Enum 4: TaskType (Afternoon)**

```
┌─────────────┬──────────────┬──────────────┬────────────┬──────────────┐
│ Value       │ Tasks Clear  │ Prod Gain    │ Energy↓    │ Use When     │
├─────────────┼──────────────┼──────────────┼────────────┼──────────────┤
│ "deep_work" │ 1-2 tasks    │ Highest      │ Highest    │ Peak energy  │
│ "email"     │ 1 task       │ Low          │ Lowest     │ Low energy   │
│ "support"   │ 1 task       │ Medium       │ Medium     │ Help others  │
│ "scheduling"│ 1 task       │ Medium-Low   │ Low        │ Planning     │
│ "rest"      │ 0 tasks      │ 0            │ +Gain      │ Recovery     │
└─────────────┴──────────────┴──────────────┴────────────┴──────────────┘
```

**Best For Each Task:**
- `"deep_work"` → Complex problems, coding, analysis
- `"email"` → Email management, quick responses
- `"support"` → Helping team, meetings, support
- `"scheduling"` → Planning, admin, organization
- `"rest"` → Mental break, recovery

---

## **Enum 5: EffortLevel (Afternoon)**

```
┌──────────┬──────────────────┬──────────────┬──────────────────┐
│ Value    │ Productivity ×   │ Energy Cost  │ Recommendation   │
├──────────┼──────────────────┼──────────────┼──────────────────┤
│ "low"    │ 0.8× base        │ 0.8× base    │ Exhausted        │
│ "medium" │ 1.0× base        │ 1.0× base    │ Normal           │
│ "high"   │ 1.2× base        │ 1.2× base    │ Well-rested      │
└──────────┴──────────────────┴──────────────┴──────────────────┘
```

**Combinations:**
- `"low"` effort = Minimum drain
- `"medium"` effort = Standard productivity
- `"high"` effort = Maximum output (high drain)

---

## **All Valid Enum Values (Matrix)**

### Morning Fitness Combinations

```
╔═══════════╦════════╦════════╦══════════╗
║ Workout   ║  Low   ║ Medium ║  High    ║
╠═══════════╬════════╬════════╬══════════╣
║ strength  ║ Valid  ║ Valid  ║ Valid    ║
║ cardio    ║ Valid  ║ Valid  ║ Valid    ║
║ yoga      ║ Valid  ║ Valid  ║ Valid    ║
║ rest      ║ Valid  ║ Valid* ║ Valid*   ║
╚═══════════╩════════╩════════╩══════════╝

* Rest is typically "low" intensity only
```

**Sample Valid Combinations (9):**
1. `("strength", "low", 30)`
2. `("strength", "medium", 40)`
3. `("strength", "high", 50)`
4. `("cardio", "low", 20)`
5. `("cardio", "medium", 30)`
6. `("cardio", "high", 45)`
7. `("yoga", "low", 15)`
8. `("yoga", "medium", 20)`
9. `("rest", "low", 0)`

---

### Afternoon Work Combinations

```
╔═════════════╦════════╦════════╦══════════╗
║ Task Type   ║  Low   ║ Medium ║  High    ║
╠═════════════╬════════╬════════╬══════════╣
║ deep_work   ║ Valid  ║ Valid  ║ Valid    ║
║ email       ║ Valid  ║ Valid  ║ Valid    ║
║ support     ║ Valid  ║ Valid  ║ Valid    ║
║ scheduling  ║ Valid  ║ Valid  ║ Valid    ║
║ rest        ║ Valid  ║ Valid* ║ Valid*   ║
╚═════════════╩════════╩════════╩══════════╝

* Rest is typically "low" effort only
```

**Sample Valid Combinations (15):**
1. `("deep_work", "low")`
2. `("deep_work", "medium")`
3. `("deep_work", "high")`
4. `("email", "low")`
5. `("email", "medium")`
6. `("email", "high")`
7. `("support", "low")`
8. `("support", "medium")`
9. `("support", "high")`
10. `("scheduling", "low")`
11. `("scheduling", "medium")`
12. `("scheduling", "high")`
13. `("rest", "low")`
14. `("rest", "medium")`
15. `("rest", "high")`

---

## **Complete JSON Enum Reference**

### Morning: Full Payload Options

```json
{
  "fitness_action": {
    "workout_type": "strength" | "cardio" | "yoga" | "rest",
    "intensity": "low" | "medium" | "high",
    "duration": 0 | 5 | 10 | ... | 120
  }
}
```

**Actual Examples:**
```json
{"fitness_action": {"workout_type": "strength", "intensity": "high", "duration": 45}}
{"fitness_action": {"workout_type": "cardio", "intensity": "medium", "duration": 30}}
{"fitness_action": {"workout_type": "yoga", "intensity": "low", "duration": 20}}
{"fitness_action": {"workout_type": "rest", "intensity": "low", "duration": 0}}
```

---

### Afternoon: Full Payload Options

```json
{
  "work_action": {
    "task_type": "deep_work" | "email" | "support" | "scheduling" | "rest",
    "effort_level": "low" | "medium" | "high"
  }
}
```

**Actual Examples:**
```json
{"work_action": {"task_type": "deep_work", "effort_level": "high"}}
{"work_action": {"task_type": "email", "effort_level": "low"}}
{"work_action": {"task_type": "support", "effort_level": "medium"}}
{"work_action": {"task_type": "scheduling", "effort_level": "low"}}
{"work_action": {"task_type": "rest", "effort_level": "low"}}
```

---

### Evening: Empty Payload

```json
{}
```

---

## **Enum Validation Rules**

| Rule | Valid | Invalid |
|------|-------|---------|
| **Case** | `"strength"` | `"Strength"`, `"STRENGTH"` |
| **Underscores** | `"deep_work"` | `"deepwork"`, `"deep-work"` |
| **Duration Type** | `30` | `"30"`, `30.0` |
| **Duration Range** | `0-120` | `-1`, `121` |
| **Null Values** | Valid (ignored) | N/A |
| **Extra Fields** | Ignored | Validation error |

---

## **Quick Copy-Paste Blocks**

### All Workout Types
```
"strength"
"cardio"
"yoga"
"rest"
```

### All Intensity Levels
```
"low"
"medium"
"high"
```

### All Task Types
```
"deep_work"
"email"
"support"
"scheduling"
"rest"
```

### All Effort Levels
```
"low"
"medium"
"high"
```

### All Valid Durations (Sample)
```
0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 90, 120
```

---

## **Enum Count Summary**

| Category | Count | Options |
|----------|-------|---------|
| WorkoutType | 4 | strength, cardio, yoga, rest |
| IntensityLevel | 3 | low, medium, high |
| Duration Range | 121 | 0, 1, 2, ..., 120 |
| TaskType | 5 | deep_work, email, support, scheduling, rest |
| EffortLevel | 3 | low, medium, high |

**Total Combinations:**
- Morning: 4 × 3 × 121 = 1,452 possible actions
- Afternoon: 5 × 3 = 15 possible actions
- Evening: 1 possible action (empty)
- **Per day: 1,468 different action combinations**

---

## **Decision Matrix: Choose Your Enum Values**

### Morning Decision Helper
```
What's your state?
  Energy LOW    → yoga (low) or rest
  Energy MED    → cardio (med) 
  Energy HIGH   → strength (high)
```

### Afternoon Decision Helper
```
What's your priority?
  Complete tasks → deep_work (high)
  Keep it light  → email (low)
  Help others    → support (med)
  Get organized  → scheduling (low)
  Need break     → rest (low)
```

---

**Use this table as your enum bible!** 📖
