"""
OpenAI Integration V4 - GPT-5-mini with Structured JSON Output
Single call returns both magazine HTML and cinematic image prompts
"""

import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
import replicate

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_user_env(user_id):
    """Load user-specific environment variables"""
    env_file = f'.env.user_{user_id}'
    if os.path.exists(env_file):
        load_dotenv(env_file)
        logger.debug(f"Loaded environment for user {user_id}")
    else:
        logger.error(f"Environment file for user {user_id} not found")


def create_structured_article_prompt(blog_post_idea, system_prompt):
    """
    Creates comprehensive prompt for GPT-5-mini to generate:
    1. Magazine-style HTML with image placeholders
    2. Cinematic image prompts for each section
    Returns everything as structured JSON
    """

    prompt = f"""You are an expert magazine writer and photography art director.

YOUR TASK: Create a comprehensive magazine article with cinematic image prompts.

OUTPUT FORMAT: Return ONLY valid JSON with this exact structure:
{{
  "title": "Compelling article title here",
  "html_content": "Complete HTML article with {{{{IMAGE_HERO}}}}, {{{{IMAGE_1}}}}, {{{{IMAGE_2}}}}, {{{{IMAGE_3}}}} placeholders",
  "image_prompts": {{
    "hero": "Cinematic prompt for hero cover image (16:9)",
    "section_1": "Cinematic prompt for first major section (4:3)",
    "section_2": "Cinematic prompt for second major section (4:3)",
    "section_3": "Cinematic prompt for third major section (4:3)"
  }}
}}

==========================================
PART 1: HTML CONTENT REQUIREMENTS
==========================================

WRITE A 1500-2500 WORD ARTICLE about the topic provided. Use this magazine layout structure with the required CSS classes:

<div class="magazine-container">
    <!-- HERO COVER SECTION -->
    <div class="cover" style="background-image: url('{{{{IMAGE_HERO}}}}');">
        <h1>[Your Creative Title]</h1>
        <div class="subtitle">[Engaging subtitle that hooks the reader]</div>
        <div class="edition">2025 Edition</div>
    </div>

    <!-- FIRST MAJOR SECTION -->
    <div class="section">
        <div class="section-header" style="background-image: url('{{{{IMAGE_1}}}}');">
            <h2>[Your Section Title]</h2>
        </div>
        <div class="content-area">
            <div class="main-column">
                <h3>[Your Subsection Heading]</h3>
                <p>[Write 3-4 rich, detailed paragraphs. Include specific examples, data points, and insights.]</p>

                <div class="pull-quote">[Extract a compelling quote from your content]</div>

                <h4>[Another Relevant Heading]</h4>
                <p>[2-3 paragraphs with concrete examples and analysis.]</p>

                <div class="case-study-box">
                    <h4>[Case Study Title]</h4>
                    <p>[Include a specific example or scenario that illustrates your points.]</p>
                </div>

                <h4>[Related Subtopic]</h4>
                <p>[2-3 more paragraphs with actionable insights.]</p>
            </div>
            <div class="sidebar">
                <div class="stat-highlight">
                    <div class="number">[Stat]</div>
                    <div class="description">[Statistic description]</div>
                </div>
                <div class="sidebar-box">
                    <h4>[Insight Title]</h4>
                    <p>[Related information that complements the main content.]</p>
                </div>
            </div>
        </div>
    </div>

    <!-- SECOND MAJOR SECTION -->
    <div class="section">
        <div class="section-header" style="background-image: url('{{{{IMAGE_2}}}}');">
            <h2>[Your Section Title]</h2>
        </div>
        <div class="content-area">
            <div class="main-column">
                <p>[Write 3-4 rich paragraphs exploring this theme with depth.]</p>

                <h4>[Subsection Heading]</h4>
                <p>[2-3 paragraphs with detailed analysis and examples.]</p>

                <ul>
                    <li>[Key insight with explanation]</li>
                    <li>[Key insight with explanation]</li>
                    <li>[Key insight with explanation]</li>
                </ul>

                <div class="checklist-magazine">
                    <ul>
                        <li>[Action item - specific and actionable]</li>
                        <li>[Action item - specific and actionable]</li>
                        <li>[Action item - specific and actionable]</li>
                    </ul>
                </div>

                <div class="pull-quote">[Another powerful insight]</div>
            </div>
        </div>
    </div>

    <!-- THIRD MAJOR SECTION -->
    <div class="section">
        <div class="section-header" style="background-image: url('{{{{IMAGE_3}}}}');">
            <h2>[Your Section Title]</h2>
        </div>
        <div class="content-area">
            <div class="main-column">
                <p>[Write 3-4 rich paragraphs on this final theme, bringing insights together.]</p>

                <h3>[Concluding Subtopic]</h3>
                <p>[2 paragraphs with practical takeaways.]</p>

                <ol>
                    <li><strong>[Step Title]:</strong> [Detailed explanation with context]</li>
                    <li><strong>[Step Title]:</strong> [Detailed explanation with examples]</li>
                    <li><strong>[Step Title]:</strong> [Detailed explanation with outcomes]</li>
                </ol>

                <div class="warning-box-magazine">
                    <h4>⚠️ [Warning Box Title]</h4>
                    <ul>
                        <li>[Important caution or consideration]</li>
                        <li>[Important caution or consideration]</li>
                        <li>[Important caution or consideration]</li>
                    </ul>
                </div>

                <h3>[Final Section Heading]</h3>
                <p>[2-3 paragraphs summarizing insights and providing actionable guidance.]</p>

                <div class="case-study-box">
                    <h4>[Action Plan Title]</h4>
                    <ul>
                        <li>[Immediate action step]</li>
                        <li>[Follow-up action]</li>
                        <li>[Long-term strategy]</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</div>

WRITING GUIDELINES:
✓ Create your OWN compelling section titles and headings that fit the topic
✓ Write naturally - let the content flow from the topic, not from a template
✓ Each section: 400-700 words of substantive, topic-specific content
✓ Professional but conversational tone
✓ Include specific examples, statistics, and real-world cases when relevant
✓ Use pull quotes, sidebars, and visual elements for variety
✓ Ensure smooth transitions between sections
✓ Provide actionable insights throughout

CRITICAL: Do NOT use generic placeholder titles like "Opening Subsection" or "Detailed Aspect 1". Create meaningful, topic-specific headings that would engage readers interested in this subject.

==========================================
PART 2: IMAGE PROMPT REQUIREMENTS
==========================================

Create 4 CINEMATIC, PHOTOREALISTIC prompts. Each prompt MUST capture the essence of its section content.

PROMPT FORMULA:
"Professional [editorial/business/corporate] photography, [main subject/scene directly related to section content], shot with [Canon EOS R5/Sony A7R IV/Nikon Z9], [studio lighting/natural light/golden hour/dramatic lighting], [wide angle/shallow depth of field/etc], [atmosphere: modern/dramatic/inspiring/professional], photorealistic, magazine quality, 2K resolution, [aspect ratio context]"

CRITICAL REQUIREMENTS FOR EACH PROMPT:
✓ MUST say "professional photography" or "editorial photography"
✓ MUST specify high-end camera (Canon EOS R5, Sony A7R IV, Nikon Z9)
✓ MUST include lighting type (studio/natural/golden hour/dramatic)
✓ MUST include composition (shallow depth of field, wide angle, bokeh, etc)
✓ MUST be PHOTOREALISTIC - NO illustrations, drawings, CGI, cartoons
✓ MUST relate directly to the specific section content
✓ Hero: 16:9 cinematic establishing shot for cover
✓ Section 1-3: 4:3 images specific to each section theme

EXAMPLE PROMPTS (adapt these formulas to YOUR specific topic):

For a BUSINESS topic:
- Hero: "Professional editorial photography of modern office environment with professionals collaborating, shot with Canon EOS R5, natural window lighting with warm tones, wide angle composition showing depth, inspiring professional atmosphere, photorealistic, magazine cover quality, 2K resolution, cinematic 16:9 establishing shot"

For a TECHNOLOGY topic:
- Section 1: "Professional business photography, executive reviewing analytics dashboard with data visualizations, shot with Sony A7R IV, studio lighting with blue highlights, shallow depth of field with bokeh background, modern atmosphere, photorealistic, editorial magazine quality, 2K resolution, 4:3 composition"

For a LIFESTYLE topic:
- Section 2: "Professional lifestyle photography, authentic moment capturing the essence of the topic, shot with Nikon Z9, natural light through large windows, medium depth of field, warm inviting atmosphere, photorealistic, lifestyle magazine quality, 2K resolution, 4:3 composition"

For a DOCUMENTARY topic:
- Section 3: "Professional documentary photography, detailed scene that tells the story, shot with Canon EOS R5, dramatic natural lighting creating depth, selective focus on key elements, authentic atmosphere, photorealistic, documentary magazine quality, 2K resolution, 4:3 composition"

CREATE YOUR OWN image prompts that match YOUR article's specific content and theme!

==========================================
SYSTEM CONTEXT & TOPIC
==========================================

SYSTEM INSTRUCTIONS: {system_prompt}

ARTICLE TOPIC: {blog_post_idea}

Now create the complete JSON output with the magazine article and 4 cinematic image prompts."""

    return prompt


def process_blog_post_with_images_v4(blog_post_idea, user_id, system_prompt):
    """
    V4: Single GPT-5-mini call returns structured JSON with HTML + image prompts
    Then generates images and replaces placeholders
    """
    load_user_env(user_id)
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or api_key == 'None':
        logger.error(f"OpenAI API key not found for user {user_id}")
        return None, "OpenAI API key not configured"

    client = OpenAI(api_key=api_key)

    try:
        # Step 1: Get structured JSON from GPT-5-mini (HTML + image prompts)
        logger.info("Step 1: Generating article and image prompts with GPT-5-mini...")

        prompt = create_structured_article_prompt(blog_post_idea, system_prompt)

        response = client.responses.create(
            model="gpt-5-mini",
            input=prompt,
            text={
                "verbosity": "high",  # High verbosity for comprehensive article
                "format": {"type": "json_object"}  # Request JSON output
            },
            max_output_tokens=16000,  # Plenty for 2000+ word article + prompts
            instructions="You are an expert magazine writer and photography art director. Generate a complete magazine article with cinematic image prompts. Return ONLY valid JSON."
        )

        # Extract JSON from response
        json_output = response.output_text if hasattr(response, 'output_text') else ""

        if not json_output:
            logger.error("Empty response from GPT-5-mini")
            return None, "Failed to generate article content"

        logger.debug(f"Received response length: {len(json_output)} characters")

        # Parse JSON
        try:
            article_data = json.loads(json_output)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response text: {json_output[:500]}...")
            return None, "Failed to parse article JSON"

        # Validate structure
        required_keys = ['title', 'html_content', 'image_prompts']
        if not all(key in article_data for key in required_keys):
            logger.error(f"Missing required keys in JSON. Got: {list(article_data.keys())}")
            return None, "Invalid article structure"

        title = article_data['title']
        html_content = article_data['html_content']
        image_prompts = article_data['image_prompts']

        logger.info(f"✓ Article generated: {title}")
        logger.info(f"✓ Content length: {len(html_content)} characters")
        logger.info(f"✓ Image prompts: {list(image_prompts.keys())}")

        # Step 2: Generate images with SeeDream-4
        logger.info("Step 2: Generating images with SeeDream-4...")

        replicate_token = os.getenv('REPLICATE_API_TOKEN')
        if not replicate_token:
            logger.warning("Replicate token not found - skipping image generation")
            return {
                'title': title,
                'content': html_content,
                'all_images': [],
                'hero_image_url': None
            }, None

        os.environ['REPLICATE_API_TOKEN'] = replicate_token
        image_urls = {}

        # Generate hero image (16:9)
        if 'hero' in image_prompts:
            logger.info("Generating hero image (16:9)...")
            logger.debug(f"Hero prompt: {image_prompts['hero'][:100]}...")
            try:
                output = replicate.run(
                    "bytedance/seedream-4",
                    input={
                        "prompt": image_prompts['hero'],
                        "aspect_ratio": "16:9",
                        "output_format": "jpg",
                        "output_quality": 90
                    }
                )
                logger.debug(f"Raw hero output: {output}")
                image_urls['hero'] = output if isinstance(output, str) else output[0]
                logger.info(f"✓ Hero image generated: {image_urls['hero']}")
            except Exception as e:
                logger.error(f"Hero image generation failed: {str(e)}")
                logger.error(f"Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                image_urls['hero'] = ""

        # Generate section images (4:3)
        for section_num in [1, 2, 3]:
            key = f'section_{section_num}'
            if key in image_prompts:
                logger.info(f"Generating section {section_num} image (4:3)...")
                logger.debug(f"Section {section_num} prompt: {image_prompts[key][:100]}...")
                try:
                    output = replicate.run(
                        "bytedance/seedream-4",
                        input={
                            "prompt": image_prompts[key],
                            "aspect_ratio": "4:3",
                            "output_format": "jpg",
                            "output_quality": 90
                        }
                    )
                    logger.debug(f"Raw section {section_num} output: {output}")
                    image_urls[key] = output if isinstance(output, str) else output[0]
                    logger.info(f"✓ Section {section_num} image generated: {image_urls[key]}")
                except Exception as e:
                    logger.error(f"Section {section_num} image generation failed: {str(e)}")
                    logger.error(f"Exception type: {type(e).__name__}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    image_urls[key] = ""

        # Step 3: Replace placeholders with actual image URLs
        logger.info("Step 3: Replacing image placeholders...")

        final_html = html_content
        final_html = final_html.replace('{{IMAGE_HERO}}', image_urls.get('hero', ''))
        final_html = final_html.replace('{{IMAGE_1}}', image_urls.get('section_1', ''))
        final_html = final_html.replace('{{IMAGE_2}}', image_urls.get('section_2', ''))
        final_html = final_html.replace('{{IMAGE_3}}', image_urls.get('section_3', ''))

        logger.info("✓ V4 blog post generation complete!")

        return {
            'title': title,
            'content': final_html,
            'all_images': [image_urls.get('hero', ''), image_urls.get('section_1', ''),
                          image_urls.get('section_2', ''), image_urls.get('section_3', '')],
            'hero_image_url': image_urls.get('hero', None)
        }, None

    except Exception as e:
        logger.error(f"V4 blog post generation error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None, f"Failed to process blog post: {str(e)}"


# Wrapper function for backwards compatibility
def create_blog_post_with_images_v4(blog_post_idea, user_id, system_prompt):
    """Wrapper for compatibility with existing code"""
    return process_blog_post_with_images_v4(blog_post_idea, user_id, system_prompt)
