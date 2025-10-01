import os
import requests
import json
from dotenv import load_dotenv
from openai_integration_v3 import create_blog_post_with_images_v3
from email_notification import send_email_notification

# Load environment variables from .env file
load_dotenv()

# Load environment variables
WORDPRESS_REST_API_URL = os.getenv("WORDPRESS_REST_API_URL")
WORDPRESS_USERNAME = os.getenv("WORDPRESS_USERNAME")
WORDPRESS_PASSWORD = os.getenv("WORDPRESS_PASSWORD")

# Debug prints to verify environment variables
print(f"WORDPRESS_REST_API_URL: {WORDPRESS_REST_API_URL}")
print(f"WORDPRESS_USERNAME: {WORDPRESS_USERNAME}")
print(f"WORDPRESS_PASSWORD: {'*' * len(WORDPRESS_PASSWORD)}")  # Mask password for security

def get_jwt_token():
    base_url = WORDPRESS_REST_API_URL.rstrip('/wp/v2/')
    auth_url = f"{base_url}/jwt-auth/v1/token"
    
    print(f"Auth URL: {auth_url}")  # Debug print
    auth_data = {
        "username": WORDPRESS_USERNAME,
        "password": WORDPRESS_PASSWORD
    }
    print(f"Attempting to get JWT token...")  # Debug print
    try:
        response = requests.post(auth_url, data=auth_data)
        response.raise_for_status()
        token = response.json()['token']
        print("JWT token obtained successfully")  # Debug print
        return token
    except requests.exceptions.RequestException as e:
        print(f"Error getting JWT token: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"Response content: {e.response.text}")
        return None

def download_image(image_url, image_path):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        with open(image_path, 'wb') as file:
            file.write(response.content)
        print(f"Image downloaded successfully: {image_path}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {str(e)}")

def create_media_id(image_path):
    token = get_jwt_token()
    if not token:
        return None

    media_url = f"{WORDPRESS_REST_API_URL.rstrip('/wp/v2/')}/wp/v2/media"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Disposition": f'attachment; filename="{os.path.basename(image_path)}"',
    }
    
    with open(image_path, 'rb') as image_file:
        files = {
            'file': image_file,
        }
        try:
            print(f"Uploading image to URL: {media_url}")
            response = requests.post(media_url, headers=headers, files=files)
            response.raise_for_status()
            media_id = response.json()['id']
            print(f"Image uploaded successfully. Media ID: {media_id}")
            return media_id
        except requests.exceptions.RequestException as e:
            print(f"Error creating media: {str(e)}")
            if hasattr(e, 'response') and e.response:
                print(f"Response content: {e.response.text}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {str(e)}")
            print(f"Response content: {response.text}")
            return None

def create_wordpress_post(post_data):
    token = get_jwt_token()
    if not token:
        return None

    posts_url = f"{WORDPRESS_REST_API_URL.rstrip('/wp/v2/')}/wp/v2/posts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        print(f"Creating WordPress post...")
        response = requests.post(posts_url, json=post_data, headers=headers)
        response.raise_for_status()
        print("WordPress post created successfully")
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error creating WordPress post: {str(e)}")
        if hasattr(e, 'response') and e.response:
            print(f"Response content: {e.response.text}")
        return None

def create_blog_post_for_user(user_id):
    print(f"Starting blog post creation for user: {user_id}")
    
    # Generate the blog post with image using OpenAI
    queries = os.getenv('USER_QUERY')
    system_prompt = os.getenv('SYSTEM_PROMPT')
    blog_post_idea = queries.split(',')[0] if queries else "Default blog post idea"

    print(f"Blog post idea: {blog_post_idea}")  # Debug print

    # V3 returns multiple images (hero + sections)
    processed_post, error = create_blog_post_with_images_v3(blog_post_idea, user_id, system_prompt)
    if error:
        print(f"Error creating blog post with images: {error}")
        return

    title = processed_post['title']
    content = processed_post['content']
    image_urls = processed_post['image_urls']  # V3 returns list of image URLs
    image_url = image_urls[0] if image_urls else None  # Use hero image

    # Download the generated image
    image_path = f"image_{user_id}.jpg"
    download_image(image_url, image_path)

    # Upload the image to WordPress and get the media ID
    media_id = create_media_id(image_path)
    if not media_id:
        print("Failed to upload image to WordPress")
        return

    # Create the WordPress post
    post_data = {
        "title": title,
        "content": f'<img src="{image_url}" alt="Post Image"/><p>{content}</p>',
        "status": "draft",  # Set to 'draft'
        "featured_media": media_id
    }

    response = create_wordpress_post(post_data)
    if response:
        post_id = response.json().get('id')
        print(f"WordPress post created successfully. Post ID: {post_id}")
        
        # Send email notification
        user_email = os.getenv('USER_EMAIL')  # Make sure to set this in your .env file
        wordpress_url = WORDPRESS_REST_API_URL.rstrip('/wp-json/wp/v2')
        email_sent = send_email_notification(
            post_id=post_id,
            title=title,
            content=content,
            img_url=image_url,
            user_email=user_email,
            wordpress_url=wordpress_url
        )
        if email_sent:
            print("Email notification sent successfully")
        else:
            print("Failed to send email notification")
        
        print("Blog post creation process completed successfully")
    else:
        print("Failed to create WordPress post")
        print("Blog post creation process failed")

    # Clean up the temporary image file
    if os.path.exists(image_path):
        os.remove(image_path)
        print(f"Temporary image file {image_path} removed")

# Example usage
if __name__ == '__main__':
    user_id = 'example_user_id'  # Replace with actual user ID in real usage
    create_blog_post_for_user(user_id)
