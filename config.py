import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mindvault-super-secure-production-secret-key-92837482347')
    
    # Database Configuration: SQLite fallback or PostgreSQL from DATABASE_URL
    raw_db_url = os.environ.get('DATABASE_URL')
    if raw_db_url:
        if raw_db_url.startswith('postgres://'):
            raw_db_url = raw_db_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = raw_db_url
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'mindvault.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit (Anti-DoS)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'App', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}
    
    # Cookie & Session Security Hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RENDER') is not None
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Rate Limiting Storage
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    
    # Google OAuth / Identity Services
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'DEMO_MINDVAULT_GOOGLE_CLIENT_ID')
    
    # Application Info
    APP_NAME = "MindVault[E-BOOK]"
    TAGLINE = "Store Knowledge. Unlock Potential."
    COMMUNITY_URL = "https://ecellcup.onrender.com/community"
