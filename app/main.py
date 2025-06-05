# Curtain Lights API - Updated 2024-12-05
# Fixed authentication issues for all test endpoints

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
import json
import os
import stripe
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
import secrets
from dotenv import load_dotenv
from PIL import Image
import io
import base64
from pathlib import Path
import requests

# Govee API configuration - Add these at the top after the imports
GOVEE_API_KEY = "846814e4-67ec-4398-ae9b-453d741b56cd"
GOVEE_DEVICE_ID = "1A:67:F3:96:2E:A2:43:DF"
GOVEE_MODEL = "H70B1"
GOVEE_BASE_URL = "https://openapi.api.govee.com"

# DIY Scene IDs
DIY_SCENES = {
    "money": 16158674,    # Your "Money" DIY scene for Stripe payments
    "youtube": 16158613,  # Your "YouTube" DIY scene for YouTube events
    "goal": 16160444      # Your "Goal" DIY scene for milestone goals
}

async def get_current_light_state():
    """Get the current state of the lights"""
    headers = {
        "Govee-API-Key": GOVEE_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "requestId": f"get-state-{datetime.now().isoformat()}",
        "payload": {
            "sku": GOVEE_MODEL,
            "device": GOVEE_DEVICE_ID
        }
    }
    
    try:
        response = requests.post(
            f"{GOVEE_BASE_URL}/router/api/v1/device/state",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 200:
                return result.get("payload", {})
        return None
            
    except requests.RequestException:
        return None

async def restore_light_state(previous_state):
    """Restore the lights to their previous state (basic settings only)"""
    if not previous_state or not previous_state.get("capabilities"):
        return
    
    headers = {
        "Govee-API-Key": GOVEE_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Extract key state information
    capabilities = previous_state["capabilities"]
    
    # Find the relevant state values
    power_state = None
    brightness = None
    color = None
    
    for cap in capabilities:
        if cap.get("type") == "devices.capabilities.on_off" and cap.get("instance") == "powerSwitch":
            power_state = cap.get("state", {}).get("value")
        elif cap.get("type") == "devices.capabilities.range" and cap.get("instance") == "brightness":
            brightness = cap.get("state", {}).get("value")
        elif cap.get("type") == "devices.capabilities.color_setting" and cap.get("instance") == "colorRgb":
            color = cap.get("state", {}).get("value")
    
    print(f"🔄 Restoring light state: power={power_state}, brightness={brightness}, color={color}")
    
    # Only restore if we're not currently in a DIY scene
    # First, clear any active scenes
    try:
        await asyncio.sleep(1)
        clear_payload = {
            "requestId": f"clear-scenes-{datetime.now().isoformat()}",
            "payload": {
                "sku": GOVEE_MODEL,
                "device": GOVEE_DEVICE_ID,
                "capability": {
                    "type": "devices.capabilities.dynamic_scene",
                    "instance": "diyScene",
                    "value": ""
                }
            }
        }
        requests.post(f"{GOVEE_BASE_URL}/router/api/v1/device/control", headers=headers, json=clear_payload, timeout=5)
        print("🧹 Cleared DIY scenes")
    except Exception as e:
        print(f"⚠️ Failed to clear scenes: {e}")
    
    # Restore power state if it was on
    if power_state == 1:
        try:
            await asyncio.sleep(0.5)
            payload = {
                "requestId": f"restore-power-{datetime.now().isoformat()}",
                "payload": {
                    "sku": GOVEE_MODEL,
                    "device": GOVEE_DEVICE_ID,
                    "capability": {
                        "type": "devices.capabilities.on_off",
                        "instance": "powerSwitch",
                        "value": 1
                    }
                }
            }
            requests.post(f"{GOVEE_BASE_URL}/router/api/v1/device/control", headers=headers, json=payload, timeout=5)
            print("🔌 Restored power state")
        except Exception as e:
            print(f"⚠️ Failed to restore power: {e}")
    
    # Restore brightness
    if brightness is not None and brightness > 0:
        try:
            await asyncio.sleep(0.5)
            payload = {
                "requestId": f"restore-brightness-{datetime.now().isoformat()}",
                "payload": {
                    "sku": GOVEE_MODEL,
                    "device": GOVEE_DEVICE_ID,
                    "capability": {
                        "type": "devices.capabilities.range",
                        "instance": "brightness",
                        "value": brightness
                    }
                }
            }
            requests.post(f"{GOVEE_BASE_URL}/router/api/v1/device/control", headers=headers, json=payload, timeout=5)
            print(f"💡 Restored brightness to {brightness}")
        except Exception as e:
            print(f"⚠️ Failed to restore brightness: {e}")
    
    # Restore color (only if it's a basic color, not white/0)
    if color is not None and color != 0 and color != 16777215:  # Not black or white
        try:
            await asyncio.sleep(0.5)
            payload = {
                "requestId": f"restore-color-{datetime.now().isoformat()}",
                "payload": {
                    "sku": GOVEE_MODEL,
                    "device": GOVEE_DEVICE_ID,
                    "capability": {
                        "type": "devices.capabilities.color_setting",
                        "instance": "colorRgb",
                        "value": color
                    }
                }
            }
            requests.post(f"{GOVEE_BASE_URL}/router/api/v1/device/control", headers=headers, json=payload, timeout=5)
            print(f"🎨 Restored color to {color}")
        except Exception as e:
            print(f"⚠️ Failed to restore color: {e}")
    
    print("✅ State restoration complete")

async def trigger_diy_scene(scene_name: str, restore_after_seconds: int = 5):
    """Trigger a specific DIY scene by name, then restore previous state"""
    if scene_name not in DIY_SCENES:
        raise HTTPException(status_code=400, detail=f"Unknown DIY scene: {scene_name}")
    
    scene_id = DIY_SCENES[scene_name]
    print(f"🎬 Triggering DIY scene '{scene_name}' (ID: {scene_id})")
    
    # Get current state before changing anything
    previous_state = await get_current_light_state()
    print(f"💾 Saved current state for restoration in {restore_after_seconds} seconds")
    
    headers = {
        "Govee-API-Key": GOVEE_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "requestId": f"diy-trigger-{scene_name}-{datetime.now().isoformat()}",
        "payload": {
            "sku": GOVEE_MODEL,
            "device": GOVEE_DEVICE_ID,
            "capability": {
                "type": "devices.capabilities.dynamic_scene",
                "instance": "diyScene",
                "value": scene_id
            }
        }
    }
    
    try:
        response = requests.post(
            f"{GOVEE_BASE_URL}/router/api/v1/device/control",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 200:
                print(f"✅ DIY scene '{scene_name}' triggered successfully")
                # Schedule restoration of previous state
                asyncio.create_task(restore_after_delay(previous_state, restore_after_seconds))
                print(f"⏰ Scheduled state restoration in {restore_after_seconds} seconds")
                return {"status": "success", "scene": scene_name, "scene_id": scene_id}
            else:
                raise HTTPException(status_code=500, detail=f"Govee API error: {result.get('msg', 'Unknown error')}")
        else:
            raise HTTPException(status_code=500, detail=f"HTTP error: {response.status_code}")
            
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")

async def restore_after_delay(previous_state, delay_seconds):
    """Wait for the specified delay, then restore the previous state"""
    print(f"⏳ Waiting {delay_seconds} seconds before restoring state...")
    await asyncio.sleep(delay_seconds)
    print("🔄 Starting state restoration...")
    await restore_light_state(previous_state)

# Load environment variables
load_dotenv()

from .govee import set_scene, get_devices, test_device_connection, set_color, red_youtube_celebration, play_celebration_with_text
from .auth import auth_manager, get_current_user, get_google_oauth_url, get_stripe_oauth_url
from .oauth_integrations import google_oauth, google_calendar, youtube_service, stripe_oauth
from .payment_interrupts import payment_interrupt_manager
from .youtube import youtube_monitor, check_subscriber_milestones_task

app = FastAPI(title="Gotham Lights", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories for storing images if they don't exist
# This needs to happen BEFORE mounting the static directory
os.makedirs("static", exist_ok=True)
os.makedirs("static/images/payment", exist_ok=True)
os.makedirs("static/images/youtube", exist_ok=True)

# Mount static files for serving uploaded images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load environment variables
stripe.api_key = os.getenv("STRIPE_SK")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Global variable to track monitoring task
youtube_monitoring_task = None

@app.on_event("startup")
async def startup_event():
    """Start background tasks when the application starts"""
    global youtube_monitoring_task
    
    # Start YouTube monitoring automatically if channel ID is configured
    youtube_channel_id = os.getenv("YOUTUBE_CHANNEL_ID")
    if youtube_channel_id:
        print(f"🎬 Starting automatic YouTube monitoring for channel: {youtube_channel_id}")
        
        # Initialize the monitor with quota-optimized interval
        await youtube_monitor.start_monitoring(youtube_channel_id, check_interval=1800)  # Check every 30 minutes
        
        # Start the background monitoring task
        youtube_monitoring_task = asyncio.create_task(check_subscriber_milestones_task())
        print("✅ YouTube monitoring started successfully!")
        print("💡 Quota-optimized: ~48 API calls/day (30-minute intervals)")
    else:
        print("⚠️ No YOUTUBE_CHANNEL_ID found in environment variables")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up background tasks when the application shuts down"""
    global youtube_monitoring_task
    
    if youtube_monitoring_task:
        youtube_monitoring_task.cancel()
        try:
            await youtube_monitoring_task
        except asyncio.CancelledError:
            pass
        print("🛑 YouTube monitoring stopped")

# Predefined color patterns for different "scenes"
COLOR_PATTERNS = {
    0: {"r": 255, "g": 255, "b": 255},  # White (default/off)
    1: {"r": 255, "g": 0, "b": 0},      # Red
    2: {"r": 0, "g": 255, "b": 0},      # Green  
    3: {"r": 0, "g": 0, "b": 255},      # Blue
    4: {"r": 255, "g": 255, "b": 0},    # Yellow
    5: {"r": 255, "g": 0, "b": 255},    # Magenta
    6: {"r": 0, "g": 255, "b": 255},    # Cyan
    7: {"r": 255, "g": 165, "b": 0},    # Orange
    8: {"r": 128, "g": 0, "b": 128},    # Purple
    9: {"r": 255, "g": 192, "b": 203},  # Pink
    10: {"r": 255, "g": 20, "b": 147}   # Deep Pink
}

# Data models
class UserRegistration(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class SceneConfig(BaseModel):
    stripe: int
    calendar: int
    youtube: int

class DeviceSettings(BaseModel):
    device_id: str
    model: str
    name: str

class TestLightRequest(BaseModel):
    action: str  # "on", "off", "color", "scene"
    value: Optional[Any] = None

class ImageConfig(BaseModel):
    celebration_type: str  # "payment", "youtube"
    image_path: str

# Image processing functions
def process_image_for_lights(image_file: bytes, max_width: int = 14, max_height: int = 20) -> Image.Image:
    """
    Process uploaded image for LED display:
    - Resize to LED grid dimensions (recommended: 64x64 or smaller)
    - Enhance contrast and saturation for better LED visibility
    - Save as optimized format
    Returns the processed PIL Image
    """
    try:
        # Open image from bytes
        image = Image.open(io.BytesIO(image_file))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize while maintaining aspect ratio
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Enhance for LED display
        from PIL import ImageEnhance
        
        # Increase contrast for better LED visibility
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.3)
        
        # Increase saturation for more vibrant colors
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.4)
        
        # Increase brightness slightly
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.1)
        
        return image
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

def process_gif_for_lights(image_file: bytes, max_width: int = 14, max_height: int = 20) -> Dict:
    """
    Process animated GIF for LED display:
    - Extract all frames from the GIF
    - Resize and enhance each frame for LED visibility
    - Return frame data with timing information
    """
    try:
        # Open GIF from bytes
        gif = Image.open(io.BytesIO(image_file))
        
        if not getattr(gif, "is_animated", False):
            # Not an animated GIF, treat as static image
            processed_image = process_image_for_lights(image_file, max_width, max_height)
            return {
                "is_animated": False,
                "frame_count": 1,
                "frames": [processed_image],
                "durations": [100]  # 100ms default
            }
        
        frames = []
        durations = []
        
        # Extract all frames
        for frame_index in range(gif.n_frames):
            gif.seek(frame_index)
            
            # Get frame duration (in milliseconds)
            duration = gif.info.get('duration', 100)  # Default 100ms if not specified
            durations.append(max(duration, 50))  # Minimum 50ms for LED visibility
            
            # Convert frame to RGB
            frame = gif.convert('RGB')
            
            # Resize while maintaining aspect ratio
            frame.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Enhance for LED display
            from PIL import ImageEnhance
            
            # Increase contrast
            enhancer = ImageEnhance.Contrast(frame)
            frame = enhancer.enhance(1.3)
            
            # Increase saturation
            enhancer = ImageEnhance.Color(frame)
            frame = enhancer.enhance(1.4)
            
            # Increase brightness
            enhancer = ImageEnhance.Brightness(frame)
            frame = enhancer.enhance(1.1)
            
            frames.append(frame)
        
        return {
            "is_animated": True,
            "frame_count": len(frames),
            "frames": frames,
            "durations": durations,
            "total_duration": sum(durations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing GIF: {str(e)}")

def image_to_color_grid(image: Image.Image) -> List[List[Dict[str, int]]]:
    """Convert processed image to a grid of RGB color values for LED display"""
    width, height = image.size
    color_grid = []
    
    for y in range(height):
        row = []
        for x in range(width):
            r, g, b = image.getpixel((x, y))
            row.append({"r": r, "g": g, "b": b})
        color_grid.append(row)
    
    return color_grid

def frames_to_animation_data(frames: List[Image.Image], durations: List[int]) -> List[Dict]:
    """Convert list of frames to animation data with color grids and timing"""
    animation_frames = []
    
    for i, (frame, duration) in enumerate(zip(frames, durations)):
        color_grid = image_to_color_grid(frame)
        animation_frames.append({
            "frame_index": i,
            "duration_ms": duration,
            "color_grid": color_grid,
            "dimensions": f"{frame.width}x{frame.height}"
        })
    
    return animation_frames

# OAuth state management
oauth_states = {}

# Image upload endpoints
@app.post("/upload/celebration-image")
async def upload_celebration_image(
    celebration_type: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload and process a custom image for celebrations
    
    celebration_type options:
    - payment_mini: $0-19 payments
    - payment_standard: $20-49 payments  
    - payment_major: $50-99 payments
    - payment_premium: $100+ payments
    - youtube_subscriber: New subscriber celebrations
    - youtube_milestone: Milestone celebrations
    """
    
    # Validate celebration type
    valid_types = ["payment", "youtube"]
    
    if celebration_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid celebration type. Must be one of: {valid_types}")
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read file content
        image_content = await file.read()
        
        # Check if it's a GIF
        is_gif = file.content_type == 'image/gif' or file.filename.lower().endswith('.gif')
        
        if is_gif:
            # Process GIF for LED display
            gif_data = process_gif_for_lights(image_content)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"{celebration_type}_{timestamp}"
            
            # Determine directory based on type
            directory = f"static/images/{celebration_type}"
            
            # Save first frame as preview image
            preview_path = os.path.join(directory, f"{base_filename}_preview.png")
            gif_data["frames"][0].save(preview_path, "PNG", optimize=True)
            
            # Convert frames to animation data
            animation_data = frames_to_animation_data(gif_data["frames"], gif_data["durations"])
            
            # Save animation data as JSON
            animation_path = os.path.join(directory, f"{base_filename}_animation.json")
            with open(animation_path, 'w') as f:
                json.dump({
                    "is_animated": gif_data["is_animated"],
                    "frame_count": gif_data["frame_count"],
                    "total_duration_ms": gif_data.get("total_duration", sum(gif_data["durations"])),
                    "frames": animation_data
                }, f, indent=2)
            
            # Update configuration
            config_path = "static/images/config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            first_frame = gif_data["frames"][0]
            config[celebration_type] = {
                "image_path": preview_path,
                "animation_path": animation_path,
                "is_animated": gif_data["is_animated"],
                "frame_count": gif_data["frame_count"],
                "total_duration_ms": gif_data.get("total_duration", sum(gif_data["durations"])),
                "uploaded_at": datetime.now().isoformat(),
                "original_filename": file.filename,
                "dimensions": f"{first_frame.width}x{first_frame.height}"
            }
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            return {
                "status": "success",
                "message": f"{'Animated GIF' if gif_data['is_animated'] else 'Static image'} uploaded and processed for {celebration_type}",
                "celebration_type": celebration_type,
                "file_type": "animated_gif" if gif_data["is_animated"] else "static_image",
                "is_animated": gif_data["is_animated"],
                "frame_count": gif_data["frame_count"],
                "total_duration": f"{gif_data.get('total_duration', 0)}ms",
                "dimensions": f"{first_frame.width}x{first_frame.height}",
                "preview_path": preview_path,
                "animation_path": animation_path if gif_data["is_animated"] else None,
                "recommendations": {
                    "optimal_dimensions": "64x64 pixels or smaller",
                    "best_gif_types": ["Simple animations", "2-10 frames", "High contrast", "Bold colors"],
                    "avoid": ["Complex animations", "Too many frames (>20)", "Very fast animations (<50ms per frame)"]
                }
            }
        
        else:
            # Process static image for LED display
            processed_image = process_image_for_lights(image_content)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{celebration_type}_{timestamp}.png"
            
            # Determine directory based on type  
            directory = f"static/images/{celebration_type}"
            
            file_path = os.path.join(directory, filename)
            
            # Save processed image
            processed_image.save(file_path, "PNG", optimize=True)
            
            # Convert to color grid for LED display
            color_grid = image_to_color_grid(processed_image)
            
            # Save color grid as JSON for fast loading
            grid_path = file_path.replace('.png', '_grid.json')
            with open(grid_path, 'w') as f:
                json.dump(color_grid, f)
            
            # Update configuration to use this image
            config_path = "static/images/config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            config[celebration_type] = {
                "image_path": file_path,
                "grid_path": grid_path,
                "is_animated": False,
                "uploaded_at": datetime.now().isoformat(),
                "original_filename": file.filename,
                "dimensions": f"{processed_image.width}x{processed_image.height}"
            }
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            return {
                "status": "success",
                "message": f"Static image uploaded and processed for {celebration_type}",
                "celebration_type": celebration_type,
                "file_type": "static_image",
                "is_animated": False,
                "file_path": file_path,
                "dimensions": f"{processed_image.width}x{processed_image.height}",
                "grid_size": f"{len(color_grid)}x{len(color_grid[0]) if color_grid else 0}",
                "recommendations": {
                    "led_optimized": "Automatically resized to 14×20 pixels for Govee H70B1 (280 LEDs)",
                    "best_image_types": ["High contrast images", "Bold colors", "Simple designs", "Logos or icons"],
                    "avoid": ["Fine details", "Complex gradients", "Low contrast images", "Very small text"]
                }
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")

@app.get("/celebration-images")
async def get_celebration_images():
    """Get all uploaded celebration images and their configurations"""
    config_path = "static/images/config.json"
    
    if not os.path.exists(config_path):
        return {"images": {}, "message": "No custom images uploaded yet"}
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Add preview URLs
    for celebration_type, image_info in config.items():
        image_info["preview_url"] = f"/static/images/{image_info['image_path'].split('/')[-1]}"
    
    return {"images": config}

@app.delete("/celebration-images/{celebration_type}")
async def delete_celebration_image(celebration_type: str):
    """Delete a celebration image"""
    config_path = "static/images/config.json"
    
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail="No images found")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    if celebration_type not in config:
        raise HTTPException(status_code=404, detail=f"No image found for {celebration_type}")
    
    # Delete files
    image_info = config[celebration_type]
    try:
        if os.path.exists(image_info["image_path"]):
            os.remove(image_info["image_path"])
        if os.path.exists(image_info["grid_path"]):
            os.remove(image_info["grid_path"])
    except Exception as e:
        print(f"Error deleting files: {e}")
    
    # Remove from config
    del config[celebration_type]
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return {"status": "success", "message": f"Deleted image for {celebration_type}"}

@app.get("/images/preview/{celebration_type}")
async def get_image_preview(celebration_type: str):
    """Get both original and 14×20 LED preview of uploaded image"""
    try:
        config_file = "static/images/config.json"
        if not os.path.exists(config_file):
            raise HTTPException(status_code=404, detail="No images found")
            
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        if celebration_type not in config:
            raise HTTPException(status_code=404, detail=f"No image found for {celebration_type}")
        
        image_info = config[celebration_type]
        image_path = image_info["image_path"]
        
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image file not found")
        
        # Open and process the image
        with Image.open(image_path) as img:
            # Create 14×20 LED preview (scaled up for visibility)
            led_preview = img.resize((14, 20), Image.Resampling.NEAREST)
            
            # Scale up the 14×20 preview to 280×400 (20x scale) for visibility
            led_preview_large = led_preview.resize((280, 400), Image.Resampling.NEAREST)
            
            # Convert to base64 for web display
            import io
            import base64
            
            # Original image
            original_buffer = io.BytesIO()
            img.save(original_buffer, format='PNG')
            original_b64 = base64.b64encode(original_buffer.getvalue()).decode()
            
            # LED preview
            led_buffer = io.BytesIO()
            led_preview_large.save(led_buffer, format='PNG')
            led_b64 = base64.b64encode(led_buffer.getvalue()).decode()
            
            return {
                "celebration_type": celebration_type,
                "original_image": f"data:image/png;base64,{original_b64}",
                "led_preview": f"data:image/png;base64,{led_b64}",
                "led_dimensions": "14×20 pixels (for Govee H70B1)",
                "info": image_info
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")

# Authentication endpoints
@app.post("/auth/register")
async def register(user: UserRegistration):
    """Register a new user"""
    try:
        user_data = auth_manager.create_user(user.email, user.password, user.name)
        access_token = auth_manager.create_access_token({"sub": user.email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_data
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login")
async def login(user: UserLogin):
    """Login user"""
    user_data = auth_manager.authenticate_user(user.email, user.password)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = auth_manager.create_access_token({"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }

@app.get("/auth/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# OAuth endpoints
@app.get("/oauth/google/authorize")
async def google_oauth_authorize(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Start Google OAuth flow"""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"user_email": current_user["email"], "service": "google"}
    
    oauth_url = get_google_oauth_url(state)
    return {"oauth_url": oauth_url}

@app.get("/oauth/google/callback")
async def google_oauth_callback(code: str, state: str):
    """Handle Google OAuth callback"""
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    user_email = oauth_states[state]["user_email"]
    del oauth_states[state]  # Clean up state
    
    try:
        tokens = await google_oauth.exchange_code_for_tokens(code)
        auth_manager.update_oauth_tokens(user_email, "google", tokens)
        
        # Redirect to frontend with success
        return RedirectResponse(
            url=f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/settings?oauth=google&status=success"
        )
    except Exception as e:
        print(f"Error in Google OAuth callback: {e}")
        return RedirectResponse(
            url=f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/settings?oauth=google&status=error"
        )

@app.get("/oauth/stripe/authorize")
async def stripe_oauth_authorize(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Start Stripe OAuth flow"""
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"user_email": current_user["email"], "service": "stripe"}
    
    oauth_url = get_stripe_oauth_url(state)
    return {"oauth_url": oauth_url}

@app.get("/oauth/stripe/callback")
async def stripe_oauth_callback(code: str, state: str):
    """Handle Stripe OAuth callback"""
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    user_email = oauth_states[state]["user_email"]
    del oauth_states[state]  # Clean up state
    
    try:
        tokens = await stripe_oauth.exchange_code_for_tokens(code)
        auth_manager.update_oauth_tokens(user_email, "stripe", tokens)
        
        # Redirect to frontend with success
        return RedirectResponse(
            url=f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/settings?oauth=stripe&status=success"
        )
    except Exception as e:
        print(f"Error in Stripe OAuth callback: {e}")
        return RedirectResponse(
            url=f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/settings?oauth=stripe&status=error"
        )

@app.post("/stripe")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle Stripe webhook events - triggers payment celebration lights! 🎉"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # 🎉 PAYMENT CELEBRATION TRIGGER!
    if event["type"] in ["payment_intent.succeeded", "checkout.session.completed", "invoice.payment_succeeded"]:
        try:
            # Extract payment amount
            payment_amount = 0
            if event["type"] == "payment_intent.succeeded":
                payment_amount = event["data"]["object"]["amount"] / 100  # Convert cents to dollars
            elif event["type"] == "checkout.session.completed":
                payment_amount = event["data"]["object"]["amount_total"] / 100
            elif event["type"] == "invoice.payment_succeeded":
                payment_amount = event["data"]["object"]["amount_paid"] / 100
            
            print(f"💰 PAYMENT RECEIVED: ${payment_amount} - TRIGGERING CELEBRATION!")
            
            # 🎆 INTERRUPT WHATEVER IS HAPPENING AND CELEBRATE!
            background_tasks.add_task(
                payment_interrupt_manager.trigger_payment_celebration,
                payment_amount,
                "stripe"
            )
            
            print(f"🎉 Payment celebration queued for ${payment_amount}")
            
        except Exception as e:
            print(f"⚠️ Error processing payment celebration: {e}")
    
    return {"status": "success", "event_type": event.get("type", "unknown")}

@app.get("/cron")
async def cron_job(background_tasks: BackgroundTasks, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Idempotent poller for YouTube and Calendar events"""
    user_settings = auth_manager.get_user_settings(current_user["email"])
    
    try:
        # Check YouTube for new subscribers
        google_tokens = auth_manager.get_oauth_tokens(current_user["email"], "google")
        if google_tokens:
            last_count = user_settings.get("last_subscriber_count", 0)
            new_count = await youtube_service.check_new_subscriber(google_tokens, last_count)
            if new_count:
                user_settings["last_subscriber_count"] = new_count
                auth_manager.update_user_settings(current_user["email"], user_settings)
                background_tasks.add_task(trigger_diy_scene, "youtube")
                print(f"New YouTube subscriber detected for {current_user['email']}: {new_count}")
        
        # Check Google Calendar for upcoming events
        if google_tokens:
            has_upcoming = await google_calendar.check_upcoming_events(google_tokens)
            if has_upcoming:
                background_tasks.add_task(trigger_diy_scene, "money")
                print(f"Upcoming calendar event detected for {current_user['email']}")
            
    except Exception as e:
        print(f"Error in cron job for {current_user['email']}: {e}")
    
    return {
        "status": "success", 
        "timestamp": datetime.now().isoformat(),
        "user": current_user["email"]
    }

@app.get("/config/scene")
async def get_scene_config():
    """Get current scene configuration"""
    # Return default configuration for now since this is for testing
    return {"stripe": 1, "calendar": 2, "youtube": 3}

@app.put("/config/scene")
async def update_scene_config(config: SceneConfig):
    """Update scene configuration"""
    # For testing purposes, just return success
    # In a real app, this would save to the database
    return {"status": "success", "scenes": config.dict()}

@app.get("/devices")
async def get_available_devices(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get list of available Govee devices"""
    try:
        devices = await get_devices()
        return {"status": "success", "devices": devices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get devices: {str(e)}")

@app.get("/config/device")
async def get_device_config(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current device configuration for user"""
    user_settings = auth_manager.get_user_settings(current_user["email"])
    return user_settings.get("selected_device", {})

@app.put("/config/device")
async def update_device_config(device: DeviceSettings, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Update selected device configuration for user"""
    user_settings = auth_manager.get_user_settings(current_user["email"])
    user_settings["selected_device"] = device.dict()
    auth_manager.update_user_settings(current_user["email"], user_settings)
    return {"status": "success", "device": user_settings["selected_device"]}

@app.get("/color-patterns")
async def get_color_patterns():
    """Get available color patterns"""
    return {"patterns": COLOR_PATTERNS}

@app.get("/oauth/status")
async def get_oauth_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get OAuth connection status for user"""
    oauth_tokens = current_user.get("oauth_tokens", {})
    
    return {
        "google": {
            "connected": "google" in oauth_tokens,
            "services": ["calendar", "youtube"] if "google" in oauth_tokens else []
        },
        "stripe": {
            "connected": "stripe" in oauth_tokens
        }
    }

@app.post("/test/light")
async def test_light(request: TestLightRequest):
    """Test light controls"""
    try:
        print(f"Testing light: {request.action} with value {request.value}")
        if request.action == "on":
            success = await test_device_connection("turn", "on")
        elif request.action == "off":
            success = await test_device_connection("turn", "off")
        elif request.action == "color" and request.value:
            success = await test_device_connection("color", request.value)
        elif request.action == "scene" and request.value:
            # Use color pattern instead of scene
            scene_id = int(request.value)
            if scene_id in COLOR_PATTERNS:
                color = COLOR_PATTERNS[scene_id]
                success = await set_color(color["r"], color["g"], color["b"])
            else:
                raise HTTPException(status_code=400, detail=f"Invalid scene ID: {scene_id}")
        else:
            raise HTTPException(status_code=400, detail="Invalid action or missing value")
        
        if success:
            return {"status": "success", "message": f"Light {request.action} command sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to control light")
    except Exception as e:
        print(f"Error in test_light: {e}")
        raise HTTPException(status_code=500, detail=f"Error controlling light: {str(e)}")

# 🎉 Payment Interrupt Endpoints

@app.post("/test/payment")
async def test_payment_celebration(amount: float = 25.0):
    """Test payment celebration manually - triggers Money DIY scene"""
    try:
        result = await trigger_diy_scene("money")
        return {
            "status": "success", 
            "message": f"Payment celebration started for ${amount}",
            "celebration": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering celebration: {str(e)}")

@app.get("/payment/interrupt/status")
async def get_interrupt_status():
    """Get current payment interrupt status"""
    interrupt = payment_interrupt_manager.get_current_interrupt()
    return {
        "interrupt_active": interrupt is not None,
        "interrupt_details": interrupt
    }

@app.post("/payment/interrupt/stop")
async def stop_interrupt():
    """Manually stop current payment interrupt"""
    result = await payment_interrupt_manager.stop_current_interrupt()
    return result

# 🎯 YouTube Monitoring endpoints

@app.get("/youtube/stats/{channel_id}")
async def get_youtube_channel_stats(
    channel_id: str, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get current YouTube channel statistics"""
    try:
        stats = await youtube_monitor.get_channel_stats(channel_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/youtube/monitor/start")
async def start_youtube_monitoring(
    channel_id: str,
    check_interval: int = 300,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Start monitoring YouTube channel for subscriber milestones"""
    try:
        result = await youtube_monitor.start_monitoring(channel_id, check_interval)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/youtube/monitor/stop")
async def stop_youtube_monitoring(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Stop YouTube channel monitoring"""
    try:
        result = youtube_monitor.stop_monitoring()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/youtube/monitor/status")
async def get_youtube_monitoring_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current YouTube monitoring status"""
    try:
        status = await youtube_monitor.get_monitoring_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/youtube/check-milestone")
async def check_subscriber_milestone(
    channel_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Manually check for subscriber milestones and trigger celebration"""
    try:
        milestone_check = await youtube_monitor.check_subscriber_milestone(channel_id)
        
        # If milestone reached, trigger celebration lights
        if milestone_check.get("should_celebrate"):
            celebration_amount = milestone_check["celebration_amount"]
            
            # Trigger the same payment interrupt system with celebration amount
            await payment_interrupt_manager.trigger_payment_celebration(
                amount=celebration_amount,
                payment_type=f"subscriber_milestone_{milestone_check['milestone_reached']}"
            )
            
        return milestone_check
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test/subscriber-milestone")
async def test_subscriber_milestone(milestone: int = 1000):
    """Test subscriber milestone celebration - triggers YouTube DIY scene"""
    try:
        result = await trigger_diy_scene("youtube")
        
        return {
            "message": f"Testing {milestone} subscriber milestone celebration",
            "celebration": result,
            "milestone": milestone
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/youtube/check-new-subscribers")
async def check_new_youtube_subscribers(
    channel_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Check for new YouTube subscribers and trigger red lights"""
    try:
        subscriber_check = await youtube_monitor.check_for_new_subscribers(channel_id)
        
        # If there are new subscribers, trigger YouTube celebration
        if subscriber_check.get("has_new_subscribers"):
            new_count = subscriber_check["new_subscribers"]
            
            # Use the new celebration system
            await play_celebration_with_text("youtube", subscriber_count=new_count)
            
            print(f"📺 Triggered YouTube celebration for {new_count} new subscribers!")
            
        return subscriber_check
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test/red-youtube")
async def test_red_youtube_celebration(
    new_subscribers: int = 1
):
    """Test YouTube subscriber celebration - triggers YouTube DIY scene"""
    try:
        result = await trigger_diy_scene("youtube")
        
        return {
            "message": f"Triggered YouTube celebration for {new_subscribers} new subscribers",
            "celebration": result,
            "new_subscribers": new_subscribers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test/goal")
async def test_goal_celebration():
    """Test goal milestone celebration - triggers Goal DIY scene"""
    try:
        result = await trigger_diy_scene("goal")
        
        return {
            "message": "Goal milestone celebration triggered!",
            "celebration": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "Gotham Lights is running", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "service": "curtain-lights-api", "timestamp": datetime.now().isoformat()}

@app.get("/status/comprehensive")
async def comprehensive_status_check():
    """Comprehensive status check for all services and configurations"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "unknown",
        "services": {}
    }
    
    issues = []
    successes = []
    
    try:
        # 1. Govee API Status
        govee_status = {
            "name": "Govee Lights API",
            "status": "unknown",
            "details": {}
        }
        
        govee_api_key = os.getenv("GOVEE_API_KEY")
        govee_device_id = os.getenv("GOVEE_DEVICE_ID") 
        govee_model = os.getenv("GOVEE_MODEL")
        
        if not govee_api_key:
            govee_status["status"] = "error"
            govee_status["details"]["error"] = "GOVEE_API_KEY not configured"
            issues.append("Govee API key missing")
        elif not govee_device_id:
            govee_status["status"] = "error"
            govee_status["details"]["error"] = "GOVEE_DEVICE_ID not configured"
            issues.append("Govee device ID missing")
        elif not govee_model:
            govee_status["status"] = "error"
            govee_status["details"]["error"] = "GOVEE_MODEL not configured"
            issues.append("Govee model missing")
        else:
            # Test actual device connection
            try:
                from .govee import test_device_connection
                device_test = await test_device_connection("state", None)
                if device_test:
                    govee_status["status"] = "healthy"
                    govee_status["details"]["api_key"] = f"***{govee_api_key[-4:]}"
                    govee_status["details"]["device_id"] = govee_device_id
                    govee_status["details"]["model"] = govee_model
                    govee_status["details"]["connection"] = "successful"
                    successes.append("Govee lights connected")
                else:
                    govee_status["status"] = "warning"
                    govee_status["details"]["error"] = "Device connection failed"
                    issues.append("Govee device not responding")
            except Exception as e:
                govee_status["status"] = "warning"
                govee_status["details"]["error"] = f"Connection test failed: {str(e)}"
                issues.append("Govee connection test failed")
        
        status["services"]["govee"] = govee_status
        
        # 2. Stripe Configuration
        stripe_status = {
            "name": "Stripe Payment Processing",
            "status": "unknown",
            "details": {}
        }
        
        stripe_sk = os.getenv("STRIPE_SK")
        stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        if not stripe_sk:
            stripe_status["status"] = "error"
            stripe_status["details"]["error"] = "STRIPE_SK not configured"
            issues.append("Stripe secret key missing")
        elif not stripe_webhook_secret:
            stripe_status["status"] = "warning"
            stripe_status["details"]["error"] = "STRIPE_WEBHOOK_SECRET not configured"
            issues.append("Stripe webhook secret missing")
        else:
            stripe_status["status"] = "healthy"
            stripe_status["details"]["secret_key"] = f"***{stripe_sk[-4:]}"
            stripe_status["details"]["webhook_configured"] = bool(stripe_webhook_secret)
            successes.append("Stripe configured")
        
        status["services"]["stripe"] = stripe_status
        
        # 3. YouTube API Configuration
        youtube_status = {
            "name": "YouTube Monitoring",
            "status": "unknown",
            "details": {}
        }
        
        yt_api_key = os.getenv("YT_API_KEY")
        youtube_channel_id = os.getenv("YOUTUBE_CHANNEL_ID")
        
        if not yt_api_key:
            youtube_status["status"] = "error"
            youtube_status["details"]["error"] = "YT_API_KEY not configured"
            issues.append("YouTube API key missing")
        elif not youtube_channel_id:
            youtube_status["status"] = "warning"
            youtube_status["details"]["error"] = "YOUTUBE_CHANNEL_ID not configured"
            issues.append("YouTube channel ID missing")
        else:
            # Test YouTube API
            try:
                from .youtube import youtube_monitor
                test_stats = await youtube_monitor.get_channel_stats(youtube_channel_id)
                if "error" not in test_stats:
                    youtube_status["status"] = "healthy"
                    youtube_status["details"]["api_key"] = f"***{yt_api_key[-4:]}"
                    youtube_status["details"]["channel_id"] = youtube_channel_id
                    youtube_status["details"]["subscriber_count"] = test_stats.get("subscriber_count", "unknown")
                    youtube_status["details"]["monitoring_active"] = youtube_monitor.monitoring_active
                    successes.append("YouTube API connected")
                else:
                    youtube_status["status"] = "error"
                    youtube_status["details"]["error"] = test_stats["error"]
                    issues.append("YouTube API test failed")
            except Exception as e:
                youtube_status["status"] = "error"
                youtube_status["details"]["error"] = f"API test failed: {str(e)}"
                issues.append("YouTube API connection failed")
        
        status["services"]["youtube"] = youtube_status
        
        # 4. Image Storage
        image_status = {
            "name": "Image Storage",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Check if directories exist
            payment_dir = "static/images/payment" 
            youtube_dir = "static/images/youtube"
            config_file = "static/images/config.json"
            
            os.makedirs(payment_dir, exist_ok=True)
            os.makedirs(youtube_dir, exist_ok=True)
            
            # Count uploaded images
            image_count = 0
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    image_count = len(config)
            
            image_status["status"] = "healthy"
            image_status["details"]["payment_directory"] = payment_dir
            image_status["details"]["youtube_directory"] = youtube_dir
            image_status["details"]["uploaded_images"] = image_count
            successes.append(f"Image storage ready ({image_count} images)")
            
        except Exception as e:
            image_status["status"] = "error"
            image_status["details"]["error"] = f"Storage setup failed: {str(e)}"
            issues.append("Image storage not accessible")
        
        status["services"]["image_storage"] = image_status
        
        # 5. Overall Status
        if not issues:
            status["overall_status"] = "healthy"
            status["message"] = "All systems operational!"
        elif len(issues) <= len(successes):
            status["overall_status"] = "warning"
            status["message"] = f"{len(successes)} services healthy, {len(issues)} issues detected"
        else:
            status["overall_status"] = "error"
            status["message"] = f"Multiple critical issues detected"
        
        status["summary"] = {
            "successes": successes,
            "issues": issues,
            "total_services": len(status["services"])
        }
        
        return status
        
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "error",
            "message": f"Status check failed: {str(e)}",
            "services": status.get("services", {}),
            "summary": {
                "successes": successes,
                "issues": issues + [f"Status check error: {str(e)}"],
                "total_services": len(status.get("services", {}))
            }
        }

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables"""
    return {
        "govee_api_key": "***" + os.getenv("GOVEE_API_KEY", "NOT_SET")[-4:] if os.getenv("GOVEE_API_KEY") else "NOT_SET",
        "govee_device_id": os.getenv("GOVEE_DEVICE_ID", "NOT_SET"),
        "govee_model": os.getenv("GOVEE_MODEL", "NOT_SET"),
        "google_client_id": "***" + os.getenv("GOOGLE_CLIENT_ID", "NOT_SET")[-4:] if os.getenv("GOOGLE_CLIENT_ID") else "NOT_SET",
        "stripe_client_id": "***" + os.getenv("STRIPE_CLIENT_ID", "NOT_SET")[-4:] if os.getenv("STRIPE_CLIENT_ID") else "NOT_SET"
    }

@app.post("/test/animated-celebration")
async def test_animated_celebration(celebration_type: str = "payment", amount: float = 25.0, subscriber_count: int = 1):
    """Test the new celebration system with custom images + text display"""
    try:
        if celebration_type == "payment":
            await play_celebration_with_text("payment", amount=amount)
            return {
                "status": "success",
                "message": f"Payment celebration completed for ${amount}",
                "celebration_type": "payment",
                "amount": amount,
                "sequence": "5s custom image/GIF + amount display"
            }
        elif celebration_type == "youtube":
            await play_celebration_with_text("youtube", subscriber_count=subscriber_count)
            return {
                "status": "success",
                "message": f"YouTube celebration completed for {subscriber_count} subscribers",
                "celebration_type": "youtube", 
                "subscriber_count": subscriber_count,
                "sequence": "5s custom image/GIF + subscriber count display"
            }
        else:
            raise HTTPException(status_code=400, detail="celebration_type must be 'payment' or 'youtube'")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing celebration: {str(e)}")

# Serve frontend static files (for production)
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend") 