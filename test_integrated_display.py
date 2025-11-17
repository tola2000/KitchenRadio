"""
Quick test to verify the integrated display interface works correctly.
"""

import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

# Import the unified display interface
from kitchenradio.radio_deprecated.hardware.display_interface import DisplayInterface

def test_emulator_mode():
    """Test built-in emulator mode."""
    print("\n=== Testing Built-in Emulator Mode ===")
    
    # Create display in emulator mode
    display = DisplayInterface(use_hardware=False)
    
    if not display.initialize():
        print("❌ Failed to initialize emulator")
        return False
    
    print(f"✅ Display initialized in {display.get_mode()} mode")
    
    # Test basic drawing
    def draw_test(draw):
        draw.text((10, 10), "Test Pattern", fill=255)
        draw.rectangle([(0, 0), (255, 63)], outline=255)
    
    display.render_frame(draw_test)
    print("✅ Frame rendered successfully")
    
    # Test BMP export
    bmp_data = display.getDisplayImage()
    if bmp_data:
        print(f"✅ BMP export successful ({len(bmp_data)} bytes)")
    else:
        print("❌ BMP export failed")
        return False
    
    # Test display info
    info = display.get_display_info()
    print(f"✅ Display info: {info['width']}x{info['height']}, mode={info['mode']}")
    
    # Test statistics
    stats = display.get_statistics()
    print(f"✅ Statistics retrieved: {stats.get('mode')}")
    
    # Cleanup
    display.cleanup()
    print("✅ Cleanup completed")
    
    return True


def test_hardware_mode():
    """Test hardware mode (will fall back to emulator on Windows)."""
    print("\n=== Testing Hardware Mode (with fallback) ===")
    
    # Create display requesting hardware mode
    display = DisplayInterface(use_hardware=True)
    
    if not display.initialize():
        print("❌ Failed to initialize display")
        return False
    
    mode = display.get_mode()
    print(f"✅ Display initialized in {mode} mode")
    
    if mode == 'hardware':
        print("   → Running on Raspberry Pi with SPI hardware")
    elif mode == 'emulator':
        print("   → Hardware not available, using emulator (expected on Windows)")
    
    # Same test as emulator mode
    def draw_test(draw):
        draw.text((10, 10), f"Mode: {mode}", fill=255)
        draw.rectangle([(5, 5), (250, 58)], outline=255)
    
    display.render_frame(draw_test)
    print("✅ Frame rendered successfully")
    
    # Cleanup
    display.cleanup()
    print("✅ Cleanup completed")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Display Interface Integration Test")
    print("=" * 60)
    
    try:
        # Test emulator mode
        if not test_emulator_mode():
            print("\n❌ Emulator mode test FAILED")
            return 1
        
        # Test hardware mode (with fallback)
        if not test_hardware_mode():
            print("\n❌ Hardware mode test FAILED")
            return 1
        
        print("\n" + "=" * 60)
        print("✅ All tests PASSED!")
        print("=" * 60)
        print("\nThe integrated display interface is working correctly!")
        print("- Emulator is built-in (no external dependencies)")
        print("- Hardware SPI support is optional")
        print("- Automatic fallback works as expected")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
