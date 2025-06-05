# 🚀 FREE 24/7 Hosting Setup - Payment-Triggered Light Celebrations

## 🎉 **What You'll Get**

✅ **Free 24/7 hosting** (no monthly costs!)  
✅ **Automatic payment celebrations** - lights interrupt current scene when you get paid  
✅ **Smart celebration patterns** based on payment amount:
- 💎 **$100+**: 30-second premium gold/purple celebration
- 🌟 **$50+**: 20-second major sale green/yellow party  
- 🎊 **$20+**: 15-second standard green celebration
- ✨ **Under $20**: 10-second gentle celebration

✅ **Auto-restore** - lights return to previous state after celebration

---

## 🆓 **Free Hosting Options**

### **Option 1: Fly.io (Recommended - FREE)**

**Why Fly.io:**
- FREE tier: 3 shared-cpu VMs with 256MB RAM
- Your lights system fits perfectly in free tier
- Global edge network
- Auto-sleep saves resources (wakes instantly)

**Setup:**
```bash
# 1. Install Fly CLI
curl -L https://fly.io/install.sh | sh

# 2. Create account (free)
fly auth signup

# 3. Deploy your app (one command!)
fly deploy

# 4. Set environment variables
fly secrets set GOVEE_API_KEY="your_govee_key"
fly secrets set GOVEE_DEVICE_ID="your_device_id"
fly secrets set GOVEE_MODEL="your_model"
fly secrets set JWT_SECRET_KEY="your_jwt_secret"
```

### **Option 2: Railway (Also FREE)**

**Setup:**
```bash
# 1. Connect GitHub to Railway
# 2. Import this repository
# 3. Set environment variables in dashboard
# 4. Deploy automatically on git push
```

### **Option 3: Render (FREE tier)**

**Setup:**
```bash
# 1. Connect GitHub to Render
# 2. Create web service from repository
# 3. Set build command: pip install -r requirements.txt
# 4. Set start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## 🎯 **Payment Integration Setup**

### **For Stripe (E-commerce/SaaS)**

1. **Create Stripe Webhook:**
```bash
# In Stripe Dashboard:
# 1. Go to Developers → Webhooks
# 2. Add endpoint: https://your-app.fly.dev/stripe
# 3. Select events:
#    - payment_intent.succeeded
#    - checkout.session.completed
#    - invoice.payment_succeeded
```

2. **Set Webhook Secret:**
```bash
fly secrets set STRIPE_WEBHOOK_SECRET="whsec_your_webhook_secret"
```

### **For PayPal/Other Providers**

Let me know and I'll add support for other payment providers!

---

## 🔧 **How It Works**

### **1. Normal Operation**
```
Your System Running 24/7 (FREE) →
├── Calendar automation
├── Time-based scenes  
├── Manual controls
└── Monitoring for payments...
```

### **2. Payment Received**
```
Payment comes in → Webhook triggered → 
├── 💾 Save current light state
├── 🛑 Stop current automation
├── 🎉 Start celebration pattern
├── ⏰ Run for X seconds
└── 🔄 Restore original state
```

### **3. Celebration Patterns**

**💎 Premium ($100+):**
- Gold → Purple → White Flash → Gold (30 seconds)

**🌟 Major Sale ($50+):**
- Green → Yellow → White Flash (20 seconds)

**🎊 Standard ($20+):**
- Green → White Flash (15 seconds)

**✨ Mini ($0-20):**
- Gentle Green → Soft White (10 seconds)

---

## 🎮 **Testing Your Setup**

### **Test Payment Celebration:**
```bash
# Visit your deployed app
curl -X POST "https://your-app.fly.dev/test/payment?amount=75" \
  -H "Authorization: Bearer your_jwt_token"
```

### **Test Different Amounts:**
- `?amount=150` → Premium celebration (30s)
- `?amount=75` → Major sale (20s)  
- `?amount=25` → Standard (15s)
- `?amount=10` → Mini (10s)

---

## 🚀 **Quick Deploy Script**

Save this as `deploy.sh`:

```bash
#!/bin/bash
echo "🚀 Deploying Gotham Lights to FREE hosting..."

# Install Fly CLI if not installed
if ! command -v fly &> /dev/null; then
    echo "Installing Fly CLI..."
    curl -L https://fly.io/install.sh | sh
fi

# Deploy
echo "🎯 Deploying to Fly.io..."
fly deploy

# Get app URL
APP_URL=$(fly info --json | jq -r '.hostname')
echo ""
echo "✅ DEPLOYED SUCCESSFULLY!"
echo "🌐 Your app: https://$APP_URL"
echo "🎮 Test payment: https://$APP_URL/test/payment?amount=50"
echo "📚 API docs: https://$APP_URL/docs"
echo ""
echo "🎉 Your lights will now celebrate payments 24/7 for FREE!"
```

---

## 🔄 **Keep-Alive Setup**

The GitHub Action in your repo already handles this:
- Pings your app every minute
- Prevents auto-sleep during important times
- Costs $0 (GitHub Actions free tier)

---

## 💰 **Cost Breakdown**

| Service | Cost | Usage |
|---------|------|-------|
| Fly.io Hosting | **FREE** | 3 VMs, 256MB each |
| GitHub Actions | **FREE** | Keep-alive pings |
| Domain (optional) | $10/year | Custom domain |
| **Total** | **$0-10/year** | Professional setup |

---

## 🛠 **Advanced Features**

### **Custom Celebration Patterns**

Edit `app/payment_interrupts.py` to customize:
```python
# Add your own patterns
def _get_celebration_pattern(self, amount: float) -> Dict:
    if amount >= 1000:  # 🎆 MEGA SALE!
        return {
            "name": "🎆 MEGA CELEBRATION",
            "duration": 60,  # 1 minute party!
            "patterns": [
                # Your custom mega pattern
            ]
        }
```

### **Multiple Payment Sources**

The system supports:
- Stripe webhooks (already set up)
- PayPal webhooks (can add)
- Manual triggers via API
- Custom payment providers

### **Team Notifications**

Add Slack/Discord webhooks to celebrate with your team:
```python
# In payment_interrupts.py
await send_slack_notification(f"💰 ${amount} payment received!")
```

---

## 🎯 **Next Steps**

1. **Deploy:** Run `fly deploy` 
2. **Test:** Visit `/test/payment?amount=50`
3. **Set up webhooks:** Add your payment provider
4. **Enjoy:** Watch your lights celebrate every sale! 🎉

**Your lights will now interrupt whatever they're doing to celebrate payments - completely automatically and FREE!**

---

## 🆘 **Troubleshooting**

### **Lights not responding:**
- Check Govee API key in secrets
- Verify device ID is correct
- Test manual controls first

### **Webhooks not working:**
- Verify webhook URL is correct
- Check webhook secret is set
- Look at app logs: `fly logs`

### **App sleeping too much:**
- GitHub Actions pings every minute
- Can adjust ping frequency if needed
- Upgrade to paid tier for always-on

**Questions? Check logs with `fly logs` or test endpoints at `/docs`!** 