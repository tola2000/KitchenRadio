#!/usr/bin/env python3
"""
Test script for KitchenRadio active source playback controls
"""

import sys
import time
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from env_config import get_project_config
    config = get_project_config()
    
    if config and 'PYTHON_PATHS' in config:
        for path in config['PYTHON_PATHS']:
            if path not in sys.path:
                sys.path.insert(0, path)
except Exception as e:
    print(f"Warning: Could not load env config: {e}")

def test_playback_controls():
    """Test the active source playback control methods"""
    try:
        from kitchenradio.radio.kitchen_radio import KitchenRadio, BackendType
        
        # Set up logging to see the commands
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        print("=== Testing KitchenRadio Active Source Playback Controls ===\n")
        
        # Create and start daemon
        daemon = KitchenRadio()
        
        if not daemon.start():
            print("✗ Failed to start daemon")
            return False
        
        print("✓ KitchenRadio daemon started")
        
        # Check available sources
        available_sources = daemon.get_available_sources()
        print(f"Available sources: {[s.value for s in available_sources]}")
        
        if not available_sources:
            print("✗ No sources available for testing")
            daemon.stop()
            return False
        
        # Test with each available source
        for source in available_sources:
            print(f"\n=== Testing {source.value.upper()} Controls ===")
            
            # Set the source
            if daemon.set_source(source):
                print(f"✓ Set active source to {source.value}")
                time.sleep(1)
                
                # Test play
                print("\n1. Testing play...")
                if daemon.play():
                    print("   ✓ Play command successful")
                else:
                    print("   ✗ Play command failed")
                time.sleep(2)
                
                # Test pause
                print("\n2. Testing pause...")
                if daemon.pause():
                    print("   ✓ Pause command successful")
                else:
                    print("   ✗ Pause command failed")
                time.sleep(1)
                
                # Test play_pause (should play since we just paused)
                print("\n3. Testing play_pause (should play)...")
                if daemon.play_pause():
                    print("   ✓ Play/pause toggle successful")
                else:
                    print("   ✗ Play/pause toggle failed")
                time.sleep(2)
                
                # Test play_pause again (should pause since we just played)
                print("\n4. Testing play_pause (should pause)...")
                if daemon.play_pause():
                    print("   ✓ Play/pause toggle successful")
                else:
                    print("   ✗ Play/pause toggle failed")
                time.sleep(1)
                
                # Test next
                print("\n5. Testing next...")
                if daemon.next():
                    print("   ✓ Next command successful")
                else:
                    print("   ✗ Next command failed")
                time.sleep(1)
                
                # Test previous
                print("\n6. Testing previous...")
                if daemon.previous():
                    print("   ✓ Previous command successful")
                else:
                    print("   ✗ Previous command failed")
                time.sleep(1)
                
                # Test stop
                print("\n7. Testing stop...")
                if daemon.stop():
                    print("   ✓ Stop command successful")
                else:
                    print("   ✗ Stop command failed")
                time.sleep(1)
                
            else:
                print(f"✗ Failed to set source to {source.value}")
        
        # Test with no active source
        print(f"\n=== Testing Commands with No Active Source ===")
        daemon.source = None  # Clear active source
        
        print("Testing commands with no active source (should all fail gracefully)...")
        commands = [
            ('play', daemon.play),
            ('pause', daemon.pause),
            ('stop', daemon.stop),
            ('next', daemon.next),
            ('previous', daemon.previous),
            ('play_pause', daemon.play_pause)
        ]
        
        for cmd_name, cmd_func in commands:
            result = cmd_func()
            status = "as expected" if not result else "unexpectedly succeeded"
            print(f"   {cmd_name}: Failed {status}")
        
        daemon.stop()
        print("\n✓ All tests completed successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_playback_controls()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
