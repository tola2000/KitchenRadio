"""
Bluetooth Audio Configuration
"""

# =============================================================================
# Bluetooth Device Settings
# =============================================================================
DEVICE_NAME = 'KitchenRadio'
PAIRING_TIMEOUT = 60  # seconds
AUTO_RECONNECT = True

# =============================================================================
# Bluetooth Audio Settings
# =============================================================================
DEFAULT_VOLUME = 50  # 0-100

# =============================================================================
# Bluetooth Monitor Settings
# =============================================================================
MONITOR_POLL_INTERVAL = 1.0  # seconds - how often to poll Bluetooth for status updates

# =============================================================================
# Bluetooth AVRCP Settings
# =============================================================================
AVRCP_RETRY_ATTEMPTS = 10
AVRCP_RETRY_DELAY = 1.0  # seconds
