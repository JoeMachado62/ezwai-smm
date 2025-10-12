"""
EZWAI SMM V3.0 Scheduler
Updated to use V4 modular integrations with GPT-5-mini + SeeDream-4
"""
import os
import json
from datetime import datetime, timedelta
import pytz
import logging
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from app_v3 import app, db, User, CompletedJob  # V3 imports
from perplexity_ai_integration import query_management, generate_blog_post_ideas
from openai_integration_v4 import create_blog_post_with_images_v4  # V4 modular refactor (feature parity with V3)
from wordpress_integration import create_wordpress_post
from email_notification import send_email_notification

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_blog_post(user_id):
    """
    V4 blog post creation for scheduled jobs
    Uses GPT-5-mini reasoning + SeeDream-4 2K images
    """
    with app.app_context():
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None, "User not found"

            query, writing_style = query_management(user_id)
            if not query:
                logger.error(f"No valid query found for user {user_id}")
                return None, "No valid query found for user"

            logger.info(f"[V3 Scheduler] Using query for user {user_id}: {query}")
            logger.info(f"[V3 Scheduler] Writing style: {writing_style or 'Default'}")

            blog_post_ideas = generate_blog_post_ideas(query, user_id, writing_style)
            if not blog_post_ideas:
                logger.error(f"No blog post ideas generated for user {user_id}")
                return None, "No blog post ideas generated"

            perplexity_research = blog_post_ideas[0]
            system_prompt = user.system_prompt or "Write a comprehensive, engaging article in a professional but conversational tone suitable for a business magazine."

            logger.info(f"[V3 Scheduler] Creating magazine-style blog post with GPT-5-mini reasoning...")
            logger.info(f"Research: {perplexity_research[:100]}...")

            # Use V4 function with GPT-5-mini + SeeDream-4
            # V4 signature: (perplexity_research, user_id, user_system_prompt, writing_style)
            processed_post, error = create_blog_post_with_images_v4(
                perplexity_research, user_id, system_prompt, writing_style
            )
            if error:
                logger.error(f"Error in create_blog_post_with_images_v4 for user {user_id}: {error}")
                return None, error

            title = processed_post['title']
            blog_post_content = processed_post['content']
            image_url = processed_post['hero_image_url']

            logger.info(f"[V3 Scheduler] Article created. Images: {len([img for img in processed_post['all_images'] if img])}")

            # Scheduled posts ALWAYS use WordPress mode (never local mode)
            # Handle WordPress upload with failure protection
            wordpress_url = user.wordpress_rest_api_url.rstrip('/') if user.wordpress_rest_api_url else None
            if wordpress_url:
                if wordpress_url.endswith('/wp-json/wp/v2'):
                    wordpress_url = wordpress_url[:-len('/wp-json/wp/v2')]
                elif wordpress_url.endswith('/wp-json'):
                    wordpress_url = wordpress_url[:-len('/wp-json')]

            try:
                post = create_wordpress_post(title, blog_post_content, user_id, image_url)

                if not post:
                    # WordPress upload failed - send failure email with article
                    logger.error(f"[Scheduler] WordPress post creation failed for user {user_id}")

                    from email_notification import send_wordpress_failure_notification
                    error_details = {
                        "error_message": "Scheduled post: WordPress upload failed - check credentials",
                        "failure_point": "article_creation",
                        "technical_details": "create_wordpress_post() returned None for scheduled post.\n"
                                           "This affects automated scheduling. Fix credentials urgently.",
                        "resolution_steps": [
                            "URGENT: This was a SCHEDULED post - fix credentials to prevent future failures",
                            "Log into WordPress dashboard to verify credentials",
                            "Go to Users → Profile → Application Passwords",
                            "Generate new Application Password if needed",
                            "Update credentials in dashboard settings",
                            "Manual upload: Open attached HTML and paste into WordPress"
                        ]
                    }

                    send_wordpress_failure_notification(
                        title=title,
                        article_html=blog_post_content,
                        user_email=user.email,
                        error_details=error_details,
                        wordpress_url=wordpress_url
                    )

                    return None, "Failed to create WordPress post (scheduled) - article emailed"

            except Exception as e:
                # WordPress upload exception - send failure email
                logger.error(f"[Scheduler] WordPress upload exception for user {user_id}: {str(e)}")

                from email_notification import send_wordpress_failure_notification
                error_details = {
                    "error_message": f"Scheduled post: WordPress error: {str(e)[:200]}",
                    "failure_point": "wordpress_upload",
                    "technical_details": f"Exception during scheduled post:\n{str(e)}\n\nType: {type(e).__name__}",
                    "resolution_steps": [
                        "URGENT: This was a SCHEDULED post - fix credentials to prevent future failures",
                        "Check WordPress credentials in dashboard",
                        "Verify WordPress site is accessible",
                        "Check WordPress error logs",
                        "Manual upload: Open attached HTML and paste into WordPress"
                    ]
                }

                send_wordpress_failure_notification(
                    title=title,
                    article_html=blog_post_content,
                    user_email=user.email,
                    error_details=error_details,
                    wordpress_url=wordpress_url
                )

                return None, f"WordPress upload failed (scheduled): {str(e)} - article emailed"

            # Send email notification with HTML attachment
            from email_notification import send_article_notification_with_attachment
            email_sent = send_article_notification_with_attachment(
                title=post['title']['rendered'],
                article_html=blog_post_content,  # Full HTML with styling
                hero_image_url=image_url,
                user_email=user.email,
                mode="wordpress",
                wordpress_url=wordpress_url,
                post_id=post['id']
            )

            if not email_sent:
                logger.warning(f"Failed to send email notification for user {user_id}")
                post['email_notification_sent'] = False
            else:
                post['email_notification_sent'] = True

            return post, None
        except Exception as e:
            logger.error(f"Unexpected error in create_blog_post for user {user_id}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None, str(e)

def check_and_trigger_jobs():
    """
    Check schedules and trigger blog post creation
    Compatible with V3 article generation
    """
    with app.app_context():
        try:
            eastern_tz = pytz.timezone('US/Eastern')
            now = datetime.now(eastern_tz)
            logger.info(f"[V3 Scheduler] Checking schedules at {now.strftime('%Y-%m-%d %H:%M:%S')} EST")

            # Time window: 2 minutes before to 5 minutes after
            start_time = now - timedelta(minutes=2)
            end_time = now + timedelta(minutes=5)

            users = User.query.all()
            for user in users:
                if not user.schedule:
                    continue

                schedule = json.loads(user.schedule) if isinstance(user.schedule, str) else user.schedule
                if not isinstance(schedule, list) or len(schedule) != 7:
                    logger.warning(f"Invalid schedule format for user {user.id}")
                    continue

                current_day = now.weekday()
                day_schedule = schedule[current_day]

                if not day_schedule['enabled']:
                    continue

                for time_slot in ['time1', 'time2']:
                    if not day_schedule[time_slot]:
                        continue

                    scheduled_time = datetime.strptime(day_schedule[time_slot], "%H:%M").time()
                    scheduled_datetime = eastern_tz.localize(
                        datetime.combine(now.date(), scheduled_time)
                    )

                    if start_time <= scheduled_datetime <= end_time:
                        job = CompletedJob.query.filter_by(user_id=user.id, scheduled_time=scheduled_datetime).first()

                        if not job:
                            logger.info(f"[V3 Scheduler] Creating new V3 job for user {user.id} scheduled at {scheduled_datetime}")
                            new_job = CompletedJob(
                                user_id=user.id,
                                scheduled_time=scheduled_datetime,
                                completed_time=None,
                                post_title=""
                            )
                            db.session.add(new_job)
                            db.session.commit()

                            logger.info(f"[V3 Scheduler] Initiating V3 blog post creation for user {user.id}")
                            post, error = create_blog_post(user.id)
                            if error:
                                logger.error(f"Failed to create V3 blog post for user {user.id}: {error}")
                            else:
                                new_job.completed_time = eastern_tz.localize(datetime.now())
                                new_job.post_title = post['title']['rendered']
                                db.session.commit()
                                logger.info(f"[V3 Scheduler] Completed job for user {user.id} scheduled at {scheduled_datetime}")
                        elif job.completed_time is None:
                            time_pending = now - scheduled_datetime
                            if time_pending > timedelta(minutes=5):
                                logger.info(f"[V3 Scheduler] Retrying job for user {user.id} scheduled at {scheduled_datetime}")

                                post, error = create_blog_post(user.id)
                                if error:
                                    logger.error(f"Failed to create V3 blog post for user {user.id} on retry: {error}")
                                else:
                                    job.completed_time = eastern_tz.localize(datetime.now())
                                    job.post_title = post['title']['rendered']
                                    db.session.commit()
                                    logger.info(f"[V3 Scheduler] Completed job for user {user.id} scheduled at {scheduled_datetime} on retry")
                            else:
                                logger.info(f"Job for user {user.id} scheduled at {scheduled_datetime} is still pending")
                        else:
                            logger.info(f"Job for user {user.id} scheduled at {scheduled_datetime} already completed")

            # Clean up old completed jobs
            week_ago = now - timedelta(days=7)
            old_jobs = CompletedJob.query.filter(CompletedJob.completed_time < week_ago).all()
            for job in old_jobs:
                db.session.delete(job)
            db.session.commit()
            logger.info(f"[V3 Scheduler] Cleaned up {len(old_jobs)} old jobs")

        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            db.session.rollback()
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    try:
        logger.info("[V3 Scheduler] Starting EZWAI SMM V3.0 Scheduler")
        logger.info("[V3 Scheduler] Using V4 pipeline: GPT-5-mini + SeeDream-4")
        check_and_trigger_jobs()
        logger.info("[V3 Scheduler] Scheduler run completed")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the main scheduler execution: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")