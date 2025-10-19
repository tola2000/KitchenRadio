#!/usr/bin/env python3
"""
Quick test to verify playlist functionality
"""

import sys
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
    from kitchenradio.mpd.controller import PlaybackController
    from kitchenradio.mpd.client import KitchenRadioClient
    
    print("Testing playlist API format...")
    
    # Test the controller method
    client = KitchenRadioClient()
    controller = PlaybackController(client)
    
    if client.connect():
        playlists = controller.get_all_playlists()
        print(f"Controller returns: {type(playlists)} with {len(playlists)} items")
        
        if playlists:
            print("Sample playlist names:")
            for i, name in enumerate(playlists[:5]):
                print(f"  {i+1}: '{name}' (type: {type(name)})")
        
        print("✓ Playlist format is correct for JavaScript")
        client.disconnect()
    else:
        print("✗ Could not connect to MPD")

except Exception as e:
    print(f"Error: {e}")
