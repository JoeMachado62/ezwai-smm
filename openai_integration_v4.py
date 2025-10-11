"""
openai_integration_v4.py - Modular Article Generation Orchestrator

Coordinates the 4-step modular pipeline:
1. Story Generation (GPT-5) - Structured JSON with components
2. Image Prompt Generation (GPT-5-mini) - Section-aligned prompts
3. Image Generation (SeeDream-4 via Replicate)
4. Magazine Formatting (GPT-5-mini) - Styled layout assembly

V4 UPDATE: Now uses structured article generation with component metadata
for reliable magazine layout assembly.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dotenv import load_dotenv
import replicate

# Import V4 modular components
from story_generation import generate_clean_article
from image_prompt_generator import generate_contextual_image_prompts
from claude_formatter import format_article_with_claude
from magazine_formatter import apply_magazine_styling  # Fallback formatter

# Import shared utilities
from wordpress_integration import load_user_env as wp_load_user_env, download_image, get_jwt_token

logger = logging.getLogger(__name__)


def _download_and_convert_to_base64(image_url: str) -> Optional[str]:
    """
    Download image from Replicate URL and convert to base64 data URI.
    Must be called within 60-minute Replicate expiry window.

    Args:
        image_url: Replicate image URL (expires in 60 minutes)

    Returns:
        Base64 data URI string (e.g., "data:image/jpeg;base64,/9j/4AAQ...") or None if failed
    """
    import requests
    import base64
    from io import BytesIO

    try:
        logger.info(f"[DOWNLOAD] Fetching image from: {image_url[:80]}...")

        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        # Detect image type from Content-Type header
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        image_format = content_type.split('/')[-1]  # e.g., "jpeg", "png", "webp"

        # Convert to base64
        image_data = base64.b64encode(response.content).decode('utf-8')
        base64_uri = f"data:{content_type};base64,{image_data}"

        size_kb = len(response.content) / 1024
        logger.info(f"[DOWNLOAD] ✅ Converted to base64 ({size_kb:.1f} KB, format: {image_format})")

        return base64_uri

    except requests.exceptions.RequestException as e:
        logger.error(f"[DOWNLOAD] Failed to download image: {e}")
        return None
    except Exception as e:
        logger.error(f"[DOWNLOAD] Failed to convert to base64: {e}")
        return None


def _save_raw_article(article_data: Dict, user_id: int, stage: str) -> None:
    """
    Save raw article content to disk at various pipeline stages.

    Args:
        article_data: Article data dictionary from generate_clean_article()
        user_id: User ID
        stage: Pipeline stage (e.g., "after_step1", "after_formatting")
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"article_backup_user{user_id}_{stage}_{timestamp}.html"

        title = article_data.get("title", "Untitled")
        html_content = article_data.get("html", "<p>No content</p>")
        components = article_data.get("components", [])
        exec_summary = article_data.get("executive_summary", {})

        backup_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        .metadata {{ background: #e7f3ff; padding: 15px; margin-bottom: 20px; border-left: 4px solid #0066cc; }}
        .exec-summary {{ background: #f0f0f0; padding: 20px; margin: 20px 0; }}
        h1 {{ color: #333; }}
    </style>
</head>
<body>
    <div class="metadata">
        <h2>📄 Article Backup - {stage.replace('_', ' ').title()}</h2>
        <p><strong>User ID:</strong> {user_id}</p>
        <p><strong>Saved:</strong> {timestamp}</p>
        <p><strong>Components:</strong> {len(components)} ({', '.join(set(c.get('type', '') for c in components))})</p>
        <p><strong>Status:</strong> RAW HTML (before magazine formatting)</p>
    </div>

    <h1>{title}</h1>

    {f'<div class="exec-summary"><h3>Executive Summary</h3><p>{exec_summary.get("intro", "")}</p></div>' if exec_summary.get("intro") else ''}

    {html_content}
</body>
</html>"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(backup_html)

        logger.info(f"[BACKUP] Raw article saved to {filename}")

    except Exception as e:
        logger.error(f"[BACKUP] Failed to save raw article: {e}")


def _save_formatted_article(final_html: str, title: str, user_id: int, hero_url: str, section_urls: List[str]) -> None:
    """
    Save fully formatted magazine article to disk.

    Args:
        final_html: Complete HTML with inline styling
        title: Article title
        user_id: User ID
        hero_url: Hero image URL
        section_urls: List of section image URLs
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"article_backup_user{user_id}_formatted_{timestamp}.html"

        metadata_banner = f"""
<!--
════════════════════════════════════════════════════════════════
FORMATTED ARTICLE BACKUP
User ID: {user_id}
Title: {title}
Saved: {timestamp}
Hero Image: {hero_url}
Section Images: {len(section_urls)}
Status: FULLY FORMATTED with inline styles
════════════════════════════════════════════════════════════════
-->
"""

        complete_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>
{metadata_banner}
{final_html}
</body>
</html>"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(complete_html)

        logger.info(f"[BACKUP] Formatted article saved to {filename}")

    except Exception as e:
        logger.error(f"[BACKUP] Failed to save formatted article: {e}")


def _wp_base_url() -> str:
    """Get WordPress base URL."""
    base_url = os.getenv("WORDPRESS_REST_API_URL", "").rstrip("/")
    if base_url.endswith("/wp-json/wp/v2"):
        base_url = base_url[: -len("/wp-json/wp/v2")]
    elif base_url.endswith("/wp-json"):
        base_url = base_url[: -len("/wp-json")]
    return base_url


def _upload_media_to_wordpress(image_path: str, user_id: int):
    """Upload image to WordPress media library and return full response."""
    import requests

    wp_load_user_env(user_id)
    token = get_jwt_token(user_id)
    if not token:
        logger.error("WP upload: missing JWT token")
        return None

    url = f"{_wp_base_url()}/wp-json/wp/v2/media"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        with open(image_path, "rb") as fh:
            files = {"file": fh}
            resp = requests.post(url, headers=headers, files=files, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"WP upload: media id={data.get('id')}")
        return data
    except Exception as e:
        logger.error(f"WP upload error: {e}")
        return None


def generate_images_with_seedream(
    prompts: List[str],
    user_id: int,
    aspect_ratio: str = "16:9"
) -> List[Optional[str]]:
    """
    Generate images via Replicate SeeDream-4.

    Args:
        prompts: List of photographic prompts
        user_id: User ID for environment
        aspect_ratio: "16:9" for hero, "21:9" for sections

    Returns:
        List of image URLs (Replicate URLs, need persistence)
    """
    load_dotenv()  # Load REPLICATE_API_TOKEN from main .env

    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        logger.error("REPLICATE_API_TOKEN not found")
        return [None] * len(prompts)

    results = []

    for i, prompt in enumerate(prompts):
        max_retries = 1  # Try once, retry once if timeout
        retry_count = 0
        image_generated = False

        while retry_count <= max_retries and not image_generated:
            try:
                attempt_num = retry_count + 1
                if retry_count > 0:
                    logger.info(f"[SeeDream] RETRY {retry_count}/{max_retries} for image {i+1}")
                else:
                    logger.info(f"[SeeDream] Generating image {i+1}/{len(prompts)}: {prompt[:80]}...")

                # Create prediction with manual polling to prevent infinite loops
                prediction = replicate.predictions.create(
                    model="bytedance/seedream-4",
                    input={
                        "prompt": prompt,
                        "aspect_ratio": aspect_ratio,
                        "output_format": "jpg",
                        "output_quality": 90,
                        "num_outputs": 1,
                        "guidance_scale": 5.0,
                        "num_inference_steps": 28,
                        "disable_safety_checker": False
                    }
                )

                # Log prediction ID immediately for debugging
                logger.info(f"[SeeDream] Created prediction ID: {prediction.id}")

                # Poll with 4-minute timeout per image (sufficient for SeeDream-4)
                from datetime import datetime, timedelta
                import time

                timeout = datetime.now() + timedelta(minutes=4)
                poll_interval = 1  # Check every second
                last_status = None

                while datetime.now() < timeout:
                    prediction.reload()

                    # Log status changes for debugging
                    if prediction.status != last_status:
                        logger.info(f"[SeeDream] Prediction {prediction.id} status: {prediction.status}")
                        last_status = prediction.status

                    if prediction.status == "succeeded":
                        if prediction.output and len(prediction.output) > 0:
                            image_url = prediction.output[0]
                            results.append(image_url)
                            logger.info(f"[SeeDream] Image {i+1} succeeded: {image_url[:60]}...")
                            image_generated = True
                        else:
                            logger.error(f"[SeeDream] No output for image {i+1}")
                            results.append(None)
                            image_generated = True
                        break

                    elif prediction.status in ["failed", "canceled"]:
                        logger.error(f"[SeeDream] Image {i+1} {prediction.status}: {getattr(prediction, 'error', 'Unknown error')}")
                        results.append(None)
                        image_generated = True
                        break

                    # Still processing, wait before next check
                    time.sleep(poll_interval)
                else:
                    # Timeout reached - prediction never completed
                    logger.error(f"[SeeDream] Image {i+1} TIMED OUT after 4 minutes (Prediction ID: {prediction.id})")

                    # Cancel the stuck prediction
                    try:
                        prediction.cancel()
                        logger.info(f"[SeeDream] ✅ Canceled stuck prediction: {prediction.id}")
                        time.sleep(2)  # Wait 2 seconds before retry
                    except Exception as cancel_error:
                        logger.warning(f"[SeeDream] Could not cancel prediction: {cancel_error}")

                    # If we have retries left, try again with NEW prediction
                    if retry_count < max_retries:
                        logger.info(f"[SeeDream] Will retry image {i+1} with NEW prediction...")
                        retry_count += 1
                        continue  # Try again
                    else:
                        logger.error(f"[SeeDream] All {max_retries + 1} attempts failed for image {i+1}")
                        results.append(None)
                        image_generated = True

            except Exception as e:
                logger.error(f"[SeeDream] Error generating image {i+1} (attempt {attempt_num}): {e}")
                import traceback
                logger.error(f"[SeeDream] Traceback: {traceback.format_exc()}")

                if retry_count < max_retries:
                    logger.info(f"[SeeDream] Will retry after error...")
                    retry_count += 1
                    time.sleep(2)
                    continue
                else:
                    results.append(None)
                    image_generated = True

    return results


def persist_image_to_wordpress(tmp_url: Optional[str], user_id: int) -> Optional[str]:
    """
    Download ephemeral Replicate URL and upload to WordPress media library.

    Returns permanent WordPress source_url.
    """
    import tempfile
    import time

    if not tmp_url:
        return None

    tmp_path = None
    try:
        wp_load_user_env(user_id)
        ts = int(time.time() * 1000)
        tmp_path = os.path.join(tempfile.gettempdir(), f"ai_img_{user_id}_{ts}.jpg")

        download_image(tmp_url, tmp_path)
        media = _upload_media_to_wordpress(tmp_path, user_id)

        return (media or {}).get("source_url")

    except Exception as e:
        logger.error(f"[WP Persist] Error: {e}")
        return None

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def create_blog_post_with_images_v4(
    perplexity_research: str,
    user_id: int,
    user_system_prompt: str,
    writing_style: Optional[str] = None,
    local_mode: bool = False
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    V4 Modular Pipeline Orchestrator with Structured Article Generation

    Args:
        perplexity_research: Enhanced research from Perplexity (2000 tokens)
        user_id: User ID for environment
        user_system_prompt: User's custom prompt
        writing_style: Optional writing style for tone/visuals
        local_mode: If True, skip WordPress upload and embed images as base64 in self-contained HTML

    Returns:
        (result_dict, error_message)
        result_dict contains:
        {
            "title": "Article title",
            "content": "Fully styled HTML with magazine components and images",
            "hero_image_url": "...",  # Base64 data URI if local_mode=True
            "section_images": [...],  # Base64 data URIs if local_mode=True
            "all_images": [...],
            "summary": "...",
            "prompts": {...},
            "components": [...]  # NEW: Component metadata for debugging
        }
    """

    try:
        logger.info("=" * 80)
        logger.info("[V4 Pipeline] Starting modular article generation")
        logger.info(f"[V4 Pipeline] Writing style: {writing_style or 'Default'}")
        logger.info("=" * 80)

        # STEP 1: Generate structured article with component metadata
        logger.info("\n[STEP 1] Generating structured article content with GPT-5...")
        article_data = generate_clean_article(
            perplexity_research=perplexity_research,
            user_id=user_id,
            user_system_prompt=user_system_prompt,
            writing_style=writing_style
        )

        if not article_data:
            return None, "Story generation failed"

        title = article_data["title"]
        components = article_data.get("components", [])
        logger.info(f"[STEP 1] ✅ Article generated - Title: {title[:60]}")
        logger.info(f"[STEP 1] Components: {len(components)} ({', '.join(set(c['type'] for c in components))})")

        # SAVE POINT #1: Save raw article immediately after generation
        _save_raw_article(article_data, user_id, "after_step1")

        # STEP 2: Generate contextual image prompts
        logger.info("\n[STEP 2] Generating contextual image prompts with GPT-5-mini...")

        # Extract summary from article data or use Perplexity research
        perplexity_summary = article_data.get("executive_summary", {}).get("intro", "")
        if not perplexity_summary:
            perplexity_summary = perplexity_research[:500] + "..." if len(perplexity_research) > 500 else perplexity_research

        prompts_data = generate_contextual_image_prompts(
            article_html=article_data["html"],
            perplexity_summary=perplexity_summary,
            user_id=user_id,
            writing_style=writing_style
        )

        if not prompts_data:
            return None, "Image prompt generation failed"

        hero_prompt = prompts_data["hero_prompt"]
        section_prompts = prompts_data["section_prompts"]

        logger.info(f"[STEP 2] ✅ Generated {len(section_prompts)} section prompts")

        # STEP 3: Generate images with SeeDream-4
        logger.info("\n[STEP 3] Generating images with SeeDream-4...")

        # Hero image (16:9)
        hero_images = generate_images_with_seedream([hero_prompt], user_id, aspect_ratio="16:9")
        hero_image_tmp = hero_images[0] if hero_images else None

        # Section images (21:9)
        section_image_prompts = [sp["prompt"] for sp in section_prompts]
        section_images_tmp = generate_images_with_seedream(section_image_prompts, user_id, aspect_ratio="21:9")

        logger.info(f"[STEP 3] ✅ Generated {1 + len(section_images_tmp)} images")

        # STEP 3.5: Handle image persistence (WordPress OR local base64)
        if local_mode:
            logger.info("\n[STEP 3.5] LOCAL MODE: Using Replicate URLs directly for Claude formatting...")
            logger.info("[STEP 3.5] Images will be downloaded and embedded as base64 after formatting")

            # Keep Replicate URLs for now (valid for 60 minutes)
            hero_image_url = hero_image_tmp
            section_image_urls = section_images_tmp
            all_images = [hero_image_url] + section_image_urls

            logger.info(f"[STEP 3.5] ✅ {len(all_images)} Replicate URLs ready (60-minute window)")
        else:
            logger.info("\n[STEP 3.5] Uploading images to WordPress media library...")

            hero_image_url = persist_image_to_wordpress(hero_image_tmp, user_id)
            if not hero_image_url:
                logger.error("[STEP 3.5] Hero image persistence failed")
                return None, "Hero image upload failed"

            section_image_urls = []
            for i, tmp_url in enumerate(section_images_tmp):
                wp_url = persist_image_to_wordpress(tmp_url, user_id)
                if wp_url:
                    section_image_urls.append(wp_url)
                else:
                    logger.warning(f"[STEP 3.5] Section image {i+1} persistence failed")

            all_images = [hero_image_url] + section_image_urls

            logger.info(f"[STEP 3.5] ✅ Uploaded {len(all_images)} images to WordPress")

        # STEP 4: Assemble magazine layout with components
        logger.info("\n[STEP 4] Assembling magazine layout...")

        # Map section images to headings
        section_image_mappings = [
            {
                "heading": section_prompts[i]["section_heading"],
                "url": section_image_urls[i]
            }
            for i in range(min(len(section_prompts), len(section_image_urls)))
        ]

        # Get user's brand colors from database
        brand_colors = None
        try:
            from app_v3 import User, app
            with app.app_context():
                user = User.query.get(user_id)
                if user and not user.use_default_branding:
                    brand_colors = {
                        "primary": user.brand_primary_color or "#08b2c6",
                        "accent": user.brand_accent_color or "#ff6b11"
                    }
                    logger.info(f"[STEP 4] Using custom brand colors: {brand_colors}")
                else:
                    logger.info("[STEP 4] Using default EZWAi brand colors")
        except Exception as e:
            logger.warning(f"[STEP 4] Could not load brand colors, using defaults: {e}")

        # Try Claude AI formatter first (intelligent layout decisions)
        logger.info("[STEP 4] Attempting Claude AI-powered formatting...")
        section_image_urls_only = [img['url'] for img in section_image_mappings if img.get('url')]

        final_html = format_article_with_claude(
            article_html=article_data['html'],
            title=title,
            hero_image_url=hero_image_url,
            section_images=section_image_urls_only,
            user_id=user_id,
            brand_colors=brand_colors,
            layout_style="premium_magazine"
        )

        # Fallback to template formatter if Claude fails
        if not final_html:
            logger.warning("[STEP 4] Claude formatter failed, using template fallback")
            final_html = apply_magazine_styling(
                article_data=article_data,
                hero_image_url=hero_image_url,
                section_images=section_image_mappings,
                user_id=user_id,
                brand_colors=brand_colors
            )

            if not final_html:
                return None, "Both Claude and template formatting failed"

            logger.info(f"[STEP 4] ✅ Template layout assembled - {len(final_html)} characters")
        else:
            logger.info(f"[STEP 4] ✅ Claude AI layout assembled - {len(final_html)} characters")

        # STEP 4.5: For LOCAL MODE, download images and replace URLs with base64
        if local_mode:
            logger.info("\n[STEP 4.5] LOCAL MODE: Downloading images and embedding as base64...")
            logger.info("[STEP 4.5] ⚠️ Must complete within 60-minute Replicate expiry window")

            # Download hero image
            hero_base64 = _download_and_convert_to_base64(hero_image_url)
            if not hero_base64:
                logger.error("[STEP 4.5] Failed to download hero image")
                return None, "Hero image download failed (URL may have expired)"

            # Download section images
            section_base64_list = []
            for i, section_url in enumerate(section_image_urls):
                section_base64 = _download_and_convert_to_base64(section_url)
                if section_base64:
                    section_base64_list.append(section_base64)
                else:
                    logger.warning(f"[STEP 4.5] Failed to download section image {i+1}")

            logger.info(f"[STEP 4.5] ✅ Downloaded {1 + len(section_base64_list)} images as base64")

            # Replace Replicate URLs with base64 in formatted HTML
            logger.info("[STEP 4.5] Replacing Replicate URLs with base64 data URIs...")

            # Replace hero URL
            final_html = final_html.replace(hero_image_url, hero_base64)

            # Replace section URLs
            for i, section_url in enumerate(section_image_urls):
                if i < len(section_base64_list):
                    final_html = final_html.replace(section_url, section_base64_list[i])

            # Update URLs in result dict to base64
            hero_image_url = hero_base64
            section_image_urls = section_base64_list
            all_images = [hero_image_url] + section_image_urls

            logger.info(f"[STEP 4.5] ✅ All URLs replaced with base64 ({len(final_html)} chars)")

        # SAVE POINT #2: Save formatted article with styling
        _save_formatted_article(final_html, title, user_id, hero_image_url, section_image_urls)

        # FINAL VALIDATION
        logger.info("\n[VALIDATION] Checking output quality...")

        # Check for inline styles instead of <style> tags
        if 'style="' not in final_html:
            logger.error("[VALIDATION] Inline styles missing")
            return None, "CSS styling missing"

        # Check for hero section (now a div with inline styles, not class)
        # In local mode, hero_image_url is base64, so just check for background-image
        if local_mode:
            if "background-image" not in final_html or "data:image/" not in final_html:
                logger.error("[VALIDATION] Hero section missing")
                return None, "Hero section missing"
        else:
            if "background-image" not in final_html or hero_image_url not in final_html:
                logger.error("[VALIDATION] Hero section missing")
                return None, "Hero section missing"

        # Check for executive summary
        if "Executive Summary" not in final_html and article_data.get("executive_summary"):
            logger.warning("[VALIDATION] Executive summary missing but data provided")

        # Count inserted components
        component_checks = {
            "pull-quote": final_html.count('class="pull-quote"'),
            "stat-highlight": final_html.count('class="stat-highlight"'),
            "case-study-box": final_html.count('class="case-study-box"'),
            "sidebar-box": final_html.count('class="sidebar-box"')
        }
        logger.info(f"[VALIDATION] Components in output: {component_checks}")

        logger.info("[VALIDATION] ✅ All checks passed")

        # Assemble result
        result = {
            "title": title,
            "content": final_html,
            "hero_image_url": hero_image_url,
            "section_images": section_image_urls,
            "all_images": all_images,
            "summary": perplexity_summary,
            "prompts": {
                "hero": hero_prompt,
                "sections": section_prompts
            },
            "components": components  # Include for debugging/logging
        }

        logger.info("=" * 80)
        logger.info(f"[V4 Pipeline] ✅ SUCCESS - Article: {title[:60]}...")
        logger.info(f"[V4 Pipeline] Magazine components: {len(components)}")
        logger.info("=" * 80)

        return result, None

    except Exception as e:
        logger.error(f"[V4 Pipeline] Unhandled error: {e}")
        logger.debug(f"[V4 Pipeline] Traceback: {e}", exc_info=True)
        return None, str(e)


# Backward compatibility alias for app_v3.py
def create_blog_post_with_images_v3(blog_post_idea: str, user_id: int, system_prompt: str):
    """
    Backward compatibility wrapper - routes to V4 pipeline.

    blog_post_idea is now expected to be Perplexity research (enhanced with writing style).
    """
    logger.info("[Compatibility] Routing V3 call to V4 pipeline")
    return create_blog_post_with_images_v4(
        perplexity_research=blog_post_idea,
        user_id=user_id,
        user_system_prompt=system_prompt,
        writing_style=None  # V3 calls don't have writing style yet
    )


if __name__ == "__main__":
    # Test the complete pipeline
    logging.basicConfig(level=logging.INFO)

    test_research = """
    Bob Rohrman Kia, Indiana's largest volume Kia dealer, achieved 43% increase in 
    lead-to-appointment conversion using Impel's AI agent. The dealership handles 45%+ 
    of leads during off-hours. Sales team now focuses on high-value customers while AI 
    handles routine inquiries 24/7.

    Elk Grove Buick GMC saw 18% increase in lead conversion rate and influenced over 
    $1 million in gross sales. The family-owned Sacramento dealership generated 19% 
    more live customer calls and 22% increase in total calls per lead.

    AutoMax Dealership, operating 5 showrooms, reported 220% sales increase and 50% 
    faster deal closings. Their AI system handles initial inquiries, schedules test 
    drives, and provides vehicle information around the clock.
    """

    result, error = create_blog_post_with_images_v4(
        perplexity_research=test_research,
        user_id=1,
        user_system_prompt="Write authoritative, data-driven content for automotive dealership executives.",
        writing_style="Authoritative/Expert"
    )

    if result:
        print(f"\n✅ SUCCESS!")
        print(f"Title: {result['title']}")
        print(f"Content length: {len(result['content'])} chars")
        print(f"Images: {len(result['all_images'])}")
        print(f"Components: {len(result['components'])}")
        print(f"\nComponent types: {set(c['type'] for c in result['components'])}")
    else:
        print(f"\n❌ FAILED: {error}")