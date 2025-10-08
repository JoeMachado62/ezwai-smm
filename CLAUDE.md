# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EZWAI SMM is an automated social media management system that generates and publishes professional magazine-style blog posts to WordPress. The system uses multiple AI services to create comprehensive 1500-2500 word articles with photorealistic images and professional HTML formatting.

## Version 3.0 (Current - 2025)

**State-of-the-Art AI Integration:**
- **GPT-5-mini with Responses API** - Latest reasoning model with "medium effort" setting
- **SeeDream-4 Image Model** - 2K resolution photorealistic images with text rendering
- **Claude Sonnet 4.5 Formatter** - AI-powered magazine layout with intelligent design decisions
- **AI-Powered Photographic Prompts** - Guarantees professional photography (not illustrations)
- **Magazine-Quality Articles** - 1500-2500 words with structured HTML formatting
- **Modern Gradient UI** - Purple/violet themed dashboard with real-time progress tracking

## Current Architecture State

### ⚠️ V3/V4 Hybrid State (Temporary)

**Current Reality:**
The codebase currently uses BOTH `openai_integration_v3.py` and `openai_integration_v4.py`:

- **app_v3.py** imports `openai_integration_v4.py`
- **scheduler_v3.py** imports `openai_integration_v3.py`

**Why Both Exist:**
- V4 is a **modular refactor** of V3 with identical features
- V4 has cleaner code structure, better separation of concerns
- V3 still used by scheduler (not yet migrated)

**Feature Parity:**
Both V3 and V4 provide:
- GPT-5-mini with Responses API
- SeeDream-4 2K image generation
- AI-powered photographic prompts
- 1500-2500 word magazine articles

**Recommendation:** See "Recommended Refactoring" section below for migration path to standardize on V4.

## Architecture

### Core Flow (V3/V4 Hybrid)
1. **Scheduler** (`scheduler_v3.py`) - Runs periodically, triggers blog posts using `openai_integration_v3.py`
2. **Query Management** (`perplexity_ai_integration.py`) - Rotates through user-defined topic queries
3. **Content Generation** - Either:
   - `openai_integration_v3.py` (scheduler path)
   - `openai_integration_v4.py` (manual post creation via app)
4. **Image Generation** - Both V3/V4 use SeeDream-4 for 4 images (1 hero 16:9 + 3 section 4:3)
5. **Magazine Formatting** - Two options:
   - `claude_formatter.py` (NEW: AI-powered layout)
   - `magazine_formatter.py` (Legacy: template-based)
6. **Publishing** (`wordpress_integration.py`) - Posts to WordPress via REST API with JWT auth
7. **Notification** (`email_notification.py`) - SendGrid email notifications

### Key Files

**V3 Core Application:**
- `app_v3.py` - Main Flask application (imports V4)
- `scheduler_v3.py` - Scheduler (imports V3)
- `static/dashboard.html` - Modern gradient UI

**Content Generation (Hybrid):**
- `openai_integration_v3.py` - Used by scheduler
- `openai_integration_v4.py` - Used by app, modular refactor of V3
- `image_prompt_generator.py` - Contextual image prompt generation

**Formatting (Choose One):**
- `claude_formatter.py` - **NEW:** AI-powered magazine layout
- `magazine_formatter.py` - Template-based formatting (fallback)

**Shared Modules:**
- `config.py` - Database configuration
- `perplexity_ai_integration.py` - Topic research with Perplexity AI
- `wordpress_integration.py` - WordPress REST API with JWT auth
- `email_notification.py` - SendGrid email notifications

**Startup Scripts (Windows):**
- `start_v3.bat` - Full startup with dependency/service checks
- `start_v3_background.bat` - Background mode with auto-restart
- `stop_v3.bat` - Graceful shutdown

**Startup Scripts (Linux/Production):**
- `start_v3.sh` - Full startup with service verification
- `start_v3_production.sh` - Gunicorn production server (4 workers)
- `stop_v3.sh` - Graceful shutdown
- `run_scheduler_v3.sh` - Cron-compatible scheduler runner

### Multi-User Architecture
- Each user has their own `.env.user_{user_id}` file generated dynamically with their API credentials
- User data (credentials, queries, schedules) stored in MySQL database
- Users can configure up to 10 specific topic queries that rotate for each post
- Users can schedule up to 2 posts per day across the week
- **NEW:** Users can store brand colors (primary/accent) for consistent article styling

### Database Models
- **User** - Stores user credentials, API keys, queries, system prompts, schedules (JSON fields), and brand colors
- **CompletedJob** - Tracks scheduled blog posts with unique constraint on (user_id, scheduled_time) to prevent duplicates

## Environment Setup

### Required Environment Variables (.env)
```bash
# Database
DB_USERNAME=<mysql_username>
DB_PASSWORD=<mysql_password>
DB_HOST=<mysql_host>
DB_NAME=<database_name>

# Flask
FLASK_SECRET_KEY=<secret_key>
FLASK_DEBUG=<True|False>

# Email (SendGrid)
EMAIL_HOST=<smtp_host>
EMAIL_PORT=<port>
EMAIL_USERNAME=<sendgrid_username>
EMAIL_PASSWORD=<sendgrid_api_key>

# Replicate (SeeDream-4 image generation)
REPLICATE_API_TOKEN=<replicate_token>

# Anthropic (Claude Formatter) - NEW
ANTHROPIC_API_KEY=<anthropic_api_key>
```

### Per-User Environment Variables (.env.user_{user_id})
Generated dynamically via `generate_env_file()`:
```bash
OPENAI_API_KEY="sk-..."
WORDPRESS_REST_API_URL="https://example.com/wp-json/wp/v2"
WORDPRESS_USERNAME="username"
WORDPRESS_PASSWORD="password"
PERPLEXITY_AI_API_TOKEN="pplx-..."
ANTHROPIC_API_KEY="sk-ant-..."  # Can also be per-user
```

## Development Commands

### Windows

#### Start Application (Development)
```bash
start_v3.bat
```
- Checks Python and dependencies
- Verifies MySQL service is running (auto-starts if needed)
- Tests database connection
- Runs on `http://localhost:5000`

#### Start Application (Background with Auto-Restart)
```bash
start_v3_background.bat
```
- Runs in background
- Automatically restarts on crashes
- Logs to `logs/app_v3_YYYYMMDD_HHMMSS.log`

#### Stop Application
```bash
stop_v3.bat
```

### Linux/Production

#### Start Application (Development)
```bash
./start_v3.sh
```
- Full service checks (Python, MySQL, dependencies)
- Activates virtual environment
- Tests database connection
- Runs on `http://0.0.0.0:5000`

#### Start Application (Production - Gunicorn)
```bash
./start_v3_production.sh
```
- 4 worker processes
- Daemon mode
- Auto-restart (max 1000 requests per worker)
- Comprehensive logging (logs/gunicorn.log)
- PID file: `gunicorn.pid`

#### Stop Application
```bash
./stop_v3.sh
```
- Graceful shutdown with fallback force-kill

#### Scheduler (Cron)
```bash
# Run manually
./run_scheduler_v3.sh

# Setup cron (every 5 minutes)
crontab -e
# Add: */5 * * * * cd /path/to/EZWAI_SMM && ./run_scheduler_v3.sh
```

### Install/Update Dependencies
```bash
pip install -r requirements.txt
```

### Database Setup
```bash
# Initialize database (first time only)
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## API Endpoints

### Authentication
- `POST /register` - Create new user account
- `POST /login` - User login (returns JWT token)

### User Management
- `GET /api/users/<user_id>` - Get user profile
- `PUT /api/users/<user_id>` - Update user profile
- `DELETE /api/users/<user_id>` - Delete user account

### Integration Configuration
- `POST /api/users/<user_id>/integrations` - Save OpenAI, WordPress, Perplexity, Anthropic credentials
- `GET /api/users/<user_id>/integrations` - Get saved integrations

### Blog Post Creation
- `POST /api/users/<user_id>/create_test_post` - Create immediate test post with V3/V4 features
- `POST /api/users/<user_id>/schedule` - Schedule automated posts

### System
- `GET /api/users/<user_id>/progress` - Server-sent events for progress tracking

## Key Features

### Claude Formatter Integration (NEW)

**AI-Powered Magazine Layout:**
- Uses Claude Sonnet 4.5 API for intelligent formatting decisions
- Replaces rigid `magazine_formatter.py` template system
- Automatically extracts pull quotes from content
- Intelligently places stats and highlights
- Adapts layout based on content density and flow
- Maintains visual rhythm and professional pacing

**Integration in Pipeline:**
```python
from claude_formatter import format_article_with_claude

# After generating article content and images
formatted_html = format_article_with_claude(
    article_html=article_data['html'],
    title=article_data['title'],
    hero_image_url=hero_url,
    section_images=[img['url'] for img in section_image_urls],
    user_id=user_id,
    brand_colors={"primary": "#4a9d5f", "accent": "#8b7355"},
    layout_style="premium_magazine"
)
```

**Migration from magazine_formatter.py:**

OLD CODE (Template-Based):
```python
from magazine_formatter import apply_magazine_styling

formatted_html = apply_magazine_styling(
    article_data=article_data,  # Full dict with components
    hero_image_url=hero_url,
    section_images=section_image_list,  # List of dicts
    user_id=user_id,
    brand_colors={"primary": "#08b2c6", "accent": "#ff6b11"}
)
```

NEW CODE (AI-Powered):
```python
from claude_formatter import format_article_with_claude

formatted_html = format_article_with_claude(
    article_html=article_data['html'],  # HTML string only
    title=article_data['title'],  # Title separate
    hero_image_url=hero_url,
    section_images=[img['url'] for img in section_image_list],  # List of URLs
    user_id=user_id,
    brand_colors={"primary": "#08b2c6", "accent": "#ff6b11"},
    layout_style="premium_magazine"  # NEW parameter
)
```

**Key Changes:**
- Pass `article_html` string instead of `article_data` dict
- Pass `title` separately
- Convert section_images from list of dicts to list of URLs
- Add `layout_style` parameter (for future multi-layout support)
- Claude makes all component placement decisions automatically

**Fallback Strategy:**
- Keep `magazine_formatter.py` in codebase as backup
- If Claude API fails, can fallback to template formatter
- Log formatting method used for monitoring

**Key Advantages:**
- **Intelligent Layout:** AI understands content and makes smart placement decisions
- **Better Visual Rhythm:** Knows when text is getting too dense and adds breaks
- **Contextual Pull Quotes:** Extracts the most impactful quotes automatically
- **Adaptive Stats:** Finds and highlights key metrics from content
- **Professional Quality:** Matches or exceeds manual formatting

**Cost per Article:** ~$0.09 (Claude Sonnet 4.5 API call)

### V3 Content Generation (openai_integration_v3.py)

**GPT-5-mini with Reasoning:**
```python
response = client.responses.create(
    model="gpt-5-mini",
    input=enhanced_prompt,
    reasoning={"effort": "medium"},  # Generates 150-300 reasoning tokens
    modalities=["text"],
    instructions="You are an expert magazine writer..."
)
```

**AI-Powered Photographic Prompts:**
- GPT-5-mini generates prompts WITH camera/lighting specifications
- Enforces photorealistic requirements (no illustrations/animations)
- Section-aware and contextually relevant to article content
- Guarantees professional photography style

**SeeDream-4 Image Generation:**
- 2K resolution (2048px)
- Text rendering capability
- Better prompt adherence than Flux-dev
- Hero image: 16:9 aspect ratio
- Section images: 4:3 aspect ratio

**Magazine-Style HTML Structure:**
- Hero image with overlay title
- Pull quotes with brand color borders
- Stat highlights with brand color backgrounds
- Case study sections with accent color highlights
- Professional typography (Playfair Display + Roboto)
- Responsive design
- **NEW:** AI-optimized layout via Claude Formatter

### V4 Content Generation (openai_integration_v4.py)

**Modular Architecture:**
V4 is a refactored version of V3 with identical features but cleaner code organization:

```python
from openai_integration_v4 import create_blog_post_with_images_v4

# Same signature as V3
processed_post, error = create_blog_post_with_images_v4(
    blog_post_idea,
    user_id,
    system_prompt
)
```

**Key Improvements over V3:**
- Better separation of concerns
- More modular function structure
- Easier to test and maintain
- Identical output quality to V3

**Feature Parity with V3:**
- GPT-5-mini Responses API with reasoning
- SeeDream-4 2K image generation
- AI-powered photographic prompts
- Magazine-style HTML output

### Cost & Performance

**V3/V4 with Claude Formatter (Current):**
- Cost per article: ~$0.54
  - GPT-5-mini: ~$0.15
  - SeeDream-4 (4 images): ~$0.30
  - Claude Formatter: ~$0.09
- Generation time: 3-5 minutes
- Article length: 1500-2500 words
- Images: 4 photorealistic 2K images
- Quality: State-of-the-art with AI formatting

**V3/V4 with Template Formatter (Previous):**
- Cost per article: ~$0.45
- Generation time: 3-4 minutes
- Quality: Good but rigid layout

**V2.0 (Deprecated):**
- Cost per article: ~$0.35
- Generation time: 2-3 minutes
- Article length: 1500-2000 words
- Images: 4 Flux-dev 1792px images
- Quality: Good magazine-style

**V1.0 (Legacy):**
- Cost per article: ~$0.10
- Generation time: 30-60 seconds
- Article length: 300-500 words
- Images: 1 DALL-E 3 image
- Quality: Basic blog post

## Important Implementation Details

### Claude Formatter Usage

**When to Use:**
- For production articles requiring professional magazine layout
- When AI-powered component placement is desired
- When content density requires intelligent visual breaks

**When to Use Template Formatter:**
- As fallback if Claude API fails
- For testing without incurring Claude API costs
- For simpler layouts that don't require AI decisions

**Implementation Example:**
```python
from claude_formatter import format_article_with_claude
from magazine_formatter import apply_magazine_styling

# Try Claude formatter first
formatted_html = format_article_with_claude(
    article_html=article_data['html'],
    title=article_data['title'],
    hero_image_url=hero_url,
    section_images=[img['url'] for img in section_image_list],
    user_id=user_id,
    brand_colors={"primary": "#08b2c6", "accent": "#ff6b11"}
)

# Fallback to template if Claude fails
if not formatted_html:
    logger.warning("Claude formatter failed, using template fallback")
    formatted_html = apply_magazine_styling(
        article_data=article_data,
        hero_image_url=hero_url,
        section_images=section_image_list,
        user_id=user_id,
        brand_colors={"primary": "#08b2c6", "accent": "#ff6b11"}
    )
```

### V3 vs V4 Usage

**Current State:**
- **scheduler_v3.py** uses `openai_integration_v3.py`
- **app_v3.py** imports `openai_integration_v4.py`

**Signature Compatibility:**
Both V3 and V4 have identical function signatures:
```python
processed_post, error = create_blog_post_with_images_v3(
    blog_post_idea, user_id, system_prompt
)

processed_post, error = create_blog_post_with_images_v4(
    blog_post_idea, user_id, system_prompt
)
```

**Return Format (Identical):**
```python
processed_post = {
    'title': str,
    'content': str,  # Full HTML
    'all_images': [hero_url, section1_url, section2_url, section3_url],
    'hero_image_url': str
}
```

### Per-User Configuration
- API credentials stored in database User model
- `generate_env_file()` creates `.env.user_{user_id}` files on login
- Each blog post creation loads user-specific environment
- Brand colors stored in User model and passed to formatter

### Query Rotation System
- Prevents topic duplication by rotating through user's query list
- `last_query_index` tracks current position in query list
- Automatically cycles to next query on each post creation

### Scheduler Duplicate Prevention
- CompletedJob table has unique constraint on (user_id, scheduled_time)
- Ensures scheduled posts run exactly once
- Critical for cron jobs that may run frequently

### WordPress Integration
- JWT authentication required (JWT Authentication for WP REST API plugin)
- Images uploaded to WordPress media library before post creation
- Posts created as "draft" status for user review
- Email notification sent after successful post creation

### Service Dependencies
**Required Services:**
- MySQL/MariaDB database
- Python 3.8+
- Virtual environment with all requirements.txt packages

**Required API Keys:**
- OpenAI API (per-user)
- Perplexity AI API (per-user)
- Replicate API (system-wide in .env)
- SendGrid API (system-wide in .env)
- **Anthropic API (system-wide or per-user)** - NEW
- WordPress with JWT plugin (per-user)

## Recommended Refactoring

### 🎯 Goal: Standardize on V4

**Why Standardize:**
- Eliminate confusion between V3/V4
- Single source of truth for content generation
- Cleaner, more maintainable codebase
- Identical features, better code structure

**Migration Checklist:**

**Step 1: Update scheduler_v3.py**
```python
# OLD
from openai_integration_v3 import create_blog_post_with_images_v3

# NEW
from openai_integration_v4 import create_blog_post_with_images_v4
```

**Step 2: Update function call in scheduler_v3.py**
```python
# OLD
processed_post, error = create_blog_post_with_images_v3(
    blog_post_idea, user_id, system_prompt
)

# NEW
processed_post, error = create_blog_post_with_images_v4(
    blog_post_idea, user_id, system_prompt
)
```

**Step 3: Test scheduler**
```bash
# Run manual test
python scheduler_v3.py

# Check logs for successful execution
tail -f /var/log/ezwai_scheduler_v3.log
```

**Step 4: Mark V3 as deprecated**
```python
# Add to top of openai_integration_v3.py
"""
DEPRECATED: This file is superseded by openai_integration_v4.py
Please use V4 for all new development.
Kept for reference only.
"""
```

**Step 5: Update documentation**
- Update CLAUDE.md to remove hybrid state section
- Update V3_UPGRADE_GUIDE.md
- Update code comments

**Step 6: Optional - Archive V3**
```bash
# After confirming V4 works in production
mkdir deprecated
mv openai_integration_v3.py deprecated/
git commit -m "Archive V3, standardize on V4"
```

## Troubleshooting

### Application Won't Start
1. Check MySQL is running: `systemctl status mysql` (Linux) or Task Manager (Windows)
2. Verify .env file exists with all required variables
3. Test database connection: `python -c "from app_v3 import app, db; app.app_context().push(); db.engine.connect()"`
4. Check dependencies: `pip install -r requirements.txt`

### Claude Formatter Issues

**Error: "ANTHROPIC_API_KEY not found"**
- Add `ANTHROPIC_API_KEY` to `.env` or `.env.user_{user_id}`
- Verify key format: `sk-ant-api03-...`
- Check key is loaded: `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('ANTHROPIC_API_KEY'))"`

**Error: "Claude API request failed"**
- Verify API key is valid at https://console.anthropic.com/
- Check Anthropic account has credits
- Verify network connectivity to api.anthropic.com
- Check rate limits (50 requests per minute for Sonnet 4.5)

**Formatted HTML looks wrong:**
- Verify image URLs are valid and accessible
- Check brand colors are in correct format (#hexcode)
- Inspect Claude response in logs for debugging
- Consider increasing max_tokens if output is truncated

**Fallback to template formatter:**
- If Claude fails, automatically use `magazine_formatter.py`
- Check logs to see which formatter was used
- Monitor Claude API success rate

### V3/V4 Confusion

**Which version am I using?**
```bash
# Check scheduler
grep "openai_integration" scheduler_v3.py

# Check app
grep "openai_integration" app_v3.py
```

**Articles have inconsistent quality:**
- Likely mixing V3 and V4 outputs
- Both produce same quality, but check which is being used
- Follow "Recommended Refactoring" to standardize

### Scheduler Not Running
1. Verify cron job setup: `crontab -l`
2. Check scheduler logs: `tail -f /var/log/ezwai_scheduler_v3.log`
3. Test manual run: `./run_scheduler_v3.sh`
4. Ensure scheduler_v3.py uses correct integration module

### Image Generation Fails
1. Verify REPLICATE_API_TOKEN in .env
2. Check Replicate account credits
3. Verify SeeDream-4 model is available: https://replicate.com/bytedance/seedream-4

### WordPress Post Creation Fails
1. Verify JWT Authentication plugin is installed and activated
2. Check WordPress REST API is accessible: `curl https://yoursite.com/wp-json/`
3. Verify user credentials in database
4. Check WordPress application passwords are enabled

### Article Quality Issues
1. V3/V4 both use GPT-5-mini with reasoning - check OpenAI API key
2. System prompt significantly affects output quality
3. Perplexity research quality depends on topic queries
4. Reasoning effort is set to "medium" - balance of quality/speed
5. Claude Formatter quality depends on input content quality

## Migration Notes

### From Template Formatter to Claude Formatter

**Steps:**
1. Add `ANTHROPIC_API_KEY` to environment
2. Add `claude_formatter.py` to project
3. Update imports in main pipeline (see "Important Implementation Details")
4. Test with sample article
5. Monitor costs (adds ~$0.09 per article)
6. Keep `magazine_formatter.py` as fallback

**Backward Compatibility:**
- Can run both formatters side-by-side
- Fallback to template if Claude fails
- No database schema changes required

### From V3 to V4 (Recommended)
- No database schema changes required
- Update imports from `openai_integration_v3` to `openai_integration_v4`
- Test scheduler with new imports
- Identical output, cleaner code
- See "Recommended Refactoring" section for detailed steps

### From V2 to V3
- No database schema changes required
- Update imports from `openai_integration_v2` to `openai_integration_v3` (or V4)
- Use V3 startup scripts (start_v3.sh/bat)
- Update cron jobs to use run_scheduler_v3.sh
- API endpoints remain backward compatible

### Breaking Changes
- V1 and V2 files have been removed (code cleanup)
- Legacy startup scripts (restart_app.sh, run_scheduler.sh) removed
- Must use V3 infrastructure for all operations
- **NEW:** Adding Claude Formatter requires Anthropic API key

## Documentation

**Setup & Features:**
- `V3_UPGRADE_GUIDE.md` - Comprehensive V3 feature guide with installation steps
- `V3_ANSWERS.md` - Detailed answers to V3 implementation questions
- `LEGACY_CODE_AUDIT.md` - Code cleanup documentation

**Architecture:**
- `CLAUDE.md` - This file (architecture overview)
- `README.md` - User-facing documentation (if exists)

**Formatters:**
- `claude_formatter.py` - AI-powered formatter implementation
- `magazine_formatter.py` - Template-based formatter (fallback)

**Project History:**
- `WORDPRESS BLOG AUTOMATION PROJECT.txt` - Original project requirements and design

## Testing

**Create Test Post:**
```bash
# Via GUI dashboard
# Navigate to: http://localhost:5000
# Login → Create Post → Click "Create Test Post"

# Via API
curl -X POST http://localhost:5000/api/users/{user_id}/create_test_post \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {jwt_token}"
```

**Test Claude Formatter Standalone:**
```python
# test_claude_formatter.py
from claude_formatter import format_article_with_claude

test_html = "<h1>Test</h1><h2>Section</h2><p>Content...</p>"

result = format_article_with_claude(
    article_html=test_html,
    title="Test Article",
    hero_image_url="https://example.com/hero.jpg",
    section_images=["https://example.com/s1.jpg", "https://example.com/s2.jpg"],
    user_id=1,
    brand_colors={"primary": "#1a73e8", "accent": "#fbbc04"}
)

if result:
    with open("test_output.html", "w") as f:
        f.write(result)
    print("✅ Saved to test_output.html")
```

**Test V4 vs V3:**
```python
# Compare outputs
from openai_integration_v3 import create_blog_post_with_images_v3
from openai_integration_v4 import create_blog_post_with_images_v4

idea = "The future of AI in healthcare"
user_id = 1
prompt = "Write professionally..."

v3_result, v3_error = create_blog_post_with_images_v3(idea, user_id, prompt)
v4_result, v4_error = create_blog_post_with_images_v4(idea, user_id, prompt)

# Both should return identical structure
print(f"V3: {len(v3_result['content'])} chars")
print(f"V4: {len(v4_result['content'])} chars")
```

**Manual Scheduler Test:**
```bash
# Linux
./run_scheduler_v3.sh

# Windows
python scheduler_v3.py
```

**Test File (Updated for V3/V4):**
- `Wordpress_post_test.py` - Standalone test script for WordPress integration

## Code Organization

```
EZWAI SMM/
├── app_v3.py                      # Main Flask application (uses V4)
├── openai_integration_v3.py       # V3 integration (used by scheduler)
├── openai_integration_v4.py       # V4 modular refactor (used by app)
├── image_prompt_generator.py      # Contextual image prompts
├── claude_formatter.py            # NEW: AI-powered formatting
├── magazine_formatter.py          # Template-based formatting (fallback)
├── scheduler_v3.py                # V3 scheduler (uses V3)
├── config.py                      # Database configuration
├── perplexity_ai_integration.py   # Topic research
├── wordpress_integration.py       # WordPress REST API
├── email_notification.py          # SendGrid notifications
├── Wordpress_post_test.py         # Test script
├── requirements.txt               # Python dependencies
├── .env                           # System environment variables
├── .env.user_{id}                 # Per-user environment files
│
├── static/
│   └── dashboard.html             # Modern gradient UI
│
├── logs/                          # Application logs
│   ├── gunicorn.log
│   ├── access.log
│   └── error.log
│
├── Windows Scripts:
│   ├── start_v3.bat
│   ├── start_v3_background.bat
│   └── stop_v3.bat
│
├── Linux Scripts:
│   ├── start_v3.sh
│   ├── start_v3_production.sh
│   ├── stop_v3.sh
│   └── run_scheduler_v3.sh
│
└── Documentation:
    ├── CLAUDE.md                  # This file
    ├── V3_UPGRADE_GUIDE.md        # V3 features and setup
    ├── V3_ANSWERS.md              # Implementation details
    └── LEGACY_CODE_AUDIT.md       # Code cleanup docs
```

## Best Practices

1. **Standardize on V4** - Follow "Recommended Refactoring" to eliminate V3/V4 confusion
2. **Use startup scripts** - They handle dependency/service checks automatically
3. **Monitor logs** - Check application logs for errors and debugging
4. **Test before production** - Use create_test_post to verify configuration
5. **Backup database** - Before major changes or migrations
6. **Keep API keys secure** - Never commit .env files to version control
7. **Update cron jobs** - Use run_scheduler_v3.sh for scheduled posts
8. **Monitor costs** - V3/V4 with Claude costs ~$0.54 per article
9. **Use production mode** - start_v3_production.sh for deployment
10. **Regular updates** - Keep dependencies updated with `pip install -U -r requirements.txt`
11. **Test Claude Formatter** - Verify formatting quality before full deployment
12. **Keep template formatter** - Maintain `magazine_formatter.py` as fallback
13. **Monitor API success rates** - Track Claude vs template formatter usage
14. **Plan V3 deprecation** - After V4 migration, archive V3 for historical reference

## Support

For issues or questions:
1. Check `V3_UPGRADE_GUIDE.md` troubleshooting section
2. Review application logs in `logs/` directory
3. Test individual components (Perplexity, OpenAI, Claude, WordPress) separately
4. Verify all API keys and credentials are current
5. Ensure all required services (MySQL) are running
6. For Claude Formatter issues, check Anthropic console for API status
7. For V3/V4 confusion, check which module is imported in affected file

## Future Enhancements

**Planned Features:**
1. **Complete V4 Migration** - Standardize entire codebase on V4 (recommended)
2. **Multi-Layout Support** - User selection of layout styles (templates ready)
3. **A/B Testing** - Compare Claude vs template formatter performance
4. **Layout Preview** - Show users layout examples before selection
5. **Dynamic Brand Colors** - Per-article color customization
6. **Caching** - Cache formatted results to reduce API costs
7. **Analytics** - Track formatting quality metrics
8. **Custom Layouts** - User-uploaded layout templates
9. **V3 Deprecation** - Archive V3 after V4 standardization complete