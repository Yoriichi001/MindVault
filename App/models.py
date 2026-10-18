from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=True)
    role = db.Column(db.String(20), default='student', nullable=False)  # 'student' or 'admin'
    avatar = db.Column(db.Text, default='default-avatar.png', nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    google_id = db.Column(db.String(128), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships with cascading deletes
    feedbacks = db.relationship('Feedback', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    reading_history = db.relationship('ReadingHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Salted bcrypt hash generation."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check password against stored hash."""
        if not self.password_hash:
            return False
        return bcrypt.check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    def get_avatar_url(self):
        if not self.avatar or self.avatar == 'default-avatar.png':
            return '/static/images/default-avatar.png'
        if self.avatar.startswith('http'):
            return self.avatar
        if self.avatar.startswith('avatars/'):
            return f'/static/uploads/{self.avatar}'
        return f'/static/images/{self.avatar}'

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Material(db.Model):
    __tablename__ = 'materials'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    author = db.Column(db.String(150), nullable=False, index=True)
    # Category MUST be one of: 'Books', 'Research Papers', 'Study Materials'
    category = db.Column(db.String(50), nullable=False, index=True)
    sub_category = db.Column(db.String(100), nullable=True, default='General')
    description = db.Column(db.Text, nullable=False)
    content_preview = db.Column(db.Text, nullable=True)
    # Full textual/chapter content for in-browser antique book reader
    full_content = db.Column(db.Text, nullable=True)
    cover_image = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.Text, nullable=True)  # PDF path or Cloudinary URL
    file_size_mb = db.Column(db.Float, default=0.0)
    pages = db.Column(db.Integer, default=1)
    edition_year = db.Column(db.String(50), nullable=True, default='')
    isbn_doi = db.Column(db.String(100), nullable=True, default='')
    language = db.Column(db.String(50), nullable=True, default='English')
    views_count = db.Column(db.Integer, default=0)
    downloads_count = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


    # Relationships with cascading deletes
    readers = db.relationship('ReadingHistory', backref='material', lazy='dynamic', cascade='all, delete-orphan')

    def get_cover_url(self):
        if not self.cover_image:
            return '/static/images/default-cover.jpg'
        if self.cover_image.startswith('http'):
            return self.cover_image
        if self.cover_image.startswith('covers/'):
            return f'/static/uploads/{self.cover_image}'
        return f'/static/images/{self.cover_image}'

    def get_pages_list(self):
        """Splits full_content into pages or chapters for the interactive antique reader."""
        if not self.full_content:
            return [self.description or "No text content available."]
        # Split by explicit page markers or double line breaks into chunks
        if '---PAGE---' in self.full_content:
            pages = [p.strip() for p in self.full_content.split('---PAGE---') if p.strip()]
            return pages if pages else [self.full_content]
        
        # Split into roughly 600-word page slices
        words = self.full_content.split()
        if len(words) <= 300:
            return [self.full_content]
        
        chunk_size = 280
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i + chunk_size]))
        return chunks

    def __repr__(self):
        return f"<Material #{self.id} '{self.title}' [{self.category}]>"


class Feedback(db.Model):
    __tablename__ = 'feedbacks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Feedback from {self.name}: {self.subject}>"


class ReadingHistory(db.Model):
    __tablename__ = 'reading_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id', ondelete='CASCADE'), nullable=False)
    last_read_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    progress_percent = db.Column(db.Integer, default=0)
    is_favorite = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<ReadingHistory User:{self.user_id} Material:{self.material_id}>"
