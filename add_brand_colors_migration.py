"""
Database migration script to add brand color fields to User model.

Run this once to add the brand customization columns to existing database.
"""
from app_v3 import app, db
from sqlalchemy import text

def migrate_brand_colors():
    """Add brand color columns to users table"""
    with app.app_context():
        try:
            # Check if columns already exist
            result = db.session.execute(text("DESCRIBE user"))
            existing_columns = [row[0] for row in result]

            columns_to_add = [
                ("brand_primary_color", "VARCHAR(7) DEFAULT '#08b2c6'"),
                ("brand_accent_color", "VARCHAR(7) DEFAULT '#ff6b11'"),
                ("use_default_branding", "TINYINT(1) DEFAULT 1")
            ]

            for col_name, col_type in columns_to_add:
                if col_name not in existing_columns:
                    print(f"Adding column: {col_name}")
                    db.session.execute(
                        text(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")
                    )
                    db.session.commit()
                    print(f"✅ Added {col_name}")
                else:
                    print(f"⏭️  Column {col_name} already exists")

            print("\n✅ Migration complete!")

        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    print("=" * 60)
    print("EZWAI SMM - Brand Colors Migration")
    print("=" * 60)
    print("\nThis will add brand customization fields to the User model:")
    print("  - brand_primary_color (VARCHAR(7))")
    print("  - brand_accent_color (VARCHAR(7))")
    print("  - use_default_branding (BOOLEAN)")
    print("\n" + "=" * 60)

    response = input("\nProceed with migration? (yes/no): ")
    if response.lower() == 'yes':
        migrate_brand_colors()
    else:
        print("Migration cancelled.")
