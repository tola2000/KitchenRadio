#!/usr/bin/env python3
"""
MoOde Audio CLI Controller - Updated Version

Command-line interface for controlling MoOde Audio servers using the improved controller.
Provides commands for play, pause, stop, next, previous, and more.
"""

import argparse
import sys
import json
import time
from typing import Optional
from moode_controller_v2 import MoOdeAudioController


class MoOdeAudioCLI:
    """Command-line interface for MoOde Audio controller - Updated version."""
    
    def __init__(self, host: str = "localhost", port: int = 80):
        """
        Initialize the CLI controller.
        
        Args:
            host: MoOde server hostname or IP address
            port: MoOde server port
        """
        self.controller = MoOdeAudioController(host, port)
        
    def check_connection(self) -> bool:
        """Check if we can connect to the MoOde server."""
        if not self.controller.is_connected():
            print(f"❌ Error: Cannot connect to MoOde server at {self.controller.host}:{self.controller.port}")
            print("\n🔧 Troubleshooting:")
            print("1. Check that MoOde Audio is running")
            print("2. Verify the server address is correct")
            print("3. Ensure the server is accessible from this machine")
            print("4. Try accessing the web interface in a browser")
            print(f"   → http://{self.controller.host}:{self.controller.port}")
            return False
        return True
        
    def cmd_play(self, args) -> int:
        """Start playback."""
        if not self.check_connection():
            return 1
            
        print("▶️  Starting playback...")
        if self.controller.play():
            print("✅ Playback started")
            return 0
        else:
            print("❌ Failed to start playback")
            return 1
    
    def cmd_pause(self, args) -> int:
        """Pause playback."""
        if not self.check_connection():
            return 1
            
        print("⏸️  Pausing playback...")
        if self.controller.pause():
            print("✅ Playback paused")
            return 0
        else:
            print("❌ Failed to pause playback")
            return 1
    
    def cmd_stop(self, args) -> int:
        """Stop playback."""
        if not self.check_connection():
            return 1
            
        print("⏹️  Stopping playback...")
        if self.controller.stop():
            print("✅ Playback stopped")
            return 0
        else:
            print("❌ Failed to stop playback")
            return 1
    
    def cmd_next(self, args) -> int:
        """Skip to next track."""
        if not self.check_connection():
            return 1
            
        print("⏭️  Skipping to next track...")
        if self.controller.next_track():
            print("✅ Skipped to next track")
            # Show current song after skipping
            time.sleep(0.5)  # Give time for track to change
            song = self.controller.get_current_song()
            if song and 'title' in song:
                print(f"🎵 Now playing: {song.get('title', 'Unknown')} - {song.get('artist', 'Unknown Artist')}")
            return 0
        else:
            print("❌ Failed to skip to next track")
            return 1
    
    def cmd_previous(self, args) -> int:
        """Skip to previous track."""
        if not self.check_connection():
            return 1
            
        print("⏮️  Skipping to previous track...")
        if self.controller.previous_track():
            print("✅ Skipped to previous track")
            # Show current song after skipping
            time.sleep(0.5)  # Give time for track to change
            song = self.controller.get_current_song()
            if song and 'title' in song:
                print(f"🎵 Now playing: {song.get('title', 'Unknown')} - {song.get('artist', 'Unknown Artist')}")
            return 0
        else:
            print("❌ Failed to skip to previous track")
            return 1
    
    def cmd_toggle(self, args) -> int:
        """Toggle between play and pause."""
        if not self.check_connection():
            return 1
            
        print("🔄 Toggling playback...")
        if self.controller.toggle_playback():
            # Check current state to show appropriate message
            status = self.controller.get_status()
            if status:
                state = status.get('state', '').lower()
                if state == 'play':
                    print("✅ Playback resumed")
                elif state == 'pause':
                    print("✅ Playback paused")
                else:
                    print("✅ Playback toggled")
            else:
                print("✅ Playback toggled")
            return 0
        else:
            print("❌ Failed to toggle playback")
            return 1
    
    def cmd_volume(self, args) -> int:
        """Get or set volume."""
        if not self.check_connection():
            return 1
            
        if args.level is not None:
            # Set volume
            try:
                level = int(args.level)
                if not 0 <= level <= 100:
                    print("❌ Volume level must be between 0 and 100")
                    return 1
                    
                print(f"🔊 Setting volume to {level}%...")
                if self.controller.set_volume(level):
                    print(f"✅ Volume set to {level}%")
                    return 0
                else:
                    print("❌ Failed to set volume")
                    return 1
            except ValueError:
                print("❌ Invalid volume level. Must be a number between 0 and 100.")
                return 1
        else:
            # Get volume
            volume = self.controller.get_volume()
            if volume is not None:
                print(f"🔊 Current volume: {volume}%")
                return 0
            else:
                print("❌ Failed to get volume")
                return 1
    
    def cmd_status(self, args) -> int:
        """Show player status."""
        if not self.check_connection():
            return 1
            
        print("📊 Getting player status...")
        status = self.controller.get_status()
        if status:
            if args.json:
                print(json.dumps(status, indent=2))
            else:
                print("\n" + "=" * 40)
                print("🎵 MoOde Audio Player Status")
                print("=" * 40)
                
                # Format common status fields nicely
                state = status.get('state', 'unknown').title()
                print(f"State: {state}")
                
                if 'volume' in status:
                    print(f"Volume: {status['volume']}%")
                
                if 'time' in status and 'duration' in status:
                    current_time = status.get('time', '0')
                    duration = status.get('duration', '0')
                    print(f"Time: {current_time}s / {duration}s")
                
                # Display other fields
                skip_fields = {'state', 'volume', 'time', 'duration'}
                for key, value in status.items():
                    if key not in skip_fields:
                        formatted_key = key.replace('_', ' ').title()
                        print(f"{formatted_key}: {value}")
                        
                print("=" * 40)
            return 0
        else:
            print("❌ Failed to get status")
            return 1
    
    def cmd_current(self, args) -> int:
        """Show current song information."""
        if not self.check_connection():
            return 1
            
        print("🎵 Getting current song...")
        song = self.controller.get_current_song()
        if song:
            if args.json:
                print(json.dumps(song, indent=2))
            else:
                print("\n" + "=" * 40)
                print("🎵 Currently Playing")
                print("=" * 40)
                
                # Display main song info
                title = song.get('title', song.get('file', 'Unknown Title'))
                artist = song.get('artist', 'Unknown Artist')
                album = song.get('album', 'Unknown Album')
                
                print(f"Title:  {title}")
                print(f"Artist: {artist}")
                print(f"Album:  {album}")
                
                if 'time' in song:
                    print(f"Duration: {song['time']}s")
                
                if 'track' in song:
                    print(f"Track: {song['track']}")
                
                if 'date' in song:
                    print(f"Year: {song['date']}")
                
                if 'genre' in song:
                    print(f"Genre: {song['genre']}")
                
                # Display any other fields
                skip_fields = {'title', 'artist', 'album', 'time', 'track', 'date', 'genre', 'file'}
                for key, value in song.items():
                    if key not in skip_fields:
                        formatted_key = key.replace('_', ' ').title()
                        print(f"{formatted_key}: {value}")
                        
                print("=" * 40)
            return 0
        else:
            print("❌ Failed to get current song information")
            return 1
    
    def cmd_playlist(self, args) -> int:
        """Show current playlist."""
        if not self.check_connection():
            return 1
            
        print("📋 Getting playlist...")
        playlist = self.controller.get_playlist()
        if playlist:
            if args.json:
                print(json.dumps(playlist, indent=2))
            else:
                print(f"\n📋 Current Playlist ({len(playlist)} songs)")
                print("=" * 60)
                
                for i, song in enumerate(playlist, 1):
                    title = song.get('title', song.get('file', 'Unknown'))
                    artist = song.get('artist', 'Unknown Artist')
                    duration = song.get('time', '')
                    
                    if duration:
                        duration_str = f" ({duration}s)"
                    else:
                        duration_str = ""
                    
                    print(f"{i:3d}. {title} - {artist}{duration_str}")
                    
                print("=" * 60)
            return 0
        else:
            print("❌ Failed to get playlist")
            return 1
    
    def cmd_seek(self, args) -> int:
        """Seek to position in current track."""
        if not self.check_connection():
            return 1
            
        try:
            position = float(args.position)
            print(f"⏩ Seeking to position {position} seconds...")
            if self.controller.seek(position):
                print(f"✅ Seeked to position {position} seconds")
                return 0
            else:
                print("❌ Failed to seek")
                return 1
        except ValueError:
            print("❌ Invalid position. Must be a number (seconds).")
            return 1
    
    def cmd_info(self, args) -> int:
        """Show system information."""
        if not self.check_connection():
            return 1
            
        print("ℹ️  Getting system information...")
        info = self.controller.get_system_info()
        if info:
            if args.json:
                print(json.dumps(info, indent=2))
            else:
                print("\n" + "=" * 40)
                print("ℹ️  System Information")
                print("=" * 40)
                for key, value in info.items():
                    formatted_key = key.replace('_', ' ').title()
                    print(f"{formatted_key}: {value}")
                print("=" * 40)
            return 0
        else:
            print("❌ Failed to get system information")
            return 1
    
    def cmd_connection(self, args) -> int:
        """Test connection to MoOde server."""
        print(f"🔗 Testing connection to {self.controller.host}:{self.controller.port}...")
        
        if self.controller.is_connected():
            print("✅ Connection successful!")
            
            # Try to get basic info to verify functionality
            status = self.controller.get_status()
            if status:
                state = status.get('state', 'unknown')
                print(f"🎵 Player state: {state}")
                
                volume = self.controller.get_volume()
                if volume is not None:
                    print(f"🔊 Volume: {volume}%")
            return 0
        else:
            print("❌ Connection failed!")
            return 1


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Control MoOde Audio server via command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s play                    # Start playback
  %(prog)s pause                   # Pause playback
  %(prog)s stop                    # Stop playback
  %(prog)s next                    # Skip to next track
  %(prog)s previous                # Skip to previous track
  %(prog)s volume 75               # Set volume to 75%%
  %(prog)s volume                  # Show current volume
  %(prog)s status                  # Show player status
  %(prog)s current                 # Show current song
  %(prog)s connection              # Test connection
  %(prog)s --host 192.168.1.100 play  # Control remote server
        """
    )
    
    parser.add_argument(
        "--host", 
        default="localhost",
        help="MoOde server hostname or IP address (default: localhost)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=80,
        help="MoOde server port (default: 80)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Playback commands
    subparsers.add_parser("play", help="Start playback")
    subparsers.add_parser("pause", help="Pause playback")
    subparsers.add_parser("stop", help="Stop playback")
    subparsers.add_parser("next", help="Skip to next track")
    subparsers.add_parser("previous", help="Skip to previous track")
    subparsers.add_parser("toggle", help="Toggle between play and pause")
    
    # Volume command
    volume_parser = subparsers.add_parser("volume", help="Get or set volume")
    volume_parser.add_argument("level", nargs="?", help="Volume level (0-100)")
    
    # Information commands
    status_parser = subparsers.add_parser("status", help="Show player status")
    status_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    current_parser = subparsers.add_parser("current", help="Show current song information")
    current_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    playlist_parser = subparsers.add_parser("playlist", help="Show current playlist")
    playlist_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    info_parser = subparsers.add_parser("info", help="Show system information")
    info_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Advanced commands
    seek_parser = subparsers.add_parser("seek", help="Seek to position in current track")
    seek_parser.add_argument("position", help="Position in seconds")
    
    # Utility commands
    subparsers.add_parser("connection", help="Test connection to MoOde server")
    
    return parser


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = MoOdeAudioCLI(args.host, args.port)
    
    # Map commands to methods
    commands = {
        "play": cli.cmd_play,
        "pause": cli.cmd_pause,
        "stop": cli.cmd_stop,
        "next": cli.cmd_next,
        "previous": cli.cmd_previous,
        "toggle": cli.cmd_toggle,
        "volume": cli.cmd_volume,
        "status": cli.cmd_status,
        "current": cli.cmd_current,
        "playlist": cli.cmd_playlist,
        "seek": cli.cmd_seek,
        "info": cli.cmd_info,
        "connection": cli.cmd_connection,
    }
    
    command_func = commands.get(args.command)
    if command_func:
        return command_func(args)
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
