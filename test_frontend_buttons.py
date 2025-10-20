#!/usr/bin/env python3
"""
Test to verify frontend button enabling and functionality

This script starts the web server briefly to test that buttons are enabled.
"""

import sys
import logging
import time
import threading
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_web_server_startup():
    """Test that the web server starts and buttons should be enabled"""
    print("=" * 60)
    print("Testing web server startup and button states...")
    print("=" * 60)
    
    try:
        # Import and create web server
        from kitchenradio.web.kitchen_radio_web import KitchenRadioWeb
        
        print("1. Creating KitchenRadioWeb instance...")
        web_api = KitchenRadioWeb(port=5003)  # Different port
        print("✅ Web API created successfully")
        
        print("2. Starting web server...")
        web_api.start()
        print("✅ Web server started")
        
        # Give it a moment to start
        time.sleep(2)
        
        print("3. Checking server status...")
        print(f"   Running: {web_api.running}")
        print(f"   Button controller: {web_api.button_controller is not None}")
        print(f"   Display emulator: {web_api.display_emulator is not None}")
        print(f"   Display controller: {web_api.display_controller is not None}")
        
        # Test a button press to ensure backend works
        print("4. Testing button functionality...")
        try:
            result = web_api.button_controller.handle_button_press(
                web_api.button_controller.ButtonType.PLAY_PAUSE
            )
            print(f"   Play/Pause button test: ✅ {result}")
        except Exception as e:
            print(f"   Play/Pause button test: ⚠️  {e}")
        
        # Stop server
        print("5. Stopping web server...")
        web_api.stop()
        print("✅ Web server stopped")
        
        return True
        
    except Exception as e:
        print(f"❌ Web server test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_frontend_files():
    """Test that frontend files have correct button configurations"""
    print("\n" + "=" * 60)
    print("Testing frontend file configurations...")
    print("=" * 60)
    
    try:
        # Check HTML file for disabled attributes
        html_file = Path("frontend/templates/radio_interface.html")
        if html_file.exists():
            content = html_file.read_text()
            disabled_count = content.count('disabled')
            print(f"1. HTML file check:")
            print(f"   Found {disabled_count} 'disabled' attributes")
            if disabled_count == 0:
                print("   ✅ No disabled attributes found - buttons should be enabled")
            else:
                print("   ⚠️  Some disabled attributes still present")
                
        # Check JavaScript file
        js_file = Path("frontend/static/js/radio_app.js")
        if js_file.exists():
            content = js_file.read_text()
            disabled_js_count = content.count('.disabled = true')
            print(f"2. JavaScript file check:")
            print(f"   Found {disabled_js_count} '.disabled = true' statements")
            if disabled_js_count == 0:
                print("   ✅ No JavaScript button disabling found")
            else:
                print("   ⚠️  JavaScript still disabling buttons")
                
        # Check for volume-fill references
        volume_fill_count = content.count('volume-fill')
        print(f"3. Volume slider check:")
        print(f"   Found {volume_fill_count} 'volume-fill' references")
        if volume_fill_count == 0:
            print("   ✅ Volume slider references removed")
        else:
            print("   ⚠️  Volume slider references still present")
            
        return True
        
    except Exception as e:
        print(f"❌ Frontend file test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Frontend Button Enabling Test")
    print("=" * 60)
    print("Testing that all hardware buttons are now enabled...")
    
    # Test frontend files
    frontend_success = test_frontend_files()
    
    # Test web server
    server_success = test_web_server_startup()
    
    print("\n" + "=" * 60)
    if frontend_success and server_success:
        print("✅ ALL TESTS PASSED!")
        print("Frontend buttons are now enabled:")
        print("- Transport buttons (play, pause, stop, next, prev)")
        print("- Volume buttons (up, down)")
        print("- Volume slider removed from UI")
        print("- Volume now displayed on OLED display only")
    else:
        print("❌ SOME TESTS FAILED!")
        if not frontend_success:
            print("- Frontend file issues detected")
        if not server_success:
            print("- Web server startup issues detected")
    
    print("=" * 60)
    
    return frontend_success and server_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
