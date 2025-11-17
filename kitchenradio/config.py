"""
KitchenRadio Configuration File

Central configuration for all KitchenRadio components.
Modify values here to customize behavior without changing code.
"""

# =============================================================================
# MPD (Music Player Daemon) Configuration
# =============================================================================
MPD_HOST = 'localhost'
MPD_PORT = 6600
MPD_PASSWORD = None
MPD_TIMEOUT = 10  # seconds
MPD_DEFAULT_VOLUME = 50  # 0-100

# =============================================================================
# Librespot (Spotify) Configuration
# =============================================================================
LIBRESPOT_HOST = 'localhost'
LIBRESPOT_PORT = 4370
LIBRESPOT_NAME = 'KitchenRadio'
LIBRESPOT_DEFAULT_VOLUME = 50  # 0-100

# =============================================================================
# Bluetooth Configuration
# =============================================================================
BLUETOOTH_DEVICE_NAME = 'KitchenRadio'
BLUETOOTH_PAIRING_TIMEOUT = 60  # seconds
BLUETOOTH_AUTO_RECONNECT = True
BLUETOOTH_DEFAULT_VOLUME = 50  # 0-100

# =============================================================================
# Display Configuration
# =============================================================================
DISPLAY_REFRESH_RATE = 80  # Hz - 80 Hz for ultra-smooth pixel scrolling
DISPLAY_WIDTH = 256  # pixels
DISPLAY_HEIGHT = 64  # pixels
DISPLAY_I2C_ADDRESS = 0x3C  # Default I2C address for SSD1322
DISPLAY_USE_HARDWARE = True  # Use actual hardware display (set False for emulation)

# SPI Display Pins (for SSD1322)
DISPLAY_GPIO_DC = 25        # GPIO pin for Data/Command (D/C) signal
DISPLAY_GPIO_RST = 24       # GPIO pin for Reset (RST) signal
DISPLAY_SPI_PORT = 0        # SPI port number
DISPLAY_SPI_DEVICE = 0      # SPI device/chip enable number
DISPLAY_SPI_BUS_SPEED = 4_000_000  # SPI bus speed in Hz (4 MHz default, max 10 MHz)
DISPLAY_ROTATE = 0          # Display rotation: 0=0°, 1=90°, 2=180°, 3=270°

# Display Overlay Timeouts
DISPLAY_VOLUME_OVERLAY_TIMEOUT = 3.0  # seconds
DISPLAY_MENU_OVERLAY_TIMEOUT = 3.0  # seconds
DISPLAY_NOTIFICATION_OVERLAY_TIMEOUT = 2.0  # seconds

# Scrolling Configuration
DISPLAY_SCROLL_STEP = 2  # pixels per update (higher = faster scrolling)
DISPLAY_SCROLL_PAUSE_DURATION = 2.0  # seconds - pause before scrolling starts
DISPLAY_SCROLL_PAUSE_AT_END = 2.0  # seconds - pause when reaching end before looping

# Volume Change Handling
DISPLAY_VOLUME_CHANGE_IGNORE_DURATION = 1.0  # seconds - ignore status updates after volume change

# =============================================================================
# Button Controller Configuration
# =============================================================================
BUTTON_USE_HARDWARE = True  # Use physical buttons (set False for software-only mode)
BUTTON_I2C_ADDRESS = 0x27  # I2C address of MCP23017 GPIO expander
BUTTON_DEBOUNCE_TIME = 0.02  # seconds - debounce time for button presses
BUTTON_LONG_PRESS_TIME = 3.0  # seconds - threshold for long press detection
BUTTON_VOLUME_STEP = 5  # Volume change per button press (0-100)

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

# =============================================================================
# Monitor Configuration
# =============================================================================
# Expected Value Timeout (for instant UI feedback)
MONITOR_EXPECTED_VALUE_TIMEOUT = 2.0  # seconds - how long to use expected values before reverting to actual

# MPD Monitor
MPD_MONITOR_POLL_INTERVAL = 1.0  # seconds

# Librespot Monitor
LIBRESPOT_MONITOR_POLL_INTERVAL = 0.5  # seconds

# Bluetooth Monitor
BLUETOOTH_MONITOR_POLL_INTERVAL = 1.0  # seconds
BLUETOOTH_AVRCP_RETRY_ATTEMPTS = 10
BLUETOOTH_AVRCP_RETRY_DELAY = 1.0  # seconds

# =============================================================================
# System Configuration
# =============================================================================
DEFAULT_SOURCE = 'mpd'  # Default audio source on startup: 'mpd', 'librespot', 'bluetooth', or 'none'
AUTO_START_PLAYBACK = False  # Automatically start playback when switching sources
POWER_ON_AT_STARTUP = True  # Power on radio when daemon starts

# Logging
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# =============================================================================
# Hardware Configuration
# =============================================================================
# I2C Bus Selection
I2C_BUS = 1  # I2C bus number (usually 1 on Raspberry Pi)

# GPIO Configuration (if using GPIO directly instead of MCP23017)
GPIO_MODE = 'BCM'  # BCM or BOARD pin numbering

# =============================================================================
# Network Configuration
# =============================================================================
# Web API (if implemented)
API_PORT = 5000
API_HOST = '0.0.0.0'
API_ENABLE = False

# =============================================================================
# Advanced Configuration
# =============================================================================
# Threading
THREAD_JOIN_TIMEOUT = 5.0  # seconds - max time to wait for threads to stop

# Reconnection
AUTO_RECONNECT_DELAY = 5.0  # seconds - delay before attempting reconnection
MAX_RECONNECT_ATTEMPTS = 10  # 0 = unlimited

# Audio
AUDIO_FADE_DURATION = 0.5  # seconds - crossfade duration when switching sources

# =============================================================================
# Feature Flags
# =============================================================================
ENABLE_BLUETOOTH = True
ENABLE_SPOTIFY = True
ENABLE_MPD = True
ENABLE_WEB_API = False
ENABLE_REMOTE_CONTROL = False

# =============================================================================
# Helper Functions
# =============================================================================

def get_button_pin_map() -> dict:
    """
    Get button pin mapping as a dictionary.
    
    Returns:
        Dictionary mapping button names to MCP23017 pin numbers
    """
    return {
        'source_mpd': BUTTON_PIN_SOURCE_MPD,
        'source_spotify': BUTTON_PIN_SOURCE_SPOTIFY,
        'source_bluetooth': BUTTON_PIN_SOURCE_BLUETOOTH,
        'menu_up': BUTTON_PIN_MENU_UP,
        'menu_down': BUTTON_PIN_MENU_DOWN,
        'sleep': BUTTON_PIN_SLEEP,
        'repeat': BUTTON_PIN_REPEAT,
        'shuffle': BUTTON_PIN_SHUFFLE,
        'display': BUTTON_PIN_DISPLAY,
        'transport_previous': BUTTON_PIN_TRANSPORT_PREVIOUS,
        'transport_play_pause': BUTTON_PIN_TRANSPORT_PLAY_PAUSE,
        'transport_stop': BUTTON_PIN_TRANSPORT_STOP,
        'transport_next': BUTTON_PIN_TRANSPORT_NEXT,
        'volume_down': BUTTON_PIN_VOLUME_DOWN,
        'volume_up': BUTTON_PIN_VOLUME_UP,
        'power': BUTTON_PIN_POWER,
    }


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


if __name__ == "__main__":
    # Print configuration when run directly
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--pins':
        print_pin_map()
    elif len(sys.argv) > 1 and sys.argv[1] == '--all':
        print_config()
        print()
        print_pin_map()
    else:
        print_config()
