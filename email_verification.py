"""
Email verification service for 2FA during registration
Sends 6-digit verification codes via SendGrid
"""
import random
import string
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

load_dotenv()
logger = logging.getLogger(__name__)

# 2FA Configuration using SendGrid
SENDGRID_API_KEY = os.getenv('EMAIL_PASSWORD')  # SendGrid API key from .env
SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL', 'joe@ezwai.com')
SMTP_FROM_NAME = os.getenv('SMTP_FROM_NAME', 'EZWAI SMM Security')

TWO_FACTOR_CODE_LENGTH = int(os.getenv('TWO_FACTOR_CODE_LENGTH', 6))
TWO_FACTOR_CODE_EXPIRE_MINUTES = int(os.getenv('TWO_FACTOR_CODE_EXPIRE_MINUTES', 10))
TWO_FACTOR_MAX_ATTEMPTS = int(os.getenv('TWO_FACTOR_MAX_ATTEMPTS', 3))


def generate_verification_code():
    """Generate a random 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=TWO_FACTOR_CODE_LENGTH))


def get_code_expiry():
    """Get expiration datetime for verification code"""
    return datetime.now(timezone.utc) + timedelta(minutes=TWO_FACTOR_CODE_EXPIRE_MINUTES)


def send_verification_email(email, verification_code, first_name=''):
    """
    Send verification code email to user

    Args:
        email: User's email address
        verification_code: 6-digit verification code
        first_name: User's first name (optional)

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # HTML email template with EZWAI branding
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    background-color: #f0f2f5;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 30px auto;
                    background-color: #ffffff;
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #08b0c4 0%, #06899a 100%);
                    padding: 30px;
                    text-align: center;
                    color: white;
                }}
                .header h1 {{
                    margin: 10px 0 0 0;
                    font-size: 28px;
                }}
                .content {{
                    padding: 30px;
                    color: #3a3a3a;
                }}
                .greeting {{
                    font-size: 18px;
                    margin-bottom: 15px;
                    color: #333;
                }}
                .code-box {{
                    background: linear-gradient(135deg, #08b0c4 0%, #06899a 100%);
                    border-radius: 12px;
                    padding: 25px;
                    text-align: center;
                    margin: 25px 0;
                }}
                .code {{
                    font-size: 36px;
                    font-weight: bold;
                    letter-spacing: 10px;
                    color: white;
                    font-family: 'Courier New', monospace;
                }}
                .warning {{
                    background: #fff3cd;
                    border-left: 5px solid #ff6b11;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 8px;
                }}
                .warning strong {{
                    color: #ff6b11;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                    border-top: 5px solid #08b0c4;
                }}
                .footer p {{
                    margin: 5px 0;
                }}
                .brand-highlight {{
                    color: #08b0c4;
                    font-weight: 600;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 EZWAI SMM</h1>
                    <p>Verify Your Email Address</p>
                </div>
                <div class="content">
                    <p class="greeting">Hi{' ' + first_name if first_name else ''},</p>

                    <p>Welcome to <span class="brand-highlight">EZWAI SMM</span>! To complete your registration, please verify your email address using the code below:</p>

                    <div class="code-box">
                        <div class="code">{verification_code}</div>
                    </div>

                    <p>Enter this code on the verification page to activate your account and start creating amazing AI-powered content.</p>

                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong><br>
                        • This code expires in {TWO_FACTOR_CODE_EXPIRE_MINUTES} minutes<br>
                        • You have {TWO_FACTOR_MAX_ATTEMPTS} attempts to enter the correct code<br>
                        • If you didn't request this code, please ignore this email
                    </div>

                    <p>Need help? Contact our support team at joe@ezwai.com</p>
                </div>
                <div class="footer">
                    <p><strong>EZWAI SMM</strong> - AI-Powered Content Automation</p>
                    <p style="color: #08b0c4;">Automated Social Media Management Made Simple</p>
                    <p style="font-size: 12px; margin-top: 10px;">This is an automated message, please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Send email via SendGrid
        sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)

        from_email = Email(SMTP_FROM_EMAIL, SMTP_FROM_NAME)
        to_email = To(email)
        subject = 'Verify Your EZWAI SMM Account'
        html_content = Content("text/html", html)

        mail = Mail(from_email, to_email, subject, html_content)

        response = sg.send(mail)

        logger.info(f"Verification email sent successfully to {email}. Status code: {response.status_code}")
        return True

    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {str(e)}")
        return False


def is_code_valid(code_expiry):
    """Check if verification code is still valid (not expired)"""
    if not code_expiry:
        return False

    # Get current time
    now = datetime.now(timezone.utc)

    # If code_expiry is timezone-naive (from database), make it timezone-aware
    if code_expiry.tzinfo is None:
        code_expiry = code_expiry.replace(tzinfo=timezone.utc)

    return now < code_expiry


def verify_code(user, submitted_code):
    """
    Verify submitted code against user's stored code

    Args:
        user: User object from database
        submitted_code: Code submitted by user

    Returns:
        tuple: (success: bool, message: str)
    """
    # Check if code exists
    if not user.verification_code:
        return False, "No verification code found. Please request a new one."

    # Check if code expired
    if not is_code_valid(user.verification_code_expiry):
        return False, "Verification code has expired. Please request a new one."

    # Check max attempts
    if user.verification_attempts >= TWO_FACTOR_MAX_ATTEMPTS:
        return False, "Maximum verification attempts exceeded. Please request a new code."

    # Check if code matches
    if user.verification_code == submitted_code:
        return True, "Email verified successfully!"
    else:
        return False, f"Invalid code. You have {TWO_FACTOR_MAX_ATTEMPTS - user.verification_attempts - 1} attempts remaining."
