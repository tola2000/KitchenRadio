#!/usr/bin/env python3
"""
Simple Display System Test Script

Quick test of display formatter and emulator interface.
Can be run standalone without unittest framework.
"""

import logging
import time
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_display_system():
    """Simple test of display system components."""
    
    print("🔧 Testing KitchenRadio Display System...")
    print("=" * 50)
    
    try:
        # Import components
        print("📦 Importing display components...")
        from kitchenradio.web.display_interface_emulator import EmulatorDisplayInterface
        from kitchenradio.radio.hardware.display_formatter import DisplayFormatter
        print("✅ Imports successful")
        
        # Test 1: Emulator Basic Functions
        print("\n🧪 Test 1: Emulator Basic Functions")
        emulator = EmulatorDisplayInterface()
        
        if emulator.initialize():
            print("✅ Emulator initialized")
            
            # Test display info
            info = emulator.get_display_info()
            print(f"   📊 Resolution: {info['width']}x{info['height']}")
            print(f"   🔧 Emulation mode: {info['emulation_mode']}")
            
            # Test clear
            emulator.clear()
            bmp_data = emulator.getDisplayImage()
            if bmp_data:
                print(f"✅ Clear operation successful ({len(bmp_data)} bytes BMP)")
            else:
                print("❌ Clear operation failed")
                return False
        else:
            print("❌ Emulator initialization failed")
            return False
        
        # Test 2: Custom Drawing
        print("\n🧪 Test 2: Custom Drawing")
        def draw_test_screen(draw):
            # Header
            draw.text((10, 5), "KitchenRadio Display Test", fill=255)
            
            # Status line
            draw.text((10, 25), f"Time: {time.strftime('%H:%M:%S')}", fill=255)
            
            # Border
            draw.rectangle([(2, 2), (253, 61)], outline=255)
            
            # Bottom info
            draw.text((10, 45), "Emulator Working!", fill=255)
        
        if emulator.render_frame(draw_test_screen):
            bmp_data = emulator.getDisplayImage()
            print(f"✅ Custom drawing successful ({len(bmp_data)} bytes BMP)")
            
            # Save test image
            test_file = Path("display_test_output.bmp")
            try:
                with open(test_file, 'wb') as f:
                    f.write(bmp_data)
                print(f"💾 Test image saved as: {test_file.absolute()}")
            except Exception as e:
                print(f"⚠️  Could not save test image: {e}")
                
        else:
            print("❌ Custom drawing failed")
            return False
        
        # Test 3: Display Formatter
        print("\n🧪 Test 3: Display Formatter")
        formatter = DisplayFormatter()
        
        # Test simple text formatting
        draw_func = formatter.format_simple_text("Format Test", "Formatter Working")
        if draw_func and callable(draw_func):
            print("✅ Text formatter created")
            
            if emulator.render_frame(draw_func):
                print("✅ Formatted text rendered")
            else:
                print("❌ Formatted text rendering failed")
                return False
        else:
            print("❌ Text formatter creation failed")
            return False
        
        # Test 4: Status Display
        print("\n🧪 Test 4: Status Display")
        mock_status = {
            'current_source': 'mpd',
            'mpd': {
                'connected': True,
                'state': 'play',
                'volume': 85,
                'current_song': {
                    'title': 'Test Track',
                    'artist': 'Test Artist',
                    'album': 'Test Album'
                }
            },
            'librespot': {
                'connected': False
            }
        }
        
        status_draw_func = formatter.format_status(mock_status)
        if status_draw_func and callable(status_draw_func):
            print("✅ Status formatter created")
            
            if emulator.render_frame(status_draw_func):
                bmp_data = emulator.getDisplayImage()
                print(f"✅ Status display rendered ({len(bmp_data)} bytes BMP)")
                
                # Save status image
                status_file = Path("display_status_test.bmp")
                try:
                    with open(status_file, 'wb') as f:
                        f.write(bmp_data)
                    print(f"💾 Status image saved as: {status_file.absolute()}")
                except Exception as e:
                    print(f"⚠️  Could not save status image: {e}")
            else:
                print("❌ Status display rendering failed")
                return False
        else:
            print("❌ Status formatter creation failed")
            return False
        
        # Test 5: Multiple Renders
        print("\n🧪 Test 5: Multiple Renders Performance")
        start_time = time.time()
        
        for i in range(5):
            def draw_counter(draw):
                draw.text((10, 20), f"Render #{i+1}", fill=255)
                draw.text((10, 35), f"Time: {time.time():.2f}", fill=255)
            
            if not emulator.render_frame(draw_counter):
                print(f"❌ Render {i+1} failed")
                return False
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 5
        print(f"✅ 5 renders completed in {end_time-start_time:.3f}s (avg: {avg_time:.3f}s)")
        
        # Cleanup
        emulator.cleanup()
        print("🧹 Cleanup completed")
        
        print("\n🎉 All tests passed! Display system is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure PIL (Pillow) is installed: pip install Pillow")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.exception("Test failed with exception")
        return False


def main():
    """Main test function."""
    print("KitchenRadio Display System Test")
    print("================================")
    
    success = test_display_system()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SUCCESS: Display system is working correctly!")
        print("📁 Check for generated BMP files in current directory")
    else:
        print("❌ FAILURE: Display system has issues")
        print("🔍 Check the error messages above for details")
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
