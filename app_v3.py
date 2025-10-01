"""
EZWAI SMM V3.0 Application - State-of-the-Art AI Content Generation
- GPT-5-mini with Responses API and reasoning (medium effort)
- SeeDream-4 for 2K photorealistic magazine photography
- Enhanced prompt engineering for professional results
"""
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import os
import re
from datetime import timedelta, datetime
from perplexity_ai_integration import generate_blog_post_ideas, query_management
from openai_integration_v3 import create_blog_post_with_images_v3  # V3 with GPT-5-mini + SeeDream-4
from wordpress_integration import create_wordpress_post
from email_notification import send_email_notification
from email_verification import generate_verification_code, get_code_expiry, send_verification_email, verify_code
import traceback

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# CORS Configuration
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://funnelmngr.com",
            "https://www.funnelmngr.com",
            "http://localhost:5000",
            "https://127.0.0.1:5000",
            "http://127.0.0.1:5000"
        ]
    }
}, supports_credentials=True)

# Consolidated Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ezwai_smm.db')  # SQLite: portable, no service required
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('EMAIL_HOST')
app.config['MAIL_PORT'] = int(os.getenv('EMAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASSWORD')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'serve_auth'  # Redirect to /auth page instead of API endpoint

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    phone = db.Column(db.String(20))
    billing_address = db.Column(db.String(200))
    openai_api_key = db.Column(db.String(255))
    wordpress_rest_api_url = db.Column(db.String(255))
    wordpress_username = db.Column(db.String(80))
    wordpress_password = db.Column(db.String(255))
    perplexity_api_token = db.Column(db.String(255))
    queries = db.Column(db.JSON)
    system_prompt = db.Column(db.Text)
    schedule = db.Column(db.JSON)
    specific_topic_queries = db.Column(db.JSON)
    last_query_index = db.Column(db.Integer, default=0)

    # 2FA email verification fields
    email_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6))
    verification_code_expiry = db.Column(db.DateTime)
    verification_attempts = db.Column(db.Integer, default=0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class CompletedJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scheduled_time = db.Column(db.DateTime(timezone=True), nullable=False)
    completed_time = db.Column(db.DateTime(timezone=True), nullable=True)
    post_title = db.Column(db.String(255), nullable=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'scheduled_time', name='_user_scheduled_time_uc'),)

# Global error handler
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}")
    return jsonify(error=str(e)), 500

# Add CORS headers to all responses
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin', '*')
    response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

# Handle OPTIONS requests
@app.route('/', methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path=''):
    return '', 204

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_env_file(user):
    """Generate per-user environment file"""
    env_content = f"""OPENAI_API_KEY="{user.openai_api_key}"
WORDPRESS_REST_API_URL="{user.wordpress_rest_api_url}"
WORDPRESS_USERNAME="{user.wordpress_username}"
WORDPRESS_PASSWORD="{user.wordpress_password}"
PERPLEXITY_AI_API_TOKEN="{user.perplexity_api_token}"
"""
    with open(f'.env.user_{user.id}', 'w') as f:
        f.write(env_content)

def is_valid_openai_api_key(api_key):
    """Validate OpenAI API key format"""
    return bool(re.match(r'^sk-[A-Za-z0-9_-]{32,}$', api_key))

def is_valid_wordpress_url(url):
    """Validate WordPress URL format"""
    return url.endswith('/') or url.endswith('/wp-json') or url.endswith('/wp-json/wp/v2')

def is_valid_perplexity_api_token(token):
    """Validate Perplexity API token format"""
    return bool(re.match(r'^pplx-[A-Za-z0-9]{32,}$', token))

def create_blog_post_v3(user_id):
    """
    V3.0: State-of-the-art blog post creation with:
    - GPT-5-mini with reasoning (medium effort)
    - SeeDream-4 2K photorealistic images
    - Enhanced photographic prompt engineering
    """
    user = User.query.get(user_id)
    if not user:
        logger.error(f"User {user_id} not found")
        return None, "User not found"

    query = query_management(user_id)
    if not query:
        logger.error(f"No valid query found for user {user_id}")
        return None, "No valid query found for user"

    logger.info(f"[V3] Using query for user {user_id}: {query}")

    blog_post_ideas = generate_blog_post_ideas(query, user_id)
    if not blog_post_ideas:
        logger.error(f"No blog post ideas generated for user {user_id}")
        return None, "No blog post ideas generated"

    blog_post_idea = blog_post_ideas[0]
    system_prompt = user.system_prompt or "Write a comprehensive, engaging article in a professional but conversational tone suitable for a business magazine."

    logger.info(f"[V3] Creating magazine-style blog post with GPT-5-mini reasoning...")
    logger.info(f"Idea: {blog_post_idea[:100]}...")

    # Use the new V3 function with GPT-5-mini + SeeDream-4
    processed_post, error = create_blog_post_with_images_v3(blog_post_idea, user_id, system_prompt)
    if error:
        logger.error(f"Error in create_blog_post_with_images_v3 for user {user_id}: {error}")
        return None, error

    title = processed_post['title']
    blog_post_content = processed_post['content']
    hero_image_url = processed_post['hero_image_url']

    logger.info(f"[V3] Article created with reasoning. Images: {len([img for img in processed_post['all_images'] if img])}")

    # Create WordPress post with hero image
    post = create_wordpress_post(title, blog_post_content, user_id, hero_image_url)
    if not post:
        logger.error(f"Failed to create WordPress post for user {user_id}")
        return None, "Failed to create WordPress post"

    # Normalize WordPress URL
    wordpress_url = user.wordpress_rest_api_url.rstrip('/')
    if wordpress_url.endswith('/wp-json/wp/v2'):
        wordpress_url = wordpress_url[:-len('/wp-json/wp/v2')]
    elif wordpress_url.endswith('/wp-json'):
        wordpress_url = wordpress_url[:-len('/wp-json')]

    # Send email notification
    email_sent = send_email_notification(
        post_id=post['id'],
        title=post['title']['rendered'],
        content=blog_post_content[:500] + '...',  # Truncate for email
        img_url=hero_image_url,
        user_email=user.email,
        wordpress_url=wordpress_url
    )

    if not email_sent:
        logger.warning(f"Failed to send email notification for user {user_id}")
        post['email_notification_sent'] = False
    else:
        post['email_notification_sent'] = True

    return post, None

# Route handlers
@app.route('/')
@login_required
def serve_dashboard():
    """Serve the new modern dashboard (requires authentication)"""
    return send_from_directory('static', 'dashboard.html')

@app.route('/auth')
def serve_auth():
    """Serve the login/register page"""
    return send_from_directory('static', 'auth.html')

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"error": "Email already registered"}), 400

        user = User(
            email=data['email'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            email_verified=False  # Not verified yet
        )
        user.set_password(data['password'])

        # Generate verification code
        verification_code = generate_verification_code()
        user.verification_code = verification_code
        user.verification_code_expiry = get_code_expiry()
        user.verification_attempts = 0

        db.session.add(user)
        db.session.commit()

        # Send verification email
        email_sent = send_verification_email(
            email=user.email,
            verification_code=verification_code,
            first_name=user.first_name
        )

        if not email_sent:
            logger.warning(f"Failed to send verification email to {user.email}")
            return jsonify({
                "message": "User registered but verification email failed to send. Please contact support.",
                "user_id": user.id,
                "requires_verification": True
            }), 201

        return jsonify({
            "message": "User registered successfully. Please check your email for verification code.",
            "user_id": user.id,
            "requires_verification": True
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred during registration"}), 500

@app.route('/api/verify_email', methods=['POST'])
def verify_email():
    """Verify email with 6-digit code"""
    try:
        data = request.json
        user_id = data.get('user_id')
        code = data.get('code')

        if not user_id or not code:
            return jsonify({"error": "User ID and verification code required"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        if user.email_verified:
            return jsonify({"message": "Email already verified"}), 200

        # Increment attempt counter
        user.verification_attempts += 1
        db.session.commit()

        # Verify the code
        success, message = verify_code(user, code)

        if success:
            user.email_verified = True
            user.verification_code = None  # Clear the code
            user.verification_code_expiry = None
            user.verification_attempts = 0
            db.session.commit()
            return jsonify({"message": message, "verified": True}), 200
        else:
            db.session.commit()
            return jsonify({"error": message, "verified": False}), 400

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Email verification error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred during verification"}), 500


@app.route('/api/resend_verification', methods=['POST'])
def resend_verification():
    """Resend verification code"""
    try:
        data = request.json
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({"error": "User ID required"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        if user.email_verified:
            return jsonify({"message": "Email already verified"}), 200

        # Generate new verification code
        verification_code = generate_verification_code()
        user.verification_code = verification_code
        user.verification_code_expiry = get_code_expiry()
        user.verification_attempts = 0  # Reset attempts
        db.session.commit()

        # Send verification email
        email_sent = send_verification_email(
            email=user.email,
            verification_code=verification_code,
            first_name=user.first_name
        )

        if not email_sent:
            return jsonify({"error": "Failed to send verification email. Please try again."}), 500

        return jsonify({"message": "Verification code resent successfully. Please check your email."}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Resend verification error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route('/api/login', methods=['GET', 'POST'])
def login():
    try:
        # Handle GET requests (redirects from @login_required)
        if request.method == 'GET':
            return jsonify({"error": "Not authenticated. Please register or login first."}), 401

        # Handle POST requests (actual login)
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        user = User.query.filter_by(email=data['email']).first()
        if user and user.check_password(data['password']):
            # Check if email is verified
            if not user.email_verified:
                return jsonify({
                    "error": "Email not verified. Please verify your email before logging in.",
                    "requires_verification": True,
                    "user_id": user.id
                }), 403

            login_user(user, remember=True)
            generate_env_file(user)  # Generate user-specific .env file
            return jsonify({"message": "Logged in successfully", "user_id": user.id}), 200
        return jsonify({"error": "Invalid email or password"}), 401
    except Exception as e:
        app.logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred during login"}), 500

@app.route('/api/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/api/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'GET':
        return jsonify({
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "phone": current_user.phone,
            "billing_address": current_user.billing_address,
            "openai_api_key": current_user.openai_api_key,
            "wordpress_rest_api_url": current_user.wordpress_rest_api_url,
            "wordpress_username": current_user.wordpress_username,
            "wordpress_password": current_user.wordpress_password,
            "perplexity_api_token": current_user.perplexity_api_token,
            "specific_topic_queries": current_user.specific_topic_queries or {},
            "system_prompt": current_user.system_prompt,
            "schedule": current_user.schedule or []
        })
    elif request.method == 'POST':
        try:
            data = request.json
            fields_to_update = [
                'first_name', 'last_name', 'phone', 'billing_address',
                'openai_api_key', 'wordpress_rest_api_url', 'wordpress_username',
                'wordpress_password', 'perplexity_api_token', 'specific_topic_queries',
                'system_prompt', 'schedule'
            ]
            for field in fields_to_update:
                if field in data:
                    setattr(current_user, field, data[field])
            db.session.commit()
            generate_env_file(current_user)
            return jsonify({"message": "Profile updated successfully!"})
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Profile update error: {str(e)}")
            return jsonify({"error": "An unexpected error occurred while updating the profile"}), 500

@app.route('/api/update_integrations', methods=['POST'])
@login_required
def update_integrations():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    fields_to_update = [
        'openai_api_key', 'wordpress_rest_api_url', 'wordpress_username',
        'wordpress_password', 'perplexity_api_token'
    ]
    updated_fields = []

    for field in fields_to_update:
        if field in data and data[field]:
            # Validation
            if field == 'openai_api_key' and not is_valid_openai_api_key(data[field]):
                return jsonify({"error": "Invalid OpenAI API key format"}), 400
            if field == 'wordpress_rest_api_url' and not is_valid_wordpress_url(data[field]):
                return jsonify({"error": "Invalid WordPress REST API URL format"}), 400
            if field == 'perplexity_api_token' and not is_valid_perplexity_api_token(data[field]):
                return jsonify({"error": "Invalid Perplexity API token format"}), 400

            setattr(current_user, field, data[field])
            updated_fields.append(field)

    if updated_fields:
        try:
            db.session.commit()
            generate_env_file(current_user)
            return jsonify({"message": f"Updated: {', '.join(updated_fields)}"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify({"message": "No fields were updated"}), 200

@app.route('/api/save_specific_queries', methods=['POST'])
@login_required
def save_specific_queries():
    data = request.json
    current_user.specific_topic_queries = data.get('specific_topic_queries', {})
    db.session.commit()
    return jsonify({"message": "Queries saved successfully!"})

@app.route('/api/get_specific_queries', methods=['GET'])
@login_required
def get_specific_queries():
    return jsonify(current_user.specific_topic_queries or {})

@app.route('/api/save_schedule', methods=['POST'])
@login_required
def save_schedule():
    data = request.json
    if not data or 'schedule' not in data:
        return jsonify({"error": "No schedule provided"}), 400

    current_user.schedule = data['schedule']
    db.session.commit()
    return jsonify({"message": "Schedule saved successfully!"})

@app.route('/api/system_prompt', methods=['POST'])
@login_required
def system_prompt():
    data = request.json
    if not data or 'prompt' not in data:
        return jsonify({"error": "No system prompt provided"}), 400

    current_user.system_prompt = data['prompt']
    db.session.commit()
    return jsonify({"message": "System prompt saved successfully!"})

@app.route('/api/create_test_post', methods=['POST'])
@login_required
def create_test_post():
    try:
        logger.info(f"[V3] Starting AI-powered magazine article creation for user {current_user.id}")
        logger.info(f"[V3] Using GPT-5-mini with reasoning + SeeDream-4 2K images")

        # Use the new V3 creation function with latest AI models
        post, error = create_blog_post_v3(current_user.id)

        if error:
            logger.error(f"Error creating V3 blog post for user {current_user.id}: {error}")
            return jsonify({"error": error}), 500
        if not post:
            logger.error(f"Failed to create V3 test post for user {current_user.id}")
            return jsonify({"error": "Failed to create the test post."}), 500

        logger.info(f"[V3] Successfully created magazine-style post with reasoning for user {current_user.id}")

        response_data = {
            "message": "V3 Magazine-style article created with GPT-5-mini reasoning & SeeDream-4 2K images!",
            "title": post['title']['rendered'],
            "content": post['content']['rendered'],
            "image_url": post.get('_links', {}).get('wp:featuredmedia', [{}])[0].get('href'),
            "version": "3.0",
            "features": "GPT-5-mini reasoning + SeeDream-4 2K photorealistic images"
        }

        if not post.get('email_notification_sent', True):
            response_data["warning"] = "Post created, but email notification failed to send."
            logger.warning(f"Email notification failed to send for user {current_user.id}")

        return jsonify(response_data), 200
    except Exception as e:
        logger.error(f"Unexpected error in V3 create_test_post for user {current_user.id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    # Print all routes for debugging
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")

    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    # Production WSGI server configuration
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)