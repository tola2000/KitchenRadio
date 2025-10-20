"""
Button Controller for KitchenRadio Physical Interface

Provides button control interface without GPIO dependencies.
Uses display-based emulation for button interactions.
"""

import logging
import threading
import time
from typing import Dict, Callable, Optional, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..kitchen_radio import KitchenRadio, BackendType

logger = logging.getLogger(__name__)


class ButtonType(Enum):
    """Types of buttons on the physical radio"""
    # Source buttons (top row)
    SOURCE_MPD = "source_mpd"
    SOURCE_SPOTIFY = "source_spotify"
    
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
    
    # Power button (bottom center)
    POWER = "power"


class ButtonEvent:
    """Represents a button event"""
    def __init__(self, button_type: ButtonType, event_type: str, timestamp: float = None):
        self.button_type = button_type
        self.event_type = event_type  # 'press', 'release', 'hold'
        self.timestamp = timestamp or time.time()


class ButtonController:
    """
    Button controller using display-based interface instead of GPIO.
    Provides programmatic button control without hardware dependencies.
    
    Features:
    - Direct KitchenRadio integration
    - Software-based button simulation
    - Long press detection for volume controls
    - No hardware dependencies
    """
    
    def __init__(self, 
                 kitchen_radio: 'KitchenRadio',
                 debounce_time: float = 0.05,
                 long_press_time: float = 1.0):
        """
        Initialize button controller with direct KitchenRadio integration.
        
        Args:
            kitchen_radio: KitchenRadio instance to control
            debounce_time: Button debounce time in seconds (for compatibility)
            long_press_time: Time threshold for long press detection
        """
        # Store KitchenRadio reference
        self.kitchen_radio = kitchen_radio
        
        # Timing configuration (kept for compatibility)
        self.debounce_time = debounce_time
        self.long_press_time = long_press_time
        
        # Button state tracking
        self.button_states: Dict[ButtonType, Dict[str, Any]] = {}
        self.press_threads: Dict[ButtonType, threading.Thread] = {}
        
        # Initialize button states
        for button_type in ButtonType:
            self.button_states[button_type] = {
                'pressed': False,
                'last_event_time': 0,
                'press_start_time': 0,
                'long_press_fired': False
            }
        
        # Button action mapping - direct KitchenRadio calls
        self.button_actions = {
            # Source buttons
            ButtonType.SOURCE_MPD: self._select_mpd,
            ButtonType.SOURCE_SPOTIFY: self._select_spotify,
            
            # Transport buttons
            ButtonType.TRANSPORT_PLAY_PAUSE: self._play_pause,
            ButtonType.TRANSPORT_STOP: self._stop,
            ButtonType.TRANSPORT_NEXT: self._next,
            ButtonType.TRANSPORT_PREVIOUS: self._previous,
            
            # Volume buttons
            ButtonType.VOLUME_UP: self._volume_up,
            ButtonType.VOLUME_DOWN: self._volume_down,
            
            # Menu buttons (basic implementation)
            ButtonType.MENU_UP: self._menu_up,
            ButtonType.MENU_DOWN: self._menu_down,
            ButtonType.MENU_OK: self._menu_ok,
            ButtonType.MENU_EXIT: self._menu_exit,
            ButtonType.MENU_TOGGLE: self._menu_toggle,
            ButtonType.MENU_SET: self._menu_set,
            
            # Power button
            ButtonType.POWER: self._power,
        }
        
        self.running = False
        self.initialized = False
        
    def initialize(self) -> bool:
        """
        Initialize button controller (display-based, no GPIO needed).
        
        Returns:
            True if initialization successful (always succeeds)
        """
        try:
            self.initialized = True
            self.running = True
            logger.info(f"ButtonController initialized in display mode with {len(self.button_actions)} buttons")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize button controller: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources (no GPIO to clean up)"""
        self.running = False
        self.initialized = False
        logger.info("Button controller cleanup completed")
    
    def press_button(self, button_name: str) -> bool:
        """
        Programmatically press a button (for display-based control).
        
        Args:
            button_name: Name of the button to press
            
        Returns:
            True if button action was successful
        """
        try:
            # Find button type by name
            button_type = None
            for bt in ButtonType:
                if bt.value == button_name:
                    button_type = bt
                    break
            
            if not button_type:
                logger.warning(f"Unknown button: {button_name}")
                return False
            
            # Simulate button press timing
            current_time = time.time()
            button_state = self.button_states[button_type]
            
            # Debounce check
            if current_time - button_state['last_event_time'] < self.debounce_time:
                logger.debug(f"Button {button_name} debounced")
                return False
            
            button_state['last_event_time'] = current_time
            
            logger.info(f"Button pressed: {button_type.value}")
            
            # Execute button action
            return self._execute_button_action(button_type)
            
        except Exception as e:
            logger.error(f"Error pressing button {button_name}: {e}")
            return False
            self._cancel_long_press_detection(button_type)
            
            logger.debug(f"Button released: {button_type.value}")
    
    def _execute_button_action(self, button_type: ButtonType) -> bool:
        """
        Execute the KitchenRadio action for a button.
        
        Args:
            button_type: The button that was pressed
            
        Returns:
            True if action was successful
        """
        if button_type not in self.button_actions:
            logger.warning(f"No action defined for button: {button_type.value}")
            return False
        
        try:
            action_method = self.button_actions[button_type]
            result = action_method()
            logger.debug(f"Button action {button_type.value} result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error executing action for button {button_type.value}: {e}")
            return False
    
    def _start_long_press_detection(self, button_type: ButtonType):
        """Start long press detection for volume buttons"""
        # Cancel any existing thread
        self._cancel_long_press_detection(button_type)
        
        def long_press_checker():
            while self.running and self.button_states[button_type]['pressed']:
                time.sleep(0.3)  # Repeat every 300ms during long press
                if self.running and self.button_states[button_type]['pressed']:
                    self._execute_button_action(button_type)
        
        thread = threading.Thread(target=long_press_checker, daemon=True)
        self.press_threads[button_type] = thread
        thread.start()
    
    def _cancel_long_press_detection(self, button_type: ButtonType):
        """Cancel long press detection for a button"""
        if button_type in self.press_threads:
            del self.press_threads[button_type]
    
    # KitchenRadio Action Methods - Direct calls to KitchenRadio
    
    def _select_mpd(self) -> bool:
        """Switch to MPD source"""
        from ..kitchen_radio import BackendType
        logger.info("Switching to MPD source")
        return self.kitchen_radio.switch_source(BackendType.MPD)
    
    def _select_spotify(self) -> bool:
        """Switch to Spotify (librespot) source"""
        from ..kitchen_radio import BackendType
        logger.info("Switching to Spotify source")
        return self.kitchen_radio.switch_source(BackendType.LIBRESPOT)
    
    def _play_pause(self) -> bool:
        """Toggle play/pause"""
        logger.info("Toggle play/pause")
        return self.kitchen_radio.play_pause()
    
    def _stop(self) -> bool:
        """Stop playback"""
        logger.info("Stop playback")
        return self.kitchen_radio.stop()
    
    def _next(self) -> bool:
        """Next track"""
        logger.info("Next track")
        return self.kitchen_radio.next()
    
    def _previous(self) -> bool:
        """Previous track"""
        logger.info("Previous track")
        return self.kitchen_radio.previous()
    
    def _volume_up(self) -> bool:
        """Increase volume"""
        logger.debug("Volume up")
        return self.kitchen_radio.volume_up(step=5)
    
    def _volume_down(self) -> bool:
        """Decrease volume"""
        logger.debug("Volume down")
        return self.kitchen_radio.volume_down(step=5)
    
    def _menu_up(self) -> bool:
        """Menu up navigation - placeholder"""
        logger.info("Menu up - not implemented yet")
        return True
    
    def _menu_down(self) -> bool:
        """Menu down navigation - placeholder"""
        logger.info("Menu down - not implemented yet")
        return True
    
    def _menu_ok(self) -> bool:
        """Menu OK/select - placeholder"""
        logger.info("Menu OK - not implemented yet")
        return True
    
    def _menu_exit(self) -> bool:
        """Menu exit/back - placeholder"""
        logger.info("Menu exit - not implemented yet")
        return True
    
    def _menu_toggle(self) -> bool:
        """Toggle menu display - placeholder"""
        logger.info("Menu toggle - not implemented yet")
        return True
    
    def _menu_set(self) -> bool:
        """Menu set/confirm - placeholder"""
        logger.info("Menu set - not implemented yet")
        return True
    
    def _power(self) -> bool:
        """Power button - stop all playback"""
        logger.info("Power button pressed - stopping all playback")
        return self.kitchen_radio.stop()
    
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
    from ..kitchen_radio import KitchenRadio
    
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Create KitchenRadio instance
    kitchen_radio = KitchenRadio()
    
    if not kitchen_radio.start():
        print("Failed to start KitchenRadio")
        sys.exit(1)
    
    # Create and initialize controller
    controller = ButtonController(kitchen_radio)
    
    if controller.initialize():
        print("ButtonController initialized successfully")
        print("Press buttons to test (Ctrl+C to exit)")
        
        try:
            # Keep running
            while True:
                time.sleep(1)
                    
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            controller.cleanup()
            kitchen_radio.stop()
    else:
        print("Failed to initialize ButtonController")
        kitchen_radio.stop()
        sys.exit(1)
