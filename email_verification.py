"""
Email verification service for 2FA during registration
Sends 6-digit verification codes via SMTP
"""
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# 2FA Configuration
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL', SMTP_USERNAME)
SMTP_FROM_NAME = os.getenv('SMTP_FROM_NAME', 'EZWAI SMM Security')

TWO_FACTOR_CODE_LENGTH = int(os.getenv('TWO_FACTOR_CODE_LENGTH', 6))
TWO_FACTOR_CODE_EXPIRE_MINUTES = int(os.getenv('TWO_FACTOR_CODE_EXPIRE_MINUTES', 10))
TWO_FACTOR_MAX_ATTEMPTS = int(os.getenv('TWO_FACTOR_MAX_ATTEMPTS', 3))


def generate_verification_code():
    """Generate a random 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=TWO_FACTOR_CODE_LENGTH))


def get_code_expiry():
    """Get expiration datetime for verification code"""
    return datetime.utcnow() + timedelta(minutes=TWO_FACTOR_CODE_EXPIRE_MINUTES)


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
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Verify Your EZWAI SMM Account'
        msg['From'] = f'{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>'
        msg['To'] = email

        # HTML email template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .code-box {{
                    background: white;
                    border: 2px solid #667eea;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    margin: 20px 0;
                }}
                .code {{
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    color: #667eea;
                    font-family: 'Courier New', monospace;
                }}
                .warning {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 12px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Verify Your Email</h1>
            </div>
            <div class="content">
                <p>Hi{' ' + first_name if first_name else ''},</p>

                <p>Welcome to EZWAI SMM! To complete your registration, please verify your email address using the code below:</p>

                <div class="code-box">
                    <div class="code">{verification_code}</div>
                </div>

                <p>Enter this code on the verification page to activate your account.</p>

                <div class="warning">
                    <strong>⚠️ Security Notice:</strong><br>
                    • This code expires in {TWO_FACTOR_CODE_EXPIRE_MINUTES} minutes<br>
                    • You have {TWO_FACTOR_MAX_ATTEMPTS} attempts to enter the correct code<br>
                    • If you didn't request this code, please ignore this email
                </div>

                <p>Need help? Contact our support team.</p>
            </div>
            <div class="footer">
                <p>EZWAI SMM - Automated Social Media Management</p>
                <p>This is an automated message, please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

        # Plain text fallback
        text = f"""
        Verify Your Email

        Hi{' ' + first_name if first_name else ''},

        Welcome to EZWAI SMM! To complete your registration, please verify your email address using the code below:

        Verification Code: {verification_code}

        Enter this code on the verification page to activate your account.

        SECURITY NOTICE:
        - This code expires in {TWO_FACTOR_CODE_EXPIRE_MINUTES} minutes
        - You have {TWO_FACTOR_MAX_ATTEMPTS} attempts to enter the correct code
        - If you didn't request this code, please ignore this email

        Need help? Contact our support team.

        ---
        EZWAI SMM - Automated Social Media Management
        This is an automated message, please do not reply to this email.
        """

        # Attach both HTML and plain text versions
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Verification email sent successfully to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {str(e)}")
        return False


def is_code_valid(code_expiry):
    """Check if verification code is still valid (not expired)"""
    if not code_expiry:
        return False
    return datetime.utcnow() < code_expiry


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
