# Article & Image Library Deployment Guide

## Quick Ubuntu Server Deployment

### 1. Pull Latest Code

```bash
cd /path/to/EZWAI_SMM
git pull origin main
```

### 2. Run Database Migration

```bash
python migrations/create_article_image_library.py
```

Expected output:
```
============================================================
Article & Image Library Migration
============================================================

Creating 'articles' table...
✓ 'articles' table created

Creating 'images' table...
✓ 'images' table created

Verifying tables...
✓ Both tables verified successfully

✅ Migration completed successfully!
```

### 3. Restart Application

```bash
# Stop current app
./stop_v3.sh

# Start with production settings
./start_v3_production.sh
```

### 4. Verify Features

1. **Login to Dashboard**
   - Navigate to `https://yourdomain.com`
   - Login with credentials

2. **Check Article Library Tab**
   - Click "📚 Article Library" tab
   - Should show "No articles found" initially
   - Create test article to populate

3. **Check Image Library Tab**
   - Click "🖼️ Image Library" tab
   - Should show "No images found" initially
   - Images appear after article generation

4. **Generate Test Article**
   - Go to "✨ Create Post" tab
   - Create article (will automatically save to database)
   - Return to Article Library - article should appear
   - Check Image Library - images should appear with prompts

## Features

### Article Library
- **Search:** Search articles by title
- **Filters:**
  - Status: published, draft, local, failed
  - Mode: WordPress, local
  - Sort: newest, oldest, by title
- **Actions:**
  - View article in new window
  - Link to WordPress post (if published)
- **Display:** Grid of cards with hero images, metadata, word count

### Image Library
- **Search:** Full-text search on image prompts
- **Filters:**
  - Type: hero images, section images
  - Sort: newest, oldest
- **Actions:**
  - Click image to view details in modal
  - View full prompt with all metadata
  - Download image
- **Display:** Grid of image cards with prompt previews

## Database Schema

### Articles Table
- `id` - Primary key
- `user_id` - Foreign key to user
- `title` - Article title (500 chars)
- `content_html` - Full HTML content (MEDIUMTEXT)
- `hero_image_url` - Hero image URL
- `section_images` - JSON array of section image URLs
- `word_count` - Article word count
- `status` - draft, published, local, failed
- `generation_mode` - wordpress, local
- `wordpress_post_id` - WordPress post ID (if published)
- `wordpress_url` - WordPress post URL
- `metadata` - JSON metadata (writing style, components, etc.)
- `backup_file_path` - Path to backup HTML file
- `created_at`, `updated_at` - Timestamps

### Images Table
- `id` - Primary key
- `user_id` - Foreign key to user
- `article_id` - Foreign key to article (nullable)
- `image_url` - Image URL (1000 chars)
- `image_type` - hero, section
- `prompt` - Full text prompt (FULLTEXT indexed for search)
- `model` - AI model used (default: seedream-4)
- `aspect_ratio` - Image aspect ratio
- `replicate_prediction_id` - Replicate API prediction ID
- `file_size_kb` - File size in KB
- `cost_usd` - Generation cost (default: $0.075)
- `tags` - JSON array of tags
- `created_at` - Timestamp

## API Endpoints

All endpoints require authentication.

### Article Endpoints

**GET /api/users/{user_id}/articles**
- List articles with filtering and pagination
- Query params: `status`, `mode`, `search`, `limit`, `offset`, `sort`
- Returns: `{ total, limit, offset, articles: [...] }`

**GET /api/users/{user_id}/articles/{article_id}**
- Get full article including HTML content
- Returns: Complete article object with all fields

### Image Endpoints

**GET /api/users/{user_id}/images**
- List images with filtering and pagination
- Query params: `type`, `article_id`, `search`, `limit`, `offset`, `sort`
- Returns: `{ total, limit, offset, images: [...] }`

**GET /api/users/{user_id}/images/{image_id}**
- Get full image details
- Returns: Complete image object with all fields

## Troubleshooting

### Migration Fails
```bash
# Check database connection
mysql -u $DB_USERNAME -p$DB_PASSWORD -h $DB_HOST

# Verify tables don't already exist
SHOW TABLES LIKE 'articles';
SHOW TABLES LIKE 'images';

# Check user permissions
SHOW GRANTS FOR 'your_user'@'localhost';
```

### API Returns 404
- Verify app restarted after migration
- Check logs: `tail -f logs/gunicorn.log`
- Verify routes registered: Check startup logs

### No Articles Showing
- Generate new test article (old articles won't be in database)
- Check browser console for API errors
- Verify user is logged in with correct user_id

### Images Not Searchable
- Full-text search requires MySQL/MariaDB
- SQLite doesn't support FULLTEXT indexes
- Verify `FULLTEXT idx_prompt` exists: `SHOW INDEX FROM images;`

## Storage Costs

**Per Article:**
- Database storage: ~100 KB (HTML + metadata)
- 4 images: ~400 KB (stored as URLs, not base64)
- Total: ~500 KB

**Cost Analysis:**
- 1000 articles = 500 MB = ~$0.025/month (AWS RDS)
- 6% of article generation cost ($0.54)
- Negligible compared to API costs

## Future Enhancements

**Planned:**
1. Edit article HTML in dashboard
2. Regenerate specific images
3. Export articles to various formats
4. Share articles via public link
5. Postiz integration for social media distribution
6. Image editing tools
7. Article analytics (views, engagement)
8. Bulk operations (delete multiple, export all)

## Support

**Issues:**
- Check CLAUDE.md for architecture details
- Review logs in `logs/` directory
- Verify all services running: MySQL, Gunicorn
- Test individual endpoints with curl

**Database Queries:**
```sql
-- Count articles per user
SELECT user_id, COUNT(*) FROM articles GROUP BY user_id;

-- Count images per article
SELECT article_id, COUNT(*) FROM images GROUP BY article_id;

-- Find images without articles (orphaned)
SELECT COUNT(*) FROM images WHERE article_id IS NULL;

-- Search images by prompt
SELECT * FROM images WHERE MATCH(prompt) AGAINST('photography' IN NATURAL LANGUAGE MODE);
```
