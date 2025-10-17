#!/usr/bin/env python3
"""
Volume Setting Test Script

This script tests different volume setting commands to find the correct format.
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moode_controller_v2 import MoOdeAudioController


def test_volume_setting_formats(host="192.168.1.4", port=80, test_volume=50):
    """Test various volume setting command formats."""
    print(f"🔧 Testing volume setting formats on {host}:{port}")
    print(f"Target volume: {test_volume}%")
    print("=" * 50)
    
    controller = MoOdeAudioController(host, port)
    
    if not controller.is_connected():
        print("❌ Cannot connect to MoOde server")
        return False
    
    print("✅ Connected to MoOde server")
    
    # Get current volume first
    current_vol = controller.get_volume()
    print(f"📊 Current volume: {current_vol}%")
    
    # Test different volume setting formats
    volume_commands = [
        # URL encoded space formats
        f"/command/?setvol%20{test_volume}",
        f"/command/?setvol {test_volume}",
        
        # Alternative command formats
        f"/command/?volume%20{test_volume}",
        f"/command/?vol%20{test_volume}",
        f"/command/?setvolume%20{test_volume}",
        
        # Without space
        f"/command/?setvol{test_volume}",
        f"/command/?volume{test_volume}",
        
        # With equals sign
        f"/command/?setvol={test_volume}",
        f"/command/?volume={test_volume}",
        
        # MPD style with + 
        f"/command/?setvol+{test_volume}",
        
        # Direct number
        f"/command/?{test_volume}",
    ]
    
    for i, cmd in enumerate(volume_commands, 1):
        print(f"\n🧪 Test {i}: {cmd}")
        try:
            result = controller._make_request(cmd)
            if result:
                print(f"  ✅ Response: {result}")
                
                # Check if volume actually changed
                import time
                time.sleep(0.5)  # Give time for change
                new_vol = controller.get_volume()
                if new_vol == test_volume:
                    print(f"  🎯 SUCCESS! Volume changed to {new_vol}%")
                    return cmd
                elif new_vol != current_vol:
                    print(f"  ⚠️  Volume changed to {new_vol}% (expected {test_volume}%)")
                else:
                    print(f"  ❌ Volume unchanged ({new_vol}%)")
            else:
                print(f"  ❌ No response")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"\n📊 Final volume: {controller.get_volume()}%")
    return None


def test_engine_endpoints(host="192.168.1.4", port=80, test_volume=50):
    """Test volume setting through engine endpoints."""
    print(f"\n🔧 Testing engine endpoints for volume setting")
    print("=" * 50)
    
    controller = MoOdeAudioController(host, port)
    
    # Test engine endpoints
    engine_tests = [
        # engine-mpd.php
        {"endpoint": "/engine-mpd.php", "method": "POST", "data": {"cmd": f"setvol {test_volume}"}},
        {"endpoint": "/engine-mpd.php", "method": "POST", "data": {"cmd": f"setvol", "vol": str(test_volume)}},
        
        # engine-cmd.php  
        {"endpoint": "/engine-cmd.php", "method": "POST", "data": {"cmd": f"setvol {test_volume}"}},
        {"endpoint": "/engine-cmd.php", "method": "POST", "data": {"cmd": f"setvol", "vol": str(test_volume)}},
        
        # Direct POST to command
        {"endpoint": "/command/", "method": "POST", "data": {"cmd": f"setvol {test_volume}"}},
        {"endpoint": "/command/", "method": "POST", "data": {"setvol": str(test_volume)}},
        
        # GET with parameters
        {"endpoint": "/command/", "method": "GET", "params": {"cmd": f"setvol {test_volume}"}},
        {"endpoint": "/command/", "method": "GET", "params": {"setvol": str(test_volume)}},
    ]
    
    current_vol = controller.get_volume()
    print(f"📊 Starting volume: {current_vol}%")
    
    for i, test in enumerate(engine_tests, 1):
        print(f"\n🧪 Engine Test {i}: {test['endpoint']}")
        print(f"  Method: {test['method']}")
        print(f"  Data: {test.get('data', test.get('params'))}")
        
        try:
            if test['method'] == 'POST':
                result = controller._make_request(test['endpoint'], "POST", test['data'])
            else:
                result = controller._make_request(test['endpoint'], "GET", params=test['params'])
            
            if result:
                print(f"  ✅ Response: {result}")
                
                import time
                time.sleep(0.5)
                new_vol = controller.get_volume()
                if new_vol == test_volume:
                    print(f"  🎯 SUCCESS! Volume changed to {new_vol}%")
                    return test
                elif new_vol != current_vol:
                    print(f"  ⚠️  Volume changed to {new_vol}% (expected {test_volume}%)")
                    current_vol = new_vol  # Update for next test
                else:
                    print(f"  ❌ Volume unchanged ({new_vol}%)")
            else:
                print(f"  ❌ No response")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"\n📊 Final volume: {controller.get_volume()}%")
    return None


def main():
    """Main test function."""
    print("🔧 MoOde Audio Volume Setting Test")
    print("=" * 35)
    
    host = "192.168.1.4"  # Based on your debug output
    port = 80
    test_volume = 60  # Test volume
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"❌ Invalid port: {sys.argv[2]}")
            sys.exit(1)
    if len(sys.argv) > 3:
        try:
            test_volume = int(sys.argv[3])
        except ValueError:
            print(f"❌ Invalid volume: {sys.argv[3]}")
            sys.exit(1)
    
    # Test command URL formats
    working_cmd = test_volume_setting_formats(host, port, test_volume)
    
    if not working_cmd:
        # Test engine endpoints
        working_engine = test_engine_endpoints(host, port, test_volume)
        
        if working_engine:
            print(f"\n✅ Working engine method found: {working_engine}")
        else:
            print(f"\n❌ No working volume setting method found")
    else:
        print(f"\n✅ Working command found: {working_cmd}")


if __name__ == "__main__":
    main()
