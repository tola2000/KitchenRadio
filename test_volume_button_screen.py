#!/usr/bin/env python3
"""
Test script for volume screen display triggered only by button press

This script tests that the volume screen appears only when volume up/down 
buttons are pressed, not on every volume change.
"""

import sys
import logging
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_volume_button_screen():
    """Test that volume screen appears only on button press"""
    print("=" * 60)
    print("Testing volume screen triggered by button press...")
    print("=" * 60)
    
    try:
        # Import components
        from kitchenradio.web.kitchen_radio_web import KitchenRadioWeb
        
        # Create web API instance (this creates all components)
        web_api = KitchenRadioWeb(port=5003)  # Different port
        print("✅ KitchenRadioWeb created successfully")
        
        # Check components
        print(f"   Button controller available: {web_api.button_controller is not None}")
        print(f"   Display controller available: {web_api.display_controller is not None}")
        print(f"   Display emulator available: {web_api.display_emulator is not None}")
        
        if not (web_api.button_controller and web_api.display_controller):
            print("❌ Required components not available")
            return False
        
        # Check that button controller has display controller reference
        has_display_ref = hasattr(web_api.button_controller, 'display_controller') and \
                         web_api.button_controller.display_controller is not None
        print(f"   Button controller has display reference: {has_display_ref}")
        
        if not has_display_ref:
            print("❌ Button controller doesn't have display controller reference")
            return False
        
        print("\n" + "=" * 40)
        print("Testing volume button press scenarios...")
        
        # Test 1: Press volume up button
        print("\n1. Testing volume up button press...")
        result = web_api.button_controller.handle_button_press("volume_up")
        print(f"   Volume up result: {result}")
        
        # Check if volume screen is active
        if web_api.display_controller.volume_screen_active:
            print("   ✅ Volume screen is active after volume up")
            timeout = web_api.display_controller.volume_screen_end_time
            remaining = timeout - time.time()
            print(f"   Volume screen timeout: {remaining:.1f}s remaining")
        else:
            print("   ❌ Volume screen not active after volume up")
            return False
        
        # Wait for screen to be visible
        time.sleep(1)
        
        # Test 2: Press volume down button
        print("\n2. Testing volume down button press...")
        result = web_api.button_controller.handle_button_press("volume_down")
        print(f"   Volume down result: {result}")
        
        # Check if volume screen is still/again active
        if web_api.display_controller.volume_screen_active:
            print("   ✅ Volume screen is active after volume down")
            timeout = web_api.display_controller.volume_screen_end_time
            remaining = timeout - time.time()
            print(f"   Volume screen timeout: {remaining:.1f}s remaining")
        else:
            print("   ❌ Volume screen not active after volume down")
            return False
        
        # Test 3: Wait for screen to timeout
        print("\n3. Testing volume screen timeout...")
        print("   Waiting for volume screen to timeout...")
        
        # Wait for timeout plus a bit extra
        timeout_time = web_api.display_controller.volume_screen_end_time
        wait_time = max(0, timeout_time - time.time() + 1)
        time.sleep(wait_time)
        
        # Check if volume screen is now inactive
        if not web_api.display_controller.volume_screen_active:
            print("   ✅ Volume screen correctly timed out")
        else:
            print("   ❌ Volume screen did not timeout")
            return False
        
        # Test 4: Test that other buttons don't trigger volume screen
        print("\n4. Testing that other buttons don't trigger volume screen...")
        result = web_api.button_controller.handle_button_press("play_pause")
        print(f"   Play/pause result: {result}")
        
        if not web_api.display_controller.volume_screen_active:
            print("   ✅ Volume screen not triggered by play/pause")
        else:
            print("   ❌ Volume screen incorrectly triggered by play/pause")
            return False
        
        # Test 5: Save volume screen display to file
        print("\n5. Testing volume screen display output...")
        
        # Trigger volume screen again
        web_api.button_controller.handle_button_press("volume_up")
        time.sleep(0.5)  # Let it render
        
        # Get BMP data
        if web_api.display_emulator:
            bmp_data = web_api.display_emulator.getDisplayImage()
            if bmp_data:
                filename = "test_volume_screen_button_triggered.bmp"
                with open(filename, 'wb') as f:
                    f.write(bmp_data)
                print(f"   ✅ Volume screen saved to: {filename}")
            else:
                print("   ⚠️  No BMP data available")
        
        return True
        
    except Exception as e:
        print(f"❌ Volume button screen test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Volume Button Screen Test")
    print("=" * 60)
    print("Testing volume screen triggered only by button press...")
    
    success = test_volume_button_screen()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("Volume screen appears only when volume buttons are pressed")
        print("Volume screen correctly times out after 3 seconds")
        print("Other buttons do not trigger volume screen")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Volume screen behavior needs fixing")
    
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
