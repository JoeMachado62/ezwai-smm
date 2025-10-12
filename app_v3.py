"""
EZWAI SMM V3.0 Application - State-of-the-Art AI Content Generation
- GPT-5-mini with Responses API and reasoning (medium effort)
- SeeDream-4 for 2K photorealistic magazine photography
- Enhanced prompt engineering for professional results
"""
# type: ignore - Suppress Pylance warnings for Flask/SQLAlchemy dynamic attributes
from __future__ import annotations
from typing import Optional, Any
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
from openai_integration_v4 import create_blog_post_with_images_v4  # V4 modular pipeline
from wordpress_integration import create_wordpress_post
from email_notification import send_email_notification
from email_verification import generate_verification_code, get_code_expiry, send_verification_email, verify_code
from purchase_receipt_email import send_purchase_receipt_email
import traceback
import stripe
from credit_system import (
    check_sufficient_credits,
    deduct_credits,
    refund_credits,
    add_credits_manual,
    add_welcome_credit,
    get_transaction_history,
    ARTICLE_COST,
    WELCOME_CREDIT,
    MIN_PURCHASE
)

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

# Stripe configuration
stripe_key = os.getenv('STRIPE_SECRET_KEY')
if stripe_key and not stripe_key.startswith('YOUR_'):
    stripe.api_key = stripe_key
    logger.info(f"Stripe API key configured: True")
else:
    logger.warning("Stripe API key not configured - payment features disabled")
    stripe.api_key = None

db = SQLAlchemy(app)  # type: ignore[var-annotated]
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'serve_auth'  # type: ignore[assignment] - Redirect to /auth page instead of API endpoint

class User(UserMixin, db.Model):  # type: ignore[misc,name-defined]
    # SQLAlchemy columns - type checker warnings suppressed
    id = db.Column(db.Integer, primary_key=True)  # type: ignore[var-annotated]
    email = db.Column(db.String(120), unique=True, nullable=False)  # type: ignore[var-annotated]
    password_hash = db.Column(db.String(128))  # type: ignore[var-annotated]
    first_name = db.Column(db.String(80))  # type: ignore[var-annotated]
    last_name = db.Column(db.String(80))  # type: ignore[var-annotated]
    phone = db.Column(db.String(20))  # type: ignore[var-annotated]
    billing_address = db.Column(db.String(200))  # type: ignore[var-annotated]
    openai_api_key = db.Column(db.String(255))  # type: ignore[var-annotated]
    wordpress_rest_api_url = db.Column(db.String(255))  # type: ignore[var-annotated]
    wordpress_app_password = db.Column(db.String(255))  # type: ignore[var-annotated]  # WordPress Application Password
    perplexity_api_token = db.Column(db.String(255))  # type: ignore[var-annotated]
    queries = db.Column(db.JSON)  # type: ignore[var-annotated]
    system_prompt = db.Column(db.Text)  # type: ignore[var-annotated]
    schedule = db.Column(db.JSON)  # type: ignore[var-annotated]
    specific_topic_queries = db.Column(db.JSON)  # type: ignore[var-annotated]
    writing_styles = db.Column(db.JSON)  # type: ignore[var-annotated]
    last_query_index = db.Column(db.Integer, default=0)  # type: ignore[var-annotated]

    # Brand customization
    brand_primary_color = db.Column(db.String(7), default='#6B5DD3')  # type: ignore[var-annotated]  # Purple
    brand_accent_color = db.Column(db.String(7), default='#FF6B4A')  # type: ignore[var-annotated]  # Coral
    use_default_branding = db.Column(db.Boolean, default=True)  # type: ignore[var-annotated]

    # 2FA email verification fields
    email_verified = db.Column(db.Boolean, default=False)  # type: ignore[var-annotated]
    verification_code = db.Column(db.String(6))  # type: ignore[var-annotated]
    verification_code_expiry = db.Column(db.DateTime)  # type: ignore[var-annotated]
    verification_attempts = db.Column(db.Integer, default=0)  # type: ignore[var-annotated]

    # Credit system fields
    credit_balance = db.Column(db.Integer, default=3)  # type: ignore[var-annotated] - Welcome credit (3 free articles)
    auto_recharge_enabled = db.Column(db.Boolean, default=False)  # type: ignore[var-annotated]
    auto_recharge_amount = db.Column(db.Float, default=25.00)  # type: ignore[var-annotated] - Dollar amount for auto-recharge
    auto_recharge_threshold = db.Column(db.Integer, default=5)  # type: ignore[var-annotated] - Credits remaining to trigger
    stripe_customer_id = db.Column(db.String(255), unique=True)  # type: ignore[var-annotated]
    stripe_payment_method_id = db.Column(db.String(255))  # type: ignore[var-annotated]
    is_admin = db.Column(db.Boolean, default=False)  # type: ignore[var-annotated]
    total_articles_generated = db.Column(db.Integer, default=0)  # type: ignore[var-annotated]
    total_spent = db.Column(db.Float, default=0.00)  # type: ignore[var-annotated]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # type: ignore[var-annotated]

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class CompletedJob(db.Model):  # type: ignore[misc,name-defined]
    id = db.Column(db.Integer, primary_key=True)  # type: ignore[var-annotated]
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # type: ignore[var-annotated]
    scheduled_time = db.Column(db.DateTime(timezone=True), nullable=False)  # type: ignore[var-annotated]
    completed_time = db.Column(db.DateTime(timezone=True), nullable=True)  # type: ignore[var-annotated]
    post_title = db.Column(db.String(255), nullable=False)  # type: ignore[var-annotated]

    __table_args__ = (db.UniqueConstraint('user_id', 'scheduled_time', name='_user_scheduled_time_uc'),)  # type: ignore[assignment]

class CreditTransaction(db.Model):  # type: ignore[misc,name-defined]
    """Transaction history for credit purchases and usage"""
    __tablename__ = 'credit_transactions'
    id = db.Column(db.Integer, primary_key=True)  # type: ignore[var-annotated]
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # type: ignore[var-annotated]
    amount = db.Column(db.Float, nullable=False)  # type: ignore[var-annotated] - Positive for purchase, negative for usage
    transaction_type = db.Column(db.String(50), nullable=False)  # type: ignore[var-annotated] - 'welcome', 'purchase', 'auto_recharge', 'article_generation', 'refund'
    stripe_payment_intent_id = db.Column(db.String(255))  # type: ignore[var-annotated]
    balance_after = db.Column(db.Float, nullable=False)  # type: ignore[var-annotated]
    description = db.Column(db.String(500))  # type: ignore[var-annotated]
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # type: ignore[var-annotated]

class Article(db.Model):  # type: ignore[misc,name-defined]
    """Generated articles with metadata"""
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)  # type: ignore[var-annotated]
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # type: ignore[var-annotated]
    title = db.Column(db.String(500), nullable=False)  # type: ignore[var-annotated]
    content_html = db.Column(db.Text, nullable=False)  # type: ignore[var-annotated]
    hero_image_url = db.Column(db.String(1000))  # type: ignore[var-annotated]
    section_images = db.Column(db.JSON)  # type: ignore[var-annotated] - List of section image URLs
    word_count = db.Column(db.Integer)  # type: ignore[var-annotated]
    status = db.Column(db.String(50), default='draft')  # type: ignore[var-annotated] - 'draft', 'published', 'scheduled', 'failed', 'local'
    generation_mode = db.Column(db.String(50), default='wordpress')  # type: ignore[var-annotated] - 'wordpress', 'local'
    wordpress_post_id = db.Column(db.Integer)  # type: ignore[var-annotated]
    wordpress_url = db.Column(db.String(1000))  # type: ignore[var-annotated]
    metadata = db.Column(db.JSON)  # type: ignore[var-annotated] - Additional metadata (topic, style, etc.)
    backup_file_path = db.Column(db.String(500))  # type: ignore[var-annotated]
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # type: ignore[var-annotated]
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)  # type: ignore[var-annotated]

class Image(db.Model):  # type: ignore[misc,name-defined]
    """Generated images with prompts"""
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)  # type: ignore[var-annotated]
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # type: ignore[var-annotated]
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=True)  # type: ignore[var-annotated]
    image_url = db.Column(db.String(1000), nullable=False)  # type: ignore[var-annotated]
    image_type = db.Column(db.String(50), default='section')  # type: ignore[var-annotated] - 'hero', 'section'
    prompt = db.Column(db.Text, nullable=False)  # type: ignore[var-annotated]
    model = db.Column(db.String(100), default='seedream-4')  # type: ignore[var-annotated]
    aspect_ratio = db.Column(db.String(20))  # type: ignore[var-annotated]
    replicate_prediction_id = db.Column(db.String(100))  # type: ignore[var-annotated]
    file_size_kb = db.Column(db.Integer)  # type: ignore[var-annotated]
    cost_usd = db.Column(db.Float, default=0.0750)  # type: ignore[var-annotated]
    tags = db.Column(db.JSON)  # type: ignore[var-annotated] - Optional tags for categorization
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # type: ignore[var-annotated]

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
    return User.query.get(int(user_id))  # type: ignore[attr-defined]

def generate_env_file(user):
    """
    Generate per-user environment file - ONLY WordPress credentials.

    OpenAI, Perplexity, and Replicate API keys are centralized in main .env file.
    This prevents user env files from overriding the admin's centralized keys.
    """
    from wordpress_integration import normalize_wordpress_url

    # Normalize WordPress URL
    wordpress_url = ''
    if user.wordpress_rest_api_url:
        wordpress_url = normalize_wordpress_url(user.wordpress_rest_api_url)

    # Use email username as WordPress username
    wordpress_username = user.email.split('@')[0] if user.email else ''

    env_content = f"""# WordPress credentials (per-user) - Application Password Method
WORDPRESS_REST_API_URL="{wordpress_url}"
WORDPRESS_APP_PASSWORD="{user.wordpress_app_password or ''}"
WORDPRESS_USERNAME="{wordpress_username}"

# NOTE: OpenAI, Perplexity, and Replicate keys are centralized in main .env
# Do NOT add them here - they will override the system keys!
"""
    with open(f'.env.user_{user.id}', 'w') as f:
        f.write(env_content)

def is_valid_openai_api_key(api_key):
    """Validate OpenAI API key format"""
    return bool(re.match(r'^sk-[A-Za-z0-9_-]{32,}$', api_key))

def is_valid_wordpress_url(url):
    """Validate WordPress URL format"""
    return url.endswith('/') or url.endswith('/wp-json') or url.endswith('/wp-json/wp/v2')

def _save_emergency_article(content: str, title: str, user_id: int) -> None:
    """Emergency save article to disk when validation fails"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"emergency_article_{user_id}_{timestamp}.html"

        emergency_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>
    <div style="background: #ffe6e6; padding: 20px; margin: 20px; border-left: 4px solid #d00;">
        <h2>⚠️ EMERGENCY SAVE - VALIDATION FAILED</h2>
        <p><strong>Title:</strong> {title}</p>
        <p><strong>User ID:</strong> {user_id}</p>
        <p><strong>Time:</strong> {timestamp}</p>
        <p>This article failed validation but content has been preserved.</p>
    </div>
    <hr>
    {content}
</body>
</html>"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(emergency_html)

        logger.error(f"[EMERGENCY] Article saved to {filename}")
    except Exception as e:
        logger.error(f"[EMERGENCY] Failed to save article: {e}")

def is_valid_perplexity_api_token(token):
    """Validate Perplexity API token format"""
    return bool(re.match(r'^pplx-[A-Za-z0-9]{32,}$', token))

def has_wordpress_configured(user):
    """
    Check if user has WordPress credentials configured.

    Returns:
        bool: True if WordPress is configured, False otherwise
    """
    return bool(
        user.wordpress_rest_api_url and
        user.wordpress_rest_api_url.strip() and
        user.wordpress_app_password and
        user.wordpress_app_password.strip() and
        user.wordpress_username and
        user.wordpress_username.strip()
    )

def create_blog_post_v3(user_id, manual_topic=None, manual_system_prompt=None, manual_writing_style=None, local_mode=False, is_scheduled=False):
    """
    V3.0 / V4.0: State-of-the-art blog post creation with:
    - GPT-5 / GPT-5-mini with reasoning (medium effort)
    - SeeDream-4 2K photorealistic images
    - Enhanced photographic prompt engineering
    - Writing style support
    - Optional local mode (downloadable HTML without WordPress)

    Args:
        user_id: User ID for post creation
        manual_topic: Optional manual topic (bypasses saved topics rotation)
        manual_system_prompt: Optional manual system prompt (overrides saved prompt)
        manual_writing_style: Optional writing style for article generation
        local_mode: If True, creates downloadable HTML with base64 images (no WordPress)
        is_scheduled: If True, this is a scheduled post (not manual) - affects error handling
    """
    user = User.query.get(user_id)  # type: ignore[attr-defined]
    if not user:
        logger.error(f"User {user_id} not found")
        return None, "User not found"

    # Use manual topic if provided, otherwise rotate through saved topics
    if manual_topic:
        logger.info(f"[V3] Using manual topic (bypassing saved topics): {manual_topic[:100]}...")
        blog_post_idea = manual_topic
        writing_style = manual_writing_style  # Use writing style from UI
    else:
        query, writing_style = query_management(user_id)
        if not query:
            logger.error(f"No valid query found for user {user_id}")
            return None, "No valid query found for user"

        logger.info(f"[V3] Using saved topic query for user {user_id}: {query}")
        logger.info(f"[V3] Writing style: {writing_style or 'Default'}")

        blog_post_ideas = generate_blog_post_ideas(query, user_id, writing_style)
        if not blog_post_ideas:
            logger.error(f"No blog post ideas generated for user {user_id}")
            return None, "No blog post ideas generated"

        blog_post_idea = blog_post_ideas[0]

    # Use manual system prompt if provided, otherwise use saved prompt
    if manual_system_prompt:
        system_prompt = manual_system_prompt
        logger.info(f"[V3] Using manual system prompt")
    else:
        system_prompt = user.system_prompt or "Write a comprehensive, engaging article in a professional but conversational tone suitable for a business magazine."
        logger.info(f"[V3] Using saved system prompt")

    # Determine mode
    mode_label = "LOCAL MODE (downloadable)" if local_mode else "WORDPRESS MODE"
    logger.info(f"[V4] Creating magazine-style blog post with V4 modular pipeline...")
    logger.info(f"[V4] Mode: {mode_label}")
    logger.info(f"Perplexity research: {blog_post_idea[:100]}...")

    # Use V4 modular pipeline with writing style and local_mode flag
    processed_post, error = create_blog_post_with_images_v4(
        perplexity_research=blog_post_idea,
        user_id=user_id,
        user_system_prompt=system_prompt,
        writing_style=writing_style,  # Pass writing style through to V4
        local_mode=local_mode  # Enable local mode if WordPress not configured or user chose it
    )
    if error:
        logger.error(f"Error in V4 pipeline for user {user_id}: {error}")
        return None, error

    if not processed_post:
        logger.error(f"No processed post returned for user {user_id}")
        return None, "Post processing failed"

    title = processed_post['title']  # type: ignore[index]
    blog_post_content = processed_post['content']  # type: ignore[index]
    hero_image_url = processed_post['hero_image_url']  # type: ignore[index]

    logger.info(f"[V3] Article created with reasoning. Images: {len([img for img in processed_post['all_images'] if img])}")  # type: ignore[index]

    # FINAL VALIDATION: Check article completeness before posting
    logger.info("[V3] Performing final validation before WordPress posting...")

    # Check 1: Inline styling present (V4 uses inline styles, not <style> tags)
    if 'style="' not in blog_post_content:
        logger.error("CRITICAL: Inline styling missing from article content")
        # EMERGENCY: Save article before rejecting
        _save_emergency_article(blog_post_content, title, current_user.id)  # type: ignore[attr-defined]
        return None, "Article missing magazine styling"

    # Check 2: Hero section present (now uses inline styles with background-image)
    if 'background-image' not in blog_post_content or hero_image_url not in blog_post_content:
        logger.error("CRITICAL: Hero section missing from article content")
        # EMERGENCY: Save article before rejecting
        _save_emergency_article(blog_post_content, title, current_user.id)  # type: ignore[attr-defined]
        return None, "Article missing hero section"

    # Check 3: Images embedded in content
    all_images_present = all(
        img_url in blog_post_content
        for img_url in processed_post['all_images']
        if img_url
    )
    if not all_images_present:
        logger.error("CRITICAL: Not all images are embedded in article content")
        missing_images = [img for img in processed_post['all_images'] if img and img not in blog_post_content]
        logger.error(f"Missing images: {missing_images}")
        return None, "Not all images embedded in article"

    # Check 4: Minimum content length (magazine articles should be substantial)
    if len(blog_post_content) < 5000:
        logger.warning(f"Article content seems short: {len(blog_post_content)} characters")

    logger.info("✓✓✓ FINAL VALIDATION PASSED: Article is complete with styling and all images")
    logger.info(f"  - Magazine styling: ✓")
    logger.info(f"  - Hero section: ✓")
    logger.info(f"  - All 4 images embedded: ✓")
    logger.info(f"  - Content length: {len(blog_post_content)} characters")

    # Normalize WordPress URL for emails
    wordpress_url = user.wordpress_rest_api_url.rstrip('/') if user.wordpress_rest_api_url else None
    if wordpress_url:
        if wordpress_url.endswith('/wp-json/wp/v2'):
            wordpress_url = wordpress_url[:-len('/wp-json/wp/v2')]
        elif wordpress_url.endswith('/wp-json'):
            wordpress_url = wordpress_url[:-len('/wp-json')]

    # LOCAL MODE: Skip WordPress upload, send email with downloadable article
    if local_mode:
        logger.info("✓✓✓ LOCAL MODE: Skipping WordPress upload")
        logger.info("✓✓✓ Sending email with downloadable article attachment")

        from email_notification import send_article_notification_with_attachment
        email_sent = send_article_notification_with_attachment(
            title=title,
            article_html=blog_post_content,
            hero_image_url=hero_image_url,
            user_email=user.email,
            mode="local",  # Use local mode email template
            wordpress_url=None,
            post_id=None
        )

        if email_sent:
            logger.info(f"✓ Local mode article emailed to {user.email}")
            return {
                'title': title,
                'content': blog_post_content,
                'hero_image_url': hero_image_url,
                'mode': 'local',
                'email_sent': True,
                'message': 'Article created successfully. Download link sent to your email.'
            }, None
        else:
            logger.warning(f"Failed to send local mode email to {user.email}")
            return {
                'title': title,
                'content': blog_post_content,
                'hero_image_url': hero_image_url,
                'mode': 'local',
                'email_sent': False,
                'message': 'Article created but email delivery failed. Please contact support.'
            }, None

    # WORDPRESS MODE: Try WordPress post creation with comprehensive error handling
    try:
        post = create_wordpress_post(title, blog_post_content, user_id, hero_image_url)

        if not post:
            # WordPress upload failed - send failure email with article attachment
            post_type = "scheduled post" if is_scheduled else "manual post"
            logger.error(f"WordPress post creation returned None for user {user_id} ({post_type})")

            error_details = {
                "error_message": f"WordPress post creation failed ({post_type}) - check credentials and site accessibility",
                "failure_point": "article_creation",
                "technical_details": f"create_wordpress_post() returned None for {post_type}. Common causes:\n"
                                   "- WordPress Application Password missing or incorrect\n"
                                   "- WordPress REST API not accessible\n"
                                   "- WordPress site URL incorrect\n"
                                   "- WordPress permissions issue\n"
                                   f"- Post type: {post_type}",
                "resolution_steps": [
                    "Log into your WordPress dashboard manually to confirm credentials work",
                    "Go to Users → Profile → Application Passwords in WordPress",
                    "Generate a new Application Password if needed",
                    "Update the Application Password in your dashboard settings",
                    "Verify your WordPress REST API URL is correct (e.g., https://yoursite.com/wp-json/wp/v2)",
                    "Check that WordPress REST API is enabled (try visiting https://yoursite.com/wp-json/)",
                    "Manual upload: Open attached HTML, copy content, paste into new WordPress post"
                ] + (["NOTE: This was a scheduled post. Fix credentials to prevent future failures."] if is_scheduled else [])
            }

            from email_notification import send_wordpress_failure_notification
            email_sent = send_wordpress_failure_notification(
                title=title,
                article_html=blog_post_content,
                user_email=user.email,
                error_details=error_details,
                wordpress_url=wordpress_url
            )

            if email_sent:
                logger.info(f"✓ Failure notification with article attachment sent to {user.email}")
                # Still return error, but user has the article
                return None, "WordPress upload failed - article emailed to you for manual upload"
            else:
                logger.error(f"Failed to send failure notification email")
                return None, "WordPress upload failed and email notification failed - contact support"

        # WordPress upload succeeded - send success email
        logger.info(f"✓ WordPress post created successfully: ID {post.get('id')}")

        from email_notification import send_article_notification_with_attachment
        email_sent = send_article_notification_with_attachment(
            title=post['title']['rendered'],
            article_html=blog_post_content,
            hero_image_url=hero_image_url,
            user_email=user.email,
            mode="wordpress",
            wordpress_url=wordpress_url,
            post_id=post['id']
        )

        if not email_sent:
            logger.warning(f"Failed to send success email notification for user {user_id}")
            post['email_notification_sent'] = False
        else:
            logger.info(f"✓ Success notification sent to {user.email}")
            post['email_notification_sent'] = True

        return post, None

    except Exception as e:
        # Catch any WordPress upload exceptions
        logger.error(f"WordPress upload exception for user {user_id}: {str(e)}")
        logger.error(traceback.format_exc())

        # Determine failure point from error message
        error_str = str(e).lower()
        if "password" in error_str or "authentication" in error_str or "401" in error_str:
            failure_point = "authentication"
            error_message = "WordPress authentication failed - check Application Password"
            resolution_steps = [
                "Log into WordPress dashboard to verify credentials",
                "Go to Users → Profile → Application Passwords",
                "Generate a new Application Password",
                "Update in dashboard settings",
                "Manual upload: Use attached HTML file"
            ]
        elif "image" in error_str or "media" in error_str or "upload" in error_str:
            failure_point = "image_upload"
            error_message = "Failed to upload images to WordPress media library"
            resolution_steps = [
                "Check WordPress media upload permissions",
                "Verify WordPress media library is accessible",
                "Check WordPress file upload size limits",
                "Manual upload: Use attached HTML (images embedded)"
            ]
        elif "rest" in error_str or "api" in error_str or "404" in error_str:
            failure_point = "rest_api"
            error_message = "WordPress REST API not accessible"
            resolution_steps = [
                "Verify WordPress REST API is enabled",
                "Visit https://yoursite.com/wp-json/ to test",
                "Check WordPress URL is correct in dashboard",
                "Manual upload: Use attached HTML file"
            ]
        else:
            failure_point = "wordpress_upload"
            error_message = f"WordPress upload error: {str(e)[:200]}"
            resolution_steps = [
                "Check all WordPress credentials in dashboard",
                "Verify WordPress site is accessible",
                "Check WordPress error logs",
                "Manual upload: Use attached HTML file"
            ]

        error_details = {
            "error_message": error_message,
            "failure_point": failure_point,
            "technical_details": f"Exception: {type(e).__name__}\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}",
            "resolution_steps": resolution_steps
        }

        from email_notification import send_wordpress_failure_notification
        email_sent = send_wordpress_failure_notification(
            title=title,
            article_html=blog_post_content,
            user_email=user.email,
            error_details=error_details,
            wordpress_url=wordpress_url
        )

        if email_sent:
            logger.info(f"✓ Failure notification with article sent to {user.email}")
            return None, f"{error_message} - article emailed to you for manual upload"
        else:
            logger.error(f"Failed to send failure notification")
            return None, f"{error_message} - email notification also failed - contact support"

# Route handlers
@app.route('/')
def serve_landing():
    """Serve the landing page"""
    return send_from_directory('static', 'landing.html')

@app.route('/dashboard')
@login_required
def serve_dashboard():
    """Serve the dashboard (requires authentication)"""
    return send_from_directory('static', 'dashboard.html')

@app.route('/auth')
def serve_auth():
    """Serve the login/register page"""
    return send_from_directory('static', 'auth.html')

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        if User.query.filter_by(email=data['email']).first():  # type: ignore[index]
            return jsonify({"error": "Email already registered"}), 400

        # Create Stripe customer first (if Stripe is configured)
        stripe_customer = None
        if stripe.api_key:
            try:
                stripe_customer = stripe.Customer.create(
                    email=data['email'],  # type: ignore[index]
                    name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                    metadata={'source': 'ezwai_registration'}
                )
                logger.info(f"Created Stripe customer: {stripe_customer.id}")
            except Exception as e:
                logger.error(f"Stripe customer creation failed: {e}")
                return jsonify({"error": "Payment system error. Please try again later."}), 500
        else:
            logger.warning("Stripe not configured - skipping customer creation")

        user = User(  # type: ignore[call-arg]
            email=data['email'],  # type: ignore[index]
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            email_verified=False,  # Not verified yet
            stripe_customer_id=stripe_customer.id if stripe_customer else None,
            credit_balance=WELCOME_CREDIT  # Add welcome credit
        )
        user.set_password(data['password'])

        # Generate verification code
        verification_code = generate_verification_code()
        user.verification_code = verification_code
        user.verification_code_expiry = get_code_expiry()
        user.verification_attempts = 0

        db.session.add(user)
        db.session.commit()

        # Log welcome credit transaction
        add_welcome_credit(user.id, db)

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

            # Auto-login the user after successful email verification
            login_user(user, remember=True)
            app.logger.info(f"User {user.id} auto-logged in after email verification")

            return jsonify({"message": message, "verified": True, "auto_login": True}), 200
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

            # Generate 2FA code for login
            from email_verification import generate_verification_code, get_code_expiry, send_verification_email

            verification_code = generate_verification_code()
            user.verification_code = verification_code
            user.verification_code_expiry = get_code_expiry()
            user.verification_attempts = 0
            db.session.commit()

            # Send 2FA code via email
            send_verification_email(user.email, verification_code, user.first_name)

            return jsonify({
                "message": "Verification code sent to your email",
                "requires_2fa": True,
                "user_id": user.id
            }), 200
        return jsonify({"error": "Invalid email or password"}), 401
    except Exception as e:
        app.logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred during login"}), 500

@app.route('/api/verify_login', methods=['POST'])
def verify_login():
    """Verify 2FA code during login"""
    try:
        data = request.json
        if not data or 'user_id' not in data or 'code' not in data:
            return jsonify({"error": "Missing required fields"}), 400

        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({"error": "User not found"}), 404

        from email_verification import verify_code

        # Increment attempts
        user.verification_attempts += 1
        db.session.commit()

        # Verify the code
        success, message = verify_code(user, data['code'])

        if success:
            # Code is valid - log user in
            login_user(user, remember=True)
            generate_env_file(user)  # Generate user-specific .env file

            # Clear verification code
            user.verification_code = None
            user.verification_code_expiry = None
            user.verification_attempts = 0
            db.session.commit()

            return jsonify({
                "message": "Login successful",
                "verified": True,
                "user_id": user.id
            }), 200
        else:
            return jsonify({
                "error": message,
                "verified": False
            }), 401

    except Exception as e:
        app.logger.error(f"Login verification error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/logout', methods=['POST', 'GET'])
@login_required
def logout():
    logout_user()
    session.clear()  # Clear all session data
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/api/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile (name, password)"""
    try:
        data = request.json
        user = User.query.get(current_user.id)

        # Update name fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']

        # Update password if provided
        if data.get('new_password'):
            if not data.get('current_password'):
                return jsonify({"error": "Current password required"}), 400

            if not user.check_password(data['current_password']):
                return jsonify({"error": "Current password is incorrect"}), 401

            user.set_password(data['new_password'])

        db.session.commit()
        return jsonify({"message": "Profile updated successfully"}), 200

    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/profile', methods=['GET', 'POST'])  # type: ignore[misc]
@login_required
def profile():  # type: ignore[return]
    if request.method == 'GET':
        return jsonify({
            "id": current_user.id,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "phone": current_user.phone,
            "billing_address": current_user.billing_address,
            "credit_balance": current_user.credit_balance,
            "openai_api_key": current_user.openai_api_key,
            "wordpress_rest_api_url": current_user.wordpress_rest_api_url,
            "wordpress_app_password": current_user.wordpress_app_password,
            "perplexity_api_token": current_user.perplexity_api_token,
            "specific_topic_queries": current_user.specific_topic_queries or {},
            "system_prompt": current_user.system_prompt,
            "schedule": current_user.schedule or [],
            "brand_primary_color": current_user.brand_primary_color,
            "brand_accent_color": current_user.brand_accent_color,
            "use_default_branding": current_user.use_default_branding
        })
    elif request.method == 'POST':
        try:
            data = request.json
            if not data:
                return jsonify({"error": "No data provided"}), 400

            fields_to_update = [
                'first_name', 'last_name', 'phone', 'billing_address',
                'openai_api_key', 'wordpress_rest_api_url', 'wordpress_app_password',
                'perplexity_api_token', 'specific_topic_queries',
                'system_prompt', 'schedule'
            ]
            for field in fields_to_update:
                if field in data:  # type: ignore[operator]
                    setattr(current_user, field, data[field])  # type: ignore[index]
            db.session.commit()  # type: ignore[attr-defined]
            generate_env_file(current_user)
            return jsonify({"message": "Profile updated successfully!"})
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Profile update error: {str(e)}")
            return jsonify({"error": "An unexpected error occurred while updating the profile"}), 500

@app.route('/api/test_wordpress', methods=['POST'])
@login_required
def test_wordpress():
    """Test WordPress connection with Application Password"""
    try:
        data = request.get_json()
        wordpress_url = data.get('wordpress_url', '').strip()
        app_password = data.get('app_password', '').strip()

        if not wordpress_url or not app_password:
            return jsonify({"error": "WordPress URL and Application Password are required"}), 400

        # Temporarily set credentials for testing (don't save yet)
        from wordpress_integration import normalize_wordpress_url, construct_api_endpoint, create_auth_header
        import requests as req

        base_url = normalize_wordpress_url(wordpress_url)
        endpoint = construct_api_endpoint(base_url)

        # Use email username as WordPress username
        username = current_user.email.split('@')[0]
        headers = create_auth_header(username, app_password)

        # Test connection
        response = req.get(endpoint, headers=headers, timeout=10)

        if response.status_code == 200:
            return jsonify({"message": "Connection successful! Your WordPress site is ready."}), 200
        elif response.status_code == 401:
            return jsonify({"error": "Authentication failed. Please check your Application Password."}), 401
        else:
            return jsonify({"error": f"Connection failed with status code: {response.status_code}"}), 400

    except req.exceptions.Timeout:
        return jsonify({"error": "Connection timeout. Please check your WordPress URL."}), 408
    except req.exceptions.RequestException as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 500
    except Exception as e:
        app.logger.error(f"Error testing WordPress connection: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/update_integrations', methods=['POST'])
@login_required
def update_integrations():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    fields_to_update = [
        'openai_api_key', 'wordpress_rest_api_url', 'wordpress_app_password',
        'perplexity_api_token'
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

@app.route('/api/update_brand_colors', methods=['POST'])
@login_required
def update_brand_colors():
    """Update user's brand customization settings"""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        # Update use_default_branding flag
        if 'use_default_branding' in data:
            current_user.use_default_branding = bool(data['use_default_branding'])

        # Update brand colors (validate hex format)
        if 'brand_primary_color' in data:
            color = data['brand_primary_color']
            if not color.startswith('#') or len(color) != 7:
                return jsonify({"error": "Invalid primary color format. Use #RRGGBB"}), 400
            current_user.brand_primary_color = color

        if 'brand_accent_color' in data:
            color = data['brand_accent_color']
            if not color.startswith('#') or len(color) != 7:
                return jsonify({"error": "Invalid accent color format. Use #RRGGBB"}), 400
            current_user.brand_accent_color = color

        db.session.commit()
        return jsonify({"message": "Brand colors updated successfully!"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@app.route('/api/save_specific_queries', methods=['POST'])
@login_required
def save_specific_queries():
    data = request.json
    current_user.specific_topic_queries = data.get('specific_topic_queries', {})
    current_user.writing_styles = data.get('writing_styles', {})
    db.session.commit()
    return jsonify({"message": "Queries and writing styles saved successfully!"})

@app.route('/api/get_specific_queries', methods=['GET'])
@login_required
def get_specific_queries():
    return jsonify({
        "queries": current_user.specific_topic_queries or {},
        "styles": current_user.writing_styles or {}
    })

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

        # Get request parameters first
        data = request.json or {}
        manual_topic = data.get('blog_post_idea', '').strip()
        manual_system_prompt = data.get('system_prompt', '').strip()
        manual_writing_style = data.get('writing_style', '').strip()
        user_chose_local_mode = data.get('local_mode', False)  # NEW: User can explicitly choose local mode

        # PRE-FLIGHT CHECK: Determine if we should use local mode
        wordpress_configured = has_wordpress_configured(current_user)

        if user_chose_local_mode:
            # User explicitly chose local mode
            local_mode = True
            logger.info(f"[V3] User explicitly chose LOCAL MODE (downloadable article)")
        elif not wordpress_configured:
            # WordPress not configured - automatically use local mode
            local_mode = True
            logger.info(f"[V3] WordPress not configured - automatically using LOCAL MODE")
        else:
            # WordPress configured and user didn't choose local mode - use WordPress
            local_mode = False
            logger.info(f"[V3] WordPress configured - using WORDPRESS MODE")

        # CHECK CREDITS FIRST
        has_credits, credit_message = check_sufficient_credits(current_user)
        if not has_credits:
            logger.warning(f"[Credits] User {current_user.id} has insufficient credits: {credit_message}")
            return jsonify({
                "error": credit_message,
                "balance": current_user.credit_balance,
                "required": ARTICLE_COST,
                "action_required": "purchase_credits"
            }), 402  # Payment Required status code

        # DEDUCT CREDITS BEFORE GENERATION
        if not deduct_credits(current_user, db):
            logger.error(f"[Credits] Failed to deduct credits for user {current_user.id}")
            return jsonify({"error": "Credit processing error. Please try again."}), 500

        logger.info(f"[V3] Credits deducted. Proceeding with article generation")
        logger.info(f"[V3] Using GPT-5-mini with reasoning + SeeDream-4 2K images")

        # Use manual inputs if provided, otherwise use saved topics
        if manual_topic:
            logger.info(f"[V3] Using manual topic from user: {manual_topic[:100]}...")
            logger.info(f"[V3] Writing style from UI: {manual_writing_style or 'Default'}")

            # Call Perplexity with manual topic + writing style
            logger.info(f"[V3] Getting Perplexity research for manual topic...")
            perplexity_research_list = generate_blog_post_ideas(
                query=manual_topic,
                user_id=current_user.id,
                writing_style=manual_writing_style or None
            )

            if not perplexity_research_list:
                return jsonify({"error": "Failed to get Perplexity research"}), 500

            perplexity_research = perplexity_research_list[0]
            logger.info(f"[V3] Perplexity research received: {len(perplexity_research)} chars")

            # Now create post with Perplexity research
            post, error = create_blog_post_v3(
                current_user.id,
                manual_topic=perplexity_research,  # Pass Perplexity research, not raw topic
                manual_system_prompt=manual_system_prompt or None,
                manual_writing_style=manual_writing_style or None,
                local_mode=local_mode,  # Pass local_mode flag
                is_scheduled=False  # This is a manual post
            )
        else:
            logger.info(f"[V3] Using saved topics rotation")
            post, error = create_blog_post_v3(
                current_user.id,
                local_mode=local_mode,  # Pass local_mode flag
                is_scheduled=False  # This is a manual post
            )

        if error:
            logger.error(f"Error creating V3 blog post for user {current_user.id}: {error}")
            # REFUND credits on failure
            refund_credits(current_user, db, reason=f"Article generation failed: {error}")
            return jsonify({"error": error}), 500
        if not post:
            logger.error(f"Failed to create V3 test post for user {current_user.id}")
            # REFUND credits on failure
            refund_credits(current_user, db, reason="Article generation failed: No post created")
            return jsonify({"error": "Failed to create the test post."}), 500

        logger.info(f"[V3] Successfully created magazine-style post for user {current_user.id}")

        # Handle response based on mode
        if local_mode:
            # Local mode response
            logger.info(f"[V3] LOCAL MODE article created for user {current_user.id}")
            response_data = {
                "message": post.get('message', "Downloadable article created! Check your email for the HTML file."),
                "title": post.get('title', 'Article'),
                "mode": "local",
                "email_sent": post.get('email_sent', False),
                "version": "3.0",
                "features": "GPT-5-mini reasoning + SeeDream-4 2K images + Local downloadable format"
            }

            if not post.get('email_sent'):
                response_data["warning"] = "Article created, but email delivery failed. Please contact support."

            return jsonify(response_data), 200
        else:
            # WordPress mode response
            logger.info(f"[V3] WORDPRESS article created for user {current_user.id}")
            response_data = {
                "message": "Magazine-style article created and published to WordPress!",
                "title": post['title']['rendered'],
                "content": post['content']['rendered'],
                "image_url": post.get('_links', {}).get('wp:featuredmedia', [{}])[0].get('href'),
                "mode": "wordpress",
                "version": "3.0",
                "features": "GPT-5-mini reasoning + SeeDream-4 2K images"
            }

            if not post.get('email_notification_sent', True):
                response_data["warning"] = "Post created, but email notification failed to send."
                logger.warning(f"Email notification failed to send for user {current_user.id}")

            return jsonify(response_data), 200
    except Exception as e:
        logger.error(f"Unexpected error in V3 create_test_post for user {current_user.id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # REFUND credits on unexpected error
        refund_credits(current_user, db, reason=f"Unexpected error: {str(e)[:100]}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/api/publish_post/<int:post_id>', methods=['POST'])
@login_required
def publish_post(post_id):
    """Publish a WordPress draft post (change status from draft to publish)"""
    try:
        from wordpress_integration import publish_wordpress_post

        logger.info(f"User {current_user.id} requesting to publish post {post_id}")

        result = publish_wordpress_post(post_id, current_user.id)

        if result:
            logger.info(f"Successfully published post {post_id} for user {current_user.id}")
            return jsonify({
                "message": "Post published successfully!",
                "post_id": post_id,
                "status": "publish"
            }), 200
        else:
            logger.error(f"Failed to publish post {post_id} for user {current_user.id}")
            return jsonify({"error": "Failed to publish post"}), 500

    except Exception as e:
        logger.error(f"Error publishing post {post_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

# ============================================================================
# CREDIT SYSTEM & STRIPE PAYMENT ENDPOINTS
# ============================================================================

@app.route('/api/users/<int:user_id>/credits', methods=['GET'])
@login_required
def get_user_credits(user_id):
    """Get user's current credit balance and stats"""
    if current_user.id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify({
        "balance": current_user.credit_balance,
        "auto_recharge_enabled": current_user.auto_recharge_enabled,
        "auto_recharge_amount": current_user.auto_recharge_amount,
        "auto_recharge_threshold": current_user.auto_recharge_threshold,
        "total_articles": current_user.total_articles_generated,
        "total_spent": current_user.total_spent,
        "article_cost": ARTICLE_COST
    }), 200


@app.route('/api/users/<int:user_id>/transactions', methods=['GET'])
@login_required
def get_user_transactions(user_id):
    """Get transaction history for user"""
    if current_user.id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    transactions = get_transaction_history(user_id, limit=50)
    return jsonify({"transactions": transactions}), 200


@app.route('/api/users/<int:user_id>/auto-recharge', methods=['PUT'])
@login_required
def update_auto_recharge(user_id):
    """Update auto-recharge settings"""
    if current_user.id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        data = request.json
        current_user.auto_recharge_enabled = data.get('enabled', False)
        current_user.auto_recharge_amount = max(float(data.get('amount', 10.00)), MIN_PURCHASE)
        current_user.auto_recharge_threshold = max(float(data.get('threshold', 2.50)), ARTICLE_COST)

        db.session.commit()

        return jsonify({
            "message": "Auto-recharge settings updated",
            "auto_recharge_enabled": current_user.auto_recharge_enabled,
            "auto_recharge_amount": current_user.auto_recharge_amount,
            "auto_recharge_threshold": current_user.auto_recharge_threshold
        }), 200
    except Exception as e:
        logger.error(f"Error updating auto-recharge: {e}")
        return jsonify({"error": "Failed to update settings"}), 500


@app.route('/api/credits/purchase', methods=['POST'])
@login_required
def purchase_credits():
    """Create Stripe checkout session for credit purchase"""
    try:
        data = request.json or {}
        amount = float(data.get('amount', MIN_PURCHASE))

        if amount < MIN_PURCHASE:
            return jsonify({"error": f"Minimum purchase is ${MIN_PURCHASE}"}), 400

        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'EZWAI SMM Credits',
                        'description': f'${amount:.2f} in article generation credits',
                        'images': ['https://funnelmngr.com/static/ezwai-logo.png']  # Optional: Add your logo
                    },
                    'unit_amount': int(amount * 100)  # Convert to cents
                },
                'quantity': 1
            }],
            mode='payment',
            success_url=f"{request.host_url}dashboard?purchase=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{request.host_url}dashboard?purchase=cancelled",
            metadata={
                'user_id': str(current_user.id),
                'credit_amount': str(amount),
                'type': 'credit_purchase'
            }
        )

        logger.info(f"[Stripe] Created checkout session {session.id} for user {current_user.id}")
        return jsonify({"checkout_url": session.url, "session_id": session.id}), 200

    except Exception as e:
        logger.error(f"[Stripe] Checkout error: {e}")
        return jsonify({"error": "Payment processing error. Please try again."}), 500


@app.route('/api/credits/setup-payment-method', methods=['POST'])
@login_required
def setup_payment_method():
    """Create Stripe Setup Intent for saving payment method (for auto-recharge)"""
    try:
        # Create setup intent
        setup_intent = stripe.SetupIntent.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=['card'],
            metadata={'user_id': str(current_user.id)}
        )

        return jsonify({"client_secret": setup_intent.client_secret}), 200

    except Exception as e:
        logger.error(f"[Stripe] Setup intent error: {e}")
        return jsonify({"error": "Failed to setup payment method"}), 500


@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    if not webhook_secret:
        logger.error("[Stripe] Webhook secret not configured")
        return jsonify({"error": "Webhook not configured"}), 500

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        logger.error(f"[Stripe] Invalid payload: {e}")
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"[Stripe] Invalid signature: {e}")
        return jsonify({"error": "Invalid signature"}), 400

    # Handle the event
    event_type = event['type']
    logger.info(f"[Stripe] Received event: {event_type}")

    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_completed(session)

    elif event_type == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        logger.info(f"[Stripe] PaymentIntent succeeded: {payment_intent['id']}")

    elif event_type == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        logger.error(f"[Stripe] PaymentIntent failed: {payment_intent['id']}")

    elif event_type == 'setup_intent.succeeded':
        setup_intent = event['data']['object']
        handle_setup_intent_succeeded(setup_intent)

    return jsonify({"status": "success"}), 200


def handle_checkout_completed(session):
    """Handle successful checkout session"""
    try:
        user_id = int(session['metadata']['user_id'])
        purchase_amount = float(session['metadata']['credit_amount'])  # Dollar amount paid
        payment_intent_id = session.get('payment_intent')

        # Check for duplicate webhook (prevent processing same payment twice)
        existing = CreditTransaction.query.filter_by(
            stripe_payment_intent_id=payment_intent_id,
            transaction_type='purchase'
        ).first()

        if existing:
            logger.warning(f"[Stripe] Duplicate webhook detected for payment {payment_intent_id}. Skipping.")
            return

        # Add credits to user account (function calculates credits from purchase amount)
        success = add_credits_manual(user_id, purchase_amount, payment_intent_id, db)

        if success:
            # Get user to access updated balance and send receipt
            user = User.query.get(user_id)
            if user:
                from credit_system import calculate_credits_from_purchase
                credits_added = calculate_credits_from_purchase(purchase_amount)
                logger.info(f"[Stripe] Added {credits_added} credits to user {user_id} (${purchase_amount} purchase)")

                try:
                    send_purchase_receipt_email(user.email, purchase_amount, credits_added, user.credit_balance, user.first_name)
                except Exception as email_error:
                    logger.error(f"[Stripe] Email notification failed: {email_error}")
        else:
            logger.error(f"[Stripe] Failed to add credits for user {user_id}")

    except Exception as e:
        logger.error(f"[Stripe] Error handling checkout completion: {e}")


def handle_setup_intent_succeeded(setup_intent):
    """Handle successful payment method setup"""
    try:
        user_id = int(setup_intent['metadata']['user_id'])
        payment_method_id = setup_intent['payment_method']

        # Save payment method to user
        user = User.query.get(user_id)
        if user:
            user.stripe_payment_method_id = payment_method_id
            db.session.commit()
            logger.info(f"[Stripe] Saved payment method for user {user_id}")

    except Exception as e:
        logger.error(f"[Stripe] Error handling setup intent: {e}")


# ====================================================================
# Article Library API Endpoints
# ====================================================================

@app.route('/api/users/<int:user_id>/articles', methods=['GET'])
@login_required
def get_user_articles(user_id):
    """
    Get all articles for a user with optional filtering and pagination.

    Query params:
        - status: Filter by status (draft, published, local, failed)
        - mode: Filter by generation_mode (wordpress, local)
        - search: Search in title
        - limit: Number of results (default 50)
        - offset: Pagination offset (default 0)
        - sort: Sort order (newest, oldest, title)
    """
    try:
        # Verify user access
        if current_user.id != user_id:
            return jsonify({"error": "Unauthorized"}), 403

        # Get query parameters
        status_filter = request.args.get('status')
        mode_filter = request.args.get('mode')
        search_term = request.args.get('search', '').strip()
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100
        offset = int(request.args.get('offset', 0))
        sort_order = request.args.get('sort', 'newest')

        # Build query
        query = Article.query.filter_by(user_id=user_id)

        if status_filter:
            query = query.filter_by(status=status_filter)

        if mode_filter:
            query = query.filter_by(generation_mode=mode_filter)

        if search_term:
            query = query.filter(Article.title.contains(search_term))

        # Apply sorting
        if sort_order == 'oldest':
            query = query.order_by(Article.created_at.asc())
        elif sort_order == 'title':
            query = query.order_by(Article.title.asc())
        else:  # newest (default)
            query = query.order_by(Article.created_at.desc())

        # Get total count
        total_count = query.count()

        # Apply pagination
        articles = query.limit(limit).offset(offset).all()

        # Format response
        result = {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "articles": [
                {
                    "id": article.id,
                    "title": article.title,
                    "word_count": article.word_count,
                    "status": article.status,
                    "generation_mode": article.generation_mode,
                    "hero_image_url": article.hero_image_url,
                    "wordpress_url": article.wordpress_url,
                    "created_at": article.created_at.isoformat(),
                    "updated_at": article.updated_at.isoformat()
                }
                for article in articles
            ]
        }

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"[API] Error fetching articles: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/users/<int:user_id>/articles/<int:article_id>', methods=['GET'])
@login_required
def get_article_by_id(user_id, article_id):
    """Get full article details including HTML content."""
    try:
        # Verify user access
        if current_user.id != user_id:
            return jsonify({"error": "Unauthorized"}), 403

        # Get article
        article = Article.query.filter_by(id=article_id, user_id=user_id).first()

        if not article:
            return jsonify({"error": "Article not found"}), 404

        # Format response with full details
        result = {
            "id": article.id,
            "title": article.title,
            "content_html": article.content_html,
            "hero_image_url": article.hero_image_url,
            "section_images": article.section_images,
            "word_count": article.word_count,
            "status": article.status,
            "generation_mode": article.generation_mode,
            "wordpress_post_id": article.wordpress_post_id,
            "wordpress_url": article.wordpress_url,
            "metadata": article.metadata,
            "backup_file_path": article.backup_file_path,
            "created_at": article.created_at.isoformat(),
            "updated_at": article.updated_at.isoformat()
        }

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"[API] Error fetching article {article_id}: {e}")
        return jsonify({"error": str(e)}), 500


# ====================================================================
# Image Library API Endpoints
# ====================================================================

@app.route('/api/users/<int:user_id>/images', methods=['GET'])
@login_required
def get_user_images(user_id):
    """
    Get all images for a user with optional filtering and pagination.

    Query params:
        - type: Filter by image_type (hero, section)
        - article_id: Filter by article
        - search: Search in prompt (full-text search)
        - limit: Number of results (default 50)
        - offset: Pagination offset (default 0)
        - sort: Sort order (newest, oldest)
    """
    try:
        # Verify user access
        if current_user.id != user_id:
            return jsonify({"error": "Unauthorized"}), 403

        # Get query parameters
        type_filter = request.args.get('type')
        article_id_filter = request.args.get('article_id')
        search_term = request.args.get('search', '').strip()
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100
        offset = int(request.args.get('offset', 0))
        sort_order = request.args.get('sort', 'newest')

        # Build query
        query = Image.query.filter_by(user_id=user_id)

        if type_filter:
            query = query.filter_by(image_type=type_filter)

        if article_id_filter:
            query = query.filter_by(article_id=int(article_id_filter))

        if search_term:
            query = query.filter(Image.prompt.contains(search_term))

        # Apply sorting
        if sort_order == 'oldest':
            query = query.order_by(Image.created_at.asc())
        else:  # newest (default)
            query = query.order_by(Image.created_at.desc())

        # Get total count
        total_count = query.count()

        # Apply pagination
        images = query.limit(limit).offset(offset).all()

        # Format response
        result = {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "images": [
                {
                    "id": image.id,
                    "article_id": image.article_id,
                    "image_url": image.image_url,
                    "image_type": image.image_type,
                    "prompt": image.prompt,
                    "model": image.model,
                    "aspect_ratio": image.aspect_ratio,
                    "cost_usd": image.cost_usd,
                    "tags": image.tags,
                    "created_at": image.created_at.isoformat()
                }
                for image in images
            ]
        }

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"[API] Error fetching images: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/users/<int:user_id>/images/<int:image_id>', methods=['GET'])
@login_required
def get_image_by_id(user_id, image_id):
    """Get full image details."""
    try:
        # Verify user access
        if current_user.id != user_id:
            return jsonify({"error": "Unauthorized"}), 403

        # Get image
        image = Image.query.filter_by(id=image_id, user_id=user_id).first()

        if not image:
            return jsonify({"error": "Image not found"}), 404

        # Format response with full details
        result = {
            "id": image.id,
            "article_id": image.article_id,
            "image_url": image.image_url,
            "image_type": image.image_type,
            "prompt": image.prompt,
            "model": image.model,
            "aspect_ratio": image.aspect_ratio,
            "replicate_prediction_id": image.replicate_prediction_id,
            "file_size_kb": image.file_size_kb,
            "cost_usd": image.cost_usd,
            "tags": image.tags,
            "created_at": image.created_at.isoformat()
        }

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"[API] Error fetching image {image_id}: {e}")
        return jsonify({"error": str(e)}), 500


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