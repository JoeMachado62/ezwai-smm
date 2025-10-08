"""
Test script to verify both save points are working correctly.
Tests the backup functionality without running full article generation.
"""

import os
import sys
from datetime import datetime

# Test Save Point #1 (raw article backup)
def test_save_point_1():
    """Test the _save_raw_article function"""
    print("=" * 80)
    print("TESTING SAVE POINT #1: Raw Article Backup")
    print("=" * 80)

    # Import the function
    from openai_integration_v4 import _save_raw_article

    # Create mock article data
    test_article_data = {
        "title": "Test Article for Save Point Verification",
        "html": """
        <h2>Introduction</h2>
        <p>This is a test article to verify that save points are working correctly.</p>

        <h2>Main Content</h2>
        <p>This content should be saved to disk when the save point is triggered.</p>

        <h2>Conclusion</h2>
        <p>If you can read this in the saved file, Save Point #1 is working!</p>
        """,
        "executive_summary": {
            "intro": "This is a test of the emergency backup system.",
            "key_stats": [
                {"number": "100%", "description": "Save point functionality"},
                {"number": "2", "description": "Total save points implemented"}
            ]
        },
        "components": [
            {"type": "pull_quote", "content": "Testing save functionality"},
            {"type": "stat_highlight", "number": "42", "description": "Test stat"}
        ]
    }

    # Call the save function
    try:
        _save_raw_article(test_article_data, user_id=999, stage="test_after_step1")
        print("\n[OK] Save Point #1 executed successfully!")
        print("Check your project directory for: article_backup_user999_test_after_step1_*.html")
        return True
    except Exception as e:
        print(f"\n[FAIL] Save Point #1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# Test Save Point #2 (formatted article backup)
def test_save_point_2():
    """Test the _save_formatted_article function"""
    print("\n" + "=" * 80)
    print("TESTING SAVE POINT #2: Formatted Article Backup")
    print("=" * 80)

    # Import the function
    from openai_integration_v4 import _save_formatted_article

    # Create mock formatted HTML
    test_formatted_html = """
    <div style="max-width: 1200px; margin: 0 auto; background-color: #fff; padding: 0;">
        <div style="height: 480px; background-color: #08b2c6; color: white; padding: 20px;">
            <h1 style="font-size: 3em;">Test Formatted Article</h1>
            <p style="font-size: 1.2em;">2025 TEST REPORT</p>
        </div>

        <div style="background: linear-gradient(135deg, #08b2c6 0%, #ff6b11 100%); padding: 60px;">
            <h2 style="color: white; text-align: center;">Executive Summary</h2>
            <p style="color: white;">This is a fully formatted test article with inline styles.</p>
        </div>

        <div style="max-width: 1080px; margin: 0 auto; padding: 24px;">
            <h2>Main Content</h2>
            <p>This content has inline styling applied.</p>

            <div style="border-left: 5px solid #08b2c6; padding: 25px; background: #f0f9fa;">
                <em>This is a styled pull quote component.</em>
            </div>

            <p>If you can see proper styling in the saved file, Save Point #2 is working!</p>
        </div>
    </div>
    """

    test_title = "Test Formatted Article for Save Point Verification"
    test_hero_url = "https://example.com/test-hero.jpg"
    test_section_urls = [
        "https://example.com/section1.jpg",
        "https://example.com/section2.jpg",
        "https://example.com/section3.jpg"
    ]

    # Call the save function
    try:
        _save_formatted_article(
            final_html=test_formatted_html,
            title=test_title,
            user_id=999,
            hero_url=test_hero_url,
            section_urls=test_section_urls
        )
        print("\n[OK] Save Point #2 executed successfully!")
        print("Check your project directory for: article_backup_user999_formatted_*.html")
        return True
    except Exception as e:
        print(f"\n[FAIL] Save Point #2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# Test Emergency Save (app_v3.py)
def test_emergency_save():
    """Test the _save_emergency_article function"""
    print("\n" + "=" * 80)
    print("TESTING EMERGENCY SAVE: Validation Failure Recovery")
    print("=" * 80)

    # Import the function
    from app_v3 import _save_emergency_article

    test_content = """
    <h1>Emergency Save Test Article</h1>
    <p>This article was rejected by validation but should be saved anyway.</p>
    <p>If you can read this file, the emergency save is working!</p>
    """

    test_title = "Emergency Save Test"

    # Call the save function
    try:
        _save_emergency_article(test_content, test_title, user_id=999)
        print("\n[OK] Emergency Save executed successfully!")
        print("Check your project directory for: emergency_article_999_*.html")
        return True
    except Exception as e:
        print(f"\n[FAIL] Emergency Save FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all save point tests"""
    print("\n")
    print("=" * 80)
    print(" " * 20 + "SAVE POINTS VERIFICATION TEST")
    print("=" * 80)
    print("\nTesting all 3 save mechanisms to ensure articles are never lost...\n")

    results = []

    # Run tests
    results.append(("Save Point #1 (Raw Article)", test_save_point_1()))
    results.append(("Save Point #2 (Formatted Article)", test_save_point_2()))
    results.append(("Emergency Save (Validation Failure)", test_emergency_save()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for name, passed in results:
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(f"{status} - {name}")

    all_passed = all(result[1] for result in results)

    print("\n" + "=" * 80)
    if all_passed:
        print("[OK] ALL TESTS PASSED - Save points are working correctly!")
        print("\nYou can now run a full article generation test.")
        print("Your articles will be saved at multiple stages:")
        print("  1. After GPT-5 generation (raw HTML)")
        print("  2. After magazine formatting (styled HTML)")
        print("  3. If validation fails (emergency backup)")
    else:
        print("[FAIL] SOME TESTS FAILED - Please review errors above")
    print("=" * 80)
    print()

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
