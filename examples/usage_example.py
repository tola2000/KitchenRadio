#!/usr/bin/env python3
"""
Simple usage example for KitchenRadio MPD library
"""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kitchenradio import KitchenRadioClient, PlaybackController, NowPlayingMonitor


def main():
    """Demonstrate basic usage."""
    print("🎵 KitchenRadio Usage Example")
    
    # Create client
    client = KitchenRadioClient(host="localhost", port=6600)
    
    # Connect
    if not client.connect():
        print("❌ Could not connect to MPD")
        print("💡 Make sure MPD is running on localhost:6600")
        return 1
    
    print("✅ Connected to MPD")
    
    try:
        # Create controller
        controller = PlaybackController(client)
        
        # Show current status
        status = controller.get_status()
        song = controller.get_current_song()
        
        print(f"📊 Status: {status.get('state', 'unknown')}")
        print(f"🔊 Volume: {controller.get_volume()}%")
        
        if song:
            title = song.get('title', song.get('file', 'Unknown'))
            artist = song.get('artist', 'Unknown')
            print(f"🎵 Playing: {artist} - {title}")
        else:
            print("🎵 No song playing")
        
        # Demonstrate monitor
        print("\n👁️ Setting up monitor...")
        monitor = NowPlayingMonitor(client)
        
        def on_track_started(track):
            print(f"🎵 Started: {track['artists']} - {track['name']}")
        
        def on_state_changed(old_state, new_state):
            print(f"🔄 State: {old_state} → {new_state}")
        
        monitor.add_callback('track_started', on_track_started)
        monitor.add_callback('state_changed', on_state_changed)
        
        print("✅ Monitor configured (callbacks added)")
        print("💡 In a real application, you'd call monitor.start_monitoring()")
        print("💡 and monitor.run_forever() to continuously monitor events")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    finally:
        client.disconnect()
        print("👋 Disconnected")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
