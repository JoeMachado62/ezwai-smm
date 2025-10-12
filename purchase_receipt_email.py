"""
Email receipt service for credit purchases
Sends professional receipts via SendGrid
"""
import os
from dotenv import load_dotenv
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from datetime import datetime

load_dotenv()
logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.getenv('EMAIL_PASSWORD')  # SendGrid API key from .env
SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL', 'support@mycontentgenerator.com')
SMTP_FROM_NAME = os.getenv('SMTP_FROM_NAME', 'My Content Generator')


def send_purchase_receipt_email(email, purchase_amount, credits_added, new_balance, first_name=''):
    """
    Send purchase receipt email to user

    Args:
        email: User's email address
        purchase_amount: Dollar amount paid
        credits_added: Number of credits added
        new_balance: New credit balance
        first_name: User's first name (optional)

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        purchase_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")

        # HTML email template with My Content Generator branding
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
                    background: linear-gradient(135deg, #6B5DD3 0%, #4A9FE8 100%);
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
                .receipt-box {{
                    background: #f8f9ff;
                    border-radius: 12px;
                    padding: 25px;
                    margin: 25px 0;
                    border-left: 5px solid #6B5DD3;
                }}
                .receipt-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid #e0e0e0;
                }}
                .receipt-row:last-child {{
                    border-bottom: none;
                }}
                .receipt-label {{
                    color: #666;
                    font-weight: 500;
                }}
                .receipt-value {{
                    color: #333;
                    font-weight: 600;
                }}
                .receipt-total {{
                    background: linear-gradient(135deg, #6B5DD3 0%, #4A9FE8 100%);
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                    margin-top: 20px;
                    font-size: 20px;
                    font-weight: 700;
                }}
                .success-badge {{
                    background: #d4edda;
                    border-left: 5px solid #28a745;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 8px;
                    color: #155724;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                    border-top: 5px solid #6B5DD3;
                }}
                .footer p {{
                    margin: 5px 0;
                }}
                .brand-highlight {{
                    color: #6B5DD3;
                    font-weight: 600;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💳 Purchase Receipt</h1>
                    <p>My Content Generator</p>
                </div>
                <div class="content">
                    <p class="greeting">Hi{' ' + first_name if first_name else ''},</p>

                    <div class="success-badge">
                        <strong>✅ Payment Successful!</strong><br>
                        Thank you for your purchase. Your credits have been added to your account.
                    </div>

                    <div class="receipt-box">
                        <h3 style="margin-top: 0; color: #6B5DD3;">Purchase Details</h3>

                        <div class="receipt-row">
                            <span class="receipt-label">Date:</span>
                            <span class="receipt-value">{purchase_date}</span>
                        </div>

                        <div class="receipt-row">
                            <span class="receipt-label">Amount Paid:</span>
                            <span class="receipt-value">${purchase_amount:.2f} USD</span>
                        </div>

                        <div class="receipt-row">
                            <span class="receipt-label">Credits Added:</span>
                            <span class="receipt-value">{credits_added} credits</span>
                        </div>

                        <div class="receipt-row">
                            <span class="receipt-label">Price Per Article:</span>
                            <span class="receipt-value">${purchase_amount / credits_added:.2f}</span>
                        </div>

                        <div class="receipt-total">
                            New Balance: {int(new_balance)} credits
                        </div>
                    </div>

                    <p>Your credits are ready to use! Each credit allows you to generate one professional magazine-style blog post with AI-powered content and photorealistic images.</p>

                    <p style="margin-top: 30px;">Questions or need help? Contact our support team at <a href="mailto:support@mycontentgenerator.com" style="color: #6B5DD3; text-decoration: none;">support@mycontentgenerator.com</a></p>
                </div>
                <div class="footer">
                    <p><strong>My Content Generator</strong> - AI-Powered Blog Content for WordPress</p>
                    <p style="color: #6B5DD3;">Professional Content Creation Made Simple</p>
                    <p style="font-size: 12px; margin-top: 10px;">This is an automated receipt. Please keep it for your records.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Send email via SendGrid
        sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)

        from_email = Email(SMTP_FROM_EMAIL, SMTP_FROM_NAME)
        to_email = To(email)
        subject = f'Receipt for ${purchase_amount:.2f} Credit Purchase - My Content Generator'
        html_content = Content("text/html", html)

        mail = Mail(from_email, to_email, subject, html_content)

        response = sg.send(mail)

        logger.info(f"Purchase receipt email sent successfully to {email}. Status code: {response.status_code}")
        return True

    except Exception as e:
        logger.error(f"Failed to send purchase receipt email to {email}: {str(e)}")
        return False
