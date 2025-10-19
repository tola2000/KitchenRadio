#!/usr/bin/env python3
"""
Test script to verify source switching functionality
"""

import sys
import os
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

try:
    from kitchenradio.radio.kitchen_radio import KitchenRadio, BackendType
    
    print("Testing source switching functionality...")
    
    # Create daemon
    daemon = KitchenRadio()
    
    if daemon.start():
        print("✓ KitchenRadio daemon started")
        
        # Check available sources
        available = daemon.get_available_sources()
        print(f"Available sources: {[s.value for s in available]}")
        
        # Test source switching
        if BackendType.MPD in available:
            print("\nTesting MPD source...")
            if daemon.set_source(BackendType.MPD):
                print("✓ Set source to MPD")
                current = daemon.get_current_source()
                print(f"Current source: {current.value if current else 'None'}")
            else:
                print("✗ Failed to set source to MPD")
        
        if BackendType.LIBRESPOT in available:
            print("\nTesting Spotify source...")
            if daemon.set_source(BackendType.LIBRESPOT):
                print("✓ Set source to Spotify")
                current = daemon.get_current_source()
                print(f"Current source: {current.value if current else 'None'}")
            else:
                print("✗ Failed to set source to Spotify")
        
        # Test convenience methods
        if BackendType.MPD in available:
            print("\nTesting convenience methods...")
            if daemon.switch_to_mpd():
                print("✓ Switched to MPD using convenience method")
            
        # Show final status
        print("\nFinal status:")
        status = daemon.get_status()
        print(f"Current source: {status.get('current_source', 'None')}")
        print(f"Available sources: {status.get('available_sources', [])}")
        
        daemon.stop()
        print("\n✓ Source switching test completed")
        
    else:
        print("✗ Could not start KitchenRadio daemon")
        print("Make sure at least one backend (MPD or librespot) is available")
        
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Make sure all dependencies are installed")
except Exception as e:
    print(f"✗ Error: {e}")
