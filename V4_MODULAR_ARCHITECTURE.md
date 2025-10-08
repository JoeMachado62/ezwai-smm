# V4 Modular Architecture Design

## Problem Statement

**Current Issues (V3):**
1. ❌ Image prompts don't align well with article content
2. ❌ Image positioning is rudimentary (just matches H2/H3 tags)
3. ❌ CSS styling applied too early (before images inserted)
4. ❌ No leverage of enhanced Perplexity research in image generation
5. ❌ Monolithic pipeline - hard to debug and control

## Proposed Solution: 4-Step Modular Pipeline

### **STEP 1: Story Generation** 📝
**Module:** `story_generation.py`
**Input:** Perplexity research (with writing style context) + User system prompt
**Model:** GPT-5 Responses API
**Output:** Clean HTML article (NO CSS, NO images, just semantic HTML)

```python
def generate_article_content(perplexity_research: str, user_system_prompt: str, writing_style: str) -> dict:
    """
    Generate pure content using enhanced Perplexity research.

    Returns:
    {
        "html": "<h1>Title</h1><h2>Section 1</h2><p>...</p>...",
        "title": "Article Title"
    }
    """
```

**Key Improvements:**
- Leverages rich Perplexity research (2000 tokens instead of 500)
- Writing style context flows through from Perplexity to GPT-5
- Clean separation: content only, no styling yet

---

### **STEP 2: Section Extraction & Intelligent Image Prompt Generation** 🎨
**Module:** `image_prompt_generator.py`
**Input:** Article HTML + Perplexity research summary
**Model:** GPT-5-mini (cheaper, faster)
**Output:** Section-aligned photographic prompts

```python
def generate_contextual_image_prompts(
    article_html: str,
    perplexity_summary: str,
    writing_style: str
) -> dict:
    """
    Extract sections and generate image prompts that align with content.

    Returns:
    {
        "hero_prompt": "...",
        "section_prompts": [
            {"section_heading": "AI in Healthcare", "prompt": "..."},
            {"section_heading": "Future Trends", "prompt": "..."}
        ]
    }
    """
```

**Critical Prompt Engineering:**

```
SYSTEM PROMPT:
"You are an expert photography art director for editorial magazines. Your job is to create
photographic image prompts that perfectly complement written content.

INSTRUCTIONS:
1. Read the article carefully to understand the narrative and key themes
2. For each section, identify the most visual, impactful concept
3. Create prompts that are:
   - PHOTOREALISTIC (not illustrations, not abstract art)
   - EDITORIAL QUALITY (National Geographic, TIME Magazine style)
   - CONTEXTUALLY ALIGNED (match the section's specific topic)
   - TECHNICALLY DETAILED (camera, lens, lighting, composition)

4. Writing Style Consideration: {writing_style}
   - Authoritative/Expert: Use professional settings, expert subjects, data visualization
   - Narrative/Storytelling: Use human subjects, emotional moments, story-driven scenes
   - Investigative: Use documentary-style, revealing details, evidence-focused
   - etc.

USER PROMPT:
Article HTML:
{article_html}

Perplexity Research Summary:
{perplexity_summary}

Generate photographic prompts for:
1. HERO image (16:9) - Captures the overall article theme
2. Section images (4:3) - One for each major section (H2), aligned with that section's content

For each prompt include:
- Main subject/scene
- Camera & lens (e.g., "Shot on Canon R5, 50mm f/1.4")
- Lighting (e.g., "Golden hour natural light", "Studio softbox lighting")
- Composition (e.g., "Rule of thirds", "Centered symmetry")
- Mood/atmosphere
- Color palette if relevant

CRITICAL: Match each section heading to its specific content. Don't use generic prompts.
Example: Section "AI in Radiology" → "Medical professional analyzing AI-enhanced X-rays on
multiple monitors in modern hospital radiology department, Canon R5, 24-70mm f/2.8, clean
clinical lighting..."
```

---

### **STEP 3: Magazine Styling & Image Insertion** 🎨
**Module:** `magazine_formatter.py`
**Input:** Clean HTML article + Section prompts + Generated images
**Model:** GPT-5-mini (HTML/CSS expert)
**Output:** Fully styled magazine article

```python
def apply_magazine_styling(
    article_html: str,
    images: dict,
    section_prompts: list
) -> str:
    """
    Apply magazine CSS and insert images intelligently.

    GPT-5-mini receives:
    - Clean HTML article
    - Section headings with corresponding image URLs
    - Magazine CSS template

    Task: Insert images as section banners BEFORE the matching heading
    """
```

**GPT-5-mini Prompt:**

```
SYSTEM:
"You are an expert HTML/CSS developer for magazine publications. Your job is to take
clean article HTML and transform it into a beautifully styled magazine layout with images."

USER:
I have a clean HTML article and section-specific images. Please:

1. Insert the HERO image as a hero-section div BEFORE the H1
2. For each section image, insert a section-header div BEFORE the corresponding H2 heading
3. Wrap everything in <div class="magazine-article">
4. Add the magazine CSS (provided below)

RULES:
- Hero image uses class "hero-section" (16:9 aspect)
- Section images use class "section-header" (4:3 aspect)
- The H1 title goes INSIDE the hero-section div
- The H2 headings go INSIDE their section-header divs
- Preserve all article content unchanged
- Use background-image CSS, not <img> tags

Article HTML:
{clean_html}

Images:
Hero: {hero_url}
Section: "{section_1_heading}" → {section_1_url}
Section: "{section_2_heading}" → {section_2_url}
...

Magazine CSS:
{MAGAZINE_ARTICLE_CSS}

Return the complete, styled HTML ready for WordPress.
```

---

### **STEP 4: WordPress Publishing** 🚀
**Module:** `wordpress_integration.py` (existing, minor updates)
**Input:** Final styled HTML + metadata
**Output:** Published WordPress post

No changes needed - just receives better formatted content.

---

## Data Flow Diagram

```
[User Input: Topic + Writing Style]
           ↓
[PERPLEXITY API - Enhanced Research]
  → 2000 tokens of rich, style-aware research
  → Statistics, quotes, case studies
           ↓
[STEP 1: GPT-5 Story Generation]
  → Input: Perplexity research + System prompt + Writing style
  → Output: Clean HTML (no CSS, no images)
           ↓
[STEP 2: GPT-5-mini Section Analysis]
  → Input: Article HTML + Perplexity summary + Writing style
  → Output: Section-aligned image prompts
           ↓
[REPLICATE: SeeDream-4 Image Generation]
  → Generate 4 photorealistic images
  → Upload to WordPress media library
           ↓
[STEP 3: GPT-5-mini Magazine Formatting]
  → Input: Clean HTML + Section mappings + Image URLs
  → Output: Fully styled magazine HTML
           ↓
[STEP 4: WordPress Publishing]
  → Post to WordPress
  → Email notification
```

---

## Benefits of Modular Architecture

### 1. **Better Image Alignment** 🎯
- Image prompts know exact section content
- Not generic "AI image" but "AI-powered radiology diagnosis with doctor reviewing scans"
- Writing style influences visual approach

### 2. **Leverages Enhanced Perplexity** 📊
- Rich research feeds into story generation
- Same research context used for image prompts
- Coherent narrative across text and visuals

### 3. **Debugging & Control** 🔧
- Each step is independently testable
- Can inspect outputs at each stage
- Easy to adjust prompts per step

### 4. **Cost Efficiency** 💰
- GPT-5 only for main article (most important)
- GPT-5-mini for extraction and formatting (cheaper)
- Same total cost, better quality

### 5. **CSS/Styling Correctness** ✨
- GPT-5-mini has one job: format correctly
- Explicit instructions for image placement
- No more style drift or positioning errors

---

## Implementation Files

1. **`story_generation.py`** - STEP 1
2. **`image_prompt_generator.py`** - STEP 2
3. **`magazine_formatter.py`** - STEP 3
4. **`openai_integration_v4.py`** - Orchestrator (ties all steps together)

---

## Migration Path

1. ✅ Keep V3 functional
2. 🔄 Build V4 modules incrementally
3. 🧪 Test each module independently
4. 🔀 Switch main flow to V4 when ready
5. 📊 Compare V3 vs V4 outputs

---

## Key Prompt Engineering Insights

### For Image Prompts (STEP 2):
```
BAD (Current V3):
"Professional image for technology article"

GOOD (V4):
"Close-up of surgeon's hands operating AR surgical interface showing
3D holographic patient anatomy, modern operating room background,
Canon R5 85mm f/1.4, dramatic side lighting, focused intensity,
teal and white color palette"
```

### Why This Works:
1. **Specificity**: Exact scene described
2. **Context**: Matches article section about AR surgery
3. **Technical**: Camera/lens adds photorealism
4. **Mood**: Lighting and composition guide
5. **Style-aware**: Authoritative → professional setting

### For Magazine Formatting (STEP 3):
- Give GPT-5-mini explicit mapping: Section heading → Image URL
- Use structured instructions (numbered steps)
- Provide CSS template to reference
- Request specific HTML structure

---

## Testing Strategy

### Unit Tests:
- `test_story_generation()` - Verify clean HTML output
- `test_image_prompts()` - Check prompt quality and section alignment
- `test_magazine_formatting()` - Validate CSS and image insertion

### Integration Test:
- End-to-end with real Perplexity → GPT-5 → Images → Formatting
- Compare against V3 outputs
- Measure image relevance (manual review)

### Success Metrics:
- ✅ Images align with section content (90%+ relevance)
- ✅ CSS styling correct (no drift)
- ✅ Hero image captures article theme
- ✅ Section images match their headings
- ✅ Magazine layout renders perfectly

---

## Next Steps

1. Create `story_generation.py`
2. Create `image_prompt_generator.py` with smart prompting
3. Create `magazine_formatter.py` with explicit styling
4. Build `openai_integration_v4.py` orchestrator
5. Test with various writing styles and topics
6. Deploy as V4
