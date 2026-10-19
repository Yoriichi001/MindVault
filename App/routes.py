import os
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    abort, current_app, jsonify, send_from_directory, send_file
)
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_, func

from App.models import db, User, Material, Feedback, ReadingHistory
from App.forms import (
    LoginForm, AdminLoginForm, RegisterForm, AccountUpdateForm,
    MaterialForm, FeedbackForm, PasswordResetRequestForm, ResetPasswordForm
)
from App.decorators import admin_required
from App.utils import (
    is_safe_url, mask_email, generate_verification_token, verify_token,
    save_uploaded_image, save_uploaded_pdf, sanitize_html
)
from App import limiter

routes_bp = Blueprint('routes', __name__)


# ==========================================
# 1. PUBLIC LIBRARY & CATALOGUE ROUTES
# ==========================================

@routes_bp.route('/')
@routes_bp.route('/library')
def index():
    """
    Main Digital Library Home.
    Preserves the authentic vintage wooden book opening visual experience
    with dynamic database catalog, category filters, and search.
    """
    category = request.args.get('category', 'all')
    # Limit search query length to 60 chars to prevent expensive full-table scans
    search_query = request.args.get('q', '').strip()[:60]


    query = Material.query
    if category in ['Books', 'Research Papers', 'Study Materials']:
        query = query.filter_by(category=category)
    
    if search_query:
        query = query.filter(
            or_(
                Material.title.ilike(f"%{search_query}%"),
                Material.author.ilike(f"%{search_query}%"),
                Material.sub_category.ilike(f"%{search_query}%"),
                Material.description.ilike(f"%{search_query}%")
            )
        )

    materials = query.order_by(Material.is_featured.desc(), Material.created_at.desc()).all()
    
    # Counts for category tabs
    total_books = Material.query.filter_by(category='Books').count()
    total_papers = Material.query.filter_by(category='Research Papers').count()
    total_study = Material.query.filter_by(category='Study Materials').count()

    return render_template(
        'index.html',
        materials=materials,
        selected_category=category,
        search_query=search_query,
        total_books=total_books,
        total_papers=total_papers,
        total_study=total_study
    )


@routes_bp.route('/books')
def books_view():
    return redirect(url_for('routes.index', category='Books'))


@routes_bp.route('/research-papers')
def papers_view():
    return redirect(url_for('routes.index', category='Research Papers'))


@routes_bp.route('/study-materials')
def study_materials_view():
    return redirect(url_for('routes.index', category='Study Materials'))


@routes_bp.route('/community')
def community_redirect():
    """Redirects to student community discussion platform."""
    return redirect(current_app.config['COMMUNITY_URL'])


@routes_bp.route('/material/<int:material_id>')
def material_detail(material_id):
    """Product detail view of book, research paper or study material."""
    material = Material.query.get_or_404(material_id)
    material.views_count = (material.views_count or 0) + 1
    db.session.commit()

    # Track reading history if user is authenticated
    if current_user.is_authenticated:
        history = ReadingHistory.query.filter_by(user_id=current_user.id, material_id=material.id).first()
        if not history:
            history = ReadingHistory(user_id=current_user.id, material_id=material.id)
            db.session.add(history)
        history.last_read_at = func.now()
        db.session.commit()

    return render_template('material_detail.html', material=material)


@routes_bp.route('/read/<int:material_id>')
def read_online(material_id):
    """
    Antique in-browser dual-page reader for online reading.
    Anyone can read online freely on the website!
    """
    material = Material.query.get_or_404(material_id)
    material.views_count = (material.views_count or 0) + 1
    db.session.commit()

    pages = material.get_pages_list()
    current_page = request.args.get('p', 1, type=int)
    if current_page < 1:
        current_page = 1
    if current_page > len(pages):
        current_page = len(pages)

    if current_user.is_authenticated:
        history = ReadingHistory.query.filter_by(user_id=current_user.id, material_id=material.id).first()
        if not history:
            history = ReadingHistory(user_id=current_user.id, material_id=material.id)
            db.session.add(history)
        history.progress_percent = int((current_page / len(pages)) * 100) if pages else 100
        db.session.commit()

    return render_template(
        'read_book.html',
        material=material,
        pages=pages,
        current_page=current_page,
        total_pages=len(pages)
    )


@routes_bp.route('/download/<int:material_id>')
def download_pdf(material_id):
    """
    Download PDF document:
    If user is authenticated -> Downloads the file & increments counter.
    If user is NOT authenticated -> Redirects to login panel with flash message.
    """
    if not current_user.is_authenticated:
        flash("Authentication required. Please sign in to your MindVault account to download PDF materials.", "warning")
        return redirect(url_for('routes.login', next=request.path))

    material = Material.query.get_or_404(material_id)

    if not material.file_path:
        flash(f"Digital PDF for '{material.title}' is currently undergoing preservation. You can read the full text online right now!", "info")
        return redirect(url_for('routes.read_online', material_id=material.id))

    # Remote Cloudinary CDN file delivery
    if material.file_path.startswith('http://') or material.file_path.startswith('https://'):
        material.downloads_count = (material.downloads_count or 0) + 1
        db.session.commit()
        return redirect(material.file_path)

    upload_folder = current_app.config['UPLOAD_FOLDER']
    full_path = os.path.join(upload_folder, material.file_path)

    if not os.path.exists(full_path):
        flash("The archival file is being re-indexed. Please read online in the meantime.", "warning")
        return redirect(url_for('routes.read_online', material_id=material.id))

    material.downloads_count = (material.downloads_count or 0) + 1
    db.session.commit()

    directory, filename = os.path.split(full_path)
    safe_download_name = f"{material.title.replace(' ', '_')}.pdf"
    return send_from_directory(directory, filename, as_attachment=True, download_name=safe_download_name)


@routes_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    """User feedback and suggestions form with honeypot bot defense."""
    form = FeedbackForm()
    if request.method == 'GET' and current_user.is_authenticated:
        form.name.data = current_user.username
        form.email.data = current_user.email

    if form.validate_on_submit():
        fb = Feedback(
            name=sanitize_html(form.name.data.strip()),
            email=form.email.data.strip().lower(),
            subject=sanitize_html(form.subject.data.strip()),
            message=sanitize_html(form.message.data.strip()),
            rating=int(form.rating.data),
            user_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(fb)
        db.session.commit()
        flash("Your thoughts have been inscribed into the MindVault archives. Thank you for your feedback!", "success")
        return redirect(url_for('routes.index'))

    return render_template('feedback.html', form=form)


# ==========================================
# 2. AUTHENTICATION & VERIFICATION
# ==========================================

@routes_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute; 30 per hour")
def login():
    """Student and reader login."""
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))

    form = LoginForm()
    if form.validate_on_submit():
        ident = form.identity.data.strip()
        user = User.query.filter(or_(User.email == ident.lower(), User.username == ident)).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("This account has been deactivated by the administration.", "danger")
                return redirect(url_for('routes.login'))

            login_user(user, remember=form.remember_me.data)
            flash(f"Welcome back to the Atelier of Knowledge, {user.username}.", "success")

            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('routes.index'))
        else:
            flash("Invalid credentials. Please verify your email/username and password.", "danger")
    elif request.method == 'POST' and form.website.data:
        flash("Bot activity detected. Form submission aborted.", "danger")

    return render_template('login.html', form=form)


@routes_bp.route('/admin', methods=['GET', 'POST'])
@routes_bp.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute; 20 per hour")
def admin_login():
    """Dedicated administrative login portal."""
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('routes.admin_dashboard'))

    form = AdminLoginForm()
    if form.validate_on_submit():
        ident = form.identity.data.strip()
        user = User.query.filter(or_(User.email == ident.lower(), User.username == ident)).first()

        if user and user.check_password(form.password.data):
            if not user.is_admin:
                flash("Access prohibited. Administrator privileges required.", "danger")
                return redirect(url_for('routes.admin_login'))

            login_user(user)
            flash("Master Administrator authentication verified.", "success")
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('routes.admin_dashboard'))
        else:
            flash("Administrator authentication failed.", "danger")
    elif request.method == 'POST' and form.website.data:
        flash("Bot activity detected. Form submission aborted.", "danger")

    return render_template('admin_login.html', form=form)


@routes_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute; 15 per hour")
def register():
    """Student registration with honeypot and sanitized input."""
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        password = form.password.data

        new_user = User(
            username=username,
            email=email,
            role='student',
            is_verified=False,  # Unverified until email confirmation is completed
            avatar='default-avatar.png'
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash("Your MindVault scholar account has been created! Please verify your email to unlock all privileges.", "success")
        return redirect(url_for('routes.account'))
    elif request.method == 'POST':
        if form.website.data:
            flash("Bot activity detected. Form submission aborted.", "danger")


    return render_template('register.html', form=form)


@routes_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have successfully signed out of MindVault. Come back soon!", "info")
    return redirect(url_for('routes.index'))


@routes_bp.route('/auth/google', methods=['POST'])
def google_auth():
    """
    Google OAuth 2.0 / GIS handler.
    Validates server-side id_token and logs in or registers user.
    Uses dual verification: local google-auth cryptographic validation
    with seamless fallback to Google's official tokeninfo endpoint.
    """
    data = request.get_json(silent=True) or request.form
    token = data.get('credential') or data.get('id_token')
    
    if not token:
        return jsonify({'success': False, 'message': 'Missing Google token'}), 400

    token = token.strip()
    client_id = (current_app.config.get('GOOGLE_CLIENT_ID') or '').strip()

    try:
        # If running in local demo without live google client ID
        if not client_id or client_id == 'DEMO_MINDVAULT_GOOGLE_CLIENT_ID':
            email = "scholar.demo@mindvault.edu"
            name = "Demo Scholar"
            sub = "google-demo-sub-12345"
            picture = "default-avatar.png"
        else:
            idinfo = None
            verify_error = None

            # Primary: Verify using google-auth library
            try:
                from google.oauth2 import id_token
                from google.auth.transport import requests as google_requests
                idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
            except Exception as e1:
                verify_error = e1
                current_app.logger.warning(f"google-auth verify failed: {e1}, trying tokeninfo endpoint...")

            # Secondary: Google official tokeninfo endpoint fallback
            if not idinfo:
                try:
                    import urllib.request
                    import json
                    token_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
                    req = urllib.request.Request(token_url, headers={'User-Agent': 'MindVault-Auth/1.0'})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        token_data = json.loads(resp.read().decode('utf-8'))
                    
                    aud = token_data.get('aud')
                    if aud != client_id:
                        raise ValueError(f"Audience mismatch: token audience '{aud}' does not match configured client_id '{client_id}'")
                    
                    iss = token_data.get('iss')
                    if iss not in ['accounts.google.com', 'https://accounts.google.com']:
                        raise ValueError(f"Untrusted issuer: {iss}")

                    idinfo = token_data
                except Exception as e2:
                    current_app.logger.error(f"Google tokeninfo endpoint failed: {e2}")
                    raise verify_error or e2

            email = idinfo['email']
            name = idinfo.get('name', email.split('@')[0])
            sub = idinfo['sub']
            picture = idinfo.get('picture')

        user = User.query.filter(or_(User.email == email.lower(), User.google_id == sub)).first()
        if not user:
            # Generate valid unique alphanumeric username
            base_user = ''.join(c for c in name if c.isalnum() or c == '_')[:20] or "scholar"
            username = base_user
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_user}_{counter}"
                counter += 1

            user = User(
                username=username,
                email=email.lower(),
                google_id=sub,
                role='student',
                is_verified=True,
                avatar=picture or 'default-avatar.png'
            )
            db.session.add(user)
            db.session.commit()
        else:
            # Update and link Google attributes
            updated = False
            if not user.google_id:
                user.google_id = sub
                updated = True
            if not user.is_verified:
                user.is_verified = True
                updated = True
            if picture and (not user.avatar or user.avatar == 'default-avatar.png'):
                user.avatar = picture
                updated = True
            if updated:
                db.session.commit()

        if not user.is_active:
            return jsonify({'success': False, 'message': 'Account is suspended or inactive. Please contact administration.'}), 403

        login_user(user, remember=True)
        return jsonify({'success': True, 'redirect': url_for('routes.index')})
    except Exception as e:
        current_app.logger.error(f"Google auth error: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Google authentication failed: {str(e)}'}), 400


@routes_bp.route('/reset-password', methods=['GET', 'POST'])
@limiter.limit("3 per minute; 10 per hour")
def reset_password_request():
    """User enumeration defense: Always returns identical neutral response."""
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_verification_token(user.email, salt='password-reset-salt')
            # Security Hardening: Never log raw reset tokens to server logs
            current_app.logger.info(f"Password reset dispatch processed for: {mask_email(email)}")

        flash("If that email address exists in our archives, password reset instructions have been dispatched.", "info")
        return redirect(url_for('routes.login'))

    return render_template('reset_password_request.html', form=form)


@routes_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    email = verify_token(token, max_age=3600, salt='password-reset-salt')
    if not email:
        flash("This reset scroll has expired or is invalid.", "danger")
        return redirect(url_for('routes.reset_password_request'))

    user = User.query.filter_by(email=email).first_or_404()
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been successfully renewed. Please log in.", "success")
        return redirect(url_for('routes.login'))

    return render_template('reset_password.html', form=form)


@routes_bp.route('/verify-email/<token>')
def verify_email(token):
    email = verify_token(token, max_age=86400, salt='email-confirm-salt')
    if not email:
        flash("Email verification link expired or invalid.", "danger")
        return redirect(url_for('routes.index'))

    user = User.query.filter_by(email=email).first_or_404()
    user.is_verified = True
    db.session.commit()
    flash("Your email address has been verified in the MindVault registry!", "success")
    return redirect(url_for('routes.account'))


@routes_bp.route('/resend-verification')
@login_required
def resend_verification():
    token = generate_verification_token(current_user.email, salt='email-confirm-salt')
    # Security Hardening: Omit raw token from logs; notify user via secure flash
    current_app.logger.info(f"Verification dispatch generated for scholar ID: {current_user.id}")
    flash(f"Verification scroll refreshed. Please check your inbox at {mask_email(current_user.email)} to confirm.", "info")
    return redirect(url_for('routes.account'))



# ==========================================
# 3. ACCOUNT PANEL / PROFILE
# ==========================================

@routes_bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    """
    Account Panel:
    Allows user to update username, email, and upload profile photo (avatar).
    Provides default avatar if user doesn't have one.
    Displays reading history and stats.
    """
    try:
        form = AccountUpdateForm(current_user=current_user)
        if request.method == 'POST':
            if form.validate_on_submit():
                # Handle avatar upload with Pillow bomb defense
                if form.avatar.data and hasattr(form.avatar.data, 'filename') and form.avatar.data.filename:
                    avatar_path = save_uploaded_image(form.avatar.data, subfolder='avatars', max_dim=400)
                    if avatar_path:
                        current_user.avatar = avatar_path
                    else:
                        flash("Failed to process image. Ensure it is a valid JPG/PNG/WEBP image under 16MB.", "danger")

                if form.username.data:
                    current_user.username = form.username.data.strip()
                if form.email.data:
                    current_user.email = form.email.data.strip().lower()

                db.session.commit()
                flash("Your scholar profile has been updated.", "success")
                return redirect(url_for('routes.account'))
            else:
                # Validation errors: flash them clearly to the user
                for field_name, error_msgs in form.errors.items():
                    for err in error_msgs:
                        field_label = form[field_name].label.text if field_name in form else field_name
                        flash(f"{field_label}: {err}", "danger")
        elif request.method == 'GET':
            form.username.data = current_user.username
            form.email.data = current_user.email
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Account update error: {e}", exc_info=True)
        flash(f"Profile update could not be processed: {str(e)}", "danger")
        return redirect(url_for('routes.account'))

    # Fetch user reading history safely
    try:
        history = ReadingHistory.query.filter_by(user_id=current_user.id).order_by(ReadingHistory.last_read_at.desc()).limit(10).all()
    except Exception as e:
        current_app.logger.warning(f"Could not load reading history: {e}")
        history = []

    try:
        user_feedbacks = Feedback.query.filter_by(user_id=current_user.id).all()
    except Exception as e:
        current_app.logger.warning(f"Could not load feedbacks: {e}")
        user_feedbacks = []

    return render_template(
        'profile.html',
        form=form,
        history=history,
        feedbacks=user_feedbacks
    )


# ==========================================
# 4. ADMIN PANEL (ROLE-BASED RBAC)
# ==========================================

@routes_bp.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """
    Live statistical counts of all database tables.
    """
    total_users = User.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_admins = User.query.filter_by(role='admin').count()

    total_materials = Material.query.count()
    total_books = Material.query.filter_by(category='Books').count()
    total_papers = Material.query.filter_by(category='Research Papers').count()
    total_study = Material.query.filter_by(category='Study Materials').count()

    total_feedbacks = Feedback.query.count()
    unread_feedbacks = Feedback.query.filter_by(is_read=False).count()

    # Aggregate views & downloads
    total_views = db.session.query(func.coalesce(func.sum(Material.views_count), 0)).scalar()
    total_downloads = db.session.query(func.coalesce(func.sum(Material.downloads_count), 0)).scalar()

    recent_users = User.query.order_by(User.created_at.desc()).limit(6).all()
    recent_feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).limit(6).all()
    recent_materials = Material.query.order_by(Material.created_at.desc()).limit(6).all()

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_students=total_students,
        total_admins=total_admins,
        total_materials=total_materials,
        total_books=total_books,
        total_papers=total_papers,
        total_study=total_study,
        total_feedbacks=total_feedbacks,
        unread_feedbacks=unread_feedbacks,
        total_views=total_views,
        total_downloads=total_downloads,
        recent_users=recent_users,
        recent_feedbacks=recent_feedbacks,
        recent_materials=recent_materials
    )


@routes_bp.route('/admin/materials')
@admin_required
def admin_materials():
    """Paginated CRUD view for all books, research papers, and study materials."""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', 'all')
    search = request.args.get('search', '').strip()

    query = Material.query
    if category != 'all':
        query = query.filter_by(category=category)
    if search:
        query = query.filter(
            or_(
                Material.title.ilike(f"%{search}%"),
                Material.author.ilike(f"%{search}%"),
                Material.sub_category.ilike(f"%{search}%")
            )
        )

    pagination = query.order_by(Material.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template(
        'admin/materials.html',
        pagination=pagination,
        category=category,
        search=search
    )


@routes_bp.route('/admin/materials/new', methods=['GET', 'POST'])
@admin_required
def admin_material_new():
    """Upload/add a new Book, Research Paper, or Study Material."""
    form = MaterialForm()
    
    # Pre-select category if passed in URL (e.g. ?category=Books or ?type=Research+Papers)
    if request.method == 'GET':
        prefill_cat = request.args.get('category') or request.args.get('type')
        if prefill_cat in ['Books', 'Research Papers', 'Study Materials']:
            form.category.data = prefill_cat

    if form.validate_on_submit():
        cover_path = None
        if form.cover_image.data:
            cover_path = save_uploaded_image(form.cover_image.data, subfolder='covers', max_dim=900)

        pdf_path, size_mb = None, 0.0
        if form.file.data:
            pdf_path, size_mb = save_uploaded_pdf(form.file.data)

        material = Material(
            title=sanitize_html(form.title.data.strip()),
            author=sanitize_html(form.author.data.strip()),
            category=form.category.data,
            sub_category=sanitize_html(form.sub_category.data.strip() if form.sub_category.data else 'General'),
            description=sanitize_html(form.description.data.strip()),
            content_preview=sanitize_html(form.content_preview.data.strip() if form.content_preview.data else ''),
            full_content=form.full_content.data.strip() if form.full_content.data else '',
            cover_image=cover_path,
            file_path=pdf_path,
            file_size_mb=size_mb,
            pages=form.pages.data or 1,
            edition_year=sanitize_html(form.edition_year.data.strip() if form.edition_year.data else ''),
            isbn_doi=sanitize_html(form.isbn_doi.data.strip() if form.isbn_doi.data else ''),
            language=sanitize_html(form.language.data.strip() if form.language.data else 'English'),
            is_featured=form.is_featured.data
        )
        db.session.add(material)
        db.session.commit()
        flash(f"'{material.title}' has been successfully inscribed into the {material.category} collection!", "success")
        return redirect(url_for('routes.admin_materials'))

    return render_template('admin/material_form.html', form=form, title="Upload New Material")


@routes_bp.route('/admin/materials/edit/<int:material_id>', methods=['GET', 'POST'])
@admin_required
def admin_material_edit(material_id):
    """Edit existing book/paper/material."""
    material = Material.query.get_or_404(material_id)
    form = MaterialForm()

    if form.validate_on_submit():
        if form.cover_image.data:
            cover_path = save_uploaded_image(form.cover_image.data, subfolder='covers', max_dim=900)
            if cover_path:
                material.cover_image = cover_path

        if form.file.data:
            pdf_path, size_mb = save_uploaded_pdf(form.file.data)
            if pdf_path:
                material.file_path = pdf_path
                material.file_size_mb = size_mb

        material.title = sanitize_html(form.title.data.strip())
        material.author = sanitize_html(form.author.data.strip())
        material.category = form.category.data
        material.sub_category = sanitize_html(form.sub_category.data.strip() if form.sub_category.data else 'General')
        material.description = sanitize_html(form.description.data.strip())
        material.content_preview = sanitize_html(form.content_preview.data.strip() if form.content_preview.data else '')
        material.full_content = form.full_content.data.strip() if form.full_content.data else ''
        material.pages = form.pages.data or material.pages
        material.edition_year = sanitize_html(form.edition_year.data.strip() if form.edition_year.data else '')
        material.isbn_doi = sanitize_html(form.isbn_doi.data.strip() if form.isbn_doi.data else '')
        material.language = sanitize_html(form.language.data.strip() if form.language.data else 'English')
        material.is_featured = form.is_featured.data

        db.session.commit()
        flash(f"Material '{material.title}' updated successfully.", "success")
        return redirect(url_for('routes.admin_materials'))

    elif request.method == 'GET':
        form.title.data = material.title
        form.author.data = material.author
        form.category.data = material.category
        form.sub_category.data = material.sub_category
        form.description.data = material.description
        form.content_preview.data = material.content_preview
        form.full_content.data = material.full_content
        form.pages.data = material.pages
        form.edition_year.data = material.edition_year or ''
        form.isbn_doi.data = material.isbn_doi or ''
        form.language.data = material.language or 'English'
        form.is_featured.data = material.is_featured

    return render_template('admin/material_form.html', form=form, title=f"Edit: {material.title}", material=material)



@routes_bp.route('/admin/materials/delete/<int:material_id>', methods=['POST'])
@admin_required
def admin_material_delete(material_id):
    """Cascading deletion of material and orphaned file assets."""
    material = Material.query.get_or_404(material_id)
    title = material.title

    # Clean up file assets from disk
    upload_root = current_app.config['UPLOAD_FOLDER']
    if material.file_path:
        p = os.path.join(upload_root, material.file_path)
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception as e:
                current_app.logger.warning(f"Could not remove PDF file: {e}")

    if material.cover_image and material.cover_image.startswith('covers/'):
        c = os.path.join(upload_root, material.cover_image)
        if os.path.exists(c):
            try:
                os.remove(c)
            except Exception as e:
                current_app.logger.warning(f"Could not remove cover image: {e}")

    db.session.delete(material)
    db.session.commit()
    flash(f"'{title}' has been removed from MindVault.", "info")
    return redirect(url_for('routes.admin_materials'))


@routes_bp.route('/admin/users')
@admin_required
def admin_users():
    """User Management Panel: check registered users, search, filter, paginate."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    role_filter = request.args.get('role', 'all')

    query = User.query
    if role_filter != 'all':
        query = query.filter_by(role=role_filter)
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )

    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', pagination=pagination, search=search, role_filter=role_filter)


@routes_bp.route('/admin/users/toggle-role/<int:user_id>', methods=['POST'])
@admin_required
def admin_user_toggle_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot modify your own administrative rank.", "warning")
        return redirect(url_for('routes.admin_users'))

    user.role = 'student' if user.role == 'admin' else 'admin'
    db.session.commit()
    flash(f"User {user.username} role updated to {user.role}.", "success")
    return redirect(url_for('routes.admin_users'))


@routes_bp.route('/admin/users/toggle-active/<int:user_id>', methods=['POST'])
@admin_required
def admin_user_toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own administrative account.", "warning")
        return redirect(url_for('routes.admin_users'))

    user.is_active = not user.is_active
    db.session.commit()
    status_str = "activated" if user.is_active else "deactivated"
    flash(f"User {user.username} has been {status_str}.", "info")
    return redirect(url_for('routes.admin_users'))


@routes_bp.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_user_delete(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete your own administrative session.", "danger")
        return redirect(url_for('routes.admin_users'))

    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f"User {username} deleted from database.", "info")
    return redirect(url_for('routes.admin_users'))


@routes_bp.route('/admin/feedbacks')
@admin_required
def admin_feedbacks():
    """Feedback Section in admin panel."""
    page = request.args.get('page', 1, type=int)
    feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/feedbacks.html', pagination=feedbacks)


@routes_bp.route('/admin/feedbacks/read/<int:feedback_id>', methods=['POST'])
@admin_required
def admin_feedback_mark_read(feedback_id):
    fb = Feedback.query.get_or_404(feedback_id)
    fb.is_read = True
    db.session.commit()
    return redirect(url_for('routes.admin_feedbacks'))


@routes_bp.route('/admin/feedbacks/delete/<int:feedback_id>', methods=['POST'])
@admin_required
def admin_feedback_delete(feedback_id):
    fb = Feedback.query.get_or_404(feedback_id)
    db.session.delete(fb)
    db.session.commit()
    flash("Feedback entry cleared.", "info")
    return redirect(url_for('routes.admin_feedbacks'))
