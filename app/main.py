from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from datetime import datetime

# --- Configuration ---
# Load API Key from environment variable for security
GOVEE_API_KEY = os.getenv("GOVEE_API_KEY", "846814e4-67ec-4398-ae9b-453d741b56cd")
GOVEE_DEVICE_ID = "1A:67:F3:96:2E:A2:43:DF"
GOVEE_MODEL = "H70B1"
GOVEE_BASE_URL = "https://openapi.api.govee.com"

# Define our new dynamic color palettes
# Each inner list is an [R, G, B] color
DYNAMIC_PALETTES = {
    "money": [[0, 128, 0], [255, 215, 0]],       # Green & Gold
    "youtube": [[255, 0, 0], [255, 255, 255]], # Red & White
    "goal": [[128, 0, 128], [255, 215, 0]]     # Purple & Gold
}

app = FastAPI(title="Curtain Lights Pro", version="2.0.0")

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Govee API Logic ---
async def trigger_dynamic_palette(palette_name: str):
    """Triggers a continuously looping dynamic palette on the device."""
    if palette_name not in DYNAMIC_PALETTES:
        raise HTTPException(status_code=400, detail=f"Unknown palette: {palette_name}")

    print(f"🎨 Triggering looping palette '{palette_name}'...")

    headers = {
        "Govee-API-Key": GOVEE_API_KEY,
        "Content-Type": "application/json"
    }

    # This is the command structure for a looping dynamic palette
    payload = {
        "requestId": f"palette-{palette_name}-{datetime.now().isoformat()}",
        "payload": {
            "sku": GOVEE_MODEL,
            "device": GOVEE_DEVICE_ID,
            "capability": {
                "type": "devices.capabilities.dynamic_palette",
                "instance": "powerSwitch", # This instance seems to work for this model
                "value": {
                    "mode": 4, # 4 corresponds to a dynamic/cycle mode
                    "cycle": "auto", # 'auto' should loop
                    "palettes": DYNAMIC_PALETTES[palette_name]
                }
            }
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{GOVEE_BASE_URL}/router/api/v1/device/control",
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

            result = response.json()
            if result.get("code") == 200:
                print(f"✅ Palette '{palette_name}' triggered successfully.")
                return {
                    "success": True,
                    "palette_name": palette_name,
                    "message": f"Looping palette '{palette_name}' is now active."
                }
            else:
                print(f"❌ Govee API error: {result}")
                raise HTTPException(status_code=500, detail=f"Govee API error: {result.get('message', 'Unknown error')}")

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP error {e.response.status_code}: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail="Error communicating with Govee API.")
        except httpx.RequestError as e:
            print(f"❌ Request failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to connect to Govee API: {e}")


# --- API Endpoints ---
@app.post("/test/payment")
async def test_payment():
    """Triggers the 'money' (Green & Gold) looping palette."""
    return await trigger_dynamic_palette("money")

@app.post("/test/subscriber-milestone")
async def test_subscriber_milestone():
    """Triggers the 'youtube' (Red & White) looping palette."""
    return await trigger_dynamic_palette("youtube")

@app.post("/test/goal")
async def test_goal():
    """Triggers the 'goal' (Purple & Gold) looping palette."""
    return await trigger_dynamic_palette("goal")

@app.post("/test/off")
async def test_off():
    """Turns the device off."""
    print("🔌 Turning device off...")
    headers = {"Govee-API-Key": GOVEE_API_KEY, "Content-Type": "application/json"}
    payload = {
        "requestId": f"off-{datetime.now().isoformat()}",
        "payload": {
            "sku": GOVEE_MODEL,
            "device": GOVEE_DEVICE_ID,
            "capability": {"type": "devices.capabilities.on_off", "instance": "powerSwitch", "value": 0}
        }
    }
    async with httpx.AsyncClient() as client:
        await client.post(f"{GOVEE_BASE_URL}/router/api/v1/device/control", headers=headers, json=payload, timeout=10)
    return {"status": "success", "message": "Device turned off."}

# --- Health Check ---
@app.get("/")
async def root():
    return {"message": "Curtain Lights Pro API - Dynamic Palette Controller"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "palettes": list(DYNAMIC_PALETTES.keys())} 