import io
import os
import re
import uuid
from urllib.parse import urlparse, urljoin
from flask import request, current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
import bleach
from PIL import Image

# Enforce Anti-DoS & Image Bomb Defense
Image.MAX_IMAGE_PIXELS = 10_000_000

# Allowed HTML tags and attributes for rich book text / markdown excerpts
ALLOWED_TAGS = [
    'p', 'b', 'i', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'hr', 'br', 'span'
]
ALLOWED_ATTRIBUTES = {
    '*': ['class'],
    'a': ['href', 'title', 'target'],
    'span': ['style']
}


def sanitize_html(text):
    """Sanitizes user or admin-provided HTML/rich text to mitigate Stored XSS."""
    if not text:
        return ""
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)


def is_safe_url(target):
    """
    Anti-Phishing & Open-Redirect Defense.
    Strictly validates that `next` URLs start with '/', do NOT start with '//',
    contain no backslashes, and have no external netloc.
    """
    if not target or not isinstance(target, str):
        return False
    # Ensure it starts with / and not //, and contains no backslash evasion
    if not target.startswith('/') or target.startswith('//') or '\\' in target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


# Common disposable / burner email domains used by automated spam bots
DISPOSABLE_EMAIL_DOMAINS = {
    'mailinator.com', 'guerrillamail.com', 'tempmail.com', 'throwawaymail.com',
    '10minutemail.com', 'sharklasers.com', 'yopmail.com', 'dispostable.com',
    'getairmail.com', 'trashmail.com', 'burnermail.io', 'mytemp.email',
    'temp-mail.org', 'fakeinbox.com', 'crazymailing.com', 'mohmal.com'
}


def is_disposable_email(email):
    """Detects and flags disposable burner email domains."""
    if not email or '@' not in email:
        return False
    domain = email.split('@')[-1].strip().lower()
    return domain in DISPOSABLE_EMAIL_DOMAINS



def mask_email(email):
    """
    Email Privacy: Mask email addresses from public displays.
    Example: john.doe@example.com -> j***e@example.com
    """
    if not email or '@' not in email:
        return "Protected"
    parts = email.split('@')
    name, domain = parts[0], parts[1]
    if len(name) <= 2:
        masked_name = name[0] + "*"
    else:
        masked_name = name[0] + ("*" * (len(name) - 2)) + name[-1]
    return f"{masked_name}@{domain}"


def generate_verification_token(email, salt="email-confirm-salt"):
    """Generates a cryptographic time-sensitive token for email verification."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=salt)


def verify_token(token, max_age=86400, salt="email-confirm-salt"):
    """Verifies the cryptographic email token within expiration window (default 24h)."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=salt, max_age=max_age)
        return email
    except (SignatureExpired, BadTimeSignature, Exception):
        return None


def save_uploaded_image(file_storage, subfolder='avatars', max_dim=800, quality=85):
    """
    Secure image upload handler:
    1. Validates extension
    2. Inspects file with Pillow
    3. Prevents decompression bombs (MAX_IMAGE_PIXELS)
    4. Strips EXIF metadata & converts to RGB
    5. Saves to Cloudinary CDN if CLOUDINARY_URL is configured, else local storage
    """
    if not file_storage or not file_storage.filename:
        return None
    
    filename = file_storage.filename.lower()
    ext = filename.rsplit('.', 1)[-1] if '.' in filename else ''
    if ext not in {'png', 'jpg', 'jpeg', 'webp'}:
        return None

    try:
        # Read image securely
        img = Image.open(file_storage.stream)
        img.verify()  # Verify integrity
        
        # Re-open for transformation (verify closes the image stream)
        file_storage.stream.seek(0)
        img = Image.open(file_storage.stream)
        
        # Convert to RGB to discard RGBA / CMYK color anomalies
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Resize if exceeding max dimensions maintaining aspect ratio
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        
        # Check for Cloudinary configuration
        cloudinary_url = current_app.config.get('CLOUDINARY_URL') or os.environ.get('CLOUDINARY_URL')
        if cloudinary_url:
            try:
                import cloudinary
                import cloudinary.uploader
                cloudinary.config(cloudinary_url=cloudinary_url)
                
                buffer = io.BytesIO()
                img.save(buffer, 'JPEG', quality=quality, optimize=True)
                buffer.seek(0)
                
                upload_res = cloudinary.uploader.upload(
                    buffer,
                    folder=f"mindvault/{subfolder}",
                    resource_type="image"
                )
                if upload_res and 'secure_url' in upload_res:
                    return upload_res['secure_url']
            except Exception as ce:
                current_app.logger.warning(f"Cloudinary image upload failed, falling back to local: {ce}")

        # Local storage fallback
        target_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(target_dir, exist_ok=True)
        unique_name = f"{uuid.uuid4().hex}.jpg"
        save_path = os.path.join(target_dir, unique_name)
        img.save(save_path, 'JPEG', quality=quality, optimize=True)
        return f"{subfolder}/{unique_name}"
    except Exception as e:
        current_app.logger.error(f"Image upload security error: {e}")
        return None


def save_uploaded_pdf(file_storage):
    """
    Secure PDF upload handler:
    1. Validates .pdf extension
    2. Checks magic bytes (%PDF)
    3. Saves to Cloudinary CDN if CLOUDINARY_URL is configured, else local storage
    """
    if not file_storage or not file_storage.filename:
        return None, 0.0
        
    filename = file_storage.filename.lower()
    if not filename.endswith('.pdf'):
        return None, 0.0
        
    try:
        # Check magic bytes
        header = file_storage.stream.read(5)
        file_storage.stream.seek(0)
        if header != b'%PDF-':
            return None, 0.0

        # Check for Cloudinary configuration
        cloudinary_url = current_app.config.get('CLOUDINARY_URL') or os.environ.get('CLOUDINARY_URL')
        if cloudinary_url:
            try:
                import cloudinary
                import cloudinary.uploader
                cloudinary.config(cloudinary_url=cloudinary_url)
                
                unique_id = uuid.uuid4().hex
                upload_res = cloudinary.uploader.upload(
                    file_storage.stream,
                    folder="mindvault/books",
                    resource_type="raw",
                    public_id=f"{unique_id}.pdf"
                )
                if upload_res and 'secure_url' in upload_res:
                    size_bytes = upload_res.get('bytes', 0)
                    size_mb = round(size_bytes / (1024 * 1024), 2)
                    return upload_res['secure_url'], size_mb
            except Exception as ce:
                current_app.logger.warning(f"Cloudinary PDF upload failed, falling back to local: {ce}")
                file_storage.stream.seek(0)
            
        target_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'books')
        os.makedirs(target_dir, exist_ok=True)
        
        unique_name = f"{uuid.uuid4().hex}.pdf"
        save_path = os.path.join(target_dir, unique_name)
        file_storage.save(save_path)
        
        size_bytes = os.path.getsize(save_path)
        size_mb = round(size_bytes / (1024 * 1024), 2)
        return f"books/{unique_name}", size_mb
    except Exception as e:
        current_app.logger.error(f"PDF upload error: {e}")
        return None, 0.0
