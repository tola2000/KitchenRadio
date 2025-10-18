#!/usr/bin/env python3
"""
Simple go-librespot monitoring example
"""

import sys
import time
from pathlib import Path

from kitchenradio.librespot import KitchenRadioLibrespotClient, LibrespotMonitor


def main():
    print("🎵 KitchenRadio go-librespot Monitor Example")
    print("=" * 45)
    
    # Create client and monitor
    client = KitchenRadioLibrespotClient(host="192.168.1.4", port=3678)
    
    # Connect
    print("🔌 Connecting to go-librespot...")
    if not client.connect():
        print("❌ Failed to connect to go-librespot!")
        print("💡 Make sure go-librespot is running and accessible")
        return 1
    
    print("✅ Connected to go-librespot!")
    
    try:
        monitor = LibrespotMonitor(client)
        
        print("\n📡 Starting monitor... (Press Ctrl+C to stop)")
        print("🎵 Watching for track changes and status updates")
        print("-" * 45)
        
        last_track_id = None
        last_state = None
        last_volume = None
        
        while True:
            try:
                # Get current track
                track = monitor.get_current_track()
                track_id = None
                if track:
                    track_id = track.get('id')
                
                # Get player state
                state = monitor.get_player_state()
                
                # Get volume
                volume = monitor.get_volume()
                
                # Check for changes
                if track_id != last_track_id:
                    if track:
                        artists = ", ".join([artist.get('name', 'Unknown') for artist in track.get('artists', [])])
                        album = track.get('album', {}).get('name', 'Unknown')
                        duration = track.get('duration_ms', 0) // 1000
                        mins, secs = divmod(duration, 60)
                        
                        print(f"\n🎵 NEW TRACK:")
                        print(f"   Title: {track.get('name', 'Unknown')}")
                        print(f"   Artist: {artists}")
                        print(f"   Album: {album}")
                        print(f"   Duration: {mins:02d}:{secs:02d}")
                    else:
                        print("\n🔇 NO TRACK PLAYING")
                    
                    last_track_id = track_id
                
                if state != last_state:
                    print(f"\n⏯️ STATE CHANGE: {state}")
                    last_state = state
                
                if volume != last_volume:
                    print(f"\n🔊 VOLUME CHANGE: {volume}%")
                    last_volume = volume
                
                # Show progress for playing tracks
                if track and state == "Playing":
                    progress = monitor.get_progress()
                    if progress:
                        progress_sec = progress // 1000
                        duration_sec = track.get('duration_ms', 0) // 1000
                        
                        if duration_sec > 0:
                            progress_mins, progress_secs = divmod(progress_sec, 60)
                            duration_mins, duration_secs = divmod(duration_sec, 60)
                            percentage = (progress_sec / duration_sec) * 100
                            
                            # Create progress bar
                            bar_width = 30
                            filled = int((percentage / 100) * bar_width)
                            bar = "█" * filled + "░" * (bar_width - filled)
                            
                            print(f"\r⏱️ [{bar}] {progress_mins:02d}:{progress_secs:02d}/{duration_mins:02d}:{duration_secs:02d} ({percentage:.1f}%)", end="", flush=True)
                
                time.sleep(1)  # Check every second
                
            except KeyboardInterrupt:
                print("\n\n👋 Stopping monitor...")
                break
            except Exception as e:
                print(f"\n❌ Monitor error: {e}")
                time.sleep(2)  # Wait before retrying
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    finally:
        # Clean disconnect
        try:
            client.disconnect()
            print("🔌 Disconnected from go-librespot")
        except:
            pass
    
    return 0


if __name__ == "__main__":
    # Configure logging
    import logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise for monitoring
    
    # Run monitor
    exit_code = main()
    sys.exit(exit_code)
