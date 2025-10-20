"""
Button Controller for KitchenRadio Physical Interface

Controls physical buttons connected to Raspberry Pi GPIO pins.
"""

import logging
import threading
import time
from typing import Dict, Callable, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logger.warning("RPi.GPIO not available - running in simulation mode")


class ButtonType(Enum):
    """Types of buttons on the physical radio"""
    # Source buttons (top row)
    SOURCE_MPD = "source_mpd"
    SOURCE_SPOTIFY = "source_spotify" 
    SOURCE_OFF = "source_off"
    
    # Menu buttons (around display)
    MENU_UP = "menu_up"
    MENU_DOWN = "menu_down"
    MENU_TOGGLE = "menu_toggle"
    MENU_SET = "menu_set"
    MENU_OK = "menu_ok"
    MENU_EXIT = "menu_exit"
    
    # Transport buttons (middle)
    TRANSPORT_PREVIOUS = "transport_previous"
    TRANSPORT_PLAY_PAUSE = "transport_play_pause"
    TRANSPORT_STOP = "transport_stop"
    TRANSPORT_NEXT = "transport_next"
    
    # Volume buttons (bottom)
    VOLUME_DOWN = "volume_down"
    VOLUME_UP = "volume_up"


class ButtonEvent:
    """Represents a button event"""
    def __init__(self, button_type: ButtonType, event_type: str, timestamp: float = None):
        self.button_type = button_type
        self.event_type = event_type  # 'press', 'release', 'hold', 'double_press'
        self.timestamp = timestamp or time.time()


class ButtonController:
    """
    Controls physical buttons connected to Raspberry Pi GPIO pins.
    
    Features:
    - Debouncing
    - Long press detection
    - Double press detection
    - Pull-up resistor configuration
    - Event callbacks
    """
    
    # Default GPIO pin mapping (BCM numbering)
    DEFAULT_PIN_MAPPING = {
        # Source buttons (top row)
        ButtonType.SOURCE_MPD: 2,
        ButtonType.SOURCE_SPOTIFY: 3,
        ButtonType.SOURCE_OFF: 4,
        
        # Menu buttons (around display)
        ButtonType.MENU_UP: 5,
        ButtonType.MENU_DOWN: 6,
        ButtonType.MENU_TOGGLE: 7,
        ButtonType.MENU_SET: 8,
        ButtonType.MENU_OK: 9,
        ButtonType.MENU_EXIT: 10,
        
        # Transport buttons (middle)
        ButtonType.TRANSPORT_PREVIOUS: 11,
        ButtonType.TRANSPORT_PLAY_PAUSE: 12,
        ButtonType.TRANSPORT_STOP: 13,
        ButtonType.TRANSPORT_NEXT: 14,
        
        # Volume buttons (bottom)
        ButtonType.VOLUME_DOWN: 15,
        ButtonType.VOLUME_UP: 16,
    }
    
    def __init__(self, 
                 pin_mapping: Dict[ButtonType, int] = None,
                 debounce_time: float = 0.05,
                 long_press_time: float = 1.0,
                 double_press_time: float = 0.5):
        """
        Initialize button controller.
        
        Args:
            pin_mapping: Custom GPIO pin mapping (uses default if None)
            debounce_time: Button debounce time in seconds
            long_press_time: Time threshold for long press detection
            double_press_time: Time window for double press detection
        """
        self.pin_mapping = pin_mapping or self.DEFAULT_PIN_MAPPING
        self.debounce_time = debounce_time
        self.long_press_time = long_press_time
        self.double_press_time = double_press_time
        
        # Event callbacks
        self.callbacks: Dict[ButtonType, Callable[[ButtonEvent], None]] = {}
        self.global_callback: Optional[Callable[[ButtonEvent], None]] = None
        
        # Button state tracking
        self.button_states: Dict[ButtonType, Dict[str, Any]] = {}
        self.last_press_times: Dict[ButtonType, float] = {}
        self.press_threads: Dict[ButtonType, threading.Thread] = {}
        
        # Initialize button states
        for button_type in ButtonType:
            self.button_states[button_type] = {
                'pressed': False,
                'last_event_time': 0,
                'press_start_time': 0,
                'long_press_fired': False
            }
            self.last_press_times[button_type] = 0
        
        self.running = False
        self.gpio_initialized = False
        
    def initialize(self) -> bool:
        """
        Initialize GPIO and setup button pins.
        
        Returns:
            True if initialization successful
        """
        if not GPIO_AVAILABLE:
            logger.warning("GPIO not available - running in simulation mode")
            self.running = True
            return True
        
        try:
            # Set GPIO mode to BCM numbering
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup each button pin
            for button_type, pin in self.pin_mapping.items():
                # Configure as input with pull-up resistor
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                
                # Add event detection for both rising and falling edges
                GPIO.add_event_detect(
                    pin, 
                    GPIO.BOTH, 
                    callback=lambda channel, bt=button_type: self._gpio_callback(bt, channel),
                    bouncetime=int(self.debounce_time * 1000)
                )
                
                logger.debug(f"Setup button {button_type.value} on GPIO pin {pin}")
            
            self.gpio_initialized = True
            self.running = True
            logger.info(f"ButtonController initialized with {len(self.pin_mapping)} buttons")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize GPIO: {e}")
            return False
    
    def cleanup(self):
        """Clean up GPIO resources"""
        self.running = False
        
        if GPIO_AVAILABLE and self.gpio_initialized:
            try:
                GPIO.cleanup()
                logger.info("GPIO cleanup completed")
            except Exception as e:
                logger.warning(f"Error during GPIO cleanup: {e}")
    
    def set_button_callback(self, button_type: ButtonType, callback: Callable[[ButtonEvent], None]):
        """
        Set callback for specific button.
        
        Args:
            button_type: Type of button
            callback: Function to call when button event occurs
        """
        self.callbacks[button_type] = callback
        logger.debug(f"Set callback for button {button_type.value}")
    
    def set_global_callback(self, callback: Callable[[ButtonEvent], None]):
        """
        Set global callback for all button events.
        
        Args:
            callback: Function to call for any button event
        """
        self.global_callback = callback
        logger.debug("Set global button callback")
    
    def simulate_button_press(self, button_type: ButtonType, event_type: str = 'press'):
        """
        Simulate a button press (for testing without hardware).
        
        Args:
            button_type: Type of button to simulate
            event_type: Type of event ('press', 'release', 'hold', 'double_press')
        """
        if not self.running:
            logger.warning("ButtonController not running - cannot simulate button press")
            return
        
        event = ButtonEvent(button_type, event_type)
        self._fire_event(event)
        logger.debug(f"Simulated {event_type} event for {button_type.value}")
    
    def _gpio_callback(self, button_type: ButtonType, channel: int):
        """Handle GPIO interrupt callback"""
        if not self.running:
            return
        
        current_time = time.time()
        pin = self.pin_mapping[button_type]
        button_state = self.button_states[button_type]
        
        # Read current pin state (LOW = pressed with pull-up)
        pin_pressed = GPIO.input(pin) == GPIO.LOW
        
        # Debounce check
        if current_time - button_state['last_event_time'] < self.debounce_time:
            return
        
        button_state['last_event_time'] = current_time
        
        if pin_pressed and not button_state['pressed']:
            # Button press detected
            button_state['pressed'] = True
            button_state['press_start_time'] = current_time
            button_state['long_press_fired'] = False
            
            # Check for double press
            if current_time - self.last_press_times[button_type] < self.double_press_time:
                self._fire_event(ButtonEvent(button_type, 'double_press', current_time))
            else:
                self._fire_event(ButtonEvent(button_type, 'press', current_time))
            
            # Start long press detection thread
            self._start_long_press_detection(button_type)
            
        elif not pin_pressed and button_state['pressed']:
            # Button release detected
            button_state['pressed'] = False
            self.last_press_times[button_type] = current_time
            
            # Cancel long press detection
            self._cancel_long_press_detection(button_type)
            
            # Fire release event if long press wasn't fired
            if not button_state['long_press_fired']:
                self._fire_event(ButtonEvent(button_type, 'release', current_time))
    
    def _start_long_press_detection(self, button_type: ButtonType):
        """Start long press detection for a button"""
        # Cancel any existing thread
        self._cancel_long_press_detection(button_type)
        
        def long_press_checker():
            time.sleep(self.long_press_time)
            button_state = self.button_states[button_type]
            
            if button_state['pressed'] and not button_state['long_press_fired']:
                button_state['long_press_fired'] = True
                self._fire_event(ButtonEvent(button_type, 'hold', time.time()))
        
        thread = threading.Thread(target=long_press_checker, daemon=True)
        self.press_threads[button_type] = thread
        thread.start()
    
    def _cancel_long_press_detection(self, button_type: ButtonType):
        """Cancel long press detection for a button"""
        if button_type in self.press_threads:
            # Thread will exit naturally when it checks the pressed state
            del self.press_threads[button_type]
    
    def _fire_event(self, event: ButtonEvent):
        """Fire button event to registered callbacks"""
        try:
            # Call specific button callback
            if event.button_type in self.callbacks:
                self.callbacks[event.button_type](event)
            
            # Call global callback
            if self.global_callback:
                self.global_callback(event)
                
        except Exception as e:
            logger.error(f"Error in button callback: {e}")
    
    def get_button_state(self, button_type: ButtonType) -> bool:
        """
        Get current state of a button.
        
        Args:
            button_type: Type of button to check
            
        Returns:
            True if button is currently pressed
        """
        return self.button_states[button_type]['pressed']
    
    def get_all_button_states(self) -> Dict[ButtonType, bool]:
        """
        Get current state of all buttons.
        
        Returns:
            Dictionary mapping button types to their pressed state
        """
        return {bt: state['pressed'] for bt, state in self.button_states.items()}


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)
    
    def button_event_handler(event: ButtonEvent):
        print(f"Button {event.button_type.value}: {event.event_type} at {event.timestamp:.3f}")
    
    # Create and initialize controller
    controller = ButtonController()
    controller.set_global_callback(button_event_handler)
    
    if controller.initialize():
        print("ButtonController initialized successfully")
        print("Press buttons to test (Ctrl+C to exit)")
        
        try:
            # Keep running
            while True:
                time.sleep(0.1)
                
                # Simulate some button presses if GPIO not available
                if not GPIO_AVAILABLE:
                    time.sleep(2)
                    controller.simulate_button_press(ButtonType.SOURCE_MPD, 'press')
                    time.sleep(0.1)
                    controller.simulate_button_press(ButtonType.SOURCE_MPD, 'release')
                    
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            controller.cleanup()
    else:
        print("Failed to initialize ButtonController")
        sys.exit(1)
