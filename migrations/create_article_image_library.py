"""
Create Article and Image Library Tables

Migration to add:
1. articles table - Store all generated articles with metadata
2. images table - Store all generated images with prompts

Run with: python migrations/create_article_image_library.py
"""

import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def run_migration():
    """Create articles and images tables"""

    # Get database connection
    db_username = os.getenv('DB_USERNAME')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')

    if not all([db_username, db_password, db_host, db_name]):
        print("❌ Missing database configuration in .env")
        return False

    connection_string = f"mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_name}?charset=utf8mb4"
    engine = create_engine(connection_string)

    print("\n" + "="*60)
    print("Article & Image Library Migration")
    print("="*60 + "\n")

    try:
        with engine.connect() as conn:
            # Create articles table
            print("Creating 'articles' table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    content_html MEDIUMTEXT NOT NULL,
                    hero_image_url VARCHAR(1000),
                    section_images JSON,
                    word_count INT,
                    status ENUM('draft', 'published', 'scheduled', 'failed', 'local') DEFAULT 'draft',
                    generation_mode ENUM('wordpress', 'local') DEFAULT 'wordpress',
                    wordpress_post_id INT,
                    wordpress_url VARCHAR(1000),
                    metadata JSON,
                    backup_file_path VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at),
                    INDEX idx_status (status),
                    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            conn.commit()
            print("✓ 'articles' table created")

            # Create images table
            print("\nCreating 'images' table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS images (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    article_id INT,
                    image_url VARCHAR(1000) NOT NULL,
                    image_type ENUM('hero', 'section') DEFAULT 'section',
                    prompt TEXT NOT NULL,
                    model VARCHAR(100) DEFAULT 'seedream-4',
                    aspect_ratio VARCHAR(20),
                    replicate_prediction_id VARCHAR(100),
                    file_size_kb INT,
                    cost_usd DECIMAL(10, 4) DEFAULT 0.0750,
                    tags JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    INDEX idx_user_id (user_id),
                    INDEX idx_article_id (article_id),
                    INDEX idx_created_at (created_at),
                    INDEX idx_image_type (image_type),
                    FULLTEXT idx_prompt (prompt),
                    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            conn.commit()
            print("✓ 'images' table created")

            # Verify tables
            print("\nVerifying tables...")
            result = conn.execute(text("SHOW TABLES LIKE 'articles'"))
            articles_exists = result.fetchone() is not None

            result = conn.execute(text("SHOW TABLES LIKE 'images'"))
            images_exists = result.fetchone() is not None

            if articles_exists and images_exists:
                print("✓ Both tables verified successfully")

                # Show table structures
                print("\n" + "="*60)
                print("Articles Table Structure:")
                print("="*60)
                result = conn.execute(text("DESCRIBE articles"))
                for row in result:
                    print(f"  {row[0]:<25} {row[1]:<30} {row[2]}")

                print("\n" + "="*60)
                print("Images Table Structure:")
                print("="*60)
                result = conn.execute(text("DESCRIBE images"))
                for row in result:
                    print(f"  {row[0]:<25} {row[1]:<30} {row[2]}")

                print("\n" + "="*60)
                print("✅ Migration completed successfully!")
                print("="*60)
                print("\nNext steps:")
                print("1. Update openai_integration_v4.py to save articles/images to database")
                print("2. Create API endpoints for retrieving articles and images")
                print("3. Add Article Library and Image Library tabs to dashboard")
                print("")

                return True
            else:
                print("❌ Table verification failed")
                return False

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
