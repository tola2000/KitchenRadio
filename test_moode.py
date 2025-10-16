#!/usr/bin/env python3
"""
Test script for MoOde Audio Controller

This script tests the basic functionality of the MoOde controller library.
"""

import sys
import time
from moode_controller import MoOdeAudioController


def test_connection(host="localhost", port=80):
    """Test connection to MoOde server."""
    print(f"Testing connection to {host}:{port}...")
    
    controller = MoOdeAudioController(host, port)
    
    if controller.is_connected():
        print("✓ Connection successful")
        return controller
    else:
        print("✗ Connection failed")
        print("\nTroubleshooting tips:")
        print("1. Check that MoOde Audio is running")
        print("2. Verify the IP address/hostname is correct")
        print("3. Ensure MoOde web interface is accessible")
        print("4. Check firewall settings")
        return None


def test_basic_commands(controller):
    """Test basic playback commands."""
    print("\nTesting basic commands...")
    
    # Test status
    print("Getting status...")
    status = controller.get_status()
    if status:
        print("✓ Status command working")
        print(f"  Current state: {status.get('state', 'unknown')}")
    else:
        print("✗ Status command failed")
    
    # Test volume
    print("Getting volume...")
    volume = controller.get_volume()
    if volume is not None:
        print(f"✓ Volume command working (current: {volume}%)")
    else:
        print("✗ Volume command failed")
    
    # Test current song
    print("Getting current song...")
    song = controller.get_current_song()
    if song:
        print("✓ Current song command working")
        title = song.get('title', 'Unknown')
        artist = song.get('artist', 'Unknown')
        print(f"  Now playing: {title} by {artist}")
    else:
        print("✗ Current song command failed")


def test_playback_control(controller):
    """Test playback control commands."""
    print("\nTesting playback control...")
    print("Note: This will affect current playback!")
    
    response = input("Continue with playback tests? (y/N): ")
    if response.lower() != 'y':
        print("Skipping playback tests")
        return
    
    original_volume = controller.get_volume()
    
    # Test volume control
    print("Testing volume control...")
    if controller.set_volume(50):
        print("✓ Volume set command working")
        time.sleep(1)
        if original_volume is not None:
            controller.set_volume(original_volume)
            print(f"✓ Volume restored to {original_volume}%")
    else:
        print("✗ Volume set command failed")
    
    # Test toggle playback
    print("Testing playback toggle...")
    if controller.toggle_playback():
        print("✓ Toggle playback working")
        time.sleep(2)
        controller.toggle_playback()  # Toggle back
        print("✓ Toggled back")
    else:
        print("✗ Toggle playback failed")


def main():
    """Main test function."""
    print("MoOde Audio Controller Test")
    print("=" * 30)
    
    # Parse command line arguments
    host = "localhost"
    port = 80
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"Invalid port: {sys.argv[2]}")
            sys.exit(1)
    
    # Test connection
    controller = test_connection(host, port)
    if not controller:
        sys.exit(1)
    
    # Test basic commands
    test_basic_commands(controller)
    
    # Test playback control (optional)
    test_playback_control(controller)
    
    print("\n" + "=" * 30)
    print("Test completed!")
    print("\nNext steps:")
    print("1. Try the CLI: python moode_cli.py status")
    print("2. Test remote control: python moode_cli.py --host <ip> status")
    print("3. Read the README.md for more examples")


if __name__ == "__main__":
    main()
