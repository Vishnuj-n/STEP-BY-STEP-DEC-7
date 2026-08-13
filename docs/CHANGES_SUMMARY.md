# ✅ Changes Made (Current State)

## 1) Groq-Powered AI Pipeline
- Swapped Gemini references for Groq (`groq` client, default model `openai/gpt-oss-120b`).
- `call_gemini`/`call_gemini_structured` now route to Groq for summaries, flashcards, scheduler, quiz, mnemonics, and tutor.

## 2) Topic-Aware Extraction via Local ONNX
- `utils/text_extraction.py` + `utils/onnx_embedder.py` use `onnx/model_int8.onnx` (nomic-embed-text-v1.5) to pull topic-relevant slices.
- Fallback keyword extraction keeps pages working if embeddings are missing.
- Used by flashcards, quiz, mnemonics, and Talk to Doc.

## 3) Full-Text Summaries & Faster Subfeatures
- Upload flow now summarizes the **entire** document text (no 10k-char cap).
- Topics still use AI on the first ~8k chars with heuristic backup for resilience.
- Scheduler uses ~8k chars for speed; other generators rely on topic slices.

## 4) Rich Learning Pages
- **Quiz page**: Structured MCQs via Pydantic schema + Groq JSON schema response, scoring, attempts, and progress updates.
- **Talk to Doc**: Socratic tutor with topic-focused context, grading, and optional speech input.
- **Memory Aid Generator**: Acronym, song, phrase, story, or “all mnemonics” in one go.
- **Flashcards**: Study mode + list view; stored per topic with mastery counters.

## 5) Data Model Consolidation
- Single `notebooks` collection embeds schedule, flashcards, quizzes, acronyms, and progress (completed tasks, total score, streaks, mastery, quiz average).
- Sidebar shows “today’s tasks” and a home button; notebooks can be deleted from the sidebar.

## 6) Prompts & Assets
- Prompts expanded beyond core features: `summary`, `topics`, `flashcard`, `scheduler`, `quiz`, `acronym`, `song`, `phrase`, `story`, `all_mnemonics`.
- Local ONNX model expected at `onnx/model_int8.onnx`; requirements include `onnxruntime`, `transformers`, `numpy`.

---

These updates make the app fully functional across all eight pages with Groq-backed generation and local semantic extraction. 🧠🚀

