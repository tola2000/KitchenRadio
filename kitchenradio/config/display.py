"""
Display Hardware Configuration
"""

# =============================================================================
# Display Hardware Settings
# =============================================================================
REFRESH_RATE = 80  # Hz - 80 Hz for ultra-smooth pixel scrolling
WIDTH = 256  # pixels
HEIGHT = 64  # pixels
I2C_ADDRESS = 0x3C  # Default I2C address for SSD1322
USE_HARDWARE = True  # Use actual hardware display (set False for emulation)

# =============================================================================
# SPI Display Pins (for SSD1322)
# =============================================================================
GPIO_DC = 25        # GPIO pin for Data/Command (D/C) signal
GPIO_RST = 24       # GPIO pin for Reset (RST) signal
SPI_PORT = 0        # SPI port number
SPI_DEVICE = 0      # SPI device/chip enable number
SPI_BUS_SPEED = 4_000_000  # SPI bus speed in Hz (4 MHz default, max 10 MHz)
ROTATE = 2          # Display rotation: 0=0°, 1=90°, 2=180°, 3=270° (2=upside down fix)

# =============================================================================
# Display Overlay Timeouts
# =============================================================================
VOLUME_OVERLAY_TIMEOUT = 3.0  # seconds
MENU_OVERLAY_TIMEOUT = 3.0  # seconds
NOTIFICATION_OVERLAY_TIMEOUT = 2.0  # seconds

# =============================================================================
# Scrolling Configuration
# =============================================================================
SCROLL_STEP = 2  # pixels per update (higher = faster scrolling)
SCROLL_PAUSE_DURATION = 2.0  # seconds - pause before scrolling starts
SCROLL_PAUSE_AT_END = 2.0  # seconds - pause when reaching end before looping

# =============================================================================
# Volume Change Handling
# =============================================================================
VOLUME_CHANGE_IGNORE_DURATION = 1.0  # seconds - ignore status updates after volume change
