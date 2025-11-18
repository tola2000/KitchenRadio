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
    from kitchenradio.sources.source_controller import SourceController, BackendType

# Import configuration
from kitchenradio import config
from kitchenradio.config import buttons as buttons_config

logger = logging.getLogger(__name__)

# Hardware configuration flag
try:
    import board
    import busio
    from adafruit_mcp230xx.mcp23017 import MCP23017
    from digitalio import Pull
    HARDWARE_AVAILABLE = True
    logger.info("[OK] Hardware libraries loaded successfully (board, busio, MCP23017, Pull)")
except ImportError as e:
    HARDWARE_AVAILABLE = False
    logger.info(f"[X] Hardware libraries not available: {e}")
    logger.info("   To enable hardware buttons: pip install adafruit-circuitpython-mcp230xx")


class ButtonType(Enum):
    """Types of buttons on the physical radio"""
    # Source buttons (top row)
    SOURCE_MPD = "source_mpd"
    SOURCE_SPOTIFY = "source_spotify"
    SOURCE_BLUETOOTH = "source_bluetooth"
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
# Now loaded from config.buttons module
def _get_button_pin_map():
    """Get button pin mapping from config"""
    return {
        # Source buttons 
        ButtonType.SOURCE_MPD: buttons_config.PIN_SOURCE_MPD,
        ButtonType.SOURCE_SPOTIFY: buttons_config.PIN_SOURCE_SPOTIFY,
        ButtonType.SOURCE_BLUETOOTH: buttons_config.PIN_SOURCE_BLUETOOTH,
        
        # Menu buttons 
        ButtonType.MENU_UP: buttons_config.PIN_MENU_UP,
        ButtonType.MENU_DOWN: buttons_config.PIN_MENU_DOWN,
        
        # Function buttons
        ButtonType.SLEEP: buttons_config.PIN_SLEEP,
        ButtonType.REPEAT: buttons_config.PIN_REPEAT,
        ButtonType.SHUFFLE: buttons_config.PIN_SHUFFLE,
        ButtonType.DISPLAY: buttons_config.PIN_DISPLAY,
        
        # Transport buttons 
        ButtonType.TRANSPORT_PREVIOUS: buttons_config.PIN_TRANSPORT_PREVIOUS,
        ButtonType.TRANSPORT_PLAY_PAUSE: buttons_config.PIN_TRANSPORT_PLAY_PAUSE,
        ButtonType.TRANSPORT_STOP: buttons_config.PIN_TRANSPORT_STOP,
        ButtonType.TRANSPORT_NEXT: buttons_config.PIN_TRANSPORT_NEXT,
        
        # Volume buttons 
        ButtonType.VOLUME_DOWN: buttons_config.PIN_VOLUME_DOWN,
        ButtonType.VOLUME_UP: buttons_config.PIN_VOLUME_UP,
        
        # Power button 
        ButtonType.POWER: buttons_config.PIN_POWER,
    }

# Initialize pin map from config
BUTTON_PIN_MAP = _get_button_pin_map()


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
                 source_controller: 'SourceController' = None,
                 debounce_time: float = None,
                 long_press_time: float = None,
                 display_controller = None,
                 use_hardware: bool = None,
                 simulation_mode: bool = False,
                 i2c_address: int = None,
                 shutdown_callback: Callable[[], None] = None):
        """
        Initialize button controller with MCP23017 hardware support.
        
        Args:
            source_controller: SourceController instance to control playback
            debounce_time: Button debounce time in seconds (default from config)
            long_press_time: Time threshold for long press detection (default from config)
            display_controller: Optional display controller for volume screen
            use_hardware: Enable MCP23017 hardware buttons (default from config, auto-disabled if not available)
            simulation_mode: Legacy parameter - disables hardware (opposite of use_hardware)
            i2c_address: I2C address of MCP23017 (default from config)
            shutdown_callback: Callback function to initiate system shutdown/reboot
        """
        # Store SourceController reference
        self.source_controller = source_controller
        
        # Store shutdown callback for long press power button
        self.shutdown_callback = shutdown_callback
        
        # Store display controller for volume screen
        self.display_controller = display_controller
        
        # Timing configuration - use config defaults if not specified
        self.debounce_time = debounce_time if debounce_time is not None else buttons_config.DEBOUNCE_TIME
        self.long_press_time = long_press_time if long_press_time is not None else buttons_config.LONG_PRESS_TIME
        
        # Hardware configuration (support both use_hardware and simulation_mode)
        # simulation_mode=True means use_hardware=False
        if simulation_mode:
            use_hardware = False
        
        # Use config default if not specified
        if use_hardware is None:
            use_hardware = buttons_config.USE_HARDWARE
            
        self.use_hardware = use_hardware and HARDWARE_AVAILABLE
        self.i2c_address = i2c_address if i2c_address is not None else buttons_config.I2C_ADDRESS
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
            ButtonType.SOURCE_BLUETOOTH: self._select_bluetooth,
            
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
        
        # Store press start time for long press detection
        state = self.button_states[button_type]
        state['press_start_time'] = time.time()
        state['pressed'] = True
        state['long_press_fired'] = False
        
        # For power button, start long press detection thread
        if button_type == ButtonType.POWER:
            logger.info(f"🔵 Power button pressed - starting long press detection (threshold: {self.long_press_time}s)")
            self._start_long_press_detection(button_type)
        else:
            # Execute button action immediately for non-power buttons
            self._execute_button_action(button_type)
    
    def _handle_button_release(self, button_type: ButtonType):
        """
        Handle button release event.
        
        Args:
            button_type: The button that was released
        """
        logger.debug(f"Button released: {button_type.value}")
        
        state = self.button_states[button_type]
        press_duration = time.time() - state['press_start_time'] if state['press_start_time'] > 0 else 0
        state['pressed'] = False
        
        # For power button, handle short press if long press didn't fire
        if button_type == ButtonType.POWER:
            logger.info(f"🔵 Power button released: duration={press_duration:.2f}s, long_press_fired={state['long_press_fired']}, threshold={self.long_press_time}s")
            
            if not state['long_press_fired'] and press_duration < self.long_press_time:
                logger.info(f"⚪ Power button SHORT PRESS detected ({press_duration:.2f}s < {self.long_press_time}s)")
                self._execute_button_action(button_type)
            elif state['long_press_fired']:
                logger.info(f"🔴 Power button released after LONG PRESS ({press_duration:.2f}s >= {self.long_press_time}s)")
            else:
                logger.warning(f"⚠️ Power button released but no action taken: duration={press_duration:.2f}s, fired={state['long_press_fired']}")
        
        state['press_start_time'] = 0
        state['long_press_fired'] = False
    
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
    
    def _start_long_press_detection(self, button_type: ButtonType):
        """
        Start long press detection for a button in a separate thread.
        
        Args:
            button_type: The button to monitor for long press
        """
        def long_press_worker():
            state = self.button_states[button_type]
            start_time = state['press_start_time']
            
            # Wait for long press duration
            time.sleep(self.long_press_time)
            
            # Check if button is still pressed and this is the same press event
            if (state['pressed'] and 
                state['press_start_time'] == start_time and 
                not state['long_press_fired']):
                
                logger.info(f"🔴 Long press detected on {button_type.value} ({self.long_press_time}s)")
                state['long_press_fired'] = True
                
                # Execute long press action
                if button_type == ButtonType.POWER:
                    self._power_long_press()
        
        # Start thread
        thread = threading.Thread(target=long_press_worker, daemon=True)
        self.press_threads[button_type] = thread
        thread.start()
    
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
            self.display_controller.show_Notification_overlay("Oeps", f"Niet Toegewezen {button_type.value}", timeout=2 )
            return False
        
        try:
            action_method = self.button_actions[button_type]
            result = action_method()
            logger.debug(f"Button action {button_type.value} result: {result}")
            if not result:
                self.display_controller.show_Notification_overlay("Oeps", f"Functie Niet Beschikbaar {button_type.value}", timeout=2)  
            
            return result
        except Exception as e:
            logger.error(f"Error executing action for button {button_type.value}: {e}")
            self.display_controller.show_Notification_overlay("Oeps Error", f"{e}", timeout=2) 
            return False


    # KitchenRadio Action Methods - Direct calls to KitchenRadio
    
    def _select_mpd(self) -> bool:
        """Switch to MPD source"""
        from kitchenradio.sources.source_controller import BackendType
        logger.info("Switching to MPD source")
        return self.source_controller.set_source(BackendType.MPD)
    
    def _select_spotify(self) -> bool:
        """Switch to Spotify (librespot) source"""
        from kitchenradio.sources.source_controller import BackendType
        logger.info("Switching to Spotify source")
        return self.source_controller.set_source(BackendType.LIBRESPOT)
    
    def _select_bluetooth(self) -> bool:
        """Switch to Bluetooth source and enter pairing mode"""
        from kitchenradio.sources.source_controller import BackendType
        logger.info("Switching to Bluetooth source")
        return self.source_controller.set_source(BackendType.BLUETOOTH)
    
    def _play_pause(self) -> bool:
        """Toggle play/pause"""
        logger.info("Toggle play/pause")
        return self.source_controller.play_pause()
    
    def _stop(self) -> bool:
        """Stop playback"""
        logger.info("Stop playback")
        return self.source_controller.stop_play()
    
    def _next(self) -> bool:
        """Next track"""
        logger.info("Next track")
        return self.source_controller.next()
    
    def _previous(self) -> bool:
        """Previous track"""
        logger.info("Previous track")
        return self.source_controller.previous()
    
    def _volume_up(self) -> bool:
        """Increase volume and show volume screen"""
        logger.debug("Volume up")
        
        # Change the volume - controller calculates and returns new volume
        new_volume = self.source_controller.volume_up(step=buttons_config.VOLUME_STEP)
        
        # Show volume screen - display will get volume from status (with expected values)
        if new_volume is not None:
            try:
                self.display_controller.show_volume_overlay()
            except Exception as e:
                logger.warning(f"Failed to show volume screen: {e}")
        
        return new_volume is not None
    
    def _volume_down(self) -> bool:
        """Decrease volume and show volume screen"""
        logger.debug("Volume down")
        
        # Change the volume - controller calculates and returns new volume
        new_volume = self.source_controller.volume_down(step=buttons_config.VOLUME_STEP)
        
        # Show volume screen - display will get volume from status (with expected values)
        if new_volume is not None:
            try:
                self.display_controller.show_volume_overlay()
            except Exception as e:
                logger.warning(f"Failed to show volume screen: {e}")
        
        return new_volume is not None
    

    
    def _menu_up(self) -> bool:
        """Menu up navigation"""
        logger.info("Menu up navigation")
        try:
            status = self.source_controller.get_status()
            if not status.get('powered_on', True):
                # If powered off, show poweroff menu
                if self.display_controller:
                    self.display_controller.show_poweroff_menu()
                return True
            # ...existing menu up logic...
            current_source = status.get('current_source')
            if current_source:
                menu_options = self.source_controller.get_menu_options()
                if not menu_options.get('has_menu', False):
                    logger.info(f"Menu not available for source: {current_source}")
                    if self.display_controller:
                        self.display_controller.show_status_message("Function not available", "⚠", "warning")
                    return False
            menu_items = self._get_menu_items()
            if menu_items:
                self._current_menu_index = (self._current_menu_index - 1) % len(menu_items)
                logger.info(f"Menu scroll up to index {self._current_menu_index}")
                if self.display_controller:
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
            status = self.source_controller.get_status()
            if not status.get('powered_on', True):
                # If powered off, show poweroff menu
                if self.display_controller:
                    self.display_controller.show_poweroff_menu()
                return True
            # ...existing menu down logic...
            current_source = status.get('current_source')
            if current_source:
                menu_options = self.source_controller.get_menu_options()
                if not menu_options.get('has_menu', False):
                    logger.info(f"Menu not available for source: {current_source}")
                    if self.display_controller:
                        self.display_controller.show_status_message("Function not available", "⚠", "warning")
                    return False
            menu_items = self._get_menu_items()
            if menu_items:
                self._current_menu_index = (self._current_menu_index + 1) % len(menu_items)
                logger.info(f"Menu scroll down to index {self._current_menu_index}")
                if self.display_controller:
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
            # Get menu options from source controller (not just the labels)
            menu_options = self.source_controller.get_menu_options()
            
            if not menu_options.get('has_menu', False):
                logger.warning("No menu available")
                return False
            
            options = menu_options.get('options', [])
            if 0 <= index < len(options):
                selected_option = options[index]
                option_id = selected_option.get('id')
                action = selected_option.get('action', 'select')
                
                logger.info(f"Handling menu selection: index={index}, option_id='{option_id}', action='{action}'")
                
                # Execute the menu action
                result = self.source_controller.execute_menu_action(action, option_id)
                logger.info(f"Menu action execution result: {result}")
                
                # Show success/error message
                if self.display_controller:
                    if result.get('success', False):
                        message = result.get('message', 'Action completed')
                        self.display_controller.show_status_message(message, "✓", "success")
                    else:
                        error = result.get('error', 'Action failed')
                        self.display_controller.show_status_message(error, "❌", "error")
                
                return result.get('success', False)
            else:
                logger.error(f"Invalid menu index: {index}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling menu selection at index {index}: {e}")
            if self.display_controller:
                self.display_controller.show_status_message(f"Error: {e}", "❌", "error")
            return False
    
    def _power(self) -> bool:
        """Power button short press - toggle power on/off"""
        logger.info("Power button short press - toggling power")
        return self.source_controller.power()
    
    def _power_long_press(self) -> bool:
        """Power button long press - initiate system reboot"""
        logger.info("🔴 Power button LONG PRESS - initiating system reboot!")
        
        try:
            # Show notification that reboot is starting
            if self.display_controller:
                self.display_controller.show_Notification_overlay(
                    "Systeem Herstart", 
                    "Bezig met herstarten...", 
                    timeout=5
                )
            
            # Give display time to show the message
            time.sleep(1)
            
            # Initiate shutdown and reboot via callback
            if self.shutdown_callback:
                self.shutdown_callback()
                return True
            else:
                logger.error("No shutdown callback configured!")
                if self.display_controller:
                    self.display_controller.show_Notification_overlay(
                        "Herstart Mislukt", 
                        "Geen shutdown callback", 
                        timeout=3
                    )
                return False
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            if self.display_controller:
                self.display_controller.show_Notification_overlay(
                    "Herstart Mislukt", 
                    f"Fout: {e}", 
                    timeout=3
                )
            return False


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
            status = self.source_controller.get_status()
            available_sources = status.get('available_sources', [])
            current_source = status.get('current_source')
            
            logger.info(f"Getting menu items - available sources: {available_sources}, current: {current_source}")
            
            # Get menu options from kitchen radio for current source
            if current_source:
                try:
                    menu_options = self.source_controller.get_menu_options()
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
    
