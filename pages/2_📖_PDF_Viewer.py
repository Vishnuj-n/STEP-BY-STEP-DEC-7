"""
PDF Viewer Page - Display the uploaded PDF document
"""
import streamlit as st
import base64
from utils.db import get_database
from utils.sidebar_utils import show_sidebar_on_all_pages

st.set_page_config(page_title="PDF Viewer", page_icon="📖", layout="wide")

# Show common sidebar on all pages
show_sidebar_on_all_pages()

db = get_database()

st.title("📖 PDF Viewer")

if 'current_notebook' not in st.session_state:
    st.warning("⚠️ No notebook selected. Please upload a PDF from the home page.")
    if st.button("Go to Home"):
        st.switch_page("app.py")
else:
    notebook = db.get_notebook(st.session_state.current_notebook)
    
    if notebook:
        filename = notebook.get('filename', 'Untitled Notebook')
        st.header(f"📓 {filename}")
        
        # Display PDF
        pdf_content = notebook.get('pdf_content')
        
        if pdf_content:
            # Decode base64 PDF
            pdf_bytes = base64.b64decode(pdf_content)
            
            # Display PDF using iframe
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
            
            st.markdown(pdf_display, unsafe_allow_html=True)
            
            # Download button
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=notebook.get('filename', 'document.pdf'),
                mime="application/pdf"
            )
        else:
            st.error("PDF content not found!")
    else:
        st.error("Notebook not found!")
