"""
Summary Page - Display AI-generated summary and key topics
"""
import streamlit as st
from utils.db import get_database
from utils.sidebar_utils import show_sidebar_on_all_pages

st.set_page_config(page_title="Summary", page_icon="📄", layout="wide")

# Show common sidebar on all pages
show_sidebar_on_all_pages()

db = get_database()

st.title("📄 Document Summary")

if 'current_notebook' not in st.session_state:
    st.warning("⚠️ No notebook selected. Please upload a PDF from the home page.")
    if st.button("Go to Home"):
        st.switch_page("app.py")
else:
    notebook = db.get_notebook(st.session_state.current_notebook)
    
    if notebook:
        filename = notebook.get('filename', 'Untitled Notebook')
        st.header(f"📓 {filename}")
        
        # Display the summary
        st.subheader("📝 Summary")
        st.markdown(notebook.get('summary', 'No summary available.'))
        
        st.divider()
        
        # Display key topics
        st.subheader("🎯 Key Topics")
        topics = notebook.get('topics', [])
        
        if topics:
            # Display in a nice grid
            cols = st.columns(2)
            for idx, topic in enumerate(topics):
                with cols[idx % 2]:
                    st.markdown(f"**{idx + 1}.** {topic}")
        else:
            st.info("No topics extracted yet.")
        
        # Additional statistics
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            word_count = len(notebook.get('text_content', '').split())
            st.metric("Word Count", f"{word_count:,}")
        
        with col2:
            st.metric("Topics Identified", len(topics))
        
        with col3:
            char_count = len(notebook.get('text_content', ''))
            st.metric("Character Count", f"{char_count:,}")
    else:
        st.error("Notebook not found!")
