# Email Notifications with HTML Attachments

## Overview

Enhanced email notification system to send users their completed articles as HTML attachments for both WordPress and local mode. Users receive a professional email with the full article attached, enabling them to:

- Review articles offline
- Copy/paste to LinkedIn, Facebook, or other social platforms
- Share articles with team members
- Archive for portfolio/records
- Post to Medium or other CMSs while preserving formatting

## Features

✅ **HTML Attachments**: Full article with embedded images (8-10 MB for local mode)
✅ **Copy/Paste Ready**: HTML preserves all styling when copied to social media
✅ **Two Modes**: WordPress (with review link) and Local (downloadable only)
✅ **Professional Emails**: Branded templates with My Content Generator styling
✅ **Usage Instructions**: Step-by-step guide for LinkedIn/Facebook posting
✅ **Both Channels**: Sent for scheduled posts AND manual creation

## Implementation

### New Email Function

**File**: `email_notification.py`

```python
def send_article_notification_with_attachment(
    title,
    article_html,
    hero_image_url,
    user_email,
    mode="wordpress",
    wordpress_url=None,
    post_id=None
):
```

**Parameters**:
- `title`: Article title
- `article_html`: Complete HTML content with all styling and images
- `hero_image_url`: Hero image URL or base64 data URI
- `user_email`: Recipient email address
- `mode`: "wordpress" or "local"
- `wordpress_url`: WordPress site URL (WordPress mode only)
- `post_id`: WordPress post ID (WordPress mode only)

### Updated Files

1. **email_notification.py**:
   - Added `Attachment` import from SendGrid
   - Added `send_article_notification_with_attachment()` function
   - WordPress mode: Email with review link + HTML attachment
   - Local mode: Email with usage instructions + HTML attachment

2. **app_v3.py** (Manual Post Creation):
   - Updated `create_blog_post_v3()` to use new email function
   - Sends full article HTML as attachment
   - Mode: "wordpress"

3. **scheduler_v3.py** (Scheduled Posts):
   - Updated `create_blog_post()` to use new email function
   - Sends full article HTML as attachment
   - Mode: "wordpress"

## Email Templates

### WordPress Mode

**Subject**: ✅ Article Published: {title}

**Content**:
- Confirmation that article is saved as draft in WordPress
- File specs: Premium layout, 4-5 images, 1500-2500 words
- Usage options: Review in WordPress, download HTML, copy to social media
- "Review in WordPress →" button with direct link to post editor
- Pro Tip: How to open HTML and copy/paste to social media

**Attachment**: Complete article as {title}.html

### Local Mode

**Subject**: 📄 Your Article is Ready: {title}

**Content**:
- Confirmation that article is ready for download
- File specs: 8-10 MB, embedded images, premium Claude AI layout
- Usage guide:
  - LinkedIn Post: Open HTML, copy, paste (formatting preserved)
  - Facebook Post: Same process
  - Email Newsletter: Copy directly into email composer
  - Medium/Blog: Copy to CMS with styling
  - Portfolio: Open in browser for offline viewing
  - Team Sharing: Forward email or share HTML file
- Pro Tip with step-by-step instructions (Ctrl+A, Ctrl+C, Ctrl+V)

**Attachment**: Complete article as {title}.html

## HTML Attachment Format

The attached HTML file is **self-contained** and **copy/paste compatible**:

### For WordPress Mode
- External image URLs (WordPress media library)
- Smaller file size (~100 KB)
- Requires internet connection to view images
- All styling preserved

### For Local Mode
- Base64-embedded images
- Larger file size (8-10 MB)
- Works completely offline
- All styling and images preserved

### Copy/Paste Behavior

When users copy from the HTML file and paste into:

**✅ LinkedIn**: Formatting, images, and styling preserved
**✅ Facebook**: Formatting, images, and styling preserved
**✅ Gmail/Outlook**: Formatting and inline styling preserved
**✅ Medium**: Most formatting preserved (some CSS simplification)
**✅ WordPress**: Full formatting preserved

The HTML is designed with inline CSS to maximize compatibility across platforms.

## Notification Triggers

### 1. Manual Post Creation
**Trigger**: User clicks "Create Test Post" in dashboard
**Flow**:
```
User Request
  → Check Credits
  → Deduct Credits
  → Generate Article (V4 Pipeline)
  → Upload to WordPress
  → Send Email with Attachment ← NEW
  → Return Success Response
```

### 2. Scheduled Posts
**Trigger**: Scheduler runs (cron job every 5 minutes)
**Flow**:
```
Scheduler Check
  → Find Due Jobs
  → For Each User:
      → Generate Article (V4 Pipeline)
      → Upload to WordPress
      → Send Email with Attachment ← NEW
      → Mark Job Complete
```

## SendGrid Configuration

**Requirements**:
- SendGrid API key (EMAIL_PASSWORD in .env)
- Verified sender: joe@ezwai.com
- Attachment support enabled (default)

**Attachment Specs**:
- Format: text/html
- Encoding: base64
- Disposition: attachment
- Max size: 30 MB (SendGrid limit, our files are 8-10 MB)

## User Benefits

1. **Never Miss an Article**: Email arrives even if user closes browser
2. **Multi-Platform Distribution**: Easy to share on LinkedIn, Facebook, etc.
3. **Offline Access**: Can view/share article without internet (local mode)
4. **Professional Archiving**: Keep portfolio of generated articles
5. **Team Collaboration**: Forward email or share HTML file with colleagues
6. **Flexible Publishing**: Can publish to WordPress OR other platforms

## Technical Details

### Filename Generation

```python
# Sanitize title for filename
safe_filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
safe_filename = safe_filename[:50]  # Limit to 50 characters
safe_filename = f"{safe_filename}.html" if safe_filename else "article.html"
```

### Base64 Encoding

```python
# Encode article HTML for email attachment
article_bytes = article_html.encode('utf-8')
article_base64 = base64.b64encode(article_bytes).decode('utf-8')
```

### Error Handling

- Email send failures are logged but don't block article creation
- Users see warning: "Post created, but email notification failed to send"
- Article is still accessible via WordPress dashboard
- Full stack trace logged for debugging

## Testing

To test email notifications:

### Test WordPress Mode

```python
from email_notification import send_article_notification_with_attachment

send_article_notification_with_attachment(
    title="Test Article Title",
    article_html=article_html_content,  # Full HTML string
    hero_image_url="https://example.com/hero.jpg",
    user_email="test@example.com",
    mode="wordpress",
    wordpress_url="https://yoursite.com",
    post_id=123
)
```

### Test Local Mode

```python
send_article_notification_with_attachment(
    title="Test Article Title",
    article_html=article_html_content,  # Full HTML with base64 images
    hero_image_url="data:image/jpeg;base64,/9j/4AAQ...",
    user_email="test@example.com",
    mode="local"
)
```

## Future Enhancements

### Planned Features

1. **PDF Attachments**: Option to attach article as PDF in addition to HTML
2. **Preview Images**: Include hero image inline in email body
3. **Download Links**: Alternative to attachment for large files
4. **Scheduling Confirmation**: Send notification when scheduled post is queued
5. **Weekly Digest**: Summary of all articles created that week
6. **Social Media Integration**: Direct post to LinkedIn API from email

### Configuration Options

Future user settings in dashboard:
- Enable/disable email notifications
- Choose attachment format (HTML, PDF, both)
- Email frequency (immediate, daily digest, weekly)
- Include/exclude attachment
- Custom email template

## Cost Impact

**No Additional Cost**: SendGrid pricing based on email count, not attachment size
- Current plan supports attachments up to 30 MB
- Our typical attachments: 8-10 MB (local mode) or ~100 KB (WordPress mode)
- No change to existing SendGrid subscription needed

## Security Considerations

1. **Email Validation**: User emails validated during registration
2. **Attachment Safety**: HTML files are safe to open in browsers
3. **Content Sanitization**: Article HTML is generated by trusted AI pipeline
4. **No External Resources**: Local mode articles are fully self-contained
5. **WordPress Links**: Direct links include post ID but require WordPress login

## Troubleshooting

### Email Not Received

**Check**:
1. SendGrid API key is valid (EMAIL_PASSWORD in .env)
2. Sender email is verified: joe@ezwai.com
3. Recipient email is correct in user account
4. Check spam/junk folder
5. Review logs for SendGrid response code

### Attachment Too Large

**Issue**: SendGrid 30 MB limit
**Solution**:
- WordPress mode: Uses external images (~100 KB)
- Local mode: Base64 images (~8-10 MB, well under limit)

### Formatting Lost on Copy/Paste

**Issue**: Some platforms strip CSS
**Solution**:
- HTML uses inline styles for maximum compatibility
- Most major platforms (LinkedIn, Facebook, Gmail) preserve formatting
- If issues persist, user can publish WordPress version

## Documentation

**Updated Files**:
- `email_notification.py`: Core email functionality
- `app_v3.py`: Manual post creation integration
- `scheduler_v3.py`: Scheduled post integration
- `EMAIL_NOTIFICATIONS_IMPLEMENTATION.md`: This document

## Changelog

### v3.1 - Email Notifications with HTML Attachments

**Added**:
- `send_article_notification_with_attachment()` function
- WordPress mode email template
- Local mode email template
- HTML attachment generation
- Usage instructions for social media

**Updated**:
- `app_v3.py`: Manual post creation now sends enhanced email
- `scheduler_v3.py`: Scheduled posts now send enhanced email

**Benefits**:
- Users never miss completed articles
- Easy distribution to LinkedIn, Facebook, email
- Professional archiving and portfolio building
- Offline access to generated content
