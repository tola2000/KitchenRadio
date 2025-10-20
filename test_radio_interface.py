#!/usr/bin/env python3
"""
Test script for the KitchenRadio Physical Radio Interface

Starts the web server and provides access to the physical radio interface.
"""

import sys
import os
import logging
import webbrowser
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from kitchenradio.web.kitchen_radio_web import KitchenRadioWeb

def main():
    """Run the radio interface test"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    print("=" * 60)
    print("KitchenRadio Physical Radio Interface Test")
    print("=" * 60)
    print("ℹ️  This server can start even if MPD and Spotify are not available")
    print("   Use the reconnect feature if backends become available later")
    print()
    
    # Create KitchenRadio Web API with radio interface
    api = KitchenRadioWeb(
        kitchen_radio=None,  # Will create its own
        host='127.0.0.1',
        port=5001,
        enable_gpio=False  # Disable GPIO for testing
    )
    
    if api.start():
        print("✅ KitchenRadio Web API started successfully")
        print(f"🌐 Physical Radio Interface: http://127.0.0.1:5001/radio")
        print(f"🔧 API Base URL: http://127.0.0.1:5001/api")
        print()
        print("Available endpoints:")
        print("  Physical Interface:")
        print("    GET  / - Redirect to radio interface")
        print("    GET  /radio - Physical radio interface")
        print("  Button Control:")
        print("    GET  /api/buttons - List all buttons")
        print("    POST /api/button/<name> - Press a button")
        print("    GET  /api/button/<name>/info - Get button info")
        print("    GET  /api/buttons/stats - Get button statistics")
        print("  Display Control:")
        print("    GET  /api/display/image - Get display image (PNG)")
        print("    GET  /api/display/ascii - Get display as ASCII art")
        print("    POST /api/display/clear - Clear display")
        print("    POST /api/display/test - Show test pattern")
        print("    GET  /api/display/stats - Get display statistics")
        print("  Menu System:")
        print("    GET  /api/menu - Get menu options for active source")
        print("    POST /api/menu/action - Execute menu action")
        print("  System:")
        print("    GET  /api/status - Get API and radio status")
        print("    GET  /api/health - Health check")
        print("    POST /api/reconnect - Reconnect to backends")
        print()
        
        # Try to open the interface in browser
        try:
            print("🚀 Opening radio interface in browser...")
            webbrowser.open('http://127.0.0.1:5001/radio')
            time.sleep(1)
        except Exception as e:
            print(f"⚠️  Could not open browser automatically: {e}")
            print("   Please manually open: http://127.0.0.1:5001/radio")
        
        print("\n🎵 KitchenRadio Physical Interface is ready!")
        print("   Use the web interface to control your radio")
        print("   Press Ctrl+C to stop")
        
        try:
            # Keep running
            while api.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        finally:
            api.stop()
            print("✅ KitchenRadio stopped successfully")
    else:
        print("❌ Failed to start KitchenRadio Web API")
        sys.exit(1)

if __name__ == "__main__":
    main()
