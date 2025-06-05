"""
🎉 Payment Interrupt System
Temporarily overrides current lighting with celebration patterns when payments are received.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
import json
from .govee import set_color, test_device_connection, get_devices, play_celebration_with_text

class PaymentInterruptManager:
    def __init__(self):
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
        
        # Run the new celebration sequence (5s custom + amount display)
        self.interrupt_task = asyncio.create_task(
            self._run_new_celebration(payment_amount)
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
            # Simple state saving - just mark that we need to turn off after
            self.original_state = {
                "timestamp": datetime.now().isoformat(),
                "needs_restore": True
            }
            print(f"💾 Saved lighting state")
            
        except Exception as e:
            print(f"⚠️ Could not save current state: {e}")
            self.original_state = None
    
    async def _run_new_celebration(self, payment_amount: float):
        """Run the new celebration sequence: 5s custom image + amount display"""
        try:
            print(f"💰 Starting payment celebration for ${payment_amount}")
            
            # Use the new celebration system
            await play_celebration_with_text("payment", amount=payment_amount)
            
            print(f"✅ Payment celebration complete for ${payment_amount}")
            
            # Restore original state
            await self._restore_original_state()
            
        except asyncio.CancelledError:
            print("🛑 Payment celebration interrupted")
            await self._restore_original_state()
        except Exception as e:
            print(f"❌ Error during payment celebration: {e}")
            await self._restore_original_state()
        finally:
            self.current_interrupt = None

    async def _run_celebration(self, celebration_pattern: Dict):
        """Legacy celebration method - fallback if needed"""
        try:
            duration = celebration_pattern["duration"]
            patterns = celebration_pattern["patterns"]
            
            print(f"🎉 Starting {celebration_pattern['name']} for {duration} seconds")
            
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=duration)
            
            # Run celebration patterns
            while datetime.now() < end_time:
                for pattern in patterns:
                    if datetime.now() >= end_time:
                        break
                    
                    # Apply pattern using govee functions
                    try:
                        color = pattern["color"]
                        await set_color(color[0], color[1], color[2])
                        await asyncio.sleep(pattern["duration"])
                    except Exception as e:
                        print(f"⚠️ Error controlling lights: {e}")
                    
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
            # Simple restore - just turn off the lights
            await test_device_connection("turn", "off")
            print("🔄 Restored lighting (turned off)")
            
        except Exception as e:
            print(f"⚠️ Error restoring state: {e}")
        
        self.original_state = None
    
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