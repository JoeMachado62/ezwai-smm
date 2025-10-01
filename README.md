# EZWAI SMM - AI-Powered Social Media Management

> Automated blog post generation and publishing system using GPT-5-mini, Perplexity AI, and SeeDream-4

## 🌟 Features

### V5 (Current - 2025)
- **GPT-5-mini with Responses API** - Latest reasoning model with structured JSON output
- **SeeDream-4 Image Generation** - 2K resolution photorealistic images
- **Magazine-Style Articles** - 1500-2500 words with professional HTML formatting
- **Smart Topic Research** - Perplexity AI integration for trending news
- **WordPress Integration** - Automatic posting with JWT authentication
- **Multi-User Support** - User-specific API credentials and scheduling
- **Email Notifications** - SendGrid integration for post alerts

### Key Capabilities
- Single GPT-5-mini call generates both article and image prompts
- 4 photorealistic images per article (1 hero 16:9 + 3 sections 4:3)
- Natural section titles and topic-specific content (no template bias)
- Automated scheduling with duplicate prevention
- Query rotation system for topic diversity

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL/MariaDB
- API Keys:
  - OpenAI (GPT-5-mini)
  - Perplexity AI
  - Replicate (SeeDream-4)
  - SendGrid (email notifications)
  - WordPress site with JWT Authentication plugin

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/JoeMachado62/ezwai-smm.git
   cd ezwai-smm
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your system credentials
   ```

5. **Initialize database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

### Running the Application

**Development (Windows):**
```bash
start_v3.bat
```

**Development (Linux/Mac):**
```bash
./start_v3.sh
```

**Production (Linux):**
```bash
./start_v3_production.sh  # Uses Gunicorn with 4 workers
```

Visit `http://localhost:5000` to access the dashboard.

### Setting Up Scheduled Posts

**Linux/Mac (cron):**
```bash
crontab -e
# Add: */5 * * * * cd /path/to/ezwai-smm && ./run_scheduler_v3.sh
```

**Windows (Task Scheduler):**
Create a task to run `scheduler_v3.py` every 5 minutes.

## 📁 Project Structure

```
ezwai-smm/
├── app_v3.py                      # Main Flask application
├── openai_integration_v4.py       # GPT-5-mini + SeeDream-4 (V5)
├── scheduler_v3.py                # Job scheduler
├── perplexity_ai_integration.py   # Topic research
├── wordpress_integration.py       # WordPress REST API
├── email_notification.py          # SendGrid notifications
├── config.py                      # Database configuration
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
├── static/
│   └── dashboard.html             # Modern gradient UI
├── tests/
│   ├── test_v4_generation.py      # V5 test script
│   ├── test_blog_generation.py    # Integration test
│   └── Wordpress_post_test.py     # WordPress test
└── docs/
    ├── CLAUDE.md                  # Architecture overview
    ├── V3_UPGRADE_GUIDE.md        # V3 features guide
    └── V3_ANSWERS.md              # Implementation details
```

## 🔧 Configuration

### System Environment (.env)
```env
DB_USERNAME=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_NAME=ezwai_smm

FLASK_SECRET_KEY=your_secret_key
FLASK_DEBUG=False

EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USERNAME=apikey
EMAIL_PASSWORD=your_sendgrid_api_key

REPLICATE_API_TOKEN=your_replicate_token
```

### Per-User Configuration
- OpenAI API key
- Perplexity AI token
- WordPress credentials
- Topic queries (up to 10)
- Post schedule (up to 2 per day)

User credentials are stored in the database and automatically generate `.env.user_{user_id}` files.

## 📊 API Endpoints

### Authentication
- `POST /register` - Create user account
- `POST /login` - User login (returns JWT)

### Blog Management
- `POST /api/users/<user_id>/create_test_post` - Create immediate post
- `POST /api/users/<user_id>/schedule` - Schedule automated posts
- `GET /api/users/<user_id>/progress` - Real-time progress (SSE)

### User Management
- `GET /api/users/<user_id>` - Get user profile
- `PUT /api/users/<user_id>` - Update profile
- `POST /api/users/<user_id>/integrations` - Save API credentials

## 🧪 Testing

Run V5 blog generation test:
```bash
python tests/test_v4_generation.py
```

Run WordPress integration test:
```bash
python tests/Wordpress_post_test.py
```

## 💰 Cost & Performance

**Per Article (V5):**
- Cost: ~$0.45
- Generation time: 3-4 minutes
- Article length: 1500-2500 words
- Images: 4 photorealistic 2K images
- Quality: State-of-the-art with reasoning

## 📝 Version History

### V5 (2025) - Current
- Removed implementation guide bias from prompts
- Natural, topic-specific section titles
- Fixed Replicate model identifier
- Enhanced error logging

### V3 (2025)
- GPT-5-mini with Responses API
- SeeDream-4 image generation
- Structured JSON output
- Magazine-style HTML

### V2 (2024)
- GPT-4o-mini with Flux-dev images
- Basic magazine layout

### V1 (2024)
- GPT-3.5-turbo with DALL-E 3
- Simple blog posts

## 🔒 Security

- Never commit `.env` files
- API keys stored per-user in database
- JWT authentication for WordPress
- Secure credential management
- `.env.user_*` files auto-generated and gitignored

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-5-mini
- Perplexity AI for trending topic research
- Replicate for SeeDream-4 image generation
- SendGrid for email notifications

## 📞 Support

For issues or questions:
- Check documentation in `docs/` folder
- Review application logs in `logs/` directory
- Verify API credentials and service status

---

**Built with ❤️ by Joe Machado**
