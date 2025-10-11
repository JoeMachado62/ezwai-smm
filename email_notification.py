import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment
import base64
import logging

logger = logging.getLogger(__name__)

def send_email_notification(post_id, title, content, img_url, user_email, wordpress_url):
    try:
        sg = SendGridAPIClient(api_key=os.environ.get('EMAIL_PASSWORD'))

        from_email = Email("joe@ezwai.com")  # Make sure this is your verified sender email
        to_email = To(user_email)
        subject = f"✅ New Magazine-Style Article Ready: {title}"

        # Generate the publish link for direct publishing from email
        publish_link = f"{wordpress_url}/wp-admin/post.php?post={post_id}&action=edit"

        html_content = f"""
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
                    max-width: 650px;
                    margin: 30px auto;
                    background-color: #ffffff;
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #08b0c4 0%, #06899a 100%);
                    padding: 35px;
                    text-align: center;
                    color: white;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 30px;
                    font-weight: 700;
                }}
                .header p {{
                    margin: 12px 0 0 0;
                    font-size: 17px;
                    opacity: 0.95;
                }}
                .status-badge {{
                    display: inline-block;
                    background: rgba(255, 255, 255, 0.3);
                    padding: 8px 20px;
                    border-radius: 20px;
                    margin-top: 10px;
                    font-size: 14px;
                    font-weight: 600;
                }}
                .content {{
                    padding: 35px;
                    color: #3a3a3a;
                }}
                .content h2 {{
                    color: #08b0c4;
                    font-size: 22px;
                    margin-top: 0;
                    margin-bottom: 15px;
                    line-height: 1.4;
                }}
                .content p {{
                    line-height: 1.7;
                    color: #666;
                    font-size: 15px;
                }}
                .validation-section {{
                    background: #e9f7fe;
                    border-left: 5px solid #08b0c4;
                    padding: 20px;
                    margin: 25px 0;
                    border-radius: 8px;
                }}
                .validation-section h3 {{
                    color: #08b0c4;
                    margin-top: 0;
                    font-size: 18px;
                }}
                .validation-item {{
                    padding: 8px 0;
                    color: #2d8a4d;
                    font-weight: 500;
                }}
                .validation-item:before {{
                    content: "✓ ";
                    font-weight: bold;
                    margin-right: 8px;
                }}
                .image-container {{
                    margin: 25px 0;
                    text-align: center;
                }}
                .image-container img {{
                    max-width: 100%;
                    border-radius: 12px;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
                }}
                .button-container {{
                    text-align: center;
                    margin: 35px 0;
                }}
                .btn-primary {{
                    display: inline-block;
                    padding: 18px 40px;
                    background: linear-gradient(135deg, #2d8a4d 0%, #1f6335 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 12px;
                    font-size: 17px;
                    font-weight: 700;
                    box-shadow: 0 6px 20px rgba(45, 138, 77, 0.4);
                    margin: 10px;
                }}
                .btn-secondary {{
                    display: inline-block;
                    padding: 18px 40px;
                    background: linear-gradient(135deg, #ff6b11 0%, #e55a00 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 12px;
                    font-size: 17px;
                    font-weight: 700;
                    box-shadow: 0 6px 20px rgba(255, 107, 17, 0.4);
                    margin: 10px;
                }}
                .info-box {{
                    background: #fff3cd;
                    border-left: 5px solid #ff6b11;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 8px;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 25px;
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                    border-top: 5px solid #08b0c4;
                }}
                .footer p {{
                    margin: 8px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 EZWAI SMM</h1>
                    <p>Your AI-Generated Magazine Article is Ready!</p>
                    <div class="status-badge">📝 Draft Status - Awaiting Review</div>
                </div>
                <div class="content">
                    <h2>{title}</h2>

                    <div class="validation-section">
                        <h3>✅ Article Quality Validation Passed</h3>
                        <div class="validation-item">Magazine-style HTML formatting applied</div>
                        <div class="validation-item">Hero image with overlay title included</div>
                        <div class="validation-item">All 4 photorealistic images embedded (1 hero + 3 sections)</div>
                        <div class="validation-item">Professional typography and styling</div>
                        <div class="validation-item">1500-2500 word comprehensive content</div>
                    </div>

                    <div class="image-container">
                        <img src='{img_url}' alt='Article Hero Image' />
                        <p style="font-size: 13px; color: #999; margin-top: 10px;">Hero Image (2K Resolution - SeeDream-4)</p>
                    </div>

                    <div class="info-box">
                        <strong>📋 Article Preview:</strong><br>
                        {content[:300]}...
                    </div>

                    <div class="button-container">
                        <a href='{publish_link}' class="btn-secondary">
                            📝 Review & Edit in WordPress
                        </a>
                    </div>

                    <p style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #e9f7fe;">
                        <strong>Ready to publish?</strong><br>
                        Review your article in WordPress and click "Publish" when you're satisfied with the content.
                    </p>
                </div>
                <div class="footer">
                    <p><strong>EZWAI SMM</strong> - AI-Powered Magazine Content Automation</p>
                    <p style="color: #08b0c4; font-weight: 600;">✨ Generated with GPT-5-mini Reasoning + SeeDream-4 2K Images</p>
                    <p style="font-size: 12px; margin-top: 15px; color: #999;">
                        This email was sent because you have an active EZWAI SMM account.<br>
                        The post is currently saved as a draft in your WordPress site.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        content = Content("text/html", html_content)
        mail = Mail(from_email, to_email, subject, content)

        response = sg.send(mail)
        logger.info(f"Email notification sent to {user_email}. Status code: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

def send_article_notification_with_attachment(
    title,
    article_html,
    hero_image_url,
    user_email,
    mode="wordpress",
    wordpress_url=None,
    post_id=None
):
    """
    Send email notification with full article HTML as attachment.

    Supports two modes:
    1. WordPress mode: Article published to WordPress, email includes review link
    2. Local mode: Self-contained HTML article, ready to copy/paste or share

    Args:
        title: Article title
        article_html: Complete HTML content with styling
        hero_image_url: Hero image URL or base64 data URI
        user_email: Recipient email
        mode: "wordpress" or "local"
        wordpress_url: WordPress site URL (required for WordPress mode)
        post_id: WordPress post ID (required for WordPress mode)

    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        sg = SendGridAPIClient(api_key=os.environ.get('EMAIL_PASSWORD'))

        from_email = Email("joe@ezwai.com")
        to_email = To(user_email)

        # Generate subject based on mode
        if mode == "wordpress":
            subject = f"✅ Article Published: {title}"
        else:
            subject = f"📄 Your Article is Ready: {title}"

        # Generate email body based on mode
        if mode == "wordpress":
            publish_link = f"{wordpress_url}/wp-admin/post.php?post={post_id}&action=edit"
            email_body = f"""
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
                        max-width: 650px;
                        margin: 30px auto;
                        background-color: #ffffff;
                        border-radius: 20px;
                        overflow: hidden;
                        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
                        padding: 35px;
                        text-align: center;
                        color: white;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 30px;
                        font-weight: 700;
                    }}
                    .content {{
                        padding: 35px;
                        color: #3a3a3a;
                    }}
                    .content h2 {{
                        color: #7c3aed;
                        font-size: 22px;
                        margin-top: 0;
                    }}
                    .btn-primary {{
                        display: inline-block;
                        padding: 18px 40px;
                        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
                        color: white;
                        text-decoration: none;
                        border-radius: 12px;
                        font-size: 17px;
                        font-weight: 700;
                        margin: 20px 0;
                    }}
                    .info-box {{
                        background: #f3f4f6;
                        border-left: 5px solid #7c3aed;
                        padding: 20px;
                        margin: 20px 0;
                        border-radius: 8px;
                    }}
                    .footer {{
                        background-color: #f8f9fa;
                        padding: 25px;
                        text-align: center;
                        color: #666;
                        font-size: 14px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚀 My Content Generator</h1>
                        <p>Your AI-Generated Article is Ready!</p>
                    </div>
                    <div class="content">
                        <h2>{title}</h2>

                        <p>Your magazine-style article has been created and saved as a draft in WordPress.</p>

                        <div class="info-box">
                            <strong>📎 Attached:</strong> Full HTML article<br>
                            <strong>✨ Features:</strong> Premium magazine layout with Claude AI formatter<br>
                            <strong>🖼️ Images:</strong> 4-5 photorealistic 2K images embedded<br>
                            <strong>📝 Length:</strong> 1500-2500 words of professional content
                        </div>

                        <p><strong>What you can do with this article:</strong></p>
                        <ul>
                            <li>Review and publish directly in WordPress</li>
                            <li>Download the HTML attachment for your records</li>
                            <li>Copy/paste content to LinkedIn, Facebook, or other platforms</li>
                            <li>Share the HTML file with your team</li>
                        </ul>

                        <div style="text-align: center;">
                            <a href='{publish_link}' class="btn-primary">
                                📝 Review in WordPress →
                            </a>
                        </div>

                        <p style="margin-top: 30px; font-size: 13px; color: #666;">
                            💡 <strong>Tip:</strong> The attached HTML file can be opened in any browser or
                            copied directly into email/social media posts while preserving all formatting.
                        </p>
                    </div>
                    <div class="footer">
                        <p><strong>My Content Generator</strong> - AI-Powered Content Creation</p>
                        <p style="color: #7c3aed;">✨ Generated with GPT-5 + Claude AI + SeeDream-4</p>
                    </div>
                </div>
            </body>
            </html>
            """
        else:  # local mode
            email_body = f"""
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
                        max-width: 650px;
                        margin: 30px auto;
                        background-color: #ffffff;
                        border-radius: 20px;
                        overflow: hidden;
                        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
                        padding: 35px;
                        text-align: center;
                        color: white;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 30px;
                        font-weight: 700;
                    }}
                    .content {{
                        padding: 35px;
                        color: #3a3a3a;
                    }}
                    .content h2 {{
                        color: #7c3aed;
                        font-size: 22px;
                        margin-top: 0;
                    }}
                    .info-box {{
                        background: #f3f4f6;
                        border-left: 5px solid #7c3aed;
                        padding: 20px;
                        margin: 20px 0;
                        border-radius: 8px;
                    }}
                    .usage-list {{
                        background: #f0fdf4;
                        border-left: 5px solid #22c55e;
                        padding: 20px;
                        margin: 20px 0;
                        border-radius: 8px;
                    }}
                    .footer {{
                        background-color: #f8f9fa;
                        padding: 25px;
                        text-align: center;
                        color: #666;
                        font-size: 14px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📄 My Content Generator</h1>
                        <p>Your Downloadable Article is Ready!</p>
                    </div>
                    <div class="content">
                        <h2>{title}</h2>

                        <p>Your premium magazine-style article is attached as a self-contained HTML file.</p>

                        <div class="info-box">
                            <strong>📎 Attachment:</strong> Complete HTML article with embedded images<br>
                            <strong>💾 File Size:</strong> 8-10 MB (all images embedded as base64)<br>
                            <strong>✨ Quality:</strong> Premium Claude AI magazine layout<br>
                            <strong>📝 Length:</strong> 1500-2500 words of professional content
                        </div>

                        <div class="usage-list">
                            <p><strong>📢 How to use your article:</strong></p>
                            <ul style="margin: 10px 0; padding-left: 20px;">
                                <li><strong>LinkedIn Post:</strong> Open HTML, copy content, paste into LinkedIn (formatting preserved)</li>
                                <li><strong>Facebook Post:</strong> Same process - copy from browser, paste to Facebook</li>
                                <li><strong>Email Newsletter:</strong> Copy article content directly into your email composer</li>
                                <li><strong>Medium/Blog:</strong> Copy/paste to your CMS while retaining all styling</li>
                                <li><strong>Portfolio:</strong> Open in browser for offline viewing or presentation</li>
                                <li><strong>Team Sharing:</strong> Forward this email or share the HTML file</li>
                            </ul>
                        </div>

                        <p style="margin-top: 30px; font-size: 14px; background: #fef3c7; padding: 15px; border-radius: 8px;">
                            <strong>💡 Pro Tip:</strong> To copy for social media:<br>
                            1. Open the attached HTML file in your browser<br>
                            2. Select the content you want (Ctrl+A for all)<br>
                            3. Copy (Ctrl+C)<br>
                            4. Paste into LinkedIn/Facebook/email (Ctrl+V)<br>
                            All formatting, images, and styling will be preserved! ✨
                        </p>
                    </div>
                    <div class="footer">
                        <p><strong>My Content Generator</strong> - Professional Content, Delivered</p>
                        <p style="color: #7c3aed;">✨ Generated with GPT-5 + Claude AI + SeeDream-4</p>
                    </div>
                </div>
            </body>
            </html>
            """

        content = Content("text/html", email_body)
        mail = Mail(from_email, to_email, subject, content)

        # Attach the full article HTML
        # Create a sanitized filename
        safe_filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_filename = safe_filename[:50]  # Limit length
        safe_filename = f"{safe_filename}.html" if safe_filename else "article.html"

        # Encode article HTML as base64 for attachment
        article_bytes = article_html.encode('utf-8')
        article_base64 = base64.b64encode(article_bytes).decode('utf-8')

        attachment = Attachment()
        attachment.file_content = article_base64
        attachment.file_name = safe_filename
        attachment.file_type = "text/html"
        attachment.disposition = "attachment"

        mail.attachment = attachment

        # Send email
        response = sg.send(mail)
        logger.info(f"Article email sent to {user_email}. Status: {response.status_code}, Mode: {mode}")
        return True

    except Exception as e:
        logger.error(f"Failed to send article email: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


# Add some debug logging to check environment variables
logger.debug(f"EMAIL_HOST: {os.environ.get('EMAIL_HOST')}")
logger.debug(f"EMAIL_PORT: {os.environ.get('EMAIL_PORT')}")
logger.debug(f"EMAIL_USERNAME: {os.environ.get('EMAIL_USERNAME')}")
logger.debug(f"EMAIL_PASSWORD: {'*' * len(os.environ.get('EMAIL_PASSWORD', ''))}")  # Mask the password