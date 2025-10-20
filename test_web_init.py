#!/usr/bin/env python3
"""
Test script to verify KitchenRadioWeb initialization with display controller
"""

import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_kitchen_radio_web_init():
    """Test KitchenRadioWeb initialization"""
    print("=" * 60)
    print("Testing KitchenRadioWeb initialization...")
    print("=" * 60)
    
    try:
        # Import KitchenRadioWeb
        from kitchenradio.web.kitchen_radio_web import KitchenRadioWeb
        print("✅ KitchenRadioWeb imported successfully")
        
        # Create instance (this should initialize display controller)
        web_api = KitchenRadioWeb(port=5002)  # Different port to avoid conflicts
        print("✅ KitchenRadioWeb instance created")
        
        # Check components
        print(f"   Button controller: {web_api.button_controller is not None}")
        print(f"   Display emulator: {web_api.display_emulator is not None}")
        print(f"   Display controller: {web_api.display_controller is not None}")
        
        if web_api.display_controller:
            print(f"   Display thread running: {web_api.display_controller.update_thread.is_alive()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("KitchenRadioWeb Initialization Test")
    print("=" * 60)
    
    success = test_kitchen_radio_web_init()
    
    if success:
        print("\n✅ TEST PASSED!")
        print("KitchenRadioWeb initializes correctly with display controller")
    else:
        print("\n❌ TEST FAILED!")
        print("KitchenRadioWeb initialization has issues")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
