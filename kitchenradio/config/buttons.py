"""
Button Controller Configuration
"""

# =============================================================================
# Button Controller Settings
# =============================================================================
USE_HARDWARE = True  # Use physical buttons (set False for software-only mode)
I2C_ADDRESS = 0x27  # I2C address of MCP23017 GPIO expander
DEBOUNCE_TIME = 0.02  # seconds - debounce time for button presses
LONG_PRESS_TIME = 3.0  # seconds - threshold for long press detection
VOLUME_STEP = 5  # Volume change per button press (0-100)

# =============================================================================
# MCP23017 Pin Assignments (0-15)
# Pins 0-7 are on Port A (GPA0-GPA7)
# Pins 8-15 are on Port B (GPB0-GPB7)
# =============================================================================

# Source buttons
PIN_SOURCE_MPD = 7           # MPD/Tuner button
PIN_SOURCE_SPOTIFY = 6       # Spotify/AUX button
PIN_SOURCE_BLUETOOTH = 5     # Bluetooth button

# Menu buttons
PIN_MENU_UP = 8              # Menu up button
PIN_MENU_DOWN = 9            # Menu down button

# Function buttons
PIN_SLEEP = 15               # Sleep timer button
PIN_REPEAT = 14              # Repeat mode button
PIN_SHUFFLE = 13             # Shuffle mode button
PIN_DISPLAY = 11             # Display mode button

# Transport buttons
PIN_TRANSPORT_PREVIOUS = 1   # Previous track button
PIN_TRANSPORT_PLAY_PAUSE = 3 # Play/Pause button
PIN_TRANSPORT_STOP = 4       # Stop button
PIN_TRANSPORT_NEXT = 2       # Next track button

# Volume buttons
PIN_VOLUME_DOWN = 10         # Volume down button
PIN_VOLUME_UP = 12           # Volume up button

# Power button
PIN_POWER = 0                # Power button


def get_pin_map() -> dict:
    """
    Get button pin mapping as a dictionary.
    
    Returns:
        Dictionary mapping button names to MCP23017 pin numbers
    """
    return {
        'source_mpd': PIN_SOURCE_MPD,
        'source_spotify': PIN_SOURCE_SPOTIFY,
        'source_bluetooth': PIN_SOURCE_BLUETOOTH,
        'menu_up': PIN_MENU_UP,
        'menu_down': PIN_MENU_DOWN,
        'sleep': PIN_SLEEP,
        'repeat': PIN_REPEAT,
        'shuffle': PIN_SHUFFLE,
        'display': PIN_DISPLAY,
        'transport_previous': PIN_TRANSPORT_PREVIOUS,
        'transport_play_pause': PIN_TRANSPORT_PLAY_PAUSE,
        'transport_stop': PIN_TRANSPORT_STOP,
        'transport_next': PIN_TRANSPORT_NEXT,
        'volume_down': PIN_VOLUME_DOWN,
        'volume_up': PIN_VOLUME_UP,
        'power': PIN_POWER,
    }
