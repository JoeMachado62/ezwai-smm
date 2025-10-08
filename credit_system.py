"""
Credit System Module for EZWAI SMM
Handles credit balance management, transactions, and Stripe integration
"""
import logging
import os
from typing import Tuple, Optional
from datetime import datetime
import stripe

logger = logging.getLogger(__name__)

# Initialize Stripe with API key from environment
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Pricing configuration
ARTICLE_COST = 1.99  # Cost per article generation
WELCOME_CREDIT = 5.00  # Welcome credit for new users
MIN_PURCHASE = 10.00  # Minimum credit purchase

def check_sufficient_credits(user) -> Tuple[bool, str]:
    """
    Check if user has enough credits for an article

    Args:
        user: User model instance

    Returns:
        Tuple of (has_credits: bool, message: str)
    """
    # Admin users have unlimited credits
    if user.is_admin:
        return True, ""

    # Handle legacy users with NULL credit_balance
    if user.credit_balance is None:
        return False, f"Credit balance not initialized. Please contact support or run migration script."

    if user.credit_balance >= ARTICLE_COST:
        return True, ""
    else:
        needed = ARTICLE_COST - user.credit_balance
        return False, f"Insufficient credits. You need ${needed:.2f} more. Current balance: ${user.credit_balance:.2f}"


def deduct_credits(user, db) -> bool:
    """
    Deduct article cost from user's balance and log transaction

    Args:
        user: User model instance
        db: SQLAlchemy database instance

    Returns:
        bool: True if successful, False otherwise
    """
    from app_v3 import CreditTransaction

    try:
        # Handle legacy users with NULL fields
        if user.credit_balance is None:
            user.credit_balance = 0.00
        if user.total_articles_generated is None:
            user.total_articles_generated = 0
        if user.total_spent is None:
            user.total_spent = 0.00

        # Admin users don't get charged (unlimited credits)
        if not user.is_admin:
            user.credit_balance -= ARTICLE_COST
            user.total_spent += ARTICLE_COST

        user.total_articles_generated += 1

        # Log transaction
        transaction = CreditTransaction(
            user_id=user.id,
            amount=-ARTICLE_COST if not user.is_admin else 0,
            transaction_type='article_generation' if not user.is_admin else 'admin_article_generation',
            balance_after=user.credit_balance,
            description=f'Article generation (#{user.total_articles_generated})' + (' [ADMIN - FREE]' if user.is_admin else '')
        )
        db.session.add(transaction)
        db.session.commit()

        if user.is_admin:
            logger.info(f"[Credits] ADMIN user {user.id} generated article (no charge). Balance unchanged: ${user.credit_balance:.2f}")
        else:
            logger.info(f"[Credits] Deducted ${ARTICLE_COST} from user {user.id}. New balance: ${user.credit_balance:.2f}")

        # Check if auto-recharge needed
        if user.auto_recharge_enabled and user.credit_balance < user.auto_recharge_threshold:
            logger.info(f"[Credits] User {user.id} balance ${user.credit_balance:.2f} below threshold ${user.auto_recharge_threshold:.2f}")
            trigger_auto_recharge(user, db)

        return True
    except Exception as e:
        logger.error(f"[Credits] Error deducting credits for user {user.id}: {e}")
        db.session.rollback()
        return False


def refund_credits(user, db, reason: str = "Article generation failed") -> bool:
    """
    Refund article cost if generation fails

    Args:
        user: User model instance
        db: SQLAlchemy database instance
        reason: Reason for refund

    Returns:
        bool: True if successful, False otherwise
    """
    from app_v3 import CreditTransaction

    try:
        # Handle legacy users with NULL fields
        if user.credit_balance is None:
            user.credit_balance = 0.00
        if user.total_articles_generated is None:
            user.total_articles_generated = 0
        if user.total_spent is None:
            user.total_spent = 0.00

        user.credit_balance += ARTICLE_COST
        user.total_articles_generated -= 1  # Reverse the increment
        user.total_spent -= ARTICLE_COST

        # Log refund transaction
        transaction = CreditTransaction(
            user_id=user.id,
            amount=ARTICLE_COST,
            transaction_type='refund',
            balance_after=user.credit_balance,
            description=f'Refund: {reason}'
        )
        db.session.add(transaction)
        db.session.commit()

        logger.info(f"[Credits] Refunded ${ARTICLE_COST} to user {user.id}. New balance: ${user.credit_balance:.2f}")
        return True
    except Exception as e:
        logger.error(f"[Credits] Error refunding credits for user {user.id}: {e}")
        db.session.rollback()
        return False


def trigger_auto_recharge(user, db):
    """
    Trigger automatic credit recharge via Stripe

    Args:
        user: User model instance
        db: SQLAlchemy database instance
    """
    from app_v3 import CreditTransaction
    from email_notification import send_email_notification

    try:
        if not user.stripe_payment_method_id:
            logger.warning(f"[Auto-Recharge] User {user.id} has no payment method configured")
            # Send email notification to add payment method
            try:
                send_email_notification(
                    user.email,
                    "Add Payment Method for Auto-Recharge",
                    f"Your EZWAI SMM balance is ${user.credit_balance:.2f}. Add a payment method to enable auto-recharge."
                )
            except:
                pass
            return

        # Create Stripe payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(user.auto_recharge_amount * 100),  # Convert to cents
            currency='usd',
            customer=user.stripe_customer_id,
            payment_method=user.stripe_payment_method_id,
            off_session=True,  # Payment without user present
            confirm=True,
            description=f'Auto-recharge ${user.auto_recharge_amount:.2f} for user {user.id}',
            metadata={
                'user_id': user.id,
                'type': 'auto_recharge'
            }
        )

        if intent.status == 'succeeded':
            # Add credits
            user.credit_balance += user.auto_recharge_amount

            # Log transaction
            transaction = CreditTransaction(
                user_id=user.id,
                amount=user.auto_recharge_amount,
                transaction_type='auto_recharge',
                stripe_payment_intent_id=intent.id,
                balance_after=user.credit_balance,
                description=f'Auto-recharge ${user.auto_recharge_amount:.2f}'
            )
            db.session.add(transaction)
            db.session.commit()

            logger.info(f"[Auto-Recharge] Successfully added ${user.auto_recharge_amount} to user {user.id}")

            # Send email notification
            try:
                send_email_notification(
                    user.email,
                    "Auto-Recharge Successful",
                    f"Your account was automatically recharged with ${user.auto_recharge_amount:.2f}. New balance: ${user.credit_balance:.2f}"
                )
            except Exception as email_error:
                logger.error(f"[Auto-Recharge] Email notification failed: {email_error}")

    except stripe.error.CardError as e:
        logger.error(f"[Auto-Recharge] Card error for user {user.id}: {e.user_message}")
        # Send email notification about failed recharge
        try:
            send_email_notification(
                user.email,
                "Auto-Recharge Failed",
                f"Your auto-recharge of ${user.auto_recharge_amount:.2f} failed: {e.user_message}. Please update your payment method."
            )
        except:
            pass

    except Exception as e:
        logger.error(f"[Auto-Recharge] Error for user {user.id}: {e}")


def add_credits_manual(user_id: int, amount: float, payment_intent_id: str, db) -> bool:
    """
    Add credits after successful manual purchase

    Args:
        user_id: User ID
        amount: Credit amount to add
        payment_intent_id: Stripe payment intent ID
        db: SQLAlchemy database instance

    Returns:
        bool: True if successful, False otherwise
    """
    from app_v3 import User, CreditTransaction

    try:
        user = User.query.get(user_id)
        if not user:
            logger.error(f"[Credits] User {user_id} not found")
            return False

        user.credit_balance += amount

        transaction = CreditTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type='purchase',
            stripe_payment_intent_id=payment_intent_id,
            balance_after=user.credit_balance,
            description=f'Credit purchase ${amount:.2f}'
        )
        db.session.add(transaction)
        db.session.commit()

        logger.info(f"[Credits] Added ${amount:.2f} to user {user_id}. New balance: ${user.credit_balance:.2f}")
        return True
    except Exception as e:
        logger.error(f"[Credits] Error adding credits to user {user_id}: {e}")
        db.session.rollback()
        return False


def add_welcome_credit(user_id: int, db) -> bool:
    """
    Add welcome credit to new user

    Args:
        user_id: User ID
        db: SQLAlchemy database instance

    Returns:
        bool: True if successful, False otherwise
    """
    from app_v3 import User, CreditTransaction

    try:
        user = User.query.get(user_id)
        if not user:
            logger.error(f"[Credits] User {user_id} not found")
            return False

        # Check if welcome credit already given
        existing_welcome = CreditTransaction.query.filter_by(
            user_id=user_id,
            transaction_type='welcome'
        ).first()

        if existing_welcome:
            logger.warning(f"[Credits] User {user_id} already received welcome credit")
            return False

        # Add welcome credit
        user.credit_balance = WELCOME_CREDIT

        transaction = CreditTransaction(
            user_id=user_id,
            amount=WELCOME_CREDIT,
            transaction_type='welcome',
            balance_after=WELCOME_CREDIT,
            description=f'Welcome credit ${WELCOME_CREDIT:.2f}'
        )
        db.session.add(transaction)
        db.session.commit()

        logger.info(f"[Credits] Added welcome credit ${WELCOME_CREDIT:.2f} to user {user_id}")
        return True
    except Exception as e:
        logger.error(f"[Credits] Error adding welcome credit to user {user_id}: {e}")
        db.session.rollback()
        return False


def get_transaction_history(user_id: int, limit: int = 50) -> list:
    """
    Get transaction history for user

    Args:
        user_id: User ID
        limit: Maximum number of transactions to return

    Returns:
        list: List of transaction dictionaries
    """
    from app_v3 import CreditTransaction

    try:
        transactions = CreditTransaction.query.filter_by(user_id=user_id)\
            .order_by(CreditTransaction.created_at.desc())\
            .limit(limit)\
            .all()

        return [{
            'id': t.id,
            'amount': t.amount,
            'type': t.transaction_type,
            'description': t.description,
            'balance_after': t.balance_after,
            'date': t.created_at.isoformat(),
            'stripe_payment_intent_id': t.stripe_payment_intent_id
        } for t in transactions]
    except Exception as e:
        logger.error(f"[Credits] Error fetching transaction history for user {user_id}: {e}")
        return []


def get_credit_stats(user_id: int) -> dict:
    """
    Get credit statistics for user

    Args:
        user_id: User ID

    Returns:
        dict: Statistics including balance, total spent, articles generated
    """
    from app_v3 import User, CreditTransaction

    try:
        user = User.query.get(user_id)
        if not user:
            return {}

        total_purchases = db.session.query(db.func.sum(CreditTransaction.amount))\
            .filter(
                CreditTransaction.user_id == user_id,
                CreditTransaction.transaction_type.in_(['purchase', 'welcome', 'auto_recharge'])
            ).scalar() or 0

        return {
            'current_balance': user.credit_balance,
            'total_spent': user.total_spent,
            'total_articles': user.total_articles_generated,
            'total_purchased': total_purchases,
            'auto_recharge_enabled': user.auto_recharge_enabled,
            'auto_recharge_amount': user.auto_recharge_amount,
            'auto_recharge_threshold': user.auto_recharge_threshold,
            'average_cost_per_article': user.total_spent / user.total_articles_generated if user.total_articles_generated > 0 else 0
        }
    except Exception as e:
        logger.error(f"[Credits] Error fetching stats for user {user_id}: {e}")
        return {}
