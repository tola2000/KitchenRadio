#!/usr/bin/env python3
"""
Simple go-librespot connection test
"""

import sys
from pathlib import Path

from kitchenradio.librespot import KitchenRadioLibrespotClient, LibrespotController


def main():
    print("🎵 KitchenRadio go-librespot Connection Test")
    
    # Create client (using default localhost:3678)
    client = KitchenRadioLibrespotClient(host="192.168.1.4", port=3678)
    
    # Connect and test
    print("🔌 Connecting to go-librespot...")
    if not client.connect():
        print("❌ Failed to connect to go-librespot!")
        print("💡 Make sure go-librespot is running on 192.168.1.4:3678")
        print("💡 Start go-librespot with: go-librespot --name 'KitchenRadio' --backend pulseaudio --device-type speaker --initial-volume 50 --enable-volume-normalisation --normalisation-gain-type track --api-port 3678")
        return 1
    
    print("✅ Connected to go-librespot!")
    
    try:
        # Test basic operations
        controller = LibrespotController(client)
        
        # Get current status
        status = controller.get_status()
        print(f"📊 Status: {status}")
        
        # Get current track
        current_track = controller.get_current_track()
        if current_track:
            print(f"🎵 Current track: {current_track.get('artists', [{}])[0].get('name', 'Unknown')} - {current_track.get('name', 'Unknown')}")
            print(f"🎧 Album: {current_track.get('album', {}).get('name', 'Unknown')}")
            print(f"⏱️ Duration: {current_track.get('duration_ms', 0) // 1000}s")
        else:
            print("🎵 No current track")
        
        # Get volume
        volume = controller.get_volume()
        print(f"🔊 Volume: {volume}%")
        
        # Get player state
        player_state = controller.get_player_state()
        print(f"⏯️ Player state: {player_state}")
        
        # Test device info
        device_info = client.get_device_info()
        if device_info:
            print(f"📱 Device: {device_info.get('name', 'Unknown')} (ID: {device_info.get('id', 'Unknown')})")
            print(f"🔧 Type: {device_info.get('device_type', 'Unknown')}")
            print(f"🎚️ Volume supported: {device_info.get('volume', 0)}%")
        
        # Test API endpoints availability
        print("\n🔍 Testing API endpoints:")
        
        # Test /status endpoint
        status_data = client._send_request("/status")
        if status_data:
            print("✅ /status endpoint working")
        else:
            print("❌ /status endpoint failed")
        
        # Test /player endpoint
        player_data = client._send_request("/player")
        if player_data:
            print("✅ /player endpoint working")
        else:
            print("❌ /player endpoint failed")
        
        # Test /metadata endpoint (if track is playing)
        if current_track:
            metadata = client._send_request("/metadata")
            if metadata:
                print("✅ /metadata endpoint working")
            else:
                print("❌ /metadata endpoint failed")
        else:
            print("ℹ️ /metadata endpoint not tested (no track playing)")
        
        print("\n✅ All connection tests passed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
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
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Run test
    exit_code = main()
    sys.exit(exit_code)
