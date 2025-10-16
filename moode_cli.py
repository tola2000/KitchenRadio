#!/usr/bin/env python3
"""
MoOde Audio CLI Controller

Command-line interface for controlling MoOde Audio servers.
Provides commands for play, pause, stop, next, previous, and more.
"""

import argparse
import sys
import json
from typing import Optional
from moode_controller import MoOdeAudioController


class MoOdeAudioCLI:
    """Command-line interface for MoOde Audio controller."""
    
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
            print(f"Error: Cannot connect to MoOde server at {self.controller.host}:{self.controller.port}")
            print("Please check that:")
            print("1. MoOde Audio is running")
            print("2. The server address is correct")
            print("3. The server is accessible from this machine")
            return False
        return True
        
    def cmd_play(self, args) -> int:
        """Start playback."""
        if not self.check_connection():
            return 1
            
        if self.controller.play():
            print("Playback started")
            return 0
        else:
            print("Failed to start playback")
            return 1
    
    def cmd_pause(self, args) -> int:
        """Pause playback."""
        if not self.check_connection():
            return 1
            
        if self.controller.pause():
            print("Playback paused")
            return 0
        else:
            print("Failed to pause playback")
            return 1
    
    def cmd_stop(self, args) -> int:
        """Stop playback."""
        if not self.check_connection():
            return 1
            
        if self.controller.stop():
            print("Playback stopped")
            return 0
        else:
            print("Failed to stop playback")
            return 1
    
    def cmd_next(self, args) -> int:
        """Skip to next track."""
        if not self.check_connection():
            return 1
            
        if self.controller.next_track():
            print("Skipped to next track")
            return 0
        else:
            print("Failed to skip to next track")
            return 1
    
    def cmd_previous(self, args) -> int:
        """Skip to previous track."""
        if not self.check_connection():
            return 1
            
        if self.controller.previous_track():
            print("Skipped to previous track")
            return 0
        else:
            print("Failed to skip to previous track")
            return 1
    
    def cmd_toggle(self, args) -> int:
        """Toggle between play and pause."""
        if not self.check_connection():
            return 1
            
        if self.controller.toggle_playback():
            print("Toggled playback")
            return 0
        else:
            print("Failed to toggle playback")
            return 1
    
    def cmd_volume(self, args) -> int:
        """Get or set volume."""
        if not self.check_connection():
            return 1
            
        if args.level is not None:
            # Set volume
            try:
                level = int(args.level)
                if self.controller.set_volume(level):
                    print(f"Volume set to {level}%")
                    return 0
                else:
                    print("Failed to set volume")
                    return 1
            except ValueError:
                print("Invalid volume level. Must be a number between 0 and 100.")
                return 1
        else:
            # Get volume
            volume = self.controller.get_volume()
            if volume is not None:
                print(f"Current volume: {volume}%")
                return 0
            else:
                print("Failed to get volume")
                return 1
    
    def cmd_status(self, args) -> int:
        """Show player status."""
        if not self.check_connection():
            return 1
            
        status = self.controller.get_status()
        if status:
            if args.json:
                print(json.dumps(status, indent=2))
            else:
                print("=== MoOde Audio Status ===")
                for key, value in status.items():
                    print(f"{key.replace('_', ' ').title()}: {value}")
            return 0
        else:
            print("Failed to get status")
            return 1
    
    def cmd_current(self, args) -> int:
        """Show current song information."""
        if not self.check_connection():
            return 1
            
        song = self.controller.get_current_song()
        if song:
            if args.json:
                print(json.dumps(song, indent=2))
            else:
                print("=== Current Song ===")
                # Common fields to display
                fields = ['title', 'artist', 'album', 'time', 'file']
                for field in fields:
                    if field in song:
                        print(f"{field.title()}: {song[field]}")
                        
                # Display any other fields
                for key, value in song.items():
                    if key not in fields:
                        print(f"{key.replace('_', ' ').title()}: {value}")
            return 0
        else:
            print("Failed to get current song information")
            return 1
    
    def cmd_playlist(self, args) -> int:
        """Show current playlist."""
        if not self.check_connection():
            return 1
            
        playlist = self.controller.get_playlist()
        if playlist:
            if args.json:
                print(json.dumps(playlist, indent=2))
            else:
                print("=== Current Playlist ===")
                for i, song in enumerate(playlist, 1):
                    title = song.get('title', song.get('file', 'Unknown'))
                    artist = song.get('artist', 'Unknown Artist')
                    print(f"{i:3d}. {title} - {artist}")
            return 0
        else:
            print("Failed to get playlist")
            return 1
    
    def cmd_seek(self, args) -> int:
        """Seek to position in current track."""
        if not self.check_connection():
            return 1
            
        try:
            position = float(args.position)
            if self.controller.seek(position):
                print(f"Seeked to position {position} seconds")
                return 0
            else:
                print("Failed to seek")
                return 1
        except ValueError:
            print("Invalid position. Must be a number (seconds).")
            return 1
    
    def cmd_info(self, args) -> int:
        """Show system information."""
        if not self.check_connection():
            return 1
            
        info = self.controller.get_system_info()
        if info:
            if args.json:
                print(json.dumps(info, indent=2))
            else:
                print("=== System Information ===")
                for key, value in info.items():
                    print(f"{key.replace('_', ' ').title()}: {value}")
            return 0
        else:
            print("Failed to get system information")
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
    
    # Play command
    subparsers.add_parser("play", help="Start playback")
    
    # Pause command
    subparsers.add_parser("pause", help="Pause playback")
    
    # Stop command
    subparsers.add_parser("stop", help="Stop playback")
    
    # Next command
    subparsers.add_parser("next", help="Skip to next track")
    
    # Previous command
    subparsers.add_parser("previous", help="Skip to previous track")
    
    # Toggle command
    subparsers.add_parser("toggle", help="Toggle between play and pause")
    
    # Volume command
    volume_parser = subparsers.add_parser("volume", help="Get or set volume")
    volume_parser.add_argument("level", nargs="?", help="Volume level (0-100)")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show player status")
    status_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Current song command
    current_parser = subparsers.add_parser("current", help="Show current song information")
    current_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Playlist command
    playlist_parser = subparsers.add_parser("playlist", help="Show current playlist")
    playlist_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Seek command
    seek_parser = subparsers.add_parser("seek", help="Seek to position in current track")
    seek_parser.add_argument("position", help="Position in seconds")
    
    # System info command
    info_parser = subparsers.add_parser("info", help="Show system information")
    info_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
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
    }
    
    command_func = commands.get(args.command)
    if command_func:
        return command_func(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
