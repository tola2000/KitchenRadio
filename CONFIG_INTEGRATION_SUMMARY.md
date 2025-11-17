# Configuration Integration Summary

## Overview

Successfully integrated the modular configuration system (`kitchenradio.config`) into all hardware controllers. All hardcoded values have been replaced with config parameters, allowing easy customization through a single source of truth.

**Date Completed:** November 17, 2025

---

## What Changed

### ButtonController Integration ✅

**File:** `kitchenradio/radio/hardware/button_controller.py`

**Changes Made:**
1. Added config imports:
   ```python
   from kitchenradio import config
   from kitchenradio.config import buttons as buttons_config
   ```

2. Replaced hardcoded `BUTTON_PIN_MAP` with config-based function:
   ```python
   def _get_button_pin_map():
       """Get button pin mapping from config"""
       return {
           ButtonType.SOURCE_MPD: buttons_config.PIN_SOURCE_MPD,
           ButtonType.SOURCE_SPOTIFY: buttons_config.PIN_SOURCE_SPOTIFY,
           # ... all 17 buttons mapped from config
       }
   BUTTON_PIN_MAP = _get_button_pin_map()
   ```

3. Updated `__init__` parameters to use config defaults:
   - `debounce_time` → `buttons_config.DEBOUNCE_TIME` (0.02s)
   - `long_press_time` → `buttons_config.LONG_PRESS_TIME` (3.0s)
   - `use_hardware` → `buttons_config.USE_HARDWARE` (True)
   - `i2c_address` → `buttons_config.I2C_ADDRESS` (0x27)

4. Updated volume methods to use config:
   - `volume_up(step=buttons_config.VOLUME_STEP)` (5)
   - `volume_down(step=buttons_config.VOLUME_STEP)` (5)

**Result:** ButtonController now respects all configuration settings while maintaining backward compatibility. Existing code calling `ButtonController()` with no arguments will use config defaults.

---

### DisplayController Integration ✅

**File:** `kitchenradio/radio/hardware/display_controller.py`

**Changes Made:**
1. Added config imports:
   ```python
   from kitchenradio import config
   from kitchenradio.config import display as display_config
   ```

2. Updated `__init__` parameters to use config defaults:
   - `refresh_rate` → `display_config.REFRESH_RATE` (80 Hz)
   - Formatter height → `display_config.HEIGHT` (64 pixels)

3. Updated overlay timeouts:
   - `overlay_timeout` → `display_config.MENU_OVERLAY_TIMEOUT` (3.0s)
   - `volume_change_ignore_duration` → `display_config.VOLUME_CHANGE_IGNORE_DURATION` (1.0s)

4. Updated scrolling configuration:
   - `scroll_step` → `display_config.SCROLL_STEP` (2 pixels)
   - `scroll_pause_duration` → `display_config.SCROLL_PAUSE_DURATION` (2.0s)

5. Updated overlay methods:
   - `show_volume_overlay(timeout=display_config.VOLUME_OVERLAY_TIMEOUT)` (3.0s)
   - `show_menu_overlay(timeout=display_config.MENU_OVERLAY_TIMEOUT)` (3.0s)

**Result:** DisplayController now uses config for all timing and overlay parameters.

---

### DisplayInterface Integration ✅

**File:** `kitchenradio/radio/hardware/display_interface.py`

**Changes Made:**
1. Added config imports:
   ```python
   from kitchenradio import config
   from kitchenradio.config import display as display_config
   ```

2. Updated class constants to use config:
   ```python
   WIDTH = display_config.WIDTH                    # 256
   HEIGHT = display_config.HEIGHT                  # 64
   DEFAULT_SPI_BUS_SPEED = display_config.SPI_BUS_SPEED  # 4 MHz
   GPIO_DC = display_config.GPIO_DC                # 25
   GPIO_RST = display_config.GPIO_RST              # 24
   SPI_PORT = display_config.SPI_PORT              # 0
   SPI_DEVICE = display_config.SPI_DEVICE          # 0
   ```

3. Updated `__init__` parameters to use config defaults:
   - `bus_speed_hz` → `display_config.SPI_BUS_SPEED` (4,000,000 Hz)
   - `gpio_dc` → `display_config.GPIO_DC` (25)
   - `gpio_rst` → `display_config.GPIO_RST` (24)
   - `spi_port` → `display_config.SPI_PORT` (0)
   - `spi_device` → `display_config.SPI_DEVICE` (0)
   - `rotate` → `display_config.ROTATE` (0)

**Result:** DisplayInterface hardware parameters now fully configurable through `config/display.py`.

---

## Benefits

### 1. **Single Source of Truth**
All hardware configuration in one place (`kitchenradio/config/`):
- **buttons.py**: Button pin mappings, timing, I2C address
- **display.py**: Display hardware, timing, overlay behavior

### 2. **Easy Customization**
Change hardware settings by editing config files instead of searching through code:
```python
# kitchenradio/config/buttons.py
PIN_SOURCE_MPD = 7      # Change button pin here
DEBOUNCE_TIME = 0.02    # Adjust timing here
VOLUME_STEP = 5         # Change volume increment here
```

### 3. **Backward Compatibility**
Existing code continues to work without changes:
```python
# Still works - uses config defaults
button_controller = ButtonController()

# Also works - overrides specific values
button_controller = ButtonController(debounce_time=0.05)
```

### 4. **Consistent Behavior**
All components use the same configuration values:
- Web interface creates controllers with same defaults
- Daemon creates controllers with same defaults
- Tests can override defaults as needed

### 5. **Documentation**
Config files are self-documenting:
```python
# config/buttons.py
DEBOUNCE_TIME = 0.02  # seconds - debounce time for button presses
LONG_PRESS_TIME = 3.0  # seconds - threshold for long press detection
VOLUME_STEP = 5  # Volume change per button press (0-100)
```

---

## Configuration Reference

### Button Configuration (`config/buttons.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `USE_HARDWARE` | `True` | Enable physical buttons (MCP23017) |
| `I2C_ADDRESS` | `0x27` | I2C address of MCP23017 |
| `DEBOUNCE_TIME` | `0.02` | Button debounce time (seconds) |
| `LONG_PRESS_TIME` | `3.0` | Long press threshold (seconds) |
| `VOLUME_STEP` | `5` | Volume change per press (0-100) |
| `PIN_SOURCE_MPD` | `7` | MPD source button pin |
| `PIN_SOURCE_SPOTIFY` | `6` | Spotify source button pin |
| `PIN_SOURCE_BLUETOOTH` | `5` | Bluetooth source button pin |
| `PIN_MENU_UP` | `8` | Menu up button pin |
| `PIN_MENU_DOWN` | `9` | Menu down button pin |
| `PIN_SLEEP` | `15` | Sleep button pin |
| `PIN_REPEAT` | `14` | Repeat button pin |
| `PIN_SHUFFLE` | `13` | Shuffle button pin |
| `PIN_DISPLAY` | `11` | Display button pin |
| `PIN_TRANSPORT_PREVIOUS` | `1` | Previous track button pin |
| `PIN_TRANSPORT_PLAY_PAUSE` | `3` | Play/Pause button pin |
| `PIN_TRANSPORT_STOP` | `4` | Stop button pin |
| `PIN_TRANSPORT_NEXT` | `2` | Next track button pin |
| `PIN_VOLUME_DOWN` | `10` | Volume down button pin |
| `PIN_VOLUME_UP` | `12` | Volume up button pin |
| `PIN_POWER` | `0` | Power button pin |

### Display Configuration (`config/display.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `REFRESH_RATE` | `80` | Display refresh rate (Hz) |
| `WIDTH` | `256` | Display width (pixels) |
| `HEIGHT` | `64` | Display height (pixels) |
| `I2C_ADDRESS` | `0x3C` | I2C address for SSD1322 |
| `USE_HARDWARE` | `True` | Use hardware display |
| `GPIO_DC` | `25` | Data/Command GPIO pin |
| `GPIO_RST` | `24` | Reset GPIO pin |
| `SPI_PORT` | `0` | SPI port number |
| `SPI_DEVICE` | `0` | SPI device/chip enable |
| `SPI_BUS_SPEED` | `4000000` | SPI bus speed (Hz) |
| `ROTATE` | `0` | Display rotation (0-3) |
| `VOLUME_OVERLAY_TIMEOUT` | `3.0` | Volume display timeout (s) |
| `MENU_OVERLAY_TIMEOUT` | `3.0` | Menu display timeout (s) |
| `NOTIFICATION_OVERLAY_TIMEOUT` | `2.0` | Notification timeout (s) |
| `SCROLL_STEP` | `2` | Scroll speed (pixels/update) |
| `SCROLL_PAUSE_DURATION` | `2.0` | Pause before scroll (s) |
| `SCROLL_PAUSE_AT_END` | `2.0` | Pause at end before loop (s) |
| `VOLUME_CHANGE_IGNORE_DURATION` | `1.0` | Ignore status after volume change (s) |

---

## Usage Examples

### Example 1: Custom Button Timing

```python
# config/buttons.py
DEBOUNCE_TIME = 0.05  # Slower debounce for noisy buttons
LONG_PRESS_TIME = 2.0  # Shorter long press threshold
VOLUME_STEP = 10       # Bigger volume steps
```

### Example 2: Custom Display Speed

```python
# config/display.py
REFRESH_RATE = 120           # Faster refresh (smoother scrolling)
SCROLL_STEP = 3              # Faster scroll speed
VOLUME_OVERLAY_TIMEOUT = 5.0 # Keep volume display longer
```

### Example 3: Remap Button Pins

```python
# config/buttons.py
PIN_SOURCE_MPD = 10      # Move MPD button to pin 10
PIN_SOURCE_SPOTIFY = 11  # Move Spotify button to pin 11
```

### Example 4: Override in Code

```python
# For testing with different timing
button_controller = ButtonController(
    debounce_time=0.1,      # Override config default
    long_press_time=5.0,    # Override config default
    i2c_address=0x20        # Different I2C address
)

# For development with custom display
display_interface = DisplayInterface(
    use_hardware=False,     # Force emulator mode
    rotate=2                # Flip display upside down
)
```

---

## Migration Notes

### For Existing Code

**No changes required!** All existing code continues to work:

```python
# These all still work exactly as before
button_controller = ButtonController()
display_controller = DisplayController(kitchen_radio)
display_interface = DisplayInterface()
```

### For New Code

**Recommended:** Let config provide defaults:

```python
# Good - uses config defaults
button_controller = ButtonController(kitchen_radio)

# Good - override only what's needed
display_interface = DisplayInterface(use_hardware=True)

# Avoid - hardcoding values
button_controller = ButtonController(
    debounce_time=0.02,    # Don't hardcode - let config provide this
    i2c_address=0x27       # Don't hardcode - let config provide this
)
```

---

## Testing

### Verify Config Integration

```python
# Test that config values are used
from kitchenradio.config import buttons, display

# Check button config
print(f"Button debounce time: {buttons.DEBOUNCE_TIME}")
print(f"Volume step: {buttons.VOLUME_STEP}")
print(f"MPD button pin: {buttons.PIN_SOURCE_MPD}")

# Check display config
print(f"Display refresh rate: {display.REFRESH_RATE}")
print(f"SPI bus speed: {display.SPI_BUS_SPEED}")
print(f"Volume overlay timeout: {display.VOLUME_OVERLAY_TIMEOUT}")

# Test controller creation
from kitchenradio.radio.hardware.button_controller import ButtonController
controller = ButtonController()
print(f"Controller debounce: {controller.debounce_time}")
print(f"Controller I2C address: 0x{controller.i2c_address:02X}")
```

### View Configuration

```bash
# Display all config values
python -m kitchenradio.config --all

# Display button pin mappings
python -m kitchenradio.config --pins
```

---

## Related Documentation

- **CONFIGURATION_REFACTORING.md** - Details of config package creation
- **CONFIG.md** - Full configuration guide
- **kitchenradio/config/README.md** - Config module documentation
- **UNIFIED_DAEMON_REFACTORING.md** - Daemon command-line options

---

## Summary

✅ **ButtonController** - All timing, pins, and hardware settings from config  
✅ **DisplayController** - All refresh rates, overlays, and scrolling from config  
✅ **DisplayInterface** - All SPI hardware settings from config  
✅ **Backward Compatible** - Existing code works without changes  
✅ **Well Documented** - Config files include comments and defaults  

**Result:** Complete configuration integration with zero breaking changes! 🎉
