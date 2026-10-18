from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError, Optional
from App.models import User
from App.utils import is_disposable_email

# Honeypot validation helper
def honeypot_check(form, field):
    if field.data:
        raise ValidationError("Bot activity detected. Form submission aborted.")


class LoginForm(FlaskForm):
    identity = StringField('Email or Username', validators=[DataRequired(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4)])
    remember_me = BooleanField('Keep Me Signed In')
    # Anti-bot honeypot field
    website = StringField('Website', validators=[honeypot_check])
    submit = SubmitField('Open MindVault')


class AdminLoginForm(FlaskForm):
    identity = StringField('Admin Username or Email', validators=[DataRequired(), Length(max=120)])
    password = PasswordField('Master Password', validators=[DataRequired()])
    # Anti-bot honeypot field
    website = StringField('Website', validators=[honeypot_check])
    submit = SubmitField('Authenticate As Administrator')


class RegisterForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(min=3, max=30),
            Regexp(r'^[a-zA-Z0-9_]+$', message="Username may only contain letters, numbers, and underscores.")
        ]
    )
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters."),
            Regexp(r'^(?=.*[A-Za-z])(?=.*\d).+$', message="Password must contain at least one letter and one number.")
        ]
    )
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords must match.")])
    # Anti-bot honeypot field
    website = StringField('Website', validators=[honeypot_check])
    submit = SubmitField('Create MindVault Account')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data.strip()).first()
        if user:
            raise ValidationError("That username is already claimed in the vault. Please choose another.")

    def validate_email(self, email):
        cleaned_email = email.data.strip().lower()
        if is_disposable_email(cleaned_email):
            raise ValidationError("Disposable or temporary email services are prohibited in MindVault.")
        user = User.query.filter_by(email=cleaned_email).first()
        if user:
            raise ValidationError("That email address is already registered. Please sign in.")



class AccountUpdateForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(min=3, max=30),
            Regexp(r'^[a-zA-Z0-9_]+$', message="Username may only contain letters, numbers, and underscores.")
        ]
    )
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    avatar = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Only image files (JPG, PNG, WEBP) are accepted.')])
    submit = SubmitField('Save Profile Changes')

    def __init__(self, current_user, *args, **kwargs):
        super(AccountUpdateForm, self).__init__(*args, **kwargs)
        self.current_user = current_user

    def validate_username(self, username):
        if username.data.strip() != self.current_user.username:
            user = User.query.filter_by(username=username.data.strip()).first()
            if user:
                raise ValidationError("Username already in use by another scholar.")

    def validate_email(self, email):
        if email.data.strip().lower() != self.current_user.email.lower():
            user = User.query.filter_by(email=email.data.strip().lower()).first()
            if user:
                raise ValidationError("Email already registered to another account.")


class PasswordResetRequestForm(FlaskForm):
    email = StringField('Registered Email', validators=[DataRequired(), Email()])
    website = StringField('Website', validators=[honeypot_check])
    submit = SubmitField('Send Password Reset Link')


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        'New Password',
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters."),
            Regexp(r'^(?=.*[A-Za-z])(?=.*\d).+$', message="Password must contain at least one letter and one number.")
        ]
    )
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password', message="Passwords must match.")])
    submit = SubmitField('Reset Password')



class MaterialForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=255)])
    author = StringField('Author / Researcher / Institution', validators=[DataRequired(), Length(max=150)])
    category = SelectField(
        'Vault Category',
        choices=[
            ('Books', 'Books (Textbooks & Literature)'),
            ('Research Papers', 'Research Papers (Journals & Publications)'),
            ('Study Materials', 'Study Materials (Notes, Guides & Handouts)')
        ],
        validators=[DataRequired()]
    )
    sub_category = StringField('Subject / Field', default='General', validators=[Optional(), Length(max=100)])
    description = TextAreaField('Overview / Synopsis', validators=[DataRequired()])
    content_preview = TextAreaField('Expository Excerpt (Quick Preview)', validators=[Optional()])
    full_content = TextAreaField(
        'Online Reading Content (Chapters / Text / Excerpt)',
        description="Text displayed in the vintage 3D dual-page online book reader. Use ---PAGE--- to create page boundaries.",
        validators=[Optional()]
    )
    cover_image = FileField('Book Cover Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only')])
    file = FileField('PDF Document File (For Online & Download)', validators=[FileAllowed(['pdf'], 'PDF documents only')])
    pages = IntegerField('Page Count', default=1, validators=[Optional()])
    is_featured = BooleanField('Feature in Spotlight')
    submit = SubmitField('Commit to Vault Database')


class FeedbackForm(FlaskForm):
    name = StringField('Your Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Your Email', validators=[DataRequired(), Email(), Length(max=120)])
    subject = StringField('Subject / Topic', validators=[DataRequired(), Length(max=150)])
    message = TextAreaField('Feedback / Suggestion / Review', validators=[DataRequired(), Length(min=5, max=3000)])
    rating = SelectField('Your Rating', choices=[('5', '5 - Masterpiece'), ('4', '4 - Very Good'), ('3', '3 - Helpful'), ('2', '2 - Needs Improvement'), ('1', '1 - Poor')], default='5')
    # Anti-bot honeypot
    website = StringField('Website', validators=[honeypot_check])
    submit = SubmitField('Inscribe Feedback')
