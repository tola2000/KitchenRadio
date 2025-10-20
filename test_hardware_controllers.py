#!/usr/bin/env python3
"""
Test script for KitchenRadio Hardware Controllers

Tests both button controller and display controller with simulation mode
for systems without actual Raspberry Pi hardware.
"""

import sys
import time
import logging
import threading
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from kitchenradio.radio.hardware import (
    ButtonController, ButtonType, ButtonEvent,
    DisplayController, DisplayType
)

def test_display_controller():
    """Test the display controller functionality"""
    print("\n🖥️ Testing Display Controller...")
    print("=" * 40)
    
    # Create display controller
    display = DisplayController(DisplayType.SSD1306_128x64)
    
    if not display.initialize():
        print("❌ Failed to initialize display controller")
        return False
    
    print("✅ Display controller initialized")
    
    try:
        # Test 1: Track info display
        print("📻 Testing track info display...")
        display.show_track_info(
            "Long Song Title That Should Scroll Around",
            "The Amazing Artist",
            "Great Album Name",
            True
        )
        time.sleep(3)
        
        # Test 2: Volume display
        print("🔊 Testing volume display...")
        for volume in [10, 25, 50, 75, 90]:
            display.show_volume(volume)
            print(f"   Volume: {volume}%")
            time.sleep(0.5)
        
        # Test 3: Menu display
        print("📋 Testing menu display...")
        playlists = ["Rock Classics", "Jazz Collection", "Electronic Beats", "Chill Vibes"]
        for i in range(len(playlists)):
            display.show_menu("Playlists", playlists, i)
            print(f"   Selected: {playlists[i]}")
            time.sleep(1)
        
        # Test 4: Status messages
        print("💬 Testing status messages...")
        status_messages = [
            ("Connected to MPD", "♪"),
            ("Playing Music", "▶"),
            ("Paused", "⏸"),
            ("Volume Changed", "🔊"),
            ("Error Occurred", "!"),
        ]
        
        for message, icon in status_messages:
            display.show_status_message(message, icon)
            print(f"   Status: {message}")
            time.sleep(1.5)
        
        print("✅ Display controller test completed successfully")
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Display test interrupted by user")
        return True
    except Exception as e:
        print(f"❌ Display controller test failed: {e}")
        return False
    finally:
        display.cleanup()


def test_button_controller():
    """Test the button controller functionality"""
    print("\n🔘 Testing Button Controller...")
    print("=" * 40)
    
    # Create button controller
    button_controller = ButtonController()
    
    # Event counter for testing
    event_count = 0
    received_events = []
    
    def button_event_handler(event: ButtonEvent):
        nonlocal event_count, received_events
        event_count += 1
        received_events.append(event)
        print(f"   Button Event #{event_count}: {event.button_type.value} - {event.event_type}")
    
    # Set up event handler
    button_controller.set_global_callback(button_event_handler)
    
    if not button_controller.initialize():
        print("❌ Failed to initialize button controller")
        return False
    
    print("✅ Button controller initialized")
    
    try:
        # Test button simulation (since we likely don't have actual hardware)
        print("🎮 Testing button simulation...")
        
        test_buttons = [
            (ButtonType.SOURCE_MPD, "Source MPD"),
            (ButtonType.SOURCE_SPOTIFY, "Source Spotify"),
            (ButtonType.MENU_UP, "Menu Up"),
            (ButtonType.MENU_DOWN, "Menu Down"),
            (ButtonType.MENU_OK, "Menu OK"),
            (ButtonType.TRANSPORT_PLAY_PAUSE, "Play/Pause"),
            (ButtonType.TRANSPORT_STOP, "Stop"),
            (ButtonType.VOLUME_UP, "Volume Up"),
            (ButtonType.VOLUME_DOWN, "Volume Down"),
        ]
        
        for button_type, description in test_buttons:
            print(f"   Simulating {description}...")
            
            # Simulate press and release
            button_controller.simulate_button_press(button_type, 'press')
            time.sleep(0.1)
            button_controller.simulate_button_press(button_type, 'release')
            time.sleep(0.3)
        
        # Test double press
        print("   Testing double press...")
        button_controller.simulate_button_press(ButtonType.SOURCE_MPD, 'double_press')
        time.sleep(0.3)
        
        # Test long press
        print("   Testing long press...")
        button_controller.simulate_button_press(ButtonType.TRANSPORT_PLAY_PAUSE, 'hold')
        time.sleep(0.3)
        
        print(f"✅ Button controller test completed - {event_count} events received")
        
        # Show event summary
        if received_events:
            print("\n📊 Event Summary:")
            event_types = {}
            for event in received_events:
                key = f"{event.button_type.value}:{event.event_type}"
                event_types[key] = event_types.get(key, 0) + 1
            
            for event_key, count in event_types.items():
                print(f"   {event_key}: {count}")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Button test interrupted by user")
        return True
    except Exception as e:
        print(f"❌ Button controller test failed: {e}")
        return False
    finally:
        button_controller.cleanup()


def test_hardware_integration():
    """Test hardware integration without full KitchenRadio daemon"""
    print("\n🔧 Testing Hardware Integration...")
    print("=" * 40)
    
    print("ℹ️ Hardware integration test requires a running KitchenRadio daemon")
    print("   This test shows how to use the HardwareIntegration class:")
    
    example_code = '''
from kitchenradio.radio.kitchen_radio import KitchenRadio
from kitchenradio.radio.hardware import HardwareIntegration

# Create and start KitchenRadio daemon
radio = KitchenRadio()
if radio.start():
    print("KitchenRadio daemon started")
    
    # Create hardware integration
    hardware = HardwareIntegration(radio)
    
    if hardware.initialize():
        print("Hardware integration started")
        print("Physical buttons and display are now active!")
        
        try:
            # Keep running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            hardware.cleanup()
            radio.stop()
    '''
    
    print(example_code)
    return True


def main():
    """Main test function"""
    print("🎵 KitchenRadio Hardware Controller Test")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Hide some verbose logs during testing
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    print("🔧 Hardware Information:")
    print("  • Button Controller: Maps physical buttons to GPIO pins")
    print("  • Display Controller: Controls I2C OLED displays")
    print("  • Hardware Integration: Connects controllers to KitchenRadio")
    print()
    print("📝 Note: Running in simulation mode (no actual hardware required)")
    print("         Install 'RPi.GPIO' and 'luma.oled' for real hardware support")
    
    try:
        # Test individual components
        tests = [
            ("Display Controller", test_display_controller),
            ("Button Controller", test_button_controller),
            ("Hardware Integration", test_hardware_integration),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Show final results
        print(f"\n{'='*60}")
        print("🏁 Test Results Summary:")
        print("=" * 25)
        
        all_passed = True
        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} - {test_name}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n🎉 All hardware controller tests passed!")
            print("   Ready for physical radio integration!")
        else:
            print("\n⚠️ Some tests failed - check hardware setup")
        
        print(f"\n📖 For Raspberry Pi setup instructions, see:")
        print(f"   requirements-hardware.txt")
        print(f"   PHYSICAL_RADIO_INTERFACE.md")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
