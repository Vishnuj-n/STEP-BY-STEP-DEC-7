"""
Study Scheduler Page - Generate personalized study schedules
"""
import streamlit as st
import json
from utils.db import get_database
from utils.helpers import load_prompt, call_llm, parse_json_response
from utils.text_extraction import get_optimal_content_for_scheduling
from utils.sidebar_utils import show_sidebar_on_all_pages
from utils.gamification import get_bonus_info

st.set_page_config(page_title="Study Scheduler", page_icon="📅", layout="wide")

# Show common sidebar on all pages
show_sidebar_on_all_pages()

db = get_database()

st.title("📅 Study Scheduler")

if 'current_notebook' not in st.session_state:
    st.warning("⚠️ No notebook selected. Please upload a PDF from the home page.")
    if st.button("Go to Home"):
        st.switch_page("app.py")
else:
    notebook = db.get_notebook(st.session_state.current_notebook)
    
    if notebook:
        filename = notebook.get('filename', 'Untitled Notebook')
        st.header(f"📓 {filename}")
        
        # Check if user has selected a learning class
        learning_class = db.get_user_learning_class(st.session_state.current_notebook)
        if not learning_class:
            st.info("💡 Tip: Choose a Learning Class from the home page to get 1.5× point bonuses!")
        
        st.markdown("""
        Create a personalized study schedule based on your target completion date.
        The schedule will break down your learning material into manageable daily tasks!
        """)
        
        # Check if schedule already exists
        existing_schedule = notebook.get('schedule')
        
        if existing_schedule:
            st.success("✅ You already have a study schedule!")
            
            if st.button("🔄 Generate New Schedule"):
                # Clear existing schedule
                db.update_notebook(st.session_state.current_notebook, {
                    'schedule': None,
                    'schedule_days': None
                })
                st.rerun()
        else:
            # Schedule creation form
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                days = st.number_input(
                    "How many days do you want to complete this in?",
                    min_value=1,
                    max_value=365,
                    value=7,
                    help="Enter the number of days for your study plan"
                )
            
            with col2:
                st.metric("Days", days)
            
            with col3:
                hours_per_day = st.number_input(
                    "Hours per day",
                    min_value=0.5,
                    max_value=24.0,
                    value=2.0,
                    step=0.5,
                    help="How many hours can you study per day?"
                )
                st.metric("Hours/Day", f"{hours_per_day}h")
            
            if st.button("📅 Generate Schedule", type="primary"):
                with st.spinner("Creating your personalized study schedule..."):
                    try:
                        # Get text content and topics
                        text_content = notebook.get('text_content', '')
                        topics = notebook.get('topics', [])
                        
                        # Get optimal content for scheduling (intro + topics + conclusion)
                        schedule_content = get_optimal_content_for_scheduling(
                            text_content, 
                            topics, 
                            max_length=8000
                        )
                        
                        # Load scheduler prompt
                        prompt_config = load_prompt('scheduler_prompt.json')
                        
                        # Generate schedule
                        response = call_llm(prompt_config, schedule_content, days=days)
                        
                        # Parse JSON response
                        schedule = parse_json_response(response)
                        
                        # Save schedule to database
                        db.save_schedule(st.session_state.current_notebook, schedule, days, hours_per_day)
                        
                        st.success("✅ Schedule created successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error generating schedule: {str(e)}")
                        st.exception(e)
        
        # Display existing schedule
        if existing_schedule:
            st.divider()
            st.subheader("📋 Your Study Schedule")
            
            schedule_days = notebook.get('schedule_days', 0)
            st.info(f"📆 {schedule_days}-Day Study Plan")
            
            # Get progress to find incomplete tasks
            progress_data = db.get_progress(st.session_state.current_notebook)
            completed_tasks = progress_data.get('completed_tasks', [])
            
            # Calculate incomplete tasks
            incomplete_tasks = []
            if isinstance(existing_schedule, list):
                for day_data in existing_schedule:
                    if isinstance(day_data, dict):
                        day = day_data.get('day', '?')
                        tasks = day_data.get('tasks', [])
                        for idx, task in enumerate(tasks):
                            task_id = f"{day}_{idx}"
                            if task_id not in completed_tasks and isinstance(task, dict):
                                incomplete_tasks.append({
                                    'topic': task.get('description', 'Task'),
                                    'original_day': day
                                })
            
            # Show reschedule button if there are incomplete tasks
            if incomplete_tasks:
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.warning(f"⏳ {len(incomplete_tasks)} task(s) remaining")
                with col2:
                    if st.button("🔄 Behind schedule? Re-plan remaining tasks.", type="secondary"):
                        st.session_state.show_reschedule = True
                
                if st.session_state.get('show_reschedule', False):
                    # Show reschedule form
                    st.divider()
                    st.subheader("📋 Create a New Schedule")
                    
                    new_days = st.number_input(
                        "How many days for the new plan?",
                        min_value=1,
                        max_value=365,
                        value=min(7, len(incomplete_tasks) * 2),
                        key="reschedule_days"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✨ Generate New Schedule", type="primary", key="generate_reschedule"):
                            with st.spinner("Creating your new study schedule..."):
                                try:
                                    # Extract topics from incomplete tasks
                                    topics_text = "\n".join([f"- {t['topic']}" for t in incomplete_tasks])
                                    
                                    # Load scheduler prompt
                                    prompt_config = load_prompt('scheduler_prompt.json')
                                    
                                    # Create new prompt for rescheduling
                                    reschedule_prompt = f"""Create a new {new_days}-day study plan using ONLY these remaining topics:

{topics_text}

Break the content into manageable daily tasks. Return the result as a JSON array of objects, where each object represents a day and contains a 'day' number and a list of 'tasks'. Each task should have a 'description' and 'points' (e.g., 10, 20).
"""
                                    
                                    # Generate new schedule
                                    response = call_llm(
                                        prompt_config, 
                                        reschedule_prompt
                                    )
                                    
                                    # Parse JSON response
                                    new_schedule = parse_json_response(response)
                                    
                                    # Get current hours per day if exists
                                    current_hours = notebook.get('hours_per_day', 2.0)
                                    
                                    # Save new schedule to database
                                    db.save_schedule(st.session_state.current_notebook, new_schedule, new_days, current_hours)
                                    
                                    st.session_state.show_reschedule = False
                                    st.success("✅ New schedule created successfully!")
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"Error generating new schedule: {str(e)}")
                                    st.exception(e)
                    
                    with col2:
                        if st.button("❌ Cancel", key="cancel_reschedule"):
                            st.session_state.show_reschedule = False
                            st.rerun()
            
            # Display schedule
            if isinstance(existing_schedule, list):
                # Calculate total incomplete tasks once (performance optimization)
                total_incomplete = sum(1 for d in existing_schedule 
                    if isinstance(d, dict) 
                    for t_idx, t in enumerate(d.get('tasks', [])) 
                    if f"{d.get('day')}_{t_idx}" not in completed_tasks)
                
                for day_data in existing_schedule:
                    if isinstance(day_data, dict):
                        day = day_data.get('day', '?')
                        tasks = day_data.get('tasks', [])
                        
                        with st.expander(f"📅 Day {day}", expanded=False):
                            for idx, task in enumerate(tasks):
                                if isinstance(task, dict):
                                    task_id = f"{day}_{idx}"
                                    is_completed = task_id in completed_tasks
                                    task_points = task.get('points', 10)
                                    
                                    # Check if bonus would apply
                                    will_apply_bonus, final_points, class_name = get_bonus_info(
                                        st.session_state.current_notebook, 
                                        task_points, 
                                        'scheduler_task'
                                    )
                                    
                                    col1, col2, col3 = st.columns([3, 1, 1])
                                    
                                    with col1:
                                        if is_completed:
                                            st.markdown(f"✅ ~~{task.get('description', 'Task')}~~")
                                        else:
                                            st.markdown(f"📌 {task.get('description', 'Task')}")
                                    
                                    with col2:
                                        if will_apply_bonus and not is_completed:
                                            st.markdown(f"**~~{task_points}~~ {final_points} pts** ⭐")
                                        else:
                                            st.markdown(f"**{task_points} pts**")
                                    
                                    with col3:
                                        if not is_completed:
                                            button_label = "✓"
                                            if will_apply_bonus:
                                                button_label = "✓ ⭐"
                                            
                                            if st.button(button_label, key=f"complete_{day}_{idx}"):
                                                db.mark_task_complete(
                                                    st.session_state.current_notebook,
                                                    day,
                                                    idx,
                                                    task_points
                                                )
                                                
                                                # Check if this was the last task (total_incomplete - 1 because this one was just completed)
                                                if total_incomplete == 1:
                                                    st.balloons()
                                                    st.success("🎉 Congratulations! You've completed all tasks!")
                                                
                                                st.rerun()
                                else:
                                    st.markdown(f"- {task}")
            else:
                # Display as text if not JSON
                st.markdown(existing_schedule)
    else:
        st.error("Notebook not found!")
