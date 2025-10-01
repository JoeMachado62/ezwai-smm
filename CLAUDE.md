# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EZWAI SMM is an automated social media management system that generates and publishes professional magazine-style blog posts to WordPress. The system uses multiple AI services to create comprehensive 1500-2500 word articles with photorealistic images and professional HTML formatting.

## Version 3.0 (Current - 2025)

**State-of-the-Art AI Integration:**
- **GPT-5-mini with Responses API** - Latest reasoning model with "medium effort" setting
- **SeeDream-4 Image Model** - 2K resolution photorealistic images with text rendering
- **AI-Powered Photographic Prompts** - Guarantees professional photography (not illustrations)
- **Magazine-Quality Articles** - 1500-2500 words with structured HTML formatting
- **Modern Gradient UI** - Purple/violet themed dashboard with real-time progress tracking

## Architecture

### Core Flow (V3)
1. **Scheduler** (`scheduler_v3.py`) - Runs periodically to check user schedules and trigger blog post creation
2. **Query Management** (`perplexity_ai_integration.py`) - Rotates through user-defined topic queries and fetches trending news using Perplexity AI
3. **Content Generation** (`openai_integration_v3.py`) - Uses GPT-5-mini with reasoning to create magazine-style articles, generates AI-powered photographic prompts, creates 4 SeeDream-4 images (1 hero 16:9 + 3 section 4:3)
4. **Publishing** (`wordpress_integration.py`) - Posts content to WordPress via REST API with JWT authentication
5. **Notification** (`email_notification.py`) - Sends email notifications via SendGrid when posts are created

### Key Files
**V3 Application:**
- `app_v3.py` - Main Flask application with V3 integrations
- `openai_integration_v3.py` - GPT-5-mini Responses API + SeeDream-4 integration
- `scheduler_v3.py` - V3-compatible scheduler
- `static/dashboard.html` - Modern gradient UI dashboard

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

### Database Models
- **User** - Stores user credentials, API keys, queries, system prompts, and schedules (JSON fields)
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
```

### Per-User Environment Variables (.env.user_{user_id})
Generated dynamically via `generate_env_file()`:
```bash
OPENAI_API_KEY="sk-..."
WORDPRESS_REST_API_URL="https://example.com/wp-json/wp/v2"
WORDPRESS_USERNAME="username"
WORDPRESS_PASSWORD="password"
PERPLEXITY_AI_API_TOKEN="pplx-..."
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
- `POST /api/users/<user_id>/integrations` - Save OpenAI, WordPress, Perplexity credentials
- `GET /api/users/<user_id>/integrations` - Get saved integrations

### Blog Post Creation
- `POST /api/users/<user_id>/create_test_post` - Create immediate test post with V3 features
- `POST /api/users/<user_id>/schedule` - Schedule automated posts

### System
- `GET /api/users/<user_id>/progress` - Server-sent events for progress tracking

## Key Features

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
- Pull quotes with teal borders
- Stat highlights with orange backgrounds
- Case study sections with gray backgrounds
- Professional typography (Playfair Display + Roboto)
- Responsive design

### Cost & Performance

**V3.0 (Current):**
- Cost per article: ~$0.45
- Generation time: 3-4 minutes
- Article length: 1500-2500 words
- Images: 4 photorealistic 2K images
- Quality: State-of-the-art with reasoning

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

### Per-User Configuration
- API credentials stored in database User model
- `generate_env_file()` creates `.env.user_{user_id}` files on login
- Each blog post creation loads user-specific environment

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
- WordPress with JWT plugin (per-user)

## Troubleshooting

### Application Won't Start
1. Check MySQL is running: `systemctl status mysql` (Linux) or Task Manager (Windows)
2. Verify .env file exists with all required variables
3. Test database connection: `python -c "from app_v3 import app, db; app.app_context().push(); db.engine.connect()"`
4. Check dependencies: `pip install -r requirements.txt`

### Scheduler Not Running
1. Verify cron job setup: `crontab -l`
2. Check scheduler logs: `tail -f /var/log/ezwai_scheduler_v3.log`
3. Test manual run: `./run_scheduler_v3.sh`
4. Ensure scheduler_v3.py uses V3 modules (NOT legacy scheduler.py)

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
1. V3 uses GPT-5-mini with reasoning - check OpenAI API key
2. System prompt significantly affects output quality
3. Perplexity research quality depends on topic queries
4. Reasoning effort is set to "medium" - balance of quality/speed

## Migration Notes

### From V2 to V3
- No database schema changes required
- Update imports from `openai_integration_v2` to `openai_integration_v3`
- Use V3 startup scripts (start_v3.sh/bat)
- Update cron jobs to use run_scheduler_v3.sh
- API endpoints remain backward compatible

### Breaking Changes
- V1 and V2 files have been removed (code cleanup)
- Legacy startup scripts (restart_app.sh, run_scheduler.sh) removed
- Must use V3 infrastructure for all operations

## Documentation

**Setup & Features:**
- `V3_UPGRADE_GUIDE.md` - Comprehensive V3 feature guide with installation steps
- `V3_ANSWERS.md` - Detailed answers to V3 implementation questions
- `LEGACY_CODE_AUDIT.md` - Code cleanup documentation

**Architecture:**
- `CLAUDE.md` - This file (architecture overview)
- `README.md` - User-facing documentation (if exists)

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

**Manual Scheduler Test:**
```bash
# Linux
./run_scheduler_v3.sh

# Windows
python scheduler_v3.py
```

**Test File (Updated for V3):**
- `Wordpress_post_test.py` - Standalone test script for WordPress integration

## Code Organization

```
EZWAI SMM/
├── app_v3.py                      # Main Flask application
├── openai_integration_v3.py       # GPT-5-mini + SeeDream-4
├── scheduler_v3.py                # V3 scheduler
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

1. **Always use V3 files** - Legacy V1/V2 code has been removed
2. **Use startup scripts** - They handle dependency/service checks automatically
3. **Monitor logs** - Check application logs for errors and debugging
4. **Test before production** - Use create_test_post to verify configuration
5. **Backup database** - Before major changes or migrations
6. **Keep API keys secure** - Never commit .env files to version control
7. **Update cron jobs** - Use run_scheduler_v3.sh for scheduled posts
8. **Monitor costs** - V3 costs ~$0.45 per article due to GPT-5-mini reasoning
9. **Use production mode** - start_v3_production.sh for deployment
10. **Regular updates** - Keep dependencies updated with `pip install -U -r requirements.txt`

## Support

For issues or questions:
1. Check `V3_UPGRADE_GUIDE.md` troubleshooting section
2. Review application logs in `logs/` directory
3. Test individual components (Perplexity, OpenAI, WordPress) separately
4. Verify all API keys and credentials are current
5. Ensure all required services (MySQL) are running
