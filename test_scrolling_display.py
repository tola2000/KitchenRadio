#!/usr/bin/env python3
"""
Test script for scrolling text functionality in the display formatter.

This script tests:
1. Text truncation detection
2. Scrolling text animation
3. Display refresh with scroll updates
4. Integration between formatter and controller
"""

import logging
import time
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from kitchenradio.radio.hardware.display_formatter import DisplayFormatter
from kitchenradio.radio.hardware.display_controller import DisplayController
from kitchenradio.web.display_interface_emulator import EmulatorDisplayInterface

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_scrolling_text():
    """Test scrolling text functionality"""
    print("🧪 Testing Scrolling Text Functionality")
    print("=" * 50)
    
    # Create emulator interface for testing
    emulator = EmulatorDisplayInterface(width=256, height=64)
    emulator.initialize()
    
    # Create formatter
    formatter = DisplayFormatter(width=256, height=64)
    
    # Test track with very long title (will be truncated)
    long_track = {
        'title': 'This is an extremely long song title that will definitely be truncated and needs scrolling',
        'artist': 'The Very Long Band Name That Also Needs Scrolling',
        'album': 'An Album With An Incredibly Long Name That Exceeds Display Width'
    }
    
    print("\n1. Testing truncation detection...")
    draw_func, truncation_info = formatter.format_track_info(long_track, True)
    
    print(f"   Title truncated: {truncation_info['title_truncated']}")
    print(f"   Original title: '{truncation_info['original_title']}'")
    print(f"   Displayed title: '{truncation_info['displayed_title']}'")
    print(f"   Artist/Album truncated: {truncation_info['artist_album_truncated']}")
    
    # Render initial frame
    emulator.render_frame(draw_func)
    emulator.save_bmp("test_scrolling_initial.bmp")
    print("   ✅ Initial frame saved as 'test_scrolling_initial.bmp'")
    
    print("\n2. Testing scroll animation...")
    scroll_positions = []
    
    for i in range(10):  # Test 10 scroll positions
        # Update scroll position
        formatter.update_scroll_position(4)  # Move 4 pixels
        
        # Re-render with new scroll position
        draw_func, truncation_info = formatter.format_track_info(long_track, True)
        emulator.render_frame(draw_func)
        
        # Save frame
        filename = f"test_scrolling_frame_{i+1:02d}.bmp"
        emulator.save_bmp(filename)
        scroll_positions.append(formatter.scroll_offset)
        
        print(f"   Frame {i+1}: scroll_offset={formatter.scroll_offset}, saved as '{filename}'")
        time.sleep(0.1)  # Small delay for demonstration
    
    print(f"   ✅ Generated {len(scroll_positions)} scroll frames")
    
    # Reset scroll
    formatter.reset_scroll()
    print(f"   ✅ Scroll reset: offset={formatter.scroll_offset}")
    
    print("\n3. Testing display controller integration...")
    
    # Mock KitchenRadio class for testing
    class MockKitchenRadio:
        def get_status(self):
            return {
                'current_source': 'mpd',
                'mpd': {
                    'connected': True,
                    'current_track': long_track,
                    'state': 'play',
                    'volume': 75
                }
            }
    
    # Create display controller with emulator
    mock_radio = MockKitchenRadio()
    controller = DisplayController(
        kitchen_radio=mock_radio,
        refresh_rate=2.0,  # 2 Hz for testing
        i2c_interface=emulator
    )
    
    if controller.initialize():
        print("   ✅ Display controller initialized")
        
        # Let it run for a few seconds to test scrolling
        print("   🔄 Running controller for 5 seconds to test auto-scrolling...")
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < 5.0:
            time.sleep(0.5)
            frame_count += 1
            
            # Save periodic frames to see scrolling in action
            if frame_count % 2 == 0:  # Every second
                filename = f"test_controller_scroll_{frame_count//2}.bmp"
                emulator.save_bmp(filename)
                print(f"      Saved controller frame: '{filename}'")
        
        controller.cleanup()
        print("   ✅ Display controller test completed")
    else:
        print("   ❌ Failed to initialize display controller")
    
    emulator.cleanup()
    print("\n✅ All scrolling tests completed!")
    print("\n📁 Generated files:")
    print("   - test_scrolling_initial.bmp (initial display)")
    print("   - test_scrolling_frame_XX.bmp (manual scroll frames)")
    print("   - test_controller_scroll_X.bmp (controller auto-scroll)")

if __name__ == "__main__":
    try:
        test_scrolling_text()
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
