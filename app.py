"""
Mind Palace - AI-Powered Learning Platform
Main application entry point
"""
import streamlit as st
import base64
import json
from utils.db import Database
from utils.helpers import extract_text_from_pdf, load_prompt, call_gemini
from utils.sidebar_utils import display_todays_tasks_sidebar
from utils.text_extraction import split_into_sentences, compute_embeddings

# Page configuration
st.set_page_config(
    page_title="Study AI - Home",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
db = Database()

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #4A90E2;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .notebook-card {
        padding: 1.5rem;
        border-radius: 10px;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    # Header
    if 'current_notebook' not in st.session_state:
        st.markdown('<div class="main-header">🧠 Mind Palace</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Your AI-Powered Learning Companion</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="sub-header">📚 My Learning Notebooks</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        if 'current_notebook' in st.session_state:
            st.header("📚 My Notebooks")
        else:
            st.header("🏠 Home")
        
        # Get all notebooks
        notebooks = db.get_all_notebooks()
        
        if notebooks:
            for notebook in notebooks:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        # Get filename safely
                        filename = notebook.get('filename', 'Untitled Notebook')
                        display_name = filename[:30] + "..." if len(filename) > 30 else filename
                        
                        if st.button(
                            display_name,
                            key=f"nb_{notebook['_id']}",
                            use_container_width=True
                        ):
                            st.session_state.current_notebook = str(notebook['_id'])
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_{notebook['_id']}"):
                            db.delete_notebook(str(notebook['_id']))
                            if 'current_notebook' in st.session_state:
                                del st.session_state.current_notebook
                            st.rerun()
        else:
            st.info("No notebooks yet. Upload a PDF to get started!")
        
        st.divider()
        
        # Today's Tasks Section (if notebook is selected)
        if 'current_notebook' in st.session_state:
            #display_todays_tasks()
            display_todays_tasks_sidebar()
            st.divider()
        
        if st.button("🏠 Home", use_container_width=True):
            if 'current_notebook' in st.session_state:
                del st.session_state.current_notebook
            st.rerun()
    
    # Main content area
    if 'current_notebook' in st.session_state:
        display_notebook_info()
    else:
        display_upload_section()
def display_upload_section():
    """Display the PDF upload section."""
    st.header("📤 Create New Notebook")
    
    st.markdown("""
    Welcome to Mind Palace! Upload a PDF document to create an interactive learning notebook.
    
    Your notebook will include:
    - 📄 **Summary** - AI-generated overview and key topics
    - 📖 **PDF Viewer** - View your original document
    - 🎴 **Flashcards** - Topic-based Q&A cards
    - 📝 **Quiz** - Test your knowledge (coming soon)
    - 💬 **Talk to Doc** - Chat with your document (coming soon)
    - 📅 **Study Scheduler** - Personalized learning plan
    - 🎯 **Progress Tracker** - Gamified learning with points
    - 🧠 **Acronym Generator** - Memory aids and mnemonics
    """)
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload a PDF document to create your learning notebook"
    )
    
    if uploaded_file is not None:
        with st.spinner("🔄 Processing your PDF..."):
            try:
                # Extract text from PDF
                text_content = extract_text_from_pdf(uploaded_file)
                
                # Reset file pointer for storage
                uploaded_file.seek(0)
                pdf_bytes = uploaded_file.read()
                pdf_base64 = base64.b64encode(pdf_bytes).decode()
                
                # Generate summary and topics using Gemini
                st.info("🤖 Generating summary and extracting key topics...")
                prompt_config = load_prompt('summary_prompt.json')
                summary_response = call_gemini(prompt_config, text_content)  # Use full text for complete summary
                
                # Parse the summary (assuming it returns summary and topics)
                # For now, we'll store the whole response as summary
                # and extract topics as the first 5 headings or sections
                topics = extract_topics_from_text(text_content)
                
                # Compute embeddings for semantic search (cache in database)
                st.info("🔍 Computing embeddings for semantic search...")
                embeddings_data = compute_embeddings(text_content)
                
                # Save to database
                notebook_id = db.save_notebook(
                    filename=uploaded_file.name,
                    pdf_content=pdf_base64,
                    text_content=text_content,
                    summary=summary_response,
                    topics=topics,
                    embeddings=embeddings_data
                )
                
                st.success(f"✅ Notebook created successfully!")
                st.session_state.current_notebook = notebook_id
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error processing PDF: {str(e)}")
                st.exception(e)

def extract_topics_from_text(text):
    """
    Extract topics from text using AI-based extraction.
    Falls back to heuristic if AI fails.
    """
    # Try AI-based extraction first
    try:
        prompt_config = load_prompt('topics_prompt.json')
        response = call_gemini(prompt_config, text[:8000])
        
        # Parse JSON response
        topics = json.loads(response.strip())
        if isinstance(topics, list) and len(topics) > 0:
            return topics[:10]
    except Exception as e:
        # Log error but don't fail - use heuristic fallback
        print(f"AI topic extraction failed: {e}")
    
    # Fallback: heuristic-based extraction
    return extract_topics_heuristic(text)

def extract_topics_heuristic(text):
    """Fallback: Extract topics using simple heuristic (line filtering)."""
    lines = text.split('\n')
    topics = []
    
    for line in lines:
        line = line.strip()
        # Look for short lines that might be headings
        if line and len(line) < 100 and len(line) > 5:
            # Check if it's not all uppercase or all lowercase
            if not line.isupper() and not line.islower():
                topics.append(line)
        
        if len(topics) >= 10:
            break
    
    # If we didn't find enough, create generic topics
    if len(topics) < 5:
        topics = [
            "Introduction and Overview",
            "Main Concepts",
            "Key Principles",
            "Applications",
            "Conclusion and Summary"
        ]
    
    return topics[:10]

def display_notebook_info():
    """Display information about the current notebook."""
    notebook = db.get_notebook(st.session_state.current_notebook)
    
    if notebook:
        filename = notebook.get('filename', 'Untitled Notebook')
        st.header(f"📓 {filename}")
        
        st.markdown(f"""
        <div class="notebook-card">
            <h3>🎯 Quick Access</h3>
            <p>Use the sidebar to navigate between different sections of your notebook:</p>
            <ul>
                <li>📄 <b>Summary</b> - View AI-generated summary and key topics</li>
                <li>📖 <b>PDF Viewer</b> - Read your original document</li>
                <li>🎴 <b>Flashcards</b> - Study with interactive flashcards</li>
                <li>📝 <b>Quiz</b> - Test your knowledge</li>
                <li>💬 <b>Talk to Doc</b> - Ask questions about your document</li>
                <li>📅 <b>Study Scheduler</b> - Create your learning plan</li>
                <li>🎯 <b>Progress Tracker</b> - Track your progress and earn points</li>
                <li>🧠 <b>Acronym Generator</b> - Create memory aids</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Display basic stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Topics Found", len(notebook.get('topics', [])))
        
        with col2:
            progress = db.get_progress(st.session_state.current_notebook)
            st.metric("Total Score", progress.get('total_score', 0))
        
        with col3:
            completed = len(progress.get('completed_tasks', []))
            st.metric("Tasks Completed", completed)
        
        # Show a preview of topics
        if notebook.get('topics'):
            st.subheader("📚 Key Topics")
            cols = st.columns(2)
            for idx, topic in enumerate(notebook['topics'][:6]):
                with cols[idx % 2]:
                    st.markdown(f"- {topic}")
    else:
        st.error("Notebook not found!")
        if st.button("Return to Home"):
            del st.session_state.current_notebook
            st.rerun()

if __name__ == "__main__":
    main()
