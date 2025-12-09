"""
Doc Page - Talk to the Doc (Socratic Tutor)
Uses Groq AI for Socratic questioning and grading with RAG context.
"""
import streamlit as st
import json
import io
import os
from utils.db import get_database
from utils.sidebar_utils import show_sidebar_on_all_pages
from utils.text_extraction import get_topic_text
from utils.helpers import client  # Importing the Groq client from helpers
import dotenv



# Optional: Speech Recognition for voice input
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False

st.set_page_config(page_title="Talk to Doc", page_icon="💬", layout="wide")

# Show common sidebar on all pages
show_sidebar_on_all_pages()

db = get_database()

# --- Helper Functions ---

def transcribe_audio(audio_bytes):
    """Transcribe audio using SpeechRecognition."""
    if not SPEECH_AVAILABLE:
        return "Error: SpeechRecognition library not installed."
    
    try:
        recognizer = sr.Recognizer()
        # Convert audio bytes to AudioFile
        with sr.AudioFile(io.BytesIO(audio_bytes.getvalue())) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            return text
    except Exception as e:
        return ""

def generate_tutor_response(messages, topic, context_text=""):
    """
    Generate the next question using Groq (Socratic method).
    """
    system_prompt = f"""You are a friendly Socratic tutor named 'Duck'. 
    Your goal is to help the student understand the topic: "{topic}".
    
    Rules:
    1. Ask ONE thought-provoking question at a time.
    2. Do NOT give long lectures. Keep it conversational.
    3. If the student answers correctly, praise them briefly and ask a deeper follow-up.
    4. If the student is wrong or stuck, give a hint based on the provided context, then ask a simpler question.
    5. Use the provided Context to ensure your questions are relevant to their specific document.

    Context from Document:
    {context_text[:2000] if context_text else "No specific context available."}
    """

    try:
        # Prepare messages for Groq
        api_messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (last 6 messages to save context window)
        for msg in messages[-6:]:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

        completion = client.chat.completions.create(
            messages=api_messages,
            model=os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b'), # Default to a good model
            temperature=0.7,
            max_tokens=250
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"🦆 *Quack* (Error generating response: {str(e)})"

def grade_student_answer(question, answer, topic, context_text):
    """
    Grade the answer and provide structured feedback.
    """
    grading_prompt = f"""You are grading a student's answer.
    
    Topic: {topic}
    Question: {question}
    Student Answer: {answer}
    
    Reference Material:
    {context_text[:1500] if context_text else "N/A"}
    
    Output ONLY valid JSON with this structure:
    {{
        "score": (number 0-10),
        "feedback": "1-2 sentence feedback",
        "correction": "Correction if needed, otherwise null"
    }}
    """
    
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a strict but fair grader. Output JSON only."},
                {"role": "user", "content": grading_prompt}
            ],
            model="openai/gpt-oss-120b",
            response_format={"type": "json_object"},
            temperature=0.3
        )
        return json.loads(completion.choices[0].message.content)
    except Exception:
        # Fallback if JSON fails
        return {"score": 5, "feedback": "Good effort!", "correction": None}

# --- Main UI ---

st.title("💬 Talk to Doc - Socratic Tutor")

if 'current_notebook' not in st.session_state:
    st.warning("⚠️ No notebook selected. Please upload a PDF from the home page.")
    if st.button("Go to Home"):
        st.switch_page("app.py")
    st.stop()

# Load Notebook Data
notebook = db.get_notebook(st.session_state.current_notebook)
if not notebook:
    st.error("Notebook not found!")
    st.stop()

filename = notebook.get('filename', 'Untitled')
st.header(f"📓 {filename}")

# --- Session State Initialization ---
if 'duck_messages' not in st.session_state:
    st.session_state.duck_messages = []
if 'duck_topic' not in st.session_state:
    st.session_state.duck_topic = None
if 'duck_score_history' not in st.session_state:
    st.session_state.duck_score_history = []
if 'last_processed_input' not in st.session_state:
    st.session_state.last_processed_input = None

# --- Topic Selection ---
topics = notebook.get('topics', [])
if not topics:
    st.info("No topics found. Please generate a summary first.")
    st.stop()

col1, col2 = st.columns([3, 1])
with col1:
    selected_topic = st.selectbox(
        "Choose a topic to practice:", 
        topics, 
        index=0 if not st.session_state.duck_topic else None,
        key="topic_selector"
    )

with col2:
    if st.button("🦆 Start Session", type="primary", use_container_width=True):
        st.session_state.duck_topic = selected_topic
        st.session_state.duck_messages = []
        st.session_state.duck_score_history = []
        st.session_state.last_processed_input = None  # Reset input tracking
        
        # Generate First Question
        with st.spinner("Duck is thinking..."):
            # Get semantic context for the topic
            cached_embeddings = notebook.get('embeddings')
            context = get_topic_text(notebook.get('text_content', ''), selected_topic, cached_embeddings=cached_embeddings)
            initial_q = generate_tutor_response([], selected_topic, context)
            
            st.session_state.duck_messages.append({
                "role": "assistant", 
                "content": initial_q
            })
        st.rerun()

st.divider()

# --- Chat Interface ---
if not st.session_state.duck_messages:
    st.info("👆 Select a topic and click 'Start Session' to begin!")
else:
    # 1. Scoreboard
    scores = st.session_state.duck_score_history
    if scores:
        avg_score = sum(scores) / len(scores)
        cols = st.columns(4)
        cols[0].metric("Average Score", f"{avg_score:.1f}/10")
        cols[1].metric("Questions Answered", len(scores))
        
    # 2. Chat History
    chat_container = st.container(height=400)
    for msg in st.session_state.duck_messages:
        with chat_container.chat_message(msg["role"], avatar="🦆" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])
            # If there's feedback metadata attached to a user message (stored in next assistant msg usually, but here handled simpler)
            
    # 3. Input Area
    st.markdown("### 🎤 Your Answer")
    
    # Audio Input
    audio_val = st.audio_input("Record your answer")
    
    # Text Input (Fallback)
    text_val = st.chat_input("Or type your answer here...")

    # Handle Input
    user_input = None
    if audio_val:
        if not SPEECH_AVAILABLE:
            st.error("❌ `SpeechRecognition` library is not installed. Please add it to requirements.txt")
        else:
            with st.spinner("🎧 Transcribing..."):
                transcribed = transcribe_audio(audio_val)
                if transcribed:
                    user_input = transcribed
                else:
                    st.warning("Could not understand audio.")
    
    if text_val:
        user_input = text_val

    # Process Submission - only if it's new input
    if user_input and user_input != st.session_state.last_processed_input:
        # Mark this input as processed
        st.session_state.last_processed_input = user_input
        
        # Append User Message
        st.session_state.duck_messages.append({"role": "user", "content": user_input})
        
        # Get Context for Grading/Next Question
        cached_embeddings = notebook.get('embeddings')
        context = get_topic_text(notebook.get('text_content', ''), st.session_state.duck_topic, cached_embeddings=cached_embeddings)
        
        # Find the last ACTUAL question (not grading feedback) asked by the Duck
        last_question = "Explain the topic."
        for m in reversed(st.session_state.duck_messages[:-1]):
            if m["role"] == "assistant" and not m["content"].startswith("**Grade:"):
                last_question = m["content"]
                break
        
        with st.spinner("🤔 Duck is grading..."):
            # Grade Answer
            grade_result = grade_student_answer(last_question, user_input, st.session_state.duck_topic, context)
            
            score = grade_result.get("score", 0)
            feedback = grade_result.get("feedback", "")
            
            st.session_state.duck_score_history.append(score)
            
            # Formulate Feedback Message - mark it distinctly so we can skip it when finding questions
            feedback_msg = f"""**Grade: {score}/10** *{feedback}*"""
            
            st.session_state.duck_messages.append({"role": "assistant", "content": feedback_msg})

        with st.spinner("🦆 Duck is thinking of the next question..."):
            # Generate Next Question
            next_q = generate_tutor_response(st.session_state.duck_messages, st.session_state.duck_topic, context)
            st.session_state.duck_messages.append({"role": "assistant", "content": next_q})
            
        st.rerun()