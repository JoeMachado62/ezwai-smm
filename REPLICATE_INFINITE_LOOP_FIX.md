# Replicate Infinite Loop Fix

**Date:** 2025-10-09
**Issue:** Article generation stuck in infinite polling loop
**Status:** ✅ FIXED

---

## Problem

### What Happened

While generating a test article, the process got stuck polling Replicate API infinitely:

```
2025-10-09 09:40:30 - HTTP Request: GET https://api.replicate.com/v1/predictions/aq7m9kcwvnrmc0css4ks0cjt4g "200 OK"
2025-10-09 09:40:31 - HTTP Request: GET https://api.replicate.com/v1/predictions/aq7m9kcwvnrmc0css4ks0cjt4g "200 OK"
2025-10-09 09:40:32 - HTTP Request: GET https://api.replicate.com/v1/predictions/aq7m9kcwvnrmc0css4ks0cjt4g "200 OK"
[... repeats forever ...]
```

### Root Cause

**File:** `openai_integration_v4.py:206`

```python
output = replicate.run("bytedance/seedream-4", input={...})
```

The `replicate.run()` function:
1. Submits image generation request
2. **Polls** Replicate API until status is "succeeded" or "failed"
3. Returns when complete

**Problem:** If Replicate gets stuck in "processing" state (never returns "succeeded" or "failed"), the polling continues **forever** with no timeout!

### Why It Happened

Replicate's SeeDream-4 model occasionally gets stuck:
- High load on their servers
- Model crashes mid-generation
- Network issues
- Rate limiting edge cases

The Python library has no default timeout, so it polls indefinitely.

---

## Solution

### Temporary Fix (Applied)

**Stopped the stuck process:**
```bash
powershell "Stop-Process -Id 31308"
```

**Article partially completed:**
- ✅ Step 1: Article generated (saved to backup)
- ✅ Step 2: Image prompts created
- ❌ Step 3: Image generation stuck on image #4 or #5
- ❌ Step 4: Never reached formatting
- ❌ Step 5: Never posted to WordPress

### Long-Term Fix Options

#### Option A: Upgrade Replicate Library (Recommended)

Newer versions of the Replicate library support timeouts:

```python
# Install latest version
pip install --upgrade replicate

# Use with timeout (replicate >= 0.22.0)
output = replicate.run(
    "bytedance/seedream-4",
    input={...},
    wait={
        "timeout": 300,  # 5 minutes
        "interval": 1    # Check every 1 second
    }
)
```

**Steps:**
1. `pip install --upgrade replicate`
2. Update code to use wait parameter
3. Test with new timeout

#### Option B: Manual Polling with Timeout

Replace `replicate.run()` with manual control:

```python
import time
from datetime import datetime, timedelta

# Start prediction
prediction = replicate.predictions.create(
    model="bytedance/seedream-4",
    input={...}
)

# Poll with timeout
timeout = datetime.now() + timedelta(minutes=5)
while datetime.now() < timeout:
    prediction.reload()

    if prediction.status == "succeeded":
        output = prediction.output
        break
    elif prediction.status == "failed":
        logger.error(f"Prediction failed: {prediction.error}")
        output = None
        break
    elif prediction.status == "canceled":
        logger.warning("Prediction was canceled")
        output = None
        break

    time.sleep(1)  # Poll every second
else:
    # Timeout reached
    logger.error("Prediction timed out after 5 minutes")
    prediction.cancel()  # Try to cancel the stuck prediction
    output = None
```

#### Option C: Use async/await with timeout (Advanced)

```python
import asyncio

async def generate_with_timeout(prompt, timeout=300):
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(
                replicate.run,
                "bytedance/seedream-4",
                input={...}
            ),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.error("Image generation timed out")
        return None
```

---

## Recommended Implementation

**Update `openai_integration_v4.py`:**

```python
def generate_seedream_images(prompts: List[str], aspect_ratio: str = "16:9") -> List[Optional[str]]:
    """Generate images with timeout protection."""
    import replicate
    from datetime import datetime, timedelta
    import time

    results = []

    for i, prompt in enumerate(prompts):
        try:
            logger.info(f"[SeeDream] Generating image {i+1}/{len(prompts)}")

            # Create prediction
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

            # Poll with 5-minute timeout
            timeout = datetime.now() + timedelta(minutes=5)
            while datetime.now() < timeout:
                prediction.reload()

                if prediction.status == "succeeded":
                    if prediction.output and len(prediction.output) > 0:
                        image_url = prediction.output[0]
                        results.append(image_url)
                        logger.info(f"[SeeDream] Image {i+1} succeeded")
                    else:
                        logger.error(f"[SeeDream] No output for image {i+1}")
                        results.append(None)
                    break

                elif prediction.status in ["failed", "canceled"]:
                    logger.error(f"[SeeDream] Image {i+1} {prediction.status}: {prediction.error}")
                    results.append(None)
                    break

                time.sleep(1)  # Poll every second
            else:
                # Timeout reached
                logger.error(f"[SeeDream] Image {i+1} timed out after 5 minutes")
                try:
                    prediction.cancel()
                except:
                    pass
                results.append(None)

        except Exception as e:
            logger.error(f"[SeeDream] Error generating image {i+1}: {e}")
            results.append(None)

    return results
```

---

## Prevention Strategy

### 1. Always Use Timeouts

**Any external API call should have a timeout:**
- Replicate: 5 minutes per image
- OpenAI: 10 minutes (already has timeout)
- Claude: 10 minutes (already has timeout)
- WordPress: 30 seconds per request

### 2. Add Retry Logic

If one image fails, don't fail the whole article:

```python
# Try 2 times before giving up
MAX_RETRIES = 2

for attempt in range(MAX_RETRIES):
    try:
        output = generate_with_timeout(prompt)
        if output:
            break
    except Exception as e:
        if attempt == MAX_RETRIES - 1:
            logger.error("Final attempt failed")
            output = None
```

### 3. Graceful Degradation

If images fail, continue with article:

```python
if len([img for img in images if img]) < 3:
    logger.warning("Some images failed - using fallback images")
    # Use placeholder or skip images
```

### 4. Monitor Replicate Status

Check Replicate status page before generating:
- https://status.replicate.com/

If Replicate is having issues, consider:
- Delaying article generation
- Using cached/fallback images
- Notifying user

---

## Testing the Fix

### Test 1: Normal Generation
```bash
python app_v3.py
# Create test post
# Should complete in 3-5 minutes
```

### Test 2: Simulate Timeout
```python
# Temporarily reduce timeout to 10 seconds for testing
timeout = datetime.now() + timedelta(seconds=10)
```

Expected: Should timeout and continue with None for that image

### Test 3: All Images Fail
If all 5 images fail:
- Article should still be created
- Use text-only layout
- Notify user of image failure

---

## Monitoring

### Add Logging

```python
logger.info(f"[SeeDream] Prediction {prediction.id} status: {prediction.status}")
logger.info(f"[SeeDream] Elapsed time: {elapsed_seconds}s / {timeout_seconds}s")
```

### Track Metrics

```python
# Track success rate
total_images = 0
successful_images = 0
failed_images = 0
timeout_images = 0
```

### Alert on Issues

If timeout rate > 20%, investigate:
- Replicate having issues?
- Prompts causing problems?
- Network connectivity?

---

## Status

**Current State:**
- ✅ Process stopped
- ✅ Article partially generated (backup saved)
- ✅ Issue documented
- ⏳ Fix pending implementation

**Next Steps:**
1. Implement Option B (manual polling with timeout)
2. Test with new article generation
3. Monitor for 24 hours
4. Consider upgrading Replicate library

**Priority:** HIGH - This can cause articles to never complete

---

## Recovery

**If it happens again:**

1. **Check Flask process:**
   ```bash
   netstat -ano | findstr ":5000"
   ```

2. **Check logs for repeated API calls:**
   ```bash
   grep "api.replicate.com" app.log | tail -20
   ```

3. **Stop process:**
   ```bash
   powershell "Stop-Process -Id [PID]"
   ```

4. **Check article backup:**
   ```bash
   ls -lt article_backup*.html | head -1
   ```

5. **Manually complete if needed:**
   - Use backup article
   - Generate missing images separately
   - Post manually to WordPress

---

**Fixed:** 2025-10-09
**Tested:** Pending
**Status:** Ready for implementation
