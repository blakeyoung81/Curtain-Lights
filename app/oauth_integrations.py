import os
import requests
import json
from typing import Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import stripe
from dotenv import load_dotenv

load_dotenv()

class GoogleOAuthHandler:
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("APP_BASE_URL", "http://localhost:8000") + "/oauth/google/callback"
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access tokens"""
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            tokens = response.json()
            # Add expiry time for easier checking
            if "expires_in" in tokens:
                tokens["expires_at"] = (datetime.now() + timedelta(seconds=tokens["expires_in"])).isoformat()
            return tokens
        else:
            raise Exception(f"Failed to exchange code for tokens: {response.text}")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            tokens = response.json()
            if "expires_in" in tokens:
                tokens["expires_at"] = (datetime.now() + timedelta(seconds=tokens["expires_in"])).isoformat()
            return tokens
        else:
            raise Exception(f"Failed to refresh token: {response.text}")
    
    def get_valid_credentials(self, tokens: Dict[str, Any]) -> Credentials:
        """Get valid Google credentials, refreshing if necessary"""
        creds = Credentials(
            token=tokens.get("access_token"),
            refresh_token=tokens.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        
        # Check if token needs refresh
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        
        return creds

class GoogleCalendarService:
    def __init__(self, oauth_handler: GoogleOAuthHandler):
        self.oauth_handler = oauth_handler
    
    async def check_upcoming_events(self, tokens: Dict[str, Any]) -> bool:
        """Check for upcoming calendar events within 10 minutes"""
        try:
            creds = self.oauth_handler.get_valid_credentials(tokens)
            service = build('calendar', 'v3', credentials=creds)
            
            # Get current time and 10 minutes from now
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(minutes=10)).isoformat() + 'Z'
            
            # Get events from primary calendar
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return len(events) > 0
            
        except Exception as e:
            print(f"Error checking calendar events: {e}")
            return False

class YouTubeService:
    def __init__(self, oauth_handler: GoogleOAuthHandler):
        self.oauth_handler = oauth_handler
    
    async def get_subscriber_count(self, tokens: Dict[str, Any]) -> Optional[int]:
        """Get current subscriber count"""
        try:
            creds = self.oauth_handler.get_valid_credentials(tokens)
            service = build('youtube', 'v3', credentials=creds)
            
            # Get channel statistics
            request = service.channels().list(
                part='statistics',
                mine=True
            )
            response = request.execute()
            
            if response['items']:
                stats = response['items'][0]['statistics']
                return int(stats.get('subscriberCount', 0))
            
            return None
            
        except Exception as e:
            print(f"Error getting YouTube subscriber count: {e}")
            return None
    
    async def check_new_subscriber(self, tokens: Dict[str, Any], last_count: int) -> Optional[int]:
        """Check if there are new subscribers"""
        current_count = await self.get_subscriber_count(tokens)
        if current_count and current_count > last_count:
            return current_count
        return None

class StripeOAuthHandler:
    def __init__(self):
        self.client_id = os.getenv("STRIPE_CLIENT_ID")
        self.client_secret = os.getenv("STRIPE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("APP_BASE_URL", "http://localhost:8000") + "/oauth/stripe/callback"
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for Stripe access tokens"""
        token_url = "https://connect.stripe.com/oauth/token"
        
        data = {
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code"
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to exchange Stripe code for tokens: {response.text}")

class StripeWebhookService:
    def __init__(self):
        self.client = stripe
    
    def setup_webhook_endpoint(self, tokens: Dict[str, Any], endpoint_url: str) -> Dict[str, Any]:
        """Set up webhook endpoint for the connected Stripe account"""
        try:
            # Use the connected account's access token
            self.client.api_key = tokens.get("access_token")
            
            webhook = self.client.WebhookEndpoint.create(
                url=endpoint_url,
                enabled_events=[
                    'payment_intent.succeeded',
                    'checkout.session.completed',
                    'invoice.payment_succeeded'
                ]
            )
            
            return {
                "webhook_id": webhook.id,
                "webhook_secret": webhook.secret,
                "url": webhook.url
            }
            
        except Exception as e:
            print(f"Error setting up Stripe webhook: {e}")
            raise e

# Global service instances
google_oauth = GoogleOAuthHandler()
google_calendar = GoogleCalendarService(google_oauth)
youtube_service = YouTubeService(google_oauth)
stripe_oauth = StripeOAuthHandler()
stripe_webhook_service = StripeWebhookService() 