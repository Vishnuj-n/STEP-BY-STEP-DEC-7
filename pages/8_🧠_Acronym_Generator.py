"""
Memory Aid Generator Page - Generates various mnemonic devices like acronyms, songs, and phrases.
"""
import streamlit as st
from utils.db import get_database
from utils.helpers import load_prompt, call_llm
from utils.text_extraction import get_topic_text
from utils.sidebar_utils import show_sidebar_on_all_pages

st.set_page_config(page_title="Memory Generator", page_icon="🧠", layout="wide")

show_sidebar_on_all_pages()

db = get_database()

# --- Configuration: All Available Generator Types and their corresponding prompt file names ---
GENERATOR_OPTIONS = {
    "Acronym/Initialism": "acronym_prompt.json",
    "Mnemonic Song/Rhyme": "song_prompt.json",
    "General Mnemonic Phrase": "phrase_prompt.json",
    "Mnemonic Story": "story_prompt.json",
}
# --- End Configuration ---

st.title("🧠 Memory Aid Generator")
st.markdown("Generate various memory devices: **Acronyms**, **Songs**, **Phrases**, **Stories**, or **All at Once**!")

# --- Generator Selection with "All Mnemonics" Option ---
col1, col2 = st.columns([3, 1])
with col1:
    selected_generator = st.selectbox(
        "Choose the type of memory aid:",
        options=["✨ All Mnemonics (Compare All 4)"] + list(GENERATOR_OPTIONS.keys()),
        key="generator_type"
    )
with col2:
    st.info("💡 **Tip:** Select 'All Mnemonics' to compare all 4 types and pick the best one!")
# --- End Generator Selection ---


if 'current_notebook' not in st.session_state:
    st.warning("⚠️ No notebook selected. Please upload a PDF from the home page.")
    if st.button("Go to Home"):
        st.switch_page("app.py")
else:
    notebook = db.get_notebook(st.session_state.current_notebook)
    
    if notebook:
        filename = notebook.get('filename', 'Untitled Notebook')
        st.header(f"📓 {filename}")
        
        # --- Unified Generation Function ---
        def run_generation(context_text, concept_text):
            """
            Core function that handles all generation types.
            It dynamically loads the correct prompt based on the selected generator.
            Supports single mnemonics or all 4 at once.
            """
            generator_type = st.session_state.generator_type
            
            # Handle "All Mnemonics" special case
            if generator_type == "✨ All Mnemonics (Compare All 4)":
                prompt_filename = "all_mnemonics_prompt.json"
                display_type = "All Mnemonics Comparison"
            else:
                prompt_filename = GENERATOR_OPTIONS.get(generator_type)
                display_type = generator_type

            if not prompt_filename:
                st.error(f"Error: Unknown generator type '{generator_type}'.")
                return

            with st.spinner(f"Creating {display_type} for '{concept_text}'..."):
                try:
                    # 1. Dynamically load the correct JSON prompt
                    prompt_config = load_prompt(prompt_filename) 

                    # 2. Call the single, unified model function
                    response = call_llm(
                        prompt_config, 
                        context_text=context_text, # PDF content (or empty string)
                        target_text=concept_text   # Topic name or Custom text
                    ) 
                    
                    st.session_state.generator_result = response
                    st.session_state.generator_concept = concept_text
                    st.session_state.generator_type_used = display_type
                    
                    # Save to database
                    db.add_acronym(
                        st.session_state.current_notebook,
                        topic=concept_text,
                        generator_type=display_type,
                        content=response
                    )
                    
                    st.success(f"{display_type} successfully generated for **{concept_text}**!")

                except Exception as e:
                    st.error(f"Error generating {display_type}. Check prompt files or API connection.")
                    st.exception(e)
        # --- End Unified Generation Function ---
        
        
        topics = notebook.get('topics', [])
        tab1, tab2, tab3 = st.tabs(["📚 From Topics", "✍️ Custom Text", "🗂️ View Previous"])
        
        # Determine button text based on selection
        button_text = "🎯 Generate All Mnemonics from Topic" if selected_generator == "✨ All Mnemonics (Compare All 4)" else f"🧠 Generate {selected_generator} from Topic"
        button_text_custom = "🎯 Generate All Mnemonics from Custom Text" if selected_generator == "✨ All Mnemonics (Compare All 4)" else f"🧠 Generate {selected_generator} from Custom Text"
        
        # --- TAB 1: From Topics ---
        with tab1:
            if topics:
                selected_topic = st.selectbox(
                    "Select a topic:",
                    topics,
                    key="topic_concept"
                )
                
                if st.button(button_text, type="primary"):
                    with st.spinner(f"🔍 Extracting content for '{selected_topic}'..."):
                        text_content = notebook.get('text_content', '')
                        cached_embeddings = notebook.get('embeddings')
                        # Uses cached embeddings from database
                        topic_specific_text = get_topic_text(text_content, selected_topic, cached_embeddings=cached_embeddings) 
                    
                    run_generation(topic_specific_text, selected_topic)
            else:
                st.warning("No topics found. Please check the Summary page or use custom text.")
        
        # --- TAB 2: Custom Text ---
        with tab2:
            custom_text = st.text_area(
                "Enter a list or concept:",
                height=150,
                placeholder="Example: Planets in our solar system\nMercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune",
                key="custom_text_input"
            )
            
            if st.button(button_text_custom, type="primary"):
                if custom_text.strip():
                    # context_text is "" for custom text, concept_text is the input
                    run_generation("", custom_text) 
                else:
                    st.warning("Please enter some text first!")
        
        # --- TAB 3: View Previous ---
        with tab3:
            st.markdown("### 🗂️ Previously Generated Memory Aids")
            
            # Get all acronyms for this notebook
            all_acronyms = db.get_acronyms(st.session_state.current_notebook)
            
            if not all_acronyms:
                st.info("No memory aids generated yet. Create your first one in the other tabs!")
            else:
                # Filter options
                col1, col2 = st.columns(2)
                with col1:
                    filter_type = st.selectbox(
                        "Filter by type:",
                        ["All Types"] + list(GENERATOR_OPTIONS.keys()) + ["All Mnemonics Comparison"],
                        key="filter_type"
                    )
                
                # Apply filter
                filtered_acronyms = all_acronyms
                if filter_type != "All Types":
                    filtered_acronyms = [a for a in all_acronyms if a.get('type') == filter_type]
                
                st.caption(f"Showing {len(filtered_acronyms)} of {len(all_acronyms)} memory aids")
                
                # Display acronyms
                for i, acronym in enumerate(reversed(filtered_acronyms)):  # Newest first
                    topic = acronym.get('topic', 'Unknown')
                    mnem_type = acronym.get('type', 'Unknown')
                    content = acronym.get('content', '')
                    created_at = acronym.get('created_at', 'Unknown')
                    rating = acronym.get('usefulness_rating', 0)
                    
                    if hasattr(created_at, 'strftime'):
                        created_str = created_at.strftime("%b %d, %Y %I:%M %p")
                    else:
                        created_str = str(created_at)
                    
                    with st.expander(f"{'⭐' * rating if rating > 0 else '☆'} {mnem_type} - {topic} ({created_str})"):
                        st.markdown(content)
                        
                        # Rating system
                        st.divider()
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            new_rating = st.slider(
                                "Usefulness Rating:",
                                0, 5, rating,
                                key=f"rating_{acronym.get('_id')}"
                            )
                        with col2:
                            if st.button("💾 Save Rating", key=f"save_rating_{acronym.get('_id')}"):
                                db.rate_acronym(
                                    st.session_state.current_notebook,
                                    str(acronym.get('_id')),
                                    new_rating
                                )
                                st.success("Rating saved!")
                                st.rerun()
        
        
        # --- Display Result (Unified) ---
        if 'generator_result' in st.session_state:
            st.divider()
            st.subheader(f"🎯 {st.session_state.generator_type_used}")
            
            st.info(f"**Concept:** {st.session_state.get('generator_concept', 'N/A')}")
            
            # Special formatting for "All Mnemonics Comparison"
            if st.session_state.generator_type_used == "All Mnemonics Comparison":
                # Display all mnemonics using markdown with better formatting
                st.markdown(st.session_state.generator_result)
                
                st.divider()
                st.subheader("📊 Comparison Guide")
                st.markdown("""
                ** reviewing all 4 mnemonics, consider:**     
                """)
            else:
                # Single mnemonic display with markdown formatting
                st.markdown(f"""
                ## 🎯 Your Mnemonic
                
                {st.session_state.generator_result}
                """)
                
                st.divider()
                st.subheader("💡 Memory Tips")
                st.markdown("""
                **How to use this mnemonic effectively:**
                
                1. 🔄 **Review regularly** - Practice the memory aid daily for best retention.
                2. 🎨 **Visualize** - Create mental images for the concept.
                3. 📝 **Write it down** - Writing helps reinforce memory.
                4. 🤝 **Share it** - Explaining to others reinforces learning.
                5. ✏️ **Personalize it** - Modify the mnemonic to fit YOUR style better.
                
                ---
                
                ### 📌 Pro Tips
                
                - **For Acronyms:** Create visual associations for each letter
                - **For Songs:** Practice singing/reciting it 5 times daily
                - **For Phrases:** Write it on sticky notes around your study space
                - **For Stories:** Draw the story or act it out with friends
                """)
            
    else:
        st.error("Notebook not found!")