"""
System-Wide Configuration
"""

# =============================================================================
# System Behavior
# =============================================================================
DEFAULT_SOURCE = 'mpd'  # Default audio source on startup: 'mpd', 'librespot', 'bluetooth', or 'none'
AUTO_START_PLAYBACK = False  # Automatically start playback when switching sources
POWER_ON_AT_STARTUP = True  # Power on radio when daemon starts

# =============================================================================
# Logging
# =============================================================================
LOG_LEVEL = 'DEBUG'  # DEBUG, INFO, WARNING, ERROR, CRITICAL

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
# Monitor Configuration
# =============================================================================
# Expected Value Timeout (for instant UI feedback)
EXPECTED_VALUE_TIMEOUT = 2.0  # seconds - how long to use expected values before reverting to actual

# =============================================================================
# Feature Flags
# =============================================================================
ENABLE_BLUETOOTH = True
ENABLE_SPOTIFY = False
ENABLE_MPD = False
ENABLE_WEB_API = False
ENABLE_REMOTE_CONTROL = False
