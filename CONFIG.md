# KitchenRadio Configuration Guide

## Configuration System

KitchenRadio uses a centralized configuration system with three layers of precedence:

1. **Environment Variables** (Highest Priority)
2. **config.py** (Default Values)
3. **Hardcoded Defaults** (Fallback)

## Configuration File

All configuration is centralized in `kitchenradio/config.py`. Edit this file to customize KitchenRadio behavior.

## Configuration Sections

### MPD (Music Player Daemon)

```python
MPD_HOST = 'localhost'          # MPD server hostname
MPD_PORT = 6600                  # MPD server port
MPD_PASSWORD = None              # MPD password (None = no password)
MPD_TIMEOUT = 10                 # Connection timeout in seconds
MPD_DEFAULT_VOLUME = 50          # Default volume (0-100)
```

### Librespot (Spotify)

```python
LIBRESPOT_HOST = 'localhost'     # Librespot server hostname
LIBRESPOT_PORT = 4370            # Librespot port
LIBRESPOT_NAME = 'KitchenRadio'  # Display name for Spotify
LIBRESPOT_DEFAULT_VOLUME = 50    # Default volume (0-100)
```

### Bluetooth

```python
BLUETOOTH_DEVICE_NAME = 'KitchenRadio'  # Bluetooth device name
BLUETOOTH_PAIRING_TIMEOUT = 60          # Pairing timeout in seconds
BLUETOOTH_AUTO_RECONNECT = True         # Auto-reconnect to devices
BLUETOOTH_DEFAULT_VOLUME = 50           # Default volume (0-100)
```

### Display

```python
DISPLAY_REFRESH_RATE = 80              # Display refresh rate in Hz
DISPLAY_WIDTH = 256                     # Display width in pixels
DISPLAY_HEIGHT = 64                     # Display height in pixels
DISPLAY_I2C_ADDRESS = 0x3C              # I2C address for display
DISPLAY_USE_HARDWARE = True             # Use physical display

# SPI Display Pins (for SSD1322)
DISPLAY_GPIO_DC = 25                    # GPIO pin for Data/Command signal
DISPLAY_GPIO_RST = 24                   # GPIO pin for Reset signal
DISPLAY_SPI_PORT = 0                    # SPI port number
DISPLAY_SPI_DEVICE = 0                  # SPI device/chip enable
DISPLAY_SPI_BUS_SPEED = 4_000_000       # SPI bus speed (4 MHz)
DISPLAY_ROTATE = 0                      # Rotation: 0=0°, 1=90°, 2=180°, 3=270°

# Overlay Timeouts
DISPLAY_VOLUME_OVERLAY_TIMEOUT = 3.0    # Volume overlay timeout
DISPLAY_MENU_OVERLAY_TIMEOUT = 3.0      # Menu overlay timeout
DISPLAY_NOTIFICATION_OVERLAY_TIMEOUT = 2.0  # Notification timeout

# Scrolling
DISPLAY_SCROLL_STEP = 2                 # Pixels per scroll update
DISPLAY_SCROLL_PAUSE_DURATION = 2.0     # Pause before scrolling starts
DISPLAY_SCROLL_PAUSE_AT_END = 2.0       # Pause at end before looping
```

### Buttons

```python
BUTTON_USE_HARDWARE = True          # Use physical buttons
BUTTON_I2C_ADDRESS = 0x27           # I2C address of MCP23017
BUTTON_DEBOUNCE_TIME = 0.02         # Debounce time in seconds
BUTTON_LONG_PRESS_TIME = 3.0        # Long press threshold in seconds
BUTTON_VOLUME_STEP = 5              # Volume change per button press

# MCP23017 Pin Assignments (0-15)
# Pins 0-7 are on Port A (GPA0-GPA7)
# Pins 8-15 are on Port B (GPB0-GPB7)

# Source buttons
BUTTON_PIN_SOURCE_MPD = 7           # MPD/Tuner button
BUTTON_PIN_SOURCE_SPOTIFY = 6       # Spotify/AUX button
BUTTON_PIN_SOURCE_BLUETOOTH = 5     # Bluetooth button

# Menu buttons
BUTTON_PIN_MENU_UP = 8              # Menu up button
BUTTON_PIN_MENU_DOWN = 9            # Menu down button

# Function buttons
BUTTON_PIN_SLEEP = 15               # Sleep timer button
BUTTON_PIN_REPEAT = 14              # Repeat mode button
BUTTON_PIN_SHUFFLE = 13             # Shuffle mode button
BUTTON_PIN_DISPLAY = 11             # Display mode button

# Transport buttons
BUTTON_PIN_TRANSPORT_PREVIOUS = 1   # Previous track button
BUTTON_PIN_TRANSPORT_PLAY_PAUSE = 3 # Play/Pause button
BUTTON_PIN_TRANSPORT_STOP = 4       # Stop button
BUTTON_PIN_TRANSPORT_NEXT = 2       # Next track button

# Volume buttons
BUTTON_PIN_VOLUME_DOWN = 10         # Volume down button
BUTTON_PIN_VOLUME_UP = 12           # Volume up button

# Power button
BUTTON_PIN_POWER = 0                # Power button
```

### Monitor

```python
MONITOR_EXPECTED_VALUE_TIMEOUT = 2.0     # Expected value timeout
MPD_MONITOR_POLL_INTERVAL = 1.0          # MPD polling interval
LIBRESPOT_MONITOR_POLL_INTERVAL = 0.5    # Librespot polling interval
BLUETOOTH_MONITOR_POLL_INTERVAL = 1.0    # Bluetooth polling interval
```

### System

```python
DEFAULT_SOURCE = 'mpd'              # Default audio source
AUTO_START_PLAYBACK = False         # Auto-start playback
POWER_ON_AT_STARTUP = True          # Power on at startup
LOG_LEVEL = 'INFO'                  # Logging level
```

## Environment Variable Override

You can override any config value using environment variables:

```bash
# Override MPD host and port
export MPD_HOST=192.168.1.100
export MPD_PORT=6600

# Override display settings
export DISPLAY_REFRESH_RATE=60
export DISPLAY_USE_HARDWARE=false

# Override button settings
export BUTTON_LONG_PRESS_TIME=2.0

# Run daemon
python run_daemon.py
```

## Usage Examples

### Running with Default Config

```python
from kitchenradio import config
from kitchenradio.radio.kitchen_radio import KitchenRadio

# Uses values from config.py
radio = KitchenRadio()
radio.start()
```

### Running with Custom Config

```python
import os
from kitchenradio import config
from kitchenradio.radio.kitchen_radio import KitchenRadio

# Override via environment
os.environ['MPD_HOST'] = '192.168.1.100'
os.environ['DEFAULT_VOLUME'] = '75'

radio = KitchenRadio()
radio.start()
```

### Programmatic Configuration

```python
from kitchenradio import config

# Modify config values directly
config.MPD_HOST = '192.168.1.100'
config.MPD_PORT = 6600
config.BUTTON_LONG_PRESS_TIME = 2.0

# Now create components
from kitchenradio.radio.kitchen_radio import KitchenRadio
radio = KitchenRadio()
```

## Configuration Debugging

### View All Configuration

Print current configuration:

```python
from kitchenradio import config
config.print_config()
```

Or from command line:

```bash
python -m kitchenradio.config
```

### View Pin Assignments

Print button and display pin map:

```python
from kitchenradio import config
config.print_pin_map()
```

Or from command line:

```bash
python -m kitchenradio.config --pins
```

### View Everything

```bash
python -m kitchenradio.config --all
```

## Hardware vs Software Mode

For development without physical hardware:

```python
# In config.py
DISPLAY_USE_HARDWARE = False  # Use display emulator
BUTTON_USE_HARDWARE = False   # Software-only buttons
```

Or with environment variables:

```bash
export DISPLAY_USE_HARDWARE=false
export BUTTON_USE_HARDWARE=false
python run_daemon.py
```

## Feature Flags

Enable/disable major features:

```python
ENABLE_BLUETOOTH = True
ENABLE_SPOTIFY = True
ENABLE_MPD = True
ENABLE_WEB_API = False
ENABLE_REMOTE_CONTROL = False
```

## Hardware Pin Customization

### Changing Button Pins

To change button pin assignments, modify the `BUTTON_PIN_*` values in `config.py`:

```python
# Example: Swap volume up/down pins
BUTTON_PIN_VOLUME_DOWN = 12  # Was 10
BUTTON_PIN_VOLUME_UP = 10    # Was 12
```

### Changing Display Pins

To change display GPIO pins:

```python
# Example: Use different GPIO pins for display
DISPLAY_GPIO_DC = 17   # Change D/C from GPIO 25 to 17
DISPLAY_GPIO_RST = 18  # Change RST from GPIO 24 to 18
```

### Pin Reference

**MCP23017 Pins (0-15)**:
- Pins 0-7: Port A (GPA0-GPA7)
- Pins 8-15: Port B (GPB0-GPB7)

**Raspberry Pi GPIO**:
- SPI: GPIO 10 (MOSI), GPIO 9 (MISO), GPIO 11 (SCLK)
- I2C: GPIO 2 (SDA), GPIO 3 (SCL)
- Custom: GPIO 24 (RST), GPIO 25 (D/C)

## Best Practices

1. **Don't modify code**: Change `config.py` instead
2. **Use environment variables** for deployment-specific settings
3. **Keep secrets out of config.py**: Use environment variables for passwords
4. **Test changes**: Verify configuration with `config.print_config()`
5. **Document changes**: Comment your modifications in config.py
6. **Pin conflicts**: Ensure GPIO pins don't conflict with SPI/I2C functions

## Troubleshooting

### Display not working

```python
# Check hardware availability
DISPLAY_USE_HARDWARE = False  # Try software mode first
```

### Buttons not responding

```python
# Adjust debounce or long press timing
BUTTON_DEBOUNCE_TIME = 0.05  # Increase debounce
BUTTON_LONG_PRESS_TIME = 2.0  # Decrease threshold
```

### Connection timeouts

```python
# Increase timeouts
MPD_TIMEOUT = 20
LIBRESPOT_TIMEOUT = 20
```

### Scroll speed issues

```python
# Adjust scrolling
DISPLAY_SCROLL_STEP = 1  # Slower scrolling
DISPLAY_SCROLL_PAUSE_DURATION = 3.0  # Longer pause
```
