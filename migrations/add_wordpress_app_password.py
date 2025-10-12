"""
Migration: Add wordpress_app_password column and remove old JWT fields
Run: python migrations/add_wordpress_app_password.py
"""

import sys
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

def migrate():
    """Add wordpress_app_password column and remove JWT authentication fields"""

    # Get database URI from environment or use SQLite default
    database_uri = os.getenv('DATABASE_URL', 'sqlite:///ezwai_smm.db')
    engine = create_engine(database_uri)

    with engine.begin() as conn:  # Use begin() for auto-commit
        print("Starting WordPress Application Password migration...")

        # Step 1: Add new column
        print("1. Adding wordpress_app_password column...")
        try:
            conn.execute(text("""
                ALTER TABLE user
                ADD COLUMN wordpress_app_password VARCHAR(255) DEFAULT NULL
            """))
            print("   [OK] Column added successfully")
        except Exception as e:
            if "Duplicate column name" in str(e) or "duplicate column" in str(e).lower():
                print("   [SKIP] Column already exists, skipping...")
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
            print(f"   [WARN] Found {len(users_to_migrate)} users with WordPress credentials")
            print("   -> These users will need to create Application Passwords")
            print("   -> Their existing credentials will be cleared")

            # Log users who need to reconfigure
            with open('wordpress_migration_users.log', 'w', encoding='utf-8') as f:
                f.write("Users who need to reconfigure WordPress:\n")
                f.write("=" * 60 + "\n")
                for user in users_to_migrate:
                    f.write(f"User ID: {user[0]}, Email: {user[1]}, Username: {user[2]}\n")

            print(f"   -> List saved to: wordpress_migration_users.log")
        else:
            print("   [OK] No existing WordPress users found")

        # Step 3: Remove old columns
        print("3. Removing old JWT authentication columns...")
        try:
            conn.execute(text("ALTER TABLE user DROP COLUMN wordpress_username"))
            print("   [OK] wordpress_username column removed")
        except Exception as e:
            if "Can't DROP" in str(e) or "no such column" in str(e).lower():
                print("   [SKIP] wordpress_username column already removed or doesn't exist")
            else:
                raise

        try:
            conn.execute(text("ALTER TABLE user DROP COLUMN wordpress_password"))
            print("   [OK] wordpress_password column removed")
        except Exception as e:
            if "Can't DROP" in str(e) or "no such column" in str(e).lower():
                print("   [SKIP] wordpress_password column already removed or doesn't exist")
            else:
                raise

        print("\n" + "=" * 60)
        print("[SUCCESS] Migration completed successfully!")
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
        print(f"\n[ERROR] Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
