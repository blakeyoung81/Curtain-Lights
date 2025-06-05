# 🎯 Stripe Webhook Setup Guide

## Quick Setup (3 steps)

### 1. **Create Webhook Endpoint in Stripe Dashboard**

1. Go to [Stripe Dashboard](https://dashboard.stripe.com) → **Developers** → **Webhooks**
2. Click **"Add endpoint"**
3. Enter your endpoint URL:
   - **Local testing**: `http://localhost:8000/webhooks/stripe`
   - **Production (Fly.io)**: `https://your-app-name.fly.dev/webhooks/stripe`
4. Select events to listen to:
   - ✅ `payment_intent.succeeded`
   - ✅ `checkout.session.completed`
   - ✅ `invoice.payment_succeeded`
5. Click **"Add endpoint"**

### 2. **Get Your Webhook Secret**

After creating the webhook:
1. Click on your new webhook endpoint
2. Click **"Reveal secret"** in the **Signing secret** section
3. Copy the secret (starts with `whsec_...`)
4. Add it to your environment:

```bash
# Add to .env file
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here
```

### 3. **Test Your Webhook**

**Option A: Use Stripe CLI (Recommended for local testing)**
```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login to your Stripe account
stripe login

# Forward events to your local server
stripe listen --forward-to localhost:8000/webhooks/stripe
```

**Option B: Test with actual payment**
1. Create a test payment in your app
2. Check webhook logs in Stripe Dashboard
3. Verify lights celebration triggers

## 🔧 **Environment Variables Needed**

Make sure these are set in your `.env` file:

```bash
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Your existing Govee settings
GOVEE_API_KEY=your_govee_key
GOVEE_DEVICE_ID=your_device_id
```

## 🚀 **Production Deployment**

When you deploy to Fly.io:

1. **Set production webhook URL**:
   ```bash
   # Update webhook endpoint in Stripe Dashboard to:
   https://your-app-name.fly.dev/webhooks/stripe
   ```

2. **Set environment variables on Fly.io**:
   ```bash
   fly secrets set STRIPE_WEBHOOK_SECRET=whsec_your_secret_here
   fly secrets set STRIPE_SECRET_KEY=sk_live_your_key_here
   fly secrets set GOVEE_API_KEY=your_govee_key
   fly secrets set GOVEE_DEVICE_ID=your_device_id
   ```

## 🧪 **Testing Payment Interrupts**

### Manual Test
```bash
# Test endpoint (while app is running)
curl -X POST http://localhost:8000/test/payment \
  -H "Content-Type: application/json" \
  -d '{"amount": 10000}'  # $100.00 in cents
```

### Real Payment Test
1. Create a test payment through your app
2. Watch for webhook in Stripe Dashboard → **Webhooks** → **Your endpoint** → **Recent attempts**
3. Check your lights for celebration pattern
4. Verify original scene restores after celebration

## 🐛 **Troubleshooting**

**Webhook not receiving events?**
1. Check webhook URL is correct
2. Verify webhook secret in `.env`
3. Check Stripe Dashboard → Webhooks → Recent attempts for errors

**Lights not changing?**
1. Test Govee API directly: `/lights/test`
2. Check payment interrupt status: `/payment/interrupt/status`
3. Verify Govee credentials in environment

**Local development issues?**
1. Use `stripe listen` for local webhook forwarding
2. Check terminal logs for errors
3. Test with `/test/payment` endpoint first

## 📋 **Event Types Explained**

- **`payment_intent.succeeded`**: Direct API payments
- **`checkout.session.completed`**: Stripe Checkout payments  
- **`invoice.payment_succeeded`**: Subscription/recurring payments

Your app handles all these automatically with different celebration patterns based on amount:
- **$100+**: 30s premium gold/purple celebration
- **$50-99**: 20s major green/yellow celebration  
- **$20-49**: 15s standard green celebration
- **$0-19**: 10s gentle mini celebration 