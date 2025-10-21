"""
Simplified Display Controller for SSD1322 256x64 OLED Display

Orchestrates display formatting and I2C hardware interface.
Simplified for KitchenRadio with SSD1322 display only.
"""

import logging
from re import S
import threading
import time
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING, Callable

from .display_formatter import DisplayFormatter
from .display_interface_i2c import I2CDisplayInterface

if TYPE_CHECKING:
    from ..kitchen_radio import KitchenRadio

logger = logging.getLogger(__name__)


class DisplayController:
    """
    Simplified Display Controller for SSD1322 256x64 OLED display.
    
    Orchestrates display formatting and I2C hardware interface.
    Much simpler than the previous complex implementation.
    """
    
    def __init__(self, 
                 kitchen_radio: 'KitchenRadio' = None,
                 i2c_port: int = 1,
                 i2c_address: int = 0x3C,
                 refresh_rate: float = 2.0,
                 i2c_interface = None):
        """
        Initialize simplified display controller for SSD1322.
        
        Args:
            kitchen_radio: KitchenRadio instance for status updates
            i2c_port: I2C port number (ignored if i2c_interface provided)
            i2c_address: I2C address of the SSD1322 display (ignored if i2c_interface provided)
            refresh_rate: Display refresh rate in Hz
            i2c_interface: Optional external I2C interface (for emulation)
        """
        self.kitchen_radio = kitchen_radio
        
        # Use provided interface or create I2C interface for SSD1322
        if i2c_interface:
            self.i2c_interface = i2c_interface
            logger.info("Using provided I2C interface (emulation mode)")
        else:
            self.i2c_interface = I2CDisplayInterface(
                i2c_port=i2c_port,
                i2c_address=i2c_address
            )
            logger.info("Created new I2C interface for hardware")
        
        # Create display formatter for SSD1322
        self.formatter = DisplayFormatter(
            width=self.i2c_interface.width,
            height=self.i2c_interface.height
        )
        
        # Display state
        self.last_status = None
        self.refresh_rate = refresh_rate
        
        # Current display tracking
        self.current_display_type = None  # 'track_info', 'status_message', 'menu', 'volume', etc.
        self.current_display_data = None  # Last data used to render current display
        
        # Truncation info storage - JSON structure with original strings as keys
        self.last_truncation_info = {}
        self.current_scroll_offsets = {}  # Track current scroll positions for each string
        
        # Scrolling state
        self.scrolling_active = False
        self.scroll_timer = None
        self.scroll_update_interval = 0.5  # Update every 500ms
        
        # Overlay state (for volume, menu, etc.)
        self.overlay_active = False
        self.overlay_type = None  # 'volume', 'menu', etc.
        self.overlay_end_time = 0
        self.overlay_timeout = 3.0  # 3 seconds default
        self.last_volume = None

        self.selected_index = 0
        self.on_menu_selected: None

        # Threading for updates
        self.update_thread = None
        self.running = False
        self.manual_update_requested = False
        
        logger.info(f"Simplified DisplayController initialized for SSD1322 ({self.i2c_interface.width}x{self.i2c_interface.height})")
    
    def initialize(self) -> bool:
        """
        Initialize the display controller.
        
        Returns:
            True if initialization successful
        """
        # Initialize I2C interface
        if not self.i2c_interface.initialize():
            logger.error("Failed to initialize display interface")
            return False
        
        # Start update thread if KitchenRadio is provided
        if self.kitchen_radio:
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            logger.info("Display update thread started")
        
        logger.info("Simplified DisplayController initialized successfully")
        return True
    
    def cleanup(self):
        """Clean up display resources"""
        logger.info("Cleaning up DisplayController...")
        
        self.running = False
        
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2.0)
        
        self.i2c_interface.cleanup()
        
        logger.info("DisplayController cleanup completed")
    
    def clear(self):
        """Clear the display"""
        self.i2c_interface.clear()
    
    def set_kitchen_radio(self, kitchen_radio: 'KitchenRadio'):
        """Set or update the KitchenRadio instance"""
        self.kitchen_radio = kitchen_radio
        
        # Start update thread if not already running
        if not self.running and kitchen_radio:
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            logger.info("Display update thread started with new KitchenRadio instance")
    
    def request_update(self):
        """Request an immediate display update"""
        self.manual_update_requested = True
    
    # def show_volume_screen(self):
    #     """Show volume screen for 3 seconds (triggered by volume button press)"""
    #     try:
    #         if self.kitchen_radio:
    #             status = self.kitchen_radio.get_status()
    #             current_volume = self._get_current_volume(status)
    #             if current_volume is not None:
    #                 self._show_volume_screen(current_volume)
    #                 logger.info(f"Volume screen displayed manually: {current_volume}%")
    #             else:
    #                 logger.warning("Could not get current volume for volume screen")
    #         else:
    #             logger.warning("No KitchenRadio instance available for volume screen")
    #     except Exception as e:
    #         logger.error(f"Error showing volume screen: {e}")
    
    def _update_loop(self):
        """Main update loop for display refresh"""
        frame_time = 1.0 / self.refresh_rate
        scroll_frame_count = 0
        scroll_frames_per_update = int(self.refresh_rate * 0.5)  # Update scroll every 0.5 seconds
        
        while self.running:
            try:
                start_time = time.time()

                # Update display if KitchenRadio is available
                if self.kitchen_radio:
                    self._update_display()

                # Handle manual update requests
                if self.manual_update_requested:
                    self.manual_update_requested = False
                    # Manual update is handled by the manual methods
                
                # Sleep to maintain refresh rate
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_time - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in display update loop: {e}")
                time.sleep(1.0)  # Wait longer on error
    
    def _update_display(self, force_refresh: bool = False, scroll_update: bool = False):
        """
        Unified display update method that handles both status updates and refresh/scrolling.
        
        Args:
            force_refresh: Force a refresh even if status hasn't changed
            scroll_update: Update is for scrolling (don't fetch new status)
        """
        try:
            # Handle status updates from KitchenRadio
            if self.kitchen_radio:

                current_status = self.kitchen_radio.get_status()
                # Update last volume for tracking
                current_volume = self._get_current_volume(current_status)

                # Determine display content based on current source
                current_source = current_status.get('current_source')
                
                scroll_update = self._is_scroll_update_needed()
                
                overlay_dismissed = self._dismiss_overlay()
           
                # Check for external update of the volume
                if (current_volume != self.last_volume) and self.overlay_active and self.overlay_type == 'volume':
                    self._render_volume_overlay(current_volume)
                    return
                elif self.overlay_active:
                    return

                # Check if status has changed or force refresh
                if not self.overlay_active and ( (current_volume != self.last_volume ) or current_status != self.last_status or overlay_dismissed or  force_refresh ):
                    self.last_status = current_status
                    self.last_volume = current_volume

                    if current_source == 'mpd' and current_status.get('mpd', {}).get('connected'):
                        self._render_mpd_display(current_status['mpd'])
                        return
                    elif current_source == 'librespot' and current_status.get('librespot', {}).get('connected'):
                        self._render_librespot_display(current_status['librespot'])
                        return
                    else:
                        self._render_no_source_display(current_status)
                        return
                # Handle scroll updates - refresh current display with updated scroll offsets
                if not self.current_display_type or not self.current_display_data:
                    return                
                elif scroll_update:
                    # Update scroll offsets in current display data
                    display_data = self.current_display_data.copy()
                    display_data['scroll_offsets'] = self.current_scroll_offsets
                    # Render with appropriate formatter
                    self._render_display_content(self.current_display_type, display_data)
                return         
        except Exception as e:
            logger.error(f"Error updating display: {e}")

    def _is_scroll_update_needed(self) -> bool:
        """Determine if a scroll update is needed based on truncation info"""
        for key, info in self.last_truncation_info.items():
            if info.get('truncated', False):
                return True
        return False
    
    def _render_display_content(self, display_type: str, display_data: Dict[str, Any]):
        """Generic method to render display content based on type"""
        try:
            truncation_info = None
            if display_type == 'track_info':
                draw_func, truncation_info = self.formatter.format_track_info(display_data)
            elif display_type == 'status_message':
                draw_func = self.formatter.format_status_message(display_data)
            elif display_type == 'menu':
                draw_func = self.formatter.format_menu_display(display_data)
            elif display_type == 'volume':
                draw_func = self.formatter.format_volume_display(display_data)
            elif display_type == 'simple_text':
                draw_func = self.formatter.format_simple_text(display_data)
            elif display_type == 'error_message':
                draw_func = self.formatter.format_error_message(display_data)
            elif display_type == 'status':
                draw_func = self.formatter.format_status(display_data)
            else:
                logger.warning(f"Unknown display type: {display_type}")
                return
            
            # Render the display
            if display_type == 'track_info':
                self.i2c_interface.render_frame(draw_func)
                if isinstance(truncation_info, dict):
                    self.last_truncation_info.update(truncation_info)
                    self._update_scroll_offsets(truncation_info)
            else:
                truncation_info = self.i2c_interface.render_frame(draw_func)
                if isinstance(truncation_info, dict):
                    self.last_truncation_info.update(truncation_info)
                    self._update_scroll_offsets(truncation_info)
        except Exception as e:
            logger.error(f"Error rendering {display_type}: {e}")
    
    def _render_mpd_display(self, mpd_status: Dict[str, Any]):
        """Update display for MPD source"""
        current_song = mpd_status.get('current_track', {})
        if current_song:
            title = current_song.get('title', 'Unknown')
            artist = current_song.get('artist', 'Unknown')
            album = current_song.get('album', '')
            playing = mpd_status.get('state') == 'play'
            volume = mpd_status.get('volume', 50)
            
            # Use unified track info formatter without progress bar for MPD
            track_data = {
                'title': current_song.get('title', 'No Track'),
                'artist': current_song.get('artist', 'Unknown'),
                'album': current_song.get('album', 'Unknown'),
                'length': current_song.get('length', 0),
                'time_position': current_song.get('time_position', 0),
                'playing': playing,
                'volume': volume,
                'scroll_offsets': self.current_scroll_offsets
            }
            
            # Track current display state
            self.current_display_type = 'track_info'
            self.current_display_data = track_data
            
            # Render the display content
            self._render_display_content('track_info', track_data)
        else:
            # No track playing
            message_data = {
                'message': 'MPD Connected',
                'icon': '♪',
                'message_type': 'info',
                'scroll_offsets': self.current_scroll_offsets
            }
            
            # Track current display state
            self.current_display_type = 'status_message'
            self.current_display_data = message_data
            
            # Render the display content
            self._render_display_content('status_message', message_data)
    
    def _render_librespot_display(self, librespot_status: Dict[str, Any]):
        """Update display for Spotify/librespot source"""
        current_track = librespot_status.get('current_track', {})
        if current_track:
  
            
            # Use unified track info formatter with progress bar for Spotify
            track_data = {
                'title': current_track.get('title', 'Unknown'),  # Spotify uses 'name' instead of 'title'
                'artist': current_track.get('artist', 'Unknown'),
                'album': current_track.get('album', 'Unknown'),
                'playing': librespot_status.get('state') == 'playing',
                'volume': librespot_status.get('volume', 50),
                'scroll_offsets': self.current_scroll_offsets
            }
            
            # Track current display state
            self.current_display_type = 'track_info'
            self.current_display_data = track_data
            
            # Render the display content
            self._render_display_content('track_info', track_data)
        else:
            # No track playing
            message_data = {
                'message': 'Spotify Connected',
                'icon': '♫',
                'message_type': 'info',
                'scroll_offsets': self.current_scroll_offsets
            }
            
            # Track current display state
            self.current_display_type = 'status_message'
            self.current_display_data = message_data
            
            # Render the display content
            self._render_display_content('status_message', message_data)
    
    def _update_scroll_offsets(self, truncation_info: Dict[str, Any]):
        """Update current scroll offsets based on truncation info using fixed keys"""
        # Initialize scroll offsets for fixed keys
        fixed_keys = ['title', 'artist_album', 'message', 'menu_title']
        
        for key in fixed_keys:
            if key in truncation_info:
                info = truncation_info[key]
                if info['truncated']:
                    # Initialize scroll offset if not already present
                    if key not in self.current_scroll_offsets:
                        self.current_scroll_offsets[key] = 0
                else:
                    # Remove scroll offset if text is not truncated
                    self.current_scroll_offsets.pop(key, None)
            else:
                # Remove scroll offset for keys not in current truncation info
                self.current_scroll_offsets.pop(key, None)



    def _render_no_source_display(self, status: Dict[str, Any]):
        """Update display when no source is active"""
        available_sources = status.get('available_sources', [])
        if available_sources:
            message = f"Available: {', '.join(available_sources)}"
            message_data = {
                'message': message,
                'icon': '♪',
                'message_type': 'info',
                'scroll_offsets': self.current_scroll_offsets
            }
        else:
            message_data = {
                'message': 'No audio sources qdsjfmslqdjfmlqskdjflkdmsqjfmlqsdjsd',
                'icon': '⚠',
                'message_type': 'warning',
                'scroll_offsets': self.current_scroll_offsets
            }
        
        # Track current display state
        self.current_display_type = 'status_message'
        self.current_display_data = message_data
        
        # Render the display content
        self._render_display_content('status_message', message_data)
    
    # Manual display control methods
    
    def show_track_info(self, track, playing: bool = False, volume: int = None):
        """Manually show track information display"""
        try:
            # Extract track info from various input formats
            if isinstance(track, dict):
                title = track.get('title', 'Unknown')
                artist = track.get('artist', 'Unknown')
                album = track.get('album', 'Unknown')
            elif hasattr(track, 'title'):
                title = getattr(track, 'title', 'Unknown')
                artist = getattr(track, 'artist', 'Unknown')
                album = getattr(track, 'album', 'Unknown')
            else:
                title = str(track) if track else 'Unknown'
                artist = 'Unknown'
                album = 'Unknown'
            
            # Use unified track info formatter
            track_data = {
                'title': title,
                'artist': artist,
                'album': album,
                'playing': playing,
                'volume': volume if volume is not None else 50,
                'scroll_offsets': self.current_scroll_offsets
            }
            draw_func, truncation_info = self.formatter.format_track_info(track_data)
            self.i2c_interface.render_frame(draw_func)
            
            # Track current display state
            self.current_display_type = 'track_info'
            self.current_display_data = track_data
            
            # Update truncation info and scroll offsets
            self.last_truncation_info = truncation_info
            self._update_scroll_offsets(truncation_info)
                
        except Exception as e:
            logger.error(f"Error showing track info: {e}")
    
    # def show_volume(self, volume: int, max_volume: int = 100, muted: bool = False, timeout: float = None):
    #     """
    #     Show volume level. If timeout is provided, uses overlay system.
    #     Otherwise shows permanent volume display until manually dismissed.
    #     """
    #     if timeout is not None:
    #         # Use overlay system for temporary volume display
    #         self.show_volume_overlay(volume, timeout)
    #     else:
    #         # Show permanent volume display (backward compatibility)
    #         volume_data = {
    #             'volume': volume,
    #             'max_volume': max_volume,
    #             'title': 'MUTED' if muted else 'VOLUME'
    #         }
            
    #         # Track current display state
    #         self.current_display_type = 'volume'
    #         self.current_display_data = volume_data
            
    #         # Render the display content
    #         self._render_display_content('volume', volume_data)
    
    # def show_menu(self, title: str, options: List[str], selected_index: int = 0, timeout: float = None):
    #     """
    #     Show menu with options. If timeout is provided, uses overlay system.
    #     Otherwise shows permanent menu until manually dismissed.
    #     """
    #     if timeout is not None:
    #         # Use overlay system for temporary menu
    #         self.show_menu_overlay(title, options, selected_index, timeout)
    #     else:
    #         # Show permanent menu (backward compatibility)
    #         menu_data = {
    #             'title': title,
    #             'menu_items': options,
    #             'selected_index': selected_index,
    #             'scroll_offsets': self.current_scroll_offsets
    #         }
            
    #         # Track current display state
    #         self.current_display_type = 'menu'
    #         self.current_display_data = menu_data
            
    #         # Render the display content
    #         self._render_display_content('menu', menu_data)
    
    def show_source_selection(self, sources: List[str], current_source: str, available_sources: List[str]):
        """Manually show source selection"""
        # Use menu display for source selection
        menu_data = {
            'title': 'Select Source',
            'menu_items': sources,
            'selected_index': sources.index(current_source) if current_source in sources else 0
        }
        draw_func = self.formatter.format_menu_display(menu_data)
        self.i2c_interface.render_frame(draw_func)
    
    def show_status_message(self, message: str, icon: str = "ℹ", message_type: str = "info"):
        """Manually show a status message"""
        message_data = {
            'message': message,
            'icon': icon,
            'message_type': message_type
        }
        draw_func, truncation_info = self.formatter.format_status_message(message_data)
        self.i2c_interface.render_frame(draw_func)
        
        # Track current display state
        self.current_display_type = 'status_message'
        self.current_display_data = message_data
        
        self.last_truncation_info.update(truncation_info)
        self._update_scroll_offsets(truncation_info)
    
    def show_clock(self, time_str: str, date_str: str = None):
        """Manually show clock display"""
        # Use simple text display for clock
        text_data = {
            'main_text': time_str,
            'sub_text': date_str if date_str else ''
        }
        draw_func = self.formatter.format_simple_text(text_data)
        self.i2c_interface.render_frame(draw_func)
    
    # Status and information methods
    def get_display_info(self) -> Dict[str, Any]:
        """Get comprehensive display information"""
        i2c_info = self.i2c_interface.get_display_info()
        
        return {
            'i2c_interface': i2c_info,
            'formatter': {
                'width': self.formatter.width,
                'height': self.formatter.height,
                'fonts': list(self.formatter.fonts.keys())
            },
            'controller': {
                'refresh_rate': self.refresh_rate,
                'running': self.running,
                'has_kitchen_radio': self.kitchen_radio is not None
            }
        }
    
    def _get_current_volume(self, status: Dict[str, Any]) -> Optional[int]:
        """Extract current volume from status"""
        try:
            current_source = status.get('current_source')
            
            if current_source == 'mpd' and status.get('mpd', {}).get('connected'):
                return status['mpd'].get('volume')
            elif current_source == 'librespot' and status.get('librespot', {}).get('connected'):
                return status['librespot'].get('volume')
            
            return None
        except Exception as e:
            logger.error(f"Error getting current volume: {e}")
            return None
    
    def _render_volume_overlay(self, volume: int):
        try: 
            volume_data = {
                'volume': volume,
                'max_volume': 100,
                'title': 'VOLUME',
                'show_percentage': True
            }
            # Render the overlay content
            self._render_display_content('volume', volume_data)
            
            logger.debug(f"Render volume overlay for volume: {volume}%")
            
        except Exception as e:
            logger.error(f"Error showing volume overlay: {e}")



    # def _show_overlay(self, overlay_type: str, data: Dict[str, Any], timeout: float = None):
    #     """Show a temporary overlay (volume, menu, etc.)"""
    #     try:
    #         # Activate overlay
    #         self.overlay_active = True
    #         self.overlay_type = overlay_type
    #         self.overlay_end_time = time.time() + (timeout or self.overlay_timeout)
            
    #         # Render the overlay content
    #         self._render_display_content(overlay_type, data)
            
    #         logger.debug(f"Showing {overlay_type} overlay for {timeout or self.overlay_timeout} seconds")
            
    #     except Exception as e:
    #         logger.error(f"Error showing {overlay_type} overlay: {e}")

    # def _show_overlay(self, overlay_type: str, data: Dict[str, Any], timeout: float = None):
    #     """Show a temporary overlay (volume, menu, etc.)"""
    #     try:
    #         # Render the overlay content
    #         self._render_display_content(overlay_type, data)
            
    #         logger.debug(f"Showing {overlay_type} overlay for {timeout or self.overlay_timeout} seconds")
            
    #     except Exception as e:
    #         logger.error(f"Error showing {overlay_type} overlay: {e}")

    # def dismiss_overlay(self):
    #     """Dismiss the current overlay and return to normal display"""
    #     if self.overlay_active:
    #         self.overlay_active = False
    #         self.overlay_type = None
    #         # Force update to return to normal display
    #         self.last_status = None
    #         if self.kitchen_radio:
    #             self._update_display(force_refresh=True)
    #         logger.debug("Overlay dismissed")

    # def extend_overlay_timeout(self, additional_time: float = None):
    #     """Extend the current overlay timeout"""
    #     if self.overlay_active:
    #         extension = additional_time or self.overlay_timeout
    #         self.overlay_end_time = time.time() + extension
    #         logger.debug(f"Extended overlay timeout by {extension} seconds")

    def _activate_overlay(self, overlay_type: str, timeout: float = None):
        """Activate volume overlay state"""
        self.overlay_active = True
        self.overlay_type = overlay_type
        self.overlay_end_time = time.time() + (timeout or self.overlay_timeout)

    def _dismiss_overlay(self):
        # Check if overlay should be dismissed
        if self.overlay_active and time.time() >= self.overlay_end_time:
            if self.overlay_type == 'menu' and self.on_menu_selected:
                self.on_menu_selected(self.selected_index)
            self.overlay_active = False
            self.overlay_type = None
            # Force update to return to normal display
            self.last_status = None
            return True
        return False

    def show_volume_overlay(self, timeout: float = 3):
        volume = self._get_current_volume(self.last_status)
        """Show volume overlay using the generic overlay system"""
        volume_data = {
            'volume': volume,
            'max_volume': 100,
            'title': 'VOLUME',
            'show_percentage': True
        }
        self._render_display_content('volume', volume_data)
        self._activate_overlay('volume', timeout)

    def show_menu_overlay(self, options: List[str], selected_index: int = 0, timeout: float = 3.0, on_selected: Optional[Callable[[int], None]] = None):
        """Show menu overlay using the generic overlay system"""
        menu_data = {
            'title': 'Menu',
            'menu_items': options,
            'selected_index': selected_index,
            'scroll_offsets': self.current_scroll_offsets
        }
        self.on_menu_selected = on_selected
        self.selected_index = selected_index
        self._render_display_content('menu', menu_data)
        self._activate_overlay('menu', timeout)
 
# Example usage and testing
if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create and initialize simplified display controller
    display = DisplayController(
        kitchen_radio=None,  # No KitchenRadio for manual testing
        refresh_rate=1.0
    )
    
    if display.initialize():
        print("✅ Simplified DisplayController initialized successfully")
        
        # Get display info
        info = display.get_display_info()
        print(f"Display: {info['i2c_interface']['width']}x{info['i2c_interface']['height']}")
        print(f"Simulation mode: {info['i2c_interface']['simulation_mode']}")
        
        try:
            test_scenarios = [
                ("Track Info", lambda: display.show_track_info(
                    "Bohemian Rhapsody", "Queen", "A Night at the Opera", True, 85)),
                ("Volume Display", lambda: display.show_volume(75, muted=False)),
                ("Menu Display", lambda: display.show_menu(
                    "Playlists", ["Rock", "Jazz", "Electronic"], 1)),
                ("Status Message", lambda: display.show_status_message(
                    "SSD1322 Ready", "✓", "success")),
                ("Clock Display", lambda: display.show_clock(
                    datetime.now().strftime("%H:%M"), datetime.now().strftime("%Y-%m-%d"))),
            ]
            
            for name, test_func in test_scenarios:
                print(f"Testing {name}...")
                test_func()
                
                # Save screenshot if in simulation mode
                if info['i2c_interface']['simulation_mode']:
                    filename = f"ssd1322_test_{name.lower().replace(' ', '_')}.png"
                    display.save_screenshot(filename)
                    print(f"  Screenshot saved: {filename}")
                
                time.sleep(2)
            
            print("✅ All simplified display tests completed successfully")
            
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            display.cleanup()
    else:
        print("❌ Failed to initialize simplified DisplayController")
        sys.exit(1)
