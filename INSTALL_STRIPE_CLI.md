# Stripe CLI Installation & Testing - Step by Step

**Date:** 2025-10-08
**System:** Windows
**Purpose:** Test Stripe payments locally before server deployment

---

## Step 1: Download Stripe CLI

### Option A: Direct Download (Recommended)

**Download link:**
https://github.com/stripe/stripe-cli/releases/latest/download/stripe_1.22.0_windows_x86_64.zip

**Steps:**
1. Click the link above (downloads automatically)
2. File will be: `stripe_1.22.0_windows_x86_64.zip` (about 15MB)
3. Save to your Downloads folder

### Option B: Manual Download

1. Go to: https://github.com/stripe/stripe-cli/releases/latest
2. Scroll to "Assets"
3. Click: `stripe_X.X.X_windows_x86_64.zip`

---

## Step 2: Extract and Install

### Extract the ZIP

**Option 1: Extract to C:\stripe\**
```
1. Right-click the downloaded ZIP
2. Click "Extract All..."
3. Change location to: C:\stripe\
4. Click "Extract"
```

**Option 2: Extract to project folder**
```
1. Right-click the downloaded ZIP
2. Click "Extract All..."
3. Change location to: C:\Users\joema\OneDrive\Documents\AI PROJECT\EZWAI SMM\stripe\
4. Click "Extract"
```

**You should now have:**
```
C:\stripe\stripe.exe  (or in your project folder)
```

---

## Step 3: Verify Installation

**Open PowerShell or Command Prompt:**

**Navigate to Stripe folder:**
```bash
cd C:\stripe
# OR
cd "C:\Users\joema\OneDrive\Documents\AI PROJECT\EZWAI SMM\stripe"
```

**Test the CLI:**
```bash
.\stripe.exe --version
```

**Expected output:**
```
stripe version 1.22.0
```

✅ If you see version number, installation succeeded!

---

## Step 4: Login to Stripe

**Run login command:**
```bash
.\stripe.exe login
```

**What happens:**
1. Opens your browser automatically
2. Shows Stripe login page
3. After login, shows: "Stripe CLI wants to access your account"
4. Click "**Allow access**"

**Terminal output:**
```
Your pairing code is: word-word-word
This pairing code verifies your authentication with Stripe.
Press Enter to open the browser or visit https://dashboard.stripe.com/stripecli/confirm_auth?t=xxxxx

✓ Done! The Stripe CLI is configured for ACME Inc with account id acct_xxxxx

Please note: this key will expire after 90 days, at which point you'll need to re-authenticate.
```

✅ **Success!** CLI is now connected to your Stripe account.

---

## Step 5: Start Webhook Forwarding

### Terminal 1: Start Flask App

**Open first terminal/PowerShell:**
```bash
cd "C:\Users\joema\OneDrive\Documents\AI PROJECT\EZWAI SMM"
python app_v3.py
```

**Expected output:**
```
 * Running on http://0.0.0.0:5000
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.0.34:5000
Press CTRL+C to quit
```

**✅ Keep this terminal open!**

### Terminal 2: Start Stripe Webhook Forwarding

**Open second terminal/PowerShell:**
```bash
cd C:\stripe
# OR
cd "C:\Users\joema\OneDrive\Documents\AI PROJECT\EZWAI SMM\stripe"

.\stripe.exe listen --forward-to localhost:5000/webhook/stripe
```

**Expected output:**
```
> Ready! You are using Stripe API Version [2024-11-20]
> Your webhook signing secret is whsec_1234567890abcdefghijklmnopqrstuvwxyz1234567890
```

**🔑 IMPORTANT: Copy the webhook secret!**

The secret looks like: `whsec_1234567890abcdefghijklmnopqrstuvwxyz1234567890`

**✅ Keep this terminal open too!**

---

## Step 6: Update .env File

**Open `.env` file in your project:**
```
C:\Users\joema\OneDrive\Documents\AI PROJECT\EZWAI SMM\.env
```

**Find this line:**
```bash
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret-here
```

**Replace with your actual secret:**
```bash
STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdefghijklmnopqrstuvwxyz1234567890
```

**Save the file.**

---

## Step 7: Restart Flask App

**Go to Terminal 1 (Flask app):**
1. Press `Ctrl+C` to stop
2. Restart: `python app_v3.py`

**This loads the new webhook secret.**

---

## Step 8: Test the Setup

### Quick Test: Trigger Test Event

**Open a THIRD terminal:**
```bash
cd C:\stripe

.\stripe.exe trigger checkout.session.completed
```

**What you should see:**

**Terminal 2 (Stripe CLI):**
```
2025-10-08 18:30:00   --> checkout.session.completed [evt_xxxxx]
2025-10-08 18:30:00  <--  [200] POST http://localhost:5000/webhook/stripe [evt_xxxxx]
```

**Terminal 1 (Flask app):**
```
[Stripe] Received event: checkout.session.completed
[Stripe] Added $10.00 credits to user 1
```

✅ **Webhooks are working!**

---

## Step 9: Test Real Payment Flow

### Get Test Stripe Keys

**Important:** Switch to TEST mode for testing!

**Get your test keys:**
1. Go to: https://dashboard.stripe.com/test/apikeys
2. Toggle "**Viewing test data**" (top right)
3. Copy:
   - **Publishable key:** `pk_test_51QuaBV...`
   - **Secret key:** `sk_test_51QuaBV...`

### Update .env with TEST Keys

**Edit `.env`:**
```bash
# Use TEST keys for local development
STRIPE_SECRET_KEY=sk_test_51QuaBVKpNqJuvdV9...
STRIPE_PUBLISHABLE_KEY=pk_test_51QuaBVKpNqJuvdV9...
STRIPE_WEBHOOK_SECRET=whsec_xxxxx  # From step 6
```

**Restart Flask app again** (Terminal 1: Ctrl+C, then `python app_v3.py`)

### Complete Test Purchase

1. **Open browser:** `http://localhost:5000`
2. **Login** to your test account
3. **Go to Credits section**
4. **Click "Buy Credits"** or "Add Credits"
5. **Select amount:** e.g., $10
6. **Click "Proceed to Payment"**
7. **Stripe Checkout page opens**

**Enter test card:**
```
Card number: 4242 4242 4242 4242
Expiry: 12/34
CVC: 123
ZIP: 12345
Name: Test User
```

8. **Click "Pay"**

### Watch the Magic! ✨

**Terminal 2 (Stripe CLI):**
```
2025-10-08 18:35:00   --> checkout.session.completed [evt_xxxxx]
2025-10-08 18:35:00  <--  [200] POST http://localhost:5000/webhook/stripe [evt_xxxxx]
```

**Terminal 1 (Flask):**
```
[Stripe] Received event: checkout.session.completed
[Stripe] Added $10.00 credits to user 1
[Email] Sent confirmation to joe@ezwai.com
```

**Your browser:**
- Redirects back to dashboard
- Shows: "Payment successful!"
- Credits updated: $5.00 → $15.00

✅ **IT WORKS!** 🎉

---

## Common Issues & Solutions

### Issue: "stripe: command not found"

**Fix:**
```bash
# Use full path
.\stripe.exe --version

# OR add to PATH
# 1. Search Windows: "environment variables"
# 2. Edit Path variable
# 3. Add: C:\stripe
# 4. Restart terminal
```

### Issue: "Could not connect to Stripe"

**Fix:**
```bash
# Re-login
.\stripe.exe login

# If that fails, check internet connection
ping stripe.com
```

### Issue: "Webhook secret not configured"

**Fix:**
1. Check `.env` has `STRIPE_WEBHOOK_SECRET=whsec_...`
2. No quotes needed around the value
3. Restart Flask app after changing .env
4. Verify: `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('STRIPE_WEBHOOK_SECRET'))"`

### Issue: "Invalid signature"

**Fix:**
1. Webhook secret doesn't match
2. Get fresh secret: Stop and restart `stripe listen`
3. Copy the NEW `whsec_` secret
4. Update `.env`
5. Restart Flask app

### Issue: "Credits not added"

**Fix:**
1. Check Terminal 1 (Flask) for errors
2. Check Terminal 2 (Stripe CLI) shows `[200]` (success)
3. Verify webhook endpoint: `curl http://localhost:5000/webhook/stripe`
4. Check database connection
5. Verify user_id in webhook metadata

---

## Daily Testing Workflow

**Each time you want to test:**

1. **Start Flask:**
   ```bash
   cd "C:\Users\joema\OneDrive\Documents\AI PROJECT\EZWAI SMM"
   python app_v3.py
   ```

2. **Start Stripe forwarding:**
   ```bash
   cd C:\stripe
   .\stripe.exe listen --forward-to localhost:5000/webhook/stripe
   ```

3. **Copy webhook secret** (if changed)
4. **Update .env** if secret changed
5. **Restart Flask** if you updated .env
6. **Test payments!**

---

## Next Steps

**Now you can:**
- ✅ Test buying credits
- ✅ Test different amounts
- ✅ Test different cards (success/failure)
- ✅ Test auto-recharge (if implemented)
- ✅ Verify email notifications
- ✅ Check credit deductions when creating articles

**When ready to deploy:**
1. Clone repo to server
2. Configure production webhook in Stripe Dashboard
3. Get production webhook secret
4. Add to server's `.env`
5. Use live API keys (sk_live_...)

---

## Test Card Reference

### Always Succeeds
```
4242 4242 4242 4242  # Visa
5555 5555 5555 4444  # Mastercard
3782 822463 10005    # American Express
```

### Always Fails
```
4000 0000 0000 0002  # Card declined
4000 0000 0000 9995  # Insufficient funds
4000 0000 0000 0069  # Expired card
```

### Requires 3D Secure
```
4000 0025 0000 3155  # Authentication required
```

**Full list:** https://stripe.com/docs/testing

---

## Summary

✅ **Installed:** Stripe CLI
✅ **Configured:** Webhook forwarding
✅ **Testing:** Local payments with test cards
✅ **Verified:** Credits add automatically

**You're ready to test the complete payment system!** 🚀

**Any issues?** Check the logs in Terminal 1 (Flask) for detailed error messages.
