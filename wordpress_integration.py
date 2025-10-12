import os
import requests
import logging
from typing import Optional, Dict, Any, Tuple
import base64
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def normalize_wordpress_url(url: str) -> str:
    """
    Normalize WordPress URL to base site URL.

    Examples:
        https://example.com -> https://example.com
        https://example.com/ -> https://example.com
        https://example.com/wp-json -> https://example.com
        https://example.com/wp-json/wp/v2 -> https://example.com

    Args:
        url: Raw URL from user input

    Returns:
        Clean base URL without trailing slash or wp-json paths
    """
    url = url.rstrip('/')

    # Remove wp-json paths if present
    if url.endswith('/wp-json/wp/v2'):
        url = url[:-len('/wp-json/wp/v2')]
    elif url.endswith('/wp-json'):
        url = url[:-len('/wp-json')]

    return url

def construct_api_endpoint(base_url: str, endpoint: str = '') -> str:
    """
    Construct full WordPress REST API endpoint.

    Args:
        base_url: Base WordPress site URL (e.g., https://example.com)
        endpoint: Optional specific endpoint (e.g., 'posts', 'media')

    Returns:
        Full API URL (e.g., https://example.com/wp-json/wp/v2/posts)
    """
    base_url = normalize_wordpress_url(base_url)

    if endpoint:
        return f"{base_url}/wp-json/wp/v2/{endpoint}"
    return f"{base_url}/wp-json/wp/v2"

def get_wordpress_credentials(user_id: int) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Get WordPress credentials from user database.

    Args:
        user_id: User ID

    Returns:
        Tuple of (base_url, username, app_password) or (None, None, None) if not configured
    """
    try:
        # Import here to avoid circular dependency
        import sys
        from pathlib import Path

        # Add project root to path if not already there
        project_root = Path(__file__).parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        from app_v3 import User

        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found")
            return None, None, None

        if not user.wordpress_rest_api_url or not user.wordpress_app_password:
            logger.error(f"User {user_id} has incomplete WordPress configuration")
            return None, None, None

        # Use email username as WordPress username (common pattern)
        username = user.email.split('@')[0]

        base_url = normalize_wordpress_url(user.wordpress_rest_api_url)
        app_password = user.wordpress_app_password.replace(' ', '')  # Remove spaces from app password

        return base_url, username, app_password
    except Exception as e:
        logger.error(f"Error getting WordPress credentials for user {user_id}: {str(e)}")
        return None, None, None

def create_auth_header(username: str, app_password: str) -> Dict[str, str]:
    """
    Create Basic Authentication header for WordPress Application Password.

    Args:
        username: WordPress username
        app_password: WordPress Application Password (spaces will be removed)

    Returns:
        Dictionary with Authorization header
    """
    # Remove spaces from app password
    clean_password = app_password.replace(' ', '')

    # Create credentials string
    credentials = f"{username}:{clean_password}"

    # Encode to base64
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

    return {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json'
    }

def test_wordpress_connection(user_id: int) -> Tuple[bool, str]:
    """
    Test WordPress connection with Application Password.

    Args:
        user_id: User ID

    Returns:
        Tuple of (success: bool, message: str)
    """
    base_url, username, app_password = get_wordpress_credentials(user_id)

    if not all([base_url, username, app_password]):
        return False, "WordPress credentials not configured"

    try:
        # Test connection by fetching site info
        endpoint = construct_api_endpoint(base_url)
        headers = create_auth_header(username, app_password)

        response = requests.get(endpoint, headers=headers, timeout=10)

        if response.status_code == 200:
            return True, "WordPress connection successful!"
        elif response.status_code == 401:
            return False, "Authentication failed. Please check your Application Password."
        else:
            return False, f"Connection failed with status code: {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "Connection timeout. Please check your WordPress URL."
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"

def upload_image_to_wordpress(image_path: str, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Upload image to WordPress media library using Application Password.

    Args:
        image_path: Local path to image file
        user_id: User ID

    Returns:
        Media object dict with 'id' and 'source_url', or None if failed
    """
    base_url, username, app_password = get_wordpress_credentials(user_id)

    if not all([base_url, username, app_password]):
        logger.error(f"WordPress credentials not configured for user {user_id}")
        return None

    try:
        endpoint = construct_api_endpoint(base_url, 'media')
        headers = create_auth_header(username, app_password)

        # Remove Content-Type from headers for file upload
        file_headers = {
            'Authorization': headers['Authorization'],
            'Content-Disposition': f'attachment; filename="{os.path.basename(image_path)}"'
        }

        with open(image_path, 'rb') as img:
            response = requests.post(
                endpoint,
                headers=file_headers,
                data=img,
                timeout=30
            )

        if response.status_code == 201:
            media = response.json()
            logger.info(f"Image uploaded successfully: {media.get('source_url')}")
            return media
        else:
            logger.error(f"Failed to upload image: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error uploading image to WordPress: {str(e)}")
        return None

def download_image(image_url: str, image_path: str) -> bool:
    """
    Download image from URL to local path.

    Args:
        image_url: URL of image to download
        image_path: Local path to save image

    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        with open(image_path, 'wb') as file:
            file.write(response.content)
        logger.info(f"Image downloaded: {image_path}")
        return True
    except Exception as e:
        logger.error(f"Error downloading image: {str(e)}")
        return False

def create_media_id(image_path: str, user_id: int) -> Optional[int]:
    """
    Upload image and get media ID (legacy function for compatibility).

    Args:
        image_path: Local path to image file
        user_id: User ID

    Returns:
        Media ID or None if failed
    """
    media = upload_image_to_wordpress(image_path, user_id)
    if media:
        return media.get('id')
    return None

def create_wordpress_post(
    title: str,
    content: str,
    user_id: int,
    image_url: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Create WordPress post using Application Password.

    Args:
        title: Post title
        content: Post content (HTML)
        user_id: User ID
        image_url: Optional featured image URL (will be downloaded and uploaded)

    Returns:
        Post object dict, or None if failed
    """
    base_url, username, app_password = get_wordpress_credentials(user_id)

    if not all([base_url, username, app_password]):
        logger.error(f"WordPress credentials not configured for user {user_id}")
        return None

    media_id = None
    if image_url:
        # Download and upload image
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"post_image_{user_id}_{timestamp}.jpg"

        if download_image(image_url, unique_filename):
            media_id = create_media_id(unique_filename, user_id)
            try:
                os.remove(unique_filename)  # Clean up
            except:
                pass

    try:
        endpoint = construct_api_endpoint(base_url, 'posts')
        headers = create_auth_header(username, app_password)

        post_data = {
            'title': title,
            'content': content,
            'status': 'draft',  # Create as draft for user review
            'format': 'standard'
        }

        # Add featured image if uploaded successfully
        if media_id:
            post_data['featured_media'] = media_id

        response = requests.post(
            endpoint,
            headers=headers,
            json=post_data,
            timeout=30
        )

        if response.status_code == 201:
            post = response.json()
            logger.info(f"WordPress post created successfully: {post.get('id')}")
            return post
        else:
            logger.error(f"Failed to create post: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error creating WordPress post: {str(e)}")
        return None

def publish_wordpress_post(post_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Change post status from draft to published.

    Args:
        post_id: WordPress post ID
        user_id: User ID

    Returns:
        Updated post object dict if successful, None otherwise
    """
    base_url, username, app_password = get_wordpress_credentials(user_id)

    if not all([base_url, username, app_password]):
        logger.error(f"WordPress credentials not configured for user {user_id}")
        return None

    try:
        endpoint = construct_api_endpoint(base_url, f'posts/{post_id}')
        headers = create_auth_header(username, app_password)

        response = requests.post(
            endpoint,
            headers=headers,
            json={'status': 'publish'},
            timeout=30
        )

        if response.status_code == 200:
            logger.info(f"Post {post_id} published successfully")
            return response.json()
        else:
            logger.error(f"Failed to publish post: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error publishing post: {str(e)}")
        return None

def update_wordpress_post(
    post_id: int,
    title: str,
    content: str,
    user_id: int,
    image_url: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Update existing WordPress post.

    Args:
        post_id: WordPress post ID to update
        title: New post title
        content: New post content (HTML)
        user_id: User ID
        image_url: Optional new featured image URL

    Returns:
        Updated post object dict, or None if failed
    """
    base_url, username, app_password = get_wordpress_credentials(user_id)

    if not all([base_url, username, app_password]):
        logger.error(f"WordPress credentials not configured for user {user_id}")
        return None

    media_id = None
    if image_url:
        # Download and upload new image
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"post_image_{user_id}_{timestamp}.jpg"

        if download_image(image_url, unique_filename):
            media_id = create_media_id(unique_filename, user_id)
            try:
                os.remove(unique_filename)
            except:
                pass

    try:
        endpoint = construct_api_endpoint(base_url, f'posts/{post_id}')
        headers = create_auth_header(username, app_password)

        post_data = {
            'title': title,
            'content': content
        }

        if media_id:
            post_data['featured_media'] = media_id

        response = requests.post(
            endpoint,
            headers=headers,
            json=post_data,
            timeout=30
        )

        if response.status_code == 200:
            logger.info(f"WordPress post {post_id} updated successfully")
            return response.json()
        else:
            logger.error(f"Failed to update post: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error updating WordPress post: {str(e)}")
        return None

def get_wordpress_posts(user_id: int, per_page: int = 10, page: int = 1) -> Optional[list]:
    """
    Get list of WordPress posts.

    Args:
        user_id: User ID
        per_page: Number of posts per page
        page: Page number

    Returns:
        List of post objects, or None if failed
    """
    base_url, username, app_password = get_wordpress_credentials(user_id)

    if not all([base_url, username, app_password]):
        logger.error(f"WordPress credentials not configured for user {user_id}")
        return None

    try:
        endpoint = construct_api_endpoint(base_url, 'posts')
        headers = create_auth_header(username, app_password)

        params = {
            'per_page': per_page,
            'page': page
        }

        response = requests.get(endpoint, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get posts: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error fetching WordPress posts: {str(e)}")
        return None

# Legacy function for backward compatibility
def load_user_env(user_id: int):
    """
    Legacy function - no longer needed with Application Passwords.
    Kept for backward compatibility.
    """
    pass

# Legacy function for backward compatibility
def get_jwt_token(user_id: int) -> Optional[str]:
    """
    Legacy function - JWT no longer used with Application Passwords.
    Kept for backward compatibility but returns None.
    """
    logger.warning("get_jwt_token() is deprecated - Application Passwords don't use JWT")
    return None
