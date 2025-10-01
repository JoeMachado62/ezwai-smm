# EZWAI SMM V3.0 - Legacy Code Audit

## Executive Summary

Complete codebase audit to identify safe-to-remove legacy code. Analysis shows **9 legacy files** and **3 legacy scripts** that are NOT used by V3 infrastructure.

---

## Files Analysis

### ✅ CURRENT V3 FILES (KEEP)
- `app_v3.py` - Main V3 application with GPT-5-mini + SeeDream-4
- `openai_integration_v3.py` - V3 content generation with Responses API
- `scheduler_v3.py` - V3 scheduler using V3 modules
- `start_v3.sh` / `start_v3.bat` - V3 startup scripts
- `start_v3_production.sh` - Gunicorn production server
- `start_v3_background.bat` - Windows auto-restart
- `stop_v3.sh` / `stop_v3.bat` - V3 stop scripts
- `run_scheduler_v3.sh` - V3 cron scheduler

### 🟡 SHARED MODULES (KEEP - Used by V3)
- `config.py` - Database configuration (used by all versions)
- `email_notification.py` - SendGrid email module (used by all versions)
- `wordpress_integration.py` - WordPress JWT API (used by all versions)
- `perplexity_ai_integration.py` - Research module (used by all versions)

### ❌ LEGACY V1 FILES (SAFE TO REMOVE)

#### 1. **app.py** - Original Flask Application (V1)
**Status:** OBSOLETE - Replaced by app_v3.py
**Used By:**
- `scheduler.py` (legacy - replaced by scheduler_v3.py)
- `restart_app.sh` (legacy - replaced by start_v3.sh)

**Import Analysis:**
```python
# app.py imports from:
from openai_integration import create_blog_post_with_image  # V1 function
```

**Safe to Remove:** ✅ YES - After removing scheduler.py and restart_app.sh

---

#### 2. **openai_integration.py** - V1 OpenAI Integration
**Status:** OBSOLETE - Replaced by openai_integration_v3.py
**Used By:**
- `app.py` (legacy)
- `flask_app.py` (legacy)
- `app_progress_bar.py` (legacy)
- `scheduler.py` (legacy)
- `Wordpress_post_test.py` (test file)

**Features:**
- Uses deprecated OpenAI 0.27.x API
- Single image generation with DALL-E 3
- Basic article structure (300-500 words)

**Safe to Remove:** ✅ YES - After removing dependent files

---

#### 3. **flask_app.py** - Extended V1 Application
**Status:** OBSOLETE - Features merged into app_v3.py
**Used By:** NONE (standalone alternative to app.py)

**Features:**
- Blog post templates (STANDARD, LISTICLE, HOW_TO, REVIEW)
- Progress tracking with Server-Sent Events
- Uses V1 openai_integration.py

**Safe to Remove:** ✅ YES - No dependencies

---

#### 4. **app_progress_bar.py** - Test/Demo File
**Status:** OBSOLETE - Progress tracking in app_v3.py
**Used By:** NONE (appears to be test/demo)

**Safe to Remove:** ✅ YES - No dependencies

---

#### 5. **scheduler.py** - V1 Scheduler
**Status:** OBSOLETE - Replaced by scheduler_v3.py
**Used By:**
- `run_scheduler.sh` (legacy)
- `scheduler-cronjob.sh` (legacy)

**Import Analysis:**
```python
from app import app, db, User, CompletedJob  # V1
from openai_integration import create_blog_post_with_image  # V1
```

**Safe to Remove:** ✅ YES - After updating cron jobs to use scheduler_v3.py

---

#### 6. **Wordpress_post_test.py** - Test Script
**Status:** TEST FILE - May still be useful for debugging
**Used By:** NONE (manual test script)

**Recommendation:** ⚠️ UPDATE to use V3 modules instead of removing:
```python
# Change from:
from openai_integration import create_blog_post_with_image
# To:
from openai_integration_v3 import create_blog_post_with_images_v3
```

**Safe to Remove:** 🟡 OPTIONAL - Can update instead

---

### ❌ LEGACY V2 FILES (SAFE TO REMOVE)

#### 7. **app_v2.py** - Mid-Upgrade Version
**Status:** OBSOLETE - Replaced by app_v3.py
**Used By:** NONE (superseded by V3)

**Features:**
- OpenAI v1.x Chat Completions (not Responses API)
- Flux model (not SeeDream-4)
- 1500+ word articles (retained in V3)
- Magazine HTML structure (enhanced in V3)

**Safe to Remove:** ✅ YES - No dependencies

---

#### 8. **openai_integration_v2.py** - V2 OpenAI Integration
**Status:** OBSOLETE - Replaced by openai_integration_v3.py
**Used By:**
- `app_v2.py` only

**Key Differences from V3:**
- Uses Chat Completions API (not Responses API)
- Uses gpt-4o-mini (not gpt-5-mini)
- No reasoning parameter
- Uses Flux-dev (not SeeDream-4)
- Basic prompt generation (not AI-powered photographic prompts)

**Safe to Remove:** ✅ YES - No dependencies

---

### ❌ LEGACY SHELL SCRIPTS (SAFE TO REMOVE)

#### 9. **restart_app.sh** - V1 Restart Script
**Status:** OBSOLETE - Replaced by start_v3.sh
**Used By:** NONE (superseded by V3)

**Issues:**
- Hardcoded production path: `/var/www/vhosts/funnelmngr.com/httpdocs/Python`
- References legacy `app.py`
- No dependency checking
- No MySQL service verification

**Safe to Remove:** ✅ YES - V3 scripts are comprehensive

---

#### 10. **run_scheduler.sh** - V1 Scheduler Runner
**Status:** OBSOLETE - Replaced by run_scheduler_v3.sh
**Used By:** Potentially active cron jobs ⚠️

**Issues:**
- Hardcoded production path
- Runs legacy `scheduler.py`
- Log file: `/tmp/scheduler_debug.log`

**Safe to Remove:** ⚠️ YES - But check crontab first:
```bash
crontab -l | grep scheduler
```

---

#### 11. **scheduler-cronjob.sh** - V1 Cron Scheduler
**Status:** DUPLICATE of run_scheduler.sh
**Used By:** Potentially active cron jobs ⚠️

**Note:** Identical to run_scheduler.sh

**Safe to Remove:** ⚠️ YES - But check crontab first

---

## Dependency Graph

```
V3 ACTIVE SYSTEM:
app_v3.py ──┐
            ├──> openai_integration_v3.py ──> config.py
            │                                 perplexity_ai_integration.py
            │                                 wordpress_integration.py
            │                                 email_notification.py
            │
scheduler_v3.py ──> (same dependencies)

LEGACY V1 SYSTEM (OBSOLETE):
app.py ──┐
         ├──> openai_integration.py ──> (shared modules)
         │
scheduler.py ──> app.py + openai_integration.py
restart_app.sh ──> app.py
run_scheduler.sh ──> scheduler.py
scheduler-cronjob.sh ──> scheduler.py

LEGACY V2 SYSTEM (OBSOLETE):
app_v2.py ──> openai_integration_v2.py ──> (shared modules)

STANDALONE LEGACY:
flask_app.py ──> openai_integration.py
app_progress_bar.py ──> openai_integration.py
Wordpress_post_test.py ──> openai_integration.py
```

---

## Removal Plan

### Phase 1: Safe Immediate Removals (No Dependencies)
```bash
# V2 files (fully superseded)
rm app_v2.py
rm openai_integration_v2.py

# Standalone V1 files
rm flask_app.py
rm app_progress_bar.py
```

### Phase 2: Check and Update Cron Jobs
```bash
# Check for active cron jobs
crontab -l

# If scheduler jobs exist, update them:
# OLD: */5 * * * * /path/to/run_scheduler.sh
# NEW: */5 * * * * /path/to/run_scheduler_v3.sh

# Or on Windows Task Scheduler:
# Change: python scheduler.py
# To:     python scheduler_v3.py
```

### Phase 3: Remove V1 System Files
```bash
# After confirming no active cron jobs use V1
rm scheduler.py
rm run_scheduler.sh
rm scheduler-cronjob.sh
rm restart_app.sh
```

### Phase 4: Remove V1 Core Application
```bash
# Final removal after confirming V3 is stable
rm app.py
rm openai_integration.py
```

### Phase 5: Update Test File (Optional)
Update `Wordpress_post_test.py` to use V3 modules:
```python
# Change line 5 from:
from openai_integration import create_blog_post_with_image

# To:
from openai_integration_v3 import create_blog_post_with_images_v3
```

---

## Pre-Removal Checklist

Before removing any files, verify:

- [ ] V3 application is running successfully (`app_v3.py`)
- [ ] V3 scheduler is functional (`scheduler_v3.py`)
- [ ] No active cron jobs reference legacy scripts
- [ ] Windows Task Scheduler doesn't reference legacy files
- [ ] Production server uses V3 scripts
- [ ] All environment variables are properly configured
- [ ] Database migrations are complete
- [ ] Users can create test posts successfully

---

## Files to Keep (Final V3 System)

**Python Application:**
- `app_v3.py` - Main application
- `openai_integration_v3.py` - GPT-5-mini + SeeDream-4
- `scheduler_v3.py` - V3 scheduler
- `config.py` - Database config
- `email_notification.py` - Email module
- `wordpress_integration.py` - WordPress API
- `perplexity_ai_integration.py` - Research module

**Windows Scripts:**
- `start_v3.bat` - Full startup with checks
- `start_v3_background.bat` - Auto-restart mode
- `stop_v3.bat` - Graceful shutdown

**Linux Scripts:**
- `start_v3.sh` - Full startup with checks
- `start_v3_production.sh` - Gunicorn production
- `stop_v3.sh` - Graceful shutdown
- `run_scheduler_v3.sh` - Cron scheduler

**Documentation:**
- `CLAUDE.md` - Architecture documentation
- `V3_UPGRADE_GUIDE.md` - V3 feature guide
- `V3_ANSWERS.md` - Implementation details
- `LEGACY_CODE_AUDIT.md` - This file

**Configuration:**
- `.env` - System-wide configuration
- `.env.user_{id}` - Per-user configurations
- `requirements.txt` - Python dependencies

---

## Estimated Space Savings

**Python Files:**
- app.py: ~15 KB
- openai_integration.py: ~12 KB
- flask_app.py: ~18 KB
- app_progress_bar.py: ~8 KB
- scheduler.py: ~10 KB
- app_v2.py: ~16 KB
- openai_integration_v2.py: ~20 KB

**Shell Scripts:**
- restart_app.sh: ~1 KB
- run_scheduler.sh: ~2 KB
- scheduler-cronjob.sh: ~2 KB

**Total:** ~104 KB of legacy code

---

## Risk Assessment

**LOW RISK** - Safe to remove after verification:
- app_v2.py, openai_integration_v2.py (V2 fully superseded)
- flask_app.py, app_progress_bar.py (standalone, no dependencies)

**MEDIUM RISK** - Check cron/Task Scheduler first:
- scheduler.py, run_scheduler.sh, scheduler-cronjob.sh

**HIGH RISK** - Remove last after V3 stability confirmed:
- app.py, openai_integration.py (V1 core system)

---

## Recommendation

**PROCEED WITH REMOVAL** following the phased approach:
1. Remove V2 files immediately ✅
2. Check and update scheduled tasks ⚠️
3. Remove V1 scheduler files after verification ✅
4. Remove V1 core after 1 week of stable V3 operation ✅

This eliminates code bloat while maintaining system stability.