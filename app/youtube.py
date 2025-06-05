import os
import aiohttp
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeMonitor:
    def __init__(self):
        self.youtube_service = None
        self.last_subscriber_count = 0
        self.monitoring_active = False
        self.channel_id = None
        
    def initialize_service(self) -> bool:
        """Initialize YouTube API service using service account credentials"""
        try:
            # Try service account first (for production)
            if os.getenv('GOOGLE_CLIENT_EMAIL') and os.getenv('GOOGLE_PRIVATE_KEY'):
                private_key = os.getenv('GOOGLE_PRIVATE_KEY').replace('\\n', '\n')
                service_account_info = {
                    "type": "service_account",
                    "client_email": os.getenv('GOOGLE_CLIENT_EMAIL'),
                    "private_key": private_key,
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
                
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info,
                    scopes=['https://www.googleapis.com/auth/youtube.readonly']
                )
                
                self.youtube_service = build('youtube', 'v3', credentials=credentials)
                logger.info("YouTube service initialized with service account")
                return True
                
            # Fall back to API key
            elif os.getenv('YT_API_KEY'):
                self.youtube_service = build('youtube', 'v3', developerKey=os.getenv('YT_API_KEY'))
                logger.info("YouTube service initialized with API key")
                return True
                
            else:
                logger.error("No YouTube credentials found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize YouTube service: {str(e)}")
            return False

    async def get_channel_stats(self, channel_id: str) -> Dict:
        """Get current channel statistics"""
        if not self.youtube_service:
            if not self.initialize_service():
                return {"error": "YouTube service not initialized"}
        
        try:
            request = self.youtube_service.channels().list(
                part='statistics,snippet',
                id=channel_id
            )
            response = request.execute()
            
            if not response['items']:
                return {"error": "Channel not found"}
            
            channel = response['items'][0]
            stats = channel['statistics']
            
            return {
                "channel_id": channel_id,
                "channel_title": channel['snippet']['title'],
                "subscriber_count": int(stats.get('subscriberCount', 0)),
                "view_count": int(stats.get('viewCount', 0)),
                "video_count": int(stats.get('videoCount', 0)),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting channel stats: {str(e)}")
            return {"error": str(e)}

    async def check_for_new_subscribers(self, channel_id: str) -> Dict:
        """Check for any new subscribers since last check (for red light celebrations)"""
        current_stats = await self.get_channel_stats(channel_id)
        
        if "error" in current_stats:
            return current_stats
        
        current_count = current_stats["subscriber_count"]
        previous_count = self.last_subscriber_count
        
        # Update stored count
        self.last_subscriber_count = current_count
        
        # Check for any new subscribers
        new_subscribers = max(0, current_count - previous_count)
        
        result = {
            "current_subscribers": current_count,
            "previous_subscribers": previous_count,
            "new_subscribers": new_subscribers,
            "has_new_subscribers": new_subscribers > 0,
            "timestamp": datetime.now().isoformat()
        }
        
        return result

    async def check_subscriber_milestone(self, channel_id: str) -> Dict:
        """Check if subscriber count hit a milestone worth celebrating"""
        current_stats = await self.get_channel_stats(channel_id)
        
        if "error" in current_stats:
            return current_stats
        
        current_count = current_stats["subscriber_count"]
        previous_count = self.last_subscriber_count
        
        # Don't update count here since check_for_new_subscribers() already did it
        
        # Check for milestones
        milestone_reached = None
        celebration_amount = 0
        
        # Define milestone thresholds and their "payment equivalent" for celebrations
        milestones = [
            (1000000, 500),    # 1M subs = $500 celebration  
            (500000, 200),     # 500K subs = $200 celebration
            (100000, 100),     # 100K subs = $100 celebration
            (50000, 75),       # 50K subs = $75 celebration
            (10000, 50),       # 10K subs = $50 celebration
            (5000, 25),        # 5K subs = $25 celebration
            (1000, 15),        # 1K subs = $15 celebration
            (500, 10),         # 500 subs = $10 celebration
            (100, 5),          # 100 subs = $5 celebration
        ]
        
        # Check if we crossed a milestone
        for threshold, amount in milestones:
            if current_count >= threshold and previous_count < threshold:
                milestone_reached = threshold
                celebration_amount = amount
                break
        
        # Also celebrate every 1000 subscribers after 10K
        if current_count >= 10000 and previous_count < current_count:
            # Check for every 1000 milestone
            current_thousands = current_count // 1000
            previous_thousands = previous_count // 1000
            
            if current_thousands > previous_thousands:
                milestone_reached = current_thousands * 1000
                celebration_amount = 50  # $50 equivalent for each 1K milestone
        
        result = {
            "current_subscribers": current_count,
            "previous_subscribers": previous_count,
            "subscriber_gain": current_count - previous_count,
            "milestone_reached": milestone_reached,
            "celebration_amount": celebration_amount,
            "should_celebrate": milestone_reached is not None,
            "timestamp": datetime.now().isoformat()
        }
        
        return result

    async def start_monitoring(self, channel_id: str, check_interval: int = 300) -> Dict:
        """Start monitoring channel for subscriber milestones"""
        self.channel_id = channel_id
        self.monitoring_active = True
        
        # Get initial count
        initial_stats = await self.get_channel_stats(channel_id)
        if "error" in initial_stats:
            return initial_stats
        
        self.last_subscriber_count = initial_stats["subscriber_count"]
        
        logger.info(f"Started monitoring channel {channel_id} with {self.last_subscriber_count} subscribers")
        
        return {
            "status": "monitoring_started",
            "channel_id": channel_id,
            "initial_subscriber_count": self.last_subscriber_count,
            "check_interval_seconds": check_interval
        }

    def stop_monitoring(self) -> Dict:
        """Stop monitoring"""
        self.monitoring_active = False
        return {
            "status": "monitoring_stopped",
            "final_subscriber_count": self.last_subscriber_count
        }

    async def get_monitoring_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            "monitoring_active": self.monitoring_active,
            "channel_id": self.channel_id,
            "last_subscriber_count": self.last_subscriber_count,
            "service_initialized": self.youtube_service is not None
        }

# Global instance
youtube_monitor = YouTubeMonitor()

# Async function for periodic checking (to be called by background task)
async def check_subscriber_milestones_task():
    """Background task to check for subscriber milestones"""
    if not youtube_monitor.monitoring_active or not youtube_monitor.channel_id:
        return None
    
    milestone_check = await youtube_monitor.check_subscriber_milestone(youtube_monitor.channel_id)
    
    if milestone_check.get("should_celebrate"):
        logger.info(f"🎉 Milestone reached! {milestone_check['milestone_reached']} subscribers!")
        # This would trigger the payment interrupt system
        return {
            "milestone": milestone_check["milestone_reached"],
            "celebration_amount": milestone_check["celebration_amount"],
            "type": "subscriber_milestone"
        }
    
    return None

async def check_new_subscriber() -> Optional[str]:
    """
    Check YouTube Data API for new subscribers
    Returns the subscriber ID if found, None otherwise
    """
    api_key = os.getenv("YT_API_KEY")
    
    if not api_key:
        print("Missing YouTube API key in environment variables")
        return None
    
    url = "https://www.googleapis.com/youtube/v3/subscriptions"
    params = {
        "part": "snippet",
        "mySubscribers": "true",
        "maxResults": 1,
        "order": "alphabetical",
        "key": api_key
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    
                    if items:
                        # Return the channel ID of the first subscriber
                        subscriber_id = items[0]["snippet"]["resourceId"]["channelId"]
                        return subscriber_id
                    else:
                        return None
                else:
                    error_text = await response.text()
                    print(f"YouTube API error {response.status}: {error_text}")
                    return None
    
    except Exception as e:
        print(f"Error calling YouTube API: {e}")
        return None

async def get_channel_info() -> Optional[dict]:
    """
    Get basic channel information for debugging
    """
    api_key = os.getenv("YT_API_KEY")
    
    if not api_key:
        return None
    
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "snippet,statistics",
        "mine": "true",
        "key": api_key
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    print(f"YouTube API error {response.status}: {await response.text()}")
                    return None
    
    except Exception as e:
        print(f"Error calling YouTube API: {e}")
        return None 