"""
Export users from local SQLite database to SQL file for VPS MySQL import
Exports: User, CompletedJob, CreditTransaction, Article, Image tables
"""
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load environment
load_dotenv()

# Import app and database
from app_v3 import app, db
from app_v3 import User, CompletedJob, CreditTransaction, Article, Image

def escape_string(value):
    """Escape string values for SQL INSERT statements"""
    if value is None:
        return 'NULL'
    if isinstance(value, str):
        # Escape single quotes and backslashes
        escaped = value.replace('\\', '\\\\').replace("'", "\\'")
        return f"'{escaped}'"
    if isinstance(value, bool):
        return '1' if value else '0'
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, datetime):
        return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
    return f"'{str(value)}'"

def export_users_to_sql(output_file='users_export.sql'):
    """Export all users and related data to SQL file"""
    with app.app_context():
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write("-- EZWAI SMM User Data Export\n")
            f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-- Import this file into VPS MySQL/MariaDB database\n\n")

            f.write("SET FOREIGN_KEY_CHECKS=0;\n\n")

            # Export Users
            users = User.query.all()
            f.write(f"-- Exporting {len(users)} users\n")

            for user in users:
                # Build INSERT statement for User (based on actual User model fields)
                columns = [
                    'id', 'email', 'password_hash', 'first_name', 'last_name',
                    'phone', 'billing_address',
                    'openai_api_key', 'wordpress_rest_api_url', 'wordpress_app_password',
                    'perplexity_api_token', 'queries', 'system_prompt', 'schedule',
                    'specific_topic_queries', 'writing_styles', 'last_query_index',
                    'brand_primary_color', 'brand_accent_color', 'use_default_branding',
                    'email_verified', 'verification_code', 'verification_code_expiry', 'verification_attempts',
                    'credit_balance', 'auto_recharge_enabled', 'auto_recharge_amount', 'auto_recharge_threshold',
                    'stripe_customer_id', 'stripe_payment_method_id', 'is_admin',
                    'total_articles_generated', 'total_spent', 'created_at'
                ]

                values = [
                    escape_string(user.id),
                    escape_string(user.email),
                    escape_string(user.password_hash),
                    escape_string(user.first_name),
                    escape_string(user.last_name),
                    escape_string(user.phone),
                    escape_string(user.billing_address),
                    escape_string(user.openai_api_key),
                    escape_string(user.wordpress_rest_api_url),
                    escape_string(user.wordpress_app_password),
                    escape_string(user.perplexity_api_token),
                    escape_string(user.queries),
                    escape_string(user.system_prompt),
                    escape_string(user.schedule),
                    escape_string(user.specific_topic_queries),
                    escape_string(user.writing_styles),
                    escape_string(user.last_query_index),
                    escape_string(user.brand_primary_color),
                    escape_string(user.brand_accent_color),
                    escape_string(user.use_default_branding),
                    escape_string(user.email_verified),
                    escape_string(user.verification_code),
                    escape_string(user.verification_code_expiry),
                    escape_string(user.verification_attempts),
                    escape_string(user.credit_balance),
                    escape_string(user.auto_recharge_enabled),
                    escape_string(user.auto_recharge_amount),
                    escape_string(user.auto_recharge_threshold),
                    escape_string(user.stripe_customer_id),
                    escape_string(user.stripe_payment_method_id),
                    escape_string(user.is_admin),
                    escape_string(user.total_articles_generated),
                    escape_string(user.total_spent),
                    escape_string(user.created_at)
                ]

                f.write(f"INSERT INTO user ({', '.join(columns)}) VALUES ({', '.join(values)});\n")

            f.write("\n")

            # Export CompletedJobs
            jobs = CompletedJob.query.all()
            f.write(f"-- Exporting {len(jobs)} completed jobs\n")

            for job in jobs:
                columns = ['id', 'user_id', 'scheduled_time', 'completed_time', 'post_title']
                values = [
                    escape_string(job.id),
                    escape_string(job.user_id),
                    escape_string(job.scheduled_time),
                    escape_string(job.completed_time),
                    escape_string(job.post_title)
                ]
                f.write(f"INSERT INTO completed_job ({', '.join(columns)}) VALUES ({', '.join(values)});\n")

            f.write("\n")

            # Export CreditTransactions
            transactions = CreditTransaction.query.all()
            f.write(f"-- Exporting {len(transactions)} credit transactions\n")

            for trans in transactions:
                columns = ['id', 'user_id', 'amount', 'transaction_type',
                          'stripe_payment_intent_id', 'balance_after', 'description', 'created_at']
                values = [
                    escape_string(trans.id),
                    escape_string(trans.user_id),
                    escape_string(trans.amount),
                    escape_string(trans.transaction_type),
                    escape_string(trans.stripe_payment_intent_id),
                    escape_string(trans.balance_after),
                    escape_string(trans.description),
                    escape_string(trans.created_at)
                ]
                f.write(f"INSERT INTO credit_transactions ({', '.join(columns)}) VALUES ({', '.join(values)});\n")

            f.write("\n")

            # Export Articles (skip if table doesn't exist)
            try:
                articles = Article.query.all()
                f.write(f"-- Exporting {len(articles)} articles\n")
            except Exception as e:
                logger.warning(f"Articles table not found, skipping: {e}")
                articles = []
                f.write("-- Articles table not found, skipping\n")

            for article in articles:
                columns = ['id', 'user_id', 'title', 'content_html', 'hero_image_url',
                          'section_images', 'word_count', 'status', 'generation_mode',
                          'wordpress_post_id', 'wordpress_url', 'article_metadata',
                          'backup_file_path', 'created_at', 'updated_at']
                values = [
                    escape_string(article.id),
                    escape_string(article.user_id),
                    escape_string(article.title),
                    escape_string(article.content_html),
                    escape_string(article.hero_image_url),
                    escape_string(article.section_images),
                    escape_string(article.word_count),
                    escape_string(article.status),
                    escape_string(article.generation_mode),
                    escape_string(article.wordpress_post_id),
                    escape_string(article.wordpress_url),
                    escape_string(article.article_metadata),
                    escape_string(article.backup_file_path),
                    escape_string(article.created_at),
                    escape_string(article.updated_at)
                ]
                f.write(f"INSERT INTO articles ({', '.join(columns)}) VALUES ({', '.join(values)});\n")

            f.write("\n")

            # Export Images (skip if table doesn't exist)
            try:
                images = Image.query.all()
                f.write(f"-- Exporting {len(images)} images\n")
            except Exception as e:
                logger.warning(f"Images table not found, skipping: {e}")
                images = []
                f.write("-- Images table not found, skipping\n")

            for image in images:
                columns = ['id', 'user_id', 'article_id', 'image_url', 'image_type',
                          'prompt', 'model', 'aspect_ratio', 'replicate_prediction_id',
                          'file_size_kb', 'cost_usd', 'tags', 'created_at']
                values = [
                    escape_string(image.id),
                    escape_string(image.user_id),
                    escape_string(image.article_id),
                    escape_string(image.image_url),
                    escape_string(image.image_type),
                    escape_string(image.prompt),
                    escape_string(image.model),
                    escape_string(image.aspect_ratio),
                    escape_string(image.replicate_prediction_id),
                    escape_string(image.file_size_kb),
                    escape_string(image.cost_usd),
                    escape_string(image.tags),
                    escape_string(image.created_at)
                ]
                f.write(f"INSERT INTO images ({', '.join(columns)}) VALUES ({', '.join(values)});\n")

            f.write("\n")
            f.write("SET FOREIGN_KEY_CHECKS=1;\n")

            print(f"[OK] Export complete: {output_file}")
            print(f"   - {len(users)} users")
            print(f"   - {len(jobs)} completed jobs")
            print(f"   - {len(transactions)} credit transactions")
            print(f"   - {len(articles)} articles")
            print(f"   - {len(images)} images")
            print(f"\nUpload this file to your VPS and import with:")
            print(f"mysql -u {os.getenv('DB_USERNAME', 'YOUR_DB_USER')} -p {os.getenv('DB_NAME', 'YOUR_DB_NAME')} < {output_file}")

if __name__ == '__main__':
    output_file = sys.argv[1] if len(sys.argv) > 1 else 'users_export.sql'
    export_users_to_sql(output_file)
