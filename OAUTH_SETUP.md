# OAuth Integration Setup Guide

## 🔐 User Authentication & OAuth Setup

Your Gotham Lights system now includes comprehensive user authentication and OAuth integrations for Google (Calendar + YouTube) and Stripe services.

## 📋 Required Environment Variables

Add these to your `.env` file:

```bash
# JWT Authentication
JWT_SECRET_KEY=super_secret_jwt_key_that_should_be_at_least_32_characters_long_for_security

# Application URLs
APP_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Stripe Configuration
STRIPE_SK=sk_test_your_stripe_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
STRIPE_CLIENT_ID=ca_your_stripe_connect_client_id_here
STRIPE_CLIENT_SECRET=your_stripe_client_secret_here
```

## 🔧 Google OAuth Setup

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the following APIs:
   - **Google Calendar API**
   - **YouTube Data API v3**

### 2. Create OAuth 2.0 Credentials
1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth 2.0 Client IDs**
3. Choose **Web Application**
4. Add authorized redirect URIs:
   ```
   http://localhost:8000/oauth/google/callback
   https://yourdomain.com/oauth/google/callback (for production)
   ```
5. Copy the Client ID and Client Secret

### 3. Configure OAuth Consent Screen
1. Go to **APIs & Services > OAuth consent screen**
2. Choose **External** (for testing) or **Internal** (for organization)
3. Fill required fields:
   - App name: "Gotham Lights"
   - User support email: your email
   - Developer contact: your email
4. Add scopes:
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/youtube.readonly`
   - `openid`
   - `email`
   - `profile`

## 💳 Stripe OAuth Setup

### 1. Create Stripe Connect Application
1. Go to [Stripe Dashboard](https://dashboard.stripe.com/)
2. Navigate to **Connect > Settings**
3. Create a new Connect application
4. Fill in application details:
   - App name: "Gotham Lights"
   - Description: "Smart lighting automation"
   - Website: your website URL

### 2. Configure OAuth Settings
1. Set redirect URI: `http://localhost:8000/oauth/stripe/callback`
2. Note your:
   - **Client ID** (starts with `ca_`)
   - **Client Secret**
   - **Webhook signing secret** (create webhook endpoint)

### 3. Set Up Webhooks
1. Go to **Developers > Webhooks**
2. Create endpoint: `http://localhost:8000/stripe`
3. Select events:
   - `payment_intent.succeeded`
   - `checkout.session.completed`
   - `invoice.payment_succeeded`

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Update Environment
Copy values from OAuth setup to your `.env` file.

### 3. Start Backend
```bash
uvicorn app.main:app --reload
```

### 4. Start Frontend
```bash
cd frontend && npm run dev
```

## 🔍 Testing OAuth Flows

### Google Integration Test
1. Register/login to your account
2. Go to Settings > Connected Services
3. Click "Connect" for Google Account
4. Complete OAuth flow in popup
5. Test Calendar/YouTube triggers in Dashboard

### Stripe Integration Test
1. Go to Settings > Connected Services
2. Click "Connect" for Stripe Account
3. Complete Stripe Connect flow
4. Test payment webhooks

## ⚡ Feature Overview

### 🔐 Authentication Features
- **User Registration/Login** with secure password hashing
- **JWT Token Authentication** with 7-day expiry
- **Protected API Endpoints** requiring authentication
- **User-specific Settings** and OAuth tokens

### 🔗 OAuth Integrations
- **Google Calendar**: Trigger lights for upcoming events (10min window)
- **YouTube**: Trigger lights for new subscribers
- **Stripe**: Trigger lights for successful payments
- **Per-user Configuration**: Each user has their own triggers and settings

### 🎨 Enhanced UI
- **Modern Authentication Pages** with login/register forms
- **OAuth Connection Status** in settings
- **User Profile Display** in navigation
- **Secure Token Management** with auto-refresh

### 🏠 Smart Automation
- **User-specific Light Scenes** for different events
- **Personal OAuth Tokens** stored securely
- **Individual Device Configuration** per user
- **Background Processing** for each user's triggers

## 🛡️ Security Features

- **Bcrypt Password Hashing**
- **JWT Token Authentication**
- **OAuth State Validation**
- **Secure Token Storage**
- **User Isolation** (each user only sees their data)

## 📱 Usage Flow

1. **Register/Login** to create your account
2. **Connect Google** for Calendar and YouTube automation
3. **Connect Stripe** for payment notifications  
4. **Configure Light Scenes** for each trigger type
5. **Test Everything** with the light testing controls
6. **Enjoy Automated Lighting** based on your connected services!

## 🔧 Production Deployment

For production, update:
- Set `APP_BASE_URL` to your domain
- Use HTTPS for all OAuth redirect URIs
- Set strong `JWT_SECRET_KEY`
- Configure proper database (PostgreSQL recommended)
- Set up proper webhook endpoints with HTTPS

## 🆘 Troubleshooting

### Common Issues
1. **OAuth Redirect Mismatch**: Ensure redirect URIs match exactly
2. **Token Expired**: Re-authenticate in Settings
3. **API Limits**: Check Google/Stripe API quotas
4. **Webhook Failures**: Verify endpoint URLs and signatures

### Debug Endpoints
- `GET /debug/env` - Check environment configuration
- `GET /oauth/status` - Check OAuth connection status
- `GET /auth/me` - Check current user authentication

## 📚 API Documentation

The FastAPI backend provides interactive documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

All endpoints now require authentication except:
- `/auth/register`
- `/auth/login`
- `/oauth/{service}/callback` 