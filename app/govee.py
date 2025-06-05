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

async def red_youtube_celebration(duration: int = 5) -> bool:
    """Quick red flash celebration for new YouTube subscribers"""
    try:
        print("🔴 Starting red YouTube subscriber celebration!")
        
        # Flash pattern: red -> off -> red -> off -> red
        # Flash 1
        await set_color(255, 0, 0)  # Bright red
        await asyncio.sleep(0.8)
        await test_device_connection("turn", "off")
        await asyncio.sleep(0.3)
        
        # Flash 2
        await set_color(255, 0, 0)  # Bright red
        await asyncio.sleep(0.8)
        await test_device_connection("turn", "off")
        await asyncio.sleep(0.3)
        
        # Flash 3 (longer)
        await set_color(255, 0, 0)  # Bright red
        await asyncio.sleep(duration - 2.2)  # Remaining time
        
        # Turn off
        await test_device_connection("turn", "off")
        
        print("✅ Red YouTube celebration completed!")
        return True
    except Exception as e:
        print(f"❌ Error in red YouTube celebration: {e}")
        return False

async def play_animated_celebration(animation_path: str, repeat_count: int = 1) -> bool:
    """
    Play an animated GIF celebration by cycling through frames
    
    Args:
        animation_path: Path to the animation JSON file
        repeat_count: Number of times to repeat the animation
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import json
        import asyncio
        
        # Load animation data
        if not os.path.exists(animation_path):
            print(f"Animation file not found: {animation_path}")
            return False
        
        with open(animation_path, 'r') as f:
            animation_data = json.load(f)
        
        if not animation_data.get("is_animated", False):
            print("Not an animated file, using first frame only")
            frames = animation_data.get("frames", [])
            if frames:
                frame = frames[0]
                color_grid = frame.get("color_grid", [])
                if color_grid:
                    # Display single frame for 3 seconds
                    await display_color_grid(color_grid)
                    await asyncio.sleep(3)
                    return True
            return False
        
        frames = animation_data.get("frames", [])
        if not frames:
            print("No frames found in animation")
            return False
        
        print(f"🎬 Playing animated celebration: {len(frames)} frames, {repeat_count} repeat(s)")
        
        for repeat in range(repeat_count):
            for frame in frames:
                color_grid = frame.get("color_grid", [])
                duration_ms = frame.get("duration_ms", 100)
                
                if color_grid:
                    # Display this frame
                    await display_color_grid(color_grid)
                    
                    # Wait for frame duration (convert ms to seconds)
                    await asyncio.sleep(duration_ms / 1000.0)
        
        # Turn off lights after animation
        await test_device_connection("turn", "off")
        print("🎬 Animated celebration completed!")
        return True
        
    except Exception as e:
        print(f"Error playing animated celebration: {e}")
        return False

async def display_color_grid(color_grid: list) -> bool:
    """
    Display a color grid on the LED device
    
    Args:
        color_grid: 2D array of color objects with r, g, b values
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not color_grid or not color_grid[0]:
            return False
        
        # For now, use the dominant color from the grid
        # In the future, this could be enhanced to display the actual grid
        # if the Govee device supports pixel-level control
        
        # Calculate average color from the grid
        total_r, total_g, total_b = 0, 0, 0
        pixel_count = 0
        
        for row in color_grid:
            for pixel in row:
                total_r += pixel.get('r', 0)
                total_g += pixel.get('g', 0)
                total_b += pixel.get('b', 0)
                pixel_count += 1
        
        if pixel_count > 0:
            avg_r = total_r // pixel_count
            avg_g = total_g // pixel_count
            avg_b = total_b // pixel_count
            
            # Set the average color
            return await set_color(avg_r, avg_g, avg_b)
        
        return False
        
    except Exception as e:
        print(f"Error displaying color grid: {e}")
        return False 