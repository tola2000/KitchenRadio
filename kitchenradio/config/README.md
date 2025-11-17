# KitchenRadio Modular Configuration

The configuration system is now split into modular files for better organization and maintainability.

## Structure

```
kitchenradio/config/
├── __init__.py      # Main config module with backward compatibility
├── __main__.py      # Command-line interface
├── mpd.py           # MPD configuration
├── spotify.py       # Spotify/Librespot configuration
├── bluetooth.py     # Bluetooth configuration
├── display.py       # Display hardware configuration
├── buttons.py       # Button controller configuration
└── system.py        # System-wide settings
```

## Usage

### Option 1: Modular Imports (Recommended for new code)

```python
from kitchenradio.config import mpd, spotify, bluetooth

# Access configuration
print(f"MPD Server: {mpd.HOST}:{mpd.PORT}")
print(f"Spotify Device: {spotify.NAME}")
print(f"Bluetooth: {bluetooth.DEVICE_NAME}")
```

### Option 2: Backward Compatible (Works with existing code)

```python
from kitchenradio import config

# Access configuration (old style still works)
print(f"MPD Server: {config.MPD_HOST}:{config.MPD_PORT}")
print(f"Spotify Device: {config.LIBRESPOT_NAME}")
print(f"Bluetooth: {config.BLUETOOTH_DEVICE_NAME}")
```

## Configuration Files

### `mpd.py` - MPD Configuration
- **HOST**: MPD server hostname
- **PORT**: MPD server port
- **PASSWORD**: MPD password (None = no password)
- **TIMEOUT**: Connection timeout
- **DEFAULT_VOLUME**: Default volume (0-100)
- **MONITOR_POLL_INTERVAL**: Polling interval for status updates

### `spotify.py` - Spotify/Librespot Configuration
- **HOST**: Librespot server hostname
- **PORT**: Librespot server port
- **NAME**: Display name for Spotify Connect
- **DEFAULT_VOLUME**: Default volume (0-100)
- **MONITOR_POLL_INTERVAL**: Polling interval for status updates

### `bluetooth.py` - Bluetooth Configuration
- **DEVICE_NAME**: Bluetooth device name
- **PAIRING_TIMEOUT**: Pairing timeout in seconds
- **AUTO_RECONNECT**: Auto-reconnect to devices
- **DEFAULT_VOLUME**: Default volume (0-100)
- **MONITOR_POLL_INTERVAL**: Polling interval for status updates
- **AVRCP_RETRY_ATTEMPTS**: AVRCP connection retry attempts
- **AVRCP_RETRY_DELAY**: Delay between AVRCP retries

### `display.py` - Display Configuration
- **REFRESH_RATE**: Display refresh rate in Hz
- **WIDTH**, **HEIGHT**: Display dimensions
- **USE_HARDWARE**: Use physical display vs emulator
- **GPIO_DC**, **GPIO_RST**: GPIO pins for display
- **SPI_PORT**, **SPI_DEVICE**, **SPI_BUS_SPEED**: SPI configuration
- **ROTATE**: Display rotation (0-3)
- **VOLUME_OVERLAY_TIMEOUT**: Timeout for volume overlay
- **SCROLL_STEP**, **SCROLL_PAUSE_DURATION**: Scrolling behavior

### `buttons.py` - Button Configuration
- **USE_HARDWARE**: Use physical buttons
- **I2C_ADDRESS**: MCP23017 I2C address
- **DEBOUNCE_TIME**: Button debounce time
- **LONG_PRESS_TIME**: Long press threshold
- **VOLUME_STEP**: Volume change per button press
- **PIN_* constants**: Pin assignments for all buttons

### `system.py` - System Configuration
- **DEFAULT_SOURCE**: Default audio source on startup
- **AUTO_START_PLAYBACK**: Auto-start playback flag
- **POWER_ON_AT_STARTUP**: Power on at daemon start
- **LOG_LEVEL**: Logging level
- **I2C_BUS**: I2C bus number
- **GPIO_MODE**: GPIO pin numbering mode
- **API_PORT**, **API_HOST**: Web API configuration
- **THREAD_JOIN_TIMEOUT**: Thread cleanup timeout
- **AUTO_RECONNECT_DELAY**: Reconnection delay
- **ENABLE_* flags**: Feature toggles

## Customization

### Edit Individual Config Files

To change MPD settings, edit `kitchenradio/config/mpd.py`:
```python
HOST = '192.168.1.100'  # Change from localhost
PORT = 6600
DEFAULT_VOLUME = 75     # Change from 50
```

### Environment Variable Override

You can still override via environment variables in the main application code:
```python
import os
from kitchenradio.config import mpd

# Override in code
os.environ['MPD_HOST'] = '192.168.1.100'
```

## Command-Line Tools

### View All Configuration
```bash
python -m kitchenradio.config
```

### View Pin Assignments
```bash
python -m kitchenradio.config --pins
```

### View Everything
```bash
python -m kitchenradio.config --all
```

## Benefits of Modular Configuration

1. **Organized**: Each component has its own config file
2. **Maintainable**: Easy to find and update settings
3. **Scalable**: Add new config modules without affecting existing ones
4. **Backward Compatible**: Old code using `config.MPD_HOST` still works
5. **Modern**: New code can use cleaner imports like `mpd.HOST`
6. **Type-Safe**: IDEs can provide better autocomplete for specific modules

## Migration Guide

### Old Code (Still Works)
```python
from kitchenradio import config
mpd_client = MPDClient(host=config.MPD_HOST, port=config.MPD_PORT)
```

### New Code (Recommended)
```python
from kitchenradio.config import mpd
mpd_client = MPDClient(host=mpd.HOST, port=mpd.PORT)
```

Both approaches work! Choose what fits your coding style.
