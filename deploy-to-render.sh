#!/bin/bash

echo "🚀 Deploying Curtain Lights to Render..."

# Initialize git if not already done
if [ ! -d .git ]; then
    echo "📁 Initializing git repository..."
    git init
fi

# Add all files and commit
echo "📝 Committing changes..."
git add .
git commit -m "Deploy Curtain Lights to Render with payment interrupts"

echo "✅ Code committed successfully!"
echo ""
echo "🎯 NEXT STEPS:"
echo ""
echo "1. 🌐 Push to GitHub:"
echo "   - Create a new repo at https://github.com/new"
echo "   - Name it 'curtain-lights'"
echo "   - Run: git remote add origin https://github.com/YOUR_USERNAME/curtain-lights.git"
echo "   - Run: git branch -M main"
echo "   - Run: git push -u origin main"
echo ""
echo "2. 🚀 Deploy on Render:"
echo "   - Go to https://render.com and sign up"
echo "   - Click 'New' → 'Web Service'"
echo "   - Connect your GitHub repo"
echo "   - Use these settings:"
echo "     • Name: curtain-lights-api"
echo "     • Runtime: Python 3"
echo "     • Build Command: pip install -r requirements.txt"
echo "     • Start Command: uvicorn app.main:app --host 0.0.0.0 --port \$PORT"
echo "     • Plan: Free"
echo ""
echo "3. 🔧 Set Environment Variables in Render:"
echo "   GOVEE_API_KEY=your_govee_api_key"
echo "   GOVEE_DEVICE_ID=your_device_id"
echo "   STRIPE_SECRET_KEY=sk_test_your_stripe_key"
echo "   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret"
echo ""
echo "4. 🎯 Update Stripe Webhook URL:"
echo "   - In Stripe Dashboard → Webhooks"
echo "   - Change URL to: https://your-app-name.onrender.com/webhooks/stripe"
echo ""
echo "📚 See RENDER_DEPLOYMENT.md for detailed instructions!"
echo ""
echo "🎉 Your app will be live at: https://your-app-name.onrender.com"
echo "🔥 Payment celebrations will work 24/7 for FREE!" 