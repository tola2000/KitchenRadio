"""
KitchenRadio Configuration Package

Modular configuration split by component:
- mpd: MPD (Music Player Daemon) configuration
- spotify: Spotify/Librespot configuration
- bluetooth: Bluetooth audio configuration
- display: Display hardware configuration
- buttons: Button controller configuration
- system: System-wide settings

You can import specific modules:
    from kitchenradio.config import mpd, spotify, bluetooth
    print(mpd.HOST, spotify.PORT, bluetooth.DEVICE_NAME)

Or use backward-compatible imports:
    from kitchenradio import config
    print(config.MPD_HOST, config.LIBRESPOT_PORT, config.BLUETOOTH_DEVICE_NAME)
"""

# Import all config modules
from . import mpd
from . import spotify
from . import bluetooth
from . import display
from . import buttons
from . import outputs
from . import system

# =============================================================================
# Backward Compatibility Exports (Old naming convention)
# =============================================================================

# MPD Configuration
MPD_HOST = mpd.HOST
MPD_PORT = mpd.PORT
MPD_PASSWORD = mpd.PASSWORD
MPD_TIMEOUT = mpd.TIMEOUT
MPD_DEFAULT_VOLUME = mpd.DEFAULT_VOLUME

# Librespot (Spotify) Configuration
LIBRESPOT_HOST = spotify.HOST
LIBRESPOT_PORT = spotify.PORT
LIBRESPOT_NAME = spotify.NAME
LIBRESPOT_DEFAULT_VOLUME = spotify.DEFAULT_VOLUME

# Bluetooth Configuration
BLUETOOTH_DEVICE_NAME = bluetooth.DEVICE_NAME
BLUETOOTH_PAIRING_TIMEOUT = bluetooth.PAIRING_TIMEOUT
BLUETOOTH_AUTO_RECONNECT = bluetooth.AUTO_RECONNECT
BLUETOOTH_DEFAULT_VOLUME = bluetooth.DEFAULT_VOLUME

# Display Configuration
DISPLAY_REFRESH_RATE = display.REFRESH_RATE
DISPLAY_WIDTH = display.WIDTH
DISPLAY_HEIGHT = display.HEIGHT
DISPLAY_I2C_ADDRESS = display.I2C_ADDRESS
DISPLAY_USE_HARDWARE = display.USE_HARDWARE
DISPLAY_GPIO_DC = display.GPIO_DC
DISPLAY_GPIO_RST = display.GPIO_RST
DISPLAY_SPI_PORT = display.SPI_PORT
DISPLAY_SPI_DEVICE = display.SPI_DEVICE
DISPLAY_SPI_BUS_SPEED = display.SPI_BUS_SPEED
DISPLAY_ROTATE = display.ROTATE
DISPLAY_VOLUME_OVERLAY_TIMEOUT = display.VOLUME_OVERLAY_TIMEOUT
DISPLAY_MENU_OVERLAY_TIMEOUT = display.MENU_OVERLAY_TIMEOUT
DISPLAY_NOTIFICATION_OVERLAY_TIMEOUT = display.NOTIFICATION_OVERLAY_TIMEOUT
DISPLAY_SCROLL_STEP = display.SCROLL_STEP
DISPLAY_SCROLL_PAUSE_DURATION = display.SCROLL_PAUSE_DURATION
DISPLAY_SCROLL_PAUSE_AT_END = display.SCROLL_PAUSE_AT_END
DISPLAY_VOLUME_CHANGE_IGNORE_DURATION = display.VOLUME_CHANGE_IGNORE_DURATION

# Button Controller Configuration
BUTTON_USE_HARDWARE = buttons.USE_HARDWARE
BUTTON_I2C_ADDRESS = buttons.I2C_ADDRESS
BUTTON_DEBOUNCE_TIME = buttons.DEBOUNCE_TIME
BUTTON_LONG_PRESS_TIME = buttons.LONG_PRESS_TIME
BUTTON_VOLUME_STEP = buttons.VOLUME_STEP
BUTTON_PIN_SOURCE_MPD = buttons.PIN_SOURCE_MPD
BUTTON_PIN_SOURCE_SPOTIFY = buttons.PIN_SOURCE_SPOTIFY
BUTTON_PIN_SOURCE_BLUETOOTH = buttons.PIN_SOURCE_BLUETOOTH
BUTTON_PIN_MENU_UP = buttons.PIN_MENU_UP
BUTTON_PIN_MENU_DOWN = buttons.PIN_MENU_DOWN
BUTTON_PIN_SLEEP = buttons.PIN_SLEEP
BUTTON_PIN_REPEAT = buttons.PIN_REPEAT
BUTTON_PIN_SHUFFLE = buttons.PIN_SHUFFLE
BUTTON_PIN_DISPLAY = buttons.PIN_DISPLAY
BUTTON_PIN_TRANSPORT_PREVIOUS = buttons.PIN_TRANSPORT_PREVIOUS
BUTTON_PIN_TRANSPORT_PLAY_PAUSE = buttons.PIN_TRANSPORT_PLAY_PAUSE
BUTTON_PIN_TRANSPORT_STOP = buttons.PIN_TRANSPORT_STOP
BUTTON_PIN_TRANSPORT_NEXT = buttons.PIN_TRANSPORT_NEXT
BUTTON_PIN_VOLUME_DOWN = buttons.PIN_VOLUME_DOWN
BUTTON_PIN_VOLUME_UP = buttons.PIN_VOLUME_UP
BUTTON_PIN_POWER = buttons.PIN_POWER

# Monitor Configuration
MONITOR_EXPECTED_VALUE_TIMEOUT = system.EXPECTED_VALUE_TIMEOUT
MPD_MONITOR_POLL_INTERVAL = mpd.MONITOR_POLL_INTERVAL
LIBRESPOT_MONITOR_POLL_INTERVAL = spotify.MONITOR_POLL_INTERVAL
BLUETOOTH_MONITOR_POLL_INTERVAL = bluetooth.MONITOR_POLL_INTERVAL
BLUETOOTH_AVRCP_RETRY_ATTEMPTS = bluetooth.AVRCP_RETRY_ATTEMPTS
BLUETOOTH_AVRCP_RETRY_DELAY = bluetooth.AVRCP_RETRY_DELAY

# Output Configuration
AMPLIFIER_PIN = outputs.AMPLIFIER_PIN
AMPLIFIER_ACTIVE_HIGH = outputs.AMPLIFIER_ACTIVE_HIGH
AMPLIFIER_POWER_ON_DELAY = outputs.AMPLIFIER_POWER_ON_DELAY
AMPLIFIER_POWER_OFF_DELAY = outputs.AMPLIFIER_POWER_OFF_DELAY
OUTPUT_USE_HARDWARE = outputs.OUTPUT_USE_HARDWARE

# System Configuration
DEFAULT_SOURCE = system.DEFAULT_SOURCE
AUTO_START_PLAYBACK = system.AUTO_START_PLAYBACK
POWER_ON_AT_STARTUP = system.POWER_ON_AT_STARTUP
LOG_LEVEL = system.LOG_LEVEL
I2C_BUS = system.I2C_BUS
GPIO_MODE = system.GPIO_MODE
API_PORT = system.API_PORT
API_HOST = system.API_HOST
API_ENABLE = system.API_ENABLE
THREAD_JOIN_TIMEOUT = system.THREAD_JOIN_TIMEOUT
AUTO_RECONNECT_DELAY = system.AUTO_RECONNECT_DELAY
MAX_RECONNECT_ATTEMPTS = system.MAX_RECONNECT_ATTEMPTS
AUDIO_FADE_DURATION = system.AUDIO_FADE_DURATION
ENABLE_BLUETOOTH = system.ENABLE_BLUETOOTH
ENABLE_SPOTIFY = system.ENABLE_SPOTIFY
ENABLE_MPD = system.ENABLE_MPD
ENABLE_WEB_API = system.ENABLE_WEB_API
ENABLE_REMOTE_CONTROL = system.ENABLE_REMOTE_CONTROL

# =============================================================================
# Helper Functions
# =============================================================================

def get_button_pin_map() -> dict:
    """
    Get button pin mapping as a dictionary.
    
    Returns:
        Dictionary mapping button names to MCP23017 pin numbers
    """
    return buttons.get_pin_map()


def get_config_dict() -> dict:
    """
    Get all configuration as a dictionary.
    
    Returns:
        Dictionary of all configuration values
    """
    import sys
    module = sys.modules[__name__]
    config = {}
    
    for key in dir(module):
        if key.isupper():  # Only include uppercase variables (constants)
            config[key] = getattr(module, key)
    
    return config


def print_config():
    """Print all configuration values."""
    config = get_config_dict()
    
    print("=" * 80)
    print("KitchenRadio Configuration")
    print("=" * 80)
    
    current_section = None
    for key, value in sorted(config.items()):
        # Detect section changes based on prefix
        section = key.split('_')[0]
        if section != current_section:
            print(f"\n{section} Configuration:")
            print("-" * 40)
            current_section = section
        
        print(f"  {key}: {value}")
    
    print("=" * 80)


def print_pin_map():
    """Print button pin assignments in a readable format."""
    print("=" * 80)
    print("KitchenRadio Button Pin Map (MCP23017)")
    print("=" * 80)
    print("\nPort A (Pins 0-7 / GPA0-GPA7):")
    print("-" * 40)
    
    pins_a = {
        0: ('POWER', BUTTON_PIN_POWER),
        1: ('TRANSPORT_PREVIOUS', BUTTON_PIN_TRANSPORT_PREVIOUS),
        2: ('TRANSPORT_NEXT', BUTTON_PIN_TRANSPORT_NEXT),
        3: ('TRANSPORT_PLAY_PAUSE', BUTTON_PIN_TRANSPORT_PLAY_PAUSE),
        4: ('TRANSPORT_STOP', BUTTON_PIN_TRANSPORT_STOP),
        5: ('SOURCE_BLUETOOTH', BUTTON_PIN_SOURCE_BLUETOOTH),
        6: ('SOURCE_SPOTIFY', BUTTON_PIN_SOURCE_SPOTIFY),
        7: ('SOURCE_MPD', BUTTON_PIN_SOURCE_MPD),
    }
    
    for pin_num in range(8):
        assigned = None
        for name, config_pin in pins_a.values():
            if config_pin == pin_num:
                assigned = name
                break
        if assigned:
            print(f"  GPA{pin_num} (Pin {pin_num}): {assigned}")
        else:
            print(f"  GPA{pin_num} (Pin {pin_num}): <unassigned>")
    
    print("\nPort B (Pins 8-15 / GPB0-GPB7):")
    print("-" * 40)
    
    pins_b = {
        8: ('MENU_UP', BUTTON_PIN_MENU_UP),
        9: ('MENU_DOWN', BUTTON_PIN_MENU_DOWN),
        10: ('VOLUME_DOWN', BUTTON_PIN_VOLUME_DOWN),
        11: ('DISPLAY', BUTTON_PIN_DISPLAY),
        12: ('VOLUME_UP', BUTTON_PIN_VOLUME_UP),
        13: ('SHUFFLE', BUTTON_PIN_SHUFFLE),
        14: ('REPEAT', BUTTON_PIN_REPEAT),
        15: ('SLEEP', BUTTON_PIN_SLEEP),
    }
    
    for pin_num in range(8, 16):
        assigned = None
        for name, config_pin in pins_b.values():
            if config_pin == pin_num:
                assigned = name
                break
        if assigned:
            print(f"  GPB{pin_num-8} (Pin {pin_num}): {assigned}")
        else:
            print(f"  GPB{pin_num-8} (Pin {pin_num}): <unassigned>")
    
    print("\nDisplay GPIO Pins:")
    print("-" * 40)
    print(f"  GPIO {DISPLAY_GPIO_DC}: D/C (Data/Command)")
    print(f"  GPIO {DISPLAY_GPIO_RST}: RST (Reset)")
    print(f"  SPI Port {DISPLAY_SPI_PORT}, Device {DISPLAY_SPI_DEVICE}")
    print("=" * 80)


__all__ = [
    # Submodules
    'mpd',
    'spotify',
    'bluetooth',
    'display',
    'buttons',
    'system',
    # Helper functions
    'get_button_pin_map',
    'get_config_dict',
    'print_config',
    'print_pin_map',
]
