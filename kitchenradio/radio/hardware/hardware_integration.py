"""
Hardware Integration for KitchenRadio Physical Interface

Integrates button controller and display controller with the main KitchenRadio system.
"""

import logging
import threading
import time
from typing import Optional, Dict, Any, List

from .button_controller import ButtonController, ButtonType, ButtonEvent
from .display_controller import DisplayController, DisplayType
from ..kitchen_radio import KitchenRadio, BackendType

logger = logging.getLogger(__name__)


class HardwareIntegration:
    """
    Integrates physical hardware controls with KitchenRadio daemon.
    
    Features:
    - Physical button mapping to radio functions
    - Display updates based on radio state
    - Menu navigation on hardware display
    - Volume control with visual feedback
    - Source selection with physical buttons
    """
    
    def __init__(self, 
                 kitchen_radio: KitchenRadio,
                 display_type: str = DisplayType.SSD1306_128x64,
                 button_pin_mapping: Dict[ButtonType, int] = None,
                 i2c_port: int = 1,
                 i2c_address: int = 0x3C):
        """
        Initialize hardware integration.
        
        Args:
            kitchen_radio: KitchenRadio daemon instance
            display_type: Type of OLED display
            button_pin_mapping: Custom GPIO pin mapping for buttons
            i2c_port: I2C port for display
            i2c_address: I2C address for display
        """
        self.kitchen_radio = kitchen_radio
        
        # Initialize hardware controllers
        self.button_controller = ButtonController(pin_mapping=button_pin_mapping)
        self.display_controller = DisplayController(
            display_type=display_type,
            i2c_port=i2c_port,
            i2c_address=i2c_address
        )
        
        # State tracking
        self.current_source = None
        self.current_track = None
        self.current_volume = 0
        self.is_playing = False
        self.menu_visible = False
        self.menu_options = []
        self.menu_selected_index = 0
        
        # Update thread
        self.update_thread = None
        self.running = False
        
        # Setup button callbacks
        self._setup_button_callbacks()
        
        logger.info("HardwareIntegration initialized")
    
    def initialize(self) -> bool:
        """
        Initialize hardware controllers.
        
        Returns:
            True if initialization successful
        """
        try:
            # Initialize button controller
            if not self.button_controller.initialize():
                logger.error("Failed to initialize button controller")
                return False
            
            # Initialize display controller
            if not self.display_controller.initialize():
                logger.error("Failed to initialize display controller")
                return False
            
            # Start update thread
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            
            # Show initial display
            self._update_display()
            
            logger.info("Hardware integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize hardware integration: {e}")
            return False
    
    def cleanup(self):
        """Clean up hardware resources"""
        self.running = False
        
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2.0)
        
        if self.button_controller:
            self.button_controller.cleanup()
        
        if self.display_controller:
            self.display_controller.cleanup()
        
        logger.info("Hardware integration cleanup completed")
    
    def _setup_button_callbacks(self):
        """Setup button event callbacks"""
        
        # Source buttons
        self.button_controller.set_button_callback(
            ButtonType.SOURCE_MPD, 
            lambda event: self._handle_source_button(event, 'mpd')
        )
        self.button_controller.set_button_callback(
            ButtonType.SOURCE_SPOTIFY, 
            lambda event: self._handle_source_button(event, 'spotify')
        )
        self.button_controller.set_button_callback(
            ButtonType.SOURCE_OFF, 
            lambda event: self._handle_source_button(event, 'off')
        )
        
        # Menu navigation buttons
        self.button_controller.set_button_callback(
            ButtonType.MENU_UP, 
            lambda event: self._handle_menu_button(event, 'up')
        )
        self.button_controller.set_button_callback(
            ButtonType.MENU_DOWN, 
            lambda event: self._handle_menu_button(event, 'down')
        )
        self.button_controller.set_button_callback(
            ButtonType.MENU_TOGGLE, 
            lambda event: self._handle_menu_button(event, 'toggle')
        )
        self.button_controller.set_button_callback(
            ButtonType.MENU_OK, 
            lambda event: self._handle_menu_button(event, 'ok')
        )
        self.button_controller.set_button_callback(
            ButtonType.MENU_EXIT, 
            lambda event: self._handle_menu_button(event, 'exit')
        )
        
        # Transport buttons
        self.button_controller.set_button_callback(
            ButtonType.TRANSPORT_PREVIOUS, 
            lambda event: self._handle_transport_button(event, 'previous')
        )
        self.button_controller.set_button_callback(
            ButtonType.TRANSPORT_PLAY_PAUSE, 
            lambda event: self._handle_transport_button(event, 'play_pause')
        )
        self.button_controller.set_button_callback(
            ButtonType.TRANSPORT_STOP, 
            lambda event: self._handle_transport_button(event, 'stop')
        )
        self.button_controller.set_button_callback(
            ButtonType.TRANSPORT_NEXT, 
            lambda event: self._handle_transport_button(event, 'next')
        )
        
        # Volume buttons
        self.button_controller.set_button_callback(
            ButtonType.VOLUME_DOWN, 
            lambda event: self._handle_volume_button(event, 'down')
        )
        self.button_controller.set_button_callback(
            ButtonType.VOLUME_UP, 
            lambda event: self._handle_volume_button(event, 'up')
        )
    
    def _handle_source_button(self, event: ButtonEvent, source: str):
        """Handle source button events"""
        if event.event_type != 'press':
            return
        
        try:
            if source == 'off':
                # Turn off radio
                self.kitchen_radio.set_source(None)
                self.current_source = None
                self._show_status_message("Radio OFF", "○")
                
            elif source == 'mpd':
                if self.current_source == 'mpd':
                    # Show MPD menu if already active
                    self._show_source_menu()
                else:
                    # Switch to MPD
                    if self.kitchen_radio.set_source(BackendType.MPD):
                        self.current_source = 'mpd'
                        self._show_status_message("MPD Selected", "♪")
                    else:
                        self._show_status_message("MPD Not Available", "!")
                        
            elif source == 'spotify':
                if self.current_source == 'spotify':
                    # Show Spotify menu if already active
                    self._show_source_menu()
                else:
                    # Switch to Spotify
                    if self.kitchen_radio.set_source(BackendType.LIBRESPOT):
                        self.current_source = 'spotify'
                        self._show_status_message("Spotify Selected", "♫")
                    else:
                        self._show_status_message("Spotify Not Available", "!")
            
        except Exception as e:
            logger.error(f"Error handling source button {source}: {e}")
            self._show_status_message("Error", "!")
    
    def _handle_menu_button(self, event: ButtonEvent, action: str):
        """Handle menu navigation button events"""
        if event.event_type != 'press':
            return
        
        try:
            if action == 'toggle':
                if self.menu_visible:
                    self._hide_menu()
                else:
                    self._show_source_menu()
                    
            elif action == 'up' and self.menu_visible:
                if self.menu_options:
                    self.menu_selected_index = max(0, self.menu_selected_index - 1)
                    self._update_menu_display()
                    
            elif action == 'down' and self.menu_visible:
                if self.menu_options:
                    self.menu_selected_index = min(len(self.menu_options) - 1, self.menu_selected_index + 1)
                    self._update_menu_display()
                    
            elif action == 'ok' and self.menu_visible:
                self._execute_menu_selection()
                
            elif action == 'exit' and self.menu_visible:
                self._hide_menu()
                
        except Exception as e:
            logger.error(f"Error handling menu button {action}: {e}")
    
    def _handle_transport_button(self, event: ButtonEvent, action: str):
        """Handle transport control button events"""
        if event.event_type != 'press':
            return
        
        if not self.current_source:
            self._show_status_message("No Source", "!")
            return
        
        try:
            success = False
            
            if action == 'play_pause':
                success = self.kitchen_radio.play_pause()
            elif action == 'stop':
                success = self.kitchen_radio.stop()
            elif action == 'previous':
                success = self.kitchen_radio.previous()
            elif action == 'next':
                success = self.kitchen_radio.next()
            
            if success:
                self._show_status_message(f"{action.upper()}", "♪")
            else:
                self._show_status_message("Command Failed", "!")
                
        except Exception as e:
            logger.error(f"Error handling transport button {action}: {e}")
            self._show_status_message("Error", "!")
    
    def _handle_volume_button(self, event: ButtonEvent, direction: str):
        """Handle volume control button events"""
        if event.event_type not in ['press', 'hold']:
            return
        
        if not self.current_source:
            self._show_status_message("No Source", "!")
            return
        
        try:
            step = 5 if event.event_type == 'press' else 2  # Smaller steps for hold
            
            if direction == 'up':
                success = self.kitchen_radio.volume_up(step)
            else:
                success = self.kitchen_radio.volume_down(step)
            
            if success:
                # Show volume briefly
                self.current_volume = self.kitchen_radio.get_volume() or 0
                self.display_controller.show_volume(self.current_volume)
                # Return to normal display after 2 seconds
                threading.Timer(2.0, self._update_display).start()
            else:
                self._show_status_message("Volume Error", "!")
                
        except Exception as e:
            logger.error(f"Error handling volume button {direction}: {e}")
    
    def _show_source_menu(self):
        """Show menu for the current active source"""
        if not self.current_source:
            return
        
        try:
            menu_data = self.kitchen_radio.get_menu_options()
            
            if menu_data.get('has_menu'):
                self.menu_options = menu_data['options']
                self.menu_selected_index = 0
                self.menu_visible = True
                self._update_menu_display()
            else:
                self._show_status_message(menu_data.get('message', 'No Menu'), "i")
                
        except Exception as e:
            logger.error(f"Error showing source menu: {e}")
            self._show_status_message("Menu Error", "!")
    
    def _update_menu_display(self):
        """Update the menu display"""
        if not self.menu_visible or not self.menu_options:
            return
        
        # Create menu title based on source
        if self.current_source == 'mpd':
            title = "Playlists"
        elif self.current_source == 'spotify':
            title = "Playback"
        else:
            title = "Menu"
        
        # Create option labels
        option_labels = [opt['label'] for opt in self.menu_options]
        
        self.display_controller.show_menu(title, option_labels, self.menu_selected_index)
    
    def _execute_menu_selection(self):
        """Execute the selected menu option"""
        if not self.menu_visible or not self.menu_options:
            return
        
        if not (0 <= self.menu_selected_index < len(self.menu_options)):
            return
        
        try:
            selected_option = self.menu_options[self.menu_selected_index]
            result = self.kitchen_radio.execute_menu_action(
                selected_option['action'], 
                selected_option.get('id')
            )
            
            if result.get('success'):
                self._show_status_message(result.get('message', 'Done'), "✓")
                self._hide_menu()
            else:
                self._show_status_message(result.get('error', 'Failed'), "!")
                
        except Exception as e:
            logger.error(f"Error executing menu selection: {e}")
            self._show_status_message("Error", "!")
    
    def _hide_menu(self):
        """Hide the menu and return to normal display"""
        self.menu_visible = False
        self.menu_options = []
        self.menu_selected_index = 0
        self._update_display()
    
    def _show_status_message(self, message: str, icon: str = "i"):
        """Show a temporary status message"""
        self.display_controller.show_status_message(message, icon)
        # Return to normal display after 2 seconds
        threading.Timer(2.0, self._update_display).start()
    
    def _update_loop(self):
        """Main update loop to sync display with radio state"""
        while self.running:
            try:
                if not self.menu_visible:
                    self._update_radio_state()
                    self._update_display()
                
                time.sleep(1.0)  # Update every second
                
            except Exception as e:
                logger.error(f"Error in hardware update loop: {e}")
                time.sleep(1.0)
    
    def _update_radio_state(self):
        """Update internal state from radio daemon"""
        try:
            status = self.kitchen_radio.get_status()
            
            # Update source
            self.current_source = status.get('current_source')
            
            # Update playback state
            if status.get('mpd', {}).get('connected') and self.current_source == 'mpd':
                mpd_status = status['mpd']
                self.is_playing = mpd_status.get('state') == 'play'
                self.current_track = mpd_status.get('current_song')
                self.current_volume = mpd_status.get('volume', 0)
                
            elif status.get('librespot', {}).get('connected') and self.current_source == 'librespot':
                spotify_status = status['librespot']
                self.is_playing = spotify_status.get('state') == 'playing'
                self.current_track = spotify_status.get('current_track')
                self.current_volume = spotify_status.get('volume', 0)
                
            else:
                self.is_playing = False
                self.current_track = None
                self.current_volume = 0
                
        except Exception as e:
            logger.error(f"Error updating radio state: {e}")
    
    def _update_display(self):
        """Update display based on current state"""
        try:
            if not self.current_source:
                # Radio is off
                self.display_controller.show_status_message("KitchenRadio Ready", "○")
                
            elif self.current_track:
                # Show current track
                title = self.current_track.get('title', 'Unknown')
                artist = self.current_track.get('artist', 'Unknown')
                album = self.current_track.get('album', '')
                
                self.display_controller.show_track_info(title, artist, album, self.is_playing)
                
            else:
                # Connected but no track
                source_name = "MPD" if self.current_source == 'mpd' else "Spotify"
                self.display_controller.show_status_message(f"{source_name} Ready", "♪")
                
        except Exception as e:
            logger.error(f"Error updating display: {e}")


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)
    
    # This would normally be done with a real KitchenRadio instance
    print("HardwareIntegration requires a running KitchenRadio daemon")
    print("Run this within the main KitchenRadio application to test hardware integration")
    
    # Example of how to integrate:
    """
    from kitchenradio.radio.kitchen_radio import KitchenRadio
    from kitchenradio.radio.hardware.hardware_integration import HardwareIntegration
    
    # Create radio daemon
    radio = KitchenRadio()
    radio.start()
    
    # Create hardware integration
    hardware = HardwareIntegration(radio)
    
    if hardware.initialize():
        print("Hardware integration started")
        try:
            # Keep running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            hardware.cleanup()
            radio.stop()
    """
