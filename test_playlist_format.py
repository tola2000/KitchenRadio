#!/usr/bin/env python3
"""
Test script to check playlist format changes
"""

import sys
import os
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
    from kitchenradio.mpd.client import KitchenRadioClient
    from kitchenradio.mpd.controller import PlaybackController
    
    print("Testing playlist format...")
    
    # Create client and controller
    client = KitchenRadioClient()
    controller = PlaybackController(client)
    
    # Test connection
    if client.connect():
        print("✓ Connected to MPD")
        
        # Test raw client method
        raw_playlists = client.get_all_playlists()
        print(f"\nRaw playlists from client ({len(raw_playlists)} items):")
        for i, playlist in enumerate(raw_playlists[:3]):  # Show first 3
            print(f"  {i+1}: {playlist}")
        
        # Test controller method (should return just names)
        playlist_names = controller.get_all_playlists()
        print(f"\nPlaylist names from controller ({len(playlist_names)} items):")
        for i, name in enumerate(playlist_names[:10]):  # Show first 10
            print(f"  {i+1}: '{name}'")
            
        client.disconnect()
        print("\n✓ Test completed successfully")
        
    else:
        print("✗ Could not connect to MPD")
        print("Make sure MPD is running and accessible")
        
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Make sure all dependencies are installed")
except Exception as e:
    print(f"✗ Error: {e}")
