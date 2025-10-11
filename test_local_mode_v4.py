"""
Test script for Local Mode in V4 Pipeline

This script tests the complete local mode flow:
1. Generate article content (GPT-5)
2. Generate image prompts (GPT-5-mini)
3. Generate images (SeeDream-4 via Replicate)
4. Format with Claude AI using Replicate URLs
5. Download images within 60-minute window
6. Replace URLs with base64 in final HTML
7. Save self-contained HTML file

Expected outcome:
- Premium magazine layout from Claude formatter
- All 5 images embedded as base64
- Self-contained HTML file ready for download
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import V4 pipeline
from openai_integration_v4 import create_blog_post_with_images_v4

def test_local_mode():
    """Test local mode with fresh article generation"""

    print("=" * 80)
    print("LOCAL MODE V4 TEST - Full Pipeline with Claude Formatter")
    print("=" * 80)
    print()

    # Test parameters
    user_id = 5
    topic = "The future of renewable energy storage technology"

    # Minimal Perplexity research for testing
    perplexity_research = f"""
    Research on {topic}:

    Battery technology is rapidly advancing with new solid-state batteries showing
    promise for higher energy density and faster charging. Companies like QuantumScape
    are developing lithium-metal batteries that could revolutionize electric vehicles.

    Grid-scale storage solutions are crucial for renewable energy adoption. Tesla's
    Megapack and similar systems are being deployed worldwide to store solar and wind
    energy for use during peak demand.

    Emerging technologies include flow batteries, compressed air energy storage, and
    hydrogen fuel cells. Each has unique advantages for different applications and scales.
    """

    system_prompt = """
    Write in a professional, informative tone suitable for business executives
    and technology professionals. Include specific examples, statistics, and
    real-world case studies where possible.
    """

    writing_style = "Professional business magazine style"

    print(f"Topic: {topic}")
    print(f"User ID: {user_id}")
    print(f"Local Mode: TRUE (will embed images as base64)")
    print()
    print("Starting V4 pipeline with local_mode=True...")
    print()

    # Run V4 pipeline with local_mode=True
    result, error = create_blog_post_with_images_v4(
        perplexity_research=perplexity_research,
        user_id=user_id,
        user_system_prompt=system_prompt,
        writing_style=writing_style,
        local_mode=True  # THIS IS THE KEY PARAMETER
    )

    if error:
        print()
        print("❌ PIPELINE FAILED")
        print(f"Error: {error}")
        return False

    if not result:
        print()
        print("❌ PIPELINE FAILED")
        print("No result returned")
        return False

    # Extract results
    title = result.get("title", "Untitled")
    content = result.get("content", "")
    hero_url = result.get("hero_image_url", "")
    section_urls = result.get("section_images", [])

    print()
    print("=" * 80)
    print("✅ PIPELINE SUCCESS")
    print("=" * 80)
    print()
    print(f"Title: {title}")
    print(f"Content length: {len(content):,} characters")
    print(f"Hero image: {'Base64' if hero_url.startswith('data:image/') else 'URL'}")
    print(f"Section images: {len(section_urls)} images")
    print()

    # Verify base64 embedding
    print("Validating base64 embedding...")
    base64_count = content.count("data:image/")
    print(f"  - Found {base64_count} base64 data URIs in HTML")

    if base64_count >= 4:  # At least hero + 3 sections
        print(f"  ✅ All images appear to be embedded")
    else:
        print(f"  ⚠️  Expected at least 4 images, found {base64_count}")

    # Check for Claude formatter styling
    print()
    print("Checking Claude formatter styling...")

    checks = {
        "Inline styles": 'style="' in content,
        "Hero section": 'background-image' in content,
        "Pull quotes": 'class="pull-quote"' in content or 'pull-quote' in content.lower(),
        "Stat highlights": 'stat-highlight' in content.lower() or 'stat' in content.lower(),
    }

    for check_name, passed in checks.items():
        status = "✅" if passed else "⚠️"
        print(f"  {status} {check_name}")

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"local_mode_test_user{user_id}_{timestamp}.html"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    file_size_mb = len(content) / (1024 * 1024)

    print()
    print(f"📁 Saved to: {filename}")
    print(f"📊 File size: {file_size_mb:.2f} MB")
    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print()
    print(f"Open the file in your browser to view the article:")
    print(f"  {os.path.abspath(filename)}")
    print()

    return True

if __name__ == "__main__":
    try:
        success = test_local_mode()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
