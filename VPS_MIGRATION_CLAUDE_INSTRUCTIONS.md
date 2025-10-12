# VPS Migration Instructions for Claude Code

**Purpose:** Instructions for Claude Code on VPS to complete the database migration after `users_export.sql` is uploaded.

---

## Context

The local Windows machine has exported user data from SQLite to `users_export.sql`. This file needs to be imported into the VPS MySQL/MariaDB database to restore all users and their settings.

## Prerequisites

Before starting, verify:
1. ✅ VPS has pulled latest code: `git pull origin main`
2. ✅ File `users_export.sql` has been uploaded to `/root/EZWAI_SMM/`
3. ✅ MySQL/MariaDB is running: `systemctl status mysql`
4. ✅ Database credentials are in `.env` file

## Migration Steps (Execute in Order)

### Step 1: Verify File Upload

```bash
# Check file exists
ls -lh /root/EZWAI_SMM/users_export.sql

# Verify file is not empty and contains user data
head -20 /root/EZWAI_SMM/users_export.sql | grep "INSERT INTO user"
```

**Expected:** Should see SQL INSERT statements for user table.

---

### Step 2: Load Database Credentials

```bash
cd /root/EZWAI_SMM
source .env

# Verify credentials loaded
echo "DB_USERNAME: $DB_USERNAME"
echo "DB_NAME: $DB_NAME"
# Don't echo password for security
```

**Expected:** Should see username and database name.

---

### Step 3: Create Database Schema (if not exists)

```bash
# Activate virtual environment
source /root/EZWAI_SMM/venv/bin/activate

# Run migrations to create tables
cd /root/EZWAI_SMM
flask db upgrade

# Verify tables exist
mysql -u "$DB_USERNAME" -p"$DB_PASSWORD" "$DB_NAME" -e "SHOW TABLES;"
```

**Expected Output:** Should see tables:
- `user`
- `completed_job`
- `credit_transactions`
- `articles`
- `images`
- `alembic_version`

---

### Step 4: Backup Current Database (if any data exists)

```bash
# Create backup directory
mkdir -p /root/EZWAI_SMM/backups

# Backup current state
BACKUP_FILE="/root/EZWAI_SMM/backups/backup_before_migration_$(date +%Y%m%d_%H%M%S).sql"
mysqldump -u "$DB_USERNAME" -p"$DB_PASSWORD" "$DB_NAME" > "$BACKUP_FILE"

echo "Backup saved to: $BACKUP_FILE"
```

**Expected:** Backup file created in `/root/EZWAI_SMM/backups/`

---

### Step 5: Import User Data

```bash
cd /root/EZWAI_SMM

# Import the SQL file
mysql -u "$DB_USERNAME" -p"$DB_PASSWORD" "$DB_NAME" < users_export.sql

# Check for errors in output
echo "Exit code: $?"
```

**Expected:** Exit code should be `0` (success).

**If Import Fails with Duplicate Key Errors:**

This means data already exists. You have two options:

**Option A: Clear existing data and re-import (CAUTION: Deletes all data)**
```bash
mysql -u "$DB_USERNAME" -p"$DB_PASSWORD" "$DB_NAME" << 'EOF'
SET FOREIGN_KEY_CHECKS=0;
TRUNCATE TABLE images;
TRUNCATE TABLE articles;
TRUNCATE TABLE credit_transactions;
TRUNCATE TABLE completed_job;
TRUNCATE TABLE user;
SET FOREIGN_KEY_CHECKS=1;
EOF

# Then re-import
mysql -u "$DB_USERNAME" -p"$DB_PASSWORD" "$DB_NAME" < users_export.sql
```

**Option B: Skip duplicate rows (keeps existing data)**
```bash
mysql -u "$DB_USERNAME" -p"$DB_PASSWORD" "$DB_NAME" --force < users_export.sql
```

---

### Step 6: Verify Import Success

```bash
# Count imported users
mysql -u "$DB_USERNAME" -p"$DB_PASSWORD" "$DB_NAME" -e "SELECT COUNT(*) as user_count FROM user;"

# List users
mysql -u "$DB_USERNAME" -p"$DB_PASSWORD" "$DB_NAME" -e "
SELECT id, email, first_name, last_name, credit_balance, created_at
FROM user
ORDER BY id;
"

# Check credit transactions
mysql -u "$DB_USERNAME" -p"$DB_PASSWORD" "$DB_NAME" -e "SELECT COUNT(*) as transaction_count FROM credit_transactions;"

# Check completed jobs
mysql -u "$DB_USERNAME" -p"$DB_PASSWORD" "$DB_NAME" -e "SELECT COUNT(*) as job_count FROM completed_job;"
```

**Expected Results:**
- User count: 6 users
- Transaction count: 17 transactions
- Job count: 0 (no completed jobs yet)

---

### Step 7: Test Database Connection from Flask App

```bash
cd /root/EZWAI_SMM
source venv/bin/activate

# Test database connection
python3 << 'EOF'
from app_v3 import app, db, User

with app.app_context():
    users = User.query.all()
    print(f"✅ Database connection successful!")
    print(f"Total users: {len(users)}")
    for user in users:
        print(f"  - {user.email} (ID: {user.id}, Credits: {user.credit_balance})")
EOF
```

**Expected:** Should print list of 6 users with their email and credit balance.

---

### Step 8: Restart Application

```bash
cd /root/EZWAI_SMM

# Stop current application
./stop_v3.sh

# Start with correct port (5001 to avoid n8n conflict)
EZWAI_PORT=5001 ./start_v3_production.sh

# Verify application started
sleep 3
curl -I http://localhost:5001
```

**Expected:** Should see `HTTP/1.1 200 OK` or redirect to login page.

---

### Step 9: Test User Login via Browser

**From local machine browser:**
```
http://YOUR_VPS_IP:5001
```

**Try logging in with existing user credentials.**

**Expected:**
- ✅ Login page loads with "My Content Generator" branding
- ✅ User can login successfully
- ✅ Dashboard shows correct credit balance
- ✅ Settings page shows configured API integrations

---

### Step 10: Cleanup Sensitive Files

```bash
# Delete SQL export file (contains sensitive data)
rm /root/EZWAI_SMM/users_export.sql

# Verify deletion
ls -la /root/EZWAI_SMM/users_export.sql
# Should show "No such file or directory"
```

**Expected:** File deleted successfully.

---

## Troubleshooting

### Issue: "Access denied for user"

**Problem:** MySQL credentials incorrect or user doesn't have permissions.

**Solution:**
```bash
# Check credentials in .env
cat /root/EZWAI_SMM/.env | grep DB_

# Grant permissions
mysql -u root -p << EOF
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USERNAME'@'localhost';
FLUSH PRIVILEGES;
EOF
```

---

### Issue: "Table 'user' doesn't exist"

**Problem:** Database schema not created.

**Solution:**
```bash
cd /root/EZWAI_SMM
source venv/bin/activate
flask db upgrade
```

---

### Issue: "Can't login after import - 500 error"

**Problem:** Password hashes may be corrupted or app can't connect to database.

**Solution:**
```bash
# Check password hash exists
mysql -u "$DB_USERNAME" -p"$DB_PASSWORD" "$DB_NAME" -e "
SELECT id, email, LENGTH(password_hash) as hash_length
FROM user;
"

# Hash should be ~100+ characters
# If 0 or NULL, passwords weren't imported

# Check Flask logs
tail -50 /root/EZWAI_SMM/logs/gunicorn.log
```

---

### Issue: "Articles/Images not showing"

**Problem:** Articles and Images tables were empty in local database (expected).

**Solution:** This is normal - the local database didn't have the articles/images tables yet. Users will create articles after login, and they'll be saved to the VPS database.

---

## Post-Migration Checklist

After completing all steps, verify:

- [ ] 6 users imported successfully
- [ ] User login works on VPS
- [ ] Credits balance correct for all users
- [ ] Dashboard loads without errors
- [ ] Settings page shows API integrations
- [ ] Application running on port 5001
- [ ] SQL export file deleted from VPS
- [ ] Backup of database created

---

## Summary

This migration:
1. ✅ Transfers all user accounts with passwords (hashed)
2. ✅ Preserves credit balances and transaction history
3. ✅ Keeps API credentials configured (OpenAI, WordPress, Perplexity)
4. ✅ Maintains topic queries and system prompts
5. ✅ Preserves brand colors and writing styles
6. ✅ Maintains Stripe customer IDs

**Time Estimate:** 10-15 minutes

**Risk Level:** Low (backup created before import)

Users can immediately login to VPS with existing credentials and continue using the platform without reconfiguration!
