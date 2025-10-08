import os
import requests
from dotenv import load_dotenv
import logging
import re
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def load_user_env(user_id):
    load_dotenv(f'.env.user_{user_id}', override=True)  # CRITICAL: Override existing env vars

def get_jwt_token(user_id):
    load_user_env(user_id)
    base_url = os.getenv('WORDPRESS_REST_API_URL', '').rstrip('/')
    
    # Remove '/wp-json/wp/v2' if it's at the end of the base_url
    if base_url.endswith('/wp-json/wp/v2'):
        base_url = base_url[:-len('/wp-json/wp/v2')]
    elif base_url.endswith('/wp-json'):
        base_url = base_url[:-len('/wp-json')]
    
    auth_url = f"{base_url}/wp-json/jwt-auth/v1/token"
    
    logger.debug(f"JWT auth URL: {auth_url}")
    
    try:
        response = requests.post(
            auth_url,
            data={
                "username": os.getenv("WORDPRESS_USERNAME"),
                "password": os.getenv("WORDPRESS_PASSWORD")
            },
            headers={
                "X-JWT-Auth-Secret": os.getenv("FLASK_SECRET_KEY")
            }
        )
        response.raise_for_status()
        return response.json().get('token')
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting JWT token: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.text}")
        return None

def download_image(image_url, image_path):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        with open(image_path, 'wb') as file:
            file.write(response.content)
        logger.info(f"Image downloaded: {image_path}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading image: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.text}")

def create_media_id(image_path, user_id):
    load_user_env(user_id)
    token = get_jwt_token(user_id)
    if not token:
        return None

    base_url = os.getenv('WORDPRESS_REST_API_URL', '').rstrip('/')
    if base_url.endswith('/wp-json/wp/v2'):
        base_url = base_url[:-len('/wp-json/wp/v2')]
    elif base_url.endswith('/wp-json'):
        base_url = base_url[:-len('/wp-json')]
    
    url = f"{base_url}/wp-json/wp/v2/media"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        with open(image_path, "rb") as image_file:
            files = {"file": image_file}
            response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()
        return response.json().get('id')
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating media: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.text}")
        return None

def create_wordpress_post(title, content, user_id, image_url=None):
    load_user_env(user_id)
    base_url = os.getenv("WORDPRESS_REST_API_URL", '').rstrip('/')
    
    # Remove '/wp-json/wp/v2' if it's at the end of the base_url
    if base_url.endswith('/wp-json/wp/v2'):
        base_url = base_url[:-len('/wp-json/wp/v2')]
    elif base_url.endswith('/wp-json'):
        base_url = base_url[:-len('/wp-json')]

    if image_url:
        # Generate a unique filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"post_image_{user_id}_{timestamp}.jpg"
        
        download_image(image_url, unique_filename)
        media_id = create_media_id(unique_filename, user_id)
        os.remove(unique_filename)  # Clean up the temporary image file
    else:
        media_id = None

    token = get_jwt_token(user_id)
    if not token:
        return None

    post_data = {
        "title": title,
        "content": content,
        "status": "draft",
        "featured_media": media_id,
        "format": "standard"  # Ensure the post format supports HTML content
    }

    posts_url = f"{base_url}/wp-json/wp/v2/posts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(posts_url, json=post_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating WordPress post: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.text}")
        return None

def get_wordpress_posts(user_id, per_page=10, page=1):
    load_user_env(user_id)
    base_url = os.getenv("WORDPRESS_REST_API_URL").rstrip('/')
    if base_url.endswith('/wp-json/wp/v2'):
        base_url = base_url[:-len('/wp-json/wp/v2')]
    elif base_url.endswith('/wp-json'):
        base_url = base_url[:-len('/wp-json')]
    
    token = get_jwt_token(user_id)
    if not token:
        return None
    
    headers = {
        "Authorization": f"Bearer {token}",
    }
    params = {
        "per_page": per_page,
        "page": page,
    }
    try:
        response = requests.get(f"{base_url}/wp-json/wp/v2/posts", headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching WordPress posts: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.text}")
        return None

def publish_wordpress_post(post_id, user_id):
    """
    Publish a WordPress draft post (change status from draft to publish)

    Args:
        post_id: WordPress post ID
        user_id: User ID for authentication

    Returns:
        dict: Updated post data or None if failed
    """
    load_user_env(user_id)
    base_url = os.getenv("WORDPRESS_REST_API_URL").rstrip('/')
    if base_url.endswith('/wp-json/wp/v2'):
        base_url = base_url[:-len('/wp-json/wp/v2')]
    elif base_url.endswith('/wp-json'):
        base_url = base_url[:-len('/wp-json')]

    token = get_jwt_token(user_id)
    if not token:
        return None

    post_data = {
        "status": "publish"
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{base_url}/wp-json/wp/v2/posts/{post_id}",
            headers=headers,
            json=post_data
        )
        response.raise_for_status()
        logger.info(f"Successfully published post {post_id}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error publishing WordPress post {post_id}: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.text}")
        return None


def update_wordpress_post(post_id, title, content, user_id, image_url=None):
    load_user_env(user_id)
    base_url = os.getenv("WORDPRESS_REST_API_URL").rstrip('/')
    if base_url.endswith('/wp-json/wp/v2'):
        base_url = base_url[:-len('/wp-json/wp/v2')]
    elif base_url.endswith('/wp-json'):
        base_url = base_url[:-len('/wp-json')]
    
    if image_url:
        # Generate a unique filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"post_image_{user_id}_{timestamp}.jpg"
        
        download_image(image_url, unique_filename)
        media_id = create_media_id(unique_filename, user_id)
        os.remove(unique_filename)  # Clean up the temporary image file
    else:
        media_id = None

    token = get_jwt_token(user_id)
    if not token:
        return None

    post_data = {
        "title": title,
        "content": content,
        "featured_media": media_id
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(f"{base_url}/wp-json/wp/v2/posts/{post_id}", headers=headers, json=post_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating WordPress post: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response content: {e.response.text}")
        return None
