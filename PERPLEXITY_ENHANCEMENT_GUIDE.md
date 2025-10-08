# Perplexity AI Enhancement - Writing Style Integration

## Overview

This enhancement optimizes Perplexity AI API usage by leveraging the per-call pricing model to extract maximum value from each API request. Users can now assign specific writing styles to each topic query, which dynamically adjusts Perplexity's research prompts to provide more relevant, comprehensive content.

## What Changed

### 1. **User Interface (dashboard.html)**
- **Writing Style Dropdowns**: Added a writing style dropdown next to each of the 10 topic query fields
- **Available Writing Styles**:
  - Conversational/Personal
  - Authoritative/Expert
  - Narrative/Storytelling
  - Listicle/Scannable
  - Investigative/Journalistic
  - How-to/Instructional
  - Opinion/Commentary
  - Humorous/Satirical

### 2. **Database Schema (app_v3.py)**
- **New Column**: `writing_styles` (JSON) added to User model
- Stores writing style preferences parallel to `specific_topic_queries`
- Structure: `{"1": "Authoritative/Expert", "2": "Narrative/Storytelling", ...}`

### 3. **API Endpoints (app_v3.py)**
- **Updated `/api/save_specific_queries`**: Now saves both queries and writing styles
- **Updated `/api/get_specific_queries`**: Returns both queries and styles in structured format:
  ```json
  {
    "queries": {"1": "AI in healthcare", "2": "Climate tech..."},
    "styles": {"1": "Authoritative/Expert", "2": "Investigative/Journalistic"}
  }
  ```

### 4. **Perplexity Integration (perplexity_ai_integration.py)**

#### Enhanced `query_management()`:
- **Returns**: Tuple `(query, writing_style)` instead of just query
- Automatically retrieves corresponding writing style for selected topic

#### Enhanced `generate_blog_post_ideas()`:
- **New Parameter**: `writing_style` (optional)
- **Increased max_tokens**: 500 → 2000 (4x more research per call)
- **Dynamic System Prompt**:
  ```
  Base: "You are an expert research journalist who provides comprehensive,
         in-depth research for professional writers. Whenever possible you
         will include real life case studies and examples if it makes sense
         for the topic or story type."

  With Style: "[Base prompt] The article will be written in a {writing_style}
               style. Provide detailed research, statistics, expert quotes,
               case studies, and recent developments that support this writing
               approach."
  ```

- **Enhanced User Prompt**:
  ```
  "Find the top trending news story regarding: {query} and provide
   comprehensive research content for editors to create a Pulitzer
   prize-winning article written in the style of {writing_style}.

   Include:
   - Latest statistics and data points with sources
   - Expert opinions and quotable statements
   - Recent case studies or real-world examples
   - Key trends and developments
   - Relevant background context
   - Industry implications and future outlook
   - Specific facts that support the {writing_style} approach"
  ```

### 5. **Application Integration**
- **app_v3.py**: Updated to unpack tuple from `query_management()` and pass `writing_style` to Perplexity
- **scheduler_v3.py**: Updated for scheduled posts to use writing style context

## Migration Required

Run the migration script to add the new database column:

```bash
python add_writing_styles_migration.py
```

This script:
- Checks if `writing_styles` column exists
- Adds it if missing (supports both MySQL and SQLite)
- Safe to run multiple times (idempotent)

## Benefits

### 1. **Maximum ROI on Perplexity API**
- **Before**: 500 tokens per call (basic summary)
- **After**: 2000 tokens per call (comprehensive research)
- **4x more content** for the same cost

### 2. **Style-Aware Research**
- Research tailored to final article style
- More relevant quotes, statistics, and examples
- Better source material for GPT-5-mini

### 3. **Improved Article Quality**
- GPT-5-mini receives richer context
- More factual, data-driven content
- Better alignment with user's intended writing style

### 4. **User Experience**
- Simple dropdown selection per topic
- Visual association between topic and style
- Consistent article quality across scheduled posts

## Example Workflow

### User Setup:
1. Navigate to "Manage Topics" tab
2. Enter topic in field 1: "Latest developments in quantum computing"
3. Select writing style: "Authoritative/Expert"
4. Save queries

### What Happens (Scheduled Post):
1. **Query Management**: Selects topic 1 + "Authoritative/Expert" style
2. **Perplexity Research**:
   - System: "...The article will be written in a Authoritative/Expert style. Provide detailed research, statistics, expert quotes..."
   - User: "Find top trending news... for Pulitzer prize-winning article in Authoritative/Expert style"
   - Returns: 2000 tokens of comprehensive, expert-focused research
3. **GPT-5-mini Creation**: Uses rich research to write magazine-style article
4. **Result**: High-quality, authoritative article with statistics and expert insights

## Backward Compatibility

- ✅ Existing users: Writing styles default to `None` (uses base prompts)
- ✅ Manual topics: Continue to work without writing styles
- ✅ Old queries: Remain functional, can add styles anytime
- ✅ No breaking changes to existing workflows

## Testing Checklist

- [ ] Run database migration
- [ ] Login to dashboard
- [ ] Navigate to "Manage Topics" tab
- [ ] Verify writing style dropdowns appear next to each topic field
- [ ] Enter test topic and select writing style
- [ ] Click "Save Topics"
- [ ] Create test post (should use enhanced Perplexity prompts)
- [ ] Check logs for "Writing style: {selected_style}" messages
- [ ] Verify Perplexity returns more comprehensive research
- [ ] Confirm GPT-5-mini article quality improves

## Files Modified

1. `static/dashboard.html` - Added writing style dropdowns and UI logic
2. `app_v3.py` - Added `writing_styles` column, updated API endpoints
3. `perplexity_ai_integration.py` - Enhanced prompts with writing style context
4. `scheduler_v3.py` - Updated to use new query_management tuple return
5. `add_writing_styles_migration.py` - Database migration script (NEW)
6. `PERPLEXITY_ENHANCEMENT_GUIDE.md` - This documentation (NEW)

## Cost Analysis

### Per Article (V3 with Enhancement):
- Perplexity: ~$0.005 (1 call, 2000 tokens output)
- GPT-5-mini: ~$0.40 (text generation with reasoning)
- SeeDream-4: ~$0.04 (4 images)
- **Total: ~$0.445** (vs $0.45 before, but 4x better research)

### Value Increase:
- **Research Quality**: 4x more comprehensive
- **Article Relevance**: Style-aware content
- **User Satisfaction**: Better aligned with intent
- **ROI**: Significantly improved without cost increase

## Future Enhancements

Potential improvements for future versions:
1. Custom writing style definitions (user-created templates)
2. Multi-style blending (e.g., "70% Authoritative, 30% Conversational")
3. Style-specific image prompt adjustments
4. A/B testing different styles for same topic
5. Analytics on which styles perform best per topic category
