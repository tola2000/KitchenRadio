#!/usr/bin/env python3
"""
Test script for EmulatorDisplayInterface

This script tests the import and construction of EmulatorDisplayInterface
to isolate any issues with the class definition or dependencies.
"""

import sys
import logging
import traceback
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_import():
    """Test importing the EmulatorDisplayInterface"""
    print("=" * 60)
    print("Testing EmulatorDisplayInterface import...")
    print("=" * 60)
    
    try:
        # Test import
        print("1. Attempting to import EmulatorDisplayInterface...")
        from kitchenradio.web.display_interface_emulator import EmulatorDisplayInterface
        print("✅ Import successful!")
        
        # Check if it's a class
        print(f"2. Type check: {type(EmulatorDisplayInterface)}")
        print(f"   Is class: {isinstance(EmulatorDisplayInterface, type)}")
        
        # Check if it's callable
        print(f"3. Callable check: {callable(EmulatorDisplayInterface)}")
        
        return EmulatorDisplayInterface
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return None
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        traceback.print_exc()
        return None

def test_construction(EmulatorDisplayInterface):
    """Test constructing an EmulatorDisplayInterface instance"""
    print("\n" + "=" * 60)
    print("Testing EmulatorDisplayInterface construction...")
    print("=" * 60)
    
    try:
        # Test basic construction
        print("1. Attempting to create EmulatorDisplayInterface instance...")
        interface = EmulatorDisplayInterface()
        print("✅ Construction successful!")
        
        # Check instance
        print(f"2. Instance type: {type(interface)}")
        print(f"   Instance of EmulatorDisplayInterface: {isinstance(interface, EmulatorDisplayInterface)}")
        
        # Check basic attributes
        print("3. Checking basic attributes...")
        print(f"   Width: {getattr(interface, 'width', 'NOT_FOUND')}")
        print(f"   Height: {getattr(interface, 'height', 'NOT_FOUND')}")
        print(f"   I2C Port: {getattr(interface, 'i2c_port', 'NOT_FOUND')}")
        print(f"   I2C Address: {getattr(interface, 'i2c_address', 'NOT_FOUND')}")
        
        return interface
        
    except Exception as e:
        print(f"❌ Construction error: {e}")
        traceback.print_exc()
        return None

def test_initialization(interface):
    """Test initializing the EmulatorDisplayInterface"""
    print("\n" + "=" * 60)
    print("Testing EmulatorDisplayInterface initialization...")
    print("=" * 60)
    
    if not interface:
        print("❌ No interface to test - skipping initialization")
        return False
    
    try:
        # Test initialization
        print("1. Attempting to initialize interface...")
        result = interface.initialize()
        print(f"✅ Initialization result: {result}")
        
        # Check state after initialization
        print("2. Checking state after initialization...")
        print(f"   Current image: {interface.current_image is not None}")
        print(f"   BMP data: {interface.bmp_data is not None}")
        print(f"   Last update: {getattr(interface, 'last_update', 'NOT_FOUND')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        traceback.print_exc()
        return False

def test_basic_operations(interface):
    """Test basic operations of the EmulatorDisplayInterface"""
    print("\n" + "=" * 60)
    print("Testing EmulatorDisplayInterface basic operations...")
    print("=" * 60)
    
    if not interface:
        print("❌ No interface to test - skipping operations")
        return False
    
    try:
        # Test clear
        print("1. Testing clear operation...")
        interface.clear()
        print("✅ Clear successful!")
        
        # Test get display info
        print("2. Testing get_display_info...")
        info = interface.get_display_info()
        print(f"✅ Display info: {info}")
        
        # Test simple drawing
        print("3. Testing simple drawing...")
        def draw_test(draw):
            draw.text((10, 20), "Test", fill=255)
            draw.rectangle([(5, 5), (50, 50)], outline=255)
        
        result = interface.render_frame(draw_test)
        print(f"✅ Drawing result: {result}")
        
        # Test BMP data retrieval
        print("4. Testing BMP data retrieval...")
        bmp_data = interface.getDisplayImage()
        if bmp_data:
            print(f"✅ BMP data retrieved: {len(bmp_data)} bytes")
        else:
            print("⚠️  No BMP data available")
        
        return True
        
    except Exception as e:
        print(f"❌ Operations error: {e}")
        traceback.print_exc()
        return False

def test_dependencies():
    """Test required dependencies"""
    print("\n" + "=" * 60)
    print("Testing required dependencies...")
    print("=" * 60)
    
    dependencies = ['PIL', 'io', 'time', 'logging']
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}: Available")
        except ImportError:
            print(f"❌ {dep}: Missing")
    
    # Test PIL submodules
    try:
        from PIL import Image, ImageDraw
        print("✅ PIL.Image and PIL.ImageDraw: Available")
    except ImportError:
        print("❌ PIL.Image or PIL.ImageDraw: Missing")

def main():
    """Main test function"""
    print("EmulatorDisplayInterface Test Suite")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Working directory: {Path.cwd()}")
    print(f"Python path: {sys.path[:3]}...")  # Show first 3 paths
    
    # Test dependencies first
    test_dependencies()
    
    # Test import
    EmulatorDisplayInterface = test_import()
    if not EmulatorDisplayInterface:
        print("\n❌ FAILED: Cannot import EmulatorDisplayInterface")
        return False
    
    # Test construction
    interface = test_construction(EmulatorDisplayInterface)
    if not interface:
        print("\n❌ FAILED: Cannot construct EmulatorDisplayInterface")
        return False
    
    # Test initialization
    init_result = test_initialization(interface)
    if not init_result:
        print("\n❌ FAILED: Cannot initialize EmulatorDisplayInterface")
        return False
    
    # Test basic operations
    ops_result = test_basic_operations(interface)
    if not ops_result:
        print("\n❌ FAILED: Basic operations failed")
        return False
    
    # Cleanup
    try:
        interface.cleanup()
        print("\n✅ Cleanup successful")
    except Exception as e:
        print(f"\n⚠️  Cleanup warning: {e}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("EmulatorDisplayInterface is working correctly")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
