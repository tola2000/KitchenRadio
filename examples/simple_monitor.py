#!/usr/bin/env python3
"""
Simple MPD monitor using Method 3 project config
"""

import sys
from pathlib import Path

# Method 3: Use project config for path setup
sys.path.insert(0, str(Path(__file__).parent.parent))
import project_config

from kitchenradio.mpd import KitchenRadioClient, NowPlayingMonitor


def print_track_started(track):
    """Callback for track started events."""
    print(f"🎵 Started: {track['artists']} - {track['name']}")


def print_track_paused(track):
    """Callback for track paused events."""
    print("⏸️ Paused")


def print_track_resumed(track):
    """Callback for track resumed events."""
    print(f"▶️ Resumed: {track['artists']} - {track['name']}")


def main():
    print("🎵 MPD Monitor - Method 3 Example")
    
    # Create client and monitor
    client = KitchenRadioClient(host="localhost", port=6600)
    monitor = NowPlayingMonitor(client)
    
    # Connect to MPD
    if not client.connect():
        print("❌ Failed to connect to MPD")
        return 1
    
    print("✅ Connected to MPD")
    
    # Set up event callbacks
    monitor.add_callback('track_started', print_track_started)
    monitor.add_callback('track_paused', print_track_paused)
    monitor.add_callback('track_resumed', print_track_resumed)
    
    # Show current track
    monitor.print_current_track()
    
    print("\n📡 Monitoring events... Press Ctrl+C to stop")
    
    try:
        monitor.run_forever()
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    finally:
        client.disconnect()
        print("👋 Disconnected")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
