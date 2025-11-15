"""
Script to replace all draw.text() calls with self._draw_text_bright() calls
"""

import re

# Read the file
with open('kitchenradio/radio/hardware/display_formatter.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to match draw.text() calls
# Matches: draw.text((x, y), text, font=font, fill=value)
# Captures: coordinates, text, font, fill value

def replace_draw_text(match):
    """Replace draw.text() with self._draw_text_bright()"""
    full_match = match.group(0)
    
    # Skip if it's in a helper function that creates buffers (_render_static_text, _render_scrolling_text)
    # These are OK because they're creating intermediate buffers, not final display
    return full_match
    
# We need to be more careful - let's just document all the locations
# and replace them manually to be safe

lines = content.split('\n')
locations = []

for i, line in enumerate(lines, 1):
    # Skip helper functions that create buffers
    if i >= 260 and i <= 315:  # _render_static_text and _render_scrolling_text range
        continue
    
    # Find draw.text() calls
    if 'draw.text(' in line and 'self._draw_text_bright' not in line:
        # Extract indentation
        indent = len(line) - len(line.lstrip())
        locations.append((i, indent, line.strip()))

print("Found draw.text() calls that need to be replaced:")
print("="*60)
for line_num, indent, code in locations:
    print(f"Line {line_num}: {code}")

print("\n" + "="*60)
print(f"Total: {len(locations)} locations")
