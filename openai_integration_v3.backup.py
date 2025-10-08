"""
openai_integration_v3.py — Canonical Full (Drop‑in, Pylance‑Clean)
------------------------------------------------------------------
- Multi-pass content pipeline using the OpenAI Responses API.
- Strict JSON via response_format=json_schema for structured steps.
- SeeDream-4 (Replicate) for photorealistic images.
- Persist ALL images to WordPress Media; embed WP source_url in final HTML.
- Expanded magazine CSS + rich logging and comments.
- Signatures and return payload align with existing callers.

Public entry (unchanged):
    create_blog_post_with_images_v3(blog_post_idea: str, user_id: int, system_prompt: str)
"""

from __future__ import annotations

import os
import re
import json
import logging
import traceback
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI
import replicate

# ----------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------
LOG_LEVEL = os.getenv("EZWAI_LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# Environment
# ----------------------------------------------------------------------------
def load_user_env(user_id: int) -> None:
    """
    Load environment for a given user then base .env as fallback.
    """
    load_dotenv(f".env.user_{user_id}")
    load_dotenv()

# ----------------------------------------------------------------------------
# Magazine CSS
# ----------------------------------------------------------------------------
MAGAZINE_ARTICLE_CSS = """
/* ===== EZWAI Magazine CSS (expanded) ===== */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --brand-primary: #08b2c6;
  --brand-accent:  #ff6b11;
  --text-ink:      #171717;
  --text-muted:    #4b5563;
  --bg-paper:      #ffffff;
  --bg-tint:       #f6f7fb;
  --rule:          #e5e7eb;
}

.magazine-article {
  font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: var(--text-ink);
  background: var(--bg-paper);
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 24px 64px;
  line-height: 1.78;
  font-size: 1.0625rem;
}

.magazine-article h1 {
  font-family: 'Playfair Display', Georgia, serif;
  font-weight: 900;
  font-size: clamp(42px, 6vw, 64px);
  line-height: 1.12;
  margin: 24px 0 8px;
  letter-spacing: -0.02em;
}

.magazine-article .dek {
  font-size: 1.125rem;
  color: var(--text-muted);
  margin: 8px 0 24px;
}

.magazine-article h2 {
  font-family: 'Playfair Display', Georgia, serif;
  font-weight: 800;
  font-size: clamp(28px, 3.4vw, 40px);
  line-height: 1.18;
  margin: 36px 0 12px;
  letter-spacing: -0.01em;
}

.magazine-article h3 {
  font-weight: 700;
  font-size: clamp(20px, 2.2vw, 26px);
  margin: 28px 0 12px;
}

.magazine-article hr {
  border: 0;
  border-top: 1px solid var(--rule);
  margin: 36px 0;
}

.magazine-article p { margin: 12px 0; }
.magazine-article ul, .magazine-article ol { padding-left: 28px; margin: 14px 0; }
.magazine-article li { margin: 6px 0; }

.hero-section {
  height: 480px;
  background-size: cover;
  background-position: center center;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  text-align: center;
  position: relative;
  margin: 24px 0 8px;
  overflow: hidden;
}
.hero-section::after {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at center, rgba(0,0,0,.25) 0%, rgba(0,0,0,.45) 60%, rgba(0,0,0,.55) 100%);
}
.hero-section h1 {
  position: relative;
  z-index: 1;
  color: #fff;
  text-shadow: 0 20px 50px rgba(0,0,0,.35);
  padding: 0 16px;
}

.section-header {
  height: 340px;
  background-size: cover;
  background-position: center;
  border-radius: 16px;
  display: flex;
  align-items: flex-end;
  color: #fff;
  margin: 40px 0 24px;
  position: relative;
  overflow: hidden;
}
.section-header .overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.0) 20%, rgba(0,0,0,0.65) 100%);
}
.section-header h2 {
  position: relative;
  z-index: 1;
  color: #fff;
  margin: 0 0 14px 16px;
  text-shadow: 0 16px 40px rgba(0,0,0,.35);
}

@media (max-width: 640px) {
  .hero-section { height: 360px; }
  .section-header { height: 260px; }
}
"""

def get_magazine_html_template() -> str:
    return f"<style>\n{MAGAZINE_ARTICLE_CSS}\n</style>"

def wrap_article_with_magazine_css(content: str) -> str:
    return f"<style>\n{MAGAZINE_ARTICLE_CSS}\n</style>\n{content}"

# ----------------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------------
def _extract_first_json_object(s: str) -> Optional[str]:
    """Extract first top-level JSON object by scanning braces (defensive)."""
    if not s:
        return None
    depth = 0
    start = None
    for i, ch in enumerate(s):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    return s[start : i + 1]
    return None

# ----------------------------------------------------------------------------
# OpenAI helpers
# ----------------------------------------------------------------------------
def _get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set.")
    return OpenAI(api_key=api_key)

def create_magazine_article_prompt(blog_post_idea: str, system_prompt: str) -> str:
    return (
        f"{system_prompt.strip()}\n\n"
        "Write a long-form magazine article in HTML using semantic tags (<h1>, <h2>, <h3>, <p>, lists). "
        "Start with <h1> (article title), then a single-paragraph dek, then well-structured sections. "
        "Avoid inline styles and do not include <style> tags.\n\n"
        "Topic:\n" + blog_post_idea.strip()
    )

# ----------------------------------------------------------------------------
# PASS 1 — Article generation
# ----------------------------------------------------------------------------
def process_blog_post_idea_v3(blog_post_idea: str, user_id: int, system_prompt: str) -> Optional[dict]:
    load_user_env(user_id)
    client = _get_openai_client()

    try:
        enhanced_prompt = create_magazine_article_prompt(blog_post_idea, system_prompt)
        logger.info("OpenAI[Pass1]: generating full article...")

        resp = client.responses.create(
            model="gpt-5-mini",
            input=[
                {"role": "system", "content": (
                    "You are an expert magazine writer. Produce clean HTML only (no JSON), "
                    "with semantic headings and paragraphs, suitable for the provided CSS."
                )},
                {"role": "user", "content": enhanced_prompt},
            ],
            max_output_tokens=16000,
        )

        full_article = getattr(resp, "output_text", None)
        if not full_article or len(full_article.strip()) < 100:
            logger.error("OpenAI[Pass1]: empty or too-short article.")
            return None

        m = re.search(r"<h1[^>]*>(.*?)</h1>", full_article, flags=re.I | re.S)
        title = re.sub(r"\s+", " ", m.group(1)).strip() if m else "Untitled"

        content_with_style = f"{get_magazine_html_template()}\n<div class=\"magazine-article\">\n{full_article}\n</div>"
        logger.info("OpenAI[Pass1]: article generated — title: %s", title[:120])
        return {"full_article": full_article, "title": title, "content": content_with_style}
    except Exception as e:
        logger.error("OpenAI[Pass1] error: %s", e)
        logger.debug("Traceback: %s", traceback.format_exc())
        return None

# ----------------------------------------------------------------------------
# PASS 2 — Summary + outline (strict JSON)
# ----------------------------------------------------------------------------
def summarize_and_outline(article_html: str) -> Optional[Dict[str, Any]]:
    client = _get_openai_client()

    schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"h2": {"type": "string"}},
                    "required": ["h2"],
                    "additionalProperties": False,
                },
                "minItems": 1,
            },
        },
        "required": ["title", "summary", "sections"],
        "additionalProperties": False,
    }

    try:
        logger.info("OpenAI[Pass2]: summarizing & extracting outline...")
        resp = client.responses.create(
            model="gpt-5-mini",
            input=[
                {"role": "system", "content":
                    "You are an accurate summarizer and structural parser. "
                    "Return only JSON that matches the provided schema."
                },
                {"role": "user", "content":
                    "From the following HTML article, extract the <h2> section headers "
                    "and write a 120–180 word executive summary. "
                    "Return ONLY JSON that matches the provided JSON schema.\n\n"
                    f"ARTICLE HTML:\n{article_html}"
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "ArticleOutline", "schema": schema, "strict": True},
            },
            # IMPORTANT: no temperature here (model rejects it)
            max_output_tokens=1200,
        )

        out = getattr(resp, "output_text", "") or ""
        json_text = _extract_first_json_object(out) or out
        data: Dict[str, Any] = json.loads(json_text)

        if not data.get("summary", "").strip():
            text_only = re.sub(r"<[^>]+>", " ", article_html)
            data["summary"] = re.sub(r"\s+", " ", text_only).strip()[:1200]
            logger.warning("OpenAI[Pass2]: empty summary corrected by fallback.")

        if len(data.get("sections", [])) < 3:
            h3s = re.findall(r"<h3[^>]*>(.*?)</h3>", article_html, flags=re.I | re.S)
            for h in h3s:
                if len(data["sections"]) >= 3:
                    break
                data["sections"].append({"h2": re.sub(r"\s+", " ", h).strip()})
            logger.debug("OpenAI[Pass2]: augmented sections to at least 3.")

        return data
    except Exception as e:
        logger.error("OpenAI[Pass2] error: %s", e)
        logger.debug("Traceback: %s", traceback.format_exc())
        return None

# ----------------------------------------------------------------------------
# PASS 3A — Image prompts (strict JSON)
# ----------------------------------------------------------------------------
def generate_photographic_image_prompts(summary: str, sections: List[Dict[str, str]], num_images: int = 4) -> List[str]:
    client = _get_openai_client()

    schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "prompts": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": num_images,
                "maxItems": num_images,
            }
        },
        "required": ["prompts"],
        "additionalProperties": False,
    }

    section_titles: List[str] = [s.get("h2", "") for s in sections][: max(0, num_images - 1)]
    instructions = (
        "You are a photography art director. Return ONLY valid JSON for prompts.\n"
        "CRITERIA:\n"
        "- Photorealistic editorial quality\n"
        "- Camera/lens + lighting guidance\n"
        "- Composition, subject, background, mood\n"
        "- Avoid brand logos/text/watermarks\n"
        "PROMPT SLOTS:\n"
        "1) HERO image (16:9) — cover image for the overall story\n" +
        "\n".join([f"{i+2}) Section image (4:3) — {t}" for i, t in enumerate(section_titles)])
    )
    payload = f"Executive Summary:\n{summary}\n\nSection Headers:\n- " + "\n- ".join(section_titles)

    try:
        logger.info("OpenAI[Pass3A]: generating image prompts...")
        resp = client.responses.create(
            model="gpt-5-mini",
            input=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": payload},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "ImagePrompts", "schema": schema, "strict": True},
            },
            # IMPORTANT: no temperature here (model rejects it)
            max_output_tokens=800,
        )
        out = getattr(resp, "output_text", "") or ""
        json_text = _extract_first_json_object(out) or out
        data: Dict[str, Any] = json.loads(json_text)
        prompts: List[str] = data.get("prompts", [])
        if len(prompts) != num_images:
            raise ValueError(f"Expected {num_images} prompts, got {len(prompts)}")
        return prompts
    except Exception as e:
        logger.error("OpenAI[Pass3A] error: %s", e)
        logger.debug("Traceback: %s", traceback.format_exc())
        return []

# ----------------------------------------------------------------------------
# SeeDream‑4 (Replicate) image gen
# ----------------------------------------------------------------------------
def generate_images_with_seedream(prompts: List[str], user_id: int, aspect_ratio: str = "16:9") -> List[Optional[str]]:
    load_user_env(user_id)
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        logger.error("SeeDream-4: REPLICATE_API_TOKEN not found.")
        return []

    try:
        rclient = replicate.Client(api_token=token)
    except Exception as e:
        logger.error("SeeDream-4: failed to init client: %s", e)
        return []

    images: List[Optional[str]] = []
    for i, prompt in enumerate(prompts):
        try:
            logger.info("SeeDream-4: generating image %d/%d (%s)", i + 1, len(prompts), aspect_ratio)
            output = rclient.run(
                "seedov/sd4.1:8e7278b3f9f39d2d2d5de8310a4c1b1b",
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "output_quality": 95,
                    "output_format": "png",
                    "safety_tolerance": "0",
                },
            )
            if isinstance(output, list) and output:
                images.append(output[0])
            elif isinstance(output, str):
                images.append(output)
            else:
                logger.warning("SeeDream-4: empty output for idx=%d", i)
                images.append(None)
        except Exception as e:
            logger.error("SeeDream-4: error for idx=%d — %s", i, e)
            images.append(None)
    return images

# ----------------------------------------------------------------------------
# WordPress media persistence
# ----------------------------------------------------------------------------
from wordpress_integration import (
    download_image as wp_download_image,
    get_jwt_token,
    load_user_env as wp_load_user_env,
)

def _wp_base_url() -> str:
    base_url = os.getenv("WORDPRESS_REST_API_URL", "").rstrip("/")
    if base_url.endswith("/wp-json/wp/v2"):
        base_url = base_url[: -len("/wp-json/wp/v2")]
    elif base_url.endswith("/wp-json"):
        base_url = base_url[: -len("/wp-json")]
    return base_url

def _upload_media_to_wordpress(image_path: str, user_id: int) -> Optional[Dict[str, Any]]:
    import requests
    wp_load_user_env(user_id)
    token = get_jwt_token(user_id)
    if not token:
        logger.error("WP upload: missing JWT token.")
        return None

    url = f"{_wp_base_url()}/wp-json/wp/v2/media"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with open(image_path, "rb") as fh:
            files = {"file": fh}
            resp = requests.post(url, headers=headers, files=files, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        logger.info("WP upload: media id=%s", data.get("id"))
        return data
    except Exception as e:
        logger.error("WP upload: error: %s", e)
        return None

def _persist_image_to_wordpress(tmp_url: Optional[str], user_id: int) -> Optional[str]:
    """
    Download ephemeral URL to temp, upload to WP Media, return permanent source_url.
    """
    import tempfile
    import time

    tmp_path: Optional[str] = None
    if not tmp_url:
        return None

    try:
        wp_load_user_env(user_id)
        ts = int(time.time() * 1000)
        tmp_path = os.path.join(tempfile.gettempdir(), f"ai_img_{user_id}_{ts}.jpg")
        wp_download_image(tmp_url, tmp_path)
        media = _upload_media_to_wordpress(tmp_path, user_id)
        return (media or {}).get("source_url")
    except Exception as e:
        logger.error("WP persist: %s", e)
        return None
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

# ----------------------------------------------------------------------------
# HTML post-processing
# ----------------------------------------------------------------------------
def insert_images_into_article(content: str, images: List[Optional[str]]) -> str:
    """
    Insert hero and section header images.
    images[0] = hero; images[1:] = section images.
    """
    if not content or not images:
        return content

    updated = content

    # HERO (insert after first </style>)
    if images[0]:
        hero_html = f"""
<div class="hero-section" style="background-image:url('{images[0]}');">
  <h1>{{TITLE_PLACEHOLDER}}</h1>
</div>
"""
        updated = re.sub(r"(</style>\s*)", r"\1" + hero_html, updated, count=1, flags=re.I)

    # SECTION HEADERS
    section_images: List[str] = [img for img in images[1:] if isinstance(img, str) and img]
    if section_images:
        h3_matches = list(re.finditer(r"<h3[^>]*>(.*?)</h3>", updated, flags=re.I | re.S))
        if not h3_matches:
            h3_matches = list(re.finditer(r"<h2[^>]*>(.*?)</h2>", updated, flags=re.I | re.S))

        if h3_matches:
            sections_per_image = max(1, len(h3_matches) // len(section_images))
            for idx, img_url in enumerate(section_images):
                insert_at = min(idx * sections_per_image, len(h3_matches) - 1)
                match = h3_matches[insert_at]
                heading_text = re.sub(r"\s+", " ", match.group(1)).strip()
                section_html = f"""
<div class="section-header" style="background-image:url('{img_url}');">
  <div class="overlay"></div>
  <h2>{heading_text}</h2>
</div>
"""
                pos = match.end()
                updated = updated[:pos] + section_html + updated[pos:]

    return updated

# ----------------------------------------------------------------------------
# Orchestrator (public entry)
# ----------------------------------------------------------------------------
def create_blog_post_with_images_v3(blog_post_idea: str, user_id: int, system_prompt: str):
    """
    Run the multi-pass pipeline and return (result, error_message).
    """
    logger.info("Pipeline: start for user=%s", user_id)
    try:
        # 1) ARTICLE
        processed = process_blog_post_idea_v3(blog_post_idea, user_id, system_prompt)
        if not processed:
            return None, "Failed to generate article."
        title = processed["title"]
        article_html = processed["full_article"]

        # 2) SUMMARY + OUTLINE
        outline = summarize_and_outline(article_html)
        if not outline:
            return None, "Failed to summarize/outline article."
        summary = outline["summary"]
        sections: List[Dict[str, str]] = outline["sections"]

        # 3) IMAGE PROMPTS
        num_images = 4
        prompts = generate_photographic_image_prompts(summary, sections, num_images=num_images)
        if len(prompts) != num_images:
            logger.warning("Pass3A: fallback image prompts (size mismatch).")
            prompts = [f"Photorealistic editorial magazine photo — {title}"]
            for s in sections[: num_images - 1]:
                prompts.append(f"Photorealistic editorial magazine photo — {s.get('h2','Section')}")
            while len(prompts) < num_images:
                prompts.append(f"Photorealistic editorial magazine photo — {title} (detail)")
            prompts = prompts[:num_images]

        # 4) IMAGE GENERATION
        hero_img = generate_images_with_seedream([prompts[0]], user_id=user_id, aspect_ratio="16:9")
        section_imgs = generate_images_with_seedream(prompts[1:], user_id=user_id, aspect_ratio="4:3")

        raw_images: List[Optional[str]] = (hero_img if hero_img else [None]) + (section_imgs if section_imgs else [None, None, None])
        logger.info("Images generated (raw): %s", raw_images)

        # 5) PERSIST TO WORDPRESS
        persisted_images: List[Optional[str]] = []
        for u in raw_images:
            persisted_images.append(_persist_image_to_wordpress(u, user_id))
        all_images: List[Optional[str]] = persisted_images
        logger.info("Images persisted (WP): %s", all_images)

        # 6) HTML INSERTION
        article_with_images = insert_images_into_article(processed["content"], all_images)
        final_content = wrap_article_with_magazine_css(article_with_images).replace("{TITLE_PLACEHOLDER}", title)

        # Result payload (compatible with callers)
        result: Dict[str, Any] = {
            "title": title,
            "content": final_content,
            "hero_image_url": all_images[0] if all_images else None,
            "section_images": all_images[1:] if all_images else [],
            "all_images": all_images,
            "summary": summary,
            "sections": sections,
            "prompts": prompts,
        }
        logger.info("Pipeline: success — title='%s'", title[:120])
        return result, None

    except Exception as e:
        logger.error("Pipeline: unhandled error: %s", e)
        logger.debug("Traceback: %s", traceback.format_exc())
        return None, str(e)
