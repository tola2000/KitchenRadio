#!/usr/bin/env python3
"""
Test state change listeners in KitchenRadio daemon
"""

import sys
import os
import time
import threading
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from env_config import get_project_config
    config = get_project_config()
    
    if config and 'PYTHON_PATHS' in config:
        for path in config['PYTHON_PATHS']:
            if path not in sys.path:
                sys.path.insert(0, path)
except Exception as e:
    print(f"Warning: Could not load env config: {e}")

def test_state_listeners():
    """Test the state change listeners"""
    try:
        from kitchenradio.radio.kitchen_radio import KitchenRadio
        
        # Set debug logging to see state changes
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        print("=== Testing KitchenRadio State Change Listeners ===\n")
        
        # Create and start daemon
        daemon = KitchenRadio()
        
        if not daemon.start():
            print("✗ Failed to start daemon")
            return False
        
        print("✓ KitchenRadio daemon started")
        print("✓ State change listeners should be registered")
        
        # Give some time for initial state detection
        print("\nWaiting for initial states...")
        time.sleep(3)
        
        print("\nConnected backends:")
        if daemon.mpd_connected:
            print("  ✓ MPD connected")
        else:
            print("  ✗ MPD not connected")
            
        if daemon.librespot_connected:
            print("  ✓ Librespot connected")
        else:
            print("  ✗ Librespot not connected")
        
        print(f"\nCurrent source: {daemon.get_current_source()}")
        print(f"Available sources: {[s.value for s in daemon.get_available_sources()]}")
        
        # If both are connected, test some playback commands
        if daemon.mpd_connected and daemon.librespot_connected:
            print("\n=== Testing automatic source switching ===")
            
            # Test MPD playback
            print("\n1. Testing MPD playback...")
            daemon.set_source(daemon.BackendType.MPD)
            time.sleep(1)
            
            if daemon.mpd_controller.play():
                print("   ✓ Started MPD playback")
                time.sleep(3)  # Listen for state changes
                daemon.mpd_controller.pause()
                print("   ✓ Paused MPD playback")
            else:
                print("   ✗ Failed to start MPD playback")
            
            time.sleep(2)
            
            # Test Spotify playback
            print("\n2. Testing Spotify playback...")
            daemon.set_source(daemon.BackendType.LIBRESPOT)
            time.sleep(1)
            
            if daemon.librespot_controller.play():
                print("   ✓ Started Spotify playback")
                time.sleep(3)  # Listen for state changes
                daemon.librespot_controller.pause()
                print("   ✓ Paused Spotify playback")
            else:
                print("   ✗ Failed to start Spotify playback")
                
        else:
            print("\nSkipping playback tests (not all backends connected)")
            print("But state listeners are still active for monitoring...")
            
            # Just wait a bit to see if any state changes occur
            print("Monitoring for 10 seconds...")
            time.sleep(10)
        
        daemon.stop()
        print("\n✓ Test completed successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_state_listeners()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
