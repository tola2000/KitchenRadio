# Fix: BMP Not Updating in Hardware Mode

## Problem
When the display interface is in hardware mode (using real SPI display on Raspberry Pi), the BMP data was not being updated. This meant the web API endpoint `/api/display/image` would show stale or empty images.

## Root Cause

### Original Code (display_interface.py)

```python
def render_frame(self, draw_func: Callable[[ImageDraw.Draw], None]):
    if self.mode == 'hardware':
        # Hardware mode - use luma canvas
        with canvas(self.device) as draw:
            draw_func(draw)
        # ❌ BMP data NOT updated!
        
    else:  # emulator
        # Emulator mode - render to PIL image
        self.current_image = Image.new('1', (self.WIDTH, self.HEIGHT), 0)
        draw = ImageDraw.Draw(self.current_image)
        draw_func(draw)
        self._update_bmp_data()  # ✅ BMP updated only in emulator mode
        self.last_update = time.time()
```

### Why This Was Wrong

**Hardware Mode:**
- ✅ Rendered to physical SPI display
- ❌ Did NOT update `self.current_image`
- ❌ Did NOT update `self.bmp_data`
- ❌ Web API `/api/display/image` returned stale/empty image

**Emulator Mode:**
- ✅ Rendered to PIL image
- ✅ Updated `self.current_image`
- ✅ Updated `self.bmp_data`
- ✅ Web API worked correctly

## The Fix

### Updated Code

```python
def render_frame(self, draw_func: Callable[[ImageDraw.Draw], None]):
    if self.mode == 'hardware':
        # Hardware mode - render to real SPI display
        with canvas(self.device) as draw:
            draw_func(draw)
        
        # ALSO render to PIL image for BMP export (web viewing) ✅
        self.current_image = Image.new('1', (self.WIDTH, self.HEIGHT), 0)
        draw = ImageDraw.Draw(self.current_image)
        draw_func(draw)
        self._update_bmp_data()
        self.last_update = time.time()
        
    else:  # emulator
        # Emulator mode - render to PIL image only
        self.current_image = Image.new('1', (self.WIDTH, self.HEIGHT), 0)
        draw = ImageDraw.Draw(self.current_image)
        draw_func(draw)
        self._update_bmp_data()
        self.last_update = time.time()
```

## How It Works Now

### Hardware Mode (Raspberry Pi with SSD1322)

1. **Render to hardware display:**
   ```python
   with canvas(self.device) as draw:
       draw_func(draw)  # Shows on physical OLED
   ```

2. **ALSO render to PIL image:**
   ```python
   self.current_image = Image.new('1', (self.WIDTH, self.HEIGHT), 0)
   draw = ImageDraw.Draw(self.current_image)
   draw_func(draw)  # Creates in-memory image
   ```

3. **Update BMP data for web:**
   ```python
   self._update_bmp_data()  # Converts to BMP bytes
   self.last_update = time.time()
   ```

**Result:**
- ✅ Physical display shows content
- ✅ Web API shows content
- ✅ Both stay in sync

### Emulator Mode (Windows/Development)

1. **Render to PIL image:**
   ```python
   self.current_image = Image.new('1', (self.WIDTH, self.HEIGHT), 0)
   draw = ImageDraw.Draw(self.current_image)
   draw_func(draw)
   ```

2. **Update BMP data:**
   ```python
   self._update_bmp_data()
   self.last_update = time.time()
   ```

**Result:**
- ✅ Web API shows content
- ✅ Perfect for development

## Benefits

### Before Fix

**Hardware Mode:**
- ✅ Physical display works
- ❌ Web API shows nothing
- ❌ Can't monitor remotely

**Emulator Mode:**
- ✅ Web API works

### After Fix

**Hardware Mode:**
- ✅ Physical display works
- ✅ Web API works
- ✅ Can monitor remotely
- ✅ Both stay synchronized

**Emulator Mode:**
- ✅ Web API works (unchanged)

## Use Cases

### Remote Monitoring
With this fix, you can:
1. Run on Raspberry Pi with hardware display
2. View what's on the display remotely via web API
3. Monitor from your phone/computer: `http://pi-address:5001/api/display/image`

### Debugging
- See what's rendering on hardware without being at the Pi
- Compare hardware vs emulator rendering
- Verify display content remotely

### Development
- Test on Windows with emulator
- Deploy to Pi with hardware
- Web API works in both modes

## Performance Impact

**Minimal** - The drawing function runs twice in hardware mode:
1. Once for hardware (luma canvas)
2. Once for PIL image (BMP export)

The draw_func is typically fast (< 1ms), and this ensures the web API always has current content.

## API Endpoints That Now Work in Hardware Mode

- `GET /api/display/image` - Returns current display as PNG ✅
- `GET /api/display/ascii` - Returns ASCII art of display ✅
- `GET /api/display/status` - Shows last update time ✅

## Testing

### Emulator Mode (Windows)
```powershell
python -m kitchenradio.web.kitchen_radio_web
# Open: http://127.0.0.1:5001/api/display/image
# Should show current display ✅
```

### Hardware Mode (Raspberry Pi)
```bash
python -m kitchenradio.web.kitchen_radio_web
# Physical display shows content ✅
# Open: http://pi-ip:5001/api/display/image
# Web shows same content ✅
```

## Summary

**Fixed File:** `kitchenradio/radio/hardware/display_interface.py`

**Change:** In hardware mode, render to BOTH hardware display AND PIL image (for BMP export)

**Result:** Web API `/api/display/image` now works in both hardware and emulator modes! ✅

The display rendering is now truly unified - it works everywhere and the web API always shows current content regardless of mode! 🎉
