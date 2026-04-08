"""
config.py — Application-wide configuration for the AI Interview System.
"""
import os
from werkzeug.security import generate_password_hash


class Config:
    # ── Core ──────────────────────────────────────────────────────────────
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SECRET_KEY = os.environ.get('SECRET_KEY', 'buddy-ai-interview-secret-2024')

    # ── Database ──────────────────────────────────────────────────────────
    # Use PostgreSQL on Heroku, SQLite locally
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Fix postgres:// → postgresql:// for SQLAlchemy 3.x
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        SQLALCHEMY_DATABASE_URI = (
            'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'interview.db')
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── File Uploads ──────────────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    REPORTS_FOLDER = os.path.join(BASE_DIR, 'reports')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # 16 MB max PDF upload
    ALLOWED_EXTENSIONS = {'pdf'}

    # ── MCQ Settings ──────────────────────────────────────────────────────
    MCQ_QUESTIONS_FILE = os.path.join(BASE_DIR, 'questions.csv')
    MCQ_QUESTIONS_PER_SESSION = 10
    MCQ_PASS_THRESHOLD = 6                  # Minimum correct to proceed

    # ── Verbal Interview Settings ─────────────────────────────────────────
    VERBAL_QUESTIONS_FILE = os.path.join(BASE_DIR, 'verbal_questions.json')
    VERBAL_MODEL_NAME = 'paraphrase-MiniLM-L6-v2'

    # ── Admin Auth ────────────────────────────────────────────────────────
    ADMIN_USERNAME = 'admin'
    # Default password: admin123 (change via ADMIN_PASSWORD env var)
    ADMIN_PASSWORD_HASH = generate_password_hash(
        os.environ.get('ADMIN_PASSWORD', 'admin123')
    )

    # ── Available Roles ───────────────────────────────────────────────────
    ROLES = [
        'Software Engineer',
        'Data Scientist',
        'Product Manager',
        'Data Analyst',
        'Product Analyst',
        'Cyber Security',
        'Information Technology',
        'Prompt Engineering'
    ]
