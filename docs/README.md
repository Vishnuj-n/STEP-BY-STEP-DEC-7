# 🧠 Mind Palace - AI-Powered Learning Platform

An interactive Streamlit app that turns PDFs into full learning notebooks with AI summaries, topic-aware flashcards, quizzes, study plans, mnemonics, progress tracking, and a Socratic tutor.

## 🌟 Features
- **PDF → Notebook pipeline:** upload once, store PDF/text/summary/topics in MongoDB
- **AI Summary:** Groq-hosted `openai/gpt-oss-120b` (default) over full document text
- **Topic Extraction:** AI prompt + heuristic fallback; topic-aware text slicing via local ONNX embeddings
- **Learning tools:** flashcards, quizzes (structured output), study scheduler, progress tracker, memory aids (acronym/song/phrase/story)
- **RAG-style chat:** Socratic “Talk to Doc” with topic-focused context
- **Gamification:** task points, achievements, and sidebar “today’s tasks”

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- MongoDB running locally (`mongodb://127.0.0.1:27017/mind_palace` by default)
- Groq API key (for `groq` client); optional custom model name
- ONNX embedding file at `onnx/model_int8.onnx` (nomic-embed-text-v1.5, int8)

### Installation & Run
```powershell
cd "c:\Users\vishn\PROJECT\STEP BY STEP DEC 7"
pip install -r requirements.txt
```

Create `.env`:
```
GROQ_API_KEY=your_api_key
GROQ_MODELS=openai/gpt-oss-120b    # optional, defaults to this
GROQ_MODEL=openai/gpt-oss-120b     # used on Talk to Duck page
MONGODB_URI=mongodb://127.0.0.1:27017/mind_palace
```

Run:
```powershell
streamlit run app.py
```
Open `http://localhost:8501`.

Download the ONNX embedding model (one-time setup):
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\download_nomic_model.ps1 -InstallDeps
```

## 📁 Project Structure
```
STEP BY STEP DEC 7/
├── app.py                      # Home: upload, notebook list, sidebar tasks
├── pages/
│   ├── 1_📄_Summary.py         # Summary + topics + stats
│   ├── 2_📖_PDF_Viewer.py      # Inline viewer + download
│   ├── 3_🎴_Flashcards.py      # Topic-aware generation + review
│   ├── 4_📝_Quiz.py            # Structured MCQ quizzes + scoring
│   ├── 5_💬_Talk_to_Duck.py     # Socratic tutor with topic context
│   ├── 6_📅_Study_Scheduler.py # Day-by-day plan + task completion
│   ├── 7_🎯_Progress_Tracker.py# Points, achievements, completion %
│   └── 8_🧠_Acronym_Generator.py# Mnemonics (acronym/song/phrase/story/all)
├── utils/
│   ├── db.py                   # Mongo CRUD, embedded flashcards/quizzes/acronyms/progress
│   ├── helpers.py              # Groq client, PDF text extraction, prompt loader
│   ├── text_extraction.py      # Topic-aware extraction via ONNX + fallback
│   ├── onnx_embedder.py        # Nomic embed ONNX wrapper
│   └── sidebar_utils.py        # Shared sidebar renderer
├── prompts/                    # JSON prompt configs (summary, topics, flashcards, scheduler, quiz, mnemonics)
├── scripts/
│   └── download_nomic_model.ps1 # One-command Nomic ONNX model downloader
├── onnx/model_int8.onnx        # Local embedding model (int8)
├── requirements.txt
└── .env                         # Runtime config (Groq + MongoDB)
```

## 🎯 Usage Workflow
1. Upload a PDF → notebook is created with full-text summary + topics.
2. Review **Summary**, then **PDF Viewer** for the source.
3. Generate **Flashcards** or **Quiz** per topic (uses topic-aware text extraction).
4. Build a **Study Schedule** and mark tasks done; **Progress Tracker** updates points/achievements.
5. Use **Memory Aid Generator** for acronyms/songs/phrases/stories or **Talk to Doc** for Socratic Q&A.

## 🔧 Technical Stack
- **Frontend:** Streamlit multipage
- **LLM:** Groq (`groq` client, default `openai/gpt-oss-120b`)
- **Embeddings:** Local ONNX `nomic-embed-text-v1.5` (int8) for topic-aware slicing
- **Database:** MongoDB (single `notebooks` collection with embedded progress/flashcards/quizzes/acronyms)
- **PDF/Text:** PyPDF2 extraction; Base64 PDF storage
- **Infra:** python-dotenv, pydantic for structured quiz responses

## 📝 Prompt Management
Prompts live in `prompts/*.json` with `system_instruction` + `user_instruction`. `helpers.call_gemini` formats placeholders (`{topic}`, `{text}`, `{target_text}`, etc.) and sends context text plus prompt to Groq.

## 🎮 Gamification
- Points: schedule tasks (10–20 pts each) + quiz scores added to total.
- Achievements: 🌱50, 🔥100, ⭐250, 🎓500 points; ✅10 tasks; 🎯50% completion; 💯100% completion.
- Sidebar shows “today’s tasks” when a notebook is selected.

## 🐛 Troubleshooting
- **MongoDB:** ensure `mongod` is running; check `MONGODB_URI`.
- **Groq auth:** verify `GROQ_API_KEY`; adjust model via `GROQ_MODELS`/`GROQ_MODEL`.
- **Embeddings:** confirm `onnx/model_int8.onnx` exists; install `onnxruntime`, `transformers`, `numpy`.
- **PDF text:** encrypted/scanned PDFs may extract empty text; provide selectable text PDFs.

---

**Happy Learning! 🎓**
