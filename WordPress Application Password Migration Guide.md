# WordPress Application Password Migration Guide

## Overview
This guide details the migration from JWT Authentication (username/password) to WordPress Application Passwords for simplified user setup.

**Benefits:**
- No WordPress plugin required (built into WP 5.6+)
- Simpler user setup (just URL + App Password)
- Auto-construct API endpoints in background
- More secure (revokable app-specific passwords)

---

## Step 1: Database Migration

### 1.1 Create Migration Script

**File:** `migrations/add_wordpress_app_password.py`

```python
"""
Migration: Add wordpress_app_password column and remove old JWT fields
Run: python migrations/add_wordpress_app_password.py
"""

import sys
import os
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config

def migrate():
    """Add wordpress_app_password column and remove JWT authentication fields"""
    
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    with engine.connect() as conn:
        print("Starting WordPress Application Password migration...")
        
        # Step 1: Add new column
        print("1. Adding wordpress_app_password column...")
        try:
            conn.execute(text("""
                ALTER TABLE user 
                ADD COLUMN wordpress_app_password VARCHAR(255) DEFAULT NULL
            """))
            conn.commit()
            print("   ✓ Column added successfully")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("   ⚠ Column already exists, skipping...")
            else:
                raise
        
        # Step 2: Migrate existing data (if users had JWT setup)
        # Note: Application passwords are different from regular passwords
        # Users will need to create new app passwords in WordPress
        print("2. Checking for users with existing WordPress credentials...")
        result = conn.execute(text("""
            SELECT id, email, wordpress_username 
            FROM user 
            WHERE wordpress_username IS NOT NULL 
            AND wordpress_username != ''
        """))
        users_to_migrate = result.fetchall()
        
        if users_to_migrate:
            print(f"   ⚠ Found {len(users_to_migrate)} users with WordPress credentials")
            print("   → These users will need to create Application Passwords")
            print("   → Their existing credentials will be cleared")
            
            # Log users who need to reconfigure
            with open('wordpress_migration_users.log', 'w') as f:
                f.write("Users who need to reconfigure WordPress:\n")
                f.write("=" * 60 + "\n")
                for user in users_to_migrate:
                    f.write(f"User ID: {user[0]}, Email: {user[1]}, Username: {user[2]}\n")
            
            print(f"   → List saved to: wordpress_migration_users.log")
        else:
            print("   ✓ No existing WordPress users found")
        
        # Step 3: Remove old columns
        print("3. Removing old JWT authentication columns...")
        try:
            conn.execute(text("ALTER TABLE user DROP COLUMN wordpress_username"))
            conn.commit()
            print("   ✓ wordpress_username column removed")
        except Exception as e:
            if "Can't DROP" in str(e):
                print("   ⚠ wordpress_username column already removed")
            else:
                raise
        
        try:
            conn.execute(text("ALTER TABLE user DROP COLUMN wordpress_password"))
            conn.commit()
            print("   ✓ wordpress_password column removed")
        except Exception as e:
            if "Can't DROP" in str(e):
                print("   ⚠ wordpress_password column already removed")
            else:
                raise
        
        print("\n" + "=" * 60)
        print("✓✓✓ Migration completed successfully!")
        print("=" * 60)
        
        if users_to_migrate:
            print("\nNEXT STEPS:")
            print("1. Email affected users about the change")
            print("2. Provide instructions for creating Application Passwords")
            print("3. Users will reconfigure in Settings tab")

if __name__ == '__main__':
    try:
        migrate()
    except Exception as e:
        print(f"\n✗ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

### 1.2 Run Migration

```bash
# Backup database first!
mysqldump -u username -p database_name > backup_before_wp_migration.sql

# Create migrations directory if it doesn't exist
mkdir -p migrations

# Run migration
python migrations/add_wordpress_app_password.py
```

---

## Step 2: Update User Model

### 2.1 Modify `config.py`

**Find the User model and update these fields:**

```python
# REMOVE these lines:
wordpress_username = db.Column(db.String(255))
wordpress_password = db.Column(db.String(255))

# ADD this line:
wordpress_app_password = db.Column(db.String(255))  # WordPress Application Password
```

**Complete updated User model fields related to WordPress:**

```python
class User(UserMixin, db.Model):
    # ... existing fields ...
    
    # WordPress Integration (Application Password method)
    wordpress_rest_api_url = db.Column(db.String(500))  # User enters: https://example.com
    wordpress_app_password = db.Column(db.String(255))  # Format: xxxx xxxx xxxx xxxx xxxx xxxx
    
    # ... rest of model ...
```

---

## Step 3: Update WordPress Integration Code

### 3.1 Modify `wordpress_integration.py`

**Replace the entire authentication section:**

```python
import os
import requests
import logging
from typing import Optional, Dict, Any
import base64
import json

logger = logging.getLogger(__name__)

def normalize_wordpress_url(url: str) -> str:
    """
    Normalize WordPress URL to base site URL.
    
    Examples:
        https://example.com → https://example.com
        https://example.com/ → https://example.com
        https://example.com/wp-json → https://example.com
        https://example.com/wp-json/wp/v2 → https://example.com
    
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

def get_wordpress_credentials(user_id: int) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Get WordPress credentials from user environment.
    
    Args:
        user_id: User ID
        
    Returns:
        Tuple of (base_url, username, app_password) or (None, None, None) if not configured
    """
    from config import User, db
    
    user = User.query.get(user_id)
    if not user:
        logger.error(f"User {user_id} not found")
        return None, None, None
    
    if not user.wordpress_rest_api_url or not user.wordpress_app_password:
        logger.error(f"User {user_id} has incomplete WordPress configuration")
        return None, None, None
    
    # Extract username from Application Password format
    # WordPress App Passwords include username in the format: username:app_password
    # But we need to get the username separately
    # IMPORTANT: We need to add a wordpress_username field or extract from email
    
    # For now, use email username as WordPress username (common pattern)
    username = user.email.split('@')[0]
    
    base_url = normalize_wordpress_url(user.wordpress_rest_api_url)
    app_password = user.wordpress_app_password.replace(' ', '')  # Remove spaces from app password
    
    return base_url, username, app_password

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

def test_wordpress_connection(user_id: int) -> tuple[bool, str]:
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

def create_wordpress_post(
    title: str,
    content: str,
    user_id: int,
    featured_image_url: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Create WordPress post using Application Password.
    
    Args:
        title: Post title
        content: Post content (HTML)
        user_id: User ID
        featured_image_url: Optional featured image URL (must be uploaded to WP media library first)
        
    Returns:
        Post object dict, or None if failed
    """
    base_url, username, app_password = get_wordpress_credentials(user_id)
    
    if not all([base_url, username, app_password]):
        logger.error(f"WordPress credentials not configured for user {user_id}")
        return None
    
    try:
        endpoint = construct_api_endpoint(base_url, 'posts')
        headers = create_auth_header(username, app_password)
        
        post_data = {
            'title': title,
            'content': content,
            'status': 'draft'  # Create as draft for user review
        }
        
        # Add featured image if provided
        if featured_image_url:
            # Note: featured_image_url should be a media ID, not URL
            # If you have the media ID, use it like this:
            # post_data['featured_media'] = media_id
            pass
        
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

def publish_wordpress_post(post_id: int, user_id: int) -> bool:
    """
    Change post status from draft to published.
    
    Args:
        post_id: WordPress post ID
        user_id: User ID
        
    Returns:
        True if successful, False otherwise
    """
    base_url, username, app_password = get_wordpress_credentials(user_id)
    
    if not all([base_url, username, app_password]):
        logger.error(f"WordPress credentials not configured for user {user_id}")
        return False
    
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
            return True
        else:
            logger.error(f"Failed to publish post: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error publishing post: {str(e)}")
        return False
```

---

## Step 4: Update Dashboard UI

### 4.1 Modify `static/dashboard.html` - Settings Tab

**Find the WordPress Integration section and replace with:**

```html
<!-- WordPress Integration Section -->
<div class="card">
    <div class="card-header">
        <h3>WordPress Integration</h3>
        <p class="help-text">Connect your WordPress site using an Application Password</p>
    </div>
    <div class="card-body">
        <div class="info-banner" style="margin-bottom: 20px;">
            <strong>ℹ️ What is an Application Password?</strong>
            <p>Application Passwords are built into WordPress 5.6+ and provide a secure way to connect apps without exposing your main password.</p>
            <button type="button" class="btn-secondary" onclick="showAppPasswordTutorial()">
                📺 Watch Tutorial (2 min)
            </button>
        </div>

        <form id="wordpressForm" onsubmit="saveWordPressSettings(event)">
            <div class="form-group">
                <label for="wordpressUrl">WordPress Site URL</label>
                <input 
                    type="url" 
                    id="wordpressUrl" 
                    class="form-control" 
                    placeholder="https://yoursite.com"
                    pattern="https?://.+"
                    title="Must start with http:// or https://"
                />
                <small class="help-text">Enter your main site URL (we'll handle the rest)</small>
            </div>

            <div class="form-group">
                <label for="wordpressAppPassword">Application Password</label>
                <div style="position: relative;">
                    <input 
                        type="password" 
                        id="wordpressAppPassword" 
                        class="form-control" 
                        placeholder="xxxx xxxx xxxx xxxx xxxx xxxx"
                        style="padding-right: 100px;"
                    />
                    <button 
                        type="button" 
                        class="btn-text" 
                        onclick="togglePasswordVisibility('wordpressAppPassword')"
                        style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%);"
                    >
                        👁️ Show
                    </button>
                </div>
                <small class="help-text">Create one in WordPress: Users → Profile → Application Passwords</small>
            </div>

            <div class="button-group">
                <button type="button" class="btn-secondary" onclick="testWordPressConnection()">
                    🔌 Test Connection
                </button>
                <button type="submit" class="btn-primary">
                    💾 Save Settings
                </button>
            </div>

            <div id="wordpressStatus" class="status-message" style="display: none;"></div>
        </form>
    </div>
</div>

<!-- Application Password Tutorial Modal -->
<div id="appPasswordModal" class="modal" style="display: none;">
    <div class="modal-content" style="max-width: 800px;">
        <span class="close" onclick="closeAppPasswordTutorial()">&times;</span>
        <h2>How to Create a WordPress Application Password</h2>
        
        <div class="tutorial-steps">
            <div class="step">
                <div class="step-number">1</div>
                <div class="step-content">
                    <h4>Log into your WordPress admin</h4>
                    <p>Go to <code>https://yoursite.com/wp-admin</code></p>
                </div>
            </div>

            <div class="step">
                <div class="step-number">2</div>
                <div class="step-content">
                    <h4>Navigate to Your Profile</h4>
                    <p>Click <strong>Users → Profile</strong> in the WordPress admin menu</p>
                </div>
            </div>

            <div class="step">
                <div class="step-number">3</div>
                <div class="step-content">
                    <h4>Scroll to Application Passwords</h4>
                    <p>Find the "Application Passwords" section at the bottom</p>
                </div>
            </div>

            <div class="step">
                <div class="step-number">4</div>
                <div class="step-content">
                    <h4>Create New Application Password</h4>
                    <p>Enter a name like "EZWAI Blog Generator" and click <strong>Add New Application Password</strong></p>
                </div>
            </div>

            <div class="step">
                <div class="step-number">5</div>
                <div class="step-content">
                    <h4>Copy the Password</h4>
                    <p><strong>⚠️ Important:</strong> Copy the generated password immediately - you won't see it again!</p>
                    <p>It will look like: <code>xxxx xxxx xxxx xxxx xxxx xxxx</code></p>
                </div>
            </div>

            <div class="step">
                <div class="step-number">6</div>
                <div class="step-content">
                    <h4>Paste into Settings</h4>
                    <p>Come back here and paste it into the Application Password field above</p>
                </div>
            </div>
        </div>

        <!-- Optional: Embed your video here -->
        <div style="margin-top: 30px; text-align: center;">
            <p><strong>Watch the full video tutorial:</strong></p>
            <!-- Replace with your actual video embed -->
            <iframe 
                width="100%" 
                height="400" 
                src="YOUR_VIDEO_URL_HERE" 
                frameborder="0" 
                allowfullscreen>
            </iframe>
        </div>
    </div>
</div>
```

### 4.2 Add JavaScript Functions

**Add to `static/dashboard.html` in the `<script>` section:**

```javascript
// Toggle password visibility
function togglePasswordVisibility(fieldId) {
    const field = document.getElementById(fieldId);
    const button = event.target;
    
    if (field.type === 'password') {
        field.type = 'text';
        button.textContent = '🙈 Hide';
    } else {
        field.type = 'password';
        button.textContent = '👁️ Show';
    }
}

// Show Application Password tutorial modal
function showAppPasswordTutorial() {
    document.getElementById('appPasswordModal').style.display = 'block';
}

// Close tutorial modal
function closeAppPasswordTutorial() {
    document.getElementById('appPasswordModal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('appPasswordModal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}

// Test WordPress connection
async function testWordPressConnection() {
    const url = document.getElementById('wordpressUrl').value;
    const appPassword = document.getElementById('wordpressAppPassword').value;
    const statusDiv = document.getElementById('wordpressStatus');

    if (!url || !appPassword) {
        showStatus(statusDiv, 'Please enter both WordPress URL and Application Password', 'error');
        return;
    }

    showStatus(statusDiv, 'Testing connection...', 'info');

    try {
        const response = await fetch(`/api/users/${currentUserId}/test_wordpress`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                wordpress_url: url,
                app_password: appPassword
            })
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(statusDiv, '✅ ' + data.message, 'success');
        } else {
            showStatus(statusDiv, '❌ ' + data.error, 'error');
        }
    } catch (error) {
        showStatus(statusDiv, '❌ Connection failed: ' + error.message, 'error');
    }
}

// Save WordPress settings
async function saveWordPressSettings(event) {
    event.preventDefault();
    
    const url = document.getElementById('wordpressUrl').value;
    const appPassword = document.getElementById('wordpressAppPassword').value;
    const statusDiv = document.getElementById('wordpressStatus');

    if (!url || !appPassword) {
        showStatus(statusDiv, 'Please fill in all fields', 'error');
        return;
    }

    showStatus(statusDiv, 'Saving...', 'info');

    try {
        const response = await fetch(`/api/users/${currentUserId}/integrations`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                wordpress_rest_api_url: url,
                wordpress_app_password: appPassword
            })
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(statusDiv, '✅ WordPress settings saved successfully!', 'success');
        } else {
            showStatus(statusDiv, '❌ ' + (data.error || 'Failed to save settings'), 'error');
        }
    } catch (error) {
        showStatus(statusDiv, '❌ Failed to save: ' + error.message, 'error');
    }
}

// Helper to show status messages
function showStatus(element, message, type) {
    element.textContent = message;
    element.className = `status-message ${type}`;
    element.style.display = 'block';
    
    if (type === 'success') {
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
}
```

### 4.3 Add CSS Styles

**Add to `static/dashboard.html` in the `<style>` section:**

```css
/* Tutorial Modal */
.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    overflow: auto;
    background-color: rgba(0,0,0,0.7);
}

.modal-content {
    background-color: #fff;
    margin: 5% auto;
    padding: 30px;
    border-radius: 12px;
    width: 90%;
    max-width: 700px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
}

.close {
    color: #aaa;
    float: right;
    font-size: 28px;
    font-weight: bold;
    cursor: pointer;
    line-height: 20px;
}

.close:hover,
.close:focus {
    color: #000;
}

.tutorial-steps {
    margin-top: 30px;
}

.step {
    display: flex;
    margin-bottom: 25px;
    align-items: flex-start;
}

.step-number {
    background: linear-gradient(135deg, #7c3aed, #6d28d9);
    color: white;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 18px;
    flex-shrink: 0;
    margin-right: 20px;
}

.step-content {
    flex: 1;
}

.step-content h4 {
    margin: 0 0 8px 0;
    color: #1f2937;
}

.step-content p {
    margin: 5px 0;
    color: #6b7280;
}

.step-content code {
    background: #f3f4f6;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 14px;
}

.info-banner {
    background: linear-gradient(135deg, #eff6ff, #dbeafe);
    border-left: 4px solid #3b82f6;
    padding: 15px;
    border-radius: 8px;
}

.info-banner strong {
    display: block;
    margin-bottom: 8px;
    color: #1e40af;
}

.info-banner p {
    margin: 8px 0;
    color: #1e3a8a;
}

.btn-text {
    background: none;
    border: none;
    color: #7c3aed;
    cursor: pointer;
    font-size: 14px;
    padding: 5px 10px;
}

.btn-text:hover {
    color: #6d28d9;
    text-decoration: underline;
}

.status-message {
    margin-top: 15px;
    padding: 12px;
    border-radius: 8px;
    font-weight: 500;
}

.status-message.success {
    background-color: #d1fae5;
    color: #065f46;
    border-left: 4px solid #10b981;
}

.status-message.error {
    background-color: #fee2e2;
    color: #991b1b;
    border-left: 4px solid #ef4444;
}

.status-message.info {
    background-color: #dbeafe;
    color: #1e40af;
    border-left: 4px solid #3b82f6;
}

.help-text {
    font-size: 13px;
    color: #6b7280;
    margin-top: 5px;
}

.button-group {
    display: flex;
    gap: 10px;
    margin-top: 20px;
}
```

---

## Step 5: Update API Endpoints

### 5.1 Add Test Connection Endpoint to `app_v3.py`

**Add this new route:**

```python
@app.route('/api/users/<int:user_id>/test_wordpress', methods=['POST'])
@login_required
def test_wordpress(user_id):
    """Test WordPress connection with Application Password"""
    if current_user.id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        data = request.get_json()
        wordpress_url = data.get('wordpress_url', '').strip()
        app_password = data.get('app_password', '').strip()
        
        if not wordpress_url or not app_password:
            return jsonify({"error": "WordPress URL and Application Password are required"}), 400
        
        # Temporarily set credentials for testing (don't save yet)
        from wordpress_integration import normalize_wordpress_url, construct_api_endpoint, create_auth_header
        import requests
        
        base_url = normalize_wordpress_url(wordpress_url)
        endpoint = construct_api_endpoint(base_url)
        
        # Use email username as WordPress username
        username = current_user.email.split('@')[0]
        headers = create_auth_header(username, app_password)
        
        # Test connection
        response = requests.get(endpoint, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return jsonify({"message": "Connection successful! Your WordPress site is ready."}), 200
        elif response.status_code == 401:
            return jsonify({"error": "Authentication failed. Please check your Application Password."}), 401
        else:
            return jsonify({"error": f"Connection failed with status code: {response.status_code}"}), 400
            
    except requests.exceptions.Timeout:
        return jsonify({"error": "Connection timeout. Please check your WordPress URL."}), 408
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Connection error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error testing WordPress connection: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500
```

### 5.2 Update Save Integrations Endpoint in `app_v3.py`

**Find the `/api/users/<int:user_id>/integrations` route and update:**

```python
@app.route('/api/users/<int:user_id>/integrations', methods=['POST'])
@login_required
def save_integrations(user_id):
    """Save user API credentials and integrations"""
    if current_user.id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        data = request.get_json()
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Update API credentials
        if 'openai_api_key' in data:
            user.openai_api_key = data['openai_api_key']
        if 'perplexity_api_token' in data:
            user.perplexity_api_token = data['perplexity_api_token']
        
        # Update WordPress credentials (NEW: Application Password method)
        if 'wordpress_rest_api_url' in data:
            user.wordpress_rest_api_url = data['wordpress_rest_api_url'].strip()
        if 'wordpress_app_password' in data:
            user.wordpress_app_password = data['wordpress_app_password'].strip()

        # Brand colors (if present)
        if 'brand_primary_color' in data:
            user.brand_primary_color = data['brand_primary_color']
        if 'brand_accent_color' in data:
            user.brand_accent_color = data['brand_accent_color']

        db.session.commit()

        # Generate user-specific .env file
        generate_env_file(user_id)

        logger.info(f"User {user_id} updated integrations successfully")
        return jsonify({"message": "Settings saved successfully!"}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving integrations for user {user_id}: {str(e)}")
        return jsonify({"error": "Failed to save settings"}), 500
```

---

## Step 6: Update Environment File Generation

### 6.1 Modify `app_v3.py` - `generate_env_file()` function

**Find and update this function:**

```python
def generate_env_file(user_id):
    """Generate user-specific .env file with their credentials"""
    user = User.query.get(user_id)
    if not user:
        logger.error(f"User {user_id} not found for env file generation")
        return

    env_file_path = f'.env.user_{user_id}'
    
    # Normalize WordPress URL
    wordpress_url = ''
    if user.wordpress_rest_api_url:
        from wordpress_integration import normalize_wordpress_url
        wordpress_url = normalize_wordpress_url(user.wordpress_rest_api_url)

    env_content = f"""# User-specific environment file for user {user_id}
# Generated automatically - do not edit manually

# OpenAI
OPENAI_API_KEY={user.openai_api_key or ''}

# Perplexity AI
PERPLEXITY_API_TOKEN={user.perplexity_api_token or ''}

# WordPress Integration (Application Password)
WORDPRESS_REST_API_URL={wordpress_url}
WORDPRESS_APP_PASSWORD={user.wordpress_app_password or ''}
WORDPRESS_USERNAME={user.email.split('@')[0]}

# User Info
USER_EMAIL={user.email}
USER_ID={user.id}

# Brand Colors
BRAND_PRIMARY_COLOR={user.brand_primary_color or '#7c3aed'}
BRAND_ACCENT_COLOR={user.brand_accent_color or '#f59e0b'}
"""

    try:
        with open(env_file_path, 'w') as f:
            f.write(env_content)
        logger.info(f"Generated env file for user {user_id}: {env_file_path}")
    except Exception as e:
        logger.error(f"Failed to generate env file for user {user_id}: {str(e)}")
```

---

## Step 7: Update Documentation

### 7.1 Update `CLAUDE.md`

**Find the WordPress Integration section and update:**

```markdown
### WordPress Integration
- **Authentication Method**: Application Passwords (WordPress 5.6+)
- **No Plugin Required**: Built-in WordPress feature
- **User Setup**: 
  1. Enter WordPress site URL (e.g., https://example.com)
  2. Create Application Password in WordPress admin
  3. Paste password into settings
- Images uploaded to WordPress media library before post creation
- Posts created as "draft" status for user review
- Email notification sent after successful post creation
```

### 7.2 Update User Documentation

**Create/Update:** `docs/WORDPRESS_SETUP_GUIDE.md`

```markdown
# WordPress Integration Setup Guide

## Quick Start (3 Steps)

### Step 1: Get Your WordPress URL
Your main website URL, for example:
- `https://yoursite.com`
- `https://blog.yourcompany.com`

**Don't include** `/wp-admin` or `/wp-json` - just the main URL.

### Step 2: Create Application Password in WordPress

1. Log into your WordPress admin: `https://yoursite.com/wp-admin`
2. Go to **Users → Profile** (or **Users → Your Profile**)
3. Scroll down to **"Application Passwords"** section
4. In the "New Application Password Name" field, enter: `EZWAI Blog Generator`
5. Click **"Add New Application Password"**
6. **Copy the generated password immediately** - you won't see it again!
   - It will look like: `xxxx xxxx xxxx xxxx xxxx xxxx`

### Step 3: Enter in EZWAI Settings

1. Go to Settings tab in EZWAI dashboard
2. Paste your WordPress URL
3. Paste your Application Password
4. Click "Test Connection" to verify
5. Click "Save Settings"

✅ Done! You're ready to publish articles to WordPress.

## Troubleshooting

### "Authentication failed"
- Double-check you copied the entire Application Password (with or without spaces is fine)
- Verify you're using the correct WordPress URL
- Make sure your WordPress is version 5.6 or higher

### "Connection timeout"
- Verify your WordPress site is online and accessible
- Check that your WordPress REST API is enabled
- Try accessing `https://yoursite.com/wp-json` in your browser - you should see JSON data

### "Application Passwords not showing in WordPress"
- Update WordPress to version 5.6 or higher
- Check if a security plugin is blocking the REST API
- Ensure you're logged in as an administrator

## Security Notes

- Application Passwords are separate from your main WordPress password
- You can revoke an Application Password anytime without affecting your main login
- Each app gets its own password for better security
- If compromised, simply delete that Application Password in WordPress

## Need Help?

- Watch the tutorial video in the EZWAI Settings tab
- Check WordPress documentation: https://wordpress.org/support/article/application-passwords/
- Contact support: support@ezwai.com
```

---

## Step 8: Testing Checklist

### 8.1 Manual Testing Steps

```bash
# 1. Test migration
python migrations/add_wordpress_app_password.py

# 2. Start application
./start_v3.sh  # or start_v3.bat on Windows

# 3. Test in browser
```

**Browser Tests:**
1. ✅ Login to dashboard
2. ✅ Go to Settings tab
3. ✅ See new WordPress fields (URL + App Password)
4. ✅ Click "Watch Tutorial" button - modal opens
5. ✅ Enter WordPress URL: `https://testsite.com`
6. ✅ Enter Application Password (get from real WordPress site)
7. ✅ Click "Test Connection" - should see success/error message
8. ✅ Click "Save Settings" - should save successfully
9. ✅ Create test article - should post to WordPress as draft
10. ✅ Check email notification received

### 8.2 WordPress Side Testing

1. ✅ Log into WordPress admin
2. ✅ Go to Users → Profile
3. ✅ Find "Application Passwords" section
4. ✅ Create new password named "EZWAI Test"
5. ✅ Copy password
6. ✅ Use in EZWAI dashboard
7. ✅ Verify post appears in WordPress drafts
8. ✅ Check images uploaded to Media Library
9. ✅ Revoke Application Password in WordPress
10. ✅ Verify connection fails in EZWAI (expected)

---

## Step 9: Email Existing Users (Optional)

### 9.1 User Migration Email Template

```html
Subject: 🔄 WordPress Integration Update - Action Required

Hi [Name],

We've upgraded our WordPress integration to make setup even easier!

**What's Changed:**
We now use WordPress Application Passwords instead of regular passwords. This is:
- ✅ More secure (separate from your main WP password)
- ✅ Easier to set up (no plugin required)
- ✅ Simpler to manage (revoke anytime)

**Action Required:**
Please update your WordPress connection in Settings:
1. Log into your EZWAI dashboard
2. Go to Settings → WordPress Integration
3. Follow the 3-step guide (takes 2 minutes)
4. Watch our tutorial video if you need help

**Why This Change?**
Application Passwords are built into WordPress 5.6+ and provide better security.
Your current setup will stop working on [date], so please update soon!

Questions? Hit reply or watch the tutorial in your dashboard.

Thanks,
EZWAI Team
```

---

## Step 10: Rollback Plan (If Needed)

### 10.1 Database Rollback

```sql
-- If you need to rollback the migration

-- 1. Restore old columns
ALTER TABLE user ADD COLUMN wordpress_username VARCHAR(255);
ALTER TABLE user ADD COLUMN wordpress_password VARCHAR(255);

-- 2. Remove new column
ALTER TABLE user DROP COLUMN wordpress_app_password;

-- 3. Restore from backup if needed
-- mysql -u username -p database_name < backup_before_wp_migration.sql
```

### 10.2 Code Rollback

```bash
# Revert to previous version using git
git log --oneline  # Find commit before changes
git revert [commit-hash]

# Or checkout specific files
git checkout [previous-commit] -- wordpress_integration.py config.py
```

---

## Summary

**Files Modified:**
1. ✅ `migrations/add_wordpress_app_password.py` (NEW)
2. ✅ `config.py` - User model
3. ✅ `wordpress_integration.py` - Complete rewrite
4. ✅ `static/dashboard.html` - Settings UI
5. ✅ `app_v3.py` - API endpoints + env generation
6. ✅ `CLAUDE.md` - Documentation
7. ✅ `docs/WORDPRESS_SETUP_GUIDE.md` (NEW)

**Benefits Achieved:**
- ✅ Simpler user setup (no plugin required)
- ✅ More secure (revocable app-specific passwords)
- ✅ Auto-construct API endpoints
- ✅ Better UX with tutorial modal
- ✅ Cleaner codebase

**Estimated Implementation Time:** 3-4 hours

**Risk Level:** Low (can rollback easily)