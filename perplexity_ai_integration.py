import json
import requests
from dotenv import load_dotenv
import os
import logging
from flask_sqlalchemy import SQLAlchemy
from flask import current_app

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

db = SQLAlchemy()

def load_user_env(user_id):
    """Load user-specific environment variables."""
    env_file = f'.env.user_{user_id}'
    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)  # CRITICAL: Override existing env vars
        logger.debug(f"Loaded environment for user {user_id}")
    else:
        logger.error(f"Environment file for user {user_id} not found")

def query_management(user_id):
    """Manage and rotate through user-specific queries. Returns tuple (query, writing_style)."""
    from app_v3 import User  # Import User model here to avoid circular imports

    user = User.query.get(user_id)
    if not user:
        logger.error(f"User {user_id} not found")
        return None, None

    if not user.specific_topic_queries:
        logger.warning(f"No specific topic queries found for user {user_id}")
        return None, None

    max_queries = 10
    start_index = user.last_query_index

    for i in range(max_queries):
        next_index = (start_index + i) % max_queries + 1  # Add 1 because queries are 1-indexed
        next_query = user.specific_topic_queries.get(str(next_index))

        if next_query:
            # Get corresponding writing style
            writing_style = None
            if user.writing_styles:
                writing_style = user.writing_styles.get(str(next_index))

            # Update last_query_index
            user.last_query_index = next_index
            try:
                db.session.commit()
                logger.info(f"Updated last_query_index to {next_index} for user {user_id}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to update last_query_index: {str(e)}")
                logger.exception(e)

            logger.info(f"Selected query {next_index} for user {user_id}: {next_query}")
            logger.info(f"Selected writing style: {writing_style or 'None (default)'}")
            return next_query, writing_style

    logger.warning(f"No non-empty queries found for user {user_id}")
    return None, None

def generate_blog_post_ideas(query, user_id, writing_style=None):
    """Generate blog post ideas using the Perplexity AI API with enhanced prompts based on writing style."""
    load_user_env(user_id)
    api_key = os.getenv('PERPLEXITY_AI_API_TOKEN')

    if not api_key:
        logger.error(f"Perplexity API token not found for user {user_id}")
        return []

    logger.debug(f"Perplexity API token (first 5 chars): {api_key[:5]}...")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Enhanced system prompt based on writing style
    base_system = "You are an expert research journalist who provides comprehensive, in-depth research for professional writers. Whenever possible you will include real life case studies and examples if it makes sense for the topic or story type."

    if writing_style:
        system_prompt = f"{base_system} The article will be written in a {writing_style} style. Provide detailed research, statistics, expert quotes, case studies, and recent developments that support this writing approach."
    else:
        system_prompt = base_system

    # Enhanced user prompt to extract maximum value per API call
    if writing_style:
        user_prompt = f"""Find the top trending news story regarding: {query} and provide comprehensive research content for editors to create a Pulitzer prize-winning article written in the style of {writing_style}.

Include:
- Latest statistics and data points with sources
- Expert opinions and quotable statements
- Recent case studies or real-world examples
- Key trends and developments
- Relevant background context
- Industry implications and future outlook
- Specific facts that support the {writing_style} approach"""
    else:
        user_prompt = f"""Find the top trending news story regarding: {query} and provide comprehensive research content.

Include:
- Latest statistics and data points with sources
- Expert opinions and quotable statements
- Recent case studies or real-world examples
- Key trends and developments
- Relevant background context
- Industry implications and future outlook"""

    logger.info(f"Generating enhanced blog post research for query: {query}")
    logger.info(f"Writing style: {writing_style or 'Default'}")

    data = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 2000,  # Increased from 500 to get more value per call
        "temperature": 0.2,
        "top_p": 0.9,
        "return_citations": True,
        "search_domain_filter": ["perplexity.ai"],
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": "month",
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1
    }

    logger.debug(f"Perplexity API request payload: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(PERPLEXITY_API_URL, json=data, headers=headers, timeout=30)
        response.raise_for_status()

        response_json = response.json()
        logger.debug(f"Perplexity API response for query '{query}': {json.dumps(response_json, indent=2)}")
        
        blog_post_idea = response_json['choices'][0]['message']['content'].strip()
        logger.info(f"Generated blog post idea for query '{query}': {blog_post_idea[:100]}...")  # Log first 100 chars

        return [blog_post_idea]
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        if e.response.status_code == 400:
            logger.error(f"Bad Request. Check the API key and request format. Response: {e.response.text}")
        elif e.response.status_code == 401:
            logger.error("Unauthorized. Check your API key.")
        elif e.response.status_code == 429:
            logger.error("Too Many Requests. You might have exceeded your rate limit.")
        else:
            logger.error(f"An HTTP {e.response.status_code} error occurred. Response: {e.response.text}")
        logger.exception(e)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error occurred: {str(e)}")
        logger.exception(e)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        logger.exception(e)
    except KeyError as e:
        logger.error(f"Unexpected response format. KeyError: {str(e)}")
        logger.error(f"Full response: {response_json if 'response_json' in locals() else 'No response'}")
        logger.exception(e)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.exception(e)

    return []  # Return empty list if any error occurs

# You can add more helper functions or classes here if needed

if __name__ == "__main__":
    # This block can be used for testing the module independently
    logging.basicConfig(level=logging.DEBUG)
    test_user_id = 1  # Replace with a valid user ID for testing
    test_query = query_management(test_user_id)
    if test_query:
        ideas = generate_blog_post_ideas(test_query, test_user_id)
        print(f"Generated ideas: {ideas}")
    else:
        print("No valid query found for testing.")