from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
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

async def trigger_diy_scene(scene_name: str):
    """Triggers a specific DIY scene by name and leaves it on."""
    if scene_name not in DIY_SCENES:
        raise HTTPException(status_code=400, detail=f"Unknown DIY scene: {scene_name}")
    
    scene_id = DIY_SCENES[scene_name]
    print(f"🎬 Triggering DIY scene '{scene_name}' (ID: {scene_id}) and keeping it on.")
    
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
                print(f"✅ DIY scene '{scene_name}' triggered successfully.")
                return {
                    "success": True,
                    "scene_name": scene_name,
                    "scene_id": scene_id,
                    "message": f"DIY scene '{scene_name}' triggered and is now active."
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

# Test endpoints
@app.post("/test/payment")
async def test_payment():
    """Test payment celebration - triggers Money DIY scene"""
    try:
        result = await trigger_diy_scene("money")
        return {
            "status": "success", 
            "message": "Payment celebration scene is now active.",
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
            "message": "Subscriber milestone scene is now active.",
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
            "message": "Goal celebration scene is now active.",
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