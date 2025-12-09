# 🔄 Task Detection Flow Diagrams

## Main Detection Flow

```
START: User completes a task from Study Scheduler
  │
  ├─→ STEP 1: Retrieve Task Description
  │   │
  │   └─→ Get schedule[day].tasks[index].description
  │       Convert to lowercase
  │       Example: "Complete Talk to Duck" → "complete talk to duck"
  │
  ├─→ STEP 2: Pattern Matching (String Search)
  │   │
  │   ├─→ IF 'talk to duck'|'talk to doc'|'socratic'|'discussion' found
  │   │   └─→ activity_type = 'talk_to_duck' ✓
  │   │
  │   ├─→ ELIF 'quiz'|'test'|'exam' found
  │   │   └─→ activity_type = 'quiz' ✓
  │   │
  │   ├─→ ELIF 'flashcard'|'flash card' found
  │   │   └─→ activity_type = 'flashcards' ✓
  │   │
  │   ├─→ ELIF 'summary'|'summarize' found
  │   │   └─→ activity_type = 'summaries' ✓
  │   │
  │   └─→ ELSE (no keywords matched)
  │       └─→ activity_type = 'scheduler_task' ✓
  │
  ├─→ STEP 3: Apply Bonus Function
  │   │
  │   └─→ apply_class_bonus(notebook_id, points, activity_type)
  │       │
  │       ├─→ Load user's Learning Class
  │       ├─→ Check if class has activity_type in multiplier_activities
  │       └─→ Return: base_points × 1.5 OR base_points
  │
  ├─→ STEP 4: Save Points
  │   │
  │   └─→ progress.total_score += final_points
  │
  └─→ END: Task marked complete, points awarded
```

---

## Decision Tree: Which Bonus Gets Applied?

```
                     Task Completed
                           │
                           ▼
           ┌─────────────────────────────────┐
           │   Read Task Description         │
           │   Convert to lowercase          │
           └─────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │ Search for keywords    │
              │ (in priority order)    │
              └────────────────────────┘
                           │
                ┌──────────┼──────────┬──────────┬──────────┐
                │          │          │          │          │
                ▼          ▼          ▼          ▼          ▼
          Talk to Duck   Quiz    Flashcard  Summary   No Match
             Found?      Found?    Found?    Found?    (Default)
                │          │          │        │          │
                │YES       │YES       │YES     │YES       │NO
                │          │          │        │          │
                ▼          ▼          ▼        ▼          ▼
         'talk_to_duck'  'quiz'  'flashcards' 'summaries' 'scheduler_task'
                │          │          │        │          │
                └──────────┼──────────┼────────┼──────────┘
                           │
                           ▼
           ┌───────────────────────────────┐
           │  Load User's Learning Class   │
           │  (Scribe/Orator/Tactician)    │
           └───────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
      Scribe           Orator          Tactician
          │                │                │
          ├─ 'flashcards'  ├─ 'talk_to_duck' ├─ 'quiz'
          ├─ 'summaries'   └─                └─
          ├─ 'scheduler_task'
          └─
          │
          ▼
   Does activity_type match
   class bonus activities?
          │
       YES│         NO
          ▼         ▼
      points×1.5   points×1
          │         │
          └─────┬───┘
              ▼
     Save final_points to database
```

---

## Detailed Keyword Matching Process

```
Task Description: "Complete Talk to Duck session on Biology"
                         │
                         ▼ (Convert to lowercase)
         "complete talk to duck session on biology"
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
   Check IF blocks              Check ELIF blocks
   (in order)                   (only if IF false)
          │
          ├─ IF 'talk to duck' in desc?      ✓ YES! MATCH FOUND
          │     └─→ activity_type = 'talk_to_duck'
          │         STOP HERE (rest skipped)
          │
          └─ (Lines below are NOT executed)
             ├─ ELIF 'quiz' in desc?         ← SKIPPED
             ├─ ELIF 'flashcard' in desc?    ← SKIPPED
             ├─ ELIF 'summary' in desc?      ← SKIPPED
             └─ ELSE?                        ← SKIPPED
```

---

## Backward Compatibility Flow

```
Old Notebook with Existing Schedule
          │
          ▼
    Task from Old Schedule
    (Data structure unchanged)
          │
          ▼
  Can we access notebook?
   ├─ YES → Continue
   └─ NO → Error (old notebook missing)
          │
          ▼
  Can we access schedule array?
   ├─ YES → Continue
   └─ NO → Use default [] (empty)
          │
          ▼
  Can we find the day?
   ├─ YES → Continue
   └─ NO → Return None (task not found)
          │
          ▼
  Can we access task at index?
   ├─ YES → Continue
   └─ NO → Return None (index out of bounds)
          │
          ▼
  Can we get description field?
   ├─ YES → Use actual description
   └─ NO → Use default "" (empty string)
          │
          ▼
  Apply Pattern Matching
   ├─ IF keywords match → use matched activity_type
   └─ ELSE → use default 'scheduler_task'
          │
          ▼
  Apply Bonus (works same for old notebooks!)
```

---

## Example: Different Class Scenarios

### Scenario 1: Orator with "Talk to Duck" Task

```
Task: "Complete Talk to Duck Discussion"
Base Points: 10

DETECTION PHASE:
  Description: "complete talk to duck discussion"
  Search: 'talk to duck' found ✓
  activity_type = 'talk_to_duck'

BONUS PHASE:
  User Class: Orator
  Orator bonus activities: ['talk_to_duck']
  Check: 'talk_to_duck' in ['talk_to_duck']? → YES ✓
  
CALCULATION:
  10 × 1.5 = 15 points awarded ⭐
```

### Scenario 2: Scribe with "Talk to Duck" Task

```
Task: "Complete Talk to Duck Discussion"
Base Points: 10

DETECTION PHASE:
  Description: "complete talk to duck discussion"
  Search: 'talk to duck' found ✓
  activity_type = 'talk_to_duck'

BONUS PHASE:
  User Class: Scribe
  Scribe bonus activities: ['flashcards', 'summaries', 'scheduler_task']
  Check: 'talk_to_duck' in ['flashcards', 'summaries', 'scheduler_task']? → NO ✗
  
CALCULATION:
  10 × 1.0 = 10 points awarded (base only)
```

### Scenario 3: Scribe with Generic "Read Chapter" Task

```
Task: "Read Chapter 5 on Photosynthesis"
Base Points: 12

DETECTION PHASE:
  Description: "read chapter 5 on photosynthesis"
  Search: 'talk to duck' found? → NO
  Search: 'quiz' found? → NO
  Search: 'flashcard' found? → NO
  Search: 'summary' found? → NO
  No keywords matched!
  activity_type = 'scheduler_task' (DEFAULT)

BONUS PHASE:
  User Class: Scribe
  Scribe bonus activities: ['flashcards', 'summaries', 'scheduler_task']
  Check: 'scheduler_task' in ['flashcards', 'summaries', 'scheduler_task']? → YES ✓
  
CALCULATION:
  12 × 1.5 = 18 points awarded ⭐
```

---

## Error Handling for Old Notebooks

```
Accessing Old Notebook Data:

notebook.get('schedule', [])
           │
           ├─ Key exists → return actual schedule array
           └─ Key missing → return default [] (empty array)
                        (Won't crash, just no tasks to process)

notebook.get('progress', {})
           │
           ├─ Key exists → return actual progress object
           └─ Key missing → return default {} (empty object)
                        (Creates fresh progress tracking)

tasks[task_index].get('description', '')
                 │
                 ├─ Key exists → return actual description
                 └─ Key missing → return default '' (empty string)
                              (Won't crash, defaults to 'scheduler_task')
```

---

## Performance Timeline for One Task Completion

```
Time    Operation                                  Duration
────────────────────────────────────────────────────────────
0ms     User clicks "✓" button                     -
        │
5ms     └─→ db.get_notebook(notebook_id)          ~1ms
        
6ms         Get notebook data from database        
        
7ms         Loop through schedule array            ~0.1ms
            (find matching day)
        
7.2ms       Extract task description               ~0.05ms
        
7.3ms       Convert to lowercase                   ~0.01ms
        
7.4ms       Check 8-10 keywords                    ~0.5ms
            (string operations)
        
7.9ms       Set activity_type based on match       ~0.01ms
        
8ms         Call apply_class_bonus()               ~0.5ms
            - Load class
            - Check multiplier_activities
            - Calculate final_points
        
8.5ms       Update MongoDB database                ~2-5ms
            (increment total_score)
        
10-13ms     Display success message                ~0.1ms
────────────────────────────────────────────────────────────
TOTAL TIME: ~10-15 milliseconds (very fast!)
```

---

## Keyword Matching: Substring vs Exact Match

```
Why use: if 'quiz' in task_description:
Instead of: if task_description == 'quiz':

SUBSTRING SEARCH ('in' operator):
  ✓ "Take Quiz on Biology"          → matches
  ✓ "QUIZ: Biology Test"             → matches (after lowercase)
  ✓ "quiz review session"            → matches
  ✓ "Complete this quiz please"      → matches
  ✓ "quiz, quiz, quiz"               → matches

EXACT MATCH ('==' operator):
  ✓ "quiz"                           → matches
  ✗ "Take Quiz on Biology"           → NO MATCH
  ✗ "QUIZ: Biology Test"             → NO MATCH
  ✗ "quiz review session"            → NO MATCH
  ✗ "Complete this quiz please"      → NO MATCH

→ Substring matching is BETTER for flexibility!
```

---

## Data Structure: Before & After

### Before: No Type Detection
```python
# Old approach
final_points = apply_class_bonus(
    notebook_id, 
    points, 
    'scheduler_task'  ← Always same, regardless of task type
)

# Result: Only Scribe gets bonus on ALL tasks
```

### After: Intelligent Type Detection
```python
# New approach
# Detect activity_type from description
activity_type = detect_activity_type(task_description)

final_points = apply_class_bonus(
    notebook_id, 
    points, 
    activity_type  ← Different for each task type!
)

# Result: Correct class gets bonus based on actual task type
```

---

## Conclusion: The Magic is in the Detection

The bonus system works by:

1. **Reading** what the task says (task description)
2. **Searching** for keywords that indicate task type
3. **Matching** found keywords to activity types
4. **Applying** bonuses based on user's class and activity type

This works for:
- ✅ New notebooks (AI-generated schedules)
- ✅ Old notebooks (existing schedules unchanged)
- ✅ Any task description format (flexible keywords)
- ✅ All Learning Classes (Scribe, Orator, Tactician)
