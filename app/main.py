from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import asyncio
from datetime import datetime

# Govee API configuration
GOVEE_API_KEY = "846814e4-67ec-4398-ae9b-453d741b56cd"
GOVEE_DEVICE_ID = "1A:67:F3:96:2E:A2:43:DF"
GOVEE_MODEL = "H70B1"
GOVEE_BASE_URL = "https://openapi.api.govee.com"

# DIY Scene IDs
DIY_SCENES = {
    "money": 16158674,    # Money DIY scene for Stripe payments
    "youtube": 16158613,  # YouTube DIY scene for new subscribers
    "goal": 16160444      # Goal DIY scene for 200 subscriber milestone
}

app = FastAPI(title="Curtain Lights", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """Restore the lights to their previous state"""
    if not previous_state or not previous_state.get("capabilities"):
        return
    
    headers = {
        "Govee-API-Key": GOVEE_API_KEY,
        "Content-Type": "application/json"
    }
    
    capabilities = previous_state["capabilities"]
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
    
    # Clear any active scenes
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
    
    # Restore power state
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
    
    # Restore color
    if color is not None and color != 0 and color != 16777215:
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
                print(f"⏰ Scheduled state restoration in {restore_after_seconds} seconds")
                
                # Schedule restoration after delay
                asyncio.create_task(restore_after_delay(previous_state, restore_after_seconds))
                
                return {
                    "success": True,
                    "scene_name": scene_name,
                    "scene_id": scene_id,
                    "message": f"DIY scene '{scene_name}' triggered successfully"
                }
            else:
                print(f"❌ Govee API error: {result}")
                raise HTTPException(status_code=500, detail=f"Govee API error: {result}")
        else:
            print(f"❌ HTTP error {response.status_code}: {response.text}")
            raise HTTPException(status_code=500, detail=f"HTTP error: {response.status_code}")
            
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

async def restore_after_delay(previous_state, delay_seconds):
    """Wait for specified delay, then restore the previous light state"""
    print(f"⏳ Waiting {delay_seconds} seconds before restoring state...")
    await asyncio.sleep(delay_seconds)
    print("🔄 Starting state restoration...")
    await restore_light_state(previous_state)

# Test endpoints
@app.post("/test/payment")
async def test_payment():
    """Test payment celebration - triggers Money DIY scene"""
    try:
        result = await trigger_diy_scene("money")
        return {
            "status": "success", 
            "message": "Payment celebration started for $25",
            "celebration": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering celebration: {str(e)}")

@app.post("/test/subscriber-milestone")
async def test_subscriber_milestone():
    """Test subscriber milestone - triggers YouTube DIY scene"""
    try:
        result = await trigger_diy_scene("youtube")
        return {
            "status": "success",
            "message": "Testing 1000 subscriber milestone celebration",
            "celebration": result,
            "milestone": 1000
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering celebration: {str(e)}")

@app.post("/test/goal")
async def test_goal():
    """Test goal celebration - triggers Goal DIY scene for 200 subscribers"""
    try:
        result = await trigger_diy_scene("goal")
        return {
            "status": "success",
            "message": "Testing 200 subscriber goal celebration",
            "celebration": result,
            "milestone": 200
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering celebration: {str(e)}")

# Health check
@app.get("/")
async def root():
    return {"message": "Curtain Lights API - Simple DIY Scene Controller"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "scenes": list(DIY_SCENES.keys())} 