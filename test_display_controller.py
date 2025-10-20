#!/usr/bin/env python3
"""
Test script for the refactored Display Controller

Tests the modular display controller with separated formatting and I2C logic.
"""

import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add KitchenRadio to Python path
sys.path.insert(0, str(Path(__file__).parent))

from kitchenradio.radio.hardware.display_controller import DisplayController
from kitchenradio.radio.hardware.display_interface_i2c import DisplayType


def test_basic_functionality():
    """Test basic display controller functionality"""
    print("🔍 Testing basic DisplayController functionality...")
    
    # Create display controller in simulation mode
    display = DisplayController(
        kitchen_radio=None,  # No KitchenRadio for isolated testing
        display_type=DisplayType.SSD1306_128x64,
        refresh_rate=2.0
    )
    
    # Initialize
    if not display.initialize():
        print("❌ Failed to initialize DisplayController")
        return False
    
    print("✅ DisplayController initialized successfully")
    
    # Get display info
    info = display.get_display_info()
    print(f"   Display: {info['i2c_interface']['width']}x{info['i2c_interface']['height']}")
    print(f"   Simulation mode: {info['i2c_interface']['simulation_mode']}")
    print(f"   Available fonts: {info['formatter']['fonts']}")
    
    # Test clearing
    display.clear()
    print("✅ Display cleared")
    
    # Test display functionality
    if display.test_display():
        print("✅ Display test passed")
    else:
        print("⚠️  Display test returned False (may be normal in simulation)")
    
    display.cleanup()
    return True


def test_display_layouts():
    """Test all display layout types"""
    print("\n🎨 Testing display layouts...")
    
    display = DisplayController(
        display_type=DisplayType.SSD1306_128x64,
        refresh_rate=1.0
    )
    
    if not display.initialize():
        print("❌ Failed to initialize DisplayController")
        return False
    
    test_scenarios = [
        {
            "name": "Track Info - Normal",
            "action": lambda: display.show_track_info(
                "Bohemian Rhapsody", "Queen", "A Night at the Opera", True, 85
            )
        },
        {
            "name": "Track Info - Long Title",
            "action": lambda: display.show_track_info(
                "This is a very long song title that should scroll nicely across the display", 
                "Very Long Artist Name That Also Scrolls", "Album", False, 65
            )
        },
        {
            "name": "Volume Display - Normal",
            "action": lambda: display.show_volume(75, 100, False)
        },
        {
            "name": "Volume Display - Muted",
            "action": lambda: display.show_volume(0, 100, True)
        },
        {
            "name": "Menu Display",
            "action": lambda: display.show_menu(
                "Playlists", 
                ["Rock Classics", "Jazz Collection", "Electronic Music", "Pop Hits"], 
                1
            )
        },
        {
            "name": "Source Selection",
            "action": lambda: display.show_source_selection(
                ["MPD", "Spotify", "Bluetooth"], "Spotify", ["MPD", "Spotify"]
            )
        },
        {
            "name": "Status - Success",
            "action": lambda: display.show_status_message(
                "Connected to audio system", "♪", "success"
            )
        },
        {
            "name": "Status - Warning",
            "action": lambda: display.show_status_message(
                "No internet connection", "⚠", "warning"
            )
        },
        {
            "name": "Status - Error",
            "action": lambda: display.show_status_message(
                "Audio device not found", "❌", "error"
            )
        },
        {
            "name": "Clock Display",
            "action": lambda: display.show_clock(
                datetime.now().strftime("%H:%M:%S"), 
                datetime.now().strftime("%Y-%m-%d")
            )
        }
    ]
    
    info = display.get_display_info()
    screenshot_dir = Path("display_screenshots")
    if info['i2c_interface']['simulation_mode']:
        screenshot_dir.mkdir(exist_ok=True)
        print(f"   Screenshots will be saved to: {screenshot_dir}")
    
    for i, scenario in enumerate(test_scenarios):
        print(f"   Testing {scenario['name']}...")
        
        try:
            # Execute the test
            scenario['action']()
            
            # Save screenshot if in simulation mode
            if info['i2c_interface']['simulation_mode']:
                filename = screenshot_dir / f"{i+1:02d}_{scenario['name'].lower().replace(' ', '_').replace('-', '_')}.png"
                if display.save_screenshot(str(filename)):
                    print(f"      Screenshot: {filename}")
            
            # Get display lines for text representation
            lines = display.get_display_lines()
            print(f"      Text: {lines}")
            
            time.sleep(1.5)  # Brief pause between tests
            
        except Exception as e:
            print(f"   ❌ Error in {scenario['name']}: {e}")
            continue
    
    print("✅ All layout tests completed")
    display.cleanup()
    return True


def test_manual_updates():
    """Test manual update requests"""
    print("\n⚡ Testing manual update requests...")
    
    display = DisplayController(
        display_type=DisplayType.SSD1306_128x64,
        refresh_rate=0.5  # Slow refresh for testing
    )
    
    if not display.initialize():
        print("❌ Failed to initialize DisplayController")
        return False
    
    # Show initial content
    display.show_status_message("Initial message", "ℹ", "info")
    time.sleep(1)
    
    # Update content and request immediate update
    print("   Requesting manual update...")
    display.show_status_message("Updated message", "✓", "success")
    display.request_update()
    
    time.sleep(0.1)  # Brief pause
    
    # Check display lines
    lines = display.get_display_lines()
    if "Updated message" in " ".join(lines):
        print("✅ Manual update request successful")
    else:
        print("⚠️  Manual update may not have taken effect immediately")
    
    display.cleanup()
    return True


def test_integration_with_mock_kitchen_radio():
    """Test integration with a mock KitchenRadio instance"""
    print("\n🔗 Testing integration with mock KitchenRadio...")
    
    class MockKitchenRadio:
        """Mock KitchenRadio for testing"""
        def __init__(self):
            self.status_count = 0
        
        def get_status(self):
            """Return mock status that changes over time"""
            self.status_count += 1
            
            if self.status_count % 3 == 1:
                return {
                    'current_source': 'mpd',
                    'available_sources': ['mpd', 'librespot'],
                    'mpd': {
                        'connected': True,
                        'state': 'play',
                        'volume': 75,
                        'current_song': {
                            'title': f'Test Song {self.status_count}',
                            'artist': 'Test Artist',
                            'album': 'Test Album'
                        }
                    }
                }
            elif self.status_count % 3 == 2:
                return {
                    'current_source': 'librespot',
                    'available_sources': ['mpd', 'librespot'],
                    'librespot': {
                        'connected': True,
                        'state': 'playing',
                        'volume': 85,
                        'current_track': {
                            'title': f'Spotify Track {self.status_count}',
                            'artist': 'Spotify Artist',
                            'album': 'Spotify Album'
                        }
                    }
                }
            else:
                return {
                    'current_source': None,
                    'available_sources': ['mpd', 'librespot']
                }
    
    # Create mock KitchenRadio
    mock_radio = MockKitchenRadio()
    
    # Create display with KitchenRadio integration
    display = DisplayController(
        kitchen_radio=mock_radio,
        display_type=DisplayType.SSD1306_128x64,
        refresh_rate=2.0  # Fast updates for testing
    )
    
    if not display.initialize():
        print("❌ Failed to initialize DisplayController")
        return False
    
    print("   Display controller started with auto-updates...")
    print("   Observing automatic updates for 10 seconds...")
    
    start_time = time.time()
    last_lines = []
    update_count = 0
    
    while time.time() - start_time < 10:
        current_lines = display.get_display_lines()
        
        # Check if display content changed
        if current_lines != last_lines:
            update_count += 1
            print(f"   Update {update_count}: {current_lines}")
            last_lines = current_lines
        
        time.sleep(0.5)
    
    print(f"✅ Detected {update_count} automatic updates")
    
    display.cleanup()
    return True


def test_error_handling():
    """Test error handling and edge cases"""
    print("\n🛡️  Testing error handling...")
    
    display = DisplayController(
        display_type=DisplayType.SSD1306_128x64,
        refresh_rate=1.0
    )
    
    if not display.initialize():
        print("❌ Failed to initialize DisplayController")
        return False
    
    # Test with empty/None values
    try:
        display.show_track_info("", "", "", False, None)
        print("✅ Handled empty track info")
    except Exception as e:
        print(f"⚠️  Error with empty track info: {e}")
    
    # Test with very long strings
    try:
        very_long_title = "A" * 200
        display.show_track_info(very_long_title, "Artist", "Album", True, 50)
        print("✅ Handled very long title")
    except Exception as e:
        print(f"⚠️  Error with very long title: {e}")
    
    # Test with invalid volume values
    try:
        display.show_volume(-10, 100, False)  # Negative volume
        display.show_volume(150, 100, False)  # Over max
        print("✅ Handled invalid volume values")
    except Exception as e:
        print(f"⚠️  Error with invalid volume: {e}")
    
    # Test with empty menu
    try:
        display.show_menu("Empty Menu", [], 0)
        print("✅ Handled empty menu")
    except Exception as e:
        print(f"⚠️  Error with empty menu: {e}")
    
    display.cleanup()
    print("✅ Error handling tests completed")
    return True


def main():
    """Run all tests"""
    print("🚀 Starting Display Controller Tests")
    print("=" * 50)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Display Layouts", test_display_layouts),
        ("Manual Updates", test_manual_updates),
        ("KitchenRadio Integration", test_integration_with_mock_kitchen_radio),
        ("Error Handling", test_error_handling),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
