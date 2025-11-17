"""
Simplified Display Controller for SSD1322 256x64 OLED Display

Orchestrates display formatting and I2C hardware interface.
Simplified for KitchenRadio with SSD1322 display only.
"""

import logging
from re import S
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING, Callable

from kitchenradio.radio.kitchen_radio import BackendType

from .display_formatter import DisplayFormatter
from .display_interface import DisplayInterface
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
                 refresh_rate: float = 80,
                 display_interface = None,
                 use_hardware_display: bool = False):
        """
        Initialize simplified display controller for SSD1322.
        
        Args:
            kitchen_radio: KitchenRadio instance for status updates
            i2c_port: I2C port number (ignored if display_interface provided)
            i2c_address: I2C address of the SSD1322 display (ignored if display_interface provided)
            refresh_rate: Display refresh rate in Hz (default: 80 Hz for ultra-smooth pixel scrolling)
            display_interface: Optional external I2C interface (for emulation or custom interface)
            use_hardware_display: Use hardware display if available (when creating interface automatically)
        """
        self.kitchen_radio = kitchen_radio

        self._wake_event = threading.Event()
        

        # Use provided display interface or create new one
        if display_interface:
            self.display_interface = display_interface
            logger.info(f"Using provided display interface")
        else:
            # Create new hybrid interface (auto-selects hardware or emulator)
            self.display_interface = DisplayInterface(use_hardware=use_hardware_display)
            logger.info(f"Created new display interface (use_hardware={use_hardware_display})")

        # Create display formatter for SSD1322
        # Don't override width - let DisplayFormatter use its USABLE_WIDTH default (with margin)
        self.formatter = DisplayFormatter(
            height=self.display_interface.height if hasattr(self.display_interface, 'height') else 64
        )
        
        # Display state
        self.last_status = None
        self.last_powered_on = None  # Track power state separately
        self.refresh_rate = refresh_rate
        self._first_update = True  # Flag to force first display update after initialization
        
        # Track if kitchen_radio has ever been running (to distinguish startup from shutdown)
        self._kitchen_radio_was_running = False
        
        # Current display tracking
        self.current_display_type = None  # 'track_info', 'status_message', 'menu', 'volume', etc.
        self.current_display_data = None  # Last data used to render current display
        
        # Truncation info storage - JSON structure with original strings as keys
        self.last_truncation_info = {}
        self.current_scroll_offsets = {}  # Track current scroll positions for each string
        
        # Scrolling state
        self.scrolling_active = False
        self.scroll_timer = None
        self.scroll_update_interval = 0.2  # Update every 500ms
          # Pause before starting scroll (seconds)
        self.scroll_pause_duration = 2  # Pause 2 seconds at start and when looping back
        # Per-key timestamp (epoch) until which scrolling is paused for that key
        self.scroll_pause_until: Dict[str, float] = {}
      
        # Overlay state (for volume, menu, etc.)
        self.overlay_active = False
        self.overlay_type = None  # 'volume', 'menu', etc.
        self.overlay_end_time = 0
        self.overlay_timeout = 3.0  # 3 seconds default
        self.last_volume = None
        self.last_volume_change_time = 0  # Track when volume was last changed
        self.volume_change_ignore_duration = 1.0  # Ignore status updates for 1 second after volume change

        self.selected_index = 0
        self.on_menu_selected: None

        self.scroll_step = 2  # pixels per update (2 pixels * 80 Hz = 160 pixels/second, 2x faster scrolling)

        # Threading for updates
        self.update_thread = None
        self.running = False
        self.manual_update_requested = False
        self._shutting_down = False  # Flag to prevent any status calls during shutdown
        
        logger.info(f"Simplified DisplayController initialized for SSD1322")
    
    def initialize(self) -> bool:
        """
        Initialize the display controller.
        
        Returns:
            True if initialization successful
        """
        # Initialize display interface if not already initialized
        if not self.display_interface.initialized:
            logger.debug("Display interface not initialized, initializing now")
            if not self.display_interface.initialize():
                logger.error("Failed to initialize display interface")
                return False
        else:
            logger.debug("Display interface already initialized")
        
        # Start update thread if KitchenRadio is provided
        if self.kitchen_radio:
            self.running = True
            self._shutting_down = False  # Clear shutdown flag on initialization
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            logger.info("Display update thread started")
            
            # Trigger initial display update to show current status
            self._wake_event.set()
        
        self.kitchen_radio.add_callback('any', self._on_client_changed)
        logger.info("Simplified DisplayController initialized successfully")
        return True
    
    def _on_client_changed(self, **kwargs):
        # Don't process callbacks during shutdown
        if self._shutting_down:
            return
        try:
            self._wake_event.set()
        except Exception:
            pass

    def cleanup(self):
        """Clean up display resources"""
        logger.info("Display controller cleanup initiated")
        
        # Set shutdown flags
        self._shutting_down = True
        self.running = False
        
        # Remove callback from kitchen_radio
        if self.kitchen_radio:
            try:
                if 'any' in self.kitchen_radio.callbacks:
                    if self._on_client_changed in self.kitchen_radio.callbacks['any']:
                        self.kitchen_radio.callbacks['any'].remove(self._on_client_changed)
            except Exception as e:
                logger.warning(f"Error removing callback: {e}")
        
        # Clear kitchen_radio reference
        self.kitchen_radio = None
        
        # Wake the thread so it can exit
        self._wake_event.set()
        
        # Wait for update thread to stop
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2.0)
            if self.update_thread.is_alive():
                logger.warning("Display update thread did not stop within timeout")
        
        # Reset all display state so next initialization starts fresh
        self.last_status = None
        self.last_powered_on = None
        self.current_display_type = None
        self.current_display_data = None
        self.last_truncation_info = {}
        self.current_scroll_offsets = {}
        self.scroll_pause_until = {}
        self.overlay_active = False
        self.overlay_type = None
        self.overlay_end_time = 0
        self.last_volume = None
        self.selected_index = 0
        self._kitchen_radio_was_running = False
        self._first_update = True  # Force first update after cleanup
        logger.debug("Display state reset to initial values")
        
        # Cleanup display interface
        self.display_interface.cleanup()
        
        logger.info("Display controller cleanup completed")
    
    def clear(self):
        """Clear the display"""
        self.display_interface.clear()
    
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

    def _update_loop(self):
        """Main update loop for display refresh"""
        frame_time = 1.0 / self.refresh_rate
        scroll_frame_count = 0
        scroll_frames_per_update = int(self.refresh_rate * 0.5)  # Update scroll every 0.5 seconds
        
        logger.info("Display update loop started")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Check running flag before doing any work
                if not self.running or self._shutting_down:
                    break

                # Update display if KitchenRadio is available
                if self.kitchen_radio:
                    self._update_display()

                # Handle manual update requests
                if self.manual_update_requested:
                    self.manual_update_requested = False
                    # Manual update is handled by the manual methods
                
                # Check running flag before sleeping
                if not self.running or self._shutting_down:
                    break

                # Calculate sleep time
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_time - elapsed)

                # Wait either for wake_event (set by callback) or timeout
                # This will wake immediately if cleanup() sets the event
                self._wake_event.wait(timeout=sleep_time)
                # Clear wake flag so next wait will block again until next callback
                self._wake_event.clear()
            except Exception as e:
                logger.error(f"Error in display update loop: {e}")
                # Exit loop if shutting down, otherwise continue
                if self._shutting_down or not self.running:
                    logger.info("Exiting update loop due to shutdown after exception")
                    break
                time.sleep(1.0)  # Wait before continuing after error
        
        logger.info("Display update loop exited")
    
    def _update_display(self, force_refresh: bool = False, scroll_update: bool = False):
        """
        Unified display update method that handles both status updates and refresh/scrolling.
        
        Args:
            force_refresh: Force a refresh even if status hasn't changed
            scroll_update: Update is for scrolling (don't fetch new status)
        """
        try:
            # Check if we're shutting down - abort immediately
            if self._shutting_down or not self.running:
                return
                
            # Handle status updates from KitchenRadio
            if self.kitchen_radio:
                # Track if kitchen_radio has been running (to distinguish startup from shutdown)
                if hasattr(self.kitchen_radio, 'running') and self.kitchen_radio.running:
                    self._kitchen_radio_was_running = True
                
                # Auto-cleanup: kitchen_radio stopped after being running -> initiate shutdown
                if (hasattr(self.kitchen_radio, 'running') and 
                    not self.kitchen_radio.running and 
                    self._kitchen_radio_was_running):
                    logger.info("Display controller: kitchen_radio stopped, initiating cleanup")
                    self.cleanup()
                    return
                current_status = self.kitchen_radio.get_status()
                logger.debug("_update_display: get_status() completed")
                # Update last volume for tracking
                current_volume = self._get_current_volume(current_status)

                # Determine display content based on current source
                current_source = current_status.get('current_source')
                current_powered_on = current_status.get('powered_on', False)
                
                # Detect power state change
                power_state_changed = (self.last_powered_on is not None and 
                                      current_powered_on != self.last_powered_on)
                
                if power_state_changed:
                    logger.info(f"Power state transition detected: {self.last_powered_on} -> {current_powered_on}, source: {current_source}")
                
                scroll_update = self._is_scroll_update_needed()
                
                overlay_dismissed = self._dismiss_overlay()
           
                # Check if we should ignore volume updates (recently changed by user)
                time_since_volume_change = time.time() - self.last_volume_change_time
                ignore_volume_updates = time_since_volume_change < self.volume_change_ignore_duration
                
                # Check for external update of the volume
                if (current_volume != self.last_volume) and self.overlay_active and self.overlay_type == 'volume':
                    # Only update if we're not ignoring volume updates
                    if not ignore_volume_updates:
                        self._render_volume_overlay(current_volume)
                        # Update last_volume to prevent continuous re-rendering
                        self.last_volume = current_volume
                        return
                    else:
                        # Ignore this volume update - keep showing user-set volume
                        return
                elif self.overlay_active:
                    return
            
                elif not current_powered_on:
                    # Powered off - show clock and clear display state
                    self.last_powered_on = current_powered_on
                    # Clear display state so next power on shows fresh content
                    self.last_status = None
                    self.current_display_type = None
                    self.current_display_data = None
                    self.last_truncation_info = {}
                    self.current_scroll_offsets = {}
                    self.scroll_pause_until = {}
                    logger.debug("Power OFF - cleared display state")
                    self._render_clock_display()
                    return
                elif current_source == 'none' or current_source is None:
                    self.last_powered_on = current_powered_on
                    self._render_no_source_display(current_status)
                    return
                
                # Check if status has changed or force refresh or first update after initialization or power state changed
                if not self.overlay_active and ( (current_volume != self.last_volume ) or current_status != self.last_status or overlay_dismissed or force_refresh or self._first_update or power_state_changed ):
                    if self._first_update:
                        logger.info("First display update after initialization - forcing render")
                        self._first_update = False
                    if power_state_changed:
                        logger.info(f"Power state changed: {self.last_powered_on} -> {current_powered_on} - forcing render")
                    
                    self.last_status = current_status
                    self.last_volume = current_volume
                    self.last_powered_on = current_powered_on

                    if current_source == 'mpd' and current_status.get('mpd', {}).get('connected'):
                        logger.info(f"Rendering MPD display after status/power change")
                        self._render_mpd_display(current_status['mpd'])
                        return
                    elif current_source == 'librespot':
                        # Render Spotify display regardless of connection status - will show "Niet Actief" if not connected
                        logger.info(f"Rendering Spotify display after status/power change")
                        self._render_librespot_display(current_status.get('librespot', {'connected': False, 'volume': 50, 'current_track': None}))
                        return
                    elif current_source == 'bluetooth':
                        logger.info(f"Rendering Bluetooth display after status/power change")
                        self._render_bluetooth_display(current_status.get('bluetooth', {}))
                        return
                    else:
                        logger.info(f"Rendering no source display after status/power change")
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
        now = time.time()
        any_truncated = False
        for key, info in self.last_truncation_info.items():
            if not info.get('truncated', False):
                # Ensure we don't keep stale pause entries for non-truncated keys
                self.scroll_pause_until.pop(key, None)
                continue

            any_truncated = True
            # Initialize offset if missing
            if key not in self.current_scroll_offsets:
                self.current_scroll_offsets[key] = 0
                # Start pause for newly truncated key
                self.scroll_pause_until[key] = now + self.scroll_pause_duration

        if not any_truncated:
            return False

        advanced = False
        for key, offset in list(self.current_scroll_offsets.items()):
            info = self.last_truncation_info.get(key)
            if not info or not info.get('truncated', False):
                # Remove offsets for keys no longer truncated
                self.current_scroll_offsets.pop(key, None)
                self.scroll_pause_until.pop(key, None)
                continue

            # Adjust scroll speed based on font size (larger fonts scroll faster for same visual speed)
            font_size = info.get('font_size', 'small')
            if font_size == 'xlarge' or font_size == 'xxlarge':
                scroll_step = 6  # Very fast for large text (480 px/s at 80 Hz) - needed for long titles
            elif font_size == 'large':
                scroll_step = 4  # Fast speed (320 px/s at 80 Hz)
            else:
                scroll_step = 2  # Default speed for small/medium (160 px/s at 80 Hz)
            
            pause_until = self.scroll_pause_until.get(key, 0)
            max_scroll = info['original_width'] - info['max_width']
            
            # Check if we're in a pause period
            if now < pause_until:
                # Still in pause - check if we should transition after pause expires
                # This happens on the frame where pause just expired
                if offset >= max_scroll:
                    # We're at the end, waiting for pause to expire to loop back
                    # Don't do anything yet, wait for next frame when now >= pause_until
                    continue
                else:
                    # We're at the start, waiting for pause to expire to start scrolling
                    continue
            
            # Pause has expired, now check position
            if offset >= max_scroll:
                # At the end position, pause has expired - loop back to start
                new_offset = 0
                self.scroll_pause_until[key] = now + self.scroll_pause_duration
                self.current_scroll_offsets[key] = new_offset
                advanced = True
            else:
                # Not at end - normal scrolling
                new_offset = offset + scroll_step
                if new_offset >= max_scroll:
                    # Just reached the end - stay at end position and set end pause
                    new_offset = max_scroll
                    self.scroll_pause_until[key] = now + self.scroll_pause_duration
                    self.current_scroll_offsets[key] = new_offset
                    advanced = True
                else:
                    # Continue scrolling
                    self.current_scroll_offsets[key] = new_offset
                    advanced = True

        return advanced

    def _render_clock_display(self):
        """Update display to show clock in Belgium/Brussels timezone"""
        from zoneinfo import ZoneInfo
        # Get current time in Belgium/Brussels timezone (CET/CEST)
        now = datetime.now(ZoneInfo('Europe/Brussels'))
        clock_data = {
            'time': now.strftime("%H:%M"),
            'date': now.strftime("%Y-%m-%d"),
            'ampm': False,
        }

        self._render_display_content('clock', clock_data)

    def _render_display_content(self, display_type: str, display_data: Dict[str, Any]):
        """Generic method to render display content based on type"""
        try:
            logger.debug(f"Rendering display type: {display_type}")
            truncation_info = None
            draw_func = None
            
            # Get formatter function based on display type
            if display_type == 'track_info':
                draw_func, truncation_info = self.formatter.format_track_info(display_data)
            elif display_type == 'status_message':
                draw_func, truncation_info = self.formatter.format_status_message(display_data)
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
            elif display_type == 'clock':
                draw_func = self.formatter.format_clock_display(display_data)
            elif display_type == 'notification':
                draw_func = self.formatter.format_simple_text(display_data)
            else:
                logger.warning(f"Unknown display type: {display_type}")
                return
            
            # Verify we got a drawing function
            if draw_func is None:
                logger.error(f"No drawing function returned for display type: {display_type}")
                return
            
            # Render the display (render_frame returns None)
            logger.debug(f"Calling render_frame for {display_type}")
            self.display_interface.render_frame(draw_func)
            logger.debug(f"Successfully rendered {display_type}")
            
            # Update truncation info if available (only from track_info and status_message)
            if truncation_info and isinstance(truncation_info, dict):
                self.last_truncation_info.update(truncation_info)
                self._update_scroll_offsets(truncation_info)
                
        except Exception as e:
            logger.error(f"Error rendering {display_type}: {e}", exc_info=True)
    
    def _render_mpd_display(self, mpd_status: Dict[str, Any]):
        """Update display for MPD source"""
        current_song = mpd_status.get('current_track', {})
        logger.debug(f"MPD render - current_song: {current_song}, has_content: {bool(current_song)}")
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
                'source': 'Radio',
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
        volume = librespot_status.get('volume', 50)
        
        if current_track:
            # Use unified track info formatter with progress bar for Spotify
            track_data = {
                'title': current_track.get('title', 'Unknown'),  # Spotify uses 'name' instead of 'title'
                'artist': current_track.get('artist', 'Unknown'),
                'album': current_track.get('album', 'Unknown'),
                'playing': librespot_status.get('state') == 'playing',
                'volume': volume,
                'source': 'Spotify',
                'scroll_offsets': self.current_scroll_offsets
            }
            
            # Track current display state
            self.current_display_type = 'track_info'
            self.current_display_data = track_data
            
            # Render the display content
            self._render_display_content('track_info', track_data)
        else:
            # No track playing - show "Niet Actief" screen in track info format
            display_data = {
                'title': 'Niet Actief',
                'artist': 'Start Spotify stream',
                'album': '',
                'playing': False,
                'pairing_mode': True,  # Use dimmed volume bar and no colon
                'volume': volume,
                'source': 'Spotify',
                'scroll_offsets': self.current_scroll_offsets
            }
            
            # Track current display state
            self.current_display_type = 'track_info'
            self.current_display_data = display_data
            
            # Render the display content
            self._render_display_content('track_info', display_data)
    
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
                       #self.current_scroll_offsets[key] = 0
                       self.current_scroll_offsets[key] = 0
                       # Set initial pause before scrolling begins
                       self.scroll_pause_until[key] = time.time() + self.scroll_pause_duration

                else:
                    # Remove scroll offset if text is not truncated
                    # self.current_scroll_offsets.pop(key, None)
                    self.current_scroll_offsets.pop(key, None)
                    self.scroll_pause_until.pop(key, None)

            else:
                # Remove scroll offset for keys not in current truncation info
                self.current_scroll_offsets.pop(key, None)
                self.scroll_pause_until.pop(key, None)




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
    
    def _render_bluetooth_display(self, bluetooth_status: Dict[str, Any]):
        """Update display for Bluetooth source"""
        is_discoverable = bluetooth_status.get('discoverable', False)
        connected_devices = bluetooth_status.get('connected_devices', [])
        volume = bluetooth_status.get('volume', 50)  # Get Bluetooth volume
        current_track = bluetooth_status.get('current_track')  # Get track info from monitor
        playback_state = bluetooth_status.get('state', 'stopped')
        
        if is_discoverable:
            # Show pairing mode in track info format (no connected device yet)
            if not connected_devices:
                display_data = {
                    'title': 'Koppelen Actief',
                    'artist': 'Koppel Nieuw Toestel',
                    'album': '',
                    'playing': False,  # Use pairing icon instead of play icon
                    'pairing_mode': True,  # Flag for pairing icon
                    'volume': volume,
                    'source': 'Bluetooth',
                    'scroll_offsets': self.current_scroll_offsets
                }
                self.current_display_type = 'track_info'
                self.current_display_data = display_data
                self._render_display_content('track_info', display_data)
            else:
                # Show connected device during pairing mode
                device = connected_devices[0]
                display_data = {
                    'title': device.get('name', 'Unknown Device'),
                    'artist': 'Bluetooth Connected',
                    'album': f"MAC: {device.get('mac', 'Unknown')}",
                    'playing': True,
                    'volume': volume,
                    'source': 'Bluetooth',
                    'scroll_offsets': self.current_scroll_offsets
                }
                self.current_display_type = 'track_info'
                self.current_display_data = display_data
                self._render_display_content('track_info', display_data)
        elif connected_devices:
            # Show track info if available from AVRCP monitor
            if current_track and current_track.get('title') != 'Unknown':
                # Display actual track information from AVRCP
                logger.debug(f"📱 Displaying Bluetooth track: {current_track.get('title')} - {current_track.get('artist')}")
                display_data = {
                    'title': current_track.get('title', 'Unknown'),
                    'artist': current_track.get('artist', 'Unknown'),
                    'album': current_track.get('album', ''),
                    'playing': playback_state == 'playing',
                    'volume': volume,
                    'source': 'Bluetooth',
                    'scroll_offsets': self.current_scroll_offsets
                }
                self.current_display_type = 'track_info'
                self.current_display_data = display_data
                self._render_display_content('track_info', display_data)
            else:
                # No track info available yet - show device ready
                device = connected_devices[0]
                display_data = {
                    'title': device.get('name', 'Unknown Device'),
                    'artist': 'Ready for streaming',
                    'album': '',
                    'playing': False,
                    'pairing_mode': True,  # Use pairing_mode to suppress colon separator
                    'volume': volume,
                    'source': 'Bluetooth',
                    'scroll_offsets': self.current_scroll_offsets
                }
                self.current_display_type = 'track_info'
                self.current_display_data = display_data
                self._render_display_content('track_info', display_data)
        else:
            # No devices connected - show "Niet Verbonden" screen in track info format
            display_data = {
                'title': 'Niet Verbonden',
                'artist': 'Verbind Toestel',
                'album': '',
                'playing': False,
                'pairing_mode': True,  # Use dimmed volume bar and no colon
                'volume': volume,
                'source': 'Bluetooth',
                'scroll_offsets': self.current_scroll_offsets
            }
            self.current_display_type = 'track_info'
            self.current_display_data = display_data
            self._render_display_content('track_info', display_data)
    
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
            self.display_interface.render_frame(draw_func)
            
            # Track current display state
            self.current_display_type = 'track_info'
            self.current_display_data = track_data
            
            # Update truncation info and scroll offsets
            self.last_truncation_info = truncation_info
            self._update_scroll_offsets(truncation_info)
                
        except Exception as e:
            logger.error(f"Error showing track info: {e}")
    
    def show_source_selection(self, sources: List[str], current_source: str, available_sources: List[str]):
        """Manually show source selection"""
        # Use menu display for source selection
        menu_data = {
            'title': 'Select Source',
            'menu_items': sources,
            'selected_index': sources.index(current_source) if current_source in sources else 0
        }
        draw_func = self.formatter.format_menu_display(menu_data)
        self.display_interface.render_frame(draw_func)
    
    def show_status_message(self, message: str, icon: str = "ℹ", message_type: str = "info"):
        """Manually show a status message"""
        message_data = {
            'message': message,
            'icon': icon,
            'message_type': message_type
        }
        draw_func, truncation_info = self.formatter.format_status_message(message_data)
        self.display_interface.render_frame(draw_func)
        
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
        self.display_interface.render_frame(draw_func)
    
    # Status and information methods
    def get_display_info(self) -> Dict[str, Any]:
        """Get comprehensive display information"""
        i2c_info = self.display_interface.get_display_info()
        
        return {
            'display_interface': i2c_info,
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
            elif current_source == 'bluetooth':
                # Get Bluetooth volume from status
                return status.get('bluetooth', {}).get('volume')
            
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
            
            # Update last_volume after successful rendering to prevent re-renders
            self.last_volume = volume
            
            logger.info(f"   Successfully rendered volume overlay: {volume}% (last_volume updated to {volume})")
            
        except Exception as e:
            logger.error(f"Error showing volume overlay: {e}")

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
        """
        Show volume overlay using the generic overlay system.
        
        Gets volume from current status which includes expected values from monitor.
        The monitor immediately provides expected volume values via callbacks,
        ensuring instant UI feedback.
        """
        logger.info(f"📢 show_volume_overlay called, timeout={timeout}")
        
        # Get volume from current status (includes expected values from monitor)
        display_volume = self._get_current_volume(self.last_status)
        logger.info(f"   Volume from status (with expected values): {display_volume}")
        
        # Track volume change time to ignore status updates temporarily
        self.last_volume_change_time = time.time()
        self.last_volume = display_volume
        
        volume_data = {
            'volume': display_volume,
            'max_volume': 100,
            'title': 'VOLUME',
            'show_percentage': True
        }
        self._render_display_content('volume', volume_data)
        self._activate_overlay('volume', timeout)
        logger.info(f"   Volume overlay activated until {self.overlay_end_time}")
        
        # Wake up the display loop to render immediately (no delay)
        self._wake_event.set()

    def show_Notification_overlay(self, title: str, description:str,  timeout: float = 3):
        """Show volume overlay using the generic overlay system"""
        notification_data = {
            'main_text': title,
            'sub_text': description 
        }
        self._render_display_content('notification', notification_data)
        self._activate_overlay('notification', timeout)

    def show_clock(self):
        """Show clock overlay using the generic overlay system"""
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        date_str = now.strftime("%Y-%m-%d")
        clock_data = {
            'main_text': time_str,
            'sub_text': date_str
        }
        self._render_display_content('clock', clock_data)

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
        print(f"Display: {info['display_interface']['width']}x{info['display_interface']['height']}")
        print(f"Simulation mode: {info['display_interface']['simulation_mode']}")
        
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
                if info['display_interface']['simulation_mode']:
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
