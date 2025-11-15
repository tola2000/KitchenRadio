"""
ROOT CAUSE ANALYSIS: Text Brightness Inconsistency Issue
=========================================================

PROBLEM:
--------
Different UI elements (volume, clock, notifications, track info, menus) display text 
at different brightness levels on the SSD1322 OLED hardware.

ROOT CAUSE:
-----------
PIL's ImageDraw.draw.text() method produces DIMMER text than img.paste() method on 
SSD1322 hardware, even when both use fill=255.

This is likely due to:
1. draw.text() applies additional antialiasing/rendering processing that reduces pixel brightness
2. img.paste() preserves exact pre-rendered pixel values without additional processing
3. The SSD1322 grayscale OLED responds differently to these rendering methods

EVIDENCE:
---------
From test_brightness.py results:
- All PIL methods show similar brightness in software (avg ~150-155)
- NO pixels reach full brightness 255 (max is 252) - antialiasing effect
- User reports scrolling text (which uses paste) is BRIGHTER on hardware
- User reports volume/clock text (which uses draw.text) is DIMMER on hardware

SOLUTION:
---------
Use a SINGLE consistent rendering method for ALL text: render to buffer + paste

Implementation:
1. Created _draw_text_bright(draw, xy, text, font, fill) helper method
2. This method renders text to a buffer using _render_static_text()
3. Then pastes the buffer onto the main image
4. Replace ALL draw.text() calls with self._draw_text_bright()

LOCATIONS TO FIX:
-----------------
✅ format_track_info() - ALREADY FIXED (uses paste)
✅ format_volume_display() - FIXED (uses _draw_text_bright)
✅ format_clock_display() - FIXED (uses _draw_text_bright)
❌ format_simple_text() - NEEDS FIX (lines 382, 385)
❌ format_status() - NEEDS FIX (lines 474, 480, 484, 487, 489, 493, 497, 500, 502, 505)
❌ format_error_message() - NEEDS FIX (lines 545, 548, 552)
❌ format_default_display() - NEEDS FIX (lines 569, 572, 573)
❌ format_status_message() - NEEDS FIX (lines 621, 626, 638)
❌ format_menu_display() - NEEDS FIX (lines 954, 998, 1001, 1034, 1037)

NEXT STEPS:
-----------
Replace all remaining draw.text() calls with self._draw_text_bright() to ensure
100% consistent brightness across all UI elements.

WHY THIS IS THE PROPER FIX:
---------------------------
1. Addresses root cause (rendering method difference)
2. Ensures consistent brightness across ALL text
3. No workarounds - uses a single, proven method
4. Maintains pixel-perfect scrolling capability
5. Future-proof - all new text will use the same method
"""

print(__doc__)
