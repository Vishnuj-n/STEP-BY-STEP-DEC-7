# 🧠 Mind Palace - Architecture & Logic Guide

## 📍 Data Model (MongoDB)
Single collection: **`notebooks`**
```javascript
{
  _id: ObjectId,
  filename: String,
  pdf_content: String,   // Base64 PDF
  text_content: String,  // Extracted via PyPDF2
  summary: String,       // Full-text Groq summary
  topics: [String],      // AI + heuristic fallback
  schedule: [ { day, tasks: [ {description, points} ] } ],
  schedule_days: Number,
  flashcards: [ { _id, topic, question, answer, difficulty, ... } ],
  quizzes: [ { _id, topic, questions, attempts } ],
  acronyms: [ { _id, topic, type, content, explanation, usefulness_rating } ],
  progress: {
    completed_tasks: [ "1_0", "1_1", ... ],
    total_score: Number,
    last_activity: Date,
    topic_mastery: Object,
    quiz_average: Number,
    study_streak: Number
  },
  created_at: Date,
  updated_at: Date
}
```

## 🔄 End-to-End Flow
### 1) Upload & Ingest (`app.py`)
```
User uploads PDF
  → extract text (PyPDF2)
  → Base64 encode PDF for storage
  → summary = call_gemini(summary_prompt, full text)
  → topics = AI (topics_prompt on first ~8k chars) with heuristic fallback
  → save notebook in MongoDB
```

### 2) Navigation & State
- Sidebar lists notebooks, deletes, and shows “today’s tasks”.
- `st.session_state.current_notebook` drives all pages.

### 3) Feature Workflows
**Summary:** show summary, topics, word/char counts.  
**PDF Viewer:** decode Base64 → iframe + download.  
**Flashcards:** topic-aware slice via ONNX (`get_topic_text`) → Groq flashcard prompt → stored in DB; study or list mode.  
**Quiz:** topic-aware slice → structured Groq response (Pydantic schema) → stored quiz + attempts; scores added to progress.  
**Study Scheduler:** prompt with first ~8k chars → JSON tasks → saved; tasks can be marked complete (points).  
**Progress Tracker:** computes totals, completion %, achievements, recent activity from `progress` + `schedule`.  
**Memory Aid Generator:** acronym/song/phrase/story/all via prompts; uses topic-aware context when a topic is chosen.  
**Talk to Doc:** Socratic tutor; context from `get_topic_text`; Groq models ask/grade; supports text or optional speech input.

## 🔌 Groq / Prompt Pipeline
```
load_prompt(prompt_file)
format user_instruction with {topic}/{text}/{target_text}/kwargs
full_prompt = user_instruction + "\n\nCONTENT:\n" + context_text (if provided)
messages = [system_instruction?, user: full_prompt]
groq.chat.completions.create(model=GROQ_MODELS or GROQ_MODEL)
parse text or JSON (parse_json_response or Pydantic validation)
```
- Default model: `openai/gpt-oss-120b` (configurable via `.env`).
- Structured quizzes use `call_gemini_structured` with JSON schema enforcement.

## 🧭 Topic-Aware Extraction (Local ONNX)
- `utils/text_extraction.py` uses ONNX `nomic-embed-text-v1.5` (int8) via `onnxruntime`.
- Steps: split text → embed sentences (`search_document:`) + query (`search_query:`) → cosine similarity → top sentences (dedup, ordered) → join up to `max_length` (default 8k).
- Fallback: keyword window around topic when embeddings unavailable.
- Used by flashcards, quiz, mnemonics, Talk to Doc.

## 🔐 Session State
```python
st.session_state = {
  current_notebook,
  flashcards, selected_topic, current_card_index, show_answer,
  in_quiz, selected_quiz, user_answers, current_question_idx,
  generator_result/type/concept (mnemonics),
  duck_messages/topic/score_history (Talk to Doc),
  current_study_day
}
```
Keeps context across page navigations without re-fetching.

## ⚙️ Performance & Limits
- Summary uses full text; topics use first ~8k chars for speed.
- Scheduler uses first ~8k chars; flashcards/quiz/tutor use targeted slices.
- ONNX model must exist at `onnx/model_int8.onnx`; load is local/CPU.
- Large PDFs inflate Base64 size; extraction still requires readable text (not scanned).

## 🔧 Common Operations
```python
# Save notebook
db.save_notebook(filename, pdf_b64, text, summary, topics)

# Add flashcards
db.add_flashcards(notebook_id, topic, cards_list)

# Mark task complete
db.mark_task_complete(notebook_id, day, idx, points)

# Save quiz + attempt
db.save_quiz(notebook_id, topic, quiz_dict)
db.save_quiz_attempt(notebook_id, quiz_id, user_answers, score, time_spent)
```

---

This reflects the current Groq-backed, ONNX-enhanced architecture. Enjoy building!
