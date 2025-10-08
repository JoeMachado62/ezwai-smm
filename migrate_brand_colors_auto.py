"""
Automatic database migration script to add brand color fields to User model.
Runs without user confirmation.
"""
from app_v3 import app, db
from sqlalchemy import text

def migrate_brand_colors():
    """Add brand color columns to users table"""
    with app.app_context():
        try:
            # Check if columns already exist
            result = db.session.execute(text("PRAGMA table_info(user)"))
            existing_columns = [row[1] for row in result]

            columns_to_add = [
                ("brand_primary_color", "VARCHAR(7) DEFAULT '#08b2c6'"),
                ("brand_accent_color", "VARCHAR(7) DEFAULT '#ff6b11'"),
                ("use_default_branding", "INTEGER DEFAULT 1")  # SQLite uses INTEGER for BOOLEAN
            ]

            added_count = 0
            for col_name, col_type in columns_to_add:
                if col_name not in existing_columns:
                    print(f"Adding column: {col_name}")
                    db.session.execute(
                        text(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")
                    )
                    db.session.commit()
                    print(f"[OK] Added {col_name}")
                    added_count += 1
                else:
                    print(f"[SKIP] Column {col_name} already exists")

            if added_count > 0:
                print(f"\n[SUCCESS] Migration complete! Added {added_count} columns.")
            else:
                print("\n[SUCCESS] All columns already exist. No changes needed.")

        except Exception as e:
            print(f"\n[ERROR] Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    print("=" * 60)
    print("EZWAI SMM - Brand Colors Migration (Auto)")
    print("=" * 60)
    migrate_brand_colors()
