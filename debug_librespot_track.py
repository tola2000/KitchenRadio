#!/usr/bin/env python3
"""
Test script to debug librespot track info issues
"""

import sys
import os
import json
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

try:
    from kitchenradio.librespot.client import KitchenRadioLibrespotClient
    from kitchenradio.librespot.controller import LibrespotController
    
    print("Testing librespot track info structure...")
    
    # Create client and controller
    client = KitchenRadioLibrespotClient()
    controller = LibrespotController(client)
    
    # Test connection
    if client.connect():
        print("✓ Connected to librespot")
        
        # Test raw status
        print("\n=== Raw Status ===")
        raw_status = client.get_status()
        if raw_status:
            print(f"Raw status type: {type(raw_status)}")
            print(f"Raw status keys: {list(raw_status.keys()) if isinstance(raw_status, dict) else 'Not a dict'}")
            print(f"Raw status: {json.dumps(raw_status, indent=2) if raw_status else 'None'}")
        else:
            print("No raw status returned")
        
        # Test current track
        print("\n=== Current Track ===")
        current_track = client.get_current_track()
        if current_track:
            print(f"Track type: {type(current_track)}")
            print(f"Track keys: {list(current_track.keys()) if isinstance(current_track, dict) else 'Not a dict'}")
            print(f"Track: {json.dumps(current_track, indent=2) if current_track else 'None'}")
        else:
            print("No current track returned")
        
        # Test controller methods
        print("\n=== Controller Status ===")
        controller_status = controller.get_status()
        if controller_status:
            print(f"Controller status: {json.dumps(controller_status, indent=2)}")
        else:
            print("No controller status returned")
        
        controller_track = controller.get_current_track()
        if controller_track:
            print(f"Controller track: {json.dumps(controller_track, indent=2)}")
        else:
            print("No controller track returned")
        
        client.disconnect()
        print("\n✓ Test completed")
        
    else:
        print("✗ Could not connect to librespot")
        print("Make sure go-librespot is running and accessible")
        
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Make sure all dependencies are installed")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
