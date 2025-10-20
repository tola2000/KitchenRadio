#!/usr/bin/env python3
"""
Test script to initialize and test DisplayInterfaceEmulator

This script tests the complete initialization and functionality 
of the DisplayInterfaceEmulator to ensure it works correctly.
"""

import sys
import logging
import time
import traceback
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_display_interface_emulator_init():
    """Test DisplayInterfaceEmulator initialization and basic operations"""
    print("=" * 60)
    print("Testing DisplayInterfaceEmulator initialization...")
    print("=" * 60)
    
    try:
        # Test import
        print("1. Testing import...")
        from kitchenradio.web.display_interface_emulator import DisplayInterfaceEmulator
        print("✅ Import successful!")
        
        # Test construction
        print("2. Testing construction...")
        emulator = DisplayInterfaceEmulator()
        print("✅ Construction successful!")
        
        # Check initial state
        print("3. Checking initial state...")
        print(f"   Width: {emulator.width}")
        print(f"   Height: {emulator.height}")
        print(f"   I2C Port: {emulator.i2c_port}")
        print(f"   I2C Address: 0x{emulator.i2c_address:02X}")
        print(f"   Current image: {emulator.current_image is not None}")
        print(f"   BMP data: {emulator.bmp_data is not None}")
        
        # Test initialization
        print("4. Testing initialization...")
        init_result = emulator.initialize()
        print(f"✅ Initialization result: {init_result}")
        
        # Check state after initialization
        print("5. Checking state after initialization...")
        print(f"   Current image: {emulator.current_image is not None}")
        print(f"   BMP data: {emulator.bmp_data is not None}")
        if emulator.bmp_data:
            print(f"   BMP data size: {len(emulator.bmp_data)} bytes")
        
        # Test clear operation
        print("6. Testing clear operation...")
        emulator.clear()
        print("✅ Clear operation successful!")
        
        # Test custom drawing
        print("7. Testing custom drawing...")
        def test_drawing(draw):
            # Draw some test content
            draw.text((10, 10), "TEST DISPLAY", fill=255)
            draw.text((10, 30), "Kitchen Radio", fill=255)
            draw.rectangle([(5, 5), (emulator.width-5, emulator.height-5)], outline=255)
            # Add some visual elements
            draw.line([(0, emulator.height//2), (emulator.width, emulator.height//2)], fill=255)
            draw.ellipse([(emulator.width-30, 5), (emulator.width-5, 30)], outline=255)
        
        render_result = emulator.render_frame(test_drawing)
        print(f"✅ Custom drawing result: {render_result}")
        
        # Test BMP data retrieval
        print("8. Testing BMP data retrieval...")
        bmp_data = emulator.getDisplayImage()
        if bmp_data:
            print(f"✅ BMP data retrieved: {len(bmp_data)} bytes")
            
            # Verify it's actually BMP data
            if bmp_data.startswith(b'BM'):
                print("✅ Valid BMP header detected")
            else:
                print("⚠️  BMP header not detected - might be invalid")
                
        else:
            print("❌ No BMP data available")
            return False
        
        # Test get_display_info
        print("9. Testing get_display_info...")
        info = emulator.get_display_info()
        print(f"✅ Display info: {info}")
        
        # Test multiple renders to ensure consistency
        print("10. Testing multiple renders...")
        for i in range(3):
            def draw_test(draw):
                draw.text((10, 20), f"Render #{i+1}", fill=255)
                draw.text((10, 40), f"Time: {time.time():.1f}", fill=255)
            
            result = emulator.render_frame(draw_test)
            if result:
                bmp = emulator.getDisplayImage()
                print(f"    Render {i+1}: ✅ ({len(bmp) if bmp else 0} bytes)")
            else:
                print(f"    Render {i+1}: ❌")
                return False
        
        # Test cleanup
        print("11. Testing cleanup...")
        emulator.cleanup()
        print("✅ Cleanup successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        traceback.print_exc()
        return False

def test_display_formatter_compatibility():
    """Test compatibility with DisplayFormatter"""
    print("\n" + "=" * 60)
    print("Testing DisplayFormatter compatibility...")
    print("=" * 60)
    
    try:
        # Import components
        from kitchenradio.web.display_interface_emulator import DisplayInterfaceEmulator
        from kitchenradio.radio.hardware.display_formatter import DisplayFormatter
        
        # Create instances
        emulator = DisplayInterfaceEmulator()
        emulator.initialize()
        
        formatter = DisplayFormatter(width=emulator.width, height=emulator.height)
        
        print("✅ Both components created successfully")
        
        # Test format methods that were missing
        print("1. Testing format_track_info...")
        try:
            draw_func = formatter.format_track_info("Test Song", "Test Artist", "Test Album", True, 75)
            result = emulator.render_frame(draw_func)
            print(f"✅ format_track_info: {result}")
        except Exception as e:
            print(f"❌ format_track_info failed: {e}")
            return False
        
        print("2. Testing format_status_message...")
        try:
            draw_func = formatter.format_status_message("Test Status", "♪", "info")
            result = emulator.render_frame(draw_func)
            print(f"✅ format_status_message: {result}")
        except Exception as e:
            print(f"❌ format_status_message failed: {e}")
            return False
        
        print("3. Testing other format methods...")
        
        # Test format_simple_text
        draw_func = formatter.format_simple_text("Main Text", "Sub Text")
        result = emulator.render_frame(draw_func)
        print(f"   format_simple_text: ✅ {result}")
        
        # Test format_volume_display
        draw_func = formatter.format_volume_display(65)
        result = emulator.render_frame(draw_func)
        print(f"   format_volume_display: ✅ {result}")
        
        # Test format_default_display
        draw_func = formatter.format_default_display()
        result = emulator.render_frame(draw_func)
        print(f"   format_default_display: ✅ {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Compatibility test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("DisplayInterfaceEmulator Initialization Test")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Working directory: {Path.cwd()}")
    
    # Test basic initialization
    init_success = test_display_interface_emulator_init()
    
    # Test formatter compatibility  
    compat_success = test_display_formatter_compatibility()
    
    print("\n" + "=" * 60)
    if init_success and compat_success:
        print("✅ ALL TESTS PASSED!")
        print("DisplayInterfaceEmulator initializes and works correctly")
        print("DisplayFormatter compatibility confirmed")
    else:
        print("❌ SOME TESTS FAILED!")
        if not init_success:
            print("- DisplayInterfaceEmulator initialization issues")
        if not compat_success:
            print("- DisplayFormatter compatibility issues")
    
    print("=" * 60)
    
    return init_success and compat_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
