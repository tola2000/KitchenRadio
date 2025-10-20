"""
Simplified Display Controller for SSD1322 256x64 OLED Display

Orchestrates display formatting and I2C hardware interface.
Simplified for KitchenRadio with SSD1322 display only.
"""

import logging
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
        
        # Volume screen state
        self.volume_screen_active = False
        self.volume_screen_end_time = 0
        self.last_volume = None
        self.volume_screen_timeout = 3.0  # 3 seconds
        
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
    
    def show_volume_screen(self):
        """Show volume screen for 3 seconds (triggered by volume button press)"""
        try:
            if self.kitchen_radio:
                status = self.kitchen_radio.get_status()
                current_volume = self._get_current_volume(status)
                if current_volume is not None:
                    self._show_volume_screen(current_volume)
                    logger.info(f"Volume screen displayed manually: {current_volume}%")
                else:
                    logger.warning("Could not get current volume for volume screen")
            else:
                logger.warning("No KitchenRadio instance available for volume screen")
        except Exception as e:
            logger.error(f"Error showing volume screen: {e}")
    
    def _update_loop(self):
        """Main update loop for display refresh"""
        frame_time = 1.0 / self.refresh_rate
        
        while self.running:
            try:
                start_time = time.time()
                
                # Check if volume screen should be dismissed
                if self.volume_screen_active and time.time() >= self.volume_screen_end_time:
                    self.volume_screen_active = False
                    # Force update to return to normal display
                    self.last_status = None
                
                # Update display if KitchenRadio is available
                if self.kitchen_radio:
                    self._update_from_kitchen_radio()
                
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
    
    def _update_from_kitchen_radio(self):
        """Update display based on KitchenRadio status"""
        try:
            status = self.kitchen_radio.get_status()
            
            # Check if status has changed
            if status != self.last_status:
                self.last_status = status
                self._update_display_content(status)
                
        except Exception as e:
            logger.error(f"Error updating from KitchenRadio: {e}")
    
    def _update_display_content(self, status: Dict[str, Any]):
        """Update display content based on status"""
        try:
            # Update last volume for tracking (but don't auto-show volume screen)
            current_volume = self._get_current_volume(status)
            if current_volume is not None:
                self.last_volume = current_volume
            
            # If volume screen is active, keep showing it
            if self.volume_screen_active:
                return
            
            # Normal display logic
            current_source = status.get('current_source')
            
            if current_source == 'mpd' and status.get('mpd', {}).get('connected'):
                self._update_mpd_display(status['mpd'])
            elif current_source == 'librespot' and status.get('librespot', {}).get('connected'):
                self._update_librespot_display(status['librespot'])
            else:
                self._update_no_source_display(status)
                
        except Exception as e:
            logger.error(f"Error updating display content: {e}")
    
    def _update_mpd_display(self, mpd_status: Dict[str, Any]):
        """Update display for MPD source"""
        current_song = mpd_status.get('current_song', {})
        if current_song:
            title = current_song.get('title', 'Unknown')
            artist = current_song.get('artist', 'Unknown')
            album = current_song.get('album', '')
            playing = mpd_status.get('state') == 'play'
            volume = mpd_status.get('volume', 50)
            
            # Use formatter to create draw function
            draw_func = self.formatter.format_track_info(title, artist, album, playing, volume)
            self.i2c_interface.render_frame(draw_func)
        else:
            # No track playing
            draw_func = self.formatter.format_status_message("MPD Connected", "♪", "info")
            self.i2c_interface.render_frame(draw_func)
    
    def _update_librespot_display(self, librespot_status: Dict[str, Any]):
        """Update display for Spotify/librespot source"""
        current_track = librespot_status.get('current_track', {})
        if current_track:
            title = current_track.get('title', 'Unknown')
            artist = current_track.get('artist', 'Unknown')
            album = current_track.get('album', '')
            playing = librespot_status.get('state') == 'playing'
            volume = librespot_status.get('volume', 50)
            
            # Get progress information for Spotify
            progress_ms = librespot_status.get('progress_ms', 0)
            duration_ms = current_track.get('duration_ms', 0)
            
            # Use formatter with progress bar for Spotify
            draw_func = self.formatter.format_track_info_with_progress(
                title, artist, album, playing, volume, progress_ms, duration_ms
            )
            self.i2c_interface.render_frame(draw_func)
        else:
            # No track playing
            draw_func = self.formatter.format_status_message("Spotify Connected", "♫", "info")
            self.i2c_interface.render_frame(draw_func)
    
    def _update_no_source_display(self, status: Dict[str, Any]):
        """Update display when no source is active"""
        available_sources = status.get('available_sources', [])
        if available_sources:
            message = f"Available: {', '.join(available_sources)}"
            draw_func = self.formatter.format_status_message(message, "♪", "info")
        else:
            draw_func = self.formatter.format_status_message("No audio sources", "⚠", "warning")
        
        self.i2c_interface.render_frame(draw_func)
    
    # Manual display control methods
    
    def show_track_info(self, title: str, artist: str, album: str = "", playing: bool = False, volume: int = None):
        """Manually show track information on the display"""
        draw_func = self.formatter.format_track_info(title, artist, album, playing, volume)
        self.i2c_interface.render_frame(draw_func)
    
    def show_volume(self, volume: int, max_volume: int = 100, muted: bool = False):
        """Manually show volume level with progress bar"""
        draw_func = self.formatter.format_volume_display(volume, max_volume, muted)
        self.i2c_interface.render_frame(draw_func)
    
    def show_menu(self, title: str, options: List[str], selected_index: int = 0):
        """Manually show menu with options"""
        draw_func = self.formatter.format_menu_display(title, options, selected_index)
        self.i2c_interface.render_frame(draw_func)
    
    def show_source_selection(self, sources: List[str], current_source: str, available_sources: List[str]):
        """Manually show source selection"""
        draw_func = self.formatter.format_source_display(sources, current_source, available_sources)
        self.i2c_interface.render_frame(draw_func)
    
    def show_status_message(self, message: str, icon: str = "ℹ", message_type: str = "info"):
        """Manually show a status message"""
        draw_func = self.formatter.format_status_message(message, icon, message_type)
        self.i2c_interface.render_frame(draw_func)
    
    def show_clock(self, time_str: str, date_str: str = None):
        """Manually show clock display"""
        draw_func = self.formatter.format_clock_display(time_str, date_str)
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
    
    def _show_volume_screen(self, volume: int):
        """Show temporary volume screen using formatter's full screen display"""
        try:
            # Activate volume screen
            self.volume_screen_active = True
            self.volume_screen_end_time = time.time() + self.volume_screen_timeout
            
            # Use formatter's full screen volume display
            draw_func = self.formatter.format_fullscreen_volume(volume)
            self.i2c_interface.render_frame(draw_func)
            
            logger.debug(f"Volume screen displayed: {volume}%")
            
        except Exception as e:
            logger.error(f"Error showing volume screen: {e}")
    
 
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
