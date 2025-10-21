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
                 long_press_time: float = 1.0,
                 display_controller = None):
        """
        Initialize button controller with direct KitchenRadio integration.
        
        Args:
            kitchen_radio: KitchenRadio instance to control
            debounce_time: Button debounce time in seconds (for compatibility)
            long_press_time: Time threshold for long press detection
            display_controller: Optional display controller for volume screen
        """
        # Store KitchenRadio reference
        self.kitchen_radio = kitchen_radio
        
        # Store display controller for volume screen
        self.display_controller = display_controller
        
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

            
            # Power button
            ButtonType.POWER: self._power,
        }
        
        self.running = False
        self.initialized = False
        
        # Menu timeout tracking
        self._menu_timeout_seconds = 3.0
        self._menu_last_activity_time = 0
        self._menu_timeout_thread = None
        self._current_menu_index = 0

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


    # KitchenRadio Action Methods - Direct calls to KitchenRadio
    
    def _select_mpd(self) -> bool:
        """Switch to MPD source"""
        from ..kitchen_radio import BackendType
        logger.info("Switching to MPD source")
        return self.kitchen_radio.set_source(BackendType.MPD)
    
    def _select_spotify(self) -> bool:
        """Switch to Spotify (librespot) source"""
        from ..kitchen_radio import BackendType
        logger.info("Switching to Spotify source")
        return self.kitchen_radio.set_source(BackendType.LIBRESPOT)
    
    def _play_pause(self) -> bool:
        """Toggle play/pause"""
        logger.info("Toggle play/pause")
        return self.kitchen_radio.play_pause()
    
    def _stop(self) -> bool:
        """Stop playback"""
        logger.info("Stop playback")
        return self.kitchen_radio.stop_play()
    
    def _next(self) -> bool:
        """Next track"""
        logger.info("Next track")
        return self.kitchen_radio.next()
    
    def _previous(self) -> bool:
        """Previous track"""
        logger.info("Previous track")
        return self.kitchen_radio.previous()
    
    def _volume_up(self) -> bool:
        """Increase volume and show volume screen"""
        logger.debug("Volume up")
        result = self.kitchen_radio.volume_up(step=5)
        
        # Show volume screen if display controller is available
        try:
            self.display_controller.show_volume_overlay()
        except Exception as e:
            logger.warning(f"Failed to show volume screen: {e}")
        
        return result
    
    def _volume_down(self) -> bool:
        """Decrease volume and show volume screen"""
        logger.debug("Volume down")
        result = self.kitchen_radio.volume_down(step=5)
        
        # Show volume screen if display controller is available
        
        try:
            self.display_controller.show_volume_overlay()
        except Exception as e:
            logger.warning(f"Failed to show volume screen: {e}")
        
        return result
    

    
    def _menu_up(self) -> bool:
        """Menu up navigation"""
        logger.info("Menu up navigation")
        try:
            menu_items = self._get_menu_items()
            if menu_items:
                # Scroll up (previous item)
                self._current_menu_index = (self._current_menu_index - 1) % len(menu_items)
                logger.info(f"Menu scroll up to index {self._current_menu_index}")
                
                # Update display with menu
                if self.display_controller:
                        # Pass an on_selected handler so selection triggers menu action
                    self.display_controller.show_menu_overlay(
                        menu_items,
                        selected_index=self._current_menu_index,
                        timeout=self._menu_timeout_seconds,
                        on_selected=self._on_menu_item_selected
                    )

                return True
        except Exception as e:
            logger.error(f"Error in menu up navigation: {e}")
            return False
    
    def _menu_down(self) -> bool:
        """Menu up navigation"""
        logger.info("Menu up navigation")
        try:
            menu_items = self._get_menu_items()
            if menu_items:
                # Scroll up (previous item)
                self._current_menu_index = (self._current_menu_index + 1) % len(menu_items)
                logger.info(f"Menu scroll up to index {self._current_menu_index}")
                
                # Update display with menu
                if self.display_controller:
                        # Pass an on_selected handler so selection triggers menu action
                    self.display_controller.show_menu_overlay(
                        menu_items,
                        selected_index=self._current_menu_index,
                        timeout=self._menu_timeout_seconds,
                        on_selected=self._on_menu_item_selected
                    )

                return True
        except Exception as e:
            logger.error(f"Error in menu up navigation: {e}")
            return False
        

    def _on_menu_item_selected(self, index: int, selected_item: Optional[str]) -> None:
        """Handle selection of a menu item"""
        logger.info(f"Handling menu selection: '{selected_item}'")
        
        try:
            result = self.kitchen_radio.execute_menu_action('select menu', selected_item)
            logger.info(f"MPD playlist execution result: {result}")
            return result.get('success', False)
                
        except Exception as e:
            logger.error(f"Error handling menu selection '{selected_item}': {e}")
            if self.display_controller:
                self.display_controller.show_status_message(f"Error: {selected_item}", "❌", "error")
            return False
    
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
    
 

    def _get_menu_items(self) -> list:
        """Get available menu items for playlist/source selection"""
        menu_items = []
        
        try:
            # Get current status to see what's available
            status = self.kitchen_radio.get_status()
            available_sources = status.get('available_sources', [])
            current_source = status.get('current_source')
            
            logger.info(f"Getting menu items - available sources: {available_sources}, current: {current_source}")
            
            # Get menu options from kitchen radio for current source
            if current_source:
                try:
                    menu_options = self.kitchen_radio.get_menu_options()
                    logger.info(f"Kitchen radio menu options: {menu_options}")
                    
                    if menu_options.get('has_menu', False):
                        options = menu_options.get('options', [])
                        for option in options:
                            # Extract label from the option
                            label = option.get('label', option.get('id', 'Unknown'))
                            menu_items.append(label)
                            logger.info(f"Added menu item from kitchen radio: {label}")
                    
                except Exception as e:
                    logger.error(f"Error getting kitchen radio menu options: {e}")
            
            
            # Ensure we always have at least one item
            if not menu_items:
                menu_items = ["No sources available"]
                
        except Exception as e:
            logger.error(f"Error getting menu items: {e}")
            menu_items = ["Menu Error"]
        
        return menu_items
    
    # def _exit_menu(self) -> bool:
    #     """Exit/hide the menu display and execute the currently selected item"""
    #     logger.info("Exiting menu")
    #     try:
    #         # Execute the currently selected menu item before hiding
    #         if (hasattr(self, '_menu_visible') and self._menu_visible and 
    #             hasattr(self, '_current_menu_index')):
                
    #             logger.info(f"Menu is visible: {self._menu_visible}, current index: {getattr(self, '_current_menu_index', 'None')}")
                
    #             menu_items = self._get_menu_items()
    #             logger.info(f"Menu items: {menu_items}")
                
    #             if menu_items and 0 <= self._current_menu_index < len(menu_items):
    #                 selected_item = menu_items[self._current_menu_index]
    #                 logger.info(f"Auto-executing selected menu item: '{selected_item}' at index {self._current_menu_index}")
                    
    #                 # Handle the menu selection
    #                 result = self._handle_menu_selection(selected_item)
    #                 logger.info(f"Menu selection result: {result}")
    #             else:
    #                 logger.warning(f"Invalid menu state: items={len(menu_items) if menu_items else 0}, index={getattr(self, '_current_menu_index', 'None')}")
            
    #         # Clear menu state
    #         if hasattr(self, '_menu_visible'):
    #             self._menu_visible = False
    #             self._current_menu_index = 0
            
    #         # Return to normal display
    #         if self.display_controller:
    #             # Trigger a return to the main display
    #             # This will cause the display controller to show the current status
    #             try:
    #                 # Get current status and show it
    #                 status = self.kitchen_radio.get_status()
    #                 current_source = status.get('current_source')
                    
    #                 if current_source == 'mpd':
    #                     mpd_status = status.get('mpd', {})
    #                     if mpd_status.get('connected') and mpd_status.get('current_track'):
    #                         # Show current MPD track
    #                         track = mpd_status['current_track']
    #                         self.display_controller.show_track_info(track, mpd_status.get('state', 'stopped'))
    #                     else:
    #                         self.display_controller.show_status_message("MPD Connected", "♪", "info")
                    
    #                 elif current_source == 'librespot':
    #                     librespot_status = status.get('librespot', {})
    #                     if librespot_status.get('connected') and librespot_status.get('current_track'):
    #                         # Show current Spotify track with progress
    #                         track = librespot_status['current_track']
    #                         progress = librespot_status.get('progress', {})
    #                         self.display_controller.show_track(track, librespot_status.get('state', 'stopped'))
    #                     else:
    #                         self.display_controller.show_status_message("Spotify Connected", "♫", "info")
                    
    #                 else:
    #                     # No active source or disconnected
    #                     self.display_controller.show_status_message("Ready", "📻", "info")
                        
    #             except Exception as e:
    #                 logger.warning(f"Error refreshing display after menu exit: {e}")
    #                 # Fallback to simple status message
    #                 self.display_controller.show_status_message("Kitchen Radio", "📻", "info")
                
    #             return True
    #         return False
    #     except Exception as e:
    #         logger.error(f"Error exiting menu: {e}")
    #         return False
    
    # def _start_menu_timeout(self):
    #     """Start or restart the menu timeout timer"""
    #     import threading
    #     import time
        
    #     # Cancel existing timeout thread if running
    #     if self._menu_timeout_thread and self._menu_timeout_thread.is_alive():
    #         self._menu_timeout_thread = None  # Let it finish naturally
        
    #     # Update last activity time
    #     self._menu_last_activity_time = time.time()
        
    #     # Start new timeout thread
    #     def timeout_worker():
    #         logger.info(f"Menu timeout worker started, will wait {self._menu_timeout_seconds} seconds")
    #         time.sleep(self._menu_timeout_seconds)
            
    #         current_time = time.time()
    #         time_since_activity = current_time - self._menu_last_activity_time
            
    #         logger.info(f"Menu timeout check: visible={getattr(self, '_menu_visible', False)}, time_since_activity={time_since_activity:.2f}s")
            
    #         # Check if menu is still active and no new activity occurred
    #         if (hasattr(self, '_menu_visible') and self._menu_visible and 
    #             time_since_activity >= self._menu_timeout_seconds):
    #             logger.info("Menu auto-hiding after timeout - calling _exit_menu()")
    #             self._exit_menu()
    #         else:
    #             logger.info("Menu timeout cancelled - activity detected or menu no longer visible")
        
    #     self._menu_timeout_thread = threading.Thread(target=timeout_worker, daemon=True)
    #     self._menu_timeout_thread.start()
    
    # def _reset_menu_timeout(self):
    #     """Reset the menu timeout (called on menu activity)"""
    #     if hasattr(self, '_menu_visible') and self._menu_visible:
    #         self._start_menu_timeout()


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
