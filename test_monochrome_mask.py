"""
Test monochrome mask rendering vs grayscale antialiased rendering
"""

from PIL import Image, ImageDraw, ImageFont
import os

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


def test_monochrome_vs_antialiased():
    """Compare monochrome mask rendering with antialiased grayscale"""
    
    print("="*60)
    print("MONOCHROME MASK vs ANTIALIASED GRAYSCALE TEST")
    print("="*60)
    
    test_text = "BRIGHT TEXT"
    font = load_font(24)
    fill_value = 255
    
    # Method 1: Direct grayscale draw.text() - antialiased (DIM)
    print("\n1. Direct grayscale draw.text() (antialiased)")
    bbox = font.getbbox(test_text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    img1 = Image.new('L', (text_width, text_height), color=0)
    draw1 = ImageDraw.Draw(img1)
    draw1.text((0, -bbox[1]), test_text, font=font, fill=fill_value)
    
    pixels1 = list(img1.getdata())
    non_zero1 = [p for p in pixels1 if p > 0]
    max1 = max(pixels1)
    avg1 = sum(non_zero1) / len(non_zero1) if non_zero1 else 0
    full_bright1 = sum(1 for p in non_zero1 if p == 255)
    
    print(f"   Max brightness: {max1}")
    print(f"   Average text brightness: {avg1:.2f}")
    print(f"   Pixels at full 255: {full_bright1} ({full_bright1/len(non_zero1)*100:.1f}%)")
    print(f"   Total text pixels: {len(non_zero1)}")
    
    # Method 2: Monochrome mask with paste (BRIGHT)
    print("\n2. Monochrome mask with paste (no antialiasing)")
    
    # Render to monochrome (1-bit)
    img2_mono = Image.new('1', (text_width, text_height), color=0)
    draw2_mono = ImageDraw.Draw(img2_mono)
    draw2_mono.text((0, -bbox[1]), test_text, font=font, fill=1)
    
    # Convert to grayscale using mask
    img2 = Image.new('L', (text_width, text_height), color=0)
    img2.paste(fill_value, (0, 0), mask=img2_mono)
    
    pixels2 = list(img2.getdata())
    non_zero2 = [p for p in pixels2 if p > 0]
    max2 = max(pixels2)
    avg2 = sum(non_zero2) / len(non_zero2) if non_zero2 else 0
    full_bright2 = sum(1 for p in non_zero2 if p == 255)
    
    print(f"   Max brightness: {max2}")
    print(f"   Average text brightness: {avg2:.2f}")
    print(f"   Pixels at full 255: {full_bright2} ({full_bright2/len(non_zero2)*100:.1f}%)")
    print(f"   Total text pixels: {len(non_zero2)}")
    
    # Save comparison
    img1.save("test_antialiased.png")
    img2.save("test_monochrome.png")
    
    # Create side-by-side comparison
    comparison = Image.new('L', (text_width * 2 + 20, text_height + 40), color=0)
    comparison.paste(img1, (10, 30))
    comparison.paste(img2, (text_width + 20, 30))
    
    draw_comp = ImageDraw.Draw(comparison)
    small_font = load_font(12)
    draw_comp.text((10, 5), "Antialiased (DIM)", font=small_font, fill=255)
    draw_comp.text((text_width + 20, 5), "Monochrome (BRIGHT)", font=small_font, fill=255)
    
    comparison.save("test_comparison.png")
    
    # Analysis
    print("\n" + "="*60)
    print("COMPARISON")
    print("="*60)
    print(f"Antialiased:")
    print(f"  - Max: {max1} (not full brightness!)")
    print(f"  - Average: {avg1:.2f}")
    print(f"  - Full bright pixels: {full_bright1}/{len(non_zero1)} ({full_bright1/len(non_zero1)*100:.1f}%)")
    print(f"\nMonochrome mask:")
    print(f"  - Max: {max2} (FULL BRIGHTNESS!)")
    print(f"  - Average: {avg2:.2f}")
    print(f"  - Full bright pixels: {full_bright2}/{len(non_zero2)} ({full_bright2/len(non_zero2)*100:.1f}%)")
    
    brightness_gain = avg2 - avg1
    print(f"\n✅ BRIGHTNESS GAIN: +{brightness_gain:.2f} ({brightness_gain/avg1*100:.1f}% brighter)")
    
    if full_bright2 == len(non_zero2):
        print("✅ PERFECT: ALL text pixels at maximum brightness (255)!")
    
    print("\nSaved images:")
    print("  - test_antialiased.png")
    print("  - test_monochrome.png")
    print("  - test_comparison.png")


if __name__ == "__main__":
    test_monochrome_vs_antialiased()
