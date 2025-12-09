# 🧠 Topic-Aware Text Extraction (Local ONNX)

## Overview
Mind Palace extracts topic-specific context with a **local ONNX embedding model** (nomic-embed-text-v1.5, int8). This replaces the old “first 8k characters” heuristic and avoids external embedding APIs.

## 🚀 What Changed
**Before:** `text_content[:8000]` regardless of topic.  
**Now:** Semantic similarity over sentences → top relevant chunks per topic (up to ~8k chars).

```python
from utils.text_extraction import get_topic_text
topic_text = get_topic_text(full_text, topic="Cell Biology")
```

## 📦 How It Works
1) Split text into sentences.  
2) Embed sentences with ONNX (`search_document:` prefix) + embed the topic query (`search_query:`).  
3) Cosine similarity to rank sentences.  
4) Take top 20 (ordered) with local context to build a coherent excerpt.  
5) Return the first ~8k chars.

Model/loader lives in `utils/onnx_embedder.py` and expects `onnx/model_int8.onnx`.

## 🤖 Model Details
- **Model:** `nomic-embed-text-v1.5` (int8 ONNX)
- **Runtime:** `onnxruntime` (CPU)
- **Tokenizer:** `transformers` AutoTokenizer (downloaded once)
- **Footprint:** ~22 MB model file (already placed under `onnx/`)
- **Cost:** Free / offline after first tokenizer download

## 📍 Where It’s Used
- **Flashcards:** topic-aware context before Groq generation.  
- **Quiz:** targeted text for structured MCQs.  
- **Mnemonics:** better acronyms/songs/phrases/stories per topic.  
- **Talk to Doc:** Socratic tutor pulls focused context.

## 🔄 Fallback Strategy
If embeddings fail or model is missing:
```python
_simple_keyword_extraction(text, topic)
```
Returns a keyword-centered window or the first `max_length` chars so pages keep working.

## 🛠️ Installation Notes
Dependencies already listed in `requirements.txt`:
```
onnxruntime
numpy
transformers
scikit-learn
nltk
```
Ensure `onnx/model_int8.onnx` exists; if you swap models, update the path in `onnx_embedder.py`.

## 🎯 Benefits
- Topic-focused prompts → better flashcards/quizzes/mnemonics/chat
- Offline, no extra API cost
- Consistent performance (<1s for ~50k chars on CPU)
- Graceful degradation via keyword fallback

## 🧪 Quick Check
```python
from utils.text_extraction import get_topic_text
text = open("sample.txt").read()
print(get_topic_text(text, "Neural Networks")[:500])
```
If this returns relevant text, ONNX extraction is ready. 🧠✨
