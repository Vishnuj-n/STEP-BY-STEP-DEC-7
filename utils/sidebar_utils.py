"""
Shared sidebar utilities for all pages.
Provides common sidebar elements like Today's Tasks.
"""

import streamlit as st
from utils.db import get_database
from datetime import datetime


def display_todays_tasks_sidebar():
    """Display today's tasks in the sidebar (used on all pages)."""
    db = get_database()  # Initialize inside function to avoid module-level Streamlit calls
    
    # Only show if a notebook is selected
    if 'current_notebook' not in st.session_state:
        return
    
    notebook = db.get_notebook(st.session_state.current_notebook)
    
    if not notebook:
        return
    
    schedule = notebook.get('schedule')
    if not schedule or not isinstance(schedule, list) or len(schedule) == 0:
        st.info("📋 No schedule yet. Create one in Study Scheduler!")
        return
    
    st.markdown("### 📋 Today's Tasks")
    
    # Calculate the current day based on start_date
    start_date = notebook.get('schedule_start_date')
    
    if start_date:
        # Parse the date if it's a string
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        
        # Calculate days elapsed
        today = datetime.now()
        days_elapsed = (today.date() - start_date.date()).days
        current_day = days_elapsed + 1  # Day 1 is the first day
    else:
        # Fallback to session state if no start date
        current_day = st.session_state.get('current_study_day', 1)
    
    # Find today's schedule
    todays_schedule = None
    for day_data in schedule:
        if isinstance(day_data, dict) and day_data.get('day') == current_day:
            todays_schedule = day_data
            break
    
    if not todays_schedule:
        # If no schedule for today, use first available day
        if isinstance(schedule[0], dict):
            todays_schedule = schedule[0]
            current_day = todays_schedule.get('day', 1)
    
    if todays_schedule:
        tasks = todays_schedule.get('tasks', [])
        
        if not tasks:
            st.info("✨ No tasks for today!")
            return
        
        # Get progress
        progress_data = db.get_progress(st.session_state.current_notebook)
        completed_tasks = progress_data.get('completed_tasks', [])
        
        # Display tasks with checkboxes
        for idx, task in enumerate(tasks):
            if isinstance(task, dict):
                task_id = f"{current_day}_{idx}"
                is_completed = task_id in completed_tasks
                
                task_desc = task.get('description', 'Task')
                task_points = task.get('points', 10)
                
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Create checkbox
                    if is_completed:
                        st.markdown(f"✅ ~~{task_desc}~~")
                    else:
                        # Use a button instead of checkbox for better control
                        if st.button(
                            f"☐ {task_desc}",
                            key=f"task_sidebar_{st.session_state.current_notebook}_{idx}",
                            use_container_width=True,
                            help=f"Click to mark complete (+{task_points} pts)"
                        ):
                            db.mark_task_complete(
                                st.session_state.current_notebook,
                                current_day,
                                idx,
                                task_points
                            )
                            st.rerun()
                
                with col2:
                    st.caption(f"{task_points}pts")
        
        # Progress summary
        completed_count = sum(1 for idx, _ in enumerate(tasks) 
                            if f"{current_day}_{idx}" in completed_tasks)
        total_count = len(tasks)
        st.progress(completed_count / total_count if total_count > 0 else 0)
        st.caption(f"{completed_count}/{total_count} completed")
    else:
        st.info("📋 No schedule available. Create one in Study Scheduler!")


def show_sidebar_on_all_pages():
    """
    Call this function at the start of every page file to show the common sidebar.
    This should be called right after st.set_page_config().
    """
    db = get_database()  # Initialize inside function to avoid module-level Streamlit calls
    
    with st.sidebar:
        st.header("📚 My Notebooks")
        
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
            display_todays_tasks_sidebar()
            st.divider()
        
        if st.button("🏠 Home", use_container_width=True):
            if 'current_notebook' in st.session_state:
                del st.session_state.current_notebook
            st.switch_page("app.py")
