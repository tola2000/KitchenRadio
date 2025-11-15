"""
Button Controller for KitchenRadio Physical Interface

Provides button control interface with MCP23017 GPIO support.
Supports both hardware buttons and programmatic control.
"""

import logging
import threading
import time
from typing import Dict, Callable, Optional, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..kitchen_radio import KitchenRadio, BackendType

logger = logging.getLogger(__name__)

# Hardware configuration flag
try:
    import board
    import busio
    from adafruit_mcp230xx.mcp23017 import MCP23017
    from digitalio import Pull
    HARDWARE_AVAILABLE = True
    logger.info("✓ Hardware libraries loaded successfully (board, busio, MCP23017, Pull)")
except ImportError as e:
    HARDWARE_AVAILABLE = False
    logger.info(f"✗ Hardware libraries not available: {e}")
    logger.info("   To enable hardware buttons: pip install adafruit-circuitpython-mcp230xx")


class ButtonType(Enum):
    """Types of buttons on the physical radio"""
    # Source buttons (top row)
    SOURCE_MPD = "source_mpd"
    SOURCE_SPOTIFY = "source_spotify"
    SOURCE_CD = "source_cd"
    # Menu buttons (around display)
    MENU_UP = "menu_up"
    MENU_DOWN = "menu_down"

    SLEEP = "sleep"              
    REPEAT = "repeat"           
    SHUFFLE = "shuffle"          
    DISPLAY = "display" 
    
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


# MCP23017 Pin assignments for buttons
# Format: ButtonType -> MCP23017 pin number (0-15)
# Pins 0-7 are on Port A (GPA0-GPA7)
# Pins 8-15 are on Port B (GPB0-GPB7)
BUTTON_PIN_MAP = {
    # Source buttons 
    ButtonType.SOURCE_MPD: 7,         # TUNER
    ButtonType.SOURCE_SPOTIFY: 6,     # AUX
    ButtonType.SOURCE_CD: 5,          # CD Player (if applicable)
    
    # Menu buttons 
    ButtonType.MENU_UP: 8,            # 
    ButtonType.MENU_DOWN: 9,          # 


    ButtonType.SLEEP: 15,              # 
    ButtonType.REPEAT: 14,             # 
    ButtonType.SHUFFLE: 13,            # 
    ButtonType.DISPLAY: 11,            # 

    
    # Transport buttons 
    ButtonType.TRANSPORT_PREVIOUS: 1,     # 
    ButtonType.TRANSPORT_PLAY_PAUSE: 3,   # 
    ButtonType.TRANSPORT_STOP: 4,        # 
    ButtonType.TRANSPORT_NEXT: 2,        # 
    
    # Volume buttons 
    ButtonType.VOLUME_DOWN: 10,       # 
    ButtonType.VOLUME_UP: 12,         # 
    
    # Power button 
    ButtonType.POWER: 0,             # 
}


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
                 kitchen_radio: 'KitchenRadio' = None,
                 debounce_time: float = 0.05,
                 long_press_time: float = 1.0,
                 display_controller = None,
                 use_hardware: bool = True,
                 simulation_mode: bool = False,
                 i2c_address: int = 0x27):
        """
        Initialize button controller with MCP23017 hardware support.
        
        Args:
            kitchen_radio: KitchenRadio instance to control
            debounce_time: Button debounce time in seconds
            long_press_time: Time threshold for long press detection
            display_controller: Optional display controller for volume screen
            use_hardware: Enable MCP23017 hardware buttons (auto-disabled if not available)
            simulation_mode: Legacy parameter - disables hardware (opposite of use_hardware)
            i2c_address: I2C address of MCP23017 (default 0x27)
        """
        # Store KitchenRadio reference
        self.kitchen_radio = kitchen_radio
        
        # Store display controller for volume screen
        self.display_controller = display_controller
        
        # Timing configuration
        self.debounce_time = debounce_time
        self.long_press_time = long_press_time
        
        # Hardware configuration (support both use_hardware and simulation_mode)
        # simulation_mode=True means use_hardware=False
        if simulation_mode:
            use_hardware = False
        self.use_hardware = use_hardware and HARDWARE_AVAILABLE
        self.i2c_address = i2c_address
        self.mcp = None
        self.button_pins = {}
        self.monitor_thread = None
        
        # Button state tracking for debouncing
        self.button_states: Dict[ButtonType, Dict[str, Any]] = {}
        self.press_threads: Dict[ButtonType, threading.Thread] = {}
        
        # Initialize button states
        for button_type in ButtonType:
            self.button_states[button_type] = {
                'pressed': False,
                'last_event_time': 0,
                'press_start_time': 0,
                'long_press_fired': False,
                'pending_state': None,
                'pending_since': None,
                'last_state': True  # HIGH (not pressed) with pull-up
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
            
            # Menu buttons
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
        Initialize button controller with MCP23017 hardware if available.
        
        Returns:
            True if initialization successful
        """
        try:
            logger.info(f"ButtonController initialization: use_hardware={self.use_hardware}, HARDWARE_AVAILABLE={HARDWARE_AVAILABLE}")
            
            if self.use_hardware:
                logger.info("Attempting to initialize MCP23017 button hardware...")
                success = self._initialize_hardware()
                if success:
                    logger.info(f"✓ ButtonController initialized with hardware support ({len(BUTTON_PIN_MAP)} buttons)")
                else:
                    logger.warning("✗ Hardware initialization failed, falling back to software mode")
                    self.use_hardware = False
                    self.running = False  # Ensure running is False if hardware failed
            else:
                if not HARDWARE_AVAILABLE:
                    logger.info("GPIO buttons disabled: Hardware libraries not available (install adafruit-circuitpython-mcp230xx)")
                else:
                    logger.info("GPIO buttons disabled: use_hardware=False (set to True to enable)")
                logger.info("ButtonController initialized in software mode (programmatic control only)")
                self.running = False  # No hardware monitoring needed
            
            self.initialized = True
            # Note: self.running is set in _initialize_hardware() if hardware is used
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize button controller: {e}")
            return False
    
    def _initialize_hardware(self) -> bool:
        """
        Initialize MCP23017 GPIO expander and configure button pins.
        
        Returns:
            True if hardware initialization successful
        """
        try:
            # Initialize I2C and MCP23017
            i2c = busio.I2C(board.SCL, board.SDA)
            self.mcp = MCP23017(i2c, address=self.i2c_address)
            logger.info(f"MCP23017 found at address 0x{self.i2c_address:02X}")
            
            # Configure all button pins as inputs with pull-up resistors
            # Buttons connect pins to GND when pressed (active-low)
            for button_type, pin_number in BUTTON_PIN_MAP.items():
                pin = self.mcp.get_pin(pin_number)
                pin.switch_to_input(pull=Pull.UP)
                self.button_pins[button_type] = pin
                logger.debug(f"Configured {button_type.value} on pin {pin_number}")
            
            # Verify pull-ups are enabled
            gppu_a = self.mcp._read_u8(0x0C)  # GPPU register Port A
            gppu_b = self.mcp._read_u8(0x0D)  # GPPU register Port B
            logger.info(f"Pull-up registers: Port A=0x{gppu_a:02X}, Port B=0x{gppu_b:02X}")
            
            # Set running flag BEFORE starting thread
            self.running = True
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor_buttons, daemon=True)
            self.monitor_thread.start()
            logger.info("Button monitoring thread started")
            
            return True
            
        except Exception as e:
            logger.error(f"Hardware initialization failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        
        # Stop monitoring thread
        if self.monitor_thread and self.monitor_thread.is_alive():
            logger.info("Stopping button monitoring thread...")
            self.monitor_thread.join(timeout=2.0)
            if self.monitor_thread.is_alive():
                logger.warning("Button monitoring thread did not stop cleanly")
        
        self.initialized = False
        logger.info("Button controller cleanup completed")
    
    def _monitor_buttons(self):
        """
        Monitor all button pins and handle state changes with debouncing.
        Runs in separate thread.
        """
        logger.info("Button monitoring started")
        
        try:
            while self.running:
                for button_type, pin in self.button_pins.items():
                    self._check_button_state(button_type, pin)
                
                time.sleep(0.01)  # 10ms polling interval
                
        except Exception as e:
            logger.error(f"Error in button monitoring: {e}")
        
        logger.info("Button monitoring stopped")
    
    def _check_button_state(self, button_type: ButtonType, pin):
        """
        Check button state and handle debouncing.
        
        Args:
            button_type: The button to check
            pin: The MCP23017 pin object
        """
        state = self.button_states[button_type]
        current_pin_state = pin.value  # True = HIGH (not pressed), False = LOW (pressed)
        current_time = time.time()
        
        # Detect state change
        if current_pin_state != state['last_state']:
            # New state change - start debounce timer
            if state['pending_state'] is None:
                state['pending_state'] = current_pin_state
                state['pending_since'] = current_time
            
            # Check if state has been stable long enough
            if (state['pending_state'] == current_pin_state and 
                (current_time - state['pending_since']) >= self.debounce_time):
                # Accept the change
                state['last_state'] = state['pending_state']
                state['pending_state'] = None
                state['pending_since'] = None
                
                # Handle button event
                if not state['last_state']:  # Button pressed (LOW)
                    self._handle_button_press(button_type)
                else:  # Button released (HIGH)
                    self._handle_button_release(button_type)
        else:
            # State returned to last_state - cancel pending change (bounce)
            if state['pending_state'] is not None:
                state['pending_state'] = None
                state['pending_since'] = None
    
    def _handle_button_press(self, button_type: ButtonType):
        """
        Handle button press event.
        
        Args:
            button_type: The button that was pressed
        """
        logger.info(f"Button pressed: {button_type.value}")
        
        # Execute button action
        self._execute_button_action(button_type)
    
    def _handle_button_release(self, button_type: ButtonType):
        """
        Handle button release event.
        
        Args:
            button_type: The button that was released
        """
        logger.debug(f"Button released: {button_type.value}")
    
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
            self.display_controller.show_Notification_overlay("Oeps, Niet Toegewezen", f"Knop {button_type.value}", timeout=2)
            return False
        
        try:
            action_method = self.button_actions[button_type]
            result = action_method()
            logger.debug(f"Button action {button_type.value} result: {result}")
            if not result:
                self.display_controller.show_Notification_overlay("Oeps, Functie Niet Beschikbaar" , f"{button_type.value}", timeout=2)  
            
            return result
        except Exception as e:
            logger.error(f"Error executing action for button {button_type.value}: {e}")
            self.display_controller.show_Notification_overlay("Oeps Error", f"{e}", timeout=2) 
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
            # Check if menu is available for current source
            status = self.kitchen_radio.get_status()
            current_source = status.get('current_source')
            
            if current_source:
                menu_options = self.kitchen_radio.get_menu_options()
                if not menu_options.get('has_menu', False):
                    logger.info(f"Menu not available for source: {current_source}")
                    if self.display_controller:
                        self.display_controller.show_status_message("Function not available", "⚠", "warning")
                    return False
            
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
        """Menu down navigation"""
        logger.info("Menu down navigation")
        try:
            # Check if menu is available for current source
            status = self.kitchen_radio.get_status()
            current_source = status.get('current_source')
            
            if current_source:
                menu_options = self.kitchen_radio.get_menu_options()
                if not menu_options.get('has_menu', False):
                    logger.info(f"Menu not available for source: {current_source}")
                    if self.display_controller:
                        self.display_controller.show_status_message("Function not available", "⚠", "warning")
                    return False
            
            menu_items = self._get_menu_items()
            if menu_items:
                # Scroll down (next item)
                self._current_menu_index = (self._current_menu_index + 1) % len(menu_items)
                logger.info(f"Menu scroll down to index {self._current_menu_index}")
                
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
            logger.error(f"Error in menu down navigation: {e}")
            return False
    
    # def _menu_toggle(self) -> bool:
    #     """Toggle menu display"""
    #     logger.info("Menu toggle")
    #     try:
    #         menu_items = self._get_menu_items()
    #         if menu_items and self.display_controller:
    #             self.display_controller.show_menu_overlay(
    #                 menu_items,
    #                 selected_index=self._current_menu_index,
    #                 timeout=self._menu_timeout_seconds,
    #                 on_selected=self._on_menu_item_selected
    #             )
    #             return True
    #         return False
    #     except Exception as e:
    #         logger.error(f"Error toggling menu: {e}")
    #         return False
    
    # def _menu_set(self) -> bool:
    #     """Set/confirm current menu selection"""
    #     logger.info("Menu set/confirm")
    #     return self._menu_ok()  # Same as OK for now
    
    # def _menu_ok(self) -> bool:
    #     """Confirm menu selection"""
    #     logger.info("Menu OK - selecting current item")
    #     try:
    #         return self._on_menu_item_selected(self._current_menu_index)
    #     except Exception as e:
    #         logger.error(f"Error confirming menu selection: {e}")
    #         return False
    
    # def _menu_exit(self) -> bool:
    #     """Exit menu and return to main display"""
    #     logger.info("Menu exit")
    #     try:
    #         if self.display_controller:
    #             # Close menu overlay
    #             self.display_controller.hide_overlay()
    #             return True
    #         return False
    #     except Exception as e:
    #         logger.error(f"Error exiting menu: {e}")
    #         return False

    def _on_menu_item_selected(self, index: int) -> None:
        """Handle selection of a menu item by index"""
        try:
            menu_items = self._get_menu_items()
            if 0 <= index < len(menu_items):
                selected_item = menu_items[index]
            else:
                selected_item = None
            logger.info(f"Handling menu selection: index={index}, item='{selected_item}'")
            result = self.kitchen_radio.execute_menu_action('select menu', selected_item)
            logger.info(f"MPD playlist execution result: {result}")
            return result.get('success', False)
        except Exception as e:
            logger.error(f"Error handling menu selection at index {index}: {e}")
            if self.display_controller:
                self.display_controller.show_status_message(f"Error: {e}", "❌", "error")
            return False
    
    def _power(self) -> bool:
        """Power button - stop all playback"""
        logger.info("Power button pressed - stopping all playback")
        return self.kitchen_radio.power()
    


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
