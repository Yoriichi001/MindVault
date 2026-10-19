import os
from datetime import datetime
from flask import Flask
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import inspect, text

from config import Config
from App.models import db, bcrypt, User
from App.utils import mask_email

# Initialize extensions
login_manager = LoginManager()
login_manager.login_view = 'routes.login'
login_manager.login_message = "Please sign in to access your MindVault library."
login_manager.login_message_category = "warning"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"],
    storage_uri=Config.RATELIMIT_STORAGE_URI
)


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None


def auto_migrate(app):
    """
    Automatic Database Auto-Migration:
    Dynamic inspection using SQLAlchemy inspect(db.engine) to detect and auto-add
    new columns to existing SQLite / PostgreSQL tables without data loss.
    """
    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        with db.engine.connect() as conn:
            for table_name, table in db.metadata.tables.items():
                if table_name in existing_tables:
                    existing_cols = {col['name'] for col in inspector.get_columns(table_name)}
                    for col in table.columns:
                        if col.name not in existing_cols:
                            # Derive column type for SQL DDL
                            col_type = col.type.compile(db.engine.dialect)
                            default_clause = ""
                            if col.default is not None and hasattr(col.default, 'arg'):
                                if isinstance(col.default.arg, (int, float, bool)):
                                    default_clause = f" DEFAULT {int(col.default.arg) if isinstance(col.default.arg, bool) else col.default.arg}"
                            
                            app.logger.info(f"Auto-Migrating: Adding missing column '{col.name}' to table '{table_name}'")
                            alter_query = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{default_clause}"
                            try:
                                conn.execute(text(alter_query))
                                conn.commit()
                            except Exception as err:
                                app.logger.warning(f"Auto-migration notice for {table_name}.{col.name}: {err}")


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure ProxyFix for cloud deployment (Render, Heroku, AWS)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    # Register routes blueprint
    from App.routes import routes_bp
    app.register_blueprint(routes_bp)

    # Ensure required static upload directories exist
    upload_root = app.config['UPLOAD_FOLDER']
    for sub in ['avatars', 'books', 'covers']:
        os.makedirs(os.path.join(upload_root, sub), exist_ok=True)

    # Initialize Cloudinary cloud storage if configured
    try:
        from urllib.parse import urlparse
        import cloudinary
        cloudinary_url = app.config.get('CLOUDINARY_URL') or os.environ.get('CLOUDINARY_URL')
        if cloudinary_url and cloudinary_url.strip():
            clean_url = cloudinary_url.strip().strip("'\"")
            p = urlparse(clean_url)
            if p.hostname and p.username and p.password:
                cloudinary.config(
                    cloud_name=p.hostname,
                    api_key=p.username,
                    api_secret=p.password,
                    secure=True
                )
                app.logger.info(f"Cloudinary cloud media storage initialized for: {p.hostname}")
        else:
            c_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
            c_key = os.environ.get('CLOUDINARY_API_KEY')
            c_secret = os.environ.get('CLOUDINARY_API_SECRET')
            if c_name and c_key and c_secret:
                cloudinary.config(
                    cloud_name=c_name.strip().strip("'\""),
                    api_key=c_key.strip().strip("'\""),
                    api_secret=c_secret.strip().strip("'\""),
                    secure=True
                )
                app.logger.info(f"Cloudinary initialized via discrete credentials for: {c_name}")
    except Exception as ce:
        app.logger.warning(f"Cloudinary configuration notice: {ce}")

    # Database creation & auto-migration
    with app.app_context():
        db.create_all()
        auto_migrate(app)

    # Template Context Processors & Filters
    @app.context_processor
    def inject_global_template_vars():
        return {
            'app_name': app.config['APP_NAME'],
            'tagline': app.config['TAGLINE'],
            'community_url': app.config['COMMUNITY_URL'],
            'google_client_id': app.config['GOOGLE_CLIENT_ID'],
            'current_year': datetime.utcnow().year,
            'mask_email': mask_email
        }

    # Security Headers Hook
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Permissions policy for student browser safety
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        # Modern Content-Security-Policy (CSP) protecting against XSS and malicious script injections
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "img-src 'self' data: blob: https://images.unsplash.com https://accounts.google.com https://res.cloudinary.com https://*.googleusercontent.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline' https://accounts.google.com; "
            "frame-src https://accounts.google.com; "
            "connect-src 'self' https://accounts.google.com https://res.cloudinary.com;"
        )
        return response

    # Global Error Handlers (Eliminates raw 500 error screens)
    from flask import render_template

    @app.errorhandler(404)
    def handle_not_found(e):
        return render_template(
            'error.html',
            status_code=404,
            error_title="Page or Resource Not Found",
            error_message="The manuscript, page, or record you requested could not be discovered in the MindVault catalogue."
        ), 404

    @app.errorhandler(413)
    def handle_large_file(e):
        return render_template(
            'error.html',
            status_code=413,
            error_title="Artifact Size Exceeds Limit",
            error_message="The uploaded file exceeds the 16 MB maximum threshold. Please choose an image or document of smaller proportions."
        ), 413

    @app.errorhandler(500)
    @app.errorhandler(Exception)
    def handle_server_error(e):
        try:
            db.session.rollback()
        except Exception:
            pass
        app.logger.error(f"Handled application exception: {e}", exc_info=True)
        return render_template(
            'error.html',
            status_code=500,
            error_title="Internal Sanctum Notice",
            error_message="The vault encountered a brief disturbance while processing your request. Your records remain intact. Please re-try in a moment."
        ), 500

    return app
