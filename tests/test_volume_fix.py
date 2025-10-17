#!/usr/bin/env python3
"""
Quick test script to verify get_volume fix
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moode_controller_v2 import MoOdeAudioController

def test_volume_fix(host="192.168.1.4", port=80):
    """Test the fixed get_volume method."""
    print(f"🔊 Testing fixed get_volume method on {host}:{port}")
    print("=" * 50)
    
    controller = MoOdeAudioController(host, port)
    
    if not controller.is_connected():
        print("❌ Cannot connect to MoOde server")
        return False
    
    print("✅ Connected to MoOde server")
    
    # Test get_status first
    print("\n📊 Testing get_status...")
    status = controller.get_status()
    if status:
        print("✅ Status retrieval successful")
        print("📋 Status fields:")
        for key, value in status.items():
            if isinstance(value, str) and 'volume' in value.lower():
                print(f"  🔊 {key}: {value}")
            else:
                print(f"  {key}: {value}")
    else:
        print("❌ Status retrieval failed")
        return False
    
    # Test get_volume
    print(f"\n🔊 Testing get_volume...")
    volume = controller.get_volume()
    if volume is not None:
        print(f"✅ Volume retrieval successful: {volume}%")
    else:
        print("❌ Volume retrieval failed")
        return False
    
    # Test volume CLI commands
    print(f"\n🧪 Testing CLI volume commands...")
    try:
        from moode_cli_v2 import MoOdeAudioCLI
        
        class MockArgs:
            def __init__(self):
                self.level = None
                self.json = False
        
        cli = MoOdeAudioCLI(host, port)
        args = MockArgs()
        
        result = cli.cmd_volume(args)
        if result == 0:
            print("✅ CLI volume command successful")
        else:
            print("❌ CLI volume command failed")
    except ImportError:
        print("⚠️  CLI module not found, skipping CLI tests")
    
    return True

if __name__ == "__main__":
    # Use the host from the debug output or default
    host = "192.168.1.4" if len(sys.argv) == 1 else sys.argv[1]
    port = 80 if len(sys.argv) <= 2 else int(sys.argv[2])
    
    test_volume_fix(host, port)
