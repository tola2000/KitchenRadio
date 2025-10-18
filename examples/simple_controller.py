#!/usr/bin/env python3
"""
Simple MPD controller using Method 3 project config
"""

import sys
import argparse
from pathlib import Path

# Method 3: Use project config for path setup
sys.path.insert(0, str(Path(__file__).parent.parent))
import project_config

from kitchenradio.mpd import KitchenRadioClient, PlaybackController


def main():
    parser = argparse.ArgumentParser(description='Simple MPD controller')
    parser.add_argument('--host', default='localhost', help='MPD host')
    parser.add_argument('--port', type=int, default=6600, help='MPD port')
    parser.add_argument('command', choices=['play', 'pause', 'stop', 'next', 'prev', 'status', 'volume'], help='Command')
    parser.add_argument('arg', nargs='?', help='Command argument (e.g., volume level)')
    
    args = parser.parse_args()
    
    print(f"🎛️ MPD Controller - Method 3 Example")
    print(f"🔌 Connecting to {args.host}:{args.port}")
    
    # Create client and controller
    client = KitchenRadioClient(host=args.host, port=args.port)
    controller = PlaybackController(client)
    
    # Connect
    if not client.connect():
        print("❌ Failed to connect to MPD")
        return 1
    
    print("✅ Connected!")
    
    try:
        # Execute command
        if args.command == 'play':
            success = controller.play()
            print("▶️ Play" if success else "❌ Play failed")
            
        elif args.command == 'pause':
            success = controller.pause()
            print("⏸️ Pause" if success else "❌ Pause failed")
            
        elif args.command == 'stop':
            success = controller.stop()
            print("⏹️ Stop" if success else "❌ Stop failed")
            
        elif args.command == 'next':
            success = controller.next_track()
            print("⏭️ Next" if success else "❌ Next failed")
            
        elif args.command == 'prev':
            success = controller.previous_track()
            print("⏮️ Previous" if success else "❌ Previous failed")
            
        elif args.command == 'volume':
            if not args.arg:
                volume = controller.get_volume()
                print(f"🔊 Volume: {volume}%")
            else:
                level = int(args.arg)
                success = controller.set_volume(level)
                print(f"🔊 Volume set to {level}%" if success else "❌ Volume change failed")
                
        elif args.command == 'status':
            status = controller.get_status()
            song = controller.get_current_song()
            
            print(f"📊 Status:")
            print(f"  State: {status.get('state', 'unknown')}")
            print(f"  Volume: {status.get('volume', 'unknown')}%")
            
            if song:
                artist = song.get('artist', 'Unknown')
                title = song.get('title', song.get('file', 'Unknown'))
                print(f"  Track: {artist} - {title}")
            else:
                print(f"  Track: None")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    finally:
        client.disconnect()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
