# 📊 PDF Summary Analysis: Full Text vs Limited Context

## Current Implementation
- Summary uses **full document text** with Groq (`call_gemini`), so users already get complete coverage.
- Topics use AI on the first ~8k chars with a heuristic fallback (fast).
- Scheduler uses the first ~8k chars for speed; flashcards/quiz/chat use topic-aware slices via ONNX.

## Full Text vs Truncated Requests
| Aspect | Truncated (~8–10k chars) | Full Text |
|--------|--------------------------|-----------|
| Coverage | Early pages only | Whole document |
| Quality | Risk of bias / missing sections | Complete + balanced |
| Speed | Faster | Slightly slower (still acceptable) |
| Cost | Lower tokens | Higher tokens but modest |

### When Full Text Shines
- Summaries and high-level overviews
- Multi-chapter books where key material is later
- Study plans that need full scope

### When Limited Can Be Acceptable
- Quick previews or rapid prototyping
- Very large PDFs where latency matters more than completeness

## Recommended Strategy (what the app does now)
- **Summary:** full text (best accuracy).  
- **Topics:** AI on first ~8k + heuristic fallback for resilience.  
- **Flashcards/Quiz/Tutor:** topic-aware slices via ONNX → targeted, small prompts.  
- **Scheduler:** first ~8k for quick generation; regenerate if plan feels too shallow.  

## Practical Notes
- Groq `openai/gpt-oss-120b` handles large prompts; still keep prompts concise.
- ONNX topic slicing keeps generation focused and cheap.
- If a summary looks off, verify the PDF text was extracted (scanned PDFs may be empty).

**Bottom line:** Keep summaries on full text, keep interactive features on targeted slices, and only truncate when speed/size is critical. 🚀
