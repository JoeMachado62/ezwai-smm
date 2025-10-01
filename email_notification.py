import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import logging

logger = logging.getLogger(__name__)

def send_email_notification(post_id, title, content, img_url, user_email, wordpress_url):
    try:
        sg = SendGridAPIClient(api_key=os.environ.get('EMAIL_PASSWORD'))
        
        from_email = Email("joe@ezwai.com")  # Make sure this is your verified sender email
        to_email = To(user_email)
        subject = f"New Draft Post: {title}"
        
        html_content = f"""
        <html>
        <head></head>
        <body>
            <h1>{title}</h1>
            <p>{content[:500]}...</p>  # Limit content to first 500 characters
            <img src='{img_url}' style='max-width: 100%;' />
            <a href='{wordpress_url}/wp-admin/post.php?post={post_id}&action=edit'>
            <button style="padding: 10px; background-color: #0073aa; color: white; border: none; cursor: pointer;">Publish Post</button>
            </a>
        </body>
        </html>
        """
        
        content = Content("text/html", html_content)
        mail = Mail(from_email, to_email, subject, content)

        response = sg.client.mail.send.post(request_body=mail.get())
        logger.info(f"Email notification sent to {user_email}. Status code: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

# Add some debug logging to check environment variables
logger.debug(f"EMAIL_HOST: {os.environ.get('EMAIL_HOST')}")
logger.debug(f"EMAIL_PORT: {os.environ.get('EMAIL_PORT')}")
logger.debug(f"EMAIL_USERNAME: {os.environ.get('EMAIL_USERNAME')}")
logger.debug(f"EMAIL_PASSWORD: {'*' * len(os.environ.get('EMAIL_PASSWORD', ''))}")  # Mask the password