#!/usr/bin/env python3
"""
Simple MPD connection test
"""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kitchenradio import KitchenRadioClient, PlaybackController


def main():
    print("🎵 KitchenRadio MPD Connection Test")
    
    # Create client
    client = KitchenRadioClient(host="localhost", port=6600)
    
    # Connect
    print("🔌 Connecting to MPD...")
    if not client.connect():
        print("❌ Failed to connect to MPD!")
        print("💡 Make sure MPD is running on localhost:6600")
        return 1
    
    print("✅ Connected to MPD!")
    
    try:
        # Test basic operations
        controller = PlaybackController(client)
        
        # Get current status
        status = controller.get_status()
        print(f"📊 Status: {status}")
        
        # Get current song
        song = controller.get_current_song()
        if song:
            print(f"🎵 Current song: {song.get('artist', 'Unknown')} - {song.get('title', song.get('file', 'Unknown'))}")
        else:
            print("🎵 No current song")
        
        # Get volume
        volume = controller.get_volume()
        print(f"🔊 Volume: {volume}%")
        
        # Get playlist
        playlist = controller.get_playlist()
        print(f"📋 Playlist: {len(playlist)} songs")
        
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return 1
    
    finally:
        client.disconnect()
        print("👋 Disconnected")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
