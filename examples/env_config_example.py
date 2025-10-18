#!/usr/bin/env python3
"""
Example using .env configuration for path and settings
"""

import sys
from pathlib import Path

# Add project root to path to access env_config
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import env_config - this automatically loads .env and sets up paths
import env_config

# Now you can import normally
from kitchenradio.mpd import KitchenRadioClient, PlaybackController


def main():
    print("🎵 KitchenRadio - .env Configuration Example")
    
    # Get configuration
    config = env_config.get_config()
    
    # Print configuration
    config.print_config()
    
    try:
        # Create client using .env defaults
        client = KitchenRadioClient(
            host=config.mpd_host,
            port=config.mpd_port,
            password=config.mpd_password,
            timeout=config.mpd_timeout
        )
        
        print(f"\n🔌 Connecting to MPD at {config.mpd_host}:{config.mpd_port}")
        
        # Connect
        if not client.connect():
            print("❌ Connection failed")
            return 1
        
        print("✅ Connected to MPD using .env configuration!")
        
        # Create controller
        controller = PlaybackController(client)
        
        # Test basic operations
        status = controller.get_status()
        print(f"📊 MPD Status: {status.get('state', 'unknown')}")
        
        volume = controller.get_volume()
        print(f"🔊 Current volume: {volume}%")
        
        # Show current song if playing
        song = controller.get_current_song()
        if song:
            artist = song.get('artist', 'Unknown')
            title = song.get('title', song.get('file', 'Unknown'))
            print(f"🎵 Current: {artist} - {title}")
        else:
            print("🎵 No current song")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        if 'client' in locals():
            client.disconnect()
            print("👋 Disconnected")


if __name__ == "__main__":
    sys.exit(main())
