# 💻 Code Walkthrough: Real Examples

## Example 1: Orator Gets Bonus

### Scenario
- **User's Class:** Orator 🎤
- **Task Description:** "Complete Talk to Duck session on Photosynthesis"
- **Base Points:** 10

### Code Execution

```python
# === STEP 1: RETRIEVE TASK DESCRIPTION ===

notebook = self.get_notebook(notebook_id)
# notebook = {
#     '_id': ObjectId(...),
#     'schedule': [
#         {
#             'day': 1,
#             'tasks': [
#                 {
#                     'description': 'Complete Talk to Duck session on Photosynthesis',
#                     'points': 10
#                 },
#                 { ... more tasks ... }
#             ]
#         },
#         { ... more days ... }
#     ],
#     'progress': { ... }
# }

schedule = notebook.get('schedule', [])
# schedule = [ { 'day': 1, 'tasks': [...] }, ... ]

task_description = ""

# Looking for day=1 (current day)
for day_data in schedule:  # Iterate through days
    if isinstance(day_data, dict) and day_data.get('day') == 1:  # Found day 1!
        # day_data = { 'day': 1, 'tasks': [...] }
        
        tasks = day_data.get('tasks', [])
        # tasks = [
        #     { 'description': 'Complete Talk to Duck...', 'points': 10 },
        #     { ... more tasks ... }
        # ]
        
        if 0 < len(tasks):  # Check if task_index 0 exists
            task_at_index = tasks[0]
            # task_at_index = {
            #     'description': 'Complete Talk to Duck session on Photosynthesis',
            #     'points': 10
            # }
            
            task_description = task_at_index.get('description', '').lower()
            # task_description = 'complete talk to duck session on photosynthesis'
            
            break  # Found task, exit loop
        
# After Step 1:
# task_description = 'complete talk to duck session on photosynthesis'
```

### Step 2: Pattern Matching

```python
# === STEP 2: PATTERN MATCHING (STRING SEARCH) ===

activity_type = 'scheduler_task'  # Default

# Check first IF statement
if 'talk to duck' in task_description or 'talk to doc' in task_description or \
   'socratic' in task_description or 'discussion' in task_description:
    
    # 'talk to duck' in 'complete talk to duck session on photosynthesis'?
    # → YES! Found at position 9 ✓
    
    activity_type = 'talk_to_duck'
    # Rest of elif statements are NOT executed due to 'elif'

# After Step 2:
# activity_type = 'talk_to_duck'
```

### Step 3: Apply Class Bonus

```python
# === STEP 3: APPLY CLASS BONUS ===

final_points = apply_class_bonus(
    notebook_id='60d5ec49c1d2a000001f4a1',
    points=10,
    activity_type='talk_to_duck'
)

# Inside apply_class_bonus():
db = get_database()

learning_class = db.get_user_learning_class(notebook_id)
# Queries database for: progress.learning_class
# Returns: 'Orator'

# learning_class = 'Orator' ✓

class_obj = None
if learning_class == 'Scribe':
    class_obj = LearningClass.SCRIBE
elif learning_class == 'Orator':
    class_obj = LearningClass.ORATOR
    # class_obj = {
    #     'name': '🎤 The Orator',
    #     'description': 'Conversationalist. Gets 1.5x points for Talk to Doc.',
    #     'multiplier_activities': ['talk_to_duck'],
    #     'multiplier': 1.5,
    #     'emoji': '🎤'
    # }
    break

# Check if activity_type matches class bonus activities
if 'talk_to_duck' in class_obj['multiplier_activities']:
    # 'talk_to_duck' in ['talk_to_duck']?
    # → YES! ✓
    
    final_points = int(10 * 1.5)
    # final_points = int(15.0)
    # final_points = 15

    return final_points  # Return 15

# After Step 3:
# final_points = 15
```

### Step 4: Save to Database

```python
# === STEP 4: SAVE TO DATABASE ===

return self.notebooks.update_one(
    {'_id': ObjectId(notebook_id)},
    {
        '$push': {'progress.completed_tasks': '1_0'},  # Mark task as complete
        '$inc': {'progress.total_score': 15},  # ← ADD 15 POINTS (not 10!)
        '$set': {
            'progress.last_activity': datetime.now(),
            'updated_at': datetime.now()
        }
    }
)

# Database Update:
# Before: progress.total_score = 45
# After:  progress.total_score = 45 + 15 = 60

# User sees: "+15 pts" instead of "+10 pts" ⭐
```

### Summary of Example 1

```
FINAL RESULT:
─────────────────────────────────────────────────────────
Input:          10 base points from "Talk to Duck" task
Detection:      Keywords matched → activity_type = 'talk_to_duck'
User Class:     Orator
Bonus Check:    'talk_to_duck' in Orator's activities? YES ✓
Calculation:    10 × 1.5 = 15
Output:         15 points awarded ⭐
─────────────────────────────────────────────────────────
```

---

## Example 2: Scribe Gets Bonus (Different Task)

### Scenario
- **User's Class:** Scribe 📖
- **Task Description:** "Review summary of Chapter 4"
- **Base Points:** 8

### Code Execution (Abbreviated)

```python
# Step 1: Retrieve
task_description = 'review summary of chapter 4'.lower()

# Step 2: Pattern Matching
activity_type = 'scheduler_task'  # Default

if 'talk to duck' in task_description:  # NO
    pass
elif 'quiz' in task_description:  # NO
    pass
elif 'flashcard' in task_description:  # NO
    pass
elif 'summary' in task_description:  # ✓ YES!
    activity_type = 'summaries'

# activity_type = 'summaries'

# Step 3: Apply Bonus
learning_class = 'Scribe'
class_obj = LearningClass.SCRIBE
# class_obj['multiplier_activities'] = ['flashcards', 'summaries', 'scheduler_task']

if 'summaries' in ['flashcards', 'summaries', 'scheduler_task']:  # YES ✓
    final_points = int(8 * 1.5)
    # final_points = 12

# Step 4: Save
# progress.total_score += 12
```

### Result

```
─────────────────────────────────────────────────────────
Input:          8 base points from "Summary" task
Detection:      Keywords matched → activity_type = 'summaries'
User Class:     Scribe
Bonus Check:    'summaries' in Scribe's activities? YES ✓
Calculation:    8 × 1.5 = 12
Output:         12 points awarded ⭐
─────────────────────────────────────────────────────────
```

---

## Example 3: No Bonus (Wrong Class for Task)

### Scenario
- **User's Class:** Tactician ⚔️
- **Task Description:** "Complete Talk to Duck Discussion"
- **Base Points:** 10

### Code Execution

```python
# Step 1: Retrieve
task_description = 'complete talk to duck discussion'.lower()

# Step 2: Pattern Matching
activity_type = 'scheduler_task'

if 'talk to duck' in task_description:  # ✓ YES!
    activity_type = 'talk_to_duck'

# activity_type = 'talk_to_duck'

# Step 3: Apply Bonus
learning_class = 'Tactician'
class_obj = LearningClass.TACTICIAN
# class_obj['multiplier_activities'] = ['quiz']

if 'talk_to_duck' in ['quiz']:  # ✗ NO MATCH
    # This block is skipped
    pass

# No else, so original base_points is returned
return 10  # Return base points unchanged

final_points = 10

# Step 4: Save
# progress.total_score += 10 (no bonus)
```

### Result

```
─────────────────────────────────────────────────────────
Input:          10 base points from "Talk to Duck" task
Detection:      Keywords matched → activity_type = 'talk_to_duck'
User Class:     Tactician
Bonus Check:    'talk_to_duck' in Tactician's activities? NO ✗
Calculation:    10 × 1.0 = 10
Output:         10 points awarded (base only)
─────────────────────────────────────────────────────────
```

---

## Example 4: Generic Task with Default Activity Type

### Scenario
- **User's Class:** Scribe 📖
- **Task Description:** "Read and study the concepts in Chapter 2"
- **Base Points:** 15

### Code Execution

```python
# Step 1: Retrieve
task_description = 'read and study the concepts in chapter 2'.lower()

# Step 2: Pattern Matching
activity_type = 'scheduler_task'  # Default

# Check all conditions
if 'talk to duck' in task_description:  # NO
    pass
elif 'quiz' in task_description:  # NO
    pass
elif 'flashcard' in task_description:  # NO
    pass
elif 'summary' in task_description:  # NO
    pass

# No keywords matched, activity_type stays as default
# activity_type = 'scheduler_task'

# Step 3: Apply Bonus
learning_class = 'Scribe'
class_obj = LearningClass.SCRIBE
# class_obj['multiplier_activities'] = ['flashcards', 'summaries', 'scheduler_task']

if 'scheduler_task' in ['flashcards', 'summaries', 'scheduler_task']:  # ✓ YES!
    final_points = int(15 * 1.5)
    # final_points = 22 (22.5 rounded down to int)

# Step 4: Save
# progress.total_score += 22
```

### Result

```
─────────────────────────────────────────────────────────
Input:          15 base points from generic reading task
Detection:      No keywords found → activity_type = 'scheduler_task' (default)
User Class:     Scribe
Bonus Check:    'scheduler_task' in Scribe's activities? YES ✓
Calculation:    15 × 1.5 = 22.5 → 22 (rounded to int)
Output:         22 points awarded ⭐
─────────────────────────────────────────────────────────
```

---

## Example 5: Old Notebook with Missing Fields

### Scenario
- **Old Notebook:** Created before this update
- **Missing Fields:** Some tasks might not have 'description'
- **Task Structure:** `{ 'points': 10 }` (no description key)
- **Base Points:** 10

### Code Execution

```python
# Step 1: Retrieve
notebook = self.get_notebook(notebook_id)
# Might be from old notebook

schedule = notebook.get('schedule', [])
# If 'schedule' key exists → works fine
# If 'schedule' key missing → returns [] (empty array, safe!)

for day_data in schedule:
    if day_data.get('day') == day:
        tasks = day_data.get('tasks', [])
        # If 'tasks' missing → returns [] (safe!)
        
        if task_index < len(tasks):
            task_description = tasks[task_index].get('description', '')
            # If 'description' missing → returns '' (empty string, safe!)
            # task_description = ''

# Step 2: Pattern Matching
activity_type = 'scheduler_task'

if 'talk to duck' in '':  # Empty string, NO match
    pass
elif 'quiz' in '':  # Empty string, NO match
    pass
# ... all checks fail on empty string ...

# activity_type = 'scheduler_task' (default)

# Step 3: Apply Bonus
if 'scheduler_task' in class_obj['multiplier_activities']:
    # Works the same as Example 4
    final_points = 10 * 1.5 = 15

# Step 4: Save
# progress.total_score += 15
```

### Result

```
─────────────────────────────────────────────────────────
Old Notebook Issue: Missing 'description' field
Graceful Handling: Uses default empty string ''
Pattern Matching: No keywords in empty string
Activity Type:    Falls back to 'scheduler_task'
User Class:       Scribe (for example)
Bonus Applied:    YES (if Scribe)
Calculation:      10 × 1.5 = 15
Output:           15 points awarded ⭐

✓ NO CRASH - Backward compatible!
─────────────────────────────────────────────────────────
```

---

## Key Insights from Code Walkthroughs

### 1. String Search is Smart
```python
if 'talk to duck' in task_description:
```
- Finds substring anywhere in the string
- Case-insensitive (because of .lower())
- Works with extra words before/after the keyword

### 2. Default Protection
```python
activity_type = 'scheduler_task'  # Set BEFORE any checks
```
- Even if all checks fail, activity_type has a safe value
- Never undefined or None

### 3. Safe Data Access
```python
notebook.get('schedule', [])  # Returns [] if key missing
tasks[task_index].get('description', '')  # Returns '' if key missing
```
- Uses `.get()` with defaults
- No KeyError exceptions
- Handles old notebooks gracefully

### 4. One-time Execution
```python
elif ...  # Second check only if first was false
elif ...  # Third check only if first and second were false
```
- Once a keyword is found, remaining checks are skipped
- Efficient and prevents duplicate matches

### 5. Database Integration
```python
final_points = apply_class_bonus(...)  # Returns calculated points
progress['total_score'] += final_points  # Add to database
```
- Calculation happens in-memory
- Only final result saved to database
- No intermediate calculations stored

---

## Visual: Point Calculation Examples

```
Base Points = 10

IF Orator with 'talk_to_duck' task:
  10 → [×1.5] → 15 ⭐

IF Orator with 'quiz' task:
  10 → [×1.0] → 10 (no bonus)

IF Scribe with 'summary' task:
  10 → [×1.5] → 15 ⭐

IF Scribe with 'talk_to_duck' task:
  10 → [×1.0] → 10 (no bonus)

IF Tactician with 'quiz' task:
  10 → [×1.5] → 15 ⭐

IF Tactician with 'summary' task:
  10 → [×1.0] → 10 (no bonus)
```

---

## Backward Compatibility Proof

Old Notebook created months ago:
```json
{
  "schedule": [
    {
      "day": 1,
      "tasks": [
        {
          "description": "Take a Quiz on Biology",
          "points": 20
        }
      ]
    }
  ]
}
```

New code runs on old notebook:
```python
# Step 1: Retrieves the description safely
task_description = "take a quiz on biology".lower()

# Step 2: Finds 'quiz' keyword
activity_type = 'quiz'

# Step 3: Applies bonus based on user's class
# (Tactician gets bonus, others don't)

# Step 4: Saves correct points
# (works exactly as designed)
```

**Result:** ✅ Old notebooks work perfectly!
