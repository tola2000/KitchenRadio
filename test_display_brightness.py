"""
Test brightness differences on actual SSD1322 hardware display.

This test renders text using different methods to the real OLED display
to visually compare brightness differences.
"""

import time
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import spi
from luma.oled.device import ssd1322
import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_font(size=24):
    """Load HomeVideo font or default"""
    font_paths = [
        "frontend/static/fonts/homevideo.ttf",
        "static/fonts/homevideo.ttf",
        "fonts/homevideo.ttf",
    ]
    
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
    
    return ImageFont.load_default()


def create_display():
    """Initialize SSD1322 display"""
    print("Initializing SSD1322 display...")
    serial = spi(device=0, port=0, gpio_DC=24, gpio_RST=25)
    device = ssd1322(serial, rotate=2)
    print(f"Display size: {device.width}x{device.height}")
    return device


def test_method_1_direct_text(device):
    """Method 1: Direct draw.text() - used for static text"""
    print("\n" + "="*60)
    print("TEST 1: Direct draw.text() (fill=255)")
    print("="*60)
    
    width = 246
    height = 64
    test_text = "Direct Text"
    font = load_font(24)
    
    img = Image.new('L', (width, height), color=0)
    draw = ImageDraw.Draw(img)
    
    # Clear screen
    draw.rectangle([(0, 0), (width, height)], fill=0)
    
    # Draw text with fill=255
    draw.text((10, 10), test_text, font=font, fill=255)
    draw.text((10, 40), "Method 1: draw.text", font=load_font(12), fill=200)
    
    device.display(img)
    print("Displaying on hardware...")
    print("Press Enter to continue to next test...")
    input()


def test_method_2_paste_buffer(device):
    """Method 2: Render to buffer, then paste - used for scrolling"""
    print("\n" + "="*60)
    print("TEST 2: Render to buffer, then paste")
    print("="*60)
    
    width = 246
    height = 64
    test_text = "Pasted Text"
    font = load_font(24)
    
    img = Image.new('L', (width, height), color=0)
    draw = ImageDraw.Draw(img)
    
    # Clear screen
    draw.rectangle([(0, 0), (width, height)], fill=0)
    
    # Create text buffer
    bbox = font.getbbox(test_text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_img = Image.new('L', (text_width, text_height), color=0)
    text_draw = ImageDraw.Draw(text_img)
    text_draw.text((0, -bbox[1]), test_text, font=font, fill=255)
    
    # Paste onto main image
    img.paste(text_img, (10, 10))
    
    # Label
    draw.text((10, 40), "Method 2: paste buffer", font=load_font(12), fill=200)
    
    device.display(img)
    print("Displaying on hardware...")
    print("Press Enter to continue to next test...")
    input()


def test_method_3_paste_via_draw_image(device):
    """Method 3: Paste via draw._image - currently used in format_track_info"""
    print("\n" + "="*60)
    print("TEST 3: Paste via draw._image (current method)")
    print("="*60)
    
    width = 246
    height = 64
    test_text = "Draw._image"
    font = load_font(24)
    
    img = Image.new('L', (width, height), color=0)
    draw = ImageDraw.Draw(img)
    
    # Clear screen
    draw.rectangle([(0, 0), (width, height)], fill=0)
    
    # Create text buffer
    bbox = font.getbbox(test_text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_img = Image.new('L', (text_width, text_height), color=0)
    text_draw = ImageDraw.Draw(text_img)
    text_draw.text((0, -bbox[1]), test_text, font=font, fill=255)
    
    # Paste using draw._image (current approach)
    img_accessed = draw._image
    img_accessed.paste(text_img, (10, 10))
    
    # Label
    draw.text((10, 40), "Method 3: draw._image", font=load_font(12), fill=200)
    
    device.display(img)
    print("Displaying on hardware...")
    print("Press Enter to continue to next test...")
    input()


def test_side_by_side(device):
    """Show all three methods side by side for direct comparison"""
    print("\n" + "="*60)
    print("TEST 4: Side-by-side comparison")
    print("="*60)
    
    width = 246
    height = 64
    test_text = "Test"
    font = load_font(24)
    small_font = load_font(12)
    
    img = Image.new('L', (width, height), color=0)
    draw = ImageDraw.Draw(img)
    
    # Clear screen
    draw.rectangle([(0, 0), (width, height)], fill=0)
    
    # Title
    draw.text((5, 2), "Brightness Test", font=small_font, fill=255)
    
    # Method 1: Direct text (left)
    draw.text((5, 18), test_text, font=font, fill=255)
    draw.text((5, 50), "direct", font=load_font(10), fill=150)
    
    # Method 2: Paste buffer (middle)
    bbox = font.getbbox(test_text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_img = Image.new('L', (text_width, text_height), color=0)
    text_draw = ImageDraw.Draw(text_img)
    text_draw.text((0, -bbox[1]), test_text, font=font, fill=255)
    img.paste(text_img, (75, 18))
    draw.text((75, 50), "paste", font=load_font(10), fill=150)
    
    # Method 3: Via draw._image (right)
    text_img2 = Image.new('L', (text_width, text_height), color=0)
    text_draw2 = ImageDraw.Draw(text_img2)
    text_draw2.text((0, -bbox[1]), test_text, font=font, fill=255)
    img_accessed = draw._image
    img_accessed.paste(text_img2, (145, 18))
    draw.text((145, 50), "_image", font=load_font(10), fill=150)
    
    device.display(img)
    print("Displaying side-by-side comparison...")
    print("Compare the brightness of each rendering method")
    print("Press Enter to continue...")
    input()


def test_static_vs_scrolling(device):
    """Compare static text (current MPD) vs scrolling text (current Spotify)"""
    print("\n" + "="*60)
    print("TEST 5: Static vs Scrolling (actual use case)")
    print("="*60)
    
    width = 246
    height = 64
    test_text = "Long Song Title That Needs To Scroll"
    font = load_font(24)
    
    # Test 5a: Static text (when fits - like short MPD titles)
    print("\n5a. Static text (draw.text - short titles)")
    img = Image.new('L', (width, height), color=0)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (width, height)], fill=0)
    draw.text((10, 5), "Short Title", font=font, fill=255)
    draw.text((10, 40), "Static (when text fits)", font=load_font(12), fill=200)
    device.display(img)
    print("Press Enter to see scrolling version...")
    input()
    
    # Test 5b: Scrolling text (when too long - like Spotify titles)
    print("\n5b. Scrolling text (paste method - long titles)")
    img = Image.new('L', (width, height), color=0)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (width, height)], fill=0)
    
    # Simulate scrolling render
    bbox = font.getbbox(test_text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    buffer_width = text_width * 2
    scroll_buffer = Image.new('L', (buffer_width, text_height), color=0)
    scroll_draw = ImageDraw.Draw(scroll_buffer)
    scroll_draw.text((0, -bbox[1]), test_text, font=font, fill=255)
    scroll_draw.text((text_width, -bbox[1]), test_text, font=font, fill=255)
    
    # Crop and paste
    cropped = scroll_buffer.crop((0, 0, width - 20, text_height))
    img_accessed = draw._image
    img_accessed.paste(cropped, (10, 5))
    
    draw.text((10, 40), "Scrolling (pasted buffer)", font=load_font(12), fill=200)
    device.display(img)
    print("Compare brightness with previous static text")
    print("Press Enter to continue...")
    input()


def test_fill_values(device):
    """Test different fill values to find optimal brightness"""
    print("\n" + "="*60)
    print("TEST 6: Different fill values")
    print("="*60)
    
    width = 246
    height = 64
    font = load_font(16)
    
    fill_values = [200, 220, 240, 255]
    
    for fill_val in fill_values:
        print(f"\nTesting fill={fill_val}")
        img = Image.new('L', (width, height), color=0)
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, 0), (width, height)], fill=0)
        
        # Direct text with this fill value
        draw.text((10, 10), f"Fill = {fill_val}", font=font, fill=fill_val)
        
        # Pasted text with this fill value
        bbox = font.getbbox("PASTED")
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_img = Image.new('L', (text_width, text_height), color=0)
        text_draw = ImageDraw.Draw(text_img)
        text_draw.text((0, -bbox[1]), "PASTED", font=font, fill=fill_val)
        img.paste(text_img, (10, 40))
        
        device.display(img)
        print("Press Enter for next fill value...")
        input()


def main():
    """Run all hardware brightness tests"""
    print("="*60)
    print("HARDWARE DISPLAY BRIGHTNESS TEST")
    print("="*60)
    print("This will test different text rendering methods on the")
    print("actual SSD1322 OLED display to compare brightness.")
    print()
    
    try:
        device = create_display()
        
        print("\nStarting tests...")
        print("Observe the display and compare brightness between methods")
        print()
        
        # Run tests
        test_method_1_direct_text(device)
        test_method_2_paste_buffer(device)
        test_method_3_paste_via_draw_image(device)
        test_side_by_side(device)
        test_static_vs_scrolling(device)
        test_fill_values(device)
        
        # Clear display
        print("\n" + "="*60)
        print("Tests complete! Clearing display...")
        img = Image.new('L', (246, 64), color=0)
        device.display(img)
        
        print("\n" + "="*60)
        print("RESULTS:")
        print("="*60)
        print("Based on what you observed:")
        print("1. If all methods look the same brightness → No issue")
        print("2. If pasted text is dimmer → Need to investigate paste operation")
        print("3. If static text is brighter → draw.text has advantage")
        print()
        print("To fix dimmer pasted text:")
        print("  - Option 1: Use draw.text() for all text (no paste)")
        print("  - Option 2: Adjust fill value for pasted text")
        print("  - Option 3: Use display contrast/brightness settings")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
