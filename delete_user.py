"""
Utility script to delete a user and all associated data
Usage: python delete_user.py <email>
"""
import sys
from app_v3 import app, db, User, CreditTransaction, CompletedJob

def delete_user_by_email(email: str):
    """Delete user and all associated data"""
    with app.app_context():
        user = User.query.filter_by(email=email).first()

        if not user:
            print(f"❌ User not found: {email}")
            return False

        print(f"\n⚠️  WARNING: About to delete user:")
        print(f"   Email: {user.email}")
        print(f"   ID: {user.id}")
        print(f"   Credit Balance: {user.credit_balance}")
        print(f"   Total Articles: {user.total_articles_generated}")
        print()

        confirm = input("Type 'DELETE' to confirm: ")
        if confirm != 'DELETE':
            print("❌ Deletion cancelled")
            return False

        try:
            # Delete associated records
            CreditTransaction.query.filter_by(user_id=user.id).delete()
            CompletedJob.query.filter_by(user_id=user.id).delete()

            # Delete user
            db.session.delete(user)
            db.session.commit()

            print(f"✅ Successfully deleted user: {email}")
            return True

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error deleting user: {e}")
            return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python delete_user.py <email>")
        sys.exit(1)

    email = sys.argv[1]
    delete_user_by_email(email)
