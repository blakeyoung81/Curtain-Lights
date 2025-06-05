import os
import requests
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Rate limiting: max 10 requests per minute
class RateLimiter:
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = datetime.now()
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < timedelta(seconds=self.time_window)]
        
        if len(self.requests) >= self.max_requests:
            # Wait until the oldest request is outside the window
            wait_time = self.time_window - (now - self.requests[0]).total_seconds()
            if wait_time > 0:
                import time
                time.sleep(wait_time)
                # Clean up again after waiting
                now = datetime.now()
                self.requests = [req_time for req_time in self.requests 
                               if now - req_time < timedelta(seconds=self.time_window)]
        
        self.requests.append(now)

# Global rate limiter instance
rate_limiter = RateLimiter()

def get_govee_credentials():
    """Get Govee credentials from environment"""
    load_dotenv()  # Reload each time to get fresh values
    api_key = os.getenv("GOVEE_API_KEY")
    device_id = os.getenv("GOVEE_DEVICE_ID")
    model = os.getenv("GOVEE_MODEL")
    
    print(f"DEBUG: API Key: {'***' + api_key[-4:] if api_key else 'NOT_SET'}")
    print(f"DEBUG: Device ID: {device_id}")
    print(f"DEBUG: Model: {model}")
    
    return api_key, device_id, model

async def get_devices() -> List[Dict[str, Any]]:
    """
    Get list of available Govee devices
    Returns list of device dictionaries
    """
    api_key, _, _ = get_govee_credentials()
    
    if not api_key:
        print("Missing Govee API key in environment variables")
        return []
    
    # Apply rate limiting
    rate_limiter.wait_if_needed()
    
    url = "https://developer-api.govee.com/v1/devices"
    headers = {
        "Govee-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            devices = data.get("data", {}).get("devices", [])
            print(f"Found {len(devices)} Govee devices")
            return devices
        else:
            print(f"Govee API error {response.status_code}: {response.text}")
            return []
    
    except Exception as e:
        print(f"Error calling Govee API: {e}")
        return []

async def test_device_connection(command: str, value: Any) -> bool:
    """
    Test device connection with a specific command
    Returns True if successful, False otherwise
    """
    api_key, device_id, model = get_govee_credentials()
    
    if not all([api_key, device_id, model]):
        print(f"Missing Govee credentials: API Key: {bool(api_key)}, Device ID: {bool(device_id)}, Model: {bool(model)}")
        return False
    
    # Apply rate limiting
    rate_limiter.wait_if_needed()
    
    url = "https://developer-api.govee.com/v1/devices/control"
    headers = {
        "Govee-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "device": device_id,
        "model": model,
        "cmd": {
            "name": command,
            "value": value
        }
    }
    
    print(f"Sending command to Govee: {command} = {value}")
    print(f"Device: {device_id}, Model: {model}")
    
    try:
        response = requests.put(url, json=payload, headers=headers, timeout=10)
        print(f"Govee API response ({response.status_code}): {response.text}")
        
        if response.status_code == 200:
            print(f"Successfully sent {command}:{value} to device")
            return True
        else:
            print(f"Govee API error {response.status_code}: {response.text}")
            return False
    
    except Exception as e:
        print(f"Error calling Govee API: {e}")
        return False

async def set_scene(scene_id: int) -> bool:
    """
    Set Govee curtain light to a specific scene
    Note: H70B1 doesn't support scene command, use set_color instead
    """
    print(f"Warning: H70B1 model doesn't support scene command. Scene ID {scene_id} ignored.")
    return False

async def set_color(r: int, g: int, b: int) -> bool:
    """
    Set Govee light to a specific RGB color
    Returns True if successful, False otherwise
    """
    color_value = {"r": r, "g": g, "b": b}
    return await test_device_connection("color", color_value)

async def set_brightness(brightness: int) -> bool:
    """
    Set Govee light brightness (0-100)
    Returns True if successful, False otherwise
    """
    if not 0 <= brightness <= 100:
        print("Brightness must be between 0 and 100")
        return False
    
    return await test_device_connection("brightness", brightness)

async def test_govee_connection() -> bool:
    """Test Govee API connection"""
    api_key, _, _ = get_govee_credentials()
    
    if not api_key:
        return False
    
    url = "https://developer-api.govee.com/v1/devices"
    headers = {
        "Govee-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.status_code == 200
    except Exception:
        return False 