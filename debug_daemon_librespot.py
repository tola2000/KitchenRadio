#!/usr/bin/env python3
"""
Test script to debug KitchenRadio daemon librespot status
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
    from kitchenradio.radio.kitchen_radio import KitchenRadio
    
    print("Testing KitchenRadio daemon librespot status...")
    
    # Create daemon
    daemon = KitchenRadio()
    
    # Start daemon
    if daemon.start():
        print("✓ KitchenRadio daemon started")
        
        # Get full status
        print("\n=== Full Daemon Status ===")
        full_status = daemon.get_status()
        print(f"Full status: {json.dumps(full_status, indent=2, default=str)}")
        
        # Check librespot specific status
        librespot_status = full_status.get('librespot', {})
        print(f"\n=== Librespot Status from Daemon ===")
        print(f"Connected: {librespot_status.get('connected', False)}")
        print(f"State: {librespot_status.get('state', 'unknown')}")
        print(f"Volume: {librespot_status.get('volume', 'unknown')}")
        
        current_track = librespot_status.get('current_track')
        print(f"Current track: {json.dumps(current_track, indent=2) if current_track else 'None'}")
        
        if current_track:
            print(f"Track title: {current_track.get('title', 'No title')}")
            print(f"Track artist: {current_track.get('artist', 'No artist')}")
            print(f"Track album: {current_track.get('album', 'No album')}")
        
        # Test individual components if connected
        if daemon.librespot_connected:
            print(f"\n=== Direct Component Tests ===")
            
            try:
                # Test controller directly
                direct_track = daemon.librespot_controller.get_current_track()
                print(f"Direct controller track: {json.dumps(direct_track, indent=2) if direct_track else 'None'}")
                
                direct_status = daemon.librespot_controller.get_status()
                print(f"Direct controller status: {json.dumps(direct_status, indent=2) if direct_status else 'None'}")
                
            except Exception as e:
                print(f"Error testing direct components: {e}")
                import traceback
                traceback.print_exc()
        
        daemon.stop()
        print("\n✓ Test completed")
        
    else:
        print("✗ Could not start KitchenRadio daemon")
        
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Make sure all dependencies are installed")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
