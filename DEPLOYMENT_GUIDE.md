# EZWAI SMM - Deployment Guide

Complete guide for deploying EZWAI SMM to a Linux VPS.

## Pre-Deployment Checklist

- [ ] Linux VPS with Python 3.8+ installed
- [ ] Domain name (optional but recommended)
- [ ] SSH access to VPS
- [ ] API Keys ready:
  - Replicate API token
  - SendGrid API key
- [ ] Git installed on VPS

## Step 1: Server Preparation

### Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### Install Required Packages
```bash
sudo apt install python3 python3-pip python3-venv nginx supervisor git -y
```

### Create Application User (recommended)
```bash
sudo useradd -m -s /bin/bash ezwai
sudo su - ezwai
```

## Step 2: Clone and Setup Application

### Clone Repository
```bash
cd ~
git clone https://github.com/yourusername/ezwai-smm.git
cd ezwai-smm
```

### Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configure Environment
```bash
cp .env.example .env
nano .env
```

**Edit .env with your values:**
```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USERNAME=apikey
EMAIL_PASSWORD=YOUR_SENDGRID_KEY

FLASK_SECRET_KEY=YOUR_RANDOM_SECRET_KEY
FLASK_DEBUG=False

REPLICATE_API_TOKEN=YOUR_REPLICATE_TOKEN

DATABASE_URL=sqlite:///ezwai_smm.db
```

### Initialize Database
```bash
python -c "from app_v3 import app, db; app.app_context().push(); db.create_all()"
```

## Step 3: Test Application

```bash
# Start in development mode
python app_v3.py
```

Access at `http://your-server-ip:5000/auth` and verify:
- Registration works
- Login works
- Dashboard loads after login

Press Ctrl+C to stop.

## Step 4: Configure Gunicorn (Production Server)

### Create Gunicorn Configuration
```bash
nano gunicorn_config.py
```

```python
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = 'logs/access.log'
errorlog = 'logs/error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'ezwai_smm'

# Server mechanics
daemon = False
pidfile = 'gunicorn.pid'
umask = 0
user = None
group = None
tmp_upload_dir = None

# Max requests per worker before restart
max_requests = 1000
max_requests_jitter = 50
```

### Create Logs Directory
```bash
mkdir -p logs
```

## Step 5: Setup Supervisor (Auto-Start & Monitoring)

### Create Supervisor Configuration
```bash
sudo nano /etc/supervisor/conf.d/ezwai-smm.conf
```

```ini
[program:ezwai-smm]
command=/home/ezwai/ezwai-smm/venv/bin/gunicorn -c gunicorn_config.py app_v3:app
directory=/home/ezwai/ezwai-smm
user=ezwai
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/home/ezwai/ezwai-smm/logs/supervisor_err.log
stdout_logfile=/home/ezwai/ezwai-smm/logs/supervisor_out.log
environment=PATH="/home/ezwai/ezwai-smm/venv/bin"
```

### Start Application
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start ezwai-smm
```

### Check Status
```bash
sudo supervisorctl status ezwai-smm
```

Should show: `ezwai-smm  RUNNING`

## Step 6: Configure Nginx (Reverse Proxy)

### Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/ezwai-smm
```

**Without Domain (IP Only):**
```nginx
server {
    listen 80;
    server_name your_server_ip;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files
    location /static {
        alias /home/ezwai/ezwai-smm/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    client_max_body_size 10M;
}
```

**With Domain:**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /home/ezwai/ezwai-smm/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    client_max_body_size 10M;
}
```

### Enable Configuration
```bash
sudo ln -s /etc/nginx/sites-available/ezwai-smm /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

## Step 7: Setup SSL (HTTPS) with Let's Encrypt

**Only if you have a domain name:**

### Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
```

### Obtain Certificate
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow prompts and choose redirect option (option 2).

### Auto-Renewal
```bash
sudo certbot renew --dry-run  # Test renewal
```

Certbot automatically creates a cron job for renewal.

## Step 8: Setup Scheduler (Optional)

### Create Cron Job
```bash
crontab -e
```

Add line to run scheduler every 5 minutes:
```bash
*/5 * * * * cd /home/ezwai/ezwai-smm && /home/ezwai/ezwai-smm/venv/bin/python scheduler_v3.py >> /home/ezwai/ezwai-smm/logs/scheduler.log 2>&1
```

Or use the provided script:
```bash
*/5 * * * * /home/ezwai/ezwai-smm/run_scheduler_v3.sh
```

### Verify Cron Jobs
```bash
crontab -l
```

## Step 9: Firewall Configuration

### UFW (Uncomplicated Firewall)
```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
sudo ufw status
```

## Step 10: First-Time Setup

1. Access application:
   - **Without SSL:** http://your-server-ip/auth
   - **With SSL:** https://yourdomain.com/auth

2. Register first admin account

3. Login and configure Settings:
   - OpenAI API Key
   - Perplexity AI Token
   - WordPress credentials

4. Add topic queries

5. Create test post to verify everything works

## Maintenance

### View Application Logs
```bash
# Real-time logs
tail -f ~/ezwai-smm/logs/error.log

# Supervisor logs
sudo tail -f /var/log/supervisor/supervisord.log
```

### Restart Application
```bash
sudo supervisorctl restart ezwai-smm
```

### Stop Application
```bash
sudo supervisorctl stop ezwai-smm
```

### Update Application
```bash
cd ~/ezwai-smm
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart ezwai-smm
```

### Backup Database
```bash
cp ~/ezwai-smm/ezwai_smm.db ~/ezwai_smm_backup_$(date +%Y%m%d).db
```

### Check Disk Space
```bash
df -h
```

### Monitor System Resources
```bash
htop  # Install with: sudo apt install htop
```

## Troubleshooting

### Application Won't Start
```bash
# Check supervisor status
sudo supervisorctl status ezwai-smm

# View error logs
tail -n 50 ~/ezwai-smm/logs/error.log

# Check if port 8000 is in use
sudo netstat -tulpn | grep 8000

# Restart supervisor
sudo systemctl restart supervisor
```

### Nginx 502 Bad Gateway
```bash
# Check if Gunicorn is running
sudo supervisorctl status ezwai-smm

# Restart application
sudo supervisorctl restart ezwai-smm

# Check Nginx error log
sudo tail -f /var/log/nginx/error.log
```

### Database Issues
```bash
# Check database file permissions
ls -la ~/ezwai-smm/ezwai_smm.db

# Fix permissions if needed
chmod 664 ~/ezwai-smm/ezwai_smm.db
```

### Out of Memory
```bash
# Check memory usage
free -h

# Reduce Gunicorn workers in gunicorn_config.py
nano ~/ezwai-smm/gunicorn_config.py
# Change: workers = 2  (instead of CPU-based calculation)

# Restart
sudo supervisorctl restart ezwai-smm
```

## Security Best Practices

1. **Keep System Updated**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Use Strong Passwords**
   - Application accounts
   - Server SSH access
   - API keys

3. **Regular Backups**
   ```bash
   # Create backup script
   nano ~/backup.sh
   ```

   ```bash
   #!/bin/bash
   DATE=$(date +%Y%m%d)
   cp ~/ezwai-smm/ezwai_smm.db ~/backups/ezwai_smm_$DATE.db
   find ~/backups -name "*.db" -mtime +7 -delete
   ```

   ```bash
   chmod +x ~/backup.sh
   crontab -e
   # Add: 0 2 * * * ~/backup.sh  # Daily at 2 AM
   ```

4. **Monitor Logs**
   ```bash
   # Setup logrotate
   sudo nano /etc/logrotate.d/ezwai-smm
   ```

   ```
   /home/ezwai/ezwai-smm/logs/*.log {
       daily
       rotate 7
       compress
       delaycompress
       notifempty
       create 0640 ezwai ezwai
   }
   ```

5. **Fail2ban** (prevent brute force)
   ```bash
   sudo apt install fail2ban -y
   ```

## Performance Optimization

### Database
- SQLite works great for single-user or small teams
- Consider PostgreSQL for high-traffic production use

### Image Optimization
- SeeDream-4 images are high-quality 2K
- WordPress automatically creates thumbnails
- Consider CDN for static assets

### Caching
- Nginx caches static files (configured above)
- Consider Redis for session storage (advanced)

## Support

If you encounter issues:
1. Check logs: `tail -f ~/ezwai-smm/logs/error.log`
2. Review this guide's troubleshooting section
3. Consult README.md documentation
4. Open GitHub issue with log excerpts

---

**Deployment complete!** Your EZWAI SMM installation should now be running in production.
