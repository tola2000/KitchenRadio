"""
Test file to investigate brightness differences in text rendering methods.

This test will help identify why some text appears dimmer than others and
how to fix brightness without converting to images.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Font setup
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


def test_brightness_methods():
    """Test different text rendering methods and their brightness"""
    
    width = 256
    height = 64
    test_text = "Test Brightness"
    font = load_font(24)
    
    print("="*60)
    print("BRIGHTNESS TEST - Different Rendering Methods")
    print("="*60)
    
    # Method 1: Direct draw.text() with fill parameter
    print("\n1. Direct draw.text() with fill=255")
    img1 = Image.new('L', (width, height), color=0)
    draw1 = ImageDraw.Draw(img1)
    draw1.text((10, 20), test_text, font=font, fill=255)
    
    # Analyze brightness
    pixels1 = list(img1.getdata())
    max_brightness1 = max(pixels1)
    avg_brightness1 = sum(pixels1) / len(pixels1)
    non_zero1 = [p for p in pixels1 if p > 0]
    avg_text_brightness1 = sum(non_zero1) / len(non_zero1) if non_zero1 else 0
    
    print(f"   Max brightness: {max_brightness1}")
    print(f"   Average overall: {avg_brightness1:.2f}")
    print(f"   Average text pixels: {avg_text_brightness1:.2f}")
    print(f"   Non-zero pixels: {len(non_zero1)}")
    
    # Method 2: Render to separate image buffer then paste
    print("\n2. Render to buffer image, then paste")
    img2 = Image.new('L', (width, height), color=0)
    
    # Create text buffer
    bbox = font.getbbox(test_text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_img = Image.new('L', (text_width, text_height), color=0)
    text_draw = ImageDraw.Draw(text_img)
    text_draw.text((0, -bbox[1]), test_text, font=font, fill=255)
    
    # Paste onto main image
    img2.paste(text_img, (10, 20))
    
    # Analyze brightness
    pixels2 = list(img2.getdata())
    max_brightness2 = max(pixels2)
    avg_brightness2 = sum(pixels2) / len(pixels2)
    non_zero2 = [p for p in pixels2 if p > 0]
    avg_text_brightness2 = sum(non_zero2) / len(non_zero2) if non_zero2 else 0
    
    print(f"   Max brightness: {max_brightness2}")
    print(f"   Average overall: {avg_brightness2:.2f}")
    print(f"   Average text pixels: {avg_text_brightness2:.2f}")
    print(f"   Non-zero pixels: {len(non_zero2)}")
    
    # Method 3: draw.text() with different modes
    print("\n3. Direct draw.text() on RGB mode image")
    img3_rgb = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw3 = ImageDraw.Draw(img3_rgb)
    draw3.text((10, 20), test_text, font=font, fill=(255, 255, 255))
    img3 = img3_rgb.convert('L')
    
    # Analyze brightness
    pixels3 = list(img3.getdata())
    max_brightness3 = max(pixels3)
    avg_brightness3 = sum(pixels3) / len(pixels3)
    non_zero3 = [p for p in pixels3 if p > 0]
    avg_text_brightness3 = sum(non_zero3) / len(non_zero3) if non_zero3 else 0
    
    print(f"   Max brightness: {max_brightness3}")
    print(f"   Average overall: {avg_brightness3:.2f}")
    print(f"   Average text pixels: {avg_text_brightness3:.2f}")
    print(f"   Non-zero pixels: {len(non_zero3)}")
    
    # Method 4: Test ImageDraw mode parameter
    print("\n4. Direct draw.text() with ImageDraw mode")
    img4 = Image.new('L', (width, height), color=0)
    draw4 = ImageDraw.Draw(img4, mode='L')
    draw4.text((10, 20), test_text, font=font, fill=255)
    
    # Analyze brightness
    pixels4 = list(img4.getdata())
    max_brightness4 = max(pixels4)
    avg_brightness4 = sum(pixels4) / len(pixels4)
    non_zero4 = [p for p in pixels4 if p > 0]
    avg_text_brightness4 = sum(non_zero4) / len(non_zero4) if non_zero4 else 0
    
    print(f"   Max brightness: {max_brightness4}")
    print(f"   Average overall: {avg_brightness4:.2f}")
    print(f"   Average text pixels: {avg_text_brightness4:.2f}")
    print(f"   Non-zero pixels: {len(non_zero4)}")
    
    # Method 5: Test with stroke parameter (outline)
    print("\n5. Direct draw.text() with stroke (outline)")
    img5 = Image.new('L', (width, height), color=0)
    draw5 = ImageDraw.Draw(img5)
    draw5.text((10, 20), test_text, font=font, fill=255, stroke_width=0)
    
    # Analyze brightness
    pixels5 = list(img5.getdata())
    max_brightness5 = max(pixels5)
    avg_brightness5 = sum(pixels5) / len(pixels5)
    non_zero5 = [p for p in pixels5 if p > 0]
    avg_text_brightness5 = sum(non_zero5) / len(non_zero5) if non_zero5 else 0
    
    print(f"   Max brightness: {max_brightness5}")
    print(f"   Average overall: {avg_brightness5:.2f}")
    print(f"   Average text pixels: {avg_text_brightness5:.2f}")
    print(f"   Non-zero pixels: {len(non_zero5)}")
    
    # Save test images for visual inspection
    print("\n" + "="*60)
    print("Saving test images for visual inspection...")
    img1.save("test_brightness_method1_direct.png")
    img2.save("test_brightness_method2_paste.png")
    img3.save("test_brightness_method3_rgb_convert.png")
    img4.save("test_brightness_method4_mode.png")
    img5.save("test_brightness_method5_stroke.png")
    print("Saved: test_brightness_method*.png")
    
    # Comparison
    print("\n" + "="*60)
    print("COMPARISON")
    print("="*60)
    print(f"Method 1 (direct):        {avg_text_brightness1:.2f} avg brightness")
    print(f"Method 2 (paste):         {avg_text_brightness2:.2f} avg brightness")
    print(f"Method 3 (RGB convert):   {avg_text_brightness3:.2f} avg brightness")
    print(f"Method 4 (mode):          {avg_text_brightness4:.2f} avg brightness")
    print(f"Method 5 (stroke):        {avg_text_brightness5:.2f} avg brightness")
    
    # Check if there are differences
    brightnesses = [avg_text_brightness1, avg_text_brightness2, avg_text_brightness3, 
                   avg_text_brightness4, avg_text_brightness5]
    if max(brightnesses) - min(brightnesses) > 1:
        print(f"\n⚠️  BRIGHTNESS DIFFERENCE DETECTED: {max(brightnesses) - min(brightnesses):.2f}")
        print(f"   Brightest method: Method {brightnesses.index(max(brightnesses)) + 1}")
        print(f"   Dimmest method: Method {brightnesses.index(min(brightnesses)) + 1}")
    else:
        print("\n✓ All methods produce similar brightness")


def test_antialiasing_effect():
    """Test if antialiasing affects perceived brightness"""
    
    print("\n" + "="*60)
    print("ANTIALIASING TEST")
    print("="*60)
    
    width = 256
    height = 64
    test_text = "Antialiasing"
    font = load_font(24)
    
    # Without any special handling
    print("\n1. Standard rendering (with antialiasing)")
    img1 = Image.new('L', (width, height), color=0)
    draw1 = ImageDraw.Draw(img1)
    draw1.text((10, 20), test_text, font=font, fill=255)
    
    pixels1 = list(img1.getdata())
    non_zero1 = [p for p in pixels1 if p > 0]
    histogram1 = {}
    for p in non_zero1:
        histogram1[p] = histogram1.get(p, 0) + 1
    
    print(f"   Non-zero pixel count: {len(non_zero1)}")
    print(f"   Unique brightness levels: {len(histogram1)}")
    print(f"   Brightness histogram (top 5):")
    for brightness, count in sorted(histogram1.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"      {brightness}: {count} pixels ({count/len(non_zero1)*100:.1f}%)")
    
    # Try to force no antialiasing (if possible)
    print("\n2. Attempting to disable antialiasing")
    print("   Note: PIL/Pillow doesn't expose direct antialiasing control for text")
    print("   Antialiasing is typically beneficial for OLED displays")
    
    # Analysis of edge pixels
    max_brightness = max(non_zero1)
    full_bright = sum(1 for p in non_zero1 if p == 255)
    partial_bright = len(non_zero1) - full_bright
    
    print(f"\n   Pixels at full brightness (255): {full_bright} ({full_bright/len(non_zero1)*100:.1f}%)")
    print(f"   Pixels with partial brightness: {partial_bright} ({partial_bright/len(non_zero1)*100:.1f}%)")
    print(f"   Average of all text pixels: {sum(non_zero1)/len(non_zero1):.2f}")
    
    img1.save("test_antialiasing.png")


def test_image_access_method():
    """Test if using draw._image affects brightness"""
    
    print("\n" + "="*60)
    print("IMAGE ACCESS METHOD TEST")
    print("="*60)
    
    width = 256
    height = 64
    test_text = "Image Access"
    font = load_font(24)
    
    # Method 1: Standard ImageDraw
    print("\n1. Standard ImageDraw (draw.text)")
    img1 = Image.new('L', (width, height), color=0)
    draw1 = ImageDraw.Draw(img1)
    draw1.text((10, 20), test_text, font=font, fill=255)
    
    pixels1 = list(img1.getdata())
    non_zero1 = [p for p in pixels1 if p > 0]
    avg1 = sum(non_zero1) / len(non_zero1) if non_zero1 else 0
    print(f"   Average text brightness: {avg1:.2f}")
    
    # Method 2: Access via draw._image (like in format_track_info)
    print("\n2. Access via draw._image then paste")
    img2_main = Image.new('L', (width, height), color=0)
    draw2 = ImageDraw.Draw(img2_main)
    
    # Create text buffer
    bbox = font.getbbox(test_text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_img = Image.new('L', (text_width, text_height), color=0)
    text_draw = ImageDraw.Draw(text_img)
    text_draw.text((0, -bbox[1]), test_text, font=font, fill=255)
    
    # Paste using draw._image (simulating format_track_info approach)
    img2_accessed = draw2._image
    img2_accessed.paste(text_img, (10, 20))
    
    pixels2 = list(img2_main.getdata())
    non_zero2 = [p for p in pixels2 if p > 0]
    avg2 = sum(non_zero2) / len(non_zero2) if non_zero2 else 0
    print(f"   Average text brightness: {avg2:.2f}")
    
    # Method 3: Direct paste without draw._image
    print("\n3. Direct image.paste (no draw object)")
    img3 = Image.new('L', (width, height), color=0)
    
    # Create text buffer (reuse from above)
    img3.paste(text_img, (10, 20))
    
    pixels3 = list(img3.getdata())
    non_zero3 = [p for p in pixels3 if p > 0]
    avg3 = sum(non_zero3) / len(non_zero3) if non_zero3 else 0
    print(f"   Average text brightness: {avg3:.2f}")
    
    print("\n" + "="*60)
    print(f"Brightness comparison:")
    print(f"  Method 1 (draw.text):     {avg1:.2f}")
    print(f"  Method 2 (draw._image):   {avg2:.2f}")
    print(f"  Method 3 (direct paste):  {avg3:.2f}")
    
    if abs(avg1 - avg2) > 1 or abs(avg1 - avg3) > 1:
        print(f"\n⚠️  SIGNIFICANT DIFFERENCE DETECTED!")
    else:
        print(f"\n✓ All methods produce similar brightness")


def test_scrolling_vs_static():
    """Compare brightness between scrolling text (paste) and static text (draw.text)"""
    
    print("\n" + "="*60)
    print("SCROLLING vs STATIC TEXT TEST")
    print("="*60)
    
    width = 246
    height = 64
    test_text = "This is a long scrolling text that needs to scroll"
    font = load_font(24)
    
    # Static text rendering (like when text fits)
    print("\n1. Static text (draw.text - used when text fits)")
    img_static = Image.new('L', (width, height), color=0)
    draw_static = ImageDraw.Draw(img_static)
    draw_static.text((10, 20), test_text[:20], font=font, fill=255)  # Truncated
    
    pixels_static = list(img_static.getdata())
    non_zero_static = [p for p in pixels_static if p > 0]
    avg_static = sum(non_zero_static) / len(non_zero_static) if non_zero_static else 0
    print(f"   Non-zero pixels: {len(non_zero_static)}")
    print(f"   Average text brightness: {avg_static:.2f}")
    
    # Scrolling text rendering (like _render_scrolling_text)
    print("\n2. Scrolling text (image paste - used when scrolling)")
    img_scroll_main = Image.new('L', (width, height), color=0)
    draw_scroll = ImageDraw.Draw(img_scroll_main)
    
    # Create scrolling buffer
    bbox = font.getbbox(test_text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    buffer_width = text_width * 2
    scroll_buffer = Image.new('L', (buffer_width, text_height), color=0)
    scroll_draw = ImageDraw.Draw(scroll_buffer)
    scroll_draw.text((0, -bbox[1]), test_text, font=font, fill=255)
    scroll_draw.text((text_width, -bbox[1]), test_text, font=font, fill=255)
    
    # Crop and paste (simulating scrolling at offset 0)
    cropped = scroll_buffer.crop((0, 0, width - 20, text_height))
    img_scroll_accessed = draw_scroll._image
    img_scroll_accessed.paste(cropped, (10, 20))
    
    pixels_scroll = list(img_scroll_main.getdata())
    non_zero_scroll = [p for p in pixels_scroll if p > 0]
    avg_scroll = sum(non_zero_scroll) / len(non_zero_scroll) if non_zero_scroll else 0
    print(f"   Non-zero pixels: {len(non_zero_scroll)}")
    print(f"   Average text brightness: {avg_scroll:.2f}")
    
    # Save for comparison
    img_static.save("test_static_text.png")
    img_scroll_main.save("test_scrolling_text.png")
    
    print("\n" + "="*60)
    print(f"Brightness comparison:")
    print(f"  Static text:    {avg_static:.2f}")
    print(f"  Scrolling text: {avg_scroll:.2f}")
    print(f"  Difference:     {abs(avg_static - avg_scroll):.2f}")
    
    if abs(avg_static - avg_scroll) > 1:
        print(f"\n⚠️  THIS IS THE ISSUE!")
        print(f"   Scrolling text ({avg_scroll:.2f}) differs from static text ({avg_static:.2f})")
        print(f"   Difference: {abs(avg_static - avg_scroll):.2f} brightness units")
    else:
        print(f"\n✓ No significant difference")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TEXT BRIGHTNESS INVESTIGATION")
    print("Testing different rendering methods to find brightness issues")
    print("="*60)
    
    test_brightness_methods()
    test_antialiasing_effect()
    test_image_access_method()
    test_scrolling_vs_static()
    
    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60)
    print("\nCheck the generated PNG files for visual comparison:")
    print("  - test_brightness_method*.png")
    print("  - test_antialiasing.png")
    print("  - test_static_text.png")
    print("  - test_scrolling_text.png")
    print("\nAnalyze the console output above to identify brightness differences.")


if __name__ == "__main__":
    main()
