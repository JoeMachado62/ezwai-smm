"""
Migration script to add default credit values to existing users
Run this once to fix existing users without credit_balance
"""
import logging
from app_v3 import app, db, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_credit_fields():
    """Add default credit values to existing users"""
    with app.app_context():
        try:
            # Find users with NULL credit fields
            users = User.query.all()
            updated_count = 0

            for user in users:
                needs_update = False

                # Set credit_balance if NULL
                if user.credit_balance is None:
                    # Admin users get unlimited credits
                    if user.is_admin:
                        user.credit_balance = 999999.99
                        logger.info(f"Setting credit_balance=999999.99 (unlimited) for ADMIN user {user.id} ({user.email})")
                    else:
                        user.credit_balance = 5.00  # Welcome credit
                        logger.info(f"Setting credit_balance=5.00 for user {user.id} ({user.email})")
                    needs_update = True

                # Set auto_recharge fields if NULL
                if user.auto_recharge_enabled is None:
                    user.auto_recharge_enabled = False
                    needs_update = True

                if user.auto_recharge_amount is None:
                    user.auto_recharge_amount = 10.00
                    needs_update = True

                if user.auto_recharge_threshold is None:
                    user.auto_recharge_threshold = 2.50
                    needs_update = True

                if user.total_articles_generated is None:
                    user.total_articles_generated = 0
                    needs_update = True

                if user.total_spent is None:
                    user.total_spent = 0.00
                    needs_update = True

                if needs_update:
                    updated_count += 1

            # Commit all changes
            if updated_count > 0:
                db.session.commit()
                logger.info(f"✓ Successfully updated {updated_count} user(s) with default credit values")
            else:
                logger.info("✓ All users already have credit fields set")

            # Display summary
            print("\n=== User Credit Summary ===")
            for user in User.query.all():
                print(f"User {user.id} ({user.email}): ${user.credit_balance:.2f}")

        except Exception as e:
            logger.error(f"✗ Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    print("Starting credit field migration...")
    migrate_credit_fields()
    print("Migration complete!")
