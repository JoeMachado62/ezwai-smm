"""
Test script for V4/V5 blog generation with structured JSON output
V5 improvements:
- Removed implementation guide bias from prompts
- Removed static section title templates
- Added comprehensive error logging for Replicate API
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
print("EZWAI SMM V5 Blog Generation Test")
print("Single GPT-5-mini call with Structured JSON Output")
print("V5: No template bias + Natural section titles + Better error handling")
print("=" * 80)
print()

# Test database and user
print("[1/5] Testing database connection...")
try:
    from app_v3 import app, db, User
    with app.app_context():
        user = User.query.first()
        if not user:
            print("❌ No user found")
            sys.exit(1)
        print(f"✅ User: {user.email} (ID: {user.id})")
        print(f"   OpenAI: {'✅' if user.openai_api_key else '❌'}")
        print(f"   Perplexity: {'✅' if user.perplexity_api_token else '❌'}")
except Exception as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)

print()

# Test Perplexity
print("[2/5] Getting trending topic from Perplexity...")
try:
    from perplexity_ai_integration import generate_blog_post_ideas
    with app.app_context():
        user = User.query.first()
        query = "Latest breakthroughs in artificial intelligence"
        ideas = generate_blog_post_ideas(query, user.id)
        if ideas and len(ideas) > 0:
            print(f"✅ Topic: {ideas[0][:100]}...")
            blog_idea = ideas[0]
        else:
            print("❌ No ideas generated")
            sys.exit(1)
except Exception as e:
    print(f"❌ Perplexity error: {e}")
    sys.exit(1)

print()

# Test V5 generation
print("[3/5] Generating article with V5 (structured JSON)...")
print("   This may take 1-2 minutes for article generation...")
print("   Then 2-3 minutes for image generation (4 images)...")
try:
    from openai_integration_v4 import create_blog_post_with_images_v4
    with app.app_context():
        user = User.query.first()

        system_prompt = "You are an expert technology journalist creating engaging, authoritative articles for business professionals."

        processed_post, error = create_blog_post_with_images_v4(
            blog_post_idea=blog_idea,
            user_id=user.id,
            system_prompt=system_prompt
        )

        if error:
            print(f"❌ Error: {error}")
            sys.exit(1)

        if not processed_post:
            print("❌ No blog post generated")
            sys.exit(1)

        print(f"✅ Article generated!")
        print(f"   Title: {processed_post['title']}")
        print(f"   Content: {len(processed_post['content'])} characters")
        print(f"   Word count: ~{len(processed_post['content'].split())} words")
        print(f"   Images: {len([img for img in processed_post['all_images'] if img])}")

except Exception as e:
    print(f"❌ V4 generation error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Save HTML
print("[4/5] Saving to HTML file...")
try:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_v4_blog_{timestamp}.html"

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{processed_post['title']}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Roboto:wght@400;500;700&display=swap');

        body {{
            font-family: 'Roboto', sans-serif;
            line-height: 1.8;
            color: #3a3a3a;
            background-color: #f0f2f5;
            margin: 0;
            padding: 0;
        }}
        .magazine-container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: #fff;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        .cover {{
            background-size: cover;
            background-position: center;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            align-items: center;
            text-align: center;
            color: white;
            padding: 20px;
            position: relative;
        }}
        .cover::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.4);
        }}
        .cover h1 {{
            font-family: 'Playfair Display', serif;
            font-size: 4em;
            margin: 0;
            z-index: 1;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.6);
        }}
        .cover .subtitle {{
            font-size: 1.5em;
            margin: 20px 0;
            z-index: 1;
        }}
        .cover .edition {{
            background-color: #ff6b11;
            padding: 10px 25px;
            margin: 20px 0 40px;
            font-weight: 700;
            border-radius: 5px;
            z-index: 1;
        }}
        .section {{
            margin: 0;
        }}
        .section-header {{
            height: 400px;
            background-size: cover;
            background-position: center;
            display: flex;
            align-items: flex-end;
            color: white;
            padding: 40px;
            position: relative;
        }}
        .section-header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0) 100%);
        }}
        .section-header h2 {{
            font-family: 'Playfair Display', serif;
            font-size: 3em;
            margin: 0;
            z-index: 1;
        }}
        .content-area {{
            padding: 50px 40px;
            display: grid;
            grid-template-columns: 1fr;
            gap: 40px;
        }}
        @media (min-width: 800px) {{
            .content-area {{
                grid-template-columns: 2fr 1fr;
            }}
        }}
        .main-column {{
            font-size: 1.1em;
        }}
        .main-column h3 {{
            font-family: 'Playfair Display', serif;
            color: #333;
            font-size: 2em;
            margin-top: 30px;
        }}
        .main-column h4 {{
            font-family: 'Roboto', sans-serif;
            font-weight: 700;
            color: #08b0c4;
            font-size: 1.5em;
            margin-top: 25px;
        }}
        .pull-quote {{
            font-family: 'Playfair Display', serif;
            font-size: 1.8em;
            color: #ff6b11;
            border-left: 5px solid #08b0c4;
            padding-left: 25px;
            margin: 40px 0;
            font-style: italic;
        }}
        .case-study-box {{
            background-color: #fff3e0;
            border-left: 5px solid #ff6b11;
            padding: 25px;
            margin: 30px 0;
            border-radius: 0 8px 8px 0;
        }}
        .case-study-box h4 {{
            color: #ff6b11;
            margin-top: 0;
            font-family: 'Playfair Display', serif;
        }}
        .warning-box-magazine {{
            background: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 20px 25px;
            margin: 20px 0;
            border-radius: 8px;
        }}
        .warning-box-magazine h4 {{
            color: #856404;
            margin-top: 0;
        }}
        .checklist-magazine {{
            background-color: #e9f7fe;
            padding: 20px 25px;
            border-radius: 8px;
        }}
        .checklist-magazine ul {{
            list-style: none;
            padding: 0;
        }}
        .checklist-magazine li::before {{
            content: '✓';
            color: #ff6b11;
            font-size: 1.5em;
            margin-right: 15px;
            font-weight: 700;
        }}
        .sidebar {{
            background-color: #f8f9fa;
            padding: 30px;
            border-radius: 8px;
            border-top: 5px solid #08b0c4;
        }}
        .stat-highlight {{
            background-color: #e6fffa;
            border: 1px solid #08b0c4;
            padding: 20px;
            margin-bottom: 25px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-highlight .number {{
            font-size: 3em;
            font-weight: 700;
            color: #08b0c4;
        }}
        .sidebar-box {{
            background-color: #fff;
            border-left: 3px solid #ff6b11;
            padding: 20px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    {processed_post['content']}
</body>
</html>
"""

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_template)

    print(f"✅ Saved to: {filename}")
    print(f"   Path: {os.path.abspath(filename)}")

except Exception as e:
    print(f"❌ Save error: {e}")
    import traceback
    traceback.print_exc()

print()

# Summary
print("[5/5] Test Summary")
print("=" * 80)
print("✅ V5 TEST COMPLETED!")
print("=" * 80)
print(f"Title: {processed_post['title']}")
print(f"Content: {len(processed_post['content'])} characters")
print(f"Words: ~{len(processed_post['content'].split())}")
print(f"Images: {len([img for img in processed_post['all_images'] if img])}/4")
print(f"Hero: {processed_post.get('hero_image_url', 'N/A')[:60]}...")
print(f"File: {filename}")
print()
print("V5 IMPROVEMENTS:")
print("✓ Removed implementation guide bias - GPT-5 writes naturally")
print("✓ No static section titles - GPT-5 creates topic-specific headings")
print("✓ Enhanced error logging for Replicate API debugging")
print("✓ Single GPT-5-mini call with structured JSON output")
print("✓ Magazine CSS classes from AI_Implementation_Guide")
print("✓ Cinematic image prompts generated WITH article content")
print("✓ 4 photorealistic images (1 hero 16:9, 3 sections 4:3)")
print()
