"""
Progress Tracker Page - Track learning progress and earn points
"""
import streamlit as st
from utils.db import get_database
from utils.sidebar_utils import show_sidebar_on_all_pages

st.set_page_config(page_title="Progress Tracker", page_icon="🎯", layout="wide")

# Show common sidebar on all pages
show_sidebar_on_all_pages()

db = get_database()

st.title("🎯 Progress Tracker")

if 'current_notebook' not in st.session_state:
    st.warning("⚠️ No notebook selected. Please upload a PDF from the home page.")
    if st.button("Go to Home"):
        st.switch_page("app.py")
else:
    notebook = db.get_notebook(st.session_state.current_notebook)
    
    if notebook:
        filename = notebook.get('filename', 'Untitled Notebook')
        st.header(f"📓 {filename}")
        
        # Get progress data
        progress_data = db.get_progress(st.session_state.current_notebook)
        total_score = progress_data.get('total_score', 0)
        completed_tasks = progress_data.get('completed_tasks', [])
        
        # Display score prominently
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 10px; color: white; margin-bottom: 2rem;">
            <h1 style="font-size: 4rem; margin: 0;">🏆 {total_score}</h1>
            <h3 style="margin: 0;">Total Points</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📝 Tasks Completed", len(completed_tasks))
        
        with col2:
            schedule = notebook.get('schedule', [])
            total_tasks = 0
            if isinstance(schedule, list):
                for day in schedule:
                    if isinstance(day, dict):
                        total_tasks += len(day.get('tasks', []))
            st.metric("📋 Total Tasks", total_tasks)
        
        with col3:
            completion_rate = (len(completed_tasks) / total_tasks * 100) if total_tasks > 0 else 0
            st.metric("✅ Completion Rate", f"{completion_rate:.1f}%")
        
        # Progress bar
        st.divider()
        st.subheader("📊 Overall Progress")
        
        if total_tasks > 0:
            st.progress(completion_rate / 100)
            st.caption(f"{len(completed_tasks)} out of {total_tasks} tasks completed")
        else:
            st.info("📅 Create a study schedule to start tracking your progress!")
            if st.button("Go to Study Scheduler"):
                st.switch_page("pages/6_📅_Study_Scheduler.py")
        
        # Achievements section
        st.divider()
        st.subheader("🏅 Achievements")
        
        achievements = []
        
        # Define achievement thresholds
        if total_score >= 50:
            achievements.append({"name": "Getting Started", "icon": "🌱", "desc": "Earned your first 50 points!"})
        if total_score >= 100:
            achievements.append({"name": "On a Roll", "icon": "🔥", "desc": "Reached 100 points!"})
        if total_score >= 250:
            achievements.append({"name": "Dedicated Learner", "icon": "⭐", "desc": "Earned 250 points!"})
        if total_score >= 500:
            achievements.append({"name": "Master Student", "icon": "🎓", "desc": "Achieved 500 points!"})
        
        if len(completed_tasks) >= 10:
            achievements.append({"name": "Task Master", "icon": "✅", "desc": "Completed 10 tasks!"})
        
        if completion_rate >= 50:
            achievements.append({"name": "Halfway There", "icon": "🎯", "desc": "Completed 50% of tasks!"})
        
        if completion_rate >= 100:
            achievements.append({"name": "Perfect Score", "icon": "💯", "desc": "Completed all tasks!"})
        
        if achievements:
            cols = st.columns(min(3, len(achievements)))
            for idx, achievement in enumerate(achievements):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div style="padding: 1rem; border-radius: 8px; background-color: #f0f2f6; text-align: center;">
                        <div style="font-size: 3rem;">{achievement['icon']}</div>
                        <div style="font-weight: bold;">{achievement['name']}</div>
                        <div style="font-size: 0.9rem; color: #666;">{achievement['desc']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Complete tasks to unlock achievements! 🏆")
        
        # Recent activity
        st.divider()
        st.subheader("📈 Recent Activity")
        
        if completed_tasks:
            st.success(f"🎉 You've completed {len(completed_tasks)} tasks! Keep up the great work!")
            
            # Show some stats
            if schedule:
                st.markdown("**Completed Tasks by Day:**")
                day_stats = {}
                for task_id in completed_tasks:
                    day = task_id.split('_')[0]
                    day_stats[day] = day_stats.get(day, 0) + 1
                
                for day, count in sorted(day_stats.items()):
                    st.markdown(f"- Day {day}: {count} task(s) ✓")
        else:
            st.info("No activity yet. Start completing tasks to see your progress here!")
        
    else:
        st.error("Notebook not found!")
