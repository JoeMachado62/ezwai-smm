# Stripe Payment Testing Guide

## Setup Complete ✅

1. **Stripe CLI** - Installed and authenticated
2. **Webhook Forwarding** - Active on `localhost:5000/webhook/stripe`
3. **Webhook Secret** - Added to `.env` file
4. **Flask App** - Running on `http://127.0.0.1:5000`

## Current Configuration

```
Stripe CLI Version: 1.21.8
Account: EZWAI Consulting (acct_1QuaBVKpNqJuvdV9)
Webhook Secret: whsec_1c4dc031bd79ff4eeb028810af1217416f773c1cf03c1054d2dc414bab8aff0a
API Version: 2025-01-27.acacia
```

## Testing Steps

### Method 1: Manual Webhook Trigger (Fastest)

Use Stripe CLI to trigger test webhooks directly:

```bash
cd stripe_cli

# Trigger successful checkout
./stripe.exe trigger checkout.session.completed

# Trigger payment failed
./stripe.exe trigger checkout.session.async_payment_failed

# Trigger setup intent (save payment method)
./stripe.exe trigger setup_intent.succeeded
```

### Method 2: Full UI Flow (Recommended)

#### Step 1: Access Dashboard
```
http://localhost:5000/dashboard
```

#### Step 2: Login
- Use your existing user account
- Create new account if needed

#### Step 3: Navigate to Credits/Purchase
- Look for "Buy Credits" button in dashboard

#### Step 4: Use Test Cards

**IMPORTANT:** You're using LIVE keys, so test cards won't work!

**Option A - Switch to Test Keys (Recommended):**
1. Get test keys from: https://dashboard.stripe.com/test/apikeys
2. Update .env with `sk_test_...` and `pk_test_...` keys
3. Restart Flask app
4. Use test card: `4242 4242 4242 4242`

**Option B - Use Live Keys (Real Charges):**
⚠️ Use real payment method (will create actual charges)

## Stripe Test Cards (Only work with sk_test_ keys)

**Successful Payment:**
```
Card: 4242 4242 4242 4242
Expiry: 12/34
CVC: 123
ZIP: 12345
```

**Card Declined:**
```
Card: 4000 0000 0000 0002
```

**Insufficient Funds:**
```
Card: 4000 0000 0000 9995
```

## Monitoring

**Terminal 1 (Stripe CLI):**
```
Ready! You are using Stripe API Version [2025-01-27.acacia]
--> checkout.session.completed [evt_xxx]
<-- [200] POST http://localhost:5000/webhook/stripe
```

**Terminal 2 (Flask App):**
```
INFO - Received Stripe webhook: checkout.session.completed
INFO - Added 100 credits to user 1
```

## Verification

Check credits were added:
```bash
curl http://localhost:5000/api/users/1/credits
```

## Troubleshooting

**Webhook not received:**
- Check Stripe CLI is running
- Check Flask app is running on port 5000
- Check no firewall blocking localhost

**Signature verification failed:**
- Verify STRIPE_WEBHOOK_SECRET in .env matches CLI output
- Restart Flask app after .env changes

**Test cards not working:**
- You're using LIVE keys (`sk_live_`)
- Switch to TEST keys (`sk_test_`) for testing

## Testing Checklist

- [ ] Stripe CLI forwarding webhooks
- [ ] Flask app running on localhost:5000
- [ ] Triggered test webhook with `./stripe.exe trigger checkout.session.completed`
- [ ] Saw webhook in Stripe CLI output
- [ ] Saw processing in Flask logs
- [ ] Verified credits added to user account

## Background Processes

**Stripe CLI Webhook Listener:**
- Running in background (ID: 535886)
- Forwarding to: localhost:5000/webhook/stripe

**Flask App:**
- Running in background (ID: 51f23e)
- Listening on: http://127.0.0.1:5000

To stop either process, use Ctrl+C or kill the process ID.
