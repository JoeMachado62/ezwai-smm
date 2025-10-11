"""
Test Local Article Formatter V2 - Template-Based with Downloaded Images

Since base64 images cause Claude API to exceed token limits (206k tokens),
this version:
1. Downloads images to local disk
2. Uses template formatter (magazine_formatter.py) instead of Claude
3. Embeds images as base64 in final HTML only (not in API call)
4. Creates self-contained HTML file
"""

import os
import sys
import logging
import requests
import base64
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Import formatters
from magazine_formatter import apply_magazine_styling

# Use fresher Replicate images (from your most recent test)
# These are the 5 from Oct 10 23:23-23:24 that succeeded
REPLICATE_IMAGES = [
    "https://replicate.delivery/xezq/h7IqZP9p59KuIdV8KvBwAHs098XtoNQ40poSzP3duwAsxdXF/tmpiiblqfkt.jpg",  # Hero
    "https://replicate.delivery/xezq/cIv1C90NXeV0OCTm79hoal4sfVaNTVMhYtckn5ovf6APNu7qA/tmpn4tq9oo7.jpg",  # Section 1
]

ARTICLE_BACKUP_PATH = "article_backup_user5_after_step1_20251010_222258.html"


def extract_article_data(backup_html_path):
    """
    Extract article components from backup file in format expected by magazine_formatter.

    Returns:
        article_data dict with title, html, components
    """
    logger.info(f"Reading backup article from: {backup_html_path}")

    with open(backup_html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract title
    title_tag = soup.find('h1')
    title = title_tag.get_text() if title_tag else "Untitled Article"

    # Extract metadata about components
    metadata_div = soup.find('div', class_='metadata')
    component_types = []
    if metadata_div:
        comp_text = metadata_div.find('p', string=lambda s: s and 'Components:' in s)
        if comp_text:
            # Extract component types from text like "12 (stat_highlight, pull_quote, sidebar, case_study)"
            comp_str = comp_text.get_text()
            if '(' in comp_str:
                types_str = comp_str.split('(')[1].split(')')[0]
                component_types = [t.strip() for t in types_str.split(',')]

    # Get clean article HTML (remove metadata div)
    if metadata_div:
        metadata_div.decompose()

    # Get executive summary
    exec_summary_div = soup.find('div', class_='exec-summary')
    exec_summary = {}
    if exec_summary_div:
        summary_p = exec_summary_div.find('p')
        if summary_p:
            exec_summary = {"intro": summary_p.get_text()}

    # Get article body
    article_html = str(soup.find('body')) if soup.find('body') else html_content

    # Create mock components list (magazine_formatter expects this)
    # Since we don't have the original components, we'll create placeholders
    components = []
    for comp_type in component_types[:12]:  # Said 12 components in metadata
        components.append({
            "type": comp_type,
            "content": "Sample content",
            "position": len(components)
        })

    article_data = {
        "title": title,
        "html": article_html,
        "components": components,
        "executive_summary": exec_summary
    }

    logger.info(f"✓ Extracted: {title[:60]}...")
    logger.info(f"✓ Article length: {len(article_html)} characters")
    logger.info(f"✓ Components: {len(components)} ({', '.join(set(component_types))})")

    return article_data


def download_image_to_disk(image_url, output_path, index=0):
    """
    Download image from Replicate to local disk.

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"[Image {index+1}] Downloading to {output_path}...")

    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)

        size_kb = len(response.content) / 1024
        logger.info(f"[Image {index+1}] ✓ Downloaded {size_kb:.1f} KB")
        return True

    except Exception as e:
        logger.error(f"[Image {index+1}] ✗ Failed: {e}")
        return False


def convert_local_image_to_base64(image_path):
    """Convert local image file to base64 data URL."""
    with open(image_path, 'rb') as f:
        image_data = f.read()

    base64_data = base64.b64encode(image_data).decode('utf-8')
    return f"data:image/jpeg;base64,{base64_data}"


def create_local_article_with_template(article_data, hero_image_path, section_image_paths, user_id=5):
    """
    Use template formatter to create magazine-style HTML, then embed images as base64.

    Returns:
        HTML string with embedded base64 images
    """
    logger.info("\n" + "="*80)
    logger.info("TESTING TEMPLATE FORMATTER WITH LOCAL IMAGES")
    logger.info("="*80)

    brand_colors = {
        "primary": "#6B5DD3",  # Purple
        "accent": "#FF6B4A"    # Coral
    }

    # Convert downloaded images to base64
    logger.info("Converting local images to base64...")
    hero_base64 = convert_local_image_to_base64(hero_image_path)
    section_base64_list = [convert_local_image_to_base64(p) for p in section_image_paths]

    logger.info(f"✓ Hero image: {len(hero_base64)} chars")
    logger.info(f"✓ Section images: {len(section_base64_list)} images")

    # Prepare section images in format expected by magazine_formatter
    section_image_mappings = []
    for i, base64_url in enumerate(section_base64_list):
        section_image_mappings.append({
            "heading": f"Section {i+1}",
            "url": base64_url
        })

    # Call template formatter
    logger.info("\nCalling template formatter...")
    formatted_html = apply_magazine_styling(
        article_data=article_data,
        hero_image_url=hero_base64,
        section_images=section_image_mappings,
        user_id=user_id,
        brand_colors=brand_colors
    )

    if formatted_html:
        logger.info(f"\n✓ Template formatter succeeded!")
        logger.info(f"✓ Output length: {len(formatted_html)} characters")
        return formatted_html
    else:
        logger.error("\n✗ Template formatter failed!")
        return None


def save_local_article(html_content, output_path):
    """Save HTML to disk."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    file_size = os.path.getsize(output_path) / 1024
    logger.info(f"\n✓ Saved: {output_path}")
    logger.info(f"✓ Size: {file_size:.1f} KB")


def main():
    print("\n" + "="*80)
    print("LOCAL ARTICLE FORMATTER TEST V2 - Template + Local Images")
    print("="*80 + "\n")

    # Step 1: Load article
    if not os.path.exists(ARTICLE_BACKUP_PATH):
        logger.error(f"Article not found: {ARTICLE_BACKUP_PATH}")
        return False

    article_data = extract_article_data(ARTICLE_BACKUP_PATH)

    # Step 2: Download images to disk
    os.makedirs("downloads", exist_ok=True)

    logger.info(f"\nDownloading {len(REPLICATE_IMAGES)} images...")
    logger.info("-" * 80)

    hero_path = "downloads/test_hero.jpg"
    if not download_image_to_disk(REPLICATE_IMAGES[0], hero_path, 0):
        logger.error("Failed to download hero image")
        return False

    section_paths = []
    for i, url in enumerate(REPLICATE_IMAGES[1:], 1):
        path = f"downloads/test_section_{i}.jpg"
        if download_image_to_disk(url, path, i):
            section_paths.append(path)

    logger.info(f"\n✓ Downloaded {1 + len(section_paths)} / {len(REPLICATE_IMAGES)} images")

    # Step 3: Format with template formatter
    formatted_html = create_local_article_with_template(
        article_data=article_data,
        hero_image_path=hero_path,
        section_image_paths=section_paths,
        user_id=5
    )

    if not formatted_html:
        logger.error("\nTest FAILED")
        return False

    # Step 4: Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"local_article_formatted_user5_{timestamp}.html"

    save_local_article(formatted_html, output_file)

    # Success
    print("\n" + "="*80)
    print("✓ TEST SUCCEEDED!")
    print("="*80)
    print(f"\nSelf-contained magazine article created:")
    print(f"  • File: {output_file}")
    print(f"  • Size: {os.path.getsize(output_file) / 1024:.1f} KB")
    print(f"  • Images: {1 + len(section_paths)} embedded as base64")
    print(f"\nOpen in browser - no internet needed!\n")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
