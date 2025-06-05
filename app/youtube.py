import os
import aiohttp
from typing import Optional

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