"""
story_generation.py - STEP 1: Structured Article Generation

Uses GPT-5 to generate article with component metadata for magazine layout.
Returns JSON with content + component placement instructions.
"""

import os
import re
import json
import logging
from typing import Optional, Dict, List
from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)

def load_user_env(user_id: int) -> None:
    """Load user-specific environment variables."""
    env_file = f".env.user_{user_id}"
    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)  # CRITICAL: Override existing env vars
        logger.debug(f"Loaded environment for user {user_id}")
    else:
        logger.error(f"Environment file for user {user_id} not found")


def _get_openai_client() -> OpenAI:
    """Get OpenAI client with API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set.")
    return OpenAI(api_key=api_key)


def create_story_prompt(
    perplexity_research: str,
    user_system_prompt: str,
    writing_style: Optional[str] = None
) -> str:
    """
    Create comprehensive prompt for GPT-5 structured article generation.
    """

    style_guidance = ""
    if writing_style:
        style_map = {
            "Conversational/Personal": "Write in a warm, friendly tone with first-person perspective and relatable anecdotes.",
            "Authoritative/Expert": "Write in a professional, credible tone with data-driven insights and industry expertise.",
            "Narrative/Storytelling": "Write with compelling story structure, vivid descriptions, and emotional journey.",
            "Listicle/Scannable": "Write in highly scannable format with numbered points and clear takeaways.",
            "Investigative/Journalistic": "Write with objective journalism style and multiple perspectives.",
            "How-to/Instructional": "Write as clear tutorial with step-by-step instructions.",
            "Opinion/Commentary": "Write as persuasive opinion piece with strong arguments.",
            "Humorous/Satirical": "Write with wit and entertainment value using wordplay."
        }
        style_guidance = f"\n\nWRITING STYLE: {style_map.get(writing_style, writing_style)}"

    return f"""You are an expert magazine writer creating a structured article for publication.

{user_system_prompt}{style_guidance}

RESEARCH CONTEXT (from Perplexity AI):
{perplexity_research}

OUTPUT FORMAT - Return valid JSON only:
{{
  "title": "Article main title",
  "html": "Article content in semantic HTML (h1, h2, h3, p, ul, ol, li only - NO classes or styling)",
  "executive_summary": {{
    "intro": "2-3 sentence overview that motivates reading",
    "key_stats": [
      {{"number": "43%", "description": "Increase in appointments"}},
      {{"number": "220%", "description": "Sales increase achieved"}}
    ]
  }},
  "components": [
    {{
      "type": "pull_quote",
      "content": "Impactful quote from article text",
      "insert_after_paragraph": 5
    }},
    {{
      "type": "stat_highlight",
      "number": "43%",
      "description": "Brief description of metric",
      "insert_after_paragraph": 8
    }},
    {{
      "type": "case_study",
      "title": "Company Name - Brief Description",
      "profile": "1-2 sentence company description",
      "challenge": "What problem they faced",
      "solution": "What they implemented",
      "results": [
        "18% increase in conversion",
        "$1M+ influenced sales",
        "19% more customer calls"
      ],
      "quote": "Optional quote from company representative",
      "insert_after_heading": "Real Dealership Results"
    }},
    {{
      "type": "sidebar",
      "title": "Sidebar heading",
      "content": "HTML content for sidebar (lists, paragraphs)",
      "insert_after_heading": "Section name where sidebar appears"
    }}
  ]
}}

CONTENT REQUIREMENTS:
1. Write 1500-2500 word article using research
2. HTML structure:
   - ONE <h1> for main title
   - 3-4 <h2> sections with substantial content (3-5 paragraphs each)
   - Use <h3> for subsections
   - Use <ul>/<ol> for lists
   - NO CSS classes, NO inline styles, NO image tags

3. Component guidelines:
   - pull_quote: 2-3 impactful quotes from your article text
   - stat_highlight: 3-5 key metrics from the research
   - case_study: 1-3 real examples with challenge/solution/results structure
   - sidebar: 0-2 complementary info boxes

4. Insert positions:
   - insert_after_paragraph: Number (counts <p> tags from start)
   - insert_after_heading: Exact text of <h2> heading

5. Executive summary:
   - Compelling 2-3 sentence intro
   - 2-3 key statistics that grab attention

Return ONLY valid JSON. No markdown, no code blocks, just the JSON object.
"""


def generate_clean_article(
    perplexity_research: str,
    user_id: int,
    user_system_prompt: str,
    writing_style: Optional[str] = None
) -> Optional[Dict]:
    """
    Generate structured article with component metadata using GPT-5.

    Returns:
    {
        "title": str,
        "html": str,
        "executive_summary": {...},
        "components": [...]
    }
    """
    load_user_env(user_id)
    client = _get_openai_client()

    model = os.getenv("MODEL_FOR_PASS1", "gpt-5")
    output_text = ""  # Initialize to prevent unbound variable error

    try:
        prompt = create_story_prompt(perplexity_research, user_system_prompt, writing_style)

        logger.info(f"[Story Gen] Generating structured article with {model}")
        logger.info(f"[Story Gen] Writing style: {writing_style or 'Default'}")

        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": "You are an expert magazine writer. Return ONLY valid JSON with article structure and component metadata."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_output_tokens=16000
        )

        output_text = getattr(response, "output_text", "")

        if not output_text or len(output_text.strip()) < 100:
            logger.error("[Story Gen] Empty or too-short response")
            return None

        # Clean JSON response (remove markdown code blocks if present)
        json_text = output_text.strip()
        json_text = re.sub(r'^```json\s*', '', json_text)
        json_text = re.sub(r'\s*```$', '', json_text)

        # Parse JSON
        article_data = json.loads(json_text)

        # Validate required fields
        required_fields = ["title", "html", "components"]
        if not all(field in article_data for field in required_fields):
            logger.error(f"[Story Gen] Missing required fields: {required_fields}")
            return None

        logger.info(f"[Story Gen] Article generated - Title: {article_data['title'][:100]}")
        logger.info(f"[Story Gen] Components: {len(article_data['components'])}")
        logger.info(f"[Story Gen] HTML length: {len(article_data['html'])} characters")

        return article_data

    except json.JSONDecodeError as e:
        logger.error(f"[Story Gen] JSON parse error: {e}")
        logger.debug(f"[Story Gen] Raw output: {output_text[:500]}...")
        return None
    except Exception as e:
        logger.error(f"[Story Gen] Error generating article: {e}")
        logger.debug(f"[Story Gen] Traceback: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    # Test the module
    logging.basicConfig(level=logging.INFO)

    test_research = """
    Bob Rohrman Kia achieved 43% increase in lead-to-appointment conversion.
    Elk Grove Buick GMC saw 18% conversion lift and influenced $1M+ in sales.
    AutoMax Dealership reported 220% sales increase with 50% faster closings.
    """

    result = generate_clean_article(
        perplexity_research=test_research,
        user_id=1,
        user_system_prompt="Write authoritative, data-driven content.",
        writing_style="Authoritative/Expert"
    )

    if result:
        print(f"\nTitle: {result['title']}")
        print(f"Components: {len(result['components'])}")
        print(f"\nFirst component: {result['components'][0]}")
    else:
        print("\nArticle generation failed")