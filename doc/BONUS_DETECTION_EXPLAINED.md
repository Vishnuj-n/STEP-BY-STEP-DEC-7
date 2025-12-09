# 🎯 How the Code Identifies Which Tasks Get Bonuses

## Overview
Points are ONLY awarded when completing tasks from the **Study Scheduler** (both in the sidebar "Today's Tasks" and the "Study Scheduler" page). The bonus system automatically detects the task type from the task description and applies the correct class bonus.

---

## 🔍 Task Type Detection Logic

### Step 1: Read the Task Description
When you click to complete a task, the code reads the task's description text.

**Example Task Descriptions:**
- "Complete Talk to Duck session on Photosynthesis"
- "Take a quiz on Chemical Reactions"  
- "Review flashcards for Chapter 5"
- "Write a summary of the introduction"

### Step 2: Match Keywords to Activity Type

The code searches for **keywords** in the task description (case-insensitive) to determine the activity type:

| Keywords Found | Activity Type | Who Gets Bonus |
|----------------|---------------|----------------|
| `talk to duck`, `talk to doc`, `socratic`, `discussion` | `talk_to_duck` | **🎤 Orator** (1.5×) |
| `quiz`, `test`, `exam` | `quiz` | **⚔️ Tactician** (1.5×) |
| `flashcard`, `flash card` | `flashcards` | **📖 Scribe** (1.5×) |
| `summary`, `summarize` | `summaries` | **📖 Scribe** (1.5×) |
| **None of the above** | `scheduler_task` | **📖 Scribe** (1.5×) |

### Step 3: Apply the Correct Bonus

Once the activity type is detected, the code checks the user's Learning Class and applies the bonus if there's a match.

---

## 💻 Code Flow

### **When You Complete a Task:**

```
1. User clicks "✓" on a task
   ↓
2. System reads task description: "Complete Talk to Duck session"
   ↓
3. Detects keywords: "talk to duck" found
   ↓
4. Sets activity_type = 'talk_to_duck'
   ↓
5. Calls apply_class_bonus(notebook_id, 10 points, 'talk_to_duck')
   ↓
6. Checks user's class: Orator
   ↓
7. Orator's multiplier_activities = ['talk_to_duck'] ✓ MATCH!
   ↓
8. Applies bonus: 10 × 1.5 = 15 points
   ↓
9. Saves 15 points to database
```

---

## 📋 Detailed Code Explanation

### **1. Detection in `db.py` (mark_task_complete function)**

```python
# Get the task description to identify the activity type
schedule = notebook.get('schedule', [])
task_description = ""

# Find the specific task by day and index
for day_data in schedule:
    if isinstance(day_data, dict) and day_data.get('day') == day:
        tasks = day_data.get('tasks', [])
        if task_index < len(tasks) and isinstance(tasks[task_index], dict):
            task_description = tasks[task_index].get('description', '').lower()
            break

# Match task description to activity type
activity_type = 'scheduler_task'  # Default

if 'talk to duck' in task_description or 'talk to doc' in task_description:
    activity_type = 'talk_to_duck'
elif 'quiz' in task_description or 'test' in task_description:
    activity_type = 'quiz'
elif 'flashcard' in task_description:
    activity_type = 'flashcards'
elif 'summary' in task_description:
    activity_type = 'summaries'

# Apply class bonus with detected activity type
final_points = apply_class_bonus(notebook_id, points, activity_type)
```

### **2. Visual Detection in Sidebar & Scheduler**

Before displaying the task, the code also detects the type to show the correct bonus preview:

```python
task_desc = task.get('description', 'Task')
task_desc_lower = task_desc.lower()

# Detect activity type
activity_type = 'scheduler_task'

if 'talk to duck' in task_desc_lower:
    activity_type = 'talk_to_duck'
elif 'quiz' in task_desc_lower:
    activity_type = 'quiz'
# ... etc

# Check if bonus applies
will_apply_bonus, final_points, class_name = get_bonus_info(
    notebook_id, 
    task_points, 
    activity_type  # Uses detected type!
)

# Show preview: "~~10~~ 15pts ⭐" if bonus applies
```

---

## 🎮 Examples

### Example 1: Orator Completes "Talk to Duck" Task

**Task:** "Complete Talk to Duck session on Cellular Biology"
**Base Points:** 10

**Detection Flow:**
1. Description: "complete **talk to duck** session on cellular biology"
2. Keyword match: "talk to duck" → `activity_type = 'talk_to_duck'`
3. User's class: Orator
4. Orator bonus activities: `['talk_to_duck']` ✓
5. **Bonus applies!** 10 × 1.5 = **15 points** ⭐

---

### Example 2: Orator Completes "Quiz" Task

**Task:** "Take a quiz on Newton's Laws"
**Base Points:** 20

**Detection Flow:**
1. Description: "take a **quiz** on newton's laws"
2. Keyword match: "quiz" → `activity_type = 'quiz'`
3. User's class: Orator
4. Orator bonus activities: `['talk_to_duck']` ✗
5. **No bonus.** Gets **20 points** (base)

---

### Example 3: Tactician Completes "Quiz" Task

**Task:** "Take a quiz on Newton's Laws"
**Base Points:** 20

**Detection Flow:**
1. Description: "take a **quiz** on newton's laws"
2. Keyword match: "quiz" → `activity_type = 'quiz'`
3. User's class: Tactician
4. Tactician bonus activities: `['quiz']` ✓
5. **Bonus applies!** 20 × 1.5 = **30 points** ⭐

---

### Example 4: Scribe Completes "Read Chapter" Task

**Task:** "Read Chapter 3: Photosynthesis"
**Base Points:** 15

**Detection Flow:**
1. Description: "read chapter 3: photosynthesis"
2. No keywords matched → `activity_type = 'scheduler_task'` (default)
3. User's class: Scribe
4. Scribe bonus activities: `['flashcards', 'summaries', 'scheduler_task']` ✓
5. **Bonus applies!** 15 × 1.5 = **22.5 → 22 points** ⭐

---

## ✅ Summary

### How the Code Knows Which Task Gets Bonus:

1. **Reads the task description** (the text that describes what to do)
2. **Searches for keywords** (talk to duck, quiz, flashcard, summary, etc.)
3. **Assigns an activity type** based on keywords found
4. **Checks user's Learning Class** from database
5. **Compares activity type** to the class's bonus activities list
6. **Applies 1.5× multiplier** if there's a match
7. **Awards base points** if no match

### Key Points:
- ✅ **ALL points come from Study Scheduler tasks only**
- ✅ **Bonus is automatic** - detects task type from description
- ✅ **Works in both** sidebar "Today's Tasks" and Study Scheduler page
- ✅ **Visual indicators** show if bonus will apply before completing task
- ✅ **No manual selection needed** - just complete tasks as usual

---

## 🧪 Testing

To see bonuses in action:

1. **Choose Orator class** on home page
2. **Create a schedule** with tasks like:
   - "Complete Talk to Duck session on Biology" 
   - "Take a quiz on Chemistry"
   - "Read Chapter 5"
3. **Complete the Talk to Duck task** → You'll get **1.5× bonus** ⭐
4. **Complete the quiz task** → You'll get **base points only** (no bonus)
5. **Complete the reading task** → You'll get **base points only** (no bonus)

Switch to **Tactician** and the quiz task will get the bonus instead!
