"""
🎉 Payment Interrupt System
Temporarily overrides current lighting with celebration patterns when payments are received.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
import json
from .govee_api import GoveeAPI

class PaymentInterruptManager:
    def __init__(self):
        self.govee_api = GoveeAPI()
        self.current_interrupt: Optional[Dict] = None
        self.original_state: Optional[Dict] = None
        self.interrupt_task: Optional[asyncio.Task] = None
        
    async def trigger_payment_celebration(self, payment_amount: float, payment_source: str = "stripe"):
        """
        🎉 Trigger celebration lighting for payment received
        
        Args:
            payment_amount: Amount of payment received
            payment_source: Source of payment (stripe, paypal, etc.)
        """
        print(f"💰 Payment received: ${payment_amount} from {payment_source}")
        
        # Store current lighting state to restore later
        await self._save_current_state()
        
        # Stop any existing interrupt
        if self.interrupt_task:
            self.interrupt_task.cancel()
        
        # Choose celebration pattern based on amount
        celebration_pattern = self._get_celebration_pattern(payment_amount)
        
        # Start the celebration
        self.current_interrupt = {
            "type": "payment_celebration",
            "amount": payment_amount,
            "source": payment_source,
            "started_at": datetime.now(),
            "pattern": celebration_pattern
        }
        
        # Run celebration for specified duration
        self.interrupt_task = asyncio.create_task(
            self._run_celebration(celebration_pattern)
        )
        
        return {
            "status": "celebration_started",
            "pattern": celebration_pattern["name"],
            "duration": celebration_pattern["duration"],
            "amount": payment_amount
        }
    
    def _get_celebration_pattern(self, amount: float) -> Dict:
        """Choose celebration pattern based on payment amount"""
        
        if amount >= 100:
            return {
                "name": "💎 Premium Celebration",
                "duration": 30,  # 30 seconds
                "patterns": [
                    {"color": [255, 215, 0], "brightness": 100, "duration": 2},    # Gold
                    {"color": [138, 43, 226], "brightness": 100, "duration": 2},   # Purple
                    {"color": [255, 255, 255], "brightness": 100, "duration": 1},  # White flash
                    {"color": [255, 215, 0], "brightness": 100, "duration": 2},    # Gold
                ]
            }
        elif amount >= 50:
            return {
                "name": "🌟 Major Sale",
                "duration": 20,  # 20 seconds
                "patterns": [
                    {"color": [0, 255, 0], "brightness": 100, "duration": 2},      # Green
                    {"color": [255, 255, 0], "brightness": 100, "duration": 2},    # Yellow
                    {"color": [255, 255, 255], "brightness": 100, "duration": 1},  # White flash
                ]
            }
        elif amount >= 20:
            return {
                "name": "🎊 Standard Celebration",
                "duration": 15,  # 15 seconds
                "patterns": [
                    {"color": [0, 255, 0], "brightness": 80, "duration": 3},       # Green
                    {"color": [255, 255, 255], "brightness": 80, "duration": 1},   # White flash
                ]
            }
        else:
            return {
                "name": "✨ Mini Celebration",
                "duration": 10,  # 10 seconds
                "patterns": [
                    {"color": [0, 255, 0], "brightness": 60, "duration": 2},       # Gentle green
                    {"color": [255, 255, 255], "brightness": 60, "duration": 1},   # Soft white
                ]
            }
    
    async def _save_current_state(self):
        """Save current lighting state before interrupt"""
        try:
            # Get current device states
            devices = await self.govee_api.get_devices()
            current_states = {}
            
            for device in devices:
                device_id = device.get('device')
                if device_id:
                    state = await self.govee_api.get_device_state(device_id)
                    current_states[device_id] = state
            
            self.original_state = {
                "timestamp": datetime.now().isoformat(),
                "device_states": current_states
            }
            
            print(f"💾 Saved lighting state for {len(current_states)} devices")
            
        except Exception as e:
            print(f"⚠️ Could not save current state: {e}")
            self.original_state = None
    
    async def _run_celebration(self, celebration_pattern: Dict):
        """Run the celebration light pattern"""
        try:
            duration = celebration_pattern["duration"]
            patterns = celebration_pattern["patterns"]
            
            print(f"🎉 Starting {celebration_pattern['name']} for {duration} seconds")
            
            # Get all available devices
            devices = await self.govee_api.get_devices()
            device_ids = [d.get('device') for d in devices if d.get('device')]
            
            if not device_ids:
                print("⚠️ No devices found for celebration")
                return
            
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=duration)
            
            # Run celebration patterns
            while datetime.now() < end_time:
                for pattern in patterns:
                    if datetime.now() >= end_time:
                        break
                    
                    # Apply pattern to all devices
                    for device_id in device_ids:
                        try:
                            await self.govee_api.control_device(
                                device_id=device_id,
                                turn_on=True,
                                brightness=pattern["brightness"],
                                color_rgb=pattern["color"]
                            )
                        except Exception as e:
                            print(f"⚠️ Error controlling device {device_id}: {e}")
                    
                    # Hold pattern for specified duration
                    await asyncio.sleep(pattern["duration"])
                    
                    if datetime.now() >= end_time:
                        break
            
            print(f"✅ Celebration complete!")
            
            # Restore original state
            await self._restore_original_state()
            
        except asyncio.CancelledError:
            print("🛑 Celebration interrupted")
            await self._restore_original_state()
        except Exception as e:
            print(f"❌ Error during celebration: {e}")
            await self._restore_original_state()
        finally:
            self.current_interrupt = None
    
    async def _restore_original_state(self):
        """Restore lighting to state before interrupt"""
        if not self.original_state:
            print("⚠️ No original state to restore")
            return
        
        try:
            device_states = self.original_state.get("device_states", {})
            
            for device_id, state in device_states.items():
                if state and isinstance(state, dict):
                    # Extract state information
                    power_state = state.get("powerState", "on") == "on"
                    brightness = state.get("brightness", 100)
                    color = state.get("color", {})
                    
                    # Restore device state
                    await self.govee_api.control_device(
                        device_id=device_id,
                        turn_on=power_state,
                        brightness=brightness,
                        color_rgb=color.get("rgb", [255, 255, 255])
                    )
            
            print(f"🔄 Restored original state for {len(device_states)} devices")
            
        except Exception as e:
            print(f"⚠️ Error restoring original state: {e}")
    
    def get_current_interrupt(self) -> Optional[Dict]:
        """Get current interrupt status"""
        if not self.current_interrupt:
            return None
        
        return {
            **self.current_interrupt,
            "time_elapsed": (datetime.now() - self.current_interrupt["started_at"]).total_seconds(),
            "is_active": self.interrupt_task and not self.interrupt_task.done()
        }
    
    async def stop_current_interrupt(self):
        """Manually stop current interrupt and restore original state"""
        if self.interrupt_task:
            self.interrupt_task.cancel()
            await self._restore_original_state()
            self.current_interrupt = None
            return {"status": "interrupt_stopped"}
        
        return {"status": "no_interrupt_active"}

# Global instance
payment_interrupt_manager = PaymentInterruptManager() 