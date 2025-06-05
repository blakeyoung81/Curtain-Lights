# 🌟 Gotham Lights

A full-stack web application that automatically triggers your Govee curtain lights based on various events:
- 💰 **Stripe payments** (payment_intent.succeeded & checkout.session.completed)
- 📅 **Google Calendar events** (starting within 10 minutes)
- 🔴 **YouTube new subscribers**

## 🚀 Features

- **FastAPI Backend** with async webhook handling
- **React Frontend** with shadcn/ui components
- **Rate-limited Govee API** integration (max 10 req/min)
- **Free-tier deployable** on Fly.io
- **Automated cron polling** via GitHub Actions
- **Real-time config updates** with React Query

## 📦 Local Development

### Prerequisites

- Python 3.12+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
cp env.template .env

# Edit .env with your API keys (see configuration section below)

# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

## 🔧 Configuration

### 1. Govee API Setup

1. Download the Govee Home app
2. Get your API key from [Govee Developer Dashboard](https://developer.govee.com/)
3. Find your device ID and model in the app or via API call:
   ```bash
   curl -H "Govee-API-Key: YOUR_API_KEY" https://developer-api.govee.com/v1/devices
   ```

### 2. Stripe Webhook Setup

1. Create a Stripe account and get your secret key
2. Set up a webhook endpoint pointing to `https://your-domain.fly.dev/stripe`
3. Select events: `payment_intent.succeeded` and `checkout.session.completed`
4. Copy the webhook signing secret

For local development, use ngrok:
```bash
# Install ngrok (free tier)
ngrok http 8000

# Use the ngrok URL for Stripe webhook: https://abc123.ngrok.io/stripe
```

### 3. Google Calendar API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the Google Calendar API
4. Create a service account:
   - Go to IAM & Admin > Service Accounts
   - Create service account with Calendar API access
   - Download the JSON key file
5. Share your calendar with the service account email
6. Extract `client_email` and `private_key` from the JSON for your `.env`

### 4. YouTube Data API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable YouTube Data API v3
3. Create API credentials (API Key)
4. Note: The current implementation checks for public subscribers, which requires channel ownership verification

## 🐳 Deployment

### Fly.io (Free Tier)

1. Install [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/)
2. Sign up for Fly.io account
3. Deploy:

```bash
# Login to Fly.io
flyctl auth login

# Launch app (first time)
flyctl launch

# Set environment variables
flyctl secrets set GOVEE_API_KEY=your_key
flyctl secrets set GOVEE_DEVICE_ID=your_device_id
flyctl secrets set GOVEE_MODEL=your_model
flyctl secrets set STRIPE_SK=your_stripe_key
flyctl secrets set STRIPE_WEBHOOK_SECRET=your_webhook_secret
flyctl secrets set GOOGLE_CLIENT_EMAIL=your_service_account_email
flyctl secrets set GOOGLE_PRIVATE_KEY="your_private_key"
flyctl secrets set YT_API_KEY=your_youtube_key

# Deploy
flyctl deploy
```

### GitHub Actions Cron Setup

1. Add repository secret `FLY_APP_NAME` with your Fly.io app name
2. The workflow in `.github/workflows/cron.yml` will automatically call `/cron` every minute

## 🔗 API Endpoints

- `GET /` - Health check
- `POST /stripe` - Stripe webhook handler
- `GET /cron` - Cron job for YouTube/Calendar polling
- `GET /config/scene` - Get current scene configuration
- `PUT /config/scene` - Update scene configuration

## 🎨 Frontend

Built with:
- React 18 + TypeScript
- Vite for fast development
- Tailwind CSS for styling
- shadcn/ui for components
- React Query for state management
- Sonner for toast notifications

## 🔍 Troubleshooting

### Common Issues

1. **Govee API Rate Limiting**: Built-in throttling limits to 10 requests/minute
2. **YouTube API Quota**: Free tier has daily limits, consider upgrading for heavy usage
3. **Calendar Events Not Triggering**: Ensure service account has calendar access
4. **Stripe Webhooks Failing**: Verify webhook URL and signing secret

### Logs

```bash
# View Fly.io logs
flyctl logs

# Local development logs
# Check terminal running uvicorn for backend logs
# Check browser console for frontend logs
```

## 📄 License

MIT License - feel free to use this project for personal or commercial purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Made with ❤️ for automated lighting experiences**

# Curtain Lights 🎭

Your Personal Light Celebration System - Automated lighting celebrations for Stripe payments and YouTube subscriber milestones using Govee smart lights.

## Latest Update
- Simplified celebration system: Just 2 image types needed (payment + youtube)
- 5-second custom celebration followed by amount/subscriber count display
- 14×20 LED optimization for Govee H70B1 curtain lights (280 LEDs)