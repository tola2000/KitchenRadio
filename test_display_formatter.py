#!/usr/bin/env python3
"""
Comprehensive test suite for display_formatter.py

Tests all display formatting functionality including:
- Text truncation with existing methods
- Scrolling text rendering
- Menu display with selection bar
- Volume display
- Track info display
- Status message display
- Error message display
"""

import sys
import os

# Add the kitchenradio module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kitchenradio'))

from kitchenradio.radio.hardware.display_formatter import DisplayFormatter
from PIL import Image, ImageDraw, ImageFont
import time

class MockDisplay:
    """Mock display for testing that simulates the actual display interface"""
    def __init__(self, width=256, height=64):
        self.width = width
        self.height = height
        self.buffer = Image.new('1', (width, height), 0)
        self.draw = ImageDraw.Draw(self.buffer)
    
    def clear(self):
        self.draw.rectangle((0, 0, self.width, self.height), fill=0)
    
    def show(self):
        pass
    
    def get_buffer(self):
        return self.buffer

def test_text_truncation():
    """Test text truncation with existing methods"""
    print("Testing text truncation...")
    
    formatter = DisplayFormatter()
    font = formatter.fonts['medium']
    
    # Test short text (should not be truncated)
    short_text = "Short"
    truncated = formatter._truncate_text(short_text, 200, font)
    print(f"Short text '{short_text}' truncated to: '{truncated}'")
    assert truncated == short_text, "Short text should not be truncated"
    
    # Test long text (should be truncated)
    long_text = "This is a very long song title that should definitely be truncated on the small display"
    truncated = formatter._truncate_text(long_text, 100, font)
    print(f"Long text truncated to: '{truncated}'")
    assert len(truncated) < len(long_text), "Long text should be truncated"
    assert truncated.endswith("..."), "Truncated text should end with ellipsis"
    
    # Test truncation with info
    is_truncated, full_width = formatter._truncate_text_with_info(long_text, 100, font)
    print(f"Truncation info - truncated: {is_truncated}, width: {full_width}")
    assert is_truncated, "Long text should be marked as truncated"
    
    print("✓ Text truncation working correctly\n")

def test_scrolling_text():
    """Test scrolling text rendering"""
    print("Testing scrolling text rendering...")
    
    formatter = DisplayFormatter()
    font = formatter.fonts['medium']
    
    long_text = "This is a very long scrolling text that should move across the display"
    max_width = 100
    
    # Test different scroll positions
    for scroll_offset in [0, 10, 20, 30, 50]:
        visible_text = formatter._get_scrolling_text(long_text, max_width, font, scroll_offset)
        print(f"Scroll offset {scroll_offset}: '{visible_text}'")
        assert len(visible_text) > 0, "Scrolling text should not be empty"
    
    # Test text that fits (no scrolling needed)
    short_text = "Short"
    visible_text = formatter._get_scrolling_text(short_text, max_width, font, 0)
    print(f"Short text (no scroll): '{visible_text}'")
    assert visible_text == short_text, "Short text should not scroll"
    
    # Test wraparound scrolling
    bbox = font.getbbox(long_text)
    text_width = bbox[2] - bbox[0]
    wrap_offset = text_width + 50  # Beyond the text width
    visible_text = formatter._get_scrolling_text(long_text, max_width, font, wrap_offset)
    print(f"Wraparound offset {wrap_offset}: '{visible_text}'")
    assert len(visible_text) > 0, "Wraparound text should not be empty"
    
    print("✓ Scrolling text rendering working correctly\n")

def test_menu_display():
    """Test menu display with selection bar"""
    print("Testing menu display...")
    
    formatter = DisplayFormatter()
    
    menu_items = [
        "Play/Pause",
        "Next Track",
        "Previous Track",
        "Volume Up",
        "Volume Down",
        "Change Source",
        "Browse Playlists"
    ]
    
    # Test different selected indices
    for selected_index in [0, 2, 4, 6]:
        menu_function = formatter.format_menu_display("Main Menu", menu_items, selected_index)
        print(f"Created menu with item {selected_index} selected: '{menu_items[selected_index]}'")
        assert callable(menu_function), "Menu function should be callable"
    
    # Test edge cases
    menu_function = formatter.format_menu_display("Main Menu", menu_items, len(menu_items) - 1)  # Last item
    print("Created menu with last item selected")
    assert callable(menu_function), "Menu function should be callable"
    
    # Test empty menu
    menu_function = formatter.format_menu_display("Empty Menu", [], 0)
    print("Created empty menu")
    assert callable(menu_function), "Empty menu function should be callable"
    
    print("✓ Menu display working correctly\n")

def test_volume_display():
    """Test volume display"""
    print("Testing volume display...")
    
    formatter = DisplayFormatter()
    
    # Test different volume levels
    for volume in [0, 25, 50, 75, 100]:
        volume_function = formatter.format_volume_display(volume)
        print(f"Created volume display at {volume}%")
        assert callable(volume_function), "Volume function should be callable"
    
    # Test fullscreen volume
    for volume in [0, 50, 100]:
        fullscreen_function = formatter.format_fullscreen_volume(volume)
        print(f"Created fullscreen volume display at {volume}%")
        assert callable(fullscreen_function), "Fullscreen volume function should be callable"
    
    print("✓ Volume display working correctly\n")

def test_track_info_with_progress():
    """Test track info display with progress (includes progress bar)"""
    print("Testing track info with progress display...")
    
    formatter = DisplayFormatter()
    
    # Test track info with progress
    track = {
        'title': 'Amazing Song Title',
        'artist': 'Great Artist',
        'album': 'Fantastic Album',
        'length': 240000,  # 4 minutes in milliseconds
        'time_position': 120000  # 2 minutes in
    }
    
    result = formatter.format_track_info(track, playing=True, volume=75)
    print(f"Created track info display")
    print(f"Result type: {type(result)}")
    
    # The format_track_info returns a tuple: (draw_function, truncation_info)
    if isinstance(result, tuple) and len(result) == 2:
        track_function, truncation_info = result
        print(f"Truncation info: {truncation_info}")
        assert callable(track_function), "Track function should be callable"
    else:
        print(f"Unexpected result format: {result}")
        assert False, "Expected tuple result from format_track_info"
    
    # Test with long title
    long_track = {
        'title': 'This is an extremely long song title that should definitely be truncated and maybe scroll',
        'artist': 'Artist with a Very Long Name',
        'album': 'Album with an Incredibly Long Title',
        'length': 300000,
        'time_position': 150000
    }
    
    long_result = formatter.format_track_info(long_track, playing=True, volume=50)
    print(f"Created long track info display")
    
    if isinstance(long_result, tuple) and len(long_result) == 2:
        long_track_function, long_truncation_info = long_result
        print(f"Long track truncation info: {long_truncation_info}")
        assert callable(long_track_function), "Long track function should be callable"
    else:
        print(f"Unexpected long result format: {long_result}")
        assert False, "Expected tuple result from format_track_info"
    
    print("✓ Track info with progress display working correctly\n")

def test_status_and_error_messages():
    """Test status and error message displays"""
    print("Testing status and error message displays...")
    
    formatter = DisplayFormatter()
    
    # Test status messages
    status_messages = [
        "Playing",
        "Paused", 
        "Stopped",
        "Connecting...",
        "Loading..."
    ]
    
    for message in status_messages:
        status_function = formatter.format_status_message(message)
        print(f"Created status message: '{message}'")
        assert callable(status_function), "Status function should be callable"
    
    # Test error messages
    error_messages = [
        ("Connection failed", "E001"),
        ("Playback error", "E002"),
        ("Network timeout", ""),
        ("Unknown error", "E999")
    ]
    
    for message, code in error_messages:
        error_function = formatter.format_error_message(message, code)
        print(f"Created error message: '{message}' (code: {code})")
        assert callable(error_function), "Error function should be callable"
    
    print("✓ Status and error message displays working correctly\n")

def test_simple_text_display():
    """Test simple text display"""
    print("Testing simple text display...")
    
    formatter = DisplayFormatter()
    
    # Test simple text displays
    test_cases = [
        ("Hello World", ""),
        ("Kitchen Radio", "Ready"),
        ("Volume", "75%"),
        ("Status", "Connected"),
        ("Long main text that might need truncation", "Sub text")
    ]
    
    for main_text, sub_text in test_cases:
        text_function = formatter.format_simple_text(main_text, sub_text)
        print(f"Created simple text display: '{main_text}' / '{sub_text}'")
        assert callable(text_function), "Simple text function should be callable"
    
    print("✓ Simple text display working correctly\n")

def test_scrolling_animation():
    """Test scrolling animation simulation"""
    print("Testing scrolling animation simulation...")
    
    formatter = DisplayFormatter()
    font = formatter.fonts['medium']
    
    long_title = "This is a very long song title that will scroll across the display to show all the text"
    max_width = 150
    
    # Check if text needs scrolling
    bbox = font.getbbox(long_title)
    text_width = bbox[2] - bbox[0]
    needs_scrolling = text_width > max_width
    
    if needs_scrolling:
        print(f"Text needs scrolling (width: {text_width}, max: {max_width})")
        print("Simulating scrolling animation...")
        
        # Simulate several scroll positions
        scroll_positions = [0, 10, 20, 30, 40, 50, 60]
        
        for i, scroll_offset in enumerate(scroll_positions):
            # Get scrolling text for this position
            visible_text = formatter._get_scrolling_text(long_title, max_width, font, scroll_offset)
            
            print(f"Frame {i+1}: scroll_offset = {scroll_offset}, visible: '{visible_text}'")
            
            # In a real application, this would be displayed on the actual screen
            # Here we just simulate the timing
            time.sleep(0.05)
    else:
        print("Text fits without scrolling")
    
    print("✓ Scrolling animation simulation completed\n")

def test_comprehensive_display():
    """Test a comprehensive display with all elements"""
    print("Testing comprehensive display layout...")
    
    formatter = DisplayFormatter()
    
    # Test status display with comprehensive data
    status_data = {
        'state': 'playing',
        'volume': 65,
        'source': 'Spotify',
        'track': {
            'title': 'Beautiful Long Song Title That Scrolls',
            'artist': 'Awesome Artist',
            'album': 'Great Album',
            'length': 240000,
            'time_position': 96000  # 1:36 of 4:00
        }
    }
    
    status_function = formatter.format_status(status_data)
    print("Created comprehensive status display")
    assert callable(status_function), "Status function should be callable"
    
    # Test track info with progress
    track = status_data['track']
    track_result = formatter.format_track_info(track, playing=True, volume=status_data['volume'])
    print(f"Created track info display with progress")
    
    if isinstance(track_result, tuple) and len(track_result) == 2:
        track_function, truncation_info = track_result
        print(f"Track title truncation info: {truncation_info}")
        assert callable(track_function), "Track function should be callable"
    else:
        print(f"Unexpected track result format: {track_result}")
        assert False, "Expected tuple result from format_track_info"
    
    # Test default display
    default_function = formatter.format_default_display()
    print("Created default display")
    assert callable(default_function), "Default function should be callable"
    
    print("✓ Comprehensive display layout working correctly\n")

def test_visual_rendering():
    """Test that the drawing functions actually render to an image"""
    print("Testing visual rendering...")
    
    formatter = DisplayFormatter()
    
    # Create a mock image to draw on
    test_image = Image.new('1', (256, 64), 0)
    draw = ImageDraw.Draw(test_image)
    
    # Test menu rendering
    menu_function = formatter.format_menu_display("Test Menu", ["Item 1", "Item 2", "Item 3"], 1)
    menu_function(draw)
    
    # Check that something was drawn (image is not all black)
    pixels = list(test_image.getdata())
    white_pixels = sum(pixels)
    print(f"Menu rendered {white_pixels} white pixels")
    assert white_pixels > 0, "Menu should render some white pixels"
    
    # Test track info rendering
    test_image = Image.new('1', (256, 64), 0)
    draw = ImageDraw.Draw(test_image)
    
    track = {
        'title': 'Test Song',
        'artist': 'Test Artist',
        'album': 'Test Album',
        'length': 180000,
        'time_position': 90000
    }
    
    track_function, truncation_info = formatter.format_track_info(track, playing=True, volume=60)
    track_function(draw)
    
    pixels = list(test_image.getdata())
    white_pixels = sum(pixels)
    print(f"Track info rendered {white_pixels} white pixels")
    assert white_pixels > 0, "Track info should render some white pixels"
    
    # Test volume display rendering
    test_image = Image.new('1', (256, 64), 0)
    draw = ImageDraw.Draw(test_image)
    
    volume_function = formatter.format_volume_display(75)
    volume_function(draw)
    
    pixels = list(test_image.getdata())
    white_pixels = sum(pixels)
    print(f"Volume display rendered {white_pixels} white pixels")
    assert white_pixels > 0, "Volume display should render some white pixels"
    
    # Test status message rendering
    test_image = Image.new('1', (256, 64), 0)
    draw = ImageDraw.Draw(test_image)
    
    status_function = formatter.format_status_message("Testing Status")
    status_function(draw)
    
    pixels = list(test_image.getdata())
    white_pixels = sum(pixels)
    print(f"Status message rendered {white_pixels} white pixels")
    assert white_pixels > 0, "Status message should render some white pixels"
    
    print("✓ Visual rendering working correctly\n")

def run_all_tests():
    """Run all display formatter tests"""
    print("=" * 60)
    print("DISPLAY FORMATTER TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        test_text_truncation()
        test_scrolling_text()
        test_menu_display()
        test_volume_display()
        test_track_info_with_progress()
        test_status_and_error_messages()
        test_simple_text_display()
        test_scrolling_animation()
        test_comprehensive_display()
        test_visual_rendering()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("Display formatter is working correctly.")
        print("=" * 60)
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        raise

if __name__ == "__main__":
    run_all_tests()
