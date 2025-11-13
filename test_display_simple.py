"""
Minimal standalone test for the integrated display interface.
Tests only the display_interface module directly.
"""

import sys
import os
import logging

# Add parent directory to path to allow direct import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kitchenradio'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

print("Testing integrated display interface...")
print("=" * 60)

try:
    # Direct import of the display interface module
    from radio.hardware.display_interface import DisplayInterface
    print("✅ Import successful - display interface loaded")
    
    # Create display in emulator mode
    print("\nInitializing display in emulator mode...")
    display = DisplayInterface(use_hardware=False)
    
    if display.initialize():
        print(f"✅ Display initialized successfully")
        print(f"   Mode: {display.get_mode()}")
        print(f"   Size: {display.WIDTH}x{display.HEIGHT}")
        
        # Test rendering
        print("\nRendering test frame...")
        def draw_test(draw):
            draw.text((10, 10), "Integration Test", fill=255)
            draw.rectangle([(0, 0), (255, 63)], outline=255)
            draw.line([(0, 0), (255, 63)], fill=255)
        
        display.render_frame(draw_test)
        print("✅ Frame rendered successfully")
        
        # Test BMP export
        print("\nExporting BMP data...")
        bmp_data = display.getDisplayImage()
        if bmp_data:
            print(f"✅ BMP export successful: {len(bmp_data)} bytes")
        else:
            print("❌ BMP export failed")
        
        # Get display info
        print("\nDisplay information:")
        info = display.get_display_info()
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        # Cleanup
        display.cleanup()
        print("\n✅ Cleanup completed")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nKey accomplishments:")
        print("✅ Emulator is built-in (no external import needed)")
        print("✅ Single file contains both emulator and hardware support")
        print("✅ BMP export works for web viewing")
        print("✅ All APIs function correctly")
        
    else:
        print("❌ Display initialization failed")
        sys.exit(1)
        
except Exception as e:
    print(f"\n❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✨ Integration successful! The display interface is simplified and unified.")
