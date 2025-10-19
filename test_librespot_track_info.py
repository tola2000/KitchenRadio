#!/usr/bin/env python3
"""
Test script to verify librespot track info is working correctly
"""

import sys
import os
import json
import time
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

def test_librespot_track_info():
    """Test the complete librespot track info pipeline"""
    print("=== Testing Librespot Track Info Pipeline ===\n")
    
    try:
        # Test 1: Direct client
        print("1. Testing librespot client directly...")
        from kitchenradio.librespot.client import KitchenRadioLibrespotClient
        
        client = KitchenRadioLibrespotClient()
        if client.connect():
            print("   ✓ Connected to librespot")
            
            status = client.get_status()
            track = client.get_current_track()
            
            print(f"   Status: {status is not None}")
            print(f"   Track: {track is not None}")
            
            if track:
                print(f"   Track data: {json.dumps(track, indent=4)}")
            
            client.disconnect()
        else:
            print("   ✗ Could not connect to librespot")
            return False
        
        # Test 2: Controller
        print("\n2. Testing librespot controller...")
        from kitchenradio.librespot.controller import LibrespotController
        
        client = KitchenRadioLibrespotClient()
        controller = LibrespotController(client)
        
        if client.connect():
            print("   ✓ Connected via controller")
            
            status = controller.get_status()
            track = controller.get_current_track()
            
            print(f"   Controller status: {status is not None}")
            print(f"   Controller track: {track is not None}")
            
            if track:
                print(f"   Controller track data: {json.dumps(track, indent=4)}")
            
            client.disconnect()
        else:
            print("   ✗ Could not connect via controller")
            return False
        
        # Test 3: Full daemon
        print("\n3. Testing full KitchenRadio daemon...")
        from kitchenradio.radio.kitchen_radio import KitchenRadio
        
        # Set debug logging
        import logging
        logging.basicConfig(level=logging.DEBUG)
        
        daemon = KitchenRadio()
        
        if daemon.start():
            print("   ✓ Daemon started")
            
            # Wait a moment for initialization
            time.sleep(2)
            
            status = daemon.get_status()
            print(f"   Daemon status retrieved: {status is not None}")
            
            if status:
                librespot_status = status.get('librespot', {})
                print(f"   Librespot connected: {librespot_status.get('connected', False)}")
                
                current_track = librespot_status.get('current_track')
                if current_track:
                    print(f"   Track title: {current_track.get('title', 'No title')}")
                    print(f"   Track artist: {current_track.get('artist', 'No artist')}")
                    print(f"   Track album: {current_track.get('album', 'No album')}")
                else:
                    print("   No current track in daemon status")
                
                print(f"\n   Full librespot status: {json.dumps(librespot_status, indent=4)}")
            
            daemon.stop()
            print("   ✓ Daemon stopped")
        else:
            print("   ✗ Could not start daemon")
            return False
        
        print("\n✅ All tests completed successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_librespot_track_info()
    sys.exit(0 if success else 1)
