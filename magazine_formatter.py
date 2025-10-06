"""
magazine_formatter.py - STEP 4: Magazine Layout Assembly

Takes structured article data and assembles complete magazine layout with:
- Brand colors and typography
- Magazine components (stats, pull quotes, case studies, sidebars)
- Section header images with overlays
- Executive summary section
- Responsive grid layouts

This is the final assembly step that produces WordPress-ready HTML.
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Complete Magazine CSS Template with Brand Color Support
MAGAZINE_CSS_TEMPLATE = """
/* ===== EZWAi Magazine CSS ===== */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Roboto:wght@400;500;700&display=swap');

:root {{
    --brand-primary: {brand_primary};
    --brand-accent: {brand_accent};
    --text-ink: #3a3a3a;
    --text-muted: #4b5563;
    --bg-paper: #fff;
    --bg-light: #f0f2f5;
    --rule: #e5e7eb;
}}

* {{
    box-sizing: border-box;
}}

.magazine-container {{
    max-width: 1200px;
    margin: 0 auto;
    background-color: var(--bg-paper);
    padding: 0;
}}

.magazine-article {{
    font-family: 'Roboto', sans-serif;
    color: var(--text-ink);
    line-height: 1.8;
    font-size: 1.1em;
    padding: 0 40px 64px;
}}

/* Hero Section */
.hero-section {{
    height: 100vh;
    background-size: cover;
    background-position: center;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    align-items: center;
    text-align: center;
    color: white;
    padding: 20px;
    position: relative;
    margin-bottom: 60px;
}}

.hero-section::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.5));
}}

.hero-section h1 {{
    font-family: 'Playfair Display', serif;
    font-size: clamp(3em, 6vw, 4.5em);
    margin: 0 0 20px 0;
    text-shadow: 3px 3px 6px rgba(0,0,0,0.6);
    line-height: 1.1;
    position: relative;
    z-index: 1;
    max-width: 900px;
}}

.hero-section .subtitle {{
    font-size: 1.6em;
    margin: 20px 0;
    font-weight: 400;
    max-width: 800px;
    position: relative;
    z-index: 1;
}}

.hero-section .edition {{
    background-color: var(--brand-accent);
    padding: 10px 25px;
    margin: 30px 0 50px;
    font-weight: 700;
    border-radius: 5px;
    font-size: 1.1em;
    position: relative;
    z-index: 1;
}}

/* Executive Summary */
.executive-summary {{
    background: linear-gradient(135deg, var(--brand-primary) 0%, #0891a3 100%);
    color: white;
    padding: 60px 40px;
    margin-bottom: 40px;
}}

.executive-summary h2 {{
    font-family: 'Playfair Display', serif;
    font-size: 3em;
    text-align: center;
    margin-bottom: 40px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}}

.stat-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 30px;
    margin-bottom: 40px;
}}

.stat-card {{
    background: rgba(255,255,255,0.15);
    padding: 25px;
    border-radius: 8px;
    backdrop-filter: blur(10px);
    text-align: center;
}}

.stat-card .number {{
    font-size: 3.5em;
    font-weight: 700;
    color: var(--brand-accent);
}}

.stat-card .description {{
    font-size: 1.1em;
    margin-top: 10px;
}}

.summary-intro {{
    background: rgba(255,255,255,0.2);
    padding: 35px;
    border-radius: 8px;
    backdrop-filter: blur(10px);
    border-left: 5px solid var(--brand-accent);
    font-size: 1.2em;
    line-height: 1.8;
}}

/* Section Headers */
.section-header {{
    height: 400px;
    background-size: cover;
    background-position: center;
    display: flex;
    align-items: flex-end;
    color: white;
    padding: 40px;
    position: relative;
    margin: 60px 0 40px;
    border-radius: 0;
}}

.section-header::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0) 100%);
}}

.section-header h2 {{
    font-family: 'Playfair Display', serif;
    font-size: 3.8em;
    margin: 0;
    z-index: 1;
    position: relative;
    color: white;
}}

/* Typography */
.magazine-article h2 {{
    font-family: 'Playfair Display', serif;
    color: #333;
    font-size: 2em;
    margin: 36px 0 20px;
}}

.magazine-article h3 {{
    font-family: 'Roboto', sans-serif;
    font-weight: 700;
    color: var(--brand-primary);
    font-size: 1.5em;
    margin: 28px 0 12px;
}}

.magazine-article h4 {{
    font-family: 'Roboto', sans-serif;
    font-weight: 700;
    color: var(--brand-primary);
    font-size: 1.3em;
    margin: 20px 0 10px;
}}

.magazine-article p {{
    margin: 12px 0;
}}

.magazine-article ul, .magazine-article ol {{
    padding-left: 25px;
    margin: 14px 0;
}}

.magazine-article li {{
    margin: 6px 0;
}}

/* Pull Quotes */
.pull-quote {{
    font-family: 'Playfair Display', serif;
    font-size: 2em;
    color: var(--brand-accent);
    border-left: 5px solid var(--brand-primary);
    padding-left: 25px;
    margin: 40px 0;
    font-style: italic;
    line-height: 1.4;
}}

/* Stat Highlights */
.stat-highlight {{
    background-color: #e6fffa;
    border: 1px solid var(--brand-primary);
    padding: 20px;
    margin: 25px 0;
    border-radius: 8px;
    text-align: center;
}}

.stat-highlight .number {{
    font-size: 4em;
    font-weight: 700;
    color: var(--brand-primary);
    line-height: 1;
}}

.stat-highlight .description {{
    font-size: 1.1em;
    color: #333;
    margin-top: 10px;
}}

/* Case Study Boxes */
.case-study-box {{
    background-color: #fff3e0;
    border-left: 5px solid var(--brand-accent);
    padding: 25px;
    margin: 30px 0;
    border-radius: 0 8px 8px 0;
}}

.case-study-box h4 {{
    color: var(--brand-accent);
    margin-top: 0;
    font-family: 'Playfair Display', serif;
    font-size: 1.6em;
}}

.case-study-box .profile {{
    font-style: italic;
    margin-bottom: 15px;
    color: var(--text-muted);
}}

.case-study-box .challenge,
.case-study-box .solution {{
    margin: 15px 0;
}}

.case-study-box .results {{
    background: rgba(255, 107, 17, 0.1);
    padding: 15px;
    border-radius: 5px;
    margin: 15px 0;
}}

.case-study-box .results ul {{
    margin: 10px 0;
    padding-left: 20px;
}}

.case-study-box .quote {{
    font-style: italic;
    border-left: 3px solid var(--brand-accent);
    padding-left: 15px;
    margin-top: 15px;
    color: var(--text-muted);
}}

/* Sidebars */
.sidebar-box {{
    background-color: #f8f9fa;
    padding: 30px;
    border-radius: 8px;
    border-top: 5px solid var(--brand-primary);
    margin: 30px 0;
}}

.sidebar-box h3 {{
    color: var(--brand-primary);
    font-size: 1.6em;
    border-bottom: 2px solid var(--brand-accent);
    padding-bottom: 10px;
    margin-top: 0;
}}

.sidebar-box h4 {{
    font-size: 1.2em;
    margin-top: 20px;
}}

/* Warning/Alert Boxes */
.warning-box {{
    background: #fff3cd;
    border-left: 5px solid #ffc107;
    padding: 20px;
    margin: 20px 0;
    border-radius: 8px;
}}

.risk-alert {{
    background: #fff5f5;
    border-left: 5px solid #e53e3e;
    padding: 25px;
    border-radius: 8px;
    margin: 20px 0;
}}

.risk-alert h4 {{
    color: #e53e3e;
    margin-top: 0;
}}

/* Content Grid */
.content-area {{
    padding: 50px 0;
    display: grid;
    grid-template-columns: 1fr;
    gap: 40px;
}}

@media (min-width: 800px) {{
    .content-area.with-sidebar {{
        grid-template-columns: 2fr 1fr;
    }}
}}

/* Mobile Responsive */
@media screen and (max-width: 768px) {{
    .magazine-article {{
        padding: 30px 15px;
    }}
    
    .hero-section {{
        height: 100vh;
        padding: 40px 20px 60px;
    }}
    
    .hero-section h1 {{
        font-size: 2.8em;
    }}
    
    .hero-section .subtitle {{
        font-size: 1.2em;
    }}
    
    .section-header {{
        height: 250px;
        padding: 20px;
    }}
    
    .section-header h2 {{
        font-size: 2.2em;
    }}
    
    .pull-quote {{
        font-size: 1.3em;
        padding-left: 15px;
        margin: 20px 0;
    }}
    
    .stat-highlight .number {{
        font-size: 2.5em;
    }}
    
    .case-study-box,
    .sidebar-box {{
        padding: 15px;
    }}
    
    .content-area.with-sidebar {{
        grid-template-columns: 1fr;
    }}
}}
"""


def load_user_env(user_id: int) -> None:
    """Load user-specific environment variables."""
    env_file = f".env.user_{user_id}"
    if os.path.exists(env_file):
        load_dotenv(env_file)


def insert_component_after_paragraph(soup: BeautifulSoup, paragraph_index: int, component_html: str):
    """Insert component HTML after the Nth paragraph tag."""
    paragraphs = soup.find_all('p')
    if 0 <= paragraph_index < len(paragraphs):
        target = paragraphs[paragraph_index]
        component_soup = BeautifulSoup(component_html, 'html.parser')
        target.insert_after(component_soup)
        logger.debug(f"Inserted component after paragraph {paragraph_index}")
    else:
        logger.warning(f"Paragraph index {paragraph_index} out of range")


def insert_component_after_heading(soup: BeautifulSoup, heading_text: str, component_html: str):
    """Insert component HTML after H2 heading with matching text."""
    for h2 in soup.find_all('h2'):
        if h2.get_text(strip=True) == heading_text.strip():
            component_soup = BeautifulSoup(component_html, 'html.parser')
            h2.insert_after(component_soup)
            logger.debug(f"Inserted component after heading: {heading_text[:50]}")
            return
    logger.warning(f"Heading not found: {heading_text[:50]}")


def build_pull_quote(content: str) -> str:
    """Build pull quote HTML."""
    return f'<div class="pull-quote">{content}</div>'


def build_stat_highlight(number: str, description: str) -> str:
    """Build stat highlight box HTML."""
    return f'''
    <div class="stat-highlight">
        <div class="number">{number}</div>
        <div class="description">{description}</div>
    </div>
    '''


def build_case_study(data: Dict) -> str:
    """Build case study box HTML."""
    results_html = ""
    if "results" in data and data["results"]:
        results_items = "\n".join([f"<li>{r}</li>" for r in data["results"]])
        results_html = f'''
        <div class="results">
            <p><strong>Results:</strong></p>
            <ul>{results_items}</ul>
        </div>
        '''
    
    quote_html = ""
    if "quote" in data and data["quote"]:
        quote_html = f'<p class="quote">"{data["quote"]}"</p>'
    
    profile_html = ""
    if "profile" in data and data["profile"]:
        profile_html = f'<p class="profile">{data["profile"]}</p>'
    
    return f'''
    <div class="case-study-box">
        <h4>{data.get("title", "Case Study")}</h4>
        {profile_html}
        <p class="challenge"><strong>Challenge:</strong> {data.get("challenge", "")}</p>
        <p class="solution"><strong>Solution:</strong> {data.get("solution", "")}</p>
        {results_html}
        {quote_html}
    </div>
    '''


def build_sidebar(title: str, content: str) -> str:
    """Build sidebar box HTML."""
    return f'''
    <div class="sidebar-box">
        <h3>{title}</h3>
        {content}
    </div>
    '''


def build_executive_summary(summary_data: Dict, primary_color: str = "#08b2c6", accent_color: str = "#ff6b11") -> str:
    """Build executive summary section with stats grid and brand colors."""
    if not summary_data:
        return ""
    
    intro = summary_data.get("intro", "")
    key_stats = summary_data.get("key_stats", [])
    
    stat_cards = ""
    for stat in key_stats:
        stat_cards += f'''
        <div style="background: white; padding: 25px; border-radius: 10px; text-align: center;">
            <div style="color: {accent_color}; font-size: 3em; font-weight: 900; line-height: 1;">{stat.get("number", "")}</div>
            <div style="color: #2c3e50; font-size: 1em; margin-top: 12px;">{stat.get("description", "")}</div>
        </div>
        '''

    return f'''
    <div style="background: linear-gradient(135deg, {primary_color} 0%, {accent_color} 100%); color: white; padding: 60px 40px; margin-bottom: 40px; border-radius: 12px;">
        <h2 style="font-family: 'Playfair Display', Georgia, serif; font-size: 3em; text-align: center; margin-bottom: 40px; font-weight: 800;">Executive Summary</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px;">
            {stat_cards}
        </div>
        <div style="max-width: 800px; margin: 0 auto; font-size: 1.1em; line-height: 1.7;">
            <p>{intro}</p>
        </div>
    </div>
    '''


def apply_magazine_styling(
    article_data: Dict,
    hero_image_url: str,
    section_images: List[Dict[str, str]],
    user_id: int,
    brand_colors: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """
    Assemble complete magazine layout from structured article data.

    Args:
        article_data: Structured data from story_generation.py
            {
                "title": str,
                "html": str,
                "executive_summary": {...},
                "components": [...]
            }
        hero_image_url: WordPress URL for hero image
        section_images: [{"heading": "...", "url": "..."}]
        user_id: User ID for environment
        brand_colors: Optional {"primary": "#08b2c6", "accent": "#ff6b11"}

    Returns:
        Complete styled HTML ready for WordPress
    """
    load_user_env(user_id)

    try:
        title = article_data.get("title", "Article")
        html_content = article_data.get("html", "")
        components = article_data.get("components", [])
        exec_summary = article_data.get("executive_summary", {})

        logger.info(f"[Formatter] Assembling magazine layout for: {title[:60]}")
        logger.info(f"[Formatter] Components to insert: {len(components)}")

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove H1 from body (will be in hero section)
        h1 = soup.find('h1')
        if h1:
            h1.decompose()

        # Insert components based on metadata
        for component in components:
            comp_type = component.get("type")
            
            if comp_type == "pull_quote":
                component_html = build_pull_quote(component.get("content", ""))
                if "insert_after_paragraph" in component:
                    insert_component_after_paragraph(
                        soup,
                        component["insert_after_paragraph"] - 1,  # 0-indexed
                        component_html
                    )
            
            elif comp_type == "stat_highlight":
                component_html = build_stat_highlight(
                    component.get("number", ""),
                    component.get("description", "")
                )
                if "insert_after_paragraph" in component:
                    insert_component_after_paragraph(
                        soup,
                        component["insert_after_paragraph"] - 1,
                        component_html
                    )
            
            elif comp_type == "case_study":
                component_html = build_case_study(component)
                if "insert_after_heading" in component:
                    insert_component_after_heading(
                        soup,
                        component["insert_after_heading"],
                        component_html
                    )
            
            elif comp_type == "sidebar":
                component_html = build_sidebar(
                    component.get("title", ""),
                    component.get("content", "")
                )
                if "insert_after_heading" in component:
                    insert_component_after_heading(
                        soup,
                        component["insert_after_heading"],
                        component_html
                    )

        # Wrap section H2s in section-header divs with images
        section_image_map = {img["heading"]: img["url"] for img in section_images}
        
        for h2 in soup.find_all('h2'):
            heading_text = h2.get_text(strip=True)
            image_url = section_image_map.get(heading_text)
            
            if image_url:
                # Create section header wrapper
                section_div = soup.new_tag('div', attrs={'class': 'section-header', 'style': f'background-image: url({image_url});'})
                h2.wrap(section_div)
                logger.debug(f"Wrapped H2 in section-header: {heading_text[:50]}")

        # Apply brand colors (use defaults if not provided)
        primary_color = brand_colors.get("primary", "#08b2c6") if brand_colors else "#08b2c6"
        accent_color = brand_colors.get("accent", "#ff6b11") if brand_colors else "#ff6b11"

        # Build hero with inline styles (16:9 aspect ratio)
        hero_html = f'''
        <div style="
            aspect-ratio: 16 / 9;
            width: 100%;
            height: auto;
            min-height: 320px;
            background: linear-gradient(135deg, {primary_color} 0%, {accent_color} 100%);
            background-image: url('{hero_image_url}');
            background-size: contain;
            background-position: center;
            background-repeat: no-repeat;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            align-items: center;
            text-align: center;
            color: white;
            padding: 20px;
            position: relative;
            margin-bottom: 60px;
            border-radius: 12px;
        ">
            <div style="position: absolute; inset: 0; background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.7)); border-radius: 12px;"></div>
            <h1 style="
                font-family: 'Playfair Display', Georgia, serif;
                font-size: clamp(2.5em, 5vw, 3.5em);
                margin: 0 0 20px 0;
                color: white !important;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.9), 0 0 20px rgba(0,0,0,0.8);
                line-height: 1.1;
                position: relative;
                z-index: 1;
                max-width: 900px;
                font-weight: 900;
            ">{title}</h1>
        </div>
        '''

        exec_summary_html = build_executive_summary(exec_summary, primary_color, accent_color)

        # Add inline styles to section headers (21:9 aspect ratio)
        for section_div in soup.find_all('div', attrs={'class': 'section-header'}):
            bg_image = section_div.get('style', '').replace('background-image: url(', '').replace(');', '')
            section_div.attrs['style'] = f'''
                aspect-ratio: 21 / 9;
                width: 100%;
                height: auto;
                min-height: 280px;
                background-image: url({bg_image});
                background-size: cover;
                background-position: center;
                border-radius: 16px;
                display: flex;
                align-items: flex-end;
                color: white;
                margin: 40px 0 24px;
                position: relative;
                overflow: hidden;
            '''
            # Add overlay
            overlay = soup.new_tag('div', attrs={'style': 'position: absolute; inset: 0; background: linear-gradient(180deg, rgba(0,0,0,0) 20%, rgba(0,0,0,0.65) 100%);'})
            section_div.insert(0, overlay)
            # Style the h2
            h2 = section_div.find('h2')
            if h2:
                h2.attrs['style'] = '''
                    font-family: 'Playfair Display', Georgia, serif;
                    font-weight: 800;
                    font-size: clamp(1.75em, 3vw, 2.5em);
                    position: relative;
                    z-index: 1;
                    color: white !important;
                    margin: 0 0 14px 16px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.9), 0 0 15px rgba(0,0,0,0.7);
                '''

        # Add inline styles to components
        for pull_quote in soup.find_all('div', attrs={'class': 'pull-quote'}):
            pull_quote.attrs['style'] = f'''
                border-left: 5px solid {primary_color};
                background-color: #f0f9fa;
                padding: 25px 30px;
                margin: 30px 0;
                font-size: 1.3em;
                font-style: italic;
                color: #2c3e50;
                border-radius: 0 8px 8px 0;
            '''

        for stat in soup.find_all('div', attrs={'class': 'stat-highlight'}):
            stat.attrs['style'] = f'''
                background-color: {accent_color};
                color: white;
                padding: 30px;
                margin: 30px 0;
                text-align: center;
                border-radius: 12px;
            '''
            number = stat.find('div', attrs={'class': 'number'})
            if number:
                number.attrs['style'] = 'font-size: 3.5em; font-weight: 900; line-height: 1;'
            desc = stat.find('div', attrs={'class': 'description'})
            if desc:
                desc.attrs['style'] = 'font-size: 1.1em; margin-top: 12px; opacity: 0.95;'

        for case_study in soup.find_all('div', attrs={'class': 'case-study-box'}):
            case_study.attrs['style'] = '''
                background-color: #f5f5f5;
                border: 2px solid #ddd;
                border-radius: 12px;
                padding: 30px;
                margin: 30px 0;
            '''

        # Style basic article content
        article_style = f'''
            max-width: 1080px;
            margin: 0 auto;
            padding: 0 24px 64px;
            font-family: Inter, system-ui, sans-serif;
            line-height: 1.78;
            font-size: 1.0625rem;
            color: #171717;
        '''

        final_html = f'''
        <div style="max-width: 1200px; margin: 0 auto; background-color: #fff; padding: 0;">
            {hero_html}
            {exec_summary_html}
            <div style="{article_style}">
                {str(soup)}
            </div>
        </div>
        '''

        logger.info(f"[Formatter] Assembly complete - {len(final_html)} characters")

        return final_html

    except Exception as e:
        logger.error(f"[Formatter] Error assembling layout: {e}")
        logger.debug(f"[Formatter] Traceback: {e}", exc_info=True)

        # EMERGENCY FALLBACK: Save raw article content to prevent total loss
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            fallback_path = f"emergency_article_{user_id}_{timestamp}.html"

            fallback_content = f"""
            <h1>{article_data.get('title', 'Untitled Article')}</h1>
            <div style="background: #ffe6e6; padding: 20px; margin: 20px 0; border-left: 4px solid #d00;">
                <strong>⚠️ STYLING FAILED - RAW CONTENT BELOW</strong><br>
                Error: {str(e)}<br>
                Time: {timestamp}
            </div>
            {article_data.get('html', '<p>No content available</p>')}
            """

            with open(fallback_path, 'w', encoding='utf-8') as f:
                f.write(fallback_content)

            logger.error(f"[Formatter] EMERGENCY: Saved raw article to {fallback_path}")
            logger.error(f"[Formatter] Article title: {article_data.get('title', 'Unknown')}")
            logger.error(f"[Formatter] Hero image: {hero_image_url}")

            # Return the fallback content so it's not completely lost
            return fallback_content

        except Exception as fallback_error:
            logger.error(f"[Formatter] Even fallback save failed: {fallback_error}")
            return None


if __name__ == "__main__":
    # Test module
    logging.basicConfig(level=logging.INFO)

    test_data = {
        "title": "AI Agents in Used Car Retail",
        "html": "<h2>Introduction</h2><p>Test content...</p>",
        "executive_summary": {
            "intro": "Test intro text",
            "key_stats": [
                {"number": "43%", "description": "Increase in appointments"}
            ]
        },
        "components": [
            {
                "type": "pull_quote",
                "content": "Test quote",
                "insert_after_paragraph": 1
            }
        ]
    }

    result = apply_magazine_styling(
        article_data=test_data,
        hero_image_url="https://example.com/hero.jpg",
        section_images=[],
        user_id=1
    )

    if result:
        print(f"\nSuccess - {len(result)} characters")
    else:
        print("\nFailed")