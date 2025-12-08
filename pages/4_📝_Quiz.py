"""
Quiz Page - Interactive quiz generation and tracking with structured output
"""
import streamlit as st
import json
import time
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import List
from utils.db import get_database
from utils.sidebar_utils import show_sidebar_on_all_pages
from utils.helpers import call_llm_structured
from utils.text_extraction import get_topic_text

st.set_page_config(page_title="Quiz", page_icon="📝", layout="wide")

# Show common sidebar on all pages
show_sidebar_on_all_pages()

db = get_database()

# Define Pydantic schemas for structured output
class QuizQuestion(BaseModel):
    """Single quiz question with multiple choice options."""
    model_config = ConfigDict(extra="forbid")  # Enforce additionalProperties: false
    
    text: str = Field(description="The question text")
    options: List[str] = Field(description="List of 4 answer options")
    answer: int = Field(description="Index (0-3) of the correct answer")

class QuizData(BaseModel):
    """Complete quiz with multiple questions."""
    model_config = ConfigDict(extra="forbid")  # Enforce additionalProperties: false
    
    questions: List[QuizQuestion] = Field(description="List of quiz questions")

st.title("📝 Interactive Quiz")

if 'current_notebook' not in st.session_state:
    st.warning("⚠️ No notebook selected. Please upload a PDF from the home page.")
    if st.button("Go to Home"):
        st.switch_page("app.py")
else:
    notebook = db.get_notebook(st.session_state.current_notebook)
    
    if notebook:
        filename = notebook.get('filename', 'Untitled Notebook')
        st.header(f"📓 {filename}")
        
        # Two tabs: Generate New and View Previous
        tab1, tab2 = st.tabs(["➕ Generate & Take Quiz", "📚 View Previous Quizzes"])
        
        with tab1:
            st.markdown("### Generate and Take a Quiz")
            
            # Get topics from notebook
            topics = notebook.get('topics', [])
            
            if not topics:
                st.warning("No topics found in this notebook. Please check your document.")
            else:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    selected_topic = st.selectbox(
                        "Choose a topic to quiz on:",
                        options=topics,
                        key="quiz_topic"
                    )
                
                with col2:
                    num_questions = st.number_input(
                        "Number of questions:",
                        min_value=1,
                        max_value=10,
                        value=5
                    )
                
                # Check for existing quiz on this topic
                existing_quizzes = db.get_quizzes(st.session_state.current_notebook, selected_topic)
                
                if existing_quizzes:
                    st.info(f"✅ {len(existing_quizzes)} quiz(zes) already exist for '{selected_topic}'")
                    if st.button("📝 Use Existing Quiz", key="use_existing"):
                        st.session_state.selected_quiz = existing_quizzes[0]
                        st.session_state.in_quiz = True
                        st.rerun()
                
                if st.button("🎯 Generate New Quiz", type="primary"):
                    with st.spinner(f"Generating {num_questions} questions on '{selected_topic}'..."):
                        try:
                            # Get topic-specific text
                            text_content = notebook.get('text_content', '')
                            cached_embeddings = notebook.get('embeddings')
                            topic_text = get_topic_text(text_content, selected_topic, cached_embeddings=cached_embeddings)
                            
                            # Build prompt for structured output
                            prompt = f"""Based on the following text about '{selected_topic}', generate exactly {num_questions} multiple-choice quiz questions.

Each question should:
- Test understanding of key concepts
- Have 4 distinct answer options
- Have only ONE correct answer
- Be challenging but fair

Text content:
{topic_text[:8000]}

Generate {num_questions} questions now."""
                            
                            # Call Groq with structured output (Pydantic schema)
                            quiz_data = call_llm_structured(prompt, QuizData, model_name="openai/gpt-oss-120b")
                            
                            # Convert Pydantic model to dict for storage
                            quiz_dict = quiz_data.model_dump()
                            
                            # Limit to requested number (safety check)
                            quiz_dict['questions'] = quiz_dict['questions'][:num_questions]
                            
                            # Save quiz to database
                            db.save_quiz(
                                st.session_state.current_notebook,
                                selected_topic,
                                quiz_dict
                            )
                            
                            st.session_state.selected_quiz = quiz_dict
                            st.session_state.current_quiz_id = None  # Will be set from DB
                            st.session_state.in_quiz = True
                            st.session_state.quiz_start_time = time.time()
                            
                            st.success(f"✅ Quiz generated with {len(quiz_dict['questions'])} questions!")
                            st.rerun()
                        
                        except Exception as e:
                            st.error(f"❌ Error generating quiz: {str(e)}")
                            st.exception(e)
        
        # Quiz Taking Interface
        if st.session_state.get('in_quiz', False):
            st.divider()
            st.markdown("### 🎯 Quiz Time!")
            
            quiz_data = st.session_state.get('selected_quiz', {})
            questions = quiz_data.get('questions', [])
            
            if questions:
                # Initialize session state for answers
                if 'user_answers' not in st.session_state:
                    st.session_state.user_answers = [None] * len(questions)
                
                if 'current_question_idx' not in st.session_state:
                    st.session_state.current_question_idx = 0
                
                current_idx = st.session_state.current_question_idx
                question = questions[current_idx]
                
                # Progress bar
                st.progress((current_idx + 1) / len(questions))
                st.caption(f"Question {current_idx + 1} of {len(questions)}")
                
                # Display question
                st.markdown(f"### {question.get('text', 'Question')}")
                
                # Display options as radio buttons
                options = question.get('options', [])
                selected_option = st.radio(
                    "Select your answer:",
                    options=range(len(options)),
                    format_func=lambda i: f"{chr(65 + i)}: {options[i]}",
                    index=st.session_state.user_answers[current_idx] if st.session_state.user_answers[current_idx] is not None else 0,
                    key=f"option_{current_idx}"
                )
                
                # Store answer
                st.session_state.user_answers[current_idx] = selected_option
                
                # Navigation buttons
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    if current_idx > 0:
                        if st.button("⬅️ Previous", use_container_width=True):
                            st.session_state.current_question_idx -= 1
                            st.rerun()
                
                with col2:
                    st.write("")  # Spacer
                
                with col3:
                    if current_idx < len(questions) - 1:
                        if st.button("Next ➡️", use_container_width=True):
                            st.session_state.current_question_idx += 1
                            st.rerun()
                    else:
                        if st.button("✅ Submit Quiz", use_container_width=True, type="primary"):
                            # Calculate score
                            correct_count = 0
                            for idx, user_answer in enumerate(st.session_state.user_answers):
                                correct_answer = questions[idx].get('answer', -1)
                                if user_answer == correct_answer:
                                    correct_count += 1
                            
                            score = (correct_count / len(questions)) * 100
                            time_spent = int(time.time() - st.session_state.get('quiz_start_time', time.time()))
                            
                            # Save attempt to database
                            notebook_id = st.session_state.current_notebook
                            quiz_id = st.session_state.get('current_quiz_id')
                            
                            if quiz_id:
                                db.save_quiz_attempt(
                                    notebook_id,
                                    quiz_id,
                                    st.session_state.user_answers,
                                    score,
                                    time_spent
                                )
                            
                            # Update progress
                            progress = db.get_progress(notebook_id)
                            progress['total_score'] += int(score)
                            db.update_progress(notebook_id, progress)
                            
                            # Show results
                            st.session_state.quiz_results = {
                                'score': score,
                                'correct': correct_count,
                                'total': len(questions),
                                'time_spent': time_spent,
                                'answers': st.session_state.user_answers,
                                'questions': questions
                            }
                            st.session_state.in_quiz = False
                            st.rerun()
        
        # Quiz Results Display
        if st.session_state.get('quiz_results'):
            st.divider()
            results = st.session_state.quiz_results
            
            st.markdown("### 🎉 Quiz Complete!")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Score", f"{results['score']:.1f}%")
            with col2:
                st.metric("Correct", f"{results['correct']}/{results['total']}")
            with col3:
                st.metric("Time Spent", f"{results['time_spent']} sec")
            with col4:
                st.metric("Points Earned", int(results['score']))
            
            # Show detailed results
            st.markdown("### 📋 Detailed Results")
            
            for idx, question in enumerate(results['questions']):
                user_answer = results['answers'][idx]
                correct_answer = question.get('answer', -1)
                is_correct = user_answer == correct_answer
                
                status = "✅" if is_correct else "❌"
                st.markdown(f"{status} **Q{idx + 1}: {question.get('text', '')}'**")
                
                options = question.get('options', [])
                for i, option in enumerate(options):
                    prefix = ""
                    if i == correct_answer:
                        prefix = "✓ (Correct) "
                    if i == user_answer and not is_correct:
                        prefix = "✗ (Your answer) "
                    st.markdown(f"  {chr(65 + i)}: {prefix}{option}")
                
                st.divider()
            
            # Reset button
            if st.button("🔄 Take Another Quiz"):
                st.session_state.in_quiz = False
                st.session_state.quiz_results = None
                st.session_state.user_answers = None
                st.session_state.current_question_idx = 0
                st.rerun()
        
        with tab2:
            st.markdown("### 📚 Previously Generated Quizzes")
            
            # Get all quizzes for this notebook
            all_quizzes = db.get_quizzes(st.session_state.current_notebook)
            
            if not all_quizzes:
                st.info("No quizzes generated yet. Go to 'Generate & Take Quiz' tab to create one!")
            else:
                # Group by topic
                topics_with_quizzes = {}
                for quiz in all_quizzes:
                    topic = quiz.get('topic', 'Unknown')
                    if topic not in topics_with_quizzes:
                        topics_with_quizzes[topic] = []
                    topics_with_quizzes[topic].append(quiz)
                
                # Display quizzes by topic
                for topic, quizzes in topics_with_quizzes.items():
                    st.subheader(f"📌 {topic}")
                    
                    for i, quiz in enumerate(quizzes):
                        num_questions = len(quiz.get('questions', []))
                        num_attempts = len(quiz.get('attempts', []))
                        created_at = quiz.get('created_at', datetime.now()).strftime("%b %d, %Y")
                        
                        with st.expander(f"Quiz #{i+1} - {num_questions} questions (Created: {created_at})"):
                            st.caption(f"**Attempts:** {num_attempts}")
                            
                            # Show questions preview
                            for j, question in enumerate(quiz.get('questions', [])[:3]):  # Show first 3
                                st.markdown(f"**Q{j+1}:** {question.get('text', 'No question')}")
                            
                            if num_questions > 3:
                                st.caption(f"... and {num_questions - 3} more questions")
                            
                            # Button to retake this quiz
                            if st.button(f"📝 Take This Quiz", key=f"retake_quiz_{quiz.get('_id')}"):
                                st.session_state.selected_quiz = quiz
                                st.session_state.in_quiz = True
                                st.session_state.quiz_start_time = time.time()
                                st.rerun()
                    
                    st.divider()
    
    else:
        st.error("Notebook not found!")
        if st.button("Return to Home"):
            st.switch_page("app.py")

