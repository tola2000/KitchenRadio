"""
Output Configuration for KitchenRadio

GPIO output pin configuration for controlling external devices like amplifier relays.
"""

# ============================================================================
# Amplifier Relay Configuration
# ============================================================================

# GPIO pin for amplifier relay control (BCM numbering)
# GPIO 26 = Physical pin 37 on the Raspberry Pi header
AMPLIFIER_PIN = 26

# Relay activation logic
# True = relay activates on HIGH signal
# False = relay activates on LOW signal (inverted/active-low)
AMPLIFIER_ACTIVE_HIGH = True  # Changed back to True - relay activates on HIGH signal

# Delays for amplifier power control (in seconds)
# Power-on delay: wait before turning on amplifier after system power-on
# Useful to prevent speaker pop or give system time to stabilize
AMPLIFIER_POWER_ON_DELAY = 0.0

# Power-off delay: wait before turning off amplifier after system power-off
# Useful to let audio complete before cutting power
AMPLIFIER_POWER_OFF_DELAY = 0.0

# Enable hardware control
# Set to False to run in simulation mode without accessing GPIO
OUTPUT_USE_HARDWARE = True
