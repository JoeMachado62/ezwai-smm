"""
image_prompt_generator.py - STEP 2: Contextual Image Prompt Generation

Analyzes article HTML and generates section-aligned photographic prompts.
Uses GPT-5-mini to understand content and create prompts that match each section.

KEY FEATURE: Image prompts are contextually aware - they know what each section discusses.
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)


def load_user_env(user_id: int) -> None:
    """Load user-specific environment variables."""
    env_file = f".env.user_{user_id}"
    if os.path.exists(env_file):
        load_dotenv(env_file)


def _get_openai_client() -> OpenAI:
    """Get OpenAI client with API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set.")
    return OpenAI(api_key=api_key)


def extract_sections_from_html(html: str) -> List[Dict[str, str]]:
    """
    Extract H2 sections with their content from HTML.

    Returns list of: [{"heading": "...", "content": "...first 300 chars..."}]
    """
    sections = []

    # Find all H2 tags and their positions
    h2_pattern = r"<h2[^>]*>(.*?)</h2>"
    h2_matches = list(re.finditer(h2_pattern, html, flags=re.I | re.S))

    for i, match in enumerate(h2_matches):
        heading = re.sub(r"\s+", " ", match.group(1)).strip()

        # Extract content after this H2 until next H2 or end
        start_pos = match.end()
        if i + 1 < len(h2_matches):
            end_pos = h2_matches[i + 1].start()
        else:
            end_pos = len(html)

        section_content = html[start_pos:end_pos]
        # Strip HTML tags for content preview
        text_content = re.sub(r"<[^>]+>", " ", section_content)
        text_content = re.sub(r"\s+", " ", text_content).strip()

        sections.append({
            "heading": heading,
            "content": text_content[:300] + "..." if len(text_content) > 300 else text_content
        })

    return sections


def create_image_prompt_instruction(
    article_html: str,
    perplexity_summary: str,
    writing_style: Optional[str] = None
) -> str:
    """
    Create detailed prompt for GPT-5-mini to generate contextual image prompts.
    """

    sections = extract_sections_from_html(article_html)

    # Extract title for hero context
    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", article_html, flags=re.I | re.S)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else "Article"

    sections_text = "\n\n".join([
        f"SECTION {i+1}: {s['heading']}\nContent preview: {s['content']}"
        for i, s in enumerate(sections)
    ])

    style_guidance = ""
    if writing_style:
        style_map = {
            "Conversational/Personal": "Use warm, relatable imagery - human subjects, everyday settings, emotional connections",
            "Authoritative/Expert": "Use professional settings, expert subjects, data visualization, corporate/medical/scientific environments",
            "Narrative/Storytelling": "Use story-driven scenes, human subjects in meaningful moments, cinematic compositions",
            "Listicle/Scannable": "Use clear, simple imagery - icons, clean backgrounds, easily identifiable subjects",
            "Investigative/Journalistic": "Use documentary-style imagery, revealing details, evidence-focused, journalistic realism",
            "How-to/Instructional": "Use process-focused imagery, step-by-step visuals, instructional clarity",
            "Opinion/Commentary": "Use thought-provoking imagery, conceptual visuals, metaphorical subjects",
            "Humorous/Satirical": "Use playful imagery, unexpected juxtapositions, clever visual humor"
        }
        style_guidance = f"\n\nVISUAL STYLE GUIDANCE: {style_map.get(writing_style, '')}"

    return f"""You are an expert photography art director for editorial magazines like National Geographic, TIME, and The Atlantic.

TASK: Generate photographic image prompts that perfectly align with the article content.

ARTICLE TITLE: {title}

PERPLEXITY RESEARCH SUMMARY:
{perplexity_summary}

ARTICLE SECTIONS:
{sections_text}{style_guidance}

CRITICAL REQUIREMENTS:
1. READ each section's content carefully
2. Create prompts that match the SPECIFIC topic of each section
3. DO NOT use generic prompts - be specific to the section's subject matter
4. Include technical photography details for photorealism

PROMPT FORMAT (for each image):
- Main subject/scene (specific to section topic)
- Camera & lens (e.g., "Canon R5, 85mm f/1.4" or "Nikon Z9, 24-70mm f/2.8")
- Lighting (e.g., "Golden hour natural light", "Studio softbox", "Dramatic side lighting")
- Composition (e.g., "Rule of thirds", "Centered symmetry", "Low angle")
- Mood/atmosphere
- Setting/background

EXAMPLE (GOOD):
Section: "AI in Radiology Diagnosis"
Prompt: "Medical radiologist analyzing AI-enhanced X-ray scans on dual 4K monitors in modern hospital radiology department, Canon R5, 50mm f/1.2, clean clinical LED lighting, focused professional concentration, teal and white color palette, shallow depth of field with monitors in sharp focus"

EXAMPLE (BAD):
"Doctor with technology" ❌ Too generic!

OUTPUT FORMAT (JSON):
{{
  "hero_prompt": "Cinematic wide shot for hero image (16:9) - captures overall article theme",
  "section_prompts": [
    {{
      "section_heading": "First Section Heading",
      "prompt": "Detailed photographic prompt matching this section's specific content..."
    }},
    {{
      "section_heading": "Second Section Heading",
      "prompt": "Detailed photographic prompt matching this section's specific content..."
    }}
  ]
}}

Generate {len(sections)} section prompts, one for each section above. Each prompt must be contextually aligned with its section's specific topic.
"""


def generate_contextual_image_prompts(
    article_html: str,
    perplexity_summary: str,
    user_id: int,
    writing_style: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Generate contextual image prompts using GPT-5-mini.

    Args:
        article_html: Clean HTML from story_generation.py
        perplexity_summary: Summary from Perplexity research
        user_id: User ID for environment loading
        writing_style: Optional writing style for visual approach

    Returns:
        {
            "hero_prompt": "...",
            "section_prompts": [
                {"section_heading": "...", "prompt": "..."},
                ...
            ]
        }
        or None if error
    """
    load_user_env(user_id)
    client = _get_openai_client()

    # STEP 2 is the image-prompt step, so use the PASS3 model
    model = os.getenv("MODEL_FOR_PASS3", "gpt-5-mini")

    try:
        instruction = create_image_prompt_instruction(article_html, perplexity_summary, writing_style)

        logger.info(f"[Image Prompts] Generating contextual prompts with {model}")
        logger.info(f"[Image Prompts] Writing style: {writing_style or 'Default'}")

        # Build messages for Responses API
        messages = [
            {"role": "system", "content": "You are an expert photography art director. Return ONLY valid JSON matching the exact structure - no markdown, no code fences, no explanations. Just the JSON object."},
            {"role": "user", "content": instruction}
        ]

        # Use prompted JSON approach (response_format not supported in responses.create)
        # Increased token limit to prevent JSON truncation
        resp = client.responses.create(
            model=model,
            input=messages,
            max_output_tokens=4000  # Increased from 2000 to handle longer prompts
        )

        # Extract output text from response (same pattern as story_generation.py)
        result_text = getattr(resp, "output_text", "")

        if not result_text:
            logger.error("[Image Prompts] Empty response from API")
            return None

        # Log response length for debugging
        logger.info(f"[Image Prompts] Received {len(result_text)} characters")

        # Clean markdown code fences if present (same as story_generation.py)
        result_text = result_text.strip()
        result_text = re.sub(r'^```json\s*', '', result_text)
        result_text = re.sub(r'\s*```$', '', result_text)

        # Extract first JSON object if the model added any prose
        def _extract_first_json_object(s: str):
            depth = 0
            start = None
            for i, ch in enumerate(s):
                if ch == "{":
                    if depth == 0:
                        start = i
                    depth += 1
                elif ch == "}":
                    if depth > 0:
                        depth -= 1
                        if depth == 0 and start is not None:
                            return s[start:i+1]
            return None

        # Try to extract JSON object
        extracted = _extract_first_json_object(result_text)
        json_text = extracted or result_text

        # Parse JSON
        prompts_data = json.loads(json_text)

        # Validate structure
        if "hero_prompt" not in prompts_data or "section_prompts" not in prompts_data:
            logger.error("[Image Prompts] Invalid JSON structure returned")
            return None

        num_sections = len(extract_sections_from_html(article_html))
        num_prompts = len(prompts_data["section_prompts"])

        logger.info(f"[Image Prompts] Generated {num_prompts} section prompts for {num_sections} sections")
        logger.info(f"[Image Prompts] Hero prompt: {prompts_data['hero_prompt'][:100]}...")

        return prompts_data

    except json.JSONDecodeError as e:
        logger.error(f"[Image Prompts] JSON parse error: {e}")
        if 'result_text' in locals():
            logger.error(f"[Image Prompts] Response length: {len(result_text)} chars")
            logger.error(f"[Image Prompts] First 500 chars: {result_text[:500]}")
            logger.error(f"[Image Prompts] Last 500 chars: {result_text[-500:]}")
        return None
    except Exception as e:
        logger.error(f"[Image Prompts] Error generating prompts: {e}")
        logger.debug(f"[Image Prompts] Traceback: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    # Test the module independently
    logging.basicConfig(level=logging.INFO)

    test_html = """
    <h1>The Future of AI in Healthcare</h1>
    <p>Introduction paragraph...</p>
    <h2>AI-Powered Radiology Diagnosis</h2>
    <p>Artificial intelligence is revolutionizing radiology with 99% accuracy in detecting tumors...</p>
    <h2>Machine Learning in Drug Discovery</h2>
    <p>Pharmaceutical companies are using ML to accelerate drug development by 10x...</p>
    """

    test_summary = "AI healthcare advances include 40% better diagnosis and reduced development time."

    result = generate_contextual_image_prompts(
        article_html=test_html,
        perplexity_summary=test_summary,
        user_id=1,
        writing_style="Authoritative/Expert"
    )

    if result:
        print(f"\n✅ Hero Prompt: {result['hero_prompt']}")
        print(f"\n📸 Section Prompts:")
        for sp in result['section_prompts']:
            print(f"  - {sp['section_heading']}: {sp['prompt'][:100]}...")
    else:
        print("\n❌ Prompt generation failed")
