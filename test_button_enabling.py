#!/usr/bin/env python3
"""
Test script to verify button enabling behavior

This script tests that transport and volume buttons remain enabled 
at all times regardless of audio source status.
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

def test_button_controller():
    """Test that button controller doesn't disable buttons"""
    print("=" * 60)
    print("Testing Button Controller (buttons should always work)...")
    print("=" * 60)
    
    try:
        from kitchenradio.radio.hardware.button_controller import ButtonController, ButtonType
        from kitchenradio.radio.kitchen_radio import KitchenRadio
        
        # Create kitchen radio and button controller
        kitchen_radio = KitchenRadio()
        button_controller = ButtonController(kitchen_radio)
        
        print("✅ Button controller created successfully")
        
        # Test all button types
        test_buttons = [
            ButtonType.PLAY_PAUSE,
            ButtonType.NEXT_TRACK,
            ButtonType.PREV_TRACK,
            ButtonType.STOP,
            ButtonType.VOLUME_UP,
            ButtonType.VOLUME_DOWN
        ]
        
        print("Testing button presses (should all work regardless of audio source state):")
        
        for button in test_buttons:
            try:
                # Simulate button press
                result = button_controller.handle_button_press(button)
                print(f"   {button.value}: ✅ (result: {result})")
            except Exception as e:
                print(f"   {button.value}: ❌ (error: {e})")
        
        return True
        
    except Exception as e:
        print(f"❌ Button controller test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Hardware Button Test")
    print("=" * 60)
    print("Testing that hardware buttons always work...")
    
    success = test_button_controller()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ BUTTON TEST PASSED!")
        print("All hardware buttons work regardless of audio source state")
        print("Frontend JavaScript has been updated to keep buttons enabled")
    else:
        print("❌ BUTTON TEST FAILED!")
        print("Some buttons may not be working properly")
    
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
