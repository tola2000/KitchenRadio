#!/usr/bin/env python3
"""
Test script to verify that the DisplayController loop starts correctly when using the emulator
"""

import sys
import logging
import time
import threading
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_display_controller_with_emulator():
    """Test that DisplayController starts update loop with emulator interface"""
    print("=" * 60)
    print("Testing DisplayController with emulator interface...")
    print("=" * 60)
    
    try:
        # Import components
        from kitchenradio.web.display_interface_emulator import DisplayInterfaceEmulator
        from kitchenradio.radio.hardware.display_controller import DisplayController
        from kitchenradio.radio.kitchen_radio import KitchenRadio
        
        print("✅ All imports successful")
        
        # Create kitchen radio instance
        kitchen_radio = KitchenRadio()
        print("✅ KitchenRadio instance created")
        
        # Create emulator interface
        emulator = DisplayInterfaceEmulator()
        emulator.initialize()
        print("✅ Display emulator created and initialized")
        
        # Create display controller with emulator and kitchen radio
        display_controller = DisplayController(
            kitchen_radio=kitchen_radio,
            i2c_interface=emulator
        )
        print("✅ DisplayController created with emulator interface")
        
        # Initialize display controller
        success = display_controller.initialize()
        print(f"✅ DisplayController initialization: {success}")
        
        # Check if update thread is running
        if display_controller.update_thread and display_controller.update_thread.is_alive():
            print("✅ Display update thread is running!")
        else:
            print("❌ Display update thread is NOT running")
            return False
        
        # Let it run for a few seconds to test
        print("🔄 Running display controller for 5 seconds...")
        time.sleep(5)
        
        # Check if thread is still alive
        if display_controller.update_thread.is_alive():
            print("✅ Display update thread still running after 5 seconds")
        else:
            print("❌ Display update thread stopped unexpectedly")
            return False
        
        # Cleanup
        display_controller.cleanup()
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Display Controller Loop Test")
    print("=" * 60)
    
    success = test_display_controller_with_emulator()
    
    if success:
        print("\n✅ ALL TESTS PASSED!")
        print("DisplayController update loop starts correctly with emulator")
    else:
        print("\n❌ TESTS FAILED!")
        print("DisplayController update loop has issues")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
