"""
claude_formatter.py - STEP 4 (Replacement): AI-Powered Magazine Formatting

Uses Claude Sonnet 4.5 API to format articles with intelligent layout decisions.
Replaces the rigid magazine_formatter.py with AI that understands visual hierarchy.

KEY ADVANTAGE: Claude makes smart decisions about:
- Where to place pull quotes for maximum impact
- How to break up dense text sections
- Optimal image placement and sizing
- Visual rhythm and pacing
"""

import os
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
import anthropic

logger = logging.getLogger(__name__)


def load_user_env(user_id: int) -> None:
    """Load user-specific environment variables."""
    env_file = f".env.user_{user_id}"
    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)


def get_premium_layout_example() -> str:
    """
    Returns the Premium Magazine layout HTML as an example for Claude.
    This is the template Claude will follow when formatting articles.
    """
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Example Article</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Roboto:wght@400;500;700&display=swap');

        :root {
            --brand-color: #4a9d5f;
            --accent-color: #8b7355;
        }

        /* WordPress Editor Compatibility - Reset unwanted styles */
        .magazine-article-wrapper * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        /* Override WordPress/Elementor default heading colors */
        .magazine-article-wrapper h1,
        .magazine-article-wrapper h2,
        .magazine-article-wrapper h3,
        .magazine-article-wrapper h4,
        .magazine-article-wrapper h5,
        .magazine-article-wrapper h6 {
            color: inherit !important;
        }

        body {
            font-family: 'Roboto', sans-serif;
            line-height: 1.8;
            color: #3a3a3a;
            background-color: #f0f2f5;
        }
        
        .magazine-container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: #fff;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .cover {
            background: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.5)), url('HERO_IMAGE_URL') no-repeat center center/cover;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            align-items: center;
            text-align: center;
            color: white !important;
            padding: 20px;
        }

        .cover h1 {
            font-family: 'Playfair Display', serif !important;
            font-size: 4.5em !important;
            margin: 0 !important;
            color: white !important;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.6) !important;
            line-height: 1.1 !important;
        }
        
        .cover .subtitle {
            font-size: 1.6em !important;
            margin: 20px 0 0 !important;
            font-weight: 400 !important;
            max-width: 800px;
            color: white !important;
        }

        .cover .edition {
            background-color: var(--brand-color) !important;
            padding: 10px 25px !important;
            margin-top: 30px !important;
            margin-bottom: 50px !important;
            font-weight: 700 !important;
            border-radius: 5px !important;
            font-size: 1.1em !important;
            color: white !important;
        }
        
        .section-header {
            height: 400px;
            background-size: cover;
            background-position: center;
            display: flex;
            align-items: flex-end;
            color: white !important;
            padding: 40px;
            position: relative;
        }

        .section-header::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0) 100%);
            z-index: 0;
        }

        .section-header h2 {
            font-family: 'Playfair Display', serif !important;
            font-size: 3.8em !important;
            margin: 0 !important;
            color: white !important;
            z-index: 1 !important;
            position: relative !important;
        }
        
        .content-area {
            padding: 50px 40px;
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 40px;
        }
        
        .main-column { font-size: 1.1em; }
        .main-column p { margin-bottom: 24px; }
        
        .sidebar {
            background-color: #f8f9fa;
            padding: 30px;
            border-radius: 8px;
            border-top: 5px solid var(--brand-color);
        }
        
        .sidebar h3 {
            font-family: 'Playfair Display', serif;
            color: var(--brand-color);
            font-size: 1.6em;
            border-bottom: 2px solid var(--accent-color);
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        .stat-highlight {
            background-color: color-mix(in srgb, var(--brand-color) 10%, white);
            border: 1px solid var(--brand-color);
            padding: 20px;
            margin-bottom: 25px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-highlight .number {
            font-size: 4em;
            font-weight: 700;
            color: var(--brand-color);
            line-height: 1;
        }
        
        .stat-highlight .description {
            font-size: 1.1em;
            color: #333;
            margin-top: 10px;
        }
        
        .pull-quote {
            font-family: 'Playfair Display', serif;
            font-size: 2em;
            color: var(--accent-color);
            border-left: 5px solid var(--brand-color);
            padding-left: 25px;
            margin: 40px 0;
            font-style: italic;
        }
        
        .case-study-box {
            background-color: color-mix(in srgb, var(--accent-color) 15%, white);
            border-left: 5px solid var(--accent-color);
            padding: 25px;
            margin: 30px 0;
            border-radius: 0 8px 8px 0;
        }
        
        .case-study-box h4 {
            color: var(--accent-color);
            margin-top: 0;
            font-family: 'Playfair Display', serif;
            font-size: 1.6em;
        }
        
        .full-width-image {
            width: 100%;
            height: 400px;
            object-fit: cover;
            margin: 40px 0;
        }
        
        @media (max-width: 768px) {
            .cover h1 { font-size: 2.8em; }
            .content-area { grid-template-columns: 1fr; padding: 30px 20px; }
            .section-header { height: 250px; }
            .section-header h2 { font-size: 2.2em; }
        }
    </style>
</head>
<body>
    <div class="magazine-article-wrapper">
    <div class="magazine-container">
        <div class="cover">
            <h1>Article Title Here</h1>
            <p class="subtitle">Compelling subtitle that draws readers in</p>
            <p class="edition">AUTUMN 2025</p>
        </div>

        <div class="section-header" style="background-image: url('SECTION_IMAGE_1_URL');">
            <h2>First Section Heading</h2>
        </div>

        <div class="content-area">
            <div class="main-column">
                <p>Opening paragraph content...</p>

                <div class="pull-quote">
                    "Impactful quote from the article that reinforces key message."
                </div>

                <p>More content...</p>

                <div class="case-study-box">
                    <h4>Case Study or Highlight</h4>
                    <p>Important information in a highlighted box...</p>
                </div>

                <p>Additional paragraphs...</p>
            </div>

            <div class="sidebar">
                <h3>By The Numbers</h3>
                
                <div class="stat-highlight">
                    <div class="number">4x</div>
                    <div class="description">Relevant statistic description</div>
                </div>

                <div class="stat-highlight">
                    <div class="number">30%</div>
                    <div class="description">Another key metric</div>
                </div>
            </div>
        </div>

        <img src="SECTION_IMAGE_2_URL" class="full-width-image" alt="Descriptive alt text">

        <div class="content-area">
            <div class="main-column">
                <p>Continued article content...</p>
            </div>

            <div class="sidebar">
                <h3>Key Takeaways</h3>
                <p><strong>Point 1:</strong> Description</p>
                <p><strong>Point 2:</strong> Description</p>
            </div>
        </div>
    </div>
    </div><!-- .magazine-article-wrapper -->
</body>
</html>"""


def format_article_with_claude(
    article_html: str,
    title: str,
    hero_image_url: str,
    section_images: List[str],
    user_id: int,
    brand_colors: Optional[Dict[str, str]] = None,
    layout_style: str = "premium_magazine"
) -> Optional[str]:
    """
    Use Claude Sonnet 4.5 API to format article with intelligent layout decisions.
    
    Args:
        article_html: Raw article HTML from story generation
        title: Article title
        hero_image_url: URL for hero cover image
        section_images: List of section image URLs
        user_id: User ID for environment loading
        brand_colors: {"primary": "#color1", "accent": "#color2"}
        layout_style: Layout template to use (currently only "premium_magazine")
    
    Returns:
        Beautifully formatted HTML or None if error
    """
    load_user_env(user_id)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("[Claude Formatter] ANTHROPIC_API_KEY not found")
        return None
    
    # Default brand colors if not provided
    primary_color = brand_colors.get("primary", "#4a9d5f") if brand_colors else "#4a9d5f"
    accent_color = brand_colors.get("accent", "#8b7355") if brand_colors else "#8b7355"
    
    # Get layout example
    layout_example = get_premium_layout_example()
    
    # Prepare image URLs list for prompt
    section_image_urls = "\n".join([f"- {url}" for url in section_images])
    
    # Create prompt for Claude
    prompt = f"""You are an expert magazine layout designer. Format the following article content into a beautiful Premium Magazine layout.

ARTICLE TITLE: {title}

ARTICLE CONTENT (raw HTML):
{article_html}

AVAILABLE IMAGES:
Hero Image: {hero_image_url}
Section Images:
{section_image_urls}

BRAND COLORS:
Primary: {primary_color}
Accent: {accent_color}

LAYOUT EXAMPLE TO FOLLOW:
{layout_example}

YOUR TASK:
1. Use the layout example above as your template structure
2. Replace --brand-color and --accent-color CSS variables with the provided colors
3. Insert the article title and content into the appropriate sections
4. Use the hero image in the cover section (replace HERO_IMAGE_URL)
5. Create 2-3 section-header divs with section images (replace SECTION_IMAGE_*_URL)
6. Intelligently insert:
   - 2-3 pull quotes in the main-column (extract impactful quotes from content)
   - 3-4 stat-highlight boxes in sidebars (extract key metrics from content)
   - 1-2 case-study-box for important highlights
7. Break content into multiple content-area sections (2-3 sections total)
8. Place full-width-image breaks between major sections
9. Ensure visual rhythm and pacing - don't let text get too dense

CRITICAL REQUIREMENTS:
- Return ONLY the complete HTML document (no markdown code fences)
- Use the EXACT CSS structure from the example
- Replace ALL placeholder URLs with actual provided URLs
- Extract actual content from the article for pull quotes and stats
- Maintain the 2-column grid layout (main + sidebar)
- Ensure mobile responsive (@media query is already in example)
- WRAP all body content in: <div class="magazine-article-wrapper">...</div>
- This wrapper is CRITICAL for WordPress/Elementor compatibility

OUTPUT: Complete formatted HTML document ready for WordPress with wrapper div."""

    try:
        logger.info(f"[Claude Formatter] Formatting article: {title[:60]}")
        logger.info(f"[Claude Formatter] Brand colors: {primary_color}, {accent_color}")
        logger.info(f"[Claude Formatter] Images: Hero + {len(section_images)} sections")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",  # Latest Sonnet 4.5
            max_tokens=8000,  # Large enough for complete HTML
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract response
        formatted_html = message.content[0].text
        
        # Clean any markdown code fences if Claude added them
        if formatted_html.startswith("```html"):
            formatted_html = formatted_html.replace("```html\n", "").replace("\n```", "")
        elif formatted_html.startswith("```"):
            formatted_html = formatted_html.replace("```\n", "").replace("\n```", "")
        
        logger.info(f"[Claude Formatter] Successfully formatted article ({len(formatted_html)} chars)")
        
        return formatted_html.strip()
        
    except Exception as e:
        logger.error(f"[Claude Formatter] Error formatting article: {e}")
        logger.debug(f"[Claude Formatter] Traceback: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    # Test the formatter
    logging.basicConfig(level=logging.INFO)
    
    test_html = """
    <h1>The Future of AI in Healthcare</h1>
    <h2>Introduction</h2>
    <p>Artificial intelligence is revolutionizing healthcare...</p>
    <h2>AI-Powered Diagnostics</h2>
    <p>Machine learning models can now detect diseases with 99% accuracy...</p>
    <p>Studies show AI reduces diagnosis time by 40% while improving accuracy.</p>
    <h2>The Road Ahead</h2>
    <p>As AI continues to evolve, the future of healthcare looks promising...</p>
    """
    
    result = format_article_with_claude(
        article_html=test_html,
        title="The Future of AI in Healthcare",
        hero_image_url="https://example.com/hero.jpg",
        section_images=[
            "https://example.com/section1.jpg",
            "https://example.com/section2.jpg",
            "https://example.com/section3.jpg"
        ],
        user_id=1,
        brand_colors={"primary": "#1a73e8", "accent": "#fbbc04"}
    )
    
    if result:
        print(f"\n✅ Formatted successfully - {len(result)} characters")
        print(f"\nFirst 500 chars:\n{result[:500]}")
    else:
        print("\n❌ Formatting failed")