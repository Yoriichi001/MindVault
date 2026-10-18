from functools import wraps
from flask import flash, redirect, url_for, request, abort
from flask_login import current_user
from App.utils import is_safe_url


def admin_required(f):
    """
    Role-based access control decorator.
    Enforces that only authenticated users with role=='admin' can access decorated routes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Administrator credentials required to enter this sanctum.", "warning")
            next_url = request.full_path if is_safe_url(request.full_path) else url_for('routes.admin_dashboard')
            return redirect(url_for('routes.admin_login', next=next_url))
        if not current_user.is_admin:
            flash("Access denied: You lack master administrative authority in MindVault.", "danger")
            return redirect(url_for('routes.index'))
        return f(*args, **kwargs)
    return decorated_function


def verified_required(f):
    """
    Ensures user has confirmed their email address before accessing critical actions.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('routes.login', next=request.url))
        if not current_user.is_verified:
            flash("Please verify your email address to unlock this privilege.", "info")
            return redirect(url_for('routes.resend_verification'))
        return f(*args, **kwargs)
    return decorated_function
