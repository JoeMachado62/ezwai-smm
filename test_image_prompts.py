"""
Test script to verify image prompt generation works after the fix.
Tests STEP 2 in isolation without running full article generation.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_image_prompt_generation():
    """Test the image prompt generation with sample article HTML"""

    print("\n" + "=" * 80)
    print("TESTING IMAGE PROMPT GENERATION (STEP 2)")
    print("=" * 80)

    # Load environment for user 1
    load_dotenv('.env.user_1')

    # Import the function
    from image_prompt_generator import generate_contextual_image_prompts

    # Create sample article HTML (simulating STEP 1 output)
    test_article_html = """
    <h1>AI Agents Transforming Small Business Operations</h1>
    <p>Small and medium-sized enterprises are discovering that AI agents can level the playing field against larger competitors.</p>

    <h2>The Revenue Impact: Real Numbers from Early Adopters</h2>
    <p>Bob Rohrman Kia achieved a 43% increase in lead-to-appointment conversion using Impel's AI agent. The dealership handles 45% of leads during off-hours. Sales teams now focus on high-value customers while AI handles routine inquiries 24/7.</p>
    <p>Elk Grove Buick GMC saw an 18% increase in lead conversion rate and influenced over $1 million in gross sales. The family-owned Sacramento dealership generated 19% more live customer calls.</p>

    <h2>Where AI Delivers Value First for SMEs</h2>
    <p>Customer service automation leads the adoption curve. AI agents handle initial inquiries, schedule appointments, and provide product information around the clock. AutoMax Dealership reported 220% sales increase and 50% faster deal closings.</p>
    <p>Marketing automation comes next. AI systems personalize customer communications, manage follow-ups, and optimize timing based on customer behavior patterns.</p>

    <h2>Implementation Strategies That Work</h2>
    <p>Successful SMEs start with one high-impact use case rather than attempting full-scale transformation. They focus on processes that directly affect revenue or customer satisfaction.</p>
    <p>The key is selecting AI solutions that integrate with existing systems. Cloud-based platforms reduce upfront costs and technical barriers.</p>
    """

    test_summary = "Small businesses are using AI agents to compete with larger companies, achieving significant revenue increases through customer service automation, marketing optimization, and strategic implementation."

    print("\n Test Article Summary:")
    print(f"  - Title: AI Agents Transforming Small Business Operations")
    print(f"  - Sections: 3 (Revenue Impact, Value Delivery, Implementation)")
    print(f"  - Writing Style: Authoritative/Expert")
    print()

    # Call the function
    print(" Calling generate_contextual_image_prompts()...")
    print()

    try:
        result = generate_contextual_image_prompts(
            article_html=test_article_html,
            perplexity_summary=test_summary,
            user_id=1,
            writing_style="Authoritative/Expert"
        )

        if not result:
            print(" FAILED: Function returned None")
            return False

        # Validate structure
        if "hero_prompt" not in result:
            print(" FAILED: Missing 'hero_prompt' in result")
            return False

        if "section_prompts" not in result:
            print(" FAILED: Missing 'section_prompts' in result")
            return False

        # Display results
        print("=" * 80)
        print(" SUCCESS: Image prompts generated!")
        print("=" * 80)

        print("\n HERO PROMPT (16:9):")
        print("-" * 80)
        print(result['hero_prompt'])

        print("\n\n SECTION PROMPTS (21:9):")
        print("-" * 80)
        for i, section_prompt in enumerate(result['section_prompts'], 1):
            print(f"\n{i}. Section: {section_prompt['section_heading']}")
            print(f"   Prompt: {section_prompt['prompt'][:200]}...")

        print("\n" + "=" * 80)
        print(f" VALIDATION PASSED")
        print(f"   - Hero prompt: {len(result['hero_prompt'])} characters")
        print(f"   - Section prompts: {len(result['section_prompts'])} generated")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_single_image_generation():
    """Test generating one actual image with SeeDream-4"""

    print("\n" + "=" * 80)
    print("TESTING SINGLE IMAGE GENERATION (SeeDream-4)")
    print("=" * 80)

    # Load main environment for Replicate token
    load_dotenv()

    # Check if REPLICATE_API_TOKEN exists
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_token:
        print(" SKIPPED: REPLICATE_API_TOKEN not found in .env")
        print("   This test requires Replicate API access")
        return None

    print(" Replicate API token found")

    # Import the function
    from openai_integration_v4 import generate_images_with_seedream

    # Test prompt
    test_prompt = "Professional business meeting in modern office, small business owners discussing AI strategy with consultant, Canon R5, 50mm f/1.4, natural window lighting, clean corporate setting, focused collaboration, blue and white color palette"

    print(f"\n Test Prompt:")
    print(f"   {test_prompt[:100]}...")
    print(f"\n Generating 21:9 aspect ratio image...")
    print("   (This will take ~30 seconds)")
    print()

    try:
        # Generate single test image
        result = generate_images_with_seedream(
            prompts=[test_prompt],
            user_id=1,
            aspect_ratio="21:9"
        )

        if not result or not result[0]:
            print(" FAILED: No image URL returned")
            return False

        image_url = result[0]

        print("=" * 80)
        print(" SUCCESS: Image generated!")
        print("=" * 80)
        print(f"\n  Image URL: {image_url}")
        print(f"\n Aspect Ratio: 21:9 (ultra-wide cinematic)")
        print(f" SeeDream-4 API is working correctly")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n")
    print("=" * 80)
    print(" " * 20 + "IMAGE GENERATION TEST SUITE")
    print("=" * 80)

    results = []

    # Test 1: Image prompt generation
    print("\nTest 1: Image Prompt Generation (GPT-5-mini)")
    results.append(("Image Prompt Generation", test_image_prompt_generation()))

    # Test 2: Actual image generation (optional, requires API credits)
    print("\n" + "=" * 80)
    user_input = input("\nRun SeeDream-4 image generation test? (uses API credits) [y/N]: ").strip().lower()

    if user_input == 'y':
        result = test_single_image_generation()
        if result is not None:
            results.append(("SeeDream-4 Image Generation", result))
    else:
        print("  Skipped SeeDream-4 test")

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for name, passed in results:
        if passed is None:
            status = "  SKIP"
        elif passed:
            status = " PASS"
        else:
            status = " FAIL"
        print(f"{status} - {name}")

    print("\n" + "=" * 80)

    # Check if any failed
    failures = [name for name, passed in results if passed is False]

    if failures:
        print(" TESTS FAILED")
        print(f"   Failed: {', '.join(failures)}")
        print("\nPlease review errors above before running full article generation.")
        return 1
    else:
        print(" ALL TESTS PASSED")
        print("\nImage generation system is working correctly!")
        print("You can now run a full article generation test with confidence.")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n  Test interrupted by user")
        sys.exit(1)
