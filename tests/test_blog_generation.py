"""
Comprehensive test script for blog post generation
Tests all components and generates a complete blog post with images
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load main environment
load_dotenv()

print("=" * 80)
print("EZWAI SMM Blog Generation Test")
print("=" * 80)
print()

# Step 1: Test database and user
print("[1/7] Testing database connection and user...")
try:
    from app_v3 import app, db, User
    with app.app_context():
        user = User.query.first()
        if not user:
            print("❌ No user found in database")
            sys.exit(1)
        print(f"✅ User found: {user.email} (ID: {user.id})")
        print(f"   - OpenAI Key: {'✅ Set' if user.openai_api_key else '❌ Missing'}")
        print(f"   - Perplexity Token: {'✅ Set' if user.perplexity_api_token else '❌ Missing'}")
        print(f"   - WordPress URL: {user.wordpress_rest_api_url or '❌ Missing'}")
        print(f"   - Queries: {len(user.specific_topic_queries or {})}")
except Exception as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)

print()

# Step 2: Test environment file generation
print("[2/7] Testing environment file generation...")
try:
    from app_v3 import generate_env_file
    with app.app_context():
        user = User.query.first()
        generate_env_file(user)
        env_file = f'.env.user_{user.id}'
        if os.path.exists(env_file):
            print(f"✅ Environment file generated: {env_file}")
            # Load and verify
            load_dotenv(env_file)
            openai_key = os.getenv('OPENAI_API_KEY')
            perplexity_token = os.getenv('PERPLEXITY_AI_API_TOKEN')
            print(f"   - OpenAI Key loaded: {'✅ Yes' if openai_key and openai_key != 'None' else '❌ No'}")
            print(f"   - Perplexity Token loaded: {'✅ Yes' if perplexity_token and perplexity_token != 'None' else '❌ No'}")
        else:
            print(f"❌ Environment file not found: {env_file}")
            sys.exit(1)
except Exception as e:
    print(f"❌ Environment file error: {e}")
    sys.exit(1)

print()

# Step 3: Test Perplexity API
print("[3/7] Testing Perplexity AI API...")
try:
    from perplexity_ai_integration import generate_blog_post_ideas
    with app.app_context():
        user = User.query.first()
        query = "Latest trends in artificial intelligence"
        print(f"   Query: {query}")
        ideas = generate_blog_post_ideas(query, user.id)
        if ideas and len(ideas) > 0:
            print(f"✅ Perplexity API working! Generated {len(ideas)} ideas")
            print(f"   First idea preview: {ideas[0][:100]}...")
        else:
            print("❌ No ideas generated from Perplexity")
            sys.exit(1)
except Exception as e:
    print(f"❌ Perplexity API error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Step 4: Test OpenAI API
print("[4/7] Testing OpenAI API...")
try:
    import openai
    from dotenv import load_dotenv
    load_dotenv(f'.env.user_{user.id}')

    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key or openai_key == 'None':
        print("❌ OpenAI API key not loaded properly")
        sys.exit(1)

    client = openai.OpenAI(api_key=openai_key)
    # Test with a simple completion
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say 'API working'"}],
        max_tokens=10
    )
    print(f"✅ OpenAI API working! Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ OpenAI API error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Step 5: Test Replicate API (SeeDream-4)
print("[5/7] Testing Replicate API (SeeDream-4)...")
try:
    import replicate
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("⚠️  Replicate token not found - images will not be generated")
    else:
        os.environ['REPLICATE_API_TOKEN'] = replicate_token
        print(f"✅ Replicate token set: {replicate_token[:20]}...")
except Exception as e:
    print(f"⚠️  Replicate setup warning: {e}")

print()

# Step 6: Generate complete blog post
print("[6/7] Generating complete blog post with images...")
print("   This may take 3-4 minutes...")
try:
    from openai_integration_v3 import create_blog_post_with_images_v3
    with app.app_context():
        user = User.query.first()

        # Use the blog idea from Perplexity
        blog_idea = ideas[0] if ideas else "Write an article about the latest trends in artificial intelligence and machine learning"
        system_prompt = "You are an expert technology writer creating engaging, informative articles for a professional audience."

        print(f"   Blog idea: {blog_idea[:100]}...")

        processed_post, error = create_blog_post_with_images_v3(
            blog_post_idea=blog_idea,
            user_id=user.id,
            system_prompt=system_prompt
        )

        if error:
            print(f"❌ Blog generation error: {error}")
            sys.exit(1)

        if not processed_post:
            print("❌ No blog post generated")
            sys.exit(1)

        print(f"✅ Blog post generated successfully!")
        print(f"   Title: {processed_post['title']}")
        print(f"   Content length: {len(processed_post['content'])} characters")
        print(f"   Images: {len([img for img in processed_post['all_images'] if img])}")

except Exception as e:
    print(f"❌ Blog generation error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Step 7: Save to HTML file
print("[7/7] Saving blog post to HTML file...")
try:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_blog_post_{timestamp}.html"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{processed_post['title']}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .article {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a1a1a;
            font-size: 2.5em;
            margin-bottom: 20px;
        }}
        .meta {{
            color: #666;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .content {{
            color: #333;
        }}
        .content img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="article">
        <h1>{processed_post['title']}</h1>
        <div class="meta">
            Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}<br>
            Length: {len(processed_post['content'])} characters<br>
            Images: {len([img for img in processed_post['all_images'] if img])}
        </div>
        <div class="content">
            {processed_post['content']}
        </div>
    </div>
</body>
</html>
"""

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ Blog post saved to: {filename}")
    print(f"   Full path: {os.path.abspath(filename)}")

except Exception as e:
    print(f"❌ Error saving HTML: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("✅ TEST COMPLETED SUCCESSFULLY!")
print("=" * 80)
print(f"\nBlog post details:")
print(f"  - Title: {processed_post['title']}")
print(f"  - Word count: ~{len(processed_post['content'].split())}")
print(f"  - Character count: {len(processed_post['content'])}")
print(f"  - Images generated: {len([img for img in processed_post['all_images'] if img])}")
print(f"  - Hero image: {processed_post.get('hero_image_url', 'N/A')}")
print(f"  - HTML file: {filename}")
print()
