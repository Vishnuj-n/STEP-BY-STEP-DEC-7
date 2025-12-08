"""
Database utilities for Mind Palace - MongoDB with optimized nested schema.
Single notebook document contains all related data: schedule, flashcards, quizzes, acronyms, progress.
"""

import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()


@st.cache_resource
def get_database():
    """Get or create cached database connection. Only one connection per Streamlit session."""
    return Database()


class Database:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client['mind_palace']
        self.notebooks = self.db['notebooks']
        self.notebooks.create_index('created_at')  # Index for sorting
    
    # ============ NOTEBOOK OPERATIONS ============
    
    def save_notebook(self, filename, pdf_content, text_content, summary, topics, embeddings=None):
        """Save a new notebook with optimized nested schema."""
        notebook = {
            'filename': filename,
            'pdf_content': pdf_content,
            'text_content': text_content,
            'summary': summary,
            'topics': topics,
            'embeddings': embeddings,  # Cached sentence embeddings
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            
            # Nested arrays (initially empty)
            'schedule': [],
            'flashcards': [],
            'quizzes': [],
            'acronyms': [],
            'progress': {
                'completed_tasks': [],
                'total_score': 0,
                'last_activity': None,
                'topic_mastery': {},  # {topic_name: mastery_percentage}
                'quiz_average': 0,
                'study_streak': 0
            }
        }
        result = self.notebooks.insert_one(notebook)
        return str(result.inserted_id)
    
    def get_notebook(self, notebook_id):
        """Retrieve a notebook by ID."""
        return self.notebooks.find_one({'_id': ObjectId(notebook_id)})
    
    def get_all_notebooks(self):
        """Get all notebooks sorted by creation date (newest first)."""
        return list(self.notebooks.find().sort('created_at', -1))
    
    def update_notebook(self, notebook_id, update_data):
        """Update notebook data."""
        update_data['updated_at'] = datetime.now()
        return self.notebooks.update_one(
            {'_id': ObjectId(notebook_id)},
            {'$set': update_data}
        )
    
    def delete_notebook(self, notebook_id):
        """Delete a notebook and all its nested data."""
        self.notebooks.delete_one({'_id': ObjectId(notebook_id)})
    
    # ============ SCHEDULE OPERATIONS ============
    
    def save_schedule(self, notebook_id, schedule, days, hours_per_day=2.0):
        """Save study schedule to notebook."""
        from datetime import datetime
        return self.update_notebook(notebook_id, {
            'schedule': schedule,
            'schedule_days': days,
            'hours_per_day': hours_per_day,
            'schedule_start_date': datetime.now().isoformat()  # Track when schedule started
        })
    
    def get_schedule(self, notebook_id):
        """Retrieve schedule from notebook."""
        notebook = self.get_notebook(notebook_id)
        if notebook:
            return notebook.get('schedule', [])
        return []
    
    # ============ FLASHCARD OPERATIONS ============
    
    def add_flashcards(self, notebook_id, topic, cards_list):
        """
        Add flashcards to notebook for a specific topic.
        cards_list format: [{'question': '...', 'answer': '...', 'difficulty': 'easy'}, ...]
        """
        flashcards_with_metadata = []
        for card in cards_list:
            flashcard = {
                '_id': ObjectId(),
                'topic': topic,
                'question': card.get('question', ''),
                'answer': card.get('answer', ''),
                'difficulty': card.get('difficulty', 'medium'),
                'review_count': 0,
                'mastery_level': 0,  # 0=new, 1=learning, 2=familiar, 3=mastered, 4-5=expert
                'last_reviewed': None,
                'created_at': datetime.now()
            }
            flashcards_with_metadata.append(flashcard)
        
        return self.notebooks.update_one(
            {'_id': ObjectId(notebook_id)},
            {
                '$push': {'flashcards': {'$each': flashcards_with_metadata}},
                '$set': {'updated_at': datetime.now()}
            }
        )
    
    def get_flashcards(self, notebook_id, topic=None):
        """Retrieve flashcards from notebook, optionally filtered by topic."""
        notebook = self.get_notebook(notebook_id)
        if notebook:
            flashcards = notebook.get('flashcards', [])
            if topic:
                return [card for card in flashcards if card.get('topic') == topic]
            return flashcards
        return []
    
    def update_flashcard_review(self, notebook_id, flashcard_id, mastery_level=None):
        """Update flashcard review count and mastery level."""
        update_data = {
            'flashcards.$.last_reviewed': datetime.now(),
            'updated_at': datetime.now()
        }
        if mastery_level:
            update_data['flashcards.$.mastery_level'] = mastery_level
        
        return self.notebooks.update_one(
            {
                '_id': ObjectId(notebook_id),
                'flashcards._id': ObjectId(flashcard_id)
            },
            {
                '$inc': {'flashcards.$.review_count': 1},
                '$set': update_data
            }
        )
    
    # ============ QUIZ OPERATIONS ============
    
    def save_quiz(self, notebook_id, topic, questions_json):
        """
        Save a quiz to notebook.
        questions_json format: {'questions': [{'text': '...', 'options': [...], 'answer': 0}, ...]}
        """
        quiz = {
            '_id': ObjectId(),
            'topic': topic,
            'questions': questions_json.get('questions', []),
            'attempts': [],
            'created_at': datetime.now()
        }
        
        return self.notebooks.update_one(
            {'_id': ObjectId(notebook_id)},
            {
                '$push': {'quizzes': quiz},
                '$set': {'updated_at': datetime.now()}
            }
        )
    
    def get_quizzes(self, notebook_id, topic=None):
        """Retrieve quizzes from notebook, optionally filtered by topic."""
        notebook = self.get_notebook(notebook_id)
        if notebook:
            quizzes = notebook.get('quizzes', [])
            if topic:
                return [q for q in quizzes if q.get('topic') == topic]
            return quizzes
        return []
    
    def save_quiz_attempt(self, notebook_id, quiz_id, user_answers, score, time_spent):
        """
        Save a quiz attempt to quiz.attempts array.
        user_answers: list of selected option indices (0-3)
        score: points earned
        time_spent: time in seconds
        """
        attempt = {
            'user_answers': user_answers,
            'score': score,
            'percentage': 0,  # Will be calculated
            'time_spent': time_spent,
            'date_taken': datetime.now()
        }
        
        # Find quiz by ID and add attempt
        return self.notebooks.update_one(
            {
                '_id': ObjectId(notebook_id),
                'quizzes._id': ObjectId(quiz_id)
            },
            {
                '$push': {'quizzes.$.attempts': attempt},
                '$set': {'updated_at': datetime.now()}
            }
        )
    
    def get_quiz_history(self, notebook_id, topic=None):
        """Get quiz history with attempts."""
        quizzes = self.get_quizzes(notebook_id, topic)
        history = []
        for quiz in quizzes:
            for attempt in quiz.get('attempts', []):
                history.append({
                    'topic': quiz.get('topic'),
                    'quiz_id': str(quiz.get('_id')),
                    'score': attempt.get('score'),
                    'percentage': attempt.get('percentage'),
                    'time_spent': attempt.get('time_spent'),
                    'date_taken': attempt.get('date_taken')
                })
        return history
    
    # ============ ACRONYM/MEMORY AID OPERATIONS ============
    
    def add_acronym(self, notebook_id, topic, generator_type, content, explanation=''):
        """
        Save a generated memory aid (acronym, song, phrase, story).
        generator_type: 'Acronym', 'Song', 'Phrase', or 'Story'
        """
        acronym = {
            '_id': ObjectId(),
            'topic': topic,
            'type': generator_type,
            'content': content,
            'explanation': explanation,
            'usefulness_rating': 0,
            'created_at': datetime.now()
        }
        
        return self.notebooks.update_one(
            {'_id': ObjectId(notebook_id)},
            {
                '$push': {'acronyms': acronym},
                '$set': {'updated_at': datetime.now()}
            }
        )
    
    def get_acronyms(self, notebook_id, topic=None, generator_type=None):
        """Retrieve memory aids, optionally filtered by topic or type."""
        notebook = self.get_notebook(notebook_id)
        if notebook:
            acronyms = notebook.get('acronyms', [])
            if topic:
                acronyms = [a for a in acronyms if a.get('topic') == topic]
            if generator_type:
                acronyms = [a for a in acronyms if a.get('type') == generator_type]
            return acronyms
        return []
    
    def rate_acronym(self, notebook_id, acronym_id, rating):
        """Rate a memory aid's usefulness (1-5)."""
        return self.notebooks.update_one(
            {
                '_id': ObjectId(notebook_id),
                'acronyms._id': ObjectId(acronym_id)
            },
            {
                '$set': {
                    'acronyms.$.usefulness_rating': rating,
                    'updated_at': datetime.now()
                }
            }
        )
    
    # ============ PROGRESS OPERATIONS ============
    
    def mark_task_complete(self, notebook_id, day, task_index, points):
        """Mark a study scheduler task as complete and add points."""
        task_id = f"{day}_{task_index}"
        notebook = self.get_notebook(notebook_id)
        
        if notebook:
            progress = notebook.get('progress', {})
            completed_tasks = progress.get('completed_tasks', [])
            
            if task_id not in completed_tasks:
                return self.notebooks.update_one(
                    {'_id': ObjectId(notebook_id)},
                    {
                        '$push': {'progress.completed_tasks': task_id},
                        '$inc': {'progress.total_score': points},
                        '$set': {
                            'progress.last_activity': datetime.now(),
                            'updated_at': datetime.now()
                        }
                    }
                )
        return None
    
    def update_progress(self, notebook_id, progress_data):
        """Update progress object with custom data."""
        progress_data['last_activity'] = datetime.now()
        return self.update_notebook(notebook_id, {'progress': progress_data})
    
    def get_progress(self, notebook_id):
        """Retrieve progress from notebook."""
        notebook = self.get_notebook(notebook_id)
        if notebook:
            return notebook.get('progress', {
                'completed_tasks': [],
                'total_score': 0,
                'last_activity': None,
                'topic_mastery': {},
                'quiz_average': 0,
                'study_streak': 0
            })
        return {}
    
    def update_topic_mastery(self, notebook_id, topic, mastery_percentage):
        """Update mastery percentage for a specific topic."""
        return self.notebooks.update_one(
            {'_id': ObjectId(notebook_id)},
            {
                '$set': {
                    f'progress.topic_mastery.{topic}': mastery_percentage,
                    'updated_at': datetime.now()
                }
            }
        )
    
    def update_quiz_average(self, notebook_id, average_score):
        """Update the average quiz score in progress."""
        return self.notebooks.update_one(
            {'_id': ObjectId(notebook_id)},
            {
                '$set': {
                    'progress.quiz_average': average_score,
                    'updated_at': datetime.now()
                }
            }
        )
    
    def update_study_streak(self, notebook_id, streak_count):
        """Update the study streak counter."""
        return self.notebooks.update_one(
            {'_id': ObjectId(notebook_id)},
            {
                '$set': {
                    'progress.study_streak': streak_count,
                    'updated_at': datetime.now()
                }
            }
        )

    # ============ GAMIFICATION FEATURES ============
    
    def update_last_study_date(self, notebook_id):
        """Update the last study date for streak tracking."""
        return self.notebooks.update_one(
            {'_id': ObjectId(notebook_id)},
            {
                '$set': {
                    'progress.last_activity': datetime.now().date().isoformat(),
                    'updated_at': datetime.now()
                }
            }
        )
    
    def get_user_learning_class(self, notebook_id):
        """Get the user's learning class (Scribe, Orator, Tactician)."""
        notebook = self.get_notebook(notebook_id)
        if notebook:
            return notebook.get('progress', {}).get('learning_class', None)
        return None
    
    def set_user_learning_class(self, notebook_id, learning_class):
        """Set the user's learning class for point multipliers."""
        valid_classes = ['Scribe', 'Orator', 'Tactician']
        if learning_class not in valid_classes:
            raise ValueError(f"Invalid learning class. Must be one of {valid_classes}")
        
        return self.notebooks.update_one(
            {'_id': ObjectId(notebook_id)},
            {
                '$set': {
                    'progress.learning_class': learning_class,
                    'updated_at': datetime.now()
                }
            }
        )
    
    def calculate_progress_percentage(self, notebook_id):
        """Calculate overall progress percentage based on completed tasks and schedule."""
        notebook = self.get_notebook(notebook_id)
        if not notebook:
            return 0
        
        schedule = notebook.get('schedule', [])
        if not schedule:
            return 0
        
        total_tasks = sum(len(day.get('tasks', [])) for day in schedule if isinstance(day, dict))
        if total_tasks == 0:
            return 0
        
        completed_tasks = len(notebook.get('progress', {}).get('completed_tasks', []))
        return int((completed_tasks / total_tasks) * 100)
    
    def get_progress_stage(self, notebook_id):
        """Get visual representation of progress (🌱 -> 🌿 -> 🌳 -> 🍎)."""
        percentage = self.calculate_progress_percentage(notebook_id)
        
        if percentage < 25:
            return "🌱 Seedling", percentage
        elif percentage < 50:
            return "🌿 Small Plant", percentage
        elif percentage < 75:
            return "🌳 Tree", percentage
        else:
            return "🍎 Fruit-bearing Tree", percentage
