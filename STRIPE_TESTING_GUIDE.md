# Stripe Payment Testing Guide - Complete Setup

**For:** Local development and testing before deployment
**System:** EZWAI SMM Credit System

---

## 📋 What is a Stripe Webhook and Why Do You Need It?

### What Is It?

A **webhook** is like a phone call from Stripe to your application. When something important happens (like a payment succeeding), Stripe "calls" your server with the details.

### Why You Need It

**Your credit system works like this:**

1. **User clicks "Buy Credits"** → Opens Stripe checkout page
2. **User enters payment info** → Stripe processes payment
3. **✅ Payment succeeds** → Stripe sends webhook to your server
4. **Your server receives webhook** → Adds credits to user's account
5. **User gets credits** → Can create articles

**Without webhooks:** You'd never know the payment succeeded, so credits wouldn't be added!

### What's the Webhook Secret?

The **webhook secret** is like a password that proves the webhook really came from Stripe (not a hacker pretending to be Stripe).

---

## 🎯 Your Current Setup

### Webhook Endpoint in Your Code

**File:** [app_v3.py:1056](app_v3.py#L1056)

```python
@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""

    # 1. Get the webhook secret
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    # 2. Verify the webhook is real
    event = stripe.Webhook.construct_event(
        payload, sig_header, webhook_secret
    )

    # 3. Handle different events
    if event_type == 'checkout.session.completed':
        # Payment successful! Add credits
        handle_checkout_completed(session)
```

### Events Your App Handles

```python
✅ checkout.session.completed  # User completed payment
✅ payment_intent.succeeded     # Payment went through
❌ payment_intent.payment_failed # Payment failed
✅ setup_intent.succeeded       # Payment method saved
```

---

## 🚀 Option 1: Stripe CLI (Recommended for Local Testing)

This is the **easiest way** to test webhooks on localhost!

### Step 1: Install Stripe CLI

**Windows (Download):**
1. Go to: https://github.com/stripe/stripe-cli/releases/latest
2. Download: `stripe_X.X.X_windows_x86_64.zip`
3. Extract to a folder (e.g., `C:\stripe\`)
4. Add to PATH or navigate to folder in terminal

**Windows (Scoop):**
```bash
scoop bucket add stripe https://github.com/stripe/scoop-stripe-cli.git
scoop install stripe
```

**Verify Installation:**
```bash
stripe --version
# Should show: stripe version X.X.X
```

### Step 2: Login to Stripe

```bash
stripe login
```

**What happens:**
1. Opens browser
2. Shows "Stripe CLI wants to access your account"
3. Click "Allow access"
4. Terminal shows "✓ Done! The Stripe CLI is configured"

### Step 3: Forward Webhooks to Localhost

**Start your Flask app first:**
```bash
python app_v3.py
# App running on http://localhost:5000
```

**In another terminal, forward webhooks:**
```bash
stripe listen --forward-to localhost:5000/webhook/stripe
```

**Output:**
```
> Ready! You are using Stripe API Version [2024-XX-XX]
> Your webhook signing secret is whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**📋 COPY THE SECRET!** It looks like: `whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 4: Update .env File

```bash
# Edit .env
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Restart your Flask app** to load the new secret.

### Step 5: Test It!

**Keep both terminals running:**
- Terminal 1: `python app_v3.py` (Flask app)
- Terminal 2: `stripe listen --forward-to localhost:5000/webhook/stripe`

**Trigger a test event:**
```bash
# In a THIRD terminal
stripe trigger checkout.session.completed
```

**You'll see:**
```
Terminal 2 (Stripe CLI):
✓ [200] POST http://localhost:5000/webhook/stripe

Terminal 1 (Flask app):
[Stripe] Received event: checkout.session.completed
[Stripe] Added $10.00 credits to user 1
```

✅ **It works!**

---

## 🌐 Option 2: ngrok (Public Tunnel)

Use this if you want to test with the **real Stripe dashboard** or share with others.

### Step 1: Install ngrok

**Download:**
1. Go to: https://ngrok.com/download
2. Sign up for free account
3. Download ngrok for Windows
4. Extract to folder

**Setup:**
```bash
# Get your auth token from: https://dashboard.ngrok.com/get-started/your-authtoken
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

### Step 2: Start Tunnel

**Start Flask app:**
```bash
python app_v3.py
```

**Start ngrok:**
```bash
ngrok http 5000
```

**Output:**
```
Forwarding   https://abc123.ngrok-free.app -> http://localhost:5000
```

**📋 COPY THE URL!** It looks like: `https://abc123.ngrok-free.app`

### Step 3: Configure Stripe Dashboard

1. Go to: https://dashboard.stripe.com/test/webhooks
2. Click "**Add endpoint**"
3. **Endpoint URL:** `https://abc123.ngrok-free.app/webhook/stripe`
4. **Events to send:**
   - `checkout.session.completed`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `setup_intent.succeeded`
5. Click "**Add endpoint**"

### Step 4: Get Webhook Secret

**After creating endpoint:**
1. Click on the endpoint you just created
2. Click "**Reveal**" under "Signing secret"
3. **📋 COPY THE SECRET!** Looks like: `whsec_xxxxxx...`

### Step 5: Update .env

```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Restart Flask app** to load the secret.

---

## 🧪 Testing the Complete Payment Flow

### Setup (One Time)

1. **Switch to Test Mode:**
   - Stripe Dashboard → Toggle "Test mode" (top right)
   - Your keys already have `sk_live_` - get test keys!

2. **Get Test API Keys:**
   ```
   Go to: https://dashboard.stripe.com/test/apikeys

   Publishable key: pk_test_xxxxxx
   Secret key: sk_test_xxxxxx
   ```

3. **Update .env with TEST keys:**
   ```bash
   # Use TEST keys for development
   STRIPE_SECRET_KEY=sk_test_51QuaBV...
   STRIPE_PUBLISHABLE_KEY=pk_test_51QuaBV...
   STRIPE_WEBHOOK_SECRET=whsec_xxxxx  # From Stripe CLI or Dashboard
   ```

4. **Restart everything:**
   ```bash
   # Terminal 1: Flask app
   python app_v3.py

   # Terminal 2: Stripe CLI
   stripe listen --forward-to localhost:5000/webhook/stripe
   ```

### Test Flow

**Step 1: Login to Your App**
```
http://localhost:5000
Login with your test user
```

**Step 2: Check Current Credits**
```
Dashboard → Credits section
Note your current balance: e.g., $5.00
```

**Step 3: Buy Credits**
```
Click "Buy Credits" or "Add Credits"
Select amount: $10
Click "Proceed to Payment"
```

**Step 4: Complete Payment (Test Card)**
```
Card number: 4242 4242 4242 4242
Expiry: 12/34 (any future date)
CVC: 123
ZIP: 12345
```

**Step 5: Watch the Logs**

**Terminal 2 (Stripe CLI):**
```
webhook_id=evt_xxxxx [200] POST http://localhost:5000/webhook/stripe
checkout.session.completed
```

**Terminal 1 (Flask):**
```
[Stripe] Received event: checkout.session.completed
[Stripe] Added $10.00 credits to user 1
[Email] Sent confirmation to user@example.com
```

**Step 6: Verify Credits Added**
```
Refresh dashboard
New balance should be: $15.00 ($5 + $10)
```

✅ **Success!** Payment system is working!

---

## 🎴 Stripe Test Cards

### Success Cards
```
4242 4242 4242 4242  # Visa - Always succeeds
4000 0566 5566 5556  # Visa (debit) - Always succeeds
5555 5555 5555 4444  # Mastercard - Always succeeds
```

### Failure Cards
```
4000 0000 0000 0002  # Declined
4000 0000 0000 9995  # Insufficient funds
4000 0000 0000 0069  # Expired card
```

### 3D Secure (Requires authentication)
```
4000 0025 0000 3155  # Requires authentication
```

**Full list:** https://stripe.com/docs/testing

---

## 🔍 Debugging Common Issues

### Issue: "Webhook secret not configured"

**Symptom:**
```
[Stripe] Webhook secret not configured
```

**Fix:**
1. Check `.env` has `STRIPE_WEBHOOK_SECRET`
2. Restart Flask app
3. Verify: `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('STRIPE_WEBHOOK_SECRET'))"`

### Issue: "Invalid signature"

**Symptom:**
```
[Stripe] Invalid signature: ...
```

**Fix:**
1. Webhook secret doesn't match
2. Get fresh secret from `stripe listen` output
3. Update `.env`
4. Restart Flask

### Issue: "Credits not added"

**Symptom:**
- Payment succeeds but credits don't increase

**Fix:**
1. Check Terminal 1 (Flask) for errors
2. Verify webhook endpoint receiving events: `stripe listen --print-json`
3. Check `handle_checkout_completed` function logs
4. Verify user_id in session metadata

### Issue: Webhook not receiving events

**Symptom:**
- Stripe CLI shows no webhook calls

**Fix:**
```bash
# Test the endpoint directly
curl -X POST http://localhost:5000/webhook/stripe
# Should return error (no signature) but confirms endpoint exists

# Check Flask routes
python -c "from app_v3 import app; print([str(rule) for rule in app.url_map.iter_rules()])"
# Should include: /webhook/stripe
```

---

## 📊 Your Webhook Endpoint Details

**URL:** `http://localhost:5000/webhook/stripe`
**Method:** POST
**File:** [app_v3.py:1056](app_v3.py#L1056)

**Events Handled:**
| Event | What It Does |
|-------|--------------|
| `checkout.session.completed` | Adds credits to user account |
| `payment_intent.succeeded` | Logs successful payment |
| `payment_intent.payment_failed` | Logs failed payment |
| `setup_intent.succeeded` | Saves payment method for auto-recharge |

**What Happens When Webhook Received:**
1. ✅ Verify signature (prevents fraud)
2. ✅ Parse event type
3. ✅ Add credits to user's account (via `add_credits_manual`)
4. ✅ Update `credit_balance` in database
5. ✅ Send confirmation email to user
6. ✅ Return 200 OK to Stripe

---

## 🎯 Production Deployment (Later)

When you deploy to a server, you'll need to:

### 1. Use Live Keys
```bash
# .env (production)
STRIPE_SECRET_KEY=sk_live_51QuaBV...  # Your real key
STRIPE_PUBLISHABLE_KEY=pk_live_51QuaBV...
```

### 2. Configure Webhook in Stripe Dashboard
```
URL: https://yourdomain.com/webhook/stripe
Events: Same as test mode
```

### 3. Get Production Webhook Secret
```
Dashboard → Webhooks → Your endpoint → Reveal secret
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

**Note:** Production and test webhooks have **different secrets!**

---

## ✅ Quick Start Checklist

For local testing RIGHT NOW:

- [ ] Install Stripe CLI: https://github.com/stripe/stripe-cli/releases
- [ ] Login: `stripe login`
- [ ] Start Flask: `python app_v3.py`
- [ ] Start webhook forwarding: `stripe listen --forward-to localhost:5000/webhook/stripe`
- [ ] Copy webhook secret from output
- [ ] Add to `.env`: `STRIPE_WEBHOOK_SECRET=whsec_xxxxx`
- [ ] Restart Flask app
- [ ] Test: `stripe trigger checkout.session.completed`
- [ ] Try real purchase with test card: `4242 4242 4242 4242`
- [ ] Verify credits added in dashboard

**That's it!** Your payment system is ready to test! 🎉

---

## 📚 Resources

- **Stripe CLI:** https://stripe.com/docs/stripe-cli
- **Test Cards:** https://stripe.com/docs/testing
- **Webhooks Guide:** https://stripe.com/docs/webhooks
- **Your Dashboard:** https://dashboard.stripe.com

**Need help?** Check the logs in both terminals for error messages.
