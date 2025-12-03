"""
Output Controller for KitchenRadio

Controls GPIO output pins to drive external devices like amplifier relays.
Listens to power events from SourceController and enables/disables outputs accordingly.
"""

import logging
import time
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from kitchenradio.sources.source_controller import SourceController

logger = logging.getLogger(__name__)

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
            try:
                if GPIO is not None:
                    # Using RPi.GPIO
                    GPIO.setmode(GPIO.BCM)
                    GPIO.setup(self.amplifier_pin, GPIO.OUT)
                    # Initialize to OFF state
                    initial_state = GPIO.HIGH if self.active_high else GPIO.LOW
                    GPIO.output(self.amplifier_pin, GPIO.LOW if not self.active_high else GPIO.HIGH)
                    logger.info(f"[OK] GPIO pin {self.amplifier_pin} initialized (RPi.GPIO)")
                else:
                    # Using gpiozero
                    from gpiozero import OutputDevice
                    self.gpio_device = OutputDevice(
                        self.amplifier_pin,
                        active_high=self.active_high,
                        initial_value=False
                    )
                    logger.info(f"[OK] GPIO pin {self.amplifier_pin} initialized (gpiozero)")
                    
            except Exception as e:
                logger.error(f"Failed to initialize GPIO: {e}")
                self.use_hardware = False
                return False
        else:
            logger.info("[X] Hardware GPIO disabled - running in simulation mode")
        
        # Subscribe to power events from SourceController
        try:
            self.source_controller.subscribe_to_events(
                event_category='client_changed',
                event_name='power_changed',
                callback=self._on_power_changed
            )
            logger.info("[OK] Subscribed to power_changed events")
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
    
    def _on_power_changed(self, powered_on: bool, **kwargs):
        """
        Callback for power state changes.
        
        Args:
            powered_on: True if system powered on, False if powered off
        """
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
        
        if self.use_hardware:
            try:
                if GPIO is not None:
                    # Using RPi.GPIO
                    if enable:
                        GPIO.output(self.amplifier_pin, GPIO.HIGH if self.active_high else GPIO.LOW)
                    else:
                        GPIO.output(self.amplifier_pin, GPIO.LOW if self.active_high else GPIO.HIGH)
                elif self.gpio_device is not None:
                    # Using gpiozero
                    if enable:
                        self.gpio_device.on()
                    else:
                        self.gpio_device.off()
                
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
