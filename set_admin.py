"""
Quick script to promote a user to admin status (unlimited credits)
Usage: python set_admin.py <email>
"""
import sys
import logging
from app_v3 import app, db, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def set_admin(email):
    """Promote user to admin with unlimited credits"""
    with app.app_context():
        try:
            user = User.query.filter_by(email=email).first()
            if not user:
                logger.error(f"✗ User not found: {email}")
                return False

            # Set admin status
            user.is_admin = True
            user.credit_balance = 999999.99  # Unlimited credits

            db.session.commit()
            logger.info(f"✓ User {user.id} ({email}) promoted to ADMIN with unlimited credits")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to set admin: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python set_admin.py <email>")
        sys.exit(1)

    email = sys.argv[1]
    print(f"Promoting {email} to admin...")
    if set_admin(email):
        print("Success!")
    else:
        print("Failed!")
        sys.exit(1)
