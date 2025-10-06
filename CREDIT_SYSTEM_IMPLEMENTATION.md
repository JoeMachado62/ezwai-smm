# Credit System Implementation - Complete Guide

## Overview

EZWAI SMM has been upgraded from a "Bring Your Own API Keys" model to a professional **usage-based SaaS platform** with Stripe payment processing.

## Pricing Model

- **$1.99 per article** (cost: ~$0.45, margin: 77%)
- **$5 welcome credit** for new users (2 free articles)
- **$10 minimum purchase**
- **Auto-recharge** available (triggers when balance below $2.50)
- Future: Volume discounts for agencies

## Database Changes

### New User Fields
```sql
credit_balance FLOAT DEFAULT 5.00
auto_recharge_enabled BOOLEAN DEFAULT FALSE
auto_recharge_amount FLOAT DEFAULT 10.00
auto_recharge_threshold FLOAT DEFAULT 2.50
stripe_customer_id VARCHAR(255) UNIQUE
stripe_payment_method_id VARCHAR(255)
is_admin BOOLEAN DEFAULT FALSE
total_articles_generated INTEGER DEFAULT 0
total_spent FLOAT DEFAULT 0.00
created_at DATETIME
```

### New Table: credit_transactions
```sql
id INTEGER PRIMARY KEY
user_id INTEGER FOREIGN KEY
amount FLOAT  # Positive for purchases, negative for usage
transaction_type VARCHAR(50)  # 'welcome', 'purchase', 'auto_recharge', 'article_generation', 'refund'
stripe_payment_intent_id VARCHAR(255)
balance_after FLOAT
description VARCHAR(500)
created_at DATETIME
```

## Architecture

### 1. Landing Page (`/`)
- Professional gradient design matching dashboard theme
- "Try It Now - Get $5 Free Credit" CTA
- No credit card required for signup
- Live article preview
- Feature showcase
- Transparent pricing section

### 2. Registration Flow
1. User registers → Stripe customer created
2. Email verification sent
3. User verifies email
4. $5 welcome credit added automatically
5. User redirected to dashboard

### 3. Credit System (`credit_system.py`)
**Functions:**
- `check_sufficient_credits(user)` - Verify balance before article generation
- `deduct_credits(user, db)` - Deduct $1.99 and trigger auto-recharge if needed
- `refund_credits(user, db, reason)` - Refund if generation fails
- `add_credits_manual(user_id, amount, payment_intent_id, db)` - Add credits after purchase
- `add_welcome_credit(user_id, db)` - Add welcome credit (one-time)
- `trigger_auto_recharge(user, db)` - Auto-charge saved payment method
- `get_transaction_history(user_id, limit)` - Fetch transaction history
- `get_credit_stats(user_id)` - Get usage statistics

### 4. Article Generation Flow
```
1. User clicks "Create Post"
2. Check credits (required: $1.99)
   - If insufficient → Return 402 error with balance info
3. Deduct credits BEFORE generation
4. Generate article (GPT-5-mini + SeeDream-4)
   - If success → Article created, email sent
   - If failure → Refund credits automatically
5. Log transaction
6. Check auto-recharge threshold
```

### 5. Stripe Integration

#### Endpoints Created

**GET `/api/users/<user_id>/credits`**
- Returns: balance, auto-recharge settings, stats
- Auth: Required (user must match)

**GET `/api/users/<user_id>/transactions`**
- Returns: Transaction history (last 50)
- Auth: Required

**PUT `/api/users/<user_id>/auto-recharge`**
- Body: `{enabled, amount, threshold}`
- Updates auto-recharge settings

**POST `/api/credits/purchase`**
- Body: `{amount}` (minimum $10)
- Creates Stripe checkout session
- Returns: `{checkout_url, session_id}`

**POST `/api/credits/setup-payment-method`**
- Creates Stripe SetupIntent for saving card
- Returns: `{client_secret}`

**POST `/webhook/stripe`**
- Handles Stripe webhook events
- Events: checkout.session.completed, payment_intent.succeeded, setup_intent.succeeded
- Verifies signature using `STRIPE_WEBHOOK_SECRET`

#### Stripe Checkout Flow
1. User clicks "Add Credits" in dashboard
2. Frontend calls `/api/credits/purchase` with amount
3. Backend creates Stripe checkout session
4. User redirected to Stripe hosted checkout
5. User enters payment details
6. On success → Stripe webhook fires
7. Backend adds credits and sends confirmation email
8. User redirected to `/dashboard?purchase=success`

#### Auto-Recharge Flow
1. User saves payment method via SetupIntent
2. Enables auto-recharge in settings
3. When `credit_balance < auto_recharge_threshold`:
   - Charge saved payment method
   - Add credits to balance
   - Send email notification
4. If card fails → Send email to update payment method

## Environment Variables Required

Add to `.env`:
```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Stripe Dashboard Configuration

### 1. Get API Keys
- Dashboard → Developers → API keys
- Use TEST mode for development
- Use LIVE mode for production

### 2. Create Webhook
- Dashboard → Developers → Webhooks
- Add endpoint: `https://yourdomain.com/webhook/stripe`
- Select events:
  - `checkout.session.completed`
  - `payment_intent.succeeded`
  - `payment_intent.payment_failed`
  - `setup_intent.succeeded`
- Copy webhook signing secret to `.env`

### 3. Local Testing
```bash
# Install Stripe CLI
stripe listen --forward-to localhost:5000/webhook/stripe

# Use the webhook secret from CLI output in .env
```

## Frontend Integration TODO

### Dashboard Updates Needed

1. **Credit Balance Display**
```javascript
// Fetch on page load
fetch('/api/users/{user_id}/credits')
  .then(res => res.json())
  .then(data => {
    document.getElementById('credit-balance').textContent = `$${data.balance.toFixed(2)}`;
  });
```

2. **Purchase Credits Button**
```javascript
async function purchaseCredits(amount) {
  const res = await fetch('/api/credits/purchase', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({amount})
  });
  const {checkout_url} = await res.json();
  window.location.href = checkout_url; // Redirect to Stripe
}
```

3. **Handle Insufficient Credits**
```javascript
// When article generation returns 402
fetch('/api/create_test_post', {method: 'POST'})
  .then(res => {
    if (res.status === 402) {
      return res.json().then(data => {
        alert(`Insufficient credits! Balance: $${data.balance}, Required: $${data.required}`);
        // Show "Add Credits" modal
      });
    }
    return res.json();
  });
```

4. **Transaction History**
```javascript
// Show in settings/account page
fetch('/api/users/{user_id}/transactions')
  .then(res => res.json())
  .then(data => {
    // Render transaction table
    data.transactions.forEach(tx => {
      // Display: date, type, amount, balance_after
    });
  });
```

5. **Auto-Recharge Toggle**
```javascript
async function updateAutoRecharge(enabled, amount, threshold) {
  await fetch('/api/users/{user_id}/auto-recharge', {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({enabled, amount, threshold})
  });
}
```

## Security Considerations

1. **Stripe Webhook Signature Verification**
   - All webhooks verified using `stripe.Webhook.construct_event()`
   - Prevents unauthorized credit additions

2. **User Authorization**
   - All credit endpoints require `@login_required`
   - User ID validation (`current_user.id != user_id`)

3. **Admin-Only API Keys**
   - OpenAI/Perplexity keys hidden from regular users
   - Only visible to users with `is_admin=True`

4. **Credit Refunds**
   - Automatic refunds on generation failure
   - Prevents charging for failed articles

5. **Minimum Purchase Enforcement**
   - Backend validates `amount >= MIN_PURCHASE` ($10)
   - Prevents abuse of payment processing

## Testing Checklist

### Registration & Welcome Credit
- [ ] Register new user → Stripe customer created
- [ ] Verify email → Welcome credit added ($5.00)
- [ ] Check transaction log shows "welcome" type

### Article Generation
- [ ] Create article with sufficient credits → Deducted $1.99
- [ ] Check balance updated correctly
- [ ] Check transaction log shows "article_generation"
- [ ] Article generation fails → Credits refunded
- [ ] Create article with insufficient credits → 402 error

### Credit Purchase
- [ ] Click "Add Credits" → Stripe checkout opens
- [ ] Complete payment → Webhook fires
- [ ] Credits added to balance
- [ ] Confirmation email sent
- [ ] Transaction log shows "purchase"

### Auto-Recharge
- [ ] Save payment method via SetupIntent
- [ ] Enable auto-recharge ($10 when below $2.50)
- [ ] Generate articles until balance < $2.50
- [ ] Auto-recharge triggers
- [ ] Credits added, email sent
- [ ] Transaction log shows "auto_recharge"

### Stripe Webhooks
- [ ] Test with Stripe CLI: `stripe trigger checkout.session.completed`
- [ ] Verify signature validation works
- [ ] Test duplicate webhook (should be idempotent)

## Migration from Old System

### For Existing Users
If you have existing users with API keys:

1. **Data Migration Script**
```python
# Run once to migrate existing users
from app_v3 import app, db, User
import stripe

with app.app_context():
    users = User.query.all()
    for user in users:
        if not user.stripe_customer_id:
            # Create Stripe customer
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}"
            )
            user.stripe_customer_id = customer.id
            user.credit_balance = 0.00  # No welcome credit for existing users
            db.session.commit()
```

2. **Transition Plan**
- Option A: Give existing users $10 credit as migration bonus
- Option B: Let them use old API keys until depleted, then switch to credits
- Option C: Immediate cutover (not recommended)

## Cost Analysis

**Per Article:**
- GPT-5-mini reasoning: ~$0.30
- SeeDream-4 (4 images): ~$0.12
- Perplexity AI: ~$0.03
- **Total Cost: $0.45**

**Revenue Per Article: $1.99**
**Profit Per Article: $1.54 (77% margin)**

**Break-Even:**
- Need to serve 10 articles to cover $10 purchase
- User gets 5 articles from $10 credit
- Profit: $5 per $10 purchase

## Monitoring & Analytics

### Key Metrics to Track

1. **User Acquisition**
   - Signups per day
   - Verification rate
   - Welcome credit usage rate

2. **Revenue**
   - Total credits purchased
   - Average purchase amount
   - Monthly recurring revenue (from heavy users)

3. **Usage**
   - Articles generated per user
   - Average credits per user
   - Churn rate (users who don't return after welcome credit)

4. **Costs**
   - OpenAI API costs
   - Replicate costs
   - Perplexity costs
   - Stripe fees (2.9% + $0.30)

5. **Auto-Recharge**
   - % of users with auto-recharge enabled
   - Auto-recharge success rate
   - Card failure rate

### Suggested Dashboard Queries

```sql
-- Total revenue this month
SELECT SUM(amount) FROM credit_transactions
WHERE transaction_type IN ('purchase', 'auto_recharge')
AND created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH);

-- Active users (generated article in last 30 days)
SELECT COUNT(DISTINCT user_id) FROM credit_transactions
WHERE transaction_type = 'article_generation'
AND created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH);

-- Average lifetime value per user
SELECT AVG(total_spent) FROM users WHERE total_spent > 0;

-- Conversion rate (% who purchase after welcome credit)
SELECT
  COUNT(DISTINCT CASE WHEN total_spent > 0 THEN id END) * 100.0 / COUNT(*)
FROM users;
```

## Future Enhancements

### Phase 2 Features
1. **Subscription Tiers**
   - Starter: $29/mo for 30 articles
   - Pro: $79/mo for 100 articles
   - Agency: $199/mo for unlimited

2. **Volume Discounts**
   - Buy $100 → Get $110 in credits
   - Buy $500 → Get $550 in credits

3. **Referral Program**
   - Give $5 credit for each referral
   - Referee gets $5 credit too

4. **Usage Analytics Dashboard**
   - Chart showing credit usage over time
   - Cost breakdown (AI, images, research)
   - ROI calculator

5. **Team Accounts**
   - Share credit pool across team members
   - Role-based access control
   - Consolidated billing

## Support & Troubleshooting

### Common Issues

**"Stripe customer creation failed"**
- Check `STRIPE_SECRET_KEY` in `.env`
- Verify Stripe account is active
- Check for IP restrictions in Stripe dashboard

**"Webhook signature verification failed"**
- Verify `STRIPE_WEBHOOK_SECRET` matches webhook endpoint
- Check webhook endpoint is publicly accessible
- Ensure payload isn't being modified by proxy/firewall

**"Credits not added after payment"**
- Check webhook received (Stripe Dashboard → Webhooks → Events)
- Check application logs for webhook processing errors
- Verify `handle_checkout_completed()` executed successfully

**"Auto-recharge not triggering"**
- Verify user has saved payment method (`stripe_payment_method_id`)
- Check auto_recharge_enabled is TRUE
- Verify balance is below threshold
- Check Stripe logs for card decline

### Logs to Check

```bash
# Application logs
tail -f logs/app_v3.log | grep -i "credit\|stripe"

# Specific user's transactions
SELECT * FROM credit_transactions WHERE user_id = X ORDER BY created_at DESC;

# Failed auto-recharges
# Check logs for: "[Auto-Recharge] Card error"
```

## Success Metrics

Target KPIs:
- **Signup Conversion**: >40% verify email
- **Welcome Credit Usage**: >60% use at least 1 free article
- **Purchase Conversion**: >20% purchase credits after welcome credit
- **Retention**: >30% return within 30 days
- **Average LTV**: >$50 per user
- **Profit Margin**: >70%

## Conclusion

The credit system transforms EZWAI SMM from a developer tool into a professional SaaS platform. With Stripe integration, auto-recharge, and transparent pricing, it's ready to scale to hundreds or thousands of users.

**Next Steps:**
1. Add environment variables to `.env`
2. Configure Stripe webhook
3. Update dashboard frontend with credit UI
4. Test full payment flow in Stripe test mode
5. Deploy to production
6. Switch to Stripe live keys
7. Launch! 🚀
