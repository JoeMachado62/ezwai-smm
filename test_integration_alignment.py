"""
Integration Test - CLAUDE.md Alignment Verification
Tests that all components work together end-to-end
"""
import os
import sys
from typing import Dict

# Fix Windows encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def test_imports():
    """Test all critical imports work"""
    print("\n=== TESTING IMPORTS ===")
    try:
        from scheduler_v3 import create_blog_post, check_and_trigger_jobs
        print("✓ scheduler_v3 imports successfully")

        from openai_integration_v4 import create_blog_post_with_images_v4
        print("✓ openai_integration_v4 imports successfully")

        from claude_formatter import format_article_with_claude
        print("✓ claude_formatter imports successfully")

        from magazine_formatter import apply_magazine_styling
        print("✓ magazine_formatter (fallback) imports successfully")

        from app_v3 import app, db, User
        print("✓ app_v3 imports successfully")

        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_v4_function_signature():
    """Verify V4 function has correct signature"""
    print("\n=== TESTING V4 FUNCTION SIGNATURE ===")
    try:
        from openai_integration_v4 import create_blog_post_with_images_v4
        import inspect

        sig = inspect.signature(create_blog_post_with_images_v4)
        params = list(sig.parameters.keys())

        # V4 has different signature than V3
        expected_params = ['perplexity_research', 'user_id', 'user_system_prompt', 'writing_style']

        if params == expected_params:
            print(f"✓ V4 signature correct: {params}")
            return True
        else:
            print(f"✗ V4 signature mismatch!")
            print(f"  Expected: {expected_params}")
            print(f"  Got: {params}")
            return False
    except Exception as e:
        print(f"✗ Signature test failed: {e}")
        return False

def test_claude_formatter_signature():
    """Verify Claude formatter has correct signature"""
    print("\n=== TESTING CLAUDE FORMATTER SIGNATURE ===")
    try:
        from claude_formatter import format_article_with_claude
        import inspect

        sig = inspect.signature(format_article_with_claude)
        params = list(sig.parameters.keys())

        expected_params = ['article_html', 'title', 'hero_image_url', 'section_images',
                          'user_id', 'brand_colors', 'layout_style']

        if params == expected_params:
            print(f"✓ Claude formatter signature correct")
            print(f"  Parameters: {params}")
            return True
        else:
            print(f"✗ Claude formatter signature mismatch!")
            print(f"  Expected: {expected_params}")
            print(f"  Got: {params}")
            return False
    except Exception as e:
        print(f"✗ Signature test failed: {e}")
        return False

def test_scheduler_uses_v4():
    """Verify scheduler imports V4 (not V3)"""
    print("\n=== TESTING SCHEDULER USES V4 ===")
    try:
        with open('scheduler_v3.py', 'r', encoding='utf-8') as f:
            content = f.read()

        if 'from openai_integration_v4 import create_blog_post_with_images_v4' in content:
            print("✓ Scheduler imports V4 correctly")

            if 'from openai_integration_v3 import' in content:
                print("✗ WARNING: Scheduler still has V3 import!")
                return False
            else:
                print("✓ No V3 imports found in scheduler")
                return True
        else:
            print("✗ Scheduler does not import V4!")
            return False
    except Exception as e:
        print(f"✗ File read failed: {e}")
        return False

def test_v4_uses_claude_formatter():
    """Verify V4 integration imports Claude formatter"""
    print("\n=== TESTING V4 USES CLAUDE FORMATTER ===")
    try:
        with open('openai_integration_v4.py', 'r', encoding='utf-8') as f:
            content = f.read()

        has_claude = 'from claude_formatter import format_article_with_claude' in content
        has_fallback = 'from magazine_formatter import apply_magazine_styling' in content
        uses_claude = 'format_article_with_claude(' in content

        if has_claude and has_fallback and uses_claude:
            print("✓ V4 imports Claude formatter")
            print("✓ V4 imports fallback formatter")
            print("✓ V4 calls format_article_with_claude()")
            return True
        else:
            print(f"✗ V4 formatter integration incomplete!")
            print(f"  Has Claude import: {has_claude}")
            print(f"  Has fallback import: {has_fallback}")
            print(f"  Uses Claude formatter: {uses_claude}")
            return False
    except Exception as e:
        print(f"✗ File read failed: {e}")
        return False

def test_v3_has_deprecation():
    """Verify V3 has deprecation notice"""
    print("\n=== TESTING V3 DEPRECATION NOTICE ===")
    try:
        with open('openai_integration_v3.py', 'r', encoding='utf-8') as f:
            content = f.read()

        if 'DEPRECATED' in content and 'openai_integration_v4' in content:
            print("✓ V3 has deprecation notice")
            print("✓ V3 references migration to V4")
            return True
        else:
            print("✗ V3 missing deprecation notice!")
            return False
    except Exception as e:
        print(f"✗ File read failed: {e}")
        return False

def test_environment_config():
    """Check environment configuration"""
    print("\n=== TESTING ENVIRONMENT CONFIGURATION ===")
    try:
        # Check .env file
        with open('.env', 'r', encoding='utf-8') as f:
            env_content = f.read()

        has_anthropic = 'ANTHROPIC_API_KEY' in env_content

        if has_anthropic:
            print("✓ .env has ANTHROPIC_API_KEY")
        else:
            print("✗ .env missing ANTHROPIC_API_KEY")
            return False

        # Check requirements.txt
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            req_content = f.read()

        has_anthropic_pkg = 'anthropic' in req_content

        if has_anthropic_pkg:
            print("✓ requirements.txt includes anthropic package")
        else:
            print("✗ requirements.txt missing anthropic package")
            return False

        return True
    except Exception as e:
        print(f"✗ Environment check failed: {e}")
        return False

def test_user_model_has_brand_colors():
    """Verify User model has brand color fields"""
    print("\n=== TESTING USER MODEL BRAND COLORS ===")
    try:
        from app_v3 import User

        # Create a dummy instance to check fields
        user_fields = dir(User)

        has_primary = 'brand_primary_color' in user_fields
        has_accent = 'brand_accent_color' in user_fields

        if has_primary and has_accent:
            print("✓ User model has brand_primary_color")
            print("✓ User model has brand_accent_color")
            return True
        else:
            print(f"✗ User model missing brand color fields!")
            print(f"  Has brand_primary_color: {has_primary}")
            print(f"  Has brand_accent_color: {has_accent}")
            return False
    except Exception as e:
        print(f"✗ User model check failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("CLAUDE.md ALIGNMENT - INTEGRATION TEST")
    print("=" * 60)

    results = []

    # Run all tests
    results.append(("Imports", test_imports()))
    results.append(("V4 Function Signature", test_v4_function_signature()))
    results.append(("Claude Formatter Signature", test_claude_formatter_signature()))
    results.append(("Scheduler Uses V4", test_scheduler_uses_v4()))
    results.append(("V4 Uses Claude Formatter", test_v4_uses_claude_formatter()))
    results.append(("V3 Deprecation", test_v3_has_deprecation()))
    results.append(("Environment Config", test_environment_config()))
    results.append(("User Model Brand Colors", test_user_model_has_brand_colors()))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED - System is aligned!")
        print("\nNext steps:")
        print("1. Add real ANTHROPIC_API_KEY to .env")
        print("2. Test with actual article generation")
        print("3. Monitor Claude vs template formatter usage in logs")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - Review above for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())
