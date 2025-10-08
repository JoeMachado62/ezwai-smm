"""
Migration script to add writing_styles column to User table.
Run this once to update the database schema.
"""
from app_v3 import app, db
from sqlalchemy import inspect, text

def add_writing_styles_column():
    """Add writing_styles JSON column to User table if it doesn't exist."""
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]

        if 'writing_styles' not in columns:
            print("Adding writing_styles column to User table...")
            with db.engine.connect() as conn:
                # Add column - syntax varies by database
                try:
                    # Try MySQL/MariaDB syntax first
                    conn.execute(text("ALTER TABLE user ADD COLUMN writing_styles JSON"))
                    conn.commit()
                    print("✅ Successfully added writing_styles column (MySQL)")
                except Exception as e1:
                    try:
                        # Try SQLite syntax
                        conn.execute(text("ALTER TABLE user ADD COLUMN writing_styles TEXT"))
                        conn.commit()
                        print("✅ Successfully added writing_styles column (SQLite)")
                    except Exception as e2:
                        print(f"❌ Failed to add column:")
                        print(f"  MySQL attempt: {e1}")
                        print(f"  SQLite attempt: {e2}")
                        return False
        else:
            print("✅ writing_styles column already exists")

        return True

if __name__ == "__main__":
    success = add_writing_styles_column()
    if success:
        print("\n🎉 Migration completed successfully!")
        print("You can now use writing styles with topic queries.")
    else:
        print("\n⚠️  Migration failed. Please check the errors above.")
