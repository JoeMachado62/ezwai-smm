here’s a clear, copy-paste friendly “fix kit” your devs can follow step-by-step. It assumes they already applied some changes that introduced tools=[...] and temperature, and you now want the final, stable version that:

uses GPT-5 (full) only for the story writing pass,

keeps mini for the structured JSON passes (summary/outline + image prompts),

never uses tools=[...] for those JSON steps,

never sends temperature to models that don’t support it, and

persists images to WordPress with permanent URLs.

✅ Implementation Guide (do these steps in order)
0) Make a safety copy (5 seconds)

Before editing:

Duplicate your current file:

openai_integration_v3.py → openai_integration_v3.backup.py

1) Add model selection + safe sampling helpers (top of file)

Put these near the imports, after import os etc., so we can safely choose per-pass models and only add temperature to models that support it.

# =========================
# Model selection & sampling
# =========================
MODEL_FOR_PASS1 = os.getenv("MODEL_FOR_PASS1", "gpt-5")       # story writing (full model)
MODEL_FOR_PASS2 = os.getenv("MODEL_FOR_PASS2", "gpt-5-mini")  # summary/outline (JSON)
MODEL_FOR_PASS3 = os.getenv("MODEL_FOR_PASS3", "gpt-5-mini")  # image prompts (JSON)

def _supports_sampling(model: str) -> bool:
    """
    Only return True for models you've verified accept temperature/top_p.
    Keep this conservative to avoid 400 errors on create().
    """
    return model in {"gpt-5", "gpt-4.1", "gpt-4.1-mini"}

def create_responses_request(model: str, messages, **kw):
    """
    Build a Responses API request and only attach temperature if the model allows it.
    For JSON steps we will NOT send temperature (callers simply won't pass it).
    """
    req = dict(model=model, input=messages, **kw)

    # Optional creativity knob for Pass 1 only (story writing)
    temp_env = os.getenv("ARTICLE_TEMPERATURE")  # e.g., "0.7"
    if temp_env and _supports_sampling(model):
        try:
            req["temperature"] = float(temp_env)
        except ValueError:
            pass  # ignore invalid values

    return req

Add these to your .env (or .env.user_{id}):
MODEL_FOR_PASS1=gpt-5
MODEL_FOR_PASS2=gpt-5-mini
MODEL_FOR_PASS3=gpt-5-mini
ARTICLE_TEMPERATURE=0.7


If you don’t want sampling on Pass 1, omit ARTICLE_TEMPERATURE entirely.

2) Fix PASS 1 (Story writing) to use the helper and messages format

Find your process_blog_post_idea_v3(...) function.
Replace the OpenAI call inside it with this block:

client = _get_openai_client()
enhanced_prompt = create_magazine_article_prompt(blog_post_idea, system_prompt)

logger.info("OpenAI[Pass1]: generating full article...")
resp = client.responses.create(**create_responses_request(
    MODEL_FOR_PASS1,
    [
        {"role": "system", "content":
            "You are an expert magazine writer. Produce clean HTML only (no JSON), "
            "with semantic headings and paragraphs, suitable for the provided CSS."
        },
        {"role": "user", "content": enhanced_prompt},
    ],
    max_output_tokens=16000,
))
full_article = getattr(resp, "output_text", None)


Do not add response_format here—we want free-form text (HTML) for Pass 1.
Do not add tools=[...] here either.

3) Fix PASS 2 (Summary + outline) — use Structured Outputs, NO tools, NO temperature

Find summarize_and_outline(article_html: str) and replace the call body with:

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

logger.info("OpenAI[Pass2]: summarizing & extracting outline...")
resp = client.responses.create(
    model=MODEL_FOR_PASS2,
    input=[
        {"role": "system", "content": "You are an accurate summarizer and structural parser. Return only JSON per the provided schema."},
        {"role": "user", "content":
            "From the following HTML article, extract the <h2> section headers and write a 120–180 word executive summary. "
            "Return ONLY JSON that matches the provided JSON schema.\n\n"
            f"ARTICLE HTML:\n{article_html}"
        },
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {"name": "ArticleOutline", "schema": schema, "strict": True},
    },
    max_output_tokens=1200,
    # IMPORTANT: no temperature here; many mini models reject it
)
out = getattr(resp, "output_text", "") or ""
json_text = _extract_first_json_object(out) or out
data: Dict[str, Any] = json.loads(json_text)


Key points:

No tools / function calling.

Use response_format: json_schema (strict).

No temperature argument.

4) Fix PASS 3A (Image prompts) — Structured Outputs, NO tools, NO temperature

Find generate_photographic_image_prompts(...) and replace the call body with:

client = _get_openai_client()
schema: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "prompts": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": num_images, "maxItems": num_images,
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

logger.info("OpenAI[Pass3A]: generating image prompts...")
resp = client.responses.create(
    model=MODEL_FOR_PASS3,
    input=[
        {"role": "system", "content": instructions},
        {"role": "user", "content": payload},
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {"name": "ImagePrompts", "schema": schema, "strict": True},
    },
    max_output_tokens=800,
    # IMPORTANT: no temperature here; keep JSON deterministic
)
out = getattr(resp, "output_text", "") or ""
json_text = _extract_first_json_object(out) or out
data: Dict[str, Any] = json.loads(json_text)
prompts: List[str] = data.get("prompts", [])


Again: no tools, no temperature here.

5) Remove all tools=[ ... ] and tool-parsing logic

Search your file for tools= or tool_calls/function_call/resp.output parsing that assumes tools. Delete it.
The design here uses Structured Outputs instead (simpler, robust, and matches the rest of your pipeline).

6) Keep image persistence to WordPress (no changes required if you already have it)

Ensure you still have these (or equivalent) functions and imports:

from wordpress_integration import (
    download_image as wp_download_image,
    get_jwt_token,
    load_user_env as wp_load_user_env,
)

# _upload_media_to_wordpress(image_path, user_id) -> returns dict with id/source_url
# _persist_image_to_wordpress(tmp_url, user_id) -> returns source_url
# insert_images_into_article(content, images) -> inserts hero + section headers


The orchestrator should still:

generate images (SeeDream),

persist each to WP (replace ephemeral Replicate links),

then embed the WP source_urls in the final HTML.

7) Optional but recommended: logging to file + Pass 2 debug dumps

At the top (after logger is created), add rotating file logs:

from logging.handlers import RotatingFileHandler
log_dir = os.getenv("EZWAI_LOG_DIR", "./logs")
os.makedirs(log_dir, exist_ok=True)
fh = RotatingFileHandler(os.path.join(log_dir, "ezwai.log"), maxBytes=2_000_000, backupCount=3, encoding="utf-8")
fh.setLevel(getattr(logging, os.getenv("EZWAI_LOG_LEVEL", "INFO").upper(), logging.INFO))
fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
logger.addHandler(fh)


In summarize_and_outline(...), add parse-fail dumps:

out = getattr(resp, "output_text", "") or ""
json_text = _extract_first_json_object(out) or out
try:
    data: Dict[str, Any] = json.loads(json_text)
except Exception:
    dump_dir = os.getenv("EZWAI_DUMP_DIR", "./logs")
    os.makedirs(dump_dir, exist_ok=True)
    with open(os.path.join(dump_dir, "pass2_out.txt"), "w", encoding="utf-8") as f: f.write(out)
    with open(os.path.join(dump_dir, "pass2_json_candidate.txt"), "w", encoding="utf-8") as f: f.write(json_text)
    with open(os.path.join(dump_dir, "pass2_article_len.txt"), "w", encoding="utf-8") as f: f.write(str(len(article_html)))
    logger.error("OpenAI[Pass2]: JSON parse error — dumped pass2_out.txt & pass2_json_candidate.txt")
    raise


To turn on verbose logging without code changes, set:

EZWAI_LOG_LEVEL=DEBUG

🔎 Quick verification checklist (run after you edit)

Search the file for tools= — it should not appear anywhere.

Search the file for temperature — it should appear only inside create_responses_request and never in Pass 2/3A calls.

Ensure these exact model variables appear at the top:

MODEL_FOR_PASS1
MODEL_FOR_PASS2
MODEL_FOR_PASS3


Ensure Pass 1 call uses:

client.responses.create(**create_responses_request(MODEL_FOR_PASS1, [...], max_output_tokens=16000))


and does not set response_format.

Ensure Pass 2 and Pass 3A calls include response_format: { type: "json_schema", strict: true } and do not include temperature or tools.

🧪 How to test

From your project root:

# (optional) Turn on debug logs
export EZWAI_LOG_LEVEL=DEBUG

# (optional) set models/temperature
export MODEL_FOR_PASS1=gpt-5
export MODEL_FOR_PASS2=gpt-5-mini
export MODEL_FOR_PASS3=gpt-5-mini
export ARTICLE_TEMPERATURE=0.7

# run your test harness
python test_article_generation.py


Expect to see in the console/logs:

OpenAI[Pass1]: generating full article... then a title

OpenAI[Pass2]: summarizing & extracting outline...

OpenAI[Pass3A]: generating image prompts...

SeeDream-4: generating image 1/4 ...

WP upload: media id=... (for each image)

Pipeline: success — title='...'

If it fails at Pass 2, check ./logs/pass2_out.txt and ./logs/pass2_json_candidate.txt.

🧯 Common mistakes (and quick fixes)

“Unsupported parameter: temperature” → You’re sending temperature to a model that rejects it.
Fix: Only add temperature via create_responses_request (which checks _supports_sampling) and never for Pass 2/3A.

They added tools=[...] to JSON steps → You’ll get non-JSON outputs or tool call objects instead of text.
Fix: Remove tools. Use response_format: json_schema and parse response.output_text.

They tried to parse resp.output events → Not needed here.
Fix: Read resp.output_text for the final text; then json.loads.

Images disappear later → You embedded Replicate URLs instead of WordPress source_urls.
Fix: Confirm the pipeline persisted each image to WP and rewrote the HTML before preview/posting.

If you want, I can also generate a single, final file with all of the above already in place so you can drop it in verbatim.