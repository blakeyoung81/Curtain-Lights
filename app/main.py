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

# Load environment variables
load_dotenv()

from .govee import set_scene, get_devices, test_device_connection, set_color, red_youtube_celebration
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

# Mount static files for serving uploaded images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load environment variables
stripe.api_key = os.getenv("STRIPE_SK")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Create directories for storing images
os.makedirs("static/images/payment", exist_ok=True)
os.makedirs("static/images/youtube", exist_ok=True)

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
    celebration_type: str  # "payment_mini", "payment_standard", "payment_major", "payment_premium", "youtube_subscriber", "youtube_milestone"
    image_path: str

# Image processing functions
def process_image_for_lights(image_file: bytes, max_width: int = 64, max_height: int = 64) -> str:
    """
    Process uploaded image for LED display:
    - Resize to LED grid dimensions (recommended: 64x64 or smaller)
    - Enhance contrast and saturation for better LED visibility
    - Save as optimized format
    Returns the file path of the processed image
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
    valid_types = [
        "payment_mini", "payment_standard", "payment_major", "payment_premium",
        "youtube_subscriber", "youtube_milestone"
    ]
    
    if celebration_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid celebration type. Must be one of: {valid_types}")
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read file content
        image_content = await file.read()
        
        # Process image for LED display
        processed_image = process_image_for_lights(image_content)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{celebration_type}_{timestamp}.png"
        
        # Determine directory based on type
        if celebration_type.startswith("payment"):
            directory = "static/images/payment"
        else:
            directory = "static/images/youtube"
        
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
            "uploaded_at": datetime.now().isoformat(),
            "original_filename": file.filename,
            "dimensions": f"{processed_image.width}x{processed_image.height}"
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return {
            "status": "success",
            "message": f"Image uploaded and processed for {celebration_type}",
            "celebration_type": celebration_type,
            "file_path": file_path,
            "dimensions": f"{processed_image.width}x{processed_image.height}",
            "grid_size": f"{len(color_grid)}x{len(color_grid[0]) if color_grid else 0}",
            "recommendations": {
                "optimal_dimensions": "64x64 pixels or smaller",
                "best_image_types": ["High contrast images", "Bold colors", "Simple designs", "Logos or icons"],
                "avoid": ["Fine details", "Text smaller than 8px", "Low contrast images"]
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
                background_tasks.add_task(trigger_color_scene, "youtube", current_user["email"])
                print(f"New YouTube subscriber detected for {current_user['email']}: {new_count}")
        
        # Check Google Calendar for upcoming events
        if google_tokens:
            has_upcoming = await google_calendar.check_upcoming_events(google_tokens)
            if has_upcoming:
                background_tasks.add_task(trigger_color_scene, "calendar", current_user["email"])
                print(f"Upcoming calendar event detected for {current_user['email']}")
            
    except Exception as e:
        print(f"Error in cron job for {current_user['email']}: {e}")
    
    return {
        "status": "success", 
        "timestamp": datetime.now().isoformat(),
        "user": current_user["email"]
    }

@app.get("/config/scene")
async def get_scene_config(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current scene configuration for user"""
    user_settings = auth_manager.get_user_settings(current_user["email"])
    return user_settings.get("scenes", {"stripe": 2, "calendar": 3, "youtube": 1})

@app.put("/config/scene")
async def update_scene_config(config: SceneConfig, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Update scene configuration for user"""
    user_settings = auth_manager.get_user_settings(current_user["email"])
    user_settings["scenes"] = config.dict()
    auth_manager.update_user_settings(current_user["email"], user_settings)
    return {"status": "success", "scenes": user_settings["scenes"]}

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
async def test_light(request: TestLightRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Test light controls"""
    try:
        print(f"Testing light for {current_user['email']}: {request.action} with value {request.value}")
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
        print(f"Error in test_light for {current_user['email']}: {e}")
        raise HTTPException(status_code=500, detail=f"Error controlling light: {str(e)}")

# 🎉 Payment Interrupt Endpoints

@app.post("/test/payment")
async def test_payment_celebration(amount: float = 25.0):
    """Test payment celebration manually - simulates receiving a payment"""
    try:
        result = await payment_interrupt_manager.trigger_payment_celebration(amount, "test")
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
    """Test subscriber milestone celebration"""
    try:
        # Map milestone to celebration amount like the YouTube monitor does
        milestone_amounts = {
            100: 5, 500: 10, 1000: 15, 5000: 25, 10000: 50,
            50000: 75, 100000: 100, 500000: 200, 1000000: 500
        }
        
        celebration_amount = milestone_amounts.get(milestone, 25)  # Default $25
        
        # Trigger celebration
        await payment_interrupt_manager.trigger_payment_celebration(
            amount=celebration_amount,
            payment_type=f"test_milestone_{milestone}"
        )
        
        return {
            "message": f"Testing {milestone} subscriber milestone celebration",
            "celebration_amount": celebration_amount,
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
        
        # If there are new subscribers, trigger red light celebrations
        if subscriber_check.get("has_new_subscribers"):
            new_count = subscriber_check["new_subscribers"]
            
            # Trigger red celebration for each new subscriber
            for i in range(min(new_count, 5)):  # Max 5 celebrations to avoid spam
                await red_youtube_celebration(duration=3)
                if i < min(new_count, 5) - 1:  # Don't wait after the last one
                    await asyncio.sleep(1)  # Brief pause between celebrations
            
            print(f"🔴 Triggered {min(new_count, 5)} red celebrations for {new_count} new subscribers!")
            
        return subscriber_check
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test/red-youtube")
async def test_red_youtube_celebration(
    new_subscribers: int = 1
):
    """Test red YouTube subscriber celebration"""
    try:
        # Trigger red celebration for specified number of new subscribers
        celebrations = min(new_subscribers, 5)  # Max 5 to avoid spam
        
        for i in range(celebrations):
            await red_youtube_celebration(duration=3)
            if i < celebrations - 1:  # Don't wait after the last one
                await asyncio.sleep(1)  # Brief pause between celebrations
        
        return {
            "message": f"Triggered {celebrations} red YouTube celebrations for {new_subscribers} new subscribers",
            "celebrations_triggered": celebrations,
            "new_subscribers": new_subscribers
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

# Serve frontend static files (for production)
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend") 