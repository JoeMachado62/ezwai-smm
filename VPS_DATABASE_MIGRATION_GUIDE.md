# VPS Database Migration Guide

Complete guide to migrate user data from local SQLite to VPS MySQL/MariaDB.

## Overview

This guide covers:
1. Exporting user data from local Windows SQLite database
2. Transferring SQL file to VPS
3. Importing data into VPS MySQL/MariaDB
4. Verifying migration success

## Prerequisites

**Local Machine (Windows):**
- Python environment with all dependencies installed
- Access to local SQLite database (`ezwai_smm.db`)
- SCP/SFTP client (WinSCP, FileZilla, or PowerShell)

**VPS (Ubuntu):**
- MySQL/MariaDB installed and running
- Database created with proper schema (tables created via Flask-Migrate)
- SSH access to VPS

## Step 1: Export Local Database (Windows)

### 1.1 Run Export Script

```bash
# Navigate to project directory
cd "c:\Users\joema\OneDrive\Documents\AI PROJECT\EZWAI SMM"

# Activate virtual environment (if using)
venv\Scripts\activate

# Run export script
python export_users_to_sql.py users_export.sql
```

**Expected Output:**
```
✅ Export complete: users_export.sql
   - 2 users
   - 15 completed jobs
   - 23 credit transactions
   - 12 articles
   - 48 images

Upload this file to your VPS and import with:
mysql -u YOUR_DB_USER -p YOUR_DB_NAME < users_export.sql
```

### 1.2 Verify Export File

```bash
# Check file was created
dir users_export.sql

# View first few lines
type users_export.sql | more
```

The file should contain SQL INSERT statements for all your users and related data.

## Step 2: Transfer SQL File to VPS

### Option A: Using PowerShell SCP

```powershell
# Transfer file to VPS
scp "users_export.sql" root@YOUR_VPS_IP:/root/EZWAI_SMM/

# Enter password when prompted
```

### Option B: Using WinSCP (GUI)

1. Open WinSCP
2. Connect to VPS (Protocol: SCP, Host: YOUR_VPS_IP, User: root)
3. Navigate to `/root/EZWAI_SMM/` on VPS
4. Upload `users_export.sql` from local machine

### Option C: Copy/Paste (Small Files Only)

```bash
# On local machine - copy file contents
type users_export.sql | clip

# SSH into VPS
ssh root@YOUR_VPS_IP

# Create file on VPS
cd /root/EZWAI_SMM
nano users_export.sql
# Paste contents (Ctrl+Shift+V)
# Save (Ctrl+O, Enter, Ctrl+X)
```

## Step 3: Prepare VPS Database

### 3.1 SSH into VPS

```bash
ssh root@YOUR_VPS_IP
cd /root/EZWAI_SMM
```

### 3.2 Verify Database Schema Exists

```bash
# Activate virtual environment
source venv/bin/activate

# Check database tables exist
mysql -u YOUR_DB_USER -p -e "USE YOUR_DB_NAME; SHOW TABLES;"
```

**Expected Tables:**
- `user`
- `completed_job`
- `credit_transaction`
- `articles`
- `images`
- `alembic_version` (migration tracking)

### 3.3 If Tables Don't Exist - Create Schema

```bash
# Initialize database with Flask-Migrate
cd /root/EZWAI_SMM
source venv/bin/activate

# Create tables
flask db upgrade

# Verify tables created
mysql -u YOUR_DB_USER -p -e "USE YOUR_DB_NAME; SHOW TABLES;"
```

## Step 4: Import User Data

### 4.1 Backup Existing Data (if any)

```bash
# Backup current database state
mysqldump -u YOUR_DB_USER -p YOUR_DB_NAME > backup_before_import_$(date +%Y%m%d_%H%M%S).sql
```

### 4.2 Import SQL File

```bash
# Import user data
mysql -u YOUR_DB_USER -p YOUR_DB_NAME < users_export.sql

# Enter MySQL password when prompted
```

**If you see errors about duplicate keys:**
```bash
# Clear existing data first (CAUTION: This deletes all data!)
mysql -u YOUR_DB_USER -p YOUR_DB_NAME -e "
SET FOREIGN_KEY_CHECKS=0;
TRUNCATE TABLE images;
TRUNCATE TABLE articles;
TRUNCATE TABLE credit_transaction;
TRUNCATE TABLE completed_job;
TRUNCATE TABLE user;
SET FOREIGN_KEY_CHECKS=1;
"

# Then import again
mysql -u YOUR_DB_USER -p YOUR_DB_NAME < users_export.sql
```

## Step 5: Verify Import Success

### 5.1 Check User Count

```bash
mysql -u YOUR_DB_USER -p YOUR_DB_NAME -e "SELECT COUNT(*) as user_count FROM user;"
```

Should match the number from export output.

### 5.2 Verify User Data

```bash
# List all users
mysql -u YOUR_DB_USER -p YOUR_DB_NAME -e "
SELECT id, username, email, first_name, last_name, credits, created_at
FROM user;
"
```

### 5.3 Check Related Data

```bash
# Check completed jobs
mysql -u YOUR_DB_USER -p YOUR_DB_NAME -e "SELECT COUNT(*) FROM completed_job;"

# Check credit transactions
mysql -u YOUR_DB_USER -p YOUR_DB_NAME -e "SELECT COUNT(*) FROM credit_transaction;"

# Check articles
mysql -u YOUR_DB_USER -p YOUR_DB_NAME -e "SELECT COUNT(*) FROM articles;"

# Check images
mysql -u YOUR_DB_USER -p YOUR_DB_NAME -e "SELECT COUNT(*) FROM images;"
```

All counts should match the export output.

## Step 6: Test Login on VPS

### 6.1 Restart Application

```bash
cd /root/EZWAI_SMM
./stop_v3.sh
EZWAI_PORT=5001 ./start_v3_production.sh
```

### 6.2 Test User Login

```bash
# From your local machine browser
http://YOUR_VPS_IP:5001

# Try logging in with your existing credentials
```

### 6.3 Verify User Data Loads

After successful login:
1. Check dashboard loads correctly
2. Verify credits balance shows correctly
3. Check Article Library shows historical articles
4. Check Image Library shows historical images
5. Verify API integrations are configured (Settings page)

## Troubleshooting

### Error: "Access denied for user"

**Problem:** MySQL credentials incorrect or user doesn't have permissions

**Solution:**
```bash
# Check .env file has correct credentials
cat /root/EZWAI_SMM/.env | grep DB_

# Grant permissions to database user
mysql -u root -p -e "
GRANT ALL PRIVILEGES ON YOUR_DB_NAME.* TO 'YOUR_DB_USER'@'localhost';
FLUSH PRIVILEGES;
"
```

### Error: "Table 'user' doesn't exist"

**Problem:** Database schema not created

**Solution:**
```bash
cd /root/EZWAI_SMM
source venv/bin/activate
flask db upgrade
```

### Error: "Duplicate entry for key 'PRIMARY'"

**Problem:** Data already exists in database

**Solution:**
```bash
# Option 1: Clear existing data (see Step 4.2 above)

# Option 2: Skip duplicate rows
mysql -u YOUR_DB_USER -p YOUR_DB_NAME --force < users_export.sql
```

### Error: "Can't login after import"

**Problem:** Password hashes may be corrupted or session issues

**Solution:**
```bash
# Check user exists and has password_hash
mysql -u YOUR_DB_USER -p YOUR_DB_NAME -e "
SELECT id, username, email, LENGTH(password_hash) as hash_length
FROM user;
"

# Hash should be ~100+ characters (bcrypt hash)
# If hash_length is 0 or NULL, passwords weren't imported correctly
```

### Error: "Articles/Images not showing in dashboard"

**Problem:** Foreign key relationships may be broken

**Solution:**
```bash
# Verify article user_id matches actual user IDs
mysql -u YOUR_DB_USER -p YOUR_DB_NAME -e "
SELECT a.id, a.title, a.user_id, u.username
FROM articles a
LEFT JOIN user u ON a.user_id = u.id
WHERE u.id IS NULL;
"

# If any rows returned, those articles have invalid user_id
# Fix with:
UPDATE articles SET user_id = YOUR_CORRECT_USER_ID WHERE user_id = INVALID_ID;
```

## Security Considerations

### 1. Secure the SQL Export File

```bash
# SQL file contains sensitive data (password hashes, API keys)
# Delete after import
rm users_export.sql

# On local machine, also delete or move to secure location
del users_export.sql
```

### 2. Verify API Keys are Encrypted

```bash
# Check that API keys are stored (they're in plaintext for now)
mysql -u YOUR_DB_USER -p YOUR_DB_NAME -e "
SELECT username,
       SUBSTRING(openai_api_key, 1, 10) as openai_key_preview,
       SUBSTRING(wordpress_app_password, 1, 10) as wp_key_preview
FROM user;
"

# Keys should show first 10 characters
# Full keys are stored in database (ensure database access is restricted)
```

### 3. Restrict Database Access

```bash
# Ensure database user only has access to EZWAI database
mysql -u root -p -e "
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'YOUR_DB_USER'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, ALTER ON YOUR_DB_NAME.* TO 'YOUR_DB_USER'@'localhost';
FLUSH PRIVILEGES;
"
```

## Post-Migration Checklist

- [ ] All users imported successfully
- [ ] User login works on VPS
- [ ] Credits balance correct for all users
- [ ] Article Library shows historical articles
- [ ] Image Library shows historical images
- [ ] API integrations configured (OpenAI, WordPress, Perplexity, Anthropic)
- [ ] Scheduled posts configured correctly
- [ ] Test post creation works
- [ ] Email notifications working
- [ ] SQL export file deleted from both machines
- [ ] Backup of VPS database created

## Automatic Migration Script (VPS)

For convenience, here's a complete VPS-side script:

```bash
#!/bin/bash
# File: import_user_data.sh
# Run on VPS to import user data

set -e  # Exit on error

# Configuration
DB_USER="${DB_USERNAME}"
DB_PASS="${DB_PASSWORD}"
DB_NAME="${DB_NAME}"
SQL_FILE="users_export.sql"

echo "=== EZWAI SMM User Data Import ==="
echo ""

# Check SQL file exists
if [ ! -f "$SQL_FILE" ]; then
    echo "❌ Error: $SQL_FILE not found"
    echo "Upload the file from your local machine first"
    exit 1
fi

# Backup existing data
echo "📦 Creating backup..."
BACKUP_FILE="backup_before_import_$(date +%Y%m%d_%H%M%S).sql"
mysqldump -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" > "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"
echo ""

# Import data
echo "📥 Importing user data..."
mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$SQL_FILE"
echo "✅ Import complete"
echo ""

# Verify import
echo "📊 Verifying import..."
USER_COUNT=$(mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -sN -e "SELECT COUNT(*) FROM user;")
JOB_COUNT=$(mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -sN -e "SELECT COUNT(*) FROM completed_job;")
TRANS_COUNT=$(mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -sN -e "SELECT COUNT(*) FROM credit_transaction;")
ARTICLE_COUNT=$(mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -sN -e "SELECT COUNT(*) FROM articles;")
IMAGE_COUNT=$(mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -sN -e "SELECT COUNT(*) FROM images;")

echo "   - $USER_COUNT users"
echo "   - $JOB_COUNT completed jobs"
echo "   - $TRANS_COUNT credit transactions"
echo "   - $ARTICLE_COUNT articles"
echo "   - $IMAGE_COUNT images"
echo ""

echo "✅ Migration complete!"
echo ""
echo "Next steps:"
echo "1. Test login at http://YOUR_VPS_IP:5001"
echo "2. Verify user data in dashboard"
echo "3. Delete SQL file: rm $SQL_FILE"
echo ""
```

## Summary

This migration process:
1. ✅ Exports all users from local SQLite
2. ✅ Transfers data to VPS securely
3. ✅ Imports into VPS MySQL/MariaDB
4. ✅ Preserves all relationships (users → articles → images)
5. ✅ Maintains credit balances and transaction history
6. ✅ Keeps WordPress integrations configured

**Estimated Time:** 10-15 minutes

**Data Preserved:**
- User accounts (username, email, password hashes)
- API credentials (OpenAI, WordPress, Perplexity, Anthropic)
- Credit balances and transaction history
- Topic queries and system prompts
- Scheduled post configurations
- Article library with full HTML content
- Image library with prompts and metadata
- Brand colors and writing styles

After migration, users can immediately login to VPS with their existing credentials and continue using the platform without reconfiguration.
