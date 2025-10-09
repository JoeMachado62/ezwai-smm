"""
Test Anthropic API Key
Quick test to verify the Claude API key works
"""
import os
import sys
from dotenv import load_dotenv
import anthropic

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Load environment
load_dotenv()

def test_anthropic_key():
    """Test if Anthropic API key is valid"""
    print("Testing Anthropic API Key...")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key or api_key == "YOUR_ANTHROPIC_API_KEY_HERE":
        print("❌ No valid API key found in .env")
        return False

    print(f"✓ API Key loaded: {api_key[:20]}...{api_key[-10:]}")

    try:
        # Initialize client
        client = anthropic.Anthropic(api_key=api_key)

        # Make a simple test request
        print("\nSending test request to Claude API...")

        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Say 'API test successful' in exactly 3 words."}
            ]
        )

        response_text = message.content[0].text
        print(f"\n✓ API Response: {response_text}")
        print(f"✓ Model: {message.model}")
        print(f"✓ Tokens used: {message.usage.input_tokens} input, {message.usage.output_tokens} output")

        print("\n" + "=" * 60)
        print("🎉 ANTHROPIC API KEY IS VALID AND WORKING!")
        print("=" * 60)

        return True

    except anthropic.AuthenticationError as e:
        print(f"\n❌ Authentication Error: {e}")
        print("The API key is invalid or expired")
        return False

    except anthropic.APIError as e:
        print(f"\n❌ API Error: {e}")
        return False

    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_anthropic_key()
    exit(0 if success else 1)
