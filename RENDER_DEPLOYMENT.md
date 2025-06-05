# 🚀 Free 24/7 Hosting on Render

## ✅ **Why Render?**
- **Truly FREE** 750 hours/month (enough for 24/7 with smart sleep)
- **Auto-wake** from sleep when requests come in  
- **Singapore region** for better performance
- **No credit card required** for free tier

## 🚀 **One-Click Deploy** 

### **Method 1: GitHub + Render Dashboard**

1. **Push your code to GitHub:**
   ```bash
   # Initialize git (if not done)
   git init
   git add .
   git commit -m "Deploy Curtain Lights to Render"
   
   # Create GitHub repo and push
   gh repo create curtain-lights --public --push
   # OR manually create repo on GitHub and push
   ```

2. **Deploy on Render:**
   - Go to [render.com](https://render.com) and sign up
   - Click **"New" → "Blueprint"**
   - Connect your GitHub repo
   - Select `render.yaml` file
   - Click **"Apply"**

### **Method 2: Direct Web Service**

1. **Go to [render.com](https://render.com)**
2. **Click "New" → "Web Service"**
3. **Connect GitHub repo**
4. **Configure:**
   - **Name**: `curtain-lights-api`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: **Free**

## 🔧 **Environment Variables Setup**

After deploying, add these environment variables in Render Dashboard:

### **Required Variables:**
```bash
GOVEE_API_KEY=your_govee_api_key
GOVEE_DEVICE_ID=your_device_id  
STRIPE_SECRET_KEY=sk_test_your_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

### **Optional Variables:**
```bash
GOOGLE_CLIENT_EMAIL=your-service-account@project.iam.gserviceaccount.com
GOOGLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----...
YT_API_KEY=your_youtube_api_key
```

## 🎯 **Stripe Webhook Setup for Production**

1. **In Stripe Dashboard:**
   - Go to **Developers → Webhooks**
   - Click **"Add endpoint"**
   - URL: `https://your-app-name.onrender.com/webhooks/stripe`
   - Events: `payment_intent.succeeded`, `checkout.session.completed`

2. **Copy webhook secret to Render environment variables**

## 🔄 **Auto-Sleep & Wake System**

**Free tier limitations:**
- **Sleeps after 15 minutes** of inactivity
- **Wakes automatically** when request received (30-60 second delay)
- **750 hours/month** total runtime

**To maximize uptime:**
- Your GitHub Actions cron job will ping every minute
- Keeps app awake during business hours
- Allows sleep during low-traffic periods
- **Effectively 24/7** for your use case

## 📊 **Cost Breakdown**

| Service | Free Tier | Your Usage | Cost |
|---------|-----------|------------|------|
| **Render** | 750 hours/month | Smart sleep/wake | **$0/month** |
| **GitHub** | Actions included | Cron pings | **$0/month** |
| **Stripe** | No monthly fee | Per transaction | **$0/month** |
| **Domain** (optional) | N/A | Custom domain | **$10/year** |

**Total: $0-10/year**

## 🎉 **Testing Your Deployment**

1. **Test API endpoints:**
   ```bash
   curl https://your-app-name.onrender.com/health
   curl https://your-app-name.onrender.com/lights/status
   ```

2. **Test payment interrupts:**
   ```bash
   curl -X POST https://your-app-name.onrender.com/test/payment \
     -H "Content-Type: application/json" \
     -d '{"amount": 5000}'
   ```

3. **Check logs in Render Dashboard** for any issues

## 🚨 **Troubleshooting**

**App won't start?**
- Check logs in Render Dashboard
- Verify all environment variables are set
- Check requirements.txt compatibility

**Webhook not working?**
- Verify webhook URL in Stripe Dashboard
- Check webhook secret matches environment variable
- Test with Stripe CLI: `stripe listen --forward-to your-app.onrender.com/webhooks/stripe`

**App sleeping too much?**
- GitHub Actions should ping every minute
- Check workflow is enabled in your repo
- Consider paid plan ($7/month) for always-on

## 🎯 **Next Steps**

1. **Deploy to Render** using instructions above
2. **Set up environment variables** 
3. **Configure Stripe webhook** with production URL
4. **Test payment celebrations** with real transactions
5. **Enjoy 24/7 free hosting!** 🎉

Your Curtain Lights system will now run 24/7 for FREE, automatically celebrating every payment with custom light shows! 