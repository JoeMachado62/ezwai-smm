# Article Backup & Recovery System - Proposal

## Current Situation

### What Exists Today
The V4 pipeline (`openai_integration_v4.py`) already has basic backup functions:
- `_save_raw_article()` - Saves HTML after Step 1 (GPT-5 generation)
- `_save_formatted_article()` - Saves final HTML after formatting

**However, there are critical gaps:**

### What Went Wrong (Recent Incident)
1. ✅ Article HTML was backed up at Step 1 (`article_backup_user6_after_step1_*.html`)
2. ❌ **Image URLs NOT saved** - Had to manually provide them for recovery
3. ❌ **Images stored as Replicate URLs** - These expire/change between runs
4. ❌ **No structured recovery tool** - Had to create 3 different ad-hoc scripts
5. ❌ **WordPress upload failure was silent** - Article lost without clear notification

## Failure Points Analysis

### Pipeline Flow & Failure Points
```
STEP 1: GPT-5 Article Generation
├─ Output: article_data (title, html, components, executive_summary)
├─ ✅ BACKUP: _save_raw_article() saves HTML
└─ ❌ RISK: If process dies here, we lose article

STEP 2: Image Prompt Generation
├─ Output: 4 photographic prompts
└─ ❌ RISK: Prompts not backed up

STEP 3: SeeDream-4 Image Generation (4 images via Replicate)
├─ Output: 4 Replicate URLs (https://replicate.delivery/...)
├─ ❌ RISK: URLs expire in ~60 minutes
├─ ❌ RISK: URLs not saved to disk
└─ ❌ RISK: If Replicate fails/times out, we lose work

STEP 4: Claude/Template Formatting
├─ Output: final_html with embedded images
├─ ✅ BACKUP: _save_formatted_article() saves HTML
└─ ❌ RISK: Images are Replicate URLs (not base64), so HTML is incomplete

STEP 5: WordPress Upload (each image + article)
├─ Uploads 4 images to WordPress media library
├─ Creates draft post with WordPress-hosted images
├─ ❌ RISK: If ANY upload fails, entire article lost
├─ ❌ RISK: No retry mechanism
└─ ❌ RISK: User not notified of specific failure point
```

### Why Recovery Was Difficult
1. **No image backup** - Replicate URLs had to be manually provided
2. **URLs changed between runs** - First set of URLs were wrong/expired
3. **No metadata file** - No JSON/manifest tracking images, prompts, timestamps
4. **Multiple recovery scripts** - Had to create 3 different scripts to try different approaches
5. **Base64 exceeds Claude token limit** - 1.1MB hero image = 1.5M chars = 208k tokens > 200k limit

## Proposed Solution: Comprehensive Backup & Recovery System

### Design Principles
1. **Backup Everything, Immediately** - Save artifacts as soon as they're created
2. **Persistent Storage** - Convert Replicate URLs to base64/local files ASAP
3. **Structured Metadata** - JSON manifest tracking all artifacts
4. **Automatic Recovery** - Single unified tool, no ad-hoc scripts
5. **Graceful Degradation** - If one formatter fails, try fallback
6. **User Notification** - Clear errors with recovery instructions

---

## Implementation Plan

### 1. Enhanced Backup System

#### A. Backup Directory Structure
```
backups/
├── user_{id}/
│   ├── article_{timestamp}/
│   │   ├── manifest.json           # Master metadata file
│   │   ├── 01_raw_article.html     # After Step 1 (GPT-5)
│   │   ├── 02_prompts.txt          # Image prompts
│   │   ├── 03_hero.jpg             # Hero image (downloaded)
│   │   ├── 03_hero_base64.txt      # Base64 encoded hero
│   │   ├── 03_section_1.jpg        # Section 1 image
│   │   ├── 03_section_1_base64.txt # Base64 encoded section 1
│   │   ├── 03_section_2.jpg        # Section 2 image
│   │   ├── 03_section_2_base64.txt # Base64 encoded section 2
│   │   ├── 03_section_3.jpg        # Section 3 image
│   │   ├── 03_section_3_base64.txt # Base64 encoded section 3
│   │   ├── 04_formatted.html       # After Claude/template formatting
│   │   └── 05_final.html           # After WordPress upload (if successful)
```

#### B. manifest.json Structure
```json
{
  "user_id": 6,
  "timestamp": "20251011_214423",
  "article": {
    "title": "Tariffs and AI Are Rewriting the Rules...",
    "word_count": 2143,
    "components": ["pull_quote", "stat_highlight", "case_study", "sidebar"]
  },
  "pipeline_stages": {
    "step1_article_generation": {
      "status": "completed",
      "timestamp": "20251011_214423",
      "file": "01_raw_article.html",
      "model": "gpt-5-mini",
      "reasoning_tokens": 287
    },
    "step2_image_prompts": {
      "status": "completed",
      "timestamp": "20251011_214424",
      "file": "02_prompts.txt",
      "prompts": [
        "Professional product photography of modern car dashboard...",
        "Documentary-style photograph of automotive manufacturing...",
        "Business editorial photograph of car dealership...",
        "Corporate photography of automotive executives..."
      ]
    },
    "step3_image_generation": {
      "status": "completed",
      "timestamp": "20251011_214445",
      "hero": {
        "replicate_url": "https://replicate.delivery/xezq/MWyv...",
        "local_file": "03_hero.jpg",
        "base64_file": "03_hero_base64.txt",
        "size_kb": 1118.1,
        "aspect_ratio": "16:9"
      },
      "sections": [
        {
          "index": 1,
          "replicate_url": "https://replicate.delivery/xezq/cbNP...",
          "local_file": "03_section_1.jpg",
          "base64_file": "03_section_1_base64.txt",
          "size_kb": 1205.3,
          "aspect_ratio": "21:9"
        },
        // ... sections 2-3
      ]
    },
    "step4_formatting": {
      "status": "completed",
      "timestamp": "20251011_214448",
      "formatter": "claude_ai",  // or "template_fallback"
      "file": "04_formatted.html",
      "brand_colors": {"primary": "#6B5DD3", "accent": "#FF6B4A"}
    },
    "step5_wordpress_upload": {
      "status": "failed",  // ← CRITICAL: Record failure point
      "timestamp": "20251011_214500",
      "error": "WP upload: missing JWT token",
      "failed_at": "hero_image_upload",
      "uploaded_images": [],
      "recovery_instructions": "Run: python recovery_tool.py --manifest backups/user_6/article_20251011_214423/manifest.json"
    }
  },
  "recovery_attempts": []  // Track recovery attempts
}
```

#### C. New Backup Module (`article_backup_manager.py`)
```python
class ArticleBackupManager:
    """
    Centralized backup management for article generation pipeline.

    Usage:
        backup = ArticleBackupManager(user_id=6)
        backup.save_article(article_data, stage="step1_article_generation")
        backup.save_image_prompts(prompts)
        backup.save_replicate_images(hero_url, section_urls)  # Downloads + base64
        backup.save_formatted_article(html)
        backup.mark_wordpress_upload_failed(error_msg)
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = f"backups/user_{user_id}/article_{self.timestamp}"
        self.manifest_path = os.path.join(self.backup_dir, "manifest.json")
        self._init_backup_directory()
        self._init_manifest()

    def save_replicate_images(self, hero_url: str, section_urls: List[str]):
        """
        CRITICAL: Download Replicate images IMMEDIATELY and save as:
        1. Local JPEG files (for viewing/debugging)
        2. Base64 text files (for recovery without re-download)

        This prevents loss when Replicate URLs expire.
        """
        pass

    def mark_stage_completed(self, stage: str, metadata: Dict):
        """Update manifest with stage completion."""
        pass

    def mark_stage_failed(self, stage: str, error: str):
        """Mark stage as failed with error details and recovery instructions."""
        pass
```

### 2. Unified Recovery Tool

Create **single recovery tool** to replace all ad-hoc scripts:

#### `article_recovery_tool.py`
```python
"""
Universal Article Recovery Tool

Recovers articles from backup manifests at any pipeline stage.

Usage:
    # Auto-discover latest failed article for user
    python article_recovery_tool.py --user-id 6

    # Recover specific article by manifest
    python article_recovery_tool.py --manifest backups/user_6/article_*/manifest.json

    # List all recoverable articles
    python article_recovery_tool.py --list-all

    # Force specific formatter
    python article_recovery_tool.py --user-id 6 --formatter template
"""

class ArticleRecoveryTool:
    def __init__(self, manifest_path: str):
        self.manifest = self._load_manifest(manifest_path)
        self.backup_dir = os.path.dirname(manifest_path)

    def recover(self, formatter: str = "auto"):
        """
        Recover article from any stage.

        Recovery paths:
        1. If WordPress upload failed but article formatted → Upload to WP
        2. If formatting failed but images exist → Re-format and upload
        3. If images missing but prompts exist → Re-generate images, format, upload
        4. If complete failure → Start from raw article HTML
        """
        stage = self.manifest["pipeline_stages"]

        if stage["step5_wordpress_upload"]["status"] == "failed":
            return self._recover_from_wordpress_failure()
        elif stage["step4_formatting"]["status"] == "failed":
            return self._recover_from_formatting_failure()
        elif stage["step3_image_generation"]["status"] == "failed":
            return self._recover_from_image_failure()
        else:
            return self._full_recovery_from_raw_article()

    def _recover_from_wordpress_failure(self):
        """
        Article is fully formatted, just need to upload to WordPress.
        Load formatted HTML and images from backup, retry upload.
        """
        pass

    def _load_base64_images(self) -> Dict[str, str]:
        """Load pre-converted base64 images from backup."""
        hero_base64 = open(f"{self.backup_dir}/03_hero_base64.txt").read()
        section_base64 = []
        for i in range(1, 4):
            path = f"{self.backup_dir}/03_section_{i}_base64.txt"
            if os.path.exists(path):
                section_base64.append(open(path).read())
        return {"hero": hero_base64, "sections": section_base64}
```

### 3. Integration Changes to V4 Pipeline

#### Modify `openai_integration_v4.py`:
```python
from article_backup_manager import ArticleBackupManager

def create_blog_post_with_images_v4(
    blog_post_idea: str,
    user_id: int,
    user_system_prompt: str = "",
    writing_style: str = "professional"
) -> Tuple[Optional[Dict], Optional[str]]:
    """Enhanced with comprehensive backup at every stage."""

    # Initialize backup manager
    backup = ArticleBackupManager(user_id=user_id)

    try:
        # STEP 1: Generate article
        article_data = generate_clean_article(blog_post_idea, user_system_prompt, writing_style)
        backup.save_article(article_data, stage="step1_article_generation")
        backup.mark_stage_completed("step1_article_generation", {...})

        # STEP 2: Generate image prompts
        prompts = generate_contextual_image_prompts(article_data, user_id)
        backup.save_image_prompts(prompts)
        backup.mark_stage_completed("step2_image_prompts", {...})

        # STEP 3: Generate images
        image_urls = generate_images_with_seedream(prompts, user_id, ...)
        # ⚠️ CRITICAL: Download and save images IMMEDIATELY
        backup.save_replicate_images(hero_url=image_urls[0], section_urls=image_urls[1:])
        backup.mark_stage_completed("step3_image_generation", {...})

        # STEP 4: Format article
        try:
            formatted_html = format_article_with_claude(...)
            backup.save_formatted_article(formatted_html, formatter="claude_ai")
            backup.mark_stage_completed("step4_formatting", {...})
        except Exception as e:
            logger.warning(f"Claude formatter failed: {e}, trying template fallback")
            formatted_html = apply_magazine_styling(...)
            backup.save_formatted_article(formatted_html, formatter="template_fallback")
            backup.mark_stage_completed("step4_formatting", {...})

        # STEP 5: Upload to WordPress
        try:
            wp_result = upload_to_wordpress(...)
            backup.mark_stage_completed("step5_wordpress_upload", {...})
            return wp_result, None
        except Exception as e:
            backup.mark_stage_failed("step5_wordpress_upload", str(e))

            # Generate recovery instructions
            recovery_cmd = f"python article_recovery_tool.py --manifest {backup.manifest_path}"
            error_msg = f"WordPress upload failed: {e}\n\nArticle backed up. Recover with:\n{recovery_cmd}"

            return None, error_msg

    except Exception as e:
        backup.mark_stage_failed("unknown", str(e))
        return None, str(e)
```

### 4. Image Storage Strategy

#### Problem: Base64 vs URLs
- **Base64**: Self-contained, never expires, but HUGE (1.1MB image → 1.5MB text → 208k tokens)
- **URLs**: Small, but expire in 60 minutes

#### Solution: Hybrid Approach
1. **During generation**: Use Replicate URLs (fast, no token limit)
2. **Immediate backup**: Download as JPEG + save base64 text file
3. **For Claude formatter**: Use URLs if < 60min old, else use local JPEG files
4. **For recovery**: Load pre-converted base64 from backup (no re-download needed)
5. **For WordPress**: Always upload local JPEG files (not URLs)

### 5. User-Facing Improvements

#### A. Clear Error Messages
```
❌ Article generation failed at: WordPress Image Upload

Your article has been automatically backed up and can be recovered.

📁 Backup location: backups/user_6/article_20251011_214423/
🔧 Recovery command: python article_recovery_tool.py --user-id 6

What was saved:
  ✅ Article content (2,143 words)
  ✅ 4 AI-generated images (downloaded)
  ✅ Formatted magazine layout
  ❌ WordPress upload (failed)

You can retry the upload or contact support with backup ID: user6_20251011_214423
```

#### B. Dashboard Integration
- Add "Failed Articles" section to dashboard
- Show recoverable articles with one-click recovery button
- Display backup manifests in user-friendly format

### 6. Maintenance & Cleanup

#### Auto-cleanup Policy
```python
# Clean up old backups to save disk space
# Keep: Last 7 days OR any failed articles (indefinitely)
# Delete: Successful articles older than 7 days

def cleanup_old_backups(retention_days=7):
    """
    Delete old successful article backups.
    Never delete failed articles (user may want to recover).
    """
    pass
```

---

## Migration Path

### Phase 1: Core Backup System (Week 1)
1. ✅ Create `article_backup_manager.py`
2. ✅ Create `backups/` directory structure
3. ✅ Implement manifest.json generation
4. ✅ Integrate into V4 pipeline
5. ✅ Test backup creation at all stages

### Phase 2: Recovery Tool (Week 2)
1. ✅ Create `article_recovery_tool.py`
2. ✅ Implement recovery from each failure point
3. ✅ Add CLI interface with --list-all, --user-id, --manifest flags
4. ✅ Test recovery scenarios
5. ✅ Delete ad-hoc recovery scripts (recover_article_*.py)

### Phase 3: User Experience (Week 3)
1. ✅ Improve error messages with recovery instructions
2. ✅ Add "Failed Articles" to dashboard
3. ✅ One-click recovery button
4. ✅ Email notifications for failed articles with recovery link

### Phase 4: Optimization (Week 4)
1. ✅ Implement auto-cleanup of old backups
2. ✅ Add backup/recovery metrics to logs
3. ✅ Performance testing (backup overhead < 5 seconds)
4. ✅ Documentation in CLAUDE.md

---

## Cost & Performance Analysis

### Storage Costs
- **Per article backup**: ~5-8 MB (4 images + HTML + metadata)
- **10 articles/day**: 50-80 MB/day
- **Monthly**: ~1.5-2.5 GB/month
- **Yearly**: ~18-30 GB/year

**Recommendation**: Store on local disk, add S3 backup option for production.

### Performance Impact
- **Backup operations**: ~3-5 seconds total per article
  - Download 4 images: 2-3 seconds
  - Base64 encode: 0.5 seconds
  - Write files: 0.5 seconds
  - Update manifest: 0.1 seconds

**Impact**: ~5-10% increase in total generation time (acceptable)

### Recovery Time
- **From WordPress failure**: ~30 seconds (just upload)
- **From formatting failure**: ~1 minute (re-format + upload)
- **From image failure**: ~3-4 minutes (re-generate images + format + upload)
- **Full recovery**: ~4-5 minutes (re-run entire pipeline)

---

## Key Benefits

### For Users
1. ✅ **Never lose work** - Every article automatically backed up
2. ✅ **Fast recovery** - One command to recover any failed article
3. ✅ **Transparent failures** - Clear error messages with recovery instructions
4. ✅ **Peace of mind** - Can retry/recover anytime

### For Developers
1. ✅ **No more ad-hoc scripts** - One unified recovery tool
2. ✅ **Easier debugging** - Complete manifest of what succeeded/failed
3. ✅ **Better testing** - Can simulate failures and test recovery
4. ✅ **Audit trail** - Know exactly what happened in each pipeline run

### For System Reliability
1. ✅ **Fault tolerance** - Graceful degradation at each stage
2. ✅ **Reduced manual intervention** - Automatic recovery where possible
3. ✅ **Better monitoring** - Track failure rates by stage
4. ✅ **Historical data** - Learn which stages fail most often

---

## Questions for Discussion

1. **Backup retention**: Keep failed articles indefinitely? Or 30-day limit?
2. **Automatic recovery**: Should system auto-retry failed uploads? Or require manual trigger?
3. **Storage location**: Local disk only? Or also backup to S3/cloud?
4. **Dashboard integration**: Show all backups? Or only failed articles?
5. **Notification strategy**: Email on every failure? Or daily digest?
6. **V3 migration**: Apply same backup system to `openai_integration_v3.py`? (scheduler)

---

## Recommendation

**Implement Phase 1 & 2 immediately** (Core Backup + Recovery Tool)

This solves the critical problem: Never losing work again. The recent incident wouldn't have required 3 different ad-hoc scripts - just one command:

```bash
python article_recovery_tool.py --user-id 6
```

Phases 3 & 4 (UX improvements, optimization) can follow once core system is proven.

**Estimated implementation time**: 2-3 days for Phase 1+2 (fully functional backup/recovery)
