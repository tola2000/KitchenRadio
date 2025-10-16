#!/usr/bin/env python3
"""
Debug script to examine MoOde Audio status response

This script shows the exact response from the status command to help debug
why get_volume() might be failing.
"""

import json
import sys
from moode_controller_v2 import MoOdeAudioController


def debug_status_response(host="localhost", port=80):
    """Debug the status response to understand its structure."""
    print(f"🔍 Debugging MoOde status response on {host}:{port}")
    print("=" * 60)
    
    controller = MoOdeAudioController(host, port)
    
    # Test connection first
    if not controller.is_connected():
        print("❌ Cannot connect to MoOde server")
        return False
    
    print("✅ Connected to MoOde server")
    
    # Get and examine status response
    print("\n📊 Getting status response...")
    status = controller.get_status()
    
    if status:
        print("✅ Status response received!")
        print("\n📋 Raw status response:")
        print(json.dumps(status, indent=2, default=str))
        
        print(f"\n🔑 Available keys: {list(status.keys())}")
        
        # Look for volume-related fields
        volume_related = {}
        for key, value in status.items():
            key_lower = key.lower()
            if any(vol_term in key_lower for vol_term in ['vol', 'mix', 'audio', 'sound', 'level']):
                volume_related[key] = value
        
        if volume_related:
            print(f"\n🔊 Volume-related fields found:")
            for key, value in volume_related.items():
                print(f"  {key}: {value} (type: {type(value).__name__})")
        else:
            print("\n⚠️  No obvious volume-related fields found")
            print("All fields:")
            for key, value in status.items():
                print(f"  {key}: {value} (type: {type(value).__name__})")
        
        # Test volume extraction
        print(f"\n🧪 Testing get_volume() method...")
        volume = controller.get_volume()
        if volume is not None:
            print(f"✅ get_volume() returned: {volume}%")
        else:
            print("❌ get_volume() returned None")
            
    else:
        print("❌ Failed to get status response")
        return False
    
    # Test direct volume-related commands
    print(f"\n🔧 Testing direct volume commands...")
    direct_commands = [
        "/command/?mixer%20volume",
        "/command/?volume", 
        "/command/?getvol",
        "/command/?status",
    ]
    
    for cmd in direct_commands:
        print(f"\n  Testing: {cmd}")
        result = controller._make_request(cmd)
        if result:
            print(f"    ✅ Response: {json.dumps(result, indent=4, default=str)[:200]}...")
        else:
            print(f"    ❌ No response")
    
    return True


def main():
    """Main debug function."""
    print("🔍 MoOde Audio Status Debug Tool")
    print("=" * 35)
    
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
    
    success = debug_status_response(host, port)
    
    if success:
        print("\n✅ Debug completed!")
        print("\n💡 Tips:")
        print("- Look for volume-related fields in the status response")
        print("- Check if volume values are strings or numbers")
        print("- Try different volume commands if needed")
    else:
        print("\n❌ Debug failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
