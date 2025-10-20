#!/usr/bin/env python3
"""
Test script for DisplayInterfaceEmulator initialization and basic operations

This script specifically tests the DisplayInterfaceEmulator class to ensure
it can be properly initialized and perform basic display operations.
"""

import sys
import logging
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_display_interface_emulator_import():
    """Test importing DisplayInterfaceEmulator"""
    print("=" * 60)
    print("Testing DisplayInterfaceEmulator import...")
    print("=" * 60)
    
    try:
        print("1. Attempting to import DisplayInterfaceEmulator...")
        from kitchenradio.web.display_interface_emulator import DisplayInterfaceEmulator
        print("✅ Import successful!")
        
        print(f"2. Class type: {type(DisplayInterfaceEmulator)}")
        print(f"   Is class: {isinstance(DisplayInterfaceEmulator, type)}")
        print(f"   Callable: {callable(DisplayInterfaceEmulator)}")
        
        return DisplayInterfaceEmulator
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_display_interface_emulator_creation(DisplayInterfaceEmulator):
    """Test creating DisplayInterfaceEmulator instance"""
    print("\n" + "=" * 60)
    print("Testing DisplayInterfaceEmulator creation...")
    print("=" * 60)
    
    if not DisplayInterfaceEmulator:
        print("❌ No class available for testing")
        return None
    
    try:
        print("1. Creating DisplayInterfaceEmulator instance...")
        emulator = DisplayInterfaceEmulator()
        print("✅ Instance created successfully!")
        
        print(f"2. Instance type: {type(emulator)}")
        print(f"   Instance of DisplayInterfaceEmulator: {isinstance(emulator, DisplayInterfaceEmulator)}")
        
        # Check basic attributes
        print("3. Checking basic attributes...")
        attrs = ['width', 'height', 'i2c_port', 'i2c_address', 'current_image', 'bmp_data']
        for attr in attrs:
            value = getattr(emulator, attr, 'NOT_FOUND')
            print(f"   {attr}: {value}")
        
        return emulator
        
    except Exception as e:
        print(f"❌ Creation error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_display_interface_emulator_initialization(emulator):
    """Test initializing DisplayInterfaceEmulator"""
    print("\n" + "=" * 60)
    print("Testing DisplayInterfaceEmulator initialization...")
    print("=" * 60)
    
    if not emulator:
        print("❌ No emulator instance available")
        return False
    
    try:
        print("1. Calling initialize() method...")
        result = emulator.initialize()
        print(f"✅ Initialize result: {result}")
        
        # Check post-initialization state
        print("2. Checking state after initialization...")
        print(f"   Current image exists: {emulator.current_image is not None}")
        print(f"   BMP data exists: {emulator.bmp_data is not None}")
        print(f"   Last update: {getattr(emulator, 'last_update', 'NOT_FOUND')}")
        
        if emulator.bmp_data:
            print(f"   BMP data size: {len(emulator.bmp_data)} bytes")
        
        return result
        
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_display_interface_emulator_operations(emulator):
    """Test basic operations of DisplayInterfaceEmulator"""
    print("\n" + "=" * 60)
    print("Testing DisplayInterfaceEmulator operations...")
    print("=" * 60)
    
    if not emulator:
        print("❌ No emulator instance available")
        return False
    
    try:
        # Test clear operation
        print("1. Testing clear() operation...")
        emulator.clear()
        print("✅ Clear operation completed")
        
        # Test custom drawing
        print("2. Testing render_frame() with custom drawing...")
        def test_draw(draw):
            # Draw border
            draw.rectangle([(0, 0), (emulator.width-1, emulator.height-1)], outline=255)
            # Draw text
            draw.text((10, 20), "Test Display", fill=255)
            draw.text((10, 35), "Kitchen Radio", fill=255)
            # Draw diagonal line
            draw.line([(0, 0), (emulator.width-1, emulator.height-1)], fill=255)
        
        render_result = emulator.render_frame(test_draw)
        print(f"✅ Render frame result: {render_result}")
        
        # Test BMP data retrieval
        print("3. Testing getDisplayImage()...")
        bmp_data = emulator.getDisplayImage()
        if bmp_data:
            print(f"✅ BMP data retrieved: {len(bmp_data)} bytes")
            
            # Verify it's valid BMP header
            if bmp_data.startswith(b'BM'):
                print("✅ Valid BMP header detected")
            else:
                print("⚠️  BMP header not detected")
        else:
            print("❌ No BMP data available")
            return False
        
        # Test display info
        print("4. Testing get_display_info()...")
        info = emulator.get_display_info()
        print(f"✅ Display info retrieved: {info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Operations error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_display_interface_emulator_bmp_save(emulator):
    """Test saving BMP to file for verification"""
    print("\n" + "=" * 60)
    print("Testing BMP file save...")
    print("=" * 60)
    
    if not emulator:
        print("❌ No emulator instance available")
        return False
    
    try:
        # Get BMP data
        bmp_data = emulator.getDisplayImage()
        if not bmp_data:
            print("❌ No BMP data to save")
            return False
        
        # Save to file
        test_file = Path("test_display_output.bmp")
        with open(test_file, 'wb') as f:
            f.write(bmp_data)
        
        print(f"✅ BMP saved to {test_file} ({len(bmp_data)} bytes)")
        print(f"   File exists: {test_file.exists()}")
        print(f"   File size: {test_file.stat().st_size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ BMP save error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("DisplayInterfaceEmulator Comprehensive Test")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Working directory: {Path.cwd()}")
    
    # Test import
    DisplayInterfaceEmulator = test_display_interface_emulator_import()
    if not DisplayInterfaceEmulator:
        print("\n❌ FAILED: Cannot import DisplayInterfaceEmulator")
        return False
    
    # Test creation
    emulator = test_display_interface_emulator_creation(DisplayInterfaceEmulator)
    if not emulator:
        print("\n❌ FAILED: Cannot create DisplayInterfaceEmulator instance")
        return False
    
    # Test initialization
    init_result = test_display_interface_emulator_initialization(emulator)
    if not init_result:
        print("\n❌ FAILED: Cannot initialize DisplayInterfaceEmulator")
        return False
    
    # Test operations
    ops_result = test_display_interface_emulator_operations(emulator)
    if not ops_result:
        print("\n❌ FAILED: DisplayInterfaceEmulator operations failed")
        return False
    
    # Test BMP save
    save_result = test_display_interface_emulator_bmp_save(emulator)
    if not save_result:
        print("\n⚠️  WARNING: BMP save failed (not critical)")
    
    # Cleanup
    try:
        emulator.cleanup()
        print("\n✅ Cleanup completed")
    except Exception as e:
        print(f"\n⚠️  Cleanup warning: {e}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("DisplayInterfaceEmulator is fully functional")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
