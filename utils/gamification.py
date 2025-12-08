"""
Gamification utilities for Mind Palace.
Implements study streaks, learning classes, and progress visualization.
"""

import streamlit as st
from datetime import datetime, timedelta
from utils.db import get_database


class LearningClass:
    """RPG-style learning class with point multipliers."""
    
    SCRIBE = {
        'name': '📖 The Scribe',
        'description': 'Master of written knowledge. Excels at Summaries & Flashcards.',
        'multiplier_activities': ['flashcards', 'summaries'],
        'multiplier': 1.5,
        'emoji': '📖'
    }
    
    ORATOR = {
        'name': '🎤 The Orator',
        'description': 'Conversationalist. Gets 1.5x points for Talk to Doc.',
        'multiplier_activities': ['talk_to_duck'],
        'multiplier': 1.5,
        'emoji': '🎤'
    }
    
    TACTICIAN = {
        'name': '⚔️ The Tactician',
        'description': 'Test-master. Gets 1.5x points for Quizzes.',
        'multiplier_activities': ['quiz'],
        'multiplier': 1.5,
        'emoji': '⚔️'
    }
    
    ALL_CLASSES = [SCRIBE, ORATOR, TACTICIAN]


def calculate_study_streak(notebook_id):
    """
    Calculate study streak based on consecutive days of activity.
    Returns: (streak_count, is_active_today, missed_days)
    """
    db = get_database()
    notebook = db.get_notebook(notebook_id)
    if not notebook:
        return 0, False, 0
    
    progress = notebook.get('progress', {})
    last_activity = progress.get('last_activity')
    current_streak = progress.get('study_streak', 0)
    
    if not last_activity:
        return 0, False, 0
    
    # Parse last activity date
    try:
        last_date = datetime.fromisoformat(last_activity).date()
    except (TypeError, ValueError):
        return 0, False, 0
    
    today = datetime.now().date()
    days_since_last = (today - last_date).days
    
    # Check if studied today
    is_active_today = days_since_last == 0
    
    # Check if streak is still active
    if days_since_last == 1:
        # Consecutive day, streak continues
        return current_streak + 1, False, 0
    elif days_since_last == 0:
        # Studied today already
        return current_streak, True, 0
    else:
        # Streak broken
        return 0, False, days_since_last - 1


def get_streak_visual(streak_count):
    """Get visual representation of streak (🔥 icons growing)."""
    if streak_count == 0:
        return "No streak"
    
    fire_count = min(streak_count, 10)  # Cap at 10 fire icons
    return "🔥" * fire_count


def apply_class_multiplier(points, notebook_id, activity_type):
    """
    Apply learning class multiplier to points.
    
    Args:
        points (int): Base points earned
        notebook_id (str): Notebook ID
        activity_type (str): Type of activity ('flashcards', 'talk_to_duck', 'quiz')
    
    Returns:
        int: Points after multiplier applied
    """
    db = get_database()
    learning_class = db.get_user_learning_class(notebook_id)
    
    if not learning_class:
        return points
    
    # Find the class
    class_obj = None
    if learning_class == 'Scribe':
        class_obj = LearningClass.SCRIBE
    elif learning_class == 'Orator':
        class_obj = LearningClass.ORATOR
    elif learning_class == 'Tactician':
        class_obj = LearningClass.TACTICIAN
    
    if not class_obj:
        return points
    
    # Check if this activity gets multiplier
    if activity_type in class_obj['multiplier_activities']:
        return int(points * class_obj['multiplier'])
    
    return points


def display_learning_class_selector():
    """Display interactive learning class selector in Streamlit."""
    st.subheader("⚔️ Choose Your Learning Class")
    st.markdown("Different classes give 1.5x point bonuses for specific activities.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        ### {LearningClass.SCRIBE['emoji']} The Scribe
        {LearningClass.SCRIBE['description']}
        """)
        if st.button("Choose Scribe", key="class_scribe", use_container_width=True):
            return "Scribe"
    
    with col2:
        st.markdown(f"""
        ### {LearningClass.ORATOR['emoji']} The Orator
        {LearningClass.ORATOR['description']}
        """)
        if st.button("Choose Orator", key="class_orator", use_container_width=True):
            return "Orator"
    
    with col3:
        st.markdown(f"""
        ### {LearningClass.TACTICIAN['emoji']} The Tactician
        {LearningClass.TACTICIAN['description']}
        """)
        if st.button("Choose Tactician", key="class_tactician", use_container_width=True):
            return "Tactician"
    
    return None


def display_gamification_stats(notebook_id):
    """Display gamification stats: streak, class, progress garden."""
    db = get_database()
    col1, col2, col3 = st.columns(3)
    
    # Study Streak
    with col1:
        streak_count, is_active_today, missed_days = calculate_study_streak(notebook_id)
        streak_visual = get_streak_visual(streak_count)
        st.metric("Study Streak", f"{streak_count} days", delta=streak_visual if streak_count > 0 else "Start studying!")
    
    # Learning Class
    with col2:
        learning_class = db.get_user_learning_class(notebook_id)
        if learning_class:
            st.metric("Learning Class", learning_class, delta="1.5x points bonus")
        else:
            st.metric("Learning Class", "Not selected", delta="Choose one to start!")
    
    # Progress Garden
    with col3:
        stage, percentage = db.get_progress_stage(notebook_id)
        st.metric("Knowledge Garden", stage, delta=f"{percentage}% complete")
    
    return streak_count, learning_class, percentage


def update_activity_log(notebook_id, activity_type, points_earned):
    """
    Log an activity and update streak tracking.
    
    Args:
        notebook_id (str): Notebook ID
        activity_type (str): Type of activity ('flashcard', 'quiz', 'talk_to_duck')
        points_earned (int): Points earned from activity
    """
    db = get_database()
    # Update last activity date for streak tracking
    db.update_last_study_date(notebook_id)
    
    # Get current streak info
    streak_count, is_active_today, _ = calculate_study_streak(notebook_id)
    
    # Update streak if needed
    if not is_active_today:
        db.update_study_streak(notebook_id, streak_count)
    
    # Apply class multiplier
    final_points = apply_class_multiplier(points_earned, notebook_id, activity_type)
    
    return final_points, streak_count
