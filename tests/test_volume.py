#!/usr/bin/env python3
"""
Volume Test Script for MoOde Audio Controller

This script specifically tests volume get/set functionality with different approaches.
"""

import sys
import time
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moode_controller_v2 import MoOdeAudioController


def test_volume_functionality(host="localhost", port=80):
    """Test volume get and set operations."""
    print(f"🔊 Testing volume functionality on {host}:{port}")
    print("=" * 50)
    
    controller = MoOdeAudioController(host, port)
    
    # Test connection first
    if not controller.is_connected():
        print("❌ Cannot connect to MoOde server")
        return False
    
    print("✅ Connected to MoOde server")
    
    # Test getting current volume
    print("\n📊 Testing volume retrieval...")
    current_volume = controller.get_volume()
    if current_volume is not None:
        print(f"✅ Current volume: {current_volume}%")
    else:
        print("❌ Failed to get current volume")
        return False
    
    # Test setting volume to different values
    test_volumes = [50, 75, current_volume]  # End with original volume
    
    for test_vol in test_volumes:
        print(f"\n🔧 Testing volume set to {test_vol}%...")
        
        if controller.set_volume(test_vol):
            print(f"✅ Volume set command successful")
            
            # Wait a moment for the change to take effect
            time.sleep(1)
            
            # Verify the volume was actually set
            new_volume = controller.get_volume()
            if new_volume is not None:
                if new_volume == test_vol:
                    print(f"✅ Volume verified: {new_volume}%")
                else:
                    print(f"⚠️  Volume mismatch: expected {test_vol}%, got {new_volume}%")
            else:
                print("❌ Failed to verify volume change")
        else:
            print(f"❌ Failed to set volume to {test_vol}%")
            
            # Try manual API testing
            print("🔍 Trying direct API calls...")
            test_direct_volume_apis(controller, test_vol)
    
    return True


def test_direct_volume_apis(controller, volume):
    """Test volume setting with direct API calls."""
    print(f"  Testing direct volume APIs for {volume}%...")
    
    # Test different API endpoints manually
    test_calls = [
        # Correct MoOde format (primary)
        lambda: controller._make_request(f"/command/?setvol%20{volume}"),
        # MPD style command
        lambda: controller._make_request("/engine-mpd.php", "POST", {"cmd": f"setvol {volume}"}),
        # Alternative command format
        lambda: controller._make_request("/engine-cmd.php", "POST", {"cmd": f"setvol {volume}"}),
        # GET style with parameters
        lambda: controller._make_request("/command/", "GET", params={"cmd": "setvol", "vol": str(volume)}),
        # Alternative parameter name
        lambda: controller._make_request("/command/", "GET", params={"cmd": "setvol", "volume": str(volume)}),
        # Direct volume endpoint
        lambda: controller._make_request("/api/volume", "POST", {"volume": volume}),
    ]
    
    for i, test_call in enumerate(test_calls, 1):
        try:
            result = test_call()
            if result is not None:
                print(f"  ✅ API test {i} successful: {result}")
                return True
            else:
                print(f"  ❌ API test {i} failed")
        except Exception as e:
            print(f"  ❌ API test {i} error: {e}")
    
    return False


def main():
    """Main test function."""
    print("🔊 MoOde Audio Volume Test")
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
            print(f"❌ Invalid port: {sys.argv[2]}")
            sys.exit(1)
    
    success = test_volume_functionality(host, port)
    
    if success:
        print("\n✅ Volume testing completed!")
    else:
        print("\n❌ Volume testing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
