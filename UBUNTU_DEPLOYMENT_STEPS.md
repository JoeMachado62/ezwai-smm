# Ubuntu Server Deployment - Article & Image Library

## What Was Implemented

✅ **Complete Article & Image Library System**
- Database models for articles and images
- Automatic saving during article generation
- REST API endpoints for retrieval
- Dashboard UI with search and filters
- Image prompt search capability

## Deployment Steps on Ubuntu Server

### Step 1: Pull Latest Code

```bash
# SSH into Ubuntu server
ssh user@your-server-ip

# Navigate to project directory
cd /path/to/EZWAI_SMM

# Pull latest changes
git pull origin main
```

You should see:
```
remote: Enumerating objects: XX, done.
remote: Counting objects: 100% (XX/XX), done.
remote: Compressing objects: 100% (XX/XX), done.
Unpacking objects: 100% (XX/XX), done.
From https://github.com/JoeMachado62/ezwai-smm
   34ef0a9..9ca3f2f  main       -> origin/main
Updating 34ef0a9..9ca3f2f
```

### Step 2: Run Database Migration

```bash
# Make sure you're in the project root
pwd
# Should show: /path/to/EZWAI_SMM

# Run migration
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

============================================================
Articles Table Structure:
============================================================
  id                        int                            NO
  user_id                   int                            NO
  title                     varchar(500)                   NO
  content_html              mediumtext                     NO
  hero_image_url            varchar(1000)                  YES
  section_images            json                           YES
  word_count                int                            YES
  status                    enum(...)                      YES
  generation_mode           enum(...)                      YES
  wordpress_post_id         int                            YES
  wordpress_url             varchar(1000)                  YES
  metadata                  json                           YES
  backup_file_path          varchar(500)                   YES
  created_at                timestamp                      NO
  updated_at                timestamp                      NO

============================================================
Images Table Structure:
============================================================
  id                        int                            NO
  user_id                   int                            NO
  article_id                int                            YES
  image_url                 varchar(1000)                  NO
  image_type                enum('hero','section')         YES
  prompt                    text                           NO
  model                     varchar(100)                   YES
  aspect_ratio              varchar(20)                    YES
  replicate_prediction_id   varchar(100)                   YES
  file_size_kb              int                            YES
  cost_usd                  decimal(10,4)                  YES
  tags                      json                           YES
  created_at                timestamp                      NO

✅ Migration completed successfully!
```

### Step 3: Restart Application

```bash
# Stop current application
./stop_v3.sh

# Start production server with Gunicorn
./start_v3_production.sh
```

Expected output:
```
Stopping EZWAI SMM application...
Stopping Gunicorn (PID: XXXXX)...
Application stopped successfully.

Starting EZWAI SMM in production mode...
Starting Gunicorn with 4 workers...
Gunicorn started with PID: XXXXX
Application running on http://0.0.0.0:5000
Logs: logs/gunicorn.log
```

### Step 4: Verify Deployment

1. **Check Logs**
```bash
tail -f logs/gunicorn.log
```

Look for startup messages without errors.

2. **Test Database Connection**
```bash
mysql -u $DB_USERNAME -p$DB_PASSWORD -e "SHOW TABLES LIKE 'articles';"
mysql -u $DB_USERNAME -p$DB_PASSWORD -e "SHOW TABLES LIKE 'images';"
```

Should show both tables exist.

3. **Test API Endpoints (from local machine)**
```bash
# Replace with your server URL and user ID
curl -X GET "https://yourdomain.com/api/users/1/articles?limit=10" \
  -H "Cookie: session=your-session-cookie"
```

Expected response:
```json
{
  "total": 0,
  "limit": 10,
  "offset": 0,
  "articles": []
}
```

### Step 5: Test in Browser

1. Navigate to your domain: `https://yourdomain.com`
2. Login with your credentials
3. **Check new tabs:**
   - Click "📚 Article Library" - Should show "No articles found"
   - Click "🖼️ Image Library" - Should show "No images found"

4. **Generate test article:**
   - Go to "✨ Create Post" tab
   - Enter topic: "Test article for library feature"
   - Click "Generate Article"
   - Wait for completion

5. **Verify article appears:**
   - Go back to "📚 Article Library"
   - Should see your test article with hero image
   - Click "👁️ View" to open article in new window

6. **Verify images appear:**
   - Go to "🖼️ Image Library"
   - Should see 4 images (1 hero + 3 section)
   - Click any image to view details with prompt
   - Test search: type keywords from prompts

## Features to Test

### Article Library
- ✅ Search by title
- ✅ Filter by status (published, draft, local, failed)
- ✅ Filter by mode (WordPress, local)
- ✅ Sort (newest, oldest, by title)
- ✅ View article HTML in new window
- ✅ Link to WordPress (if published)
- ✅ Pagination (when > 12 articles)

### Image Library
- ✅ Search prompts (full-text search)
- ✅ Filter by type (hero, section)
- ✅ Sort (newest, oldest)
- ✅ View image details in modal
- ✅ Download image
- ✅ See full prompt and metadata
- ✅ Pagination (when > 24 images)

## Troubleshooting

### Issue: Migration fails with "user table not found"

**Solution:** Run user table migration first:
```bash
python migrations/add_wordpress_app_password.py
```

### Issue: API returns 404

**Check:**
1. Application restarted? `ps aux | grep gunicorn`
2. Logs show errors? `tail -f logs/gunicorn.log`
3. Routes registered? Check startup logs

### Issue: Articles/Images not showing

**Possible causes:**
1. Old articles won't appear (generated before database feature)
2. Generate new test article to populate database
3. Check browser console for API errors (F12)
4. Verify user is logged in

### Issue: Image search not working

**Check FULLTEXT index:**
```bash
mysql -u $DB_USERNAME -p$DB_PASSWORD -e "SHOW INDEX FROM images WHERE Key_name='idx_prompt';"
```

Should show FULLTEXT index exists.

### Issue: Permission denied

**Fix permissions:**
```bash
chmod +x stop_v3.sh start_v3_production.sh
chown -R $USER:$USER /path/to/EZWAI_SMM
```

## Database Verification Queries

```bash
# Connect to database
mysql -u $DB_USERNAME -p$DB_PASSWORD $DB_NAME

# Count articles
SELECT COUNT(*) as total_articles FROM articles;

# Count images
SELECT COUNT(*) as total_images FROM images;

# Articles per user
SELECT user_id, COUNT(*) as article_count
FROM articles
GROUP BY user_id;

# Images per article
SELECT article_id, COUNT(*) as image_count
FROM images
WHERE article_id IS NOT NULL
GROUP BY article_id;

# Recent articles
SELECT id, title, status, created_at
FROM articles
ORDER BY created_at DESC
LIMIT 5;

# Search images by prompt
SELECT id, image_type, LEFT(prompt, 50) as prompt_preview
FROM images
WHERE MATCH(prompt) AGAINST('photography' IN NATURAL LANGUAGE MODE)
LIMIT 5;
```

## Success Criteria

✅ Migration completes without errors
✅ Application restarts successfully
✅ Article Library tab shows in dashboard
✅ Image Library tab shows in dashboard
✅ Test article generation saves to database
✅ Articles appear in Article Library
✅ Images appear in Image Library with searchable prompts
✅ Existing functionality remains unchanged

## Next Steps After Deployment

1. **Monitor Storage:**
   - Check database size growth
   - Plan backup strategy

2. **User Testing:**
   - Generate several articles
   - Test search functionality
   - Verify WordPress integration still works

3. **Optional Cleanup:**
   - Review CLEANUP_AUDIT_2025.md
   - Remove old test scripts (don't delete backups/)
   - Organize legacy documentation

4. **Future Enhancements:**
   - Article editing in dashboard
   - Image regeneration
   - Postiz integration for social media
   - Analytics dashboard

## Documentation

- **Architecture:** See CLAUDE.md
- **Detailed Guide:** See ARTICLE_LIBRARY_DEPLOYMENT.md
- **API Docs:** Included in deployment guide
- **Troubleshooting:** Both documents have troubleshooting sections

## Support

If issues arise:
1. Check logs: `tail -f logs/gunicorn.log`
2. Verify database: Run verification queries above
3. Test API: Use curl commands above
4. Review error messages in browser console (F12)
