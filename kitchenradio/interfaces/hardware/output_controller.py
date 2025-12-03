"""
Output Controller for KitchenRadio

Controls GPIO output pins to drive external devi            logger.debug(f"GPIO module available: {GPIO is not None}")
            try:
                if GPIO is not None:
                    # Using RPi.GPIO
                    logger.debug("Using RPi.GPIO library")
                    
                    # Check if GPIO mode is already set, if not set it
                    try:
                        mode = GPIO.getmode()
                        if mode is None:
                            logger.debug("GPIO mode not set, setting to BCM")
                            GPIO.setmode(GPIO.BCM)
                        elif mode == GPIO.BCM:
                            logger.debug("GPIO already in BCM mode")
                        else:
                            logger.warning(f"GPIO in different mode ({mode}), setting to BCM")
                            GPIO.setmode(GPIO.BCM)
                    except Exception as e:
                        logger.debug(f"Error checking/setting GPIO mode: {e}")
                        GPIO.setmode(GPIO.BCM)
                    
                    # Setup pin as output with pull-down to prevent floating
                    # Note: Pull-down is important for relays to ensure clean LOW state
                    GPIO.setup(self.amplifier_pin, GPIO.OUT, initial=GPIO.LOW if self.active_high else GPIO.HIGH, pull_up_down=GPIO.PUD_DOWN)
                    
                    # Initialize to OFF state
                    # For active_high=True: OFF = LOW, for active_high=False: OFF = HIGH
                    initial_state = GPIO.LOW if self.active_high else GPIO.HIGH
                    logger.debug(f"Setting initial state: {'LOW' if initial_state == GPIO.LOW else 'HIGH'}")
                    GPIO.output(self.amplifier_pin, initial_state)
                    
                    # Verify the output
                    actual_state = GPIO.input(self.amplifier_pin)
                    logger.debug(f"Verified pin state: {'HIGH' if actual_state else 'LOW'}")
                    
                    logger.info(f"[OK] GPIO pin {self.amplifier_pin} initialized to OFF (RPi.GPIO)")ifier relays.
Listens to power events from SourceController and enables/disables outputs accordingly.
"""

import logging
import time
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from kitchenradio.sources.source_controller import SourceController

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Hardware configuration flag
try:
    import RPi.GPIO as GPIO
    HARDWARE_AVAILABLE = True
    logger.info("[OK] RPi.GPIO loaded successfully")
except ImportError:
    try:
        # Alternative: Use gpiozero as fallback
        from gpiozero import OutputDevice
        HARDWARE_AVAILABLE = True
        logger.info("[OK] gpiozero loaded successfully")
        GPIO = None  # Mark that we're using gpiozero
    except ImportError as e:
        HARDWARE_AVAILABLE = False
        GPIO = None
        logger.info(f"[X] GPIO libraries not available: {e}")
        logger.info("   To enable GPIO output: pip install RPi.GPIO or pip install gpiozero")


class OutputController:
    """
    Controls GPIO output pins for external devices.
    
    Primary use case: Control amplifier relay based on power state.
    """
    
    def __init__(self,
                 source_controller: 'SourceController',
                 amplifier_pin: int = 26,
                 use_hardware: bool = True,
                 active_high: bool = True,
                 power_on_delay: float = 0.0,
                 power_off_delay: float = 0.0):
        """
        Initialize Output Controller.
        
        Args:
            source_controller: SourceController instance to monitor
            amplifier_pin: GPIO pin number (BCM numbering) for amplifier relay
            use_hardware: Enable hardware GPIO control
            active_high: True if relay is active-high, False for active-low
            power_on_delay: Delay in seconds before turning on amplifier (default: 0.0)
            power_off_delay: Delay in seconds before turning off amplifier (default: 0.0)
        """
        self.source_controller = source_controller
        self.amplifier_pin = amplifier_pin
        self.use_hardware = use_hardware and HARDWARE_AVAILABLE
        self.active_high = active_high
        self.power_on_delay = power_on_delay
        self.power_off_delay = power_off_delay
        
        # State tracking
        self.amplifier_enabled = False
        self.initialized = False
        
        # GPIO device (for gpiozero)
        self.gpio_device = None
        
        logger.info(f"OutputController created - Pin: {amplifier_pin}, Hardware: {self.use_hardware}, Active: {'HIGH' if active_high else 'LOW'}")
    
    def initialize(self) -> bool:
        """
        Initialize GPIO and register event callbacks.
        
        Returns:
            True if initialization succeeded
        """
        if self.initialized:
            logger.warning("OutputController already initialized")
            return True
        
        # Setup GPIO hardware
        if self.use_hardware:
            logger.info(f"Attempting to initialize GPIO hardware on pin {self.amplifier_pin}...")
            logger.debug(f"GPIO module available: {GPIO is not None}")
            try:
                if GPIO is not None:
                    # Using RPi.GPIO
                    logger.debug("Using RPi.GPIO library")
                    GPIO.setmode(GPIO.BCM)
                    GPIO.setup(self.amplifier_pin, GPIO.OUT)
                    # Initialize to OFF state
                    # For active_high=True: OFF = LOW, for active_high=False: OFF = HIGH
                    initial_state = GPIO.LOW if self.active_high else GPIO.HIGH
                    logger.debug(f"Setting initial state: {'LOW' if initial_state == GPIO.LOW else 'HIGH'}")
                    GPIO.output(self.amplifier_pin, initial_state)
                    logger.info(f"[OK] GPIO pin {self.amplifier_pin} initialized to OFF (RPi.GPIO)")
                else:
                    # Using gpiozero
                    logger.debug("Using gpiozero library")
                    from gpiozero import OutputDevice
                    self.gpio_device = OutputDevice(
                        self.amplifier_pin,
                        active_high=self.active_high,
                        initial_value=False
                    )
                    logger.info(f"[OK] GPIO pin {self.amplifier_pin} initialized to OFF (gpiozero)")
                    
            except Exception as e:
                logger.error(f"Failed to initialize GPIO: {e}", exc_info=True)
                logger.warning("Falling back to simulation mode")
                self.use_hardware = False
                # Don't return False - continue in simulation mode
                # return False
        else:
            logger.info("[X] Hardware GPIO disabled - running in simulation mode")
        
        # Subscribe to power events from SourceController
        try:
            # Register callback for 'client_changed' events
            # The callback will receive event='power_changed' and powered_on=True/False
            self.source_controller.add_callback('client_changed', self._on_power_changed)
            logger.info("[OK] Subscribed to client_changed events (for power_changed)")
        except Exception as e:
            logger.error(f"Failed to subscribe to power events: {e}")
            return False
        
        self.initialized = True
        logger.info("[OK] OutputController initialized")
        
        # Sync initial state with current power state
        if self.source_controller.powered_on:
            logger.info("System already powered on - enabling amplifier")
            self._set_amplifier_state(True)
        
        return True
    
    def cleanup(self):
        """Clean up GPIO resources."""
        logger.info("Cleaning up OutputController...")
        
        # Turn off amplifier before cleanup
        if self.amplifier_enabled:
            self._set_amplifier_state(False)
        
        # Release GPIO resources
        if self.use_hardware:
            try:
                if GPIO is not None:
                    GPIO.cleanup(self.amplifier_pin)
                    logger.info(f"[OK] GPIO pin {self.amplifier_pin} cleaned up (RPi.GPIO)")
                elif self.gpio_device is not None:
                    self.gpio_device.close()
                    logger.info(f"[OK] GPIO pin {self.amplifier_pin} cleaned up (gpiozero)")
            except Exception as e:
                logger.error(f"Error during GPIO cleanup: {e}")
        
        self.initialized = False
        logger.info("[OK] OutputController cleanup complete")
    
    def _on_power_changed(self, event: str = None, powered_on: bool = None, **kwargs):
        """
        Callback for power state changes from SourceController.
        
        Args:
            event: Event name (should be 'power_changed')
            powered_on: True if system powered on, False if powered off
        """
        # Only respond to power_changed events
        if event != 'power_changed':
            return
        
        if powered_on is None:
            logger.warning("Received power_changed event without powered_on parameter")
            return
        
        logger.info(f"🔌 Power state changed: {'ON' if powered_on else 'OFF'}")
        
        if powered_on:
            # Apply power-on delay if configured
            if self.power_on_delay > 0:
                logger.info(f"Waiting {self.power_on_delay}s before enabling amplifier...")
                time.sleep(self.power_on_delay)
            self._set_amplifier_state(True)
        else:
            # Apply power-off delay if configured
            if self.power_off_delay > 0:
                logger.info(f"Waiting {self.power_off_delay}s before disabling amplifier...")
                time.sleep(self.power_off_delay)
            self._set_amplifier_state(False)
    
    def _set_amplifier_state(self, enable: bool):
        """
        Set amplifier relay state.
        
        Args:
            enable: True to enable amplifier, False to disable
        """
        if not self.initialized:
            logger.warning("Cannot set amplifier state - OutputController not initialized")
            return
        
        if enable == self.amplifier_enabled:
            logger.debug(f"Amplifier already {'enabled' if enable else 'disabled'}")
            return
        
        logger.info(f"🔊 {'Enabling' if enable else 'Disabling'} amplifier (pin {self.amplifier_pin})")
        logger.debug(f"Hardware mode: {self.use_hardware}, GPIO available: {GPIO is not None}, gpio_device: {self.gpio_device is not None}")
        
        if self.use_hardware:
            try:
                if GPIO is not None:
                    # Using RPi.GPIO
                    # INVERTED LOGIC: The relay control is inverted from the expected behavior
                    # When enable=True (amplifier should be ON), we set pin LOW
                    # When enable=False (amplifier should be OFF), we set pin HIGH
                    if enable:
                        pin_state = GPIO.LOW if self.active_high else GPIO.HIGH
                        GPIO.output(self.amplifier_pin, pin_state)
                        actual_state = GPIO.input(self.amplifier_pin)
                        logger.debug(f"🔌 GPIO pin {self.amplifier_pin} set to {'HIGH' if pin_state == GPIO.HIGH else 'LOW'} (verified: {'HIGH' if actual_state else 'LOW'})")
                    else:
                        pin_state = GPIO.HIGH if self.active_high else GPIO.LOW
                        GPIO.output(self.amplifier_pin, pin_state)
                        actual_state = GPIO.input(self.amplifier_pin)
                        logger.debug(f"🔌 GPIO pin {self.amplifier_pin} set to {'HIGH' if pin_state == GPIO.HIGH else 'LOW'} (verified: {'HIGH' if actual_state else 'LOW'})")
                elif self.gpio_device is not None:
                    # Using gpiozero
                    if enable:
                        self.gpio_device.on()
                        logger.debug(f"🔌 GPIO pin {self.amplifier_pin} set to {'HIGH' if self.active_high else 'LOW'} (gpiozero on)")
                    else:
                        self.gpio_device.off()
                        logger.debug(f"🔌 GPIO pin {self.amplifier_pin} set to {'HIGH' if not self.active_high else 'LOW'} (gpiozero off)")
                
                logger.info(f"[OK] Amplifier {'enabled' if enable else 'disabled'}")
            except Exception as e:
                logger.error(f"Failed to set GPIO state: {e}")
                return
        else:
            logger.info(f"[SIM] Amplifier would be {'enabled' if enable else 'disabled'} (hardware disabled)")
        
        self.amplifier_enabled = enable
    
    def get_amplifier_state(self) -> bool:
        """
        Get current amplifier state.
        
        Returns:
            True if amplifier is enabled, False otherwise
        """
        return self.amplifier_enabled
    
    def enable_amplifier(self):
        """Manually enable amplifier."""
        logger.info("Manual amplifier enable requested")
        self._set_amplifier_state(True)
    
    def disable_amplifier(self):
        """Manually disable amplifier."""
        logger.info("Manual amplifier disable requested")
        self._set_amplifier_state(False)
