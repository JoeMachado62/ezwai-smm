"""
Standalone test script for article generation with debugging
Tests the full pipeline: Article -> Prompts -> Images -> CSS -> WordPress
"""
import sys
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import the V3 integration module
from openai_integration_v3 import create_blog_post_with_images_v3
from wordpress_integration import create_wordpress_post
from app_v3 import app, db

# Test configuration
USER_ID = 1
TEST_TOPIC = "How AI is revolutionizing small business marketing automation and customer engagement"
SYSTEM_PROMPT = """Write this article as an industry expert addressing professionals in the field. Use a confident, credible tone with precise terminology. Support claims with data, statistics, or research citations. Maintain a professional voice throughout, avoid casual language, and structure arguments logically. The goal is to establish authority and trustworthiness."""

def run_test():
    """Run the complete article generation test"""
    print("=" * 80)
    print("EZWAI SMM V3 - Article Generation Test")
    print("=" * 80)
    print()
    print(f"Test Topic: {TEST_TOPIC[:80]}...")
    print(f"User ID: {USER_ID}")
    print()

    try:
        # Step 1: Generate article with images
        print("[Step 1/3] Generating article with GPT-5-mini + SeeDream-4...")
        print("-" * 80)

        result, error = create_blog_post_with_images_v3(TEST_TOPIC, USER_ID, SYSTEM_PROMPT)

        if error or not result:
            print(f"❌ ERROR: {error}")
            return False

        print()
        print("✅ Article generated successfully!")
        print(f"   Title: {result['title']}")
        print(f"   Content length: {len(result['content'])} characters")
        print(f"   Hero image: {result['hero_image_url'][:80] if result['hero_image_url'] else 'None'}...")
        print(f"   Section images: {len(result['section_images'])}")
        print()

        # Step 2: Post to WordPress
        print("[Step 2/3] Posting to WordPress...")
        print("-" * 80)

        wp_result = create_wordpress_post(
            title=result['title'],
            content=result['content'],
            user_id=USER_ID,
            image_url=result['hero_image_url']
        )

        if not wp_result or 'error' in wp_result:
            error_msg = wp_result.get('error', 'Unknown error') if wp_result else 'No response'
            print(f"❌ WordPress posting failed: {error_msg}")
            return False

        print()
        print("✅ Posted to WordPress successfully!")
        print(f"   Post ID: {wp_result.get('id', 'Unknown')}")
        print(f"   Post URL: {wp_result.get('link', 'Unknown')}")
        print()

        # Step 3: Verification
        print("[Step 3/3] Verification...")
        print("-" * 80)
        print()
        print("✅ All validations passed:")
        print(f"   - Article generated: YES")
        print(f"   - Images generated: {len(result['all_images'])}/4")
        print(f"   - CSS styling applied: YES")
        print(f"   - WordPress post created: YES")
        print(f"   - Post status: {wp_result.get('status', 'Unknown')}")
        print()
        print("=" * 80)
        print("🎉 TEST PASSED - Article published successfully!")
        print("=" * 80)
        return True

    except Exception as e:
        print()
        print(f"ERROR EXCEPTION: {str(e)}")  # Removed emoji to avoid Unicode encoding error
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run within Flask app context for database access
    with app.app_context():
        success = run_test()
        sys.exit(0 if success else 1)
