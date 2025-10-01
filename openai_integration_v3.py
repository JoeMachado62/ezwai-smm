"""
EZWAI SMM V3.0 - Latest OpenAI & Image Generation Integration
- OpenAI GPT-5-mini with Responses API and reasoning
- SeeDream-4 for 2K photorealistic images with text rendering
- Enhanced prompt engineering for magazine photography
"""
import os
import logging
import traceback
from openai import OpenAI
import replicate
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def load_user_env(user_id):
    """Load user-specific environment variables"""
    load_dotenv(f'.env.user_{user_id}')


def get_magazine_html_template():
    """Returns the magazine-style HTML/CSS template"""
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Roboto:wght@400;500;700&display=swap');

        .magazine-article {
            font-family: 'Roboto', sans-serif;
            line-height: 1.8;
            color: #3a3a3a;
            max-width: 1200px;
            margin: 0 auto;
        }

        .hero-section {
            position: relative;
            height: 500px;
            background-size: cover;
            background-position: center;
            display: flex;
            align-items: flex-end;
            color: white;
            padding: 40px;
            margin-bottom: 40px;
        }

        .hero-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0) 100%);
        }

        .hero-section h1 {
            font-family: 'Playfair Display', serif;
            font-size: 3.5em;
            margin: 0;
            z-index: 1;
            position: relative;
        }

        .section-header {
            height: 350px;
            background-size: cover;
            background-position: center;
            display: flex;
            align-items: flex-end;
            color: white;
            padding: 30px;
            position: relative;
            margin: 40px 0 30px 0;
        }

        .section-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0) 100%);
        }

        .section-header h2 {
            font-family: 'Playfair Display', serif;
            font-size: 2.8em;
            margin: 0;
            z-index: 1;
            position: relative;
        }

        .content-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 40px;
            padding: 0 40px;
        }

        @media (max-width: 800px) {
            .content-grid {
                grid-template-columns: 1fr;
            }
        }

        .main-content h3 {
            font-family: 'Playfair Display', serif;
            color: #333;
            font-size: 2em;
            margin-top: 30px;
        }

        .main-content h4 {
            font-family: 'Roboto', sans-serif;
            font-weight: 700;
            color: #08b0c4;
            font-size: 1.5em;
            margin-top: 25px;
        }

        .sidebar {
            background-color: #f8f9fa;
            padding: 30px;
            border-radius: 8px;
            border-top: 5px solid #08b0c4;
            height: fit-content;
            position: sticky;
            top: 20px;
        }

        .sidebar h3 {
            font-family: 'Playfair Display', serif;
            color: #08b0c4;
            font-size: 1.6em;
            border-bottom: 2px solid #ff6b11;
            padding-bottom: 10px;
        }

        .pull-quote {
            font-family: 'Playfair Display', serif;
            font-size: 2em;
            color: #ff6b11;
            border-left: 5px solid #08b0c4;
            padding-left: 25px;
            margin: 40px 0;
            font-style: italic;
        }

        .stat-highlight {
            background-color: #e6fffa;
            border: 1px solid #08b0c4;
            padding: 20px;
            margin-bottom: 25px;
            border-radius: 8px;
            text-align: center;
        }

        .stat-highlight .number {
            font-size: 3.5em;
            font-weight: 700;
            color: #08b0c4;
            line-height: 1;
        }

        .stat-highlight .description {
            font-size: 1.1em;
            color: #333;
            margin-top: 10px;
        }

        .case-study-box {
            background-color: #fff3e0;
            border-left: 5px solid #ff6b11;
            padding: 25px;
            margin: 30px 0;
            border-radius: 0 8px 8px 0;
        }

        .case-study-box h4 {
            color: #ff6b11;
            margin-top: 0;
            font-family: 'Playfair Display', serif;
            font-size: 1.6em;
        }

        .info-box {
            background-color: #f0f2f5;
            border-left: 5px solid #08b0c4;
            padding: 20px 25px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }

        .warning-box {
            background: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 20px 25px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }

        ul, ol {
            padding-left: 25px;
            margin: 15px 0;
        }

        li {
            margin-bottom: 10px;
        }

        p {
            margin: 15px 0;
            font-size: 1.1em;
        }
    </style>
    """


def create_magazine_article_prompt(blog_post_idea, system_prompt):
    """Creates an enhanced prompt for generating magazine-style articles"""

    magazine_structure_prompt = """
You are an expert magazine writer creating in-depth, engaging articles for a professional business publication.

CRITICAL REQUIREMENTS:
- Minimum 1500 words (aim for 2000-2500 words)
- Use structured HTML with magazine-style formatting
- Include multiple sections with descriptive headers
- Add pull quotes, statistics, and examples throughout
- Write in an engaging, authoritative voice
- Include practical takeaways and actionable insights

STRUCTURE YOUR ARTICLE AS FOLLOWS:

<div class="magazine-article">
    <h1>[Compelling Main Title]</h1>

    <div class="main-content">
        <p class="introduction">[2-3 paragraph introduction that hooks the reader and establishes the topic's importance]</p>

        <h3>[First Major Section Heading]</h3>
        <p>[3-4 detailed paragraphs exploring this aspect]</p>

        <div class="pull-quote">[Extract a compelling quote from your content]</div>

        <h4>[Subsection 1]</h4>
        <p>[2-3 paragraphs with details]</p>

        <h4>[Subsection 2]</h4>
        <p>[2-3 paragraphs with details]</p>

        <div class="case-study-box">
            <h4>Real-World Example</h4>
            <p>[Include a specific case study or example]</p>
        </div>

        <h3>[Second Major Section Heading]</h3>
        <p>[3-4 detailed paragraphs]</p>

        <h4>[Subsection A]</h4>
        <p>[2-3 paragraphs]</p>
        <ul>
            <li>[Key point 1]</li>
            <li>[Key point 2]</li>
            <li>[Key point 3]</li>
        </ul>

        <div class="info-box">
            <h4>Expert Insight</h4>
            <p>[Professional tip or industry insight]</p>
        </div>

        <h3>[Third Major Section Heading]</h3>
        <p>[3-4 detailed paragraphs]</p>

        <h4>[Subsection I]</h4>
        <p>[2-3 paragraphs]</p>

        <h4>[Subsection II]</h4>
        <p>[2-3 paragraphs]</p>

        <div class="pull-quote">[Another compelling insight]</div>

        <h3>[Fourth Major Section: Practical Application]</h3>
        <p>[Explain how to implement these ideas]</p>

        <h4>Step-by-Step Implementation</h4>
        <ol>
            <li>[Step 1 with detailed explanation]</li>
            <li>[Step 2 with detailed explanation]</li>
            <li>[Step 3 with detailed explanation]</li>
        </ol>

        <div class="warning-box">
            <h4>⚠️ Common Pitfalls to Avoid</h4>
            <p>[List 3-4 mistakes to watch out for]</p>
        </div>

        <h3>Conclusion: Key Takeaways</h3>
        <p>[2-3 paragraphs summarizing the main points and providing final thoughts]</p>

        <div class="case-study-box">
            <h4>Action Steps</h4>
            <ul>
                <li>[Specific action 1]</li>
                <li>[Specific action 2]</li>
                <li>[Specific action 3]</li>
            </ul>
        </div>
    </div>
</div>

IMPORTANT GUIDELINES:
- Expand each section with rich detail, examples, and insights
- Use conversational but professional language
- Include statistics and data points when relevant (you can use realistic examples)
- Make each section substantive - no thin paragraphs
- Ensure the article provides genuine value and actionable information
- Use transitional phrases to connect sections smoothly
"""

    combined_prompt = f"{system_prompt}\n\n{magazine_structure_prompt}\n\nTOPIC: {blog_post_idea}"
    return combined_prompt


def process_blog_post_idea_v3(blog_post_idea, user_id, system_prompt):
    """
    Process blog post idea using OpenAI GPT-5-mini with Responses API and reasoning
    Returns enhanced magazine-style article with structured HTML
    """
    load_user_env(user_id)
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        logger.error(f"OpenAI API key not found for user {user_id}")
        return None

    client = OpenAI(api_key=api_key)

    try:
        enhanced_prompt = create_magazine_article_prompt(blog_post_idea, system_prompt)

        logger.debug(f"Sending request to OpenAI GPT-5-mini with reasoning. Idea length: {len(blog_post_idea)}")

        # Use Responses API with GPT-5-mini with reasoning
        response = client.responses.create(
            model="gpt-5-mini",
            input=enhanced_prompt,
            text={"verbosity": "medium"},  # Medium verbosity for comprehensive articles
            max_output_tokens=16000,  # Sufficient for 1500-2500 word articles
            instructions="You are an expert magazine writer specializing in creating long-form, engaging, and professionally formatted articles. Use your reasoning capabilities to structure compelling narratives with logical flow."
        )

        # Extract content from Responses API format
        # Use output_text for GPT-5-mini (simpler than iterating output items)
        full_article = response.output_text if hasattr(response, 'output_text') else ""

        # Fallback to output items if output_text is empty
        if not full_article and hasattr(response, 'output'):
            for item in response.output:
                if hasattr(item, 'type') and item.type == "text":
                    full_article += item.text

        full_article = full_article.strip()
        logger.debug(f"Received response from OpenAI. Article length: {len(full_article)} characters")

        # Extract title (first h1 tag or first line)
        if "<h1>" in full_article:
            title_start = full_article.find("<h1>") + 4
            title_end = full_article.find("</h1>")
            title = full_article[title_start:title_end]
        else:
            lines = full_article.split('\n')
            title = lines[0].strip()
            if title.startswith('#'):
                title = title.lstrip('#').strip()

        # Add CSS to the content
        content_with_style = get_magazine_html_template() + "\n" + full_article

        logger.info(f"Successfully processed blog post with reasoning. Title: {title[:50]}...")
        return {
            "full_article": full_article,
            "title": title,
            "content": content_with_style
        }
    except Exception as e:
        logger.error(f"OpenAI API error in process_blog_post_idea_v3: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


def generate_photographic_image_prompts(full_article, num_images=4):
    """
    Generate multiple PHOTOGRAPHIC image prompts for different sections
    Uses GPT-5-mini with reasoning to create professional magazine photography prompts
    """
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    system_instructions = f"""You are a professional photography art director for a business magazine.

Your task: Analyze this article and create {num_images} distinct image prompts for magazine photography.

CRITICAL REQUIREMENTS FOR EACH PROMPT:
1. MUST be photorealistic, shot with professional camera equipment
2. MUST specify: "professional photography", "high-end camera", "magazine quality"
3. MUST include lighting details: "studio lighting" or "natural light" or "golden hour"
4. MUST avoid: illustrations, drawings, animations, cartoons, CGI, 3D renders
5. MUST specify composition: "shallow depth of field", "bokeh", "wide angle", etc.
6. MUST include setting/context relevant to that section
7. Target aspect ratio: 16:9 for hero, 4:3 for sections

PROMPT STRUCTURE:
"Professional [subject] photograph, shot with [camera type], [lighting], [composition], [mood/atmosphere], magazine editorial quality, photorealistic, ultra high definition"

IMAGE ASSIGNMENTS:
1. HERO IMAGE - Dramatic, cinematic opening shot for main article theme
2. SECTION IMAGE 1 - Supporting the first major section topic
3. SECTION IMAGE 2 - Supporting the second major section topic
4. SECTION IMAGE 3 - Supporting the third major section topic

Return a JSON array with {num_images} prompts, each optimized for photorealistic magazine photography.

Format: {{"prompts": ["prompt1", "prompt2", "prompt3", "prompt4"]}}
"""

    try:
        # Use Responses API for better prompt quality
        response = client.responses.create(
            model="gpt-5-mini",
            input=f"Article content:\n{full_article[:3000]}",  # First 3000 chars
            text={
                "verbosity": "low",  # Concise prompts
                "format": {"type": "json"}  # Request JSON output
            },
            max_output_tokens=2000,  # Sufficient for 4 image prompts
            instructions=system_instructions
        )

        # Extract JSON from response
        import json
        result_text = response.output_text if hasattr(response, 'output_text') else ""

        # Fallback to output items if output_text is empty
        if not result_text and hasattr(response, 'output'):
            for item in response.output:
                if hasattr(item, 'type') and item.type == "text":
                    result_text += item.text

        result = json.loads(result_text)
        prompts = result.get("prompts", [])

        logger.info(f"Generated {len(prompts)} photographic image prompts with reasoning")
        return prompts

    except Exception as e:
        logger.error(f"Error generating photographic prompts: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Fallback to single prompt
        return [generate_fallback_photo_prompt(full_article)]


def generate_fallback_photo_prompt(full_article):
    """Generate a single photographic hero image prompt - fallback method"""
    return "Professional business magazine cover photography, modern office environment, shot with Canon EOS R5, natural window lighting, shallow depth of field with bokeh, corporate professional atmosphere, ultra high definition, photorealistic, editorial quality"


def generate_images_with_seedream(prompts, user_id, aspect_ratio="16:9"):
    """
    Generate 2K resolution photorealistic images using SeeDream-4
    Supports text rendering on images for magazine overlays
    """
    load_user_env(user_id)
    replicate_token = os.getenv("REPLICATE_API_TOKEN")

    if not replicate_token:
        logger.error(f"Replicate API token not found for user {user_id}")
        return []

    replicate.api_token = replicate_token
    images = []

    for i, prompt in enumerate(prompts):
        try:
            logger.debug(f"Generating 2K image {i+1}/{len(prompts)} with SeeDream-4")
            logger.debug(f"Prompt: {prompt[:150]}...")

            # SeeDream-4 API parameters
            input_data = {
                "prompt": prompt,
                "size": "2K",  # 2K resolution
                "aspect_ratio": aspect_ratio,
                "max_images": 1
            }

            # Run SeeDream-4 model
            output = replicate.run(
                "bytedance/seedream-4",
                input=input_data
            )

            if output:
                # SeeDream-4 returns image URL(s)
                if isinstance(output, list) and len(output) > 0:
                    image_url = output[0]
                elif isinstance(output, str):
                    image_url = output
                else:
                    image_url = str(output)

                images.append(image_url)
                logger.info(f"SeeDream-4 image {i+1} generated: {image_url}")
            else:
                logger.error(f"No output from SeeDream-4 for image {i+1}")
                images.append(None)

        except Exception as e:
            logger.error(f"Error generating SeeDream-4 image {i+1}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            images.append(None)

    return images


def create_blog_post_with_images_v3(blog_post_idea, user_id, system_prompt):
    """
    V3 Main function - Complete article creation with:
    - GPT-5-mini with Responses API and reasoning
    - SeeDream-4 for 2K photorealistic images
    - Enhanced photographic prompt engineering
    """
    logger.info(f"Starting V3 enhanced blog post creation for user {user_id}")
    logger.debug(f"Blog post idea: {blog_post_idea[:100]}...")

    # Step 1: Generate article content with GPT-5-mini reasoning
    processed_post = process_blog_post_idea_v3(blog_post_idea, user_id, system_prompt)
    if not processed_post:
        logger.error("Failed to process blog post idea with GPT-5-mini")
        return None, "Failed to process blog post idea"

    logger.info(f"Article processed with reasoning. Title: {processed_post['title'][:50]}...")
    logger.info(f"Article length: {len(processed_post['content'])} characters")

    # Step 2: Generate photographic prompts using reasoning
    photo_prompts = generate_photographic_image_prompts(processed_post['full_article'], num_images=4)

    if not photo_prompts or len(photo_prompts) == 0:
        logger.error("Failed to generate photographic prompts")
        return None, "Failed to generate image prompts"

    logger.info(f"Generated {len(photo_prompts)} photographic prompts")

    # Step 3: Generate 2K images with SeeDream-4
    # Hero image in 16:9, section images in 4:3
    hero_image = generate_images_with_seedream([photo_prompts[0]], user_id, aspect_ratio="16:9")
    section_images = generate_images_with_seedream(photo_prompts[1:], user_id, aspect_ratio="4:3")

    all_images = hero_image + section_images

    if not all_images or not any(all_images):
        logger.error("Failed to generate images with SeeDream-4")
        return None, "Failed to generate images"

    logger.info(f"Successfully created V3 blog post with {len([img for img in all_images if img])} SeeDream-4 images")

    return {
        "title": processed_post['title'],
        "content": processed_post['content'],
        "hero_image_url": all_images[0] if all_images[0] else None,
        "section_images": all_images[1:] if len(all_images) > 1 else [],
        "all_images": all_images
    }, None