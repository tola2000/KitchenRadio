#!/usr/bin/env python3
"""
go-librespot playback control example
"""

import sys
import time
from pathlib import Path

from kitchenradio.librespot import KitchenRadioLibrespotClient, LibrespotController


def display_current_track(controller):
    """Display information about the current track"""
    track = controller.get_current_track()
    if track:
        artists = ", ".join([artist.get('name', 'Unknown') for artist in track.get('artists', [])])
        print(f"🎵 Now playing: {artists} - {track.get('name', 'Unknown')}")
        print(f"🎧 Album: {track.get('album', {}).get('name', 'Unknown')}")
        
        # Progress information
        progress = controller.get_progress()
        duration = track.get('duration_ms', 0) // 1000
        if progress and duration > 0:
            progress_sec = progress // 1000
            mins_prog, secs_prog = divmod(progress_sec, 60)
            mins_dur, secs_dur = divmod(duration, 60)
            print(f"⏱️ Progress: {mins_prog:02d}:{secs_prog:02d} / {mins_dur:02d}:{secs_dur:02d}")
    else:
        print("🎵 No track currently playing")


def main():
    print("🎵 KitchenRadio go-librespot Playback Control Example")
    print("=" * 50)
    
    # Create client and controller
    client = KitchenRadioLibrespotClient(host="192.168.1.4", port=3678)
    
    # Connect
    print("🔌 Connecting to go-librespot...")
    if not client.connect():
        print("❌ Failed to connect to go-librespot!")
        print("💡 Make sure go-librespot is running and accessible")
        return 1
    
    print("✅ Connected to go-librespot!")
    
    try:
        controller = LibrespotController(client)
        
        # Show initial status
        print("\n📊 Initial Status:")
        status = controller.get_status()
        print(f"Player state: {controller.get_player_state()}")
        print(f"Volume: {controller.get_volume()}%")
        display_current_track(controller)
        
        # Interactive demo
        print("\n🎮 Interactive Demo:")
        print("Commands: [p]lay, [pause], [n]ext, [prev], [v]olume, [s]tatus, [q]uit")
        
        while True:
            try:
                cmd = input("\n> ").strip().lower()
                
                if cmd in ['q', 'quit', 'exit']:
                    break
                    
                elif cmd in ['p', 'play']:
                    if controller.play():
                        print("▶️ Playback started")
                    else:
                        print("❌ Failed to start playback")
                        
                elif cmd in ['pause']:
                    if controller.pause():
                        print("⏸️ Playback paused")
                    else:
                        print("❌ Failed to pause playback")
                        
                elif cmd in ['n', 'next']:
                    if controller.next_track():
                        print("⏭️ Skipped to next track")
                        time.sleep(0.5)  # Give time for track change
                        display_current_track(controller)
                    else:
                        print("❌ Failed to skip to next track")
                        
                elif cmd in ['prev', 'previous']:
                    if controller.previous_track():
                        print("⏮️ Skipped to previous track")
                        time.sleep(0.5)  # Give time for track change
                        display_current_track(controller)
                    else:
                        print("❌ Failed to skip to previous track")
                        
                elif cmd in ['v', 'volume']:
                    try:
                        vol_input = input("Enter volume (0-100): ").strip()
                        volume = int(vol_input)
                        if 0 <= volume <= 100:
                            if controller.set_volume(volume):
                                print(f"🔊 Volume set to {volume}%")
                            else:
                                print("❌ Failed to set volume")
                        else:
                            print("❌ Volume must be between 0 and 100")
                    except ValueError:
                        print("❌ Please enter a valid number")
                        
                elif cmd in ['s', 'status']:
                    print("\n📊 Current Status:")
                    print(f"Player state: {controller.get_player_state()}")
                    print(f"Volume: {controller.get_volume()}%")
                    display_current_track(controller)
                    
                    # Device info
                    device_info = client.get_device_info()
                    if device_info:
                        print(f"📱 Device: {device_info.get('name', 'Unknown')}")
                        print(f"🔧 Type: {device_info.get('device_type', 'Unknown')}")
                        
                else:
                    print("❓ Unknown command. Use [p]lay, [pause], [n]ext, [prev], [v]olume, [s]tatus, [q]uit")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
    
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
    logging.basicConfig(level=logging.WARNING)  # Reduce noise for interactive demo
    
    # Run demo
    exit_code = main()
    sys.exit(exit_code)
