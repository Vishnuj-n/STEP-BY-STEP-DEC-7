# 🧠 Mind Palace - Quick Reference Guide

## 🚀 Launch
```powershell
streamlit run app.py
```

## ⬇️ Download ONNX Model (One-time)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\download_nomic_model.ps1 -InstallDeps
```

## 📋 Project Overview
Mind Palace converts PDFs into interactive study notebooks with AI summaries, topic-aware flashcards/quizzes, mnemonics, study plans, and a Socratic tutor.

### Key Features
- ✅ 8 fully functional pages (summary, viewer, flashcards, quiz, talk to doc, scheduler, progress, mnemonics)
- ✅ AI generation via Groq (`openai/gpt-oss-120b` by default)
- ✅ Local ONNX topic-aware extraction (nomic-embed-text-v1.5 int8)
- ✅ MongoDB persistence (single `notebooks` collection with embedded progress/flashcards/quizzes/acronyms)
- ✅ Gamified learning (points + achievements)

## 📂 File Structure (high level)
```
app.py
pages/1_📄_Summary.py ... 8_🧠_Acronym_Generator.py
utils/db.py, helpers.py, text_extraction.py, onnx_embedder.py, sidebar_utils.py
prompts/*.json (summary, topics, flashcards, scheduler, quiz, mnemonics)
onnx/model_int8.onnx
```

## 🎯 Usage Workflow
1️⃣ Upload PDF → summary + topics generated (full text)  
2️⃣ Explore via sidebar:
- **Summary:** summary, topics, stats
- **PDF Viewer:** inline view + download
- **Flashcards:** topic-aware generation + study/list modes
- **Quiz:** structured MCQs per topic with scoring
- **Study Scheduler:** day-by-day tasks, mark complete
- **Progress Tracker:** points, achievements, completion %
- **Memory Aid Generator:** acronym/song/phrase/story/all
- **Talk to Doc:** Socratic tutor using topic-focused context

3️⃣ Complete tasks & quizzes → points update in Progress Tracker and sidebar “today’s tasks”.

## 🏆 Achievement Milestones
| Achievement | Requirement | Icon |
|------------|-------------|------|
| Getting Started | 50 points | 🌱 |
| On a Roll | 100 points | 🔥 |
| Dedicated Learner | 250 points | ⭐ |
| Master Student | 500 points | 🎓 |
| Task Master | 10 tasks | ✅ |
| Halfway There | 50% complete | 🎯 |
| Perfect Score | 100% complete | 💯 |

## 🔧 Customization
- **Prompts:** edit JSON under `prompts/` (supports `{topic}`, `{text}`, `{target_text}` placeholders).
- **Models:** override via `.env` (`GROQ_MODELS`, `GROQ_MODEL`); replace `onnx/model_int8.onnx` if you want a different embedding variant.

## 🐛 Common Issues
- **MongoDB:** ensure `mongod` is running; check `MONGODB_URI`.
- **Groq key:** set `GROQ_API_KEY`; choose model if needed.
- **Embeddings:** keep `onnx/model_int8.onnx` present; install `onnxruntime`, `transformers`, `numpy`.
- **PDF text:** scanned/encrypted PDFs may not extract text—use selectable-text PDFs.

## 📝 Notes
- Summary uses full document text; topics use AI+heuristic; scheduler uses the first ~8k chars for speed.
- Flashcards/quiz/tutor use topic-aware text slices via ONNX embeddings.
- Session state keeps flashcards/quiz/tutor context in-browser.

## 🎓 Best Practices
1. Upload well-structured PDFs for best extraction.  
2. Generate schedule early so points/achievements track instantly.  
3. Use topic-aware flashcards/quiz before Talk to Doc for focused practice.  
4. Regenerate mnemonics if a style doesn’t fit—song/phrase/story options exist.  
5. Clear Streamlit cache if prompts/models change (`streamlit cache clear`).  

---

**Enjoy your learning journey! 🧠✨**
