import logging
from tkinter import S
import traceback
import time
from typing import Optional, Dict, Any, Callable
from enum import Enum

# Import configuration
from kitchenradio import config
from kitchenradio.sources.source_model import TrackInfo, SourceInfo, PlaybackState, PlaybackStatus, SourceType

# Import backends

from kitchenradio.sources.mediaplayer import PlaybackController as MPDController
from kitchenradio.sources.spotify import LibrespotController
from kitchenradio.sources.bluetooth import BluetoothController, BluetoothMonitor


class SourceController:
    """
    Manages all music playback backends and provides unified control interface.
    
    Manages all music playback backends and provides unified control interface.
    
    This class encapsulates all backend-specific logic and provides a clean
    API for playback control, volume management, and source switching.
    """
    
    def __init__(self, config_dict: Dict[str, Any] = None):
        """
        Initialize SourceController with configuration.
        
        Args:
            config_dict: Configuration dictionary. If None, loads from config module.
        """
        self.logger = logging.getLogger(__name__)
        # Enable debug logging to verify display controller receives events
        #self.logger.setLevel(logging.DEBUG)
 
        # Configuration
        self.config = config_dict or self._load_default_config()
        
        # Backend clients and controllers
        self.mpd_client = None
        self.mpd_controller = None
        self.mpd_monitor = None
        self.mpd_connected = False
        
        self.librespot_client = None
        self.librespot_controller = None
        self.librespot_monitor = None
        self.librespot_connected = False
        
        self.bluetooth_bluez_client = None
        self.bluetooth_avrcp_client = None
        self.bluetooth_controller = None
        self.bluetooth_monitor = None
        self.bluetooth_connected = False
        
        # Current active source
        self.source = SourceType.NONE
        self.previous_source = SourceType.NONE
        
        # Power state
        self.powered_on = False
        
        # Callbacks storage
        self._callbacks = {}
        
        self.logger.info("SourceController initialized")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration from config module"""
        return {
            # MPD settings
            'mpd_host': config.MPD_HOST,
            'mpd_port': config.MPD_PORT,
            'mpd_password': config.MPD_PASSWORD,
            'mpd_timeout': config.MPD_TIMEOUT,
            'mpd_default_volume': config.MPD_DEFAULT_VOLUME,
            
            # Librespot settings
            'librespot_host': config.LIBRESPOT_HOST,
            'librespot_port': config.LIBRESPOT_PORT,
            'librespot_timeout': config.MPD_TIMEOUT,
            'librespot_default_volume': config.LIBRESPOT_DEFAULT_VOLUME,
            
            # Bluetooth settings
            'bluetooth_default_volume': config.BLUETOOTH_DEFAULT_VOLUME,
            'bluetooth_pairing_timeout': config.BLUETOOTH_PAIRING_TIMEOUT,
            
            # General settings
            'default_volume': config.MPD_DEFAULT_VOLUME,
            'default_source': config.DEFAULT_SOURCE,
            'power_on_at_startup': config.POWER_ON_AT_STARTUP,
        }
    
    # =========================================================================
    # Backend Initialization
    # =========================================================================
    
    def initialize(self) -> bool:
        """
        Initialize all backends.
        
        Returns:
            True always - controller can operate even if backends unavailable
        """
        self.logger.info("Initializing backends...")
        
        mpd_success = self._initialize_mpd()
        librespot_success = self._initialize_librespot()
        bluetooth_success = self._initialize_bluetooth()
        
        if not mpd_success and not librespot_success and not bluetooth_success:
            self.logger.warning("[!] No backends available - starting in offline mode")
        
        # Log backend status
        if mpd_success:
            self.logger.info("[OK] MPD backend available")
        else:
            self.logger.warning("[X] MPD backend unavailable")
            
        if librespot_success:
            self.logger.info("[OK] Librespot backend available")
        else:
            self.logger.warning("[X] Librespot backend unavailable")
        
        if bluetooth_success:
            self.logger.info("[OK] Bluetooth backend available")
        else:
            self.logger.warning("[X] Bluetooth backend unavailable")
        
        return True
    
    def _initialize_mpd(self) -> bool:
        """Initialize MPD backend"""
        self.logger.info("Initializing MPD backend with retries...")
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.mpd_controller = MPDController(
                    host=self.config.get('mpd_host', config.MPD_HOST),
                    port=self.config.get('mpd_port', config.MPD_PORT),
                    password=self.config.get('mpd_password', config.MPD_PASSWORD),
                    timeout=self.config.get('mpd_timeout', config.MPD_TIMEOUT)
                )
                if self.mpd_controller.connect():
                    self.mpd_client = self.mpd_controller.client
                    self.mpd_monitor = self.mpd_controller.monitor
                    self.mpd_connected = True
                    self.logger.info(f"MPD backend initialized - {self.config['mpd_host']}:{self.config['mpd_port']}")
                    return True
                else:
                    self.logger.warning(f"Failed to connect to MPD (attempt {attempt+1}/{max_retries})")
            except Exception as e:
                self.logger.warning(f"MPD initialization failed (attempt {attempt+1}/{max_retries}): {e}")
            time.sleep(10)  # Wait 10 seconds before retrying
        return False
    
    def _initialize_librespot(self) -> bool:
        """Initialize librespot backend"""
        self.logger.info("Initializing librespot backend...")
        
        try:
            self.librespot_controller = LibrespotController(
                host=self.config.get('librespot_host', config.LIBRESPOT_HOST),
                port=self.config.get('librespot_port', config.LIBRESPOT_PORT),
                timeout=self.config.get('librespot_timeout', config.MPD_TIMEOUT)
            )
            
            if not self.librespot_controller.connect():
                self.logger.warning("Failed to connect to librespot")
                return False
            
            self.librespot_client = self.librespot_controller.client
            self.librespot_monitor = self.librespot_controller.monitor
            self.librespot_connected = True
            
            # Register callbacks for device connection/disconnection
            self.librespot_controller.on_device_connected = self._on_spotify_device_connected
            self.librespot_controller.on_device_disconnected = self._on_spotify_device_disconnected
            
            self.logger.info(f"Librespot backend initialized - {self.config['librespot_host']}:{self.config['librespot_port']}")
            return True
            
        except Exception as e:
            self.logger.warning(f"Librespot initialization failed: {e}")
            return False
    
    def _initialize_bluetooth(self) -> bool:
        """Initialize Bluetooth backend"""
        self.logger.info("Initializing Bluetooth backend...")
        
        # if not BLUETOOTH_AVAILABLE:
        #     self.logger.warning("Bluetooth module not available (Linux only)")
        #     return False
        
        try:
            self.bluetooth_controller = BluetoothController()
            self.bluetooth_monitor = self.bluetooth_controller.monitor
            
            # Register callbacks for device connection events
            self.bluetooth_controller.on_device_connected = self._on_bluetooth_device_connected
            self.bluetooth_controller.on_device_disconnected = self._on_bluetooth_device_disconnected
            
            # Give it time to initialize
            time.sleep(0.5)
            
            self.bluetooth_connected = True
            self.logger.info("Bluetooth backend initialized")
            return True
            
        except Exception as e:
            self.logger.warning(f"Bluetooth initialization failed: {e}")
            return False
    
    def _on_bluetooth_device_connected(self, name: str, address: str):
        """
        Handle Bluetooth device connection event.
        
        Args:
            name: Device name
            address: Device MAC address
        """
        self.logger.info(f"🔵 Bluetooth device connected: {name} ({address})")
        # Emit device_connected event for auto-switching logic
        self._handle_monitor_event(SourceType.BLUETOOTH, 'device_connected', device_name=name, device_address=address)
    
    def _on_bluetooth_device_disconnected(self, name: str, address: str):
        """
        Handle Bluetooth device disconnection event.
        
        Args:
            name: Device name
            address: Device MAC address
        """
        self.logger.info(f"🔴 Bluetooth device disconnected: {name} ({address})")
        # Emit device_disconnected event (but don't auto-switch away from Bluetooth)
        self._handle_monitor_event(SourceType.BLUETOOTH, 'device_disconnected', device_name=name, device_address=address)
    
    def _on_spotify_device_connected(self):
        """
        Handle Spotify device connection event.
        """
        self.logger.info(f"🟢 Spotify device connected")
        # Emit device_connected event
        self._handle_monitor_event(SourceType.LIBRESPOT, 'device_connected')
    
    def _on_spotify_device_disconnected(self):
        """
        Handle Spotify device disconnection event.
        """
        self.logger.info(f"🔴 Spotify device disconnected")
        # Emit device_disconnected event
        self._handle_monitor_event(SourceType.LIBRESPOT, 'device_disconnected')
    
    # =========================================================================
    # Source Management
    # =========================================================================
    
    def get_current_source(self) -> SourceType:
        """Get currently active source"""
        return self.source
    
    def get_available_sources(self) -> list:
        """Get list of available (connected) sources"""
        sources = []
        if self.mpd_connected:
            sources.append(SourceType.MPD)
        if self.librespot_connected:
            sources.append(SourceType.LIBRESPOT)
        if self.bluetooth_connected:
            sources.append(SourceType.BLUETOOTH)
        return sources
    
    def set_source(self, source: SourceType) -> bool:
        """
        Switch to specified source.
        
        Args:
            source: Backend to switch to
            
        Returns:
            True if successful
        """
        # Auto-power on if currently off
        if not self.powered_on:
            self.logger.info("Auto-powering on via source selection...")
            # Pass the requested source as trigger_source to power_on
            self.power_on(trigger_source=source)
            # power_on already sets the source, so return
            return True
        
        self.logger.info(f"Setting audio source to: {source.value}")
        
        # Validate source
        if source not in [SourceType.MPD, SourceType.LIBRESPOT, SourceType.BLUETOOTH, SourceType.NONE]:
            self.logger.error(f"Invalid source: {source}")
            return False
        
        # Store previous source
        previous_source = self.source
        
        # Stop current source if different
        if self.source and self.source != source and self.source != SourceType.NONE:
            self._stop_source(self.source)
        
        # Set new source
        self.source = source
        
        # Handle source-specific logic
        if source == SourceType.BLUETOOTH:
            if not self.bluetooth_connected:
                self.logger.warning(f"Source set to {source.value} but backend is not available")
            elif self.bluetooth_controller:
                if self.bluetooth_controller.is_connected():
                    self.logger.info(f"✅ Active source set to: {source.value} (device connected)")
                else:
                    # Enter pairing mode if BT pressed again while already on BT
                    if previous_source == SourceType.BLUETOOTH:
                        self.logger.info(f"BT button pressed while already on BT - entering pairing mode")
                        self.bluetooth_controller.enter_pairing_mode(timeout_seconds=60)
                    else:
                        self.logger.info(f"✅ Source set to {source.value} - showing disconnected state")
        else:
            # MPD or Librespot - check if connected
            play_started = False
            
            if source == SourceType.MPD and not self.mpd_connected:
                self.logger.warning(f"Source set to {source.value} but backend is not connected")
            elif source == SourceType.LIBRESPOT and not self.librespot_connected:
                self.logger.warning(f"Source set to {source.value} but backend is not connected")
            else:
                self.logger.info(f"✅ Active source set to: {source.value}")
                
                # Start MPD monitoring if switching to MPD source
                if source == SourceType.MPD and self.mpd_monitor and not self.mpd_monitor.is_monitoring:
                    self.logger.info("Starting MPD monitoring for track info")
                    self.mpd_monitor.start_monitoring()
                
            # Auto-play when switching sources
        play_started = False
        try:
            if source == SourceType.MPD:
                # Always start playing when MPD source is selected
                self.logger.info(f"Auto-starting playback on {source.value}")
                play_started = self.play()
            elif source == SourceType.LIBRESPOT:
                self.logger.info(f"Auto-starting playback on {source.value}")
                play_started = self.play()
        except Exception as e:
            self.logger.warning(f"Could not auto-start playback on {source.value}: {e}")
        
        # Trigger update for the new source
        # If we just started playing, add a small delay to let monitor fetch track info
        if play_started:
            time.sleep(0.2)
        
        self._trigger_source_update()
        
        return True
    
    # def switch_to_mpd(self) -> bool:
    #     """Switch to MPD source"""
    #     return self.set_source(SourceType.MPD)
    
    # def switch_to_spotify(self) -> bool:
    #     """Switch to Spotify (librespot) source"""
    #     return self.set_source(SourceType.LIBRESPOT)
    
    # def switch_to_bluetooth(self) -> bool:
    #     """Switch to Bluetooth source"""
    #     return self.set_source(SourceType.BLUETOOTH)
    
    def _stop_source(self, source: SourceType):
        """Stop playback on specified source"""
        self.logger.info(f"Stopping playback on: {source.value}")
        
        try:
            if source == SourceType.MPD and self.mpd_connected and self.mpd_controller:
                self.mpd_controller.stop()
                self.mpd_monitor.stop_monitoring()
                self.logger.info("🛑 Stopped MPD playback")
            elif source == SourceType.LIBRESPOT and self.librespot_connected and self.librespot_controller:
                self.librespot_controller.stop()
                self.logger.info("🛑 Stopped Spotify playback")
            elif source == SourceType.BLUETOOTH and self.bluetooth_connected and self.bluetooth_controller:
                if self.bluetooth_controller.pairing_mode:
                    self.logger.info("Exiting Bluetooth pairing mode (switching sources)")
                    self.bluetooth_controller.exit_pairing_mode()
                if self.bluetooth_controller.is_connected():
                    self.logger.info("Disconnecting Bluetooth device (switching sources)")
                    self.bluetooth_controller.disconnect_current()
        except Exception as e:
            self.logger.warning(f"Error stopping {source.value}: {e}")
    
    def _get_active_controller(self):
        """
        Get controller for currently active source.
        
        Returns:
            Tuple of (controller, source_name, is_connected)
        """
        if self.source == SourceType.MPD:
            return self.mpd_controller, "MPD", self.mpd_connected
        elif self.source == SourceType.LIBRESPOT:
            return self.librespot_controller, "Spotify", self.librespot_connected
        elif self.source == SourceType.BLUETOOTH:
            return self.bluetooth_controller, "Bluetooth", self.bluetooth_connected
        else:
            return None, None, False
    
    # =========================================================================
    # Playback Control
    # =========================================================================
    
    def play(self) -> bool:
        """Start playback on active source"""
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller:
            self.logger.warning("No active source set for play command")
            return False
        
        if not is_connected:
            self.logger.warning(f"Active source {source_name} is not connected")
            return False
        
        try:
            result = controller.play()
            if result:
                self.logger.info(f"▶️ [{source_name}] Playing")
            return result
        except Exception as e:
            self.logger.error(f"Error in play command: {e}\n{traceback.format_exc()}")
            return False
    
    def pause(self) -> bool:
        """Pause playback on active source"""
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller:
            self.logger.warning("No active source set for pause command")
            return False
        
        if not is_connected:
            self.logger.warning(f"Active source {source_name} is not connected")
            return False
        
        try:
            result = controller.pause()
            if result:
                self.logger.info(f"⏸️ [{source_name}] Paused")
            return result
        except Exception as e:
            self.logger.error(f"Error in pause command: {e}\n{traceback.format_exc()}")
            return False
    
    def stop(self) -> bool:
        """Stop playback on active source"""
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller:
            self.logger.warning("No active source set for stop command")
            return False
        
        if not is_connected:
            self.logger.warning(f"Active source {source_name} is not connected")
            return False
        
        try:
            result = controller.stop()
            if result:
                self.logger.info(f"⏹️ [{source_name}] Stopped")
            return result
        except Exception as e:
            self.logger.error(f"Error in stop command: {e}\n{traceback.format_exc()}")
            return False
    
    def play_pause(self) -> bool:
        """Toggle play/pause on active source"""
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller:
            self.logger.warning("No active source set for play/pause command")
            return False
        
        if not is_connected:
            self.logger.warning(f"Active source {source_name} is not connected")
            return False
        
        try:
            result = controller.playpause()
            if result:
                self.logger.info(f"⏯️ [{source_name}] Play/Pause toggled")
            return result
        except Exception as e:
            self.logger.error(f"Error in play/pause command: {e}\n{traceback.format_exc()}")
            return False
    
    def next(self) -> bool:
        """Skip to next track on active source"""
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller:
            self.logger.warning("No active source set for next command")
            return False
        
        if not is_connected:
            self.logger.warning(f"Active source {source_name} is not connected")
            return False
        
        if self.source == SourceType.NONE:
            self.logger.warning("No active source selected for next command")
            return False
        
        try:
            result = controller.next()
            if result:
                self.logger.info(f"⏭️ [{source_name}] Next track")
            return result
        except Exception as e:
            self.logger.error(f"Error in next command: {e}\n{traceback.format_exc()}")
            return False
    
    def previous(self) -> bool:
        """Skip to previous track on active source"""
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller:
            self.logger.warning("No active source set for previous command")
            return False
        
        if not is_connected:
            self.logger.warning(f"Active source {source_name} is not connected")
            return False
        
        if self.source == SourceType.NONE:
            self.logger.warning("No active source selected for previous command")
            return False
        
        try:
            result = controller.previous()
            if result:
                self.logger.info(f"⏮️ [{source_name}] Previous track")
            return result
        except Exception as e:
            self.logger.error(f"Error in previous command: {e}\n{traceback.format_exc()}")
            return False
    
    # =========================================================================
    # Volume Control
    # =========================================================================
    
    def get_volume(self) -> Optional[int]:
        """Get current volume level from active source"""
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller or not is_connected:
            return None
        
        if self.source == SourceType.NONE:
            return None
        
        # Special handling for Bluetooth volume via controller
        if self.source == SourceType.BLUETOOTH and self.bluetooth_controller:
            try:
                return self.bluetooth_controller.get_volume()
            except Exception as e:
                self.logger.error(f"Error getting Bluetooth volume: {e}")
                return None

        try:
            return controller.get_volume()
        except Exception as e:
            self.logger.error(f"Error getting volume: {e}\n{traceback.format_exc()}")
            return None
    
    def set_volume(self, volume: int) -> bool:
        """Set volume on active source"""
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller:
            self.logger.warning("No active source set for volume command")
            return False
        
        if not is_connected:
            self.logger.warning(f"Active source {source_name} is not connected")
            return False
        
        if self.source == SourceType.NONE:
            self.logger.warning("No active source selected for set volume")
            return False
        
        if not 0 <= volume <= 100:
            self.logger.error(f"Invalid volume: {volume}. Must be 0-100")
            return False
        
        # Special handling for Bluetooth volume via controller
        if self.source == SourceType.BLUETOOTH and self.bluetooth_controller:
            try:
                return self.bluetooth_controller.set_volume(volume)
            except Exception as e:
                self.logger.error(f"Error setting Bluetooth volume: {e}")
                return False

        try:
            result = controller.set_volume(volume)
            if result:
                self.logger.info(f"🔊 [{source_name}] Volume set to {volume}%")
            return result
        except Exception as e:
            self.logger.error(f"Error setting volume: {e}")
            return False
    
    def volume_up(self, step: int = 5) -> Optional[int]:
        """Increase volume by step"""
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller or not is_connected:
            return None
        
        if self.source == SourceType.NONE:
            return None
        
        # Special handling for Bluetooth volume via controller
        if self.source == SourceType.BLUETOOTH and self.bluetooth_controller:
            try:
                if self.bluetooth_controller.volume_up(step):
                    # Return new volume if possible
                    return self.bluetooth_controller.get_volume()
                return None
            except Exception as e:
                self.logger.error(f"Error increasing Bluetooth volume: {e}")
                return None

        try:
            new_volume = controller.volume_up(step)
            if new_volume is not None:
                self.logger.info(f"🔊 [{source_name}] Volume up to {new_volume}%")
            return new_volume
        except Exception as e:
            self.logger.error(f"Error increasing volume: {e}")
            return None
    
    def volume_down(self, step: int = 5) -> Optional[int]:
        """Decrease volume by step"""
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller or not is_connected:
            return None
        
        if self.source == SourceType.NONE:
            return None
        
        # Special handling for Bluetooth volume via controller
        if self.source == SourceType.BLUETOOTH and self.bluetooth_controller:
            try:
                if self.bluetooth_controller.volume_down(step):
                    # Return new volume if possible
                    return self.bluetooth_controller.get_volume()
                return None
            except Exception as e:
                self.logger.error(f"Error decreasing Bluetooth volume: {e}")
                return None

        try:
            new_volume = controller.volume_down(step)
            if new_volume is not None:
                self.logger.info(f"🔊 [{source_name}] Volume down to {new_volume}%")
            return new_volume
        except Exception as e:
            self.logger.error(f"Error decreasing volume: {e}")
            return None
    
    # =========================================================================
    # Power Management
    # =========================================================================
    
    def power_on(self, trigger_source: 'SourceType' = None) -> bool:
        """Power on - restore source and start playback. If trigger_source is provided, use it as initial source."""
        if self.powered_on:
            self.logger.info("Already powered on")
            return True

        self.powered_on = True
        self.logger.info("Powering on...")

        # Determine source to use
        source_to_use = None
        if trigger_source is not None:
            source_to_use = trigger_source
            self.logger.info(f"Power-on triggered by source: {source_to_use.value}")
        elif self.previous_source and self.previous_source != SourceType.NONE:
            source_to_use = self.previous_source
            self.logger.info(f"Restoring previous source: {source_to_use.value}")
        else:
            available = self.get_available_sources()
            if available:
                source_to_use = available[0]
                self.logger.info(f"Selecting first available source: {source_to_use.value}")

        # Set source and auto-start playback
        if source_to_use:
            self.set_source(source_to_use)
            try:
                self.logger.info("Auto-starting playback on power on")
                self.play()
            except Exception as e:
                self.logger.warning(f"Could not auto-start playback on power on: {e}")
        else:
            # No sources available, but still allow power on (useful for testing/development)
            self.logger.warning("No sources available for power on - powering on with no source")
            self.source = SourceType.NONE
        
        # Always emit power changed callback
        self._emit_callback('client_changed', 'power_changed', powered_on=True)
        return True
    
    def power_off(self) -> bool:
        """Power off - save source and stop playback"""
        if not self.powered_on:
            self.logger.info("Already powered off")
            return True
        
        self.logger.info("Powering off...")
        
        # Save current source
        if self.source and self.source != SourceType.NONE:
            self.previous_source = self.source
            self.logger.info(f"Saving current source: {self.previous_source.value}")
        
        # Stop all playback
        self._stop_source(SourceType.MPD)
        self._stop_source(SourceType.LIBRESPOT)
        self._stop_source(SourceType.BLUETOOTH)
        
        # Clear source
        self.source = SourceType.NONE
        self.powered_on = False
        
        self._emit_callback('client_changed', 'power_changed', powered_on=False)
        self.logger.info("[OK] Powered off")
        return True
    
    def power(self) -> bool:
        """Toggle power state"""
        if not self.powered_on:
            return self.power_on()
        else:
            return self.power_off()
    
    # =========================================================================
    # Status
    # =========================================================================
    
    def get_playback_state(self, force_refresh: bool = False) -> PlaybackState:
        """
        Get current playback state from active source.
        
        Args:
            force_refresh: If True, fetch fresh state from source instead of cached value
        
        Returns:
            Playback state object
        """
        if self.source == SourceType.MPD and self.mpd_connected and self.mpd_monitor:
            return self.mpd_monitor.get_playback_state(force_refresh=force_refresh)
        elif self.source == SourceType.LIBRESPOT and self.librespot_connected and self.librespot_monitor:
            return self.librespot_monitor.get_playback_state(force_refresh=force_refresh)
        elif self.source == SourceType.BLUETOOTH and self.bluetooth_connected and self.bluetooth_monitor:
            return self.bluetooth_monitor.get_playback_state()
        
        return PlaybackState(status=PlaybackStatus.STOPPED, volume=0)

    def get_track_info(self) -> Optional[TrackInfo]:
        """
        Get current track info from active source.
        
        Returns:
            Track info object or None
        """
        if self.source == SourceType.MPD and self.mpd_connected and self.mpd_monitor:
            return self.mpd_monitor.get_track_info()
        elif self.source == SourceType.LIBRESPOT and self.librespot_connected and self.librespot_monitor:
            return self.librespot_monitor.get_track_info()
        elif self.source == SourceType.BLUETOOTH and self.bluetooth_connected and self.bluetooth_monitor:
            return self.bluetooth_monitor.get_track_info()
            
        return None

    def get_source_info(self) -> SourceInfo:
        """
        Get current source info.
        
        Returns:
            Source info object
        """
        # Get monitor (not controller) for state queries
        monitor = None
        is_connected = False
        if self.source == SourceType.MPD:
            monitor = self.mpd_monitor
            is_connected = self.mpd_connected
        elif self.source == SourceType.LIBRESPOT:
            monitor = self.librespot_monitor
            is_connected = self.librespot_connected
        elif self.source == SourceType.BLUETOOTH:
            monitor = self.bluetooth_monitor
            is_connected = self.bluetooth_connected
        
        if monitor and is_connected:
            info = monitor.get_source_info()
            # Enrich with source type enum and power state
            if isinstance(info, SourceInfo):
                info.source = self.source
                info.power = self.powered_on
            return info
        
        return SourceInfo(source=SourceType.NONE, device_name="Unknown", power=self.powered_on)
    
    def get_menu_options(self) -> Dict[str, Any]:
        """
        Get menu options for current source.
        
        Returns source-specific menu options (e.g., MPD playlists).
        If no source-specific menu is available, returns has_menu=False.
        
        Returns:
            Menu options dict with has_menu and options list
        """
        # For MPD, get playlists as menu options
        if self.source == SourceType.MPD and self.mpd_connected and self.mpd_controller:
            try:
                playlists = self.mpd_controller.get_playlists()
                if playlists:
                    options = [
                        {
                            'id': f'playlist_{i}',
                            'label': playlist,
                            'type': 'playlist',
                            'action': 'load_playlist',
                            'playlist_name': playlist
                        }
                        for i, playlist in enumerate(playlists)
                    ]
                    return {
                        'has_menu': True,
                        'menu_type': 'playlists',
                        'options': options,
                        'message': f'{len(playlists)} playlists available'
                    }
            except Exception as e:
                self.logger.error(f"Error getting MPD playlists: {e}")
        
        # No source-specific menu available
        return {
            'has_menu': False,
            'options': []
        }
    
    def execute_menu_action(self, action: str, option_id: str = None) -> Dict[str, Any]:
        """
        Execute a menu action for the current source.
        
        Args:
            action: Action to perform (e.g., 'load_playlist')
            option_id: Optional ID of the selected option
            
        Returns:
            Result dict with status and message
        """
        try:
            if action == 'load_playlist':
                # Extract playlist name from the current menu options
                menu_options = self.get_menu_options()
                if menu_options.get('has_menu', False):
                    options = menu_options.get('options', [])
                    selected = next((opt for opt in options if opt['id'] == option_id), None)
                    if selected:
                        playlist_name = selected.get('playlist_name')
                        if playlist_name and self.source == SourceType.MPD and self.mpd_controller:
                            # Load and play the playlist
                            success = self.mpd_controller.play_playlist(playlist_name)
                            if success:
                                return {
                                    'status': 'success',
                                    'message': f'Playing: {playlist_name}'
                                }
                            else:
                                return {
                                    'status': 'error',
                                    'message': f'Failed to load playlist'
                                }
            
            return {
                'status': 'error',
                'message': 'Unknown action or invalid state'
            }
            
        except Exception as e:
            self.logger.error(f"Error executing menu action '{action}': {e}")
            return {
                'status': 'error',
                'message': f'Error: {str(e)}'
            }
    
    def _trigger_source_update(self):
        """Fetch current state from active monitor and trigger callbacks"""
        # Get monitor (not controller) for state queries
        monitor = None
        is_connected = False
        if self.source == SourceType.MPD:
            monitor = self.mpd_monitor
            is_connected = self.mpd_connected
        elif self.source == SourceType.LIBRESPOT:
            monitor = self.librespot_monitor
            is_connected = self.librespot_connected
        elif self.source == SourceType.BLUETOOTH:
            monitor = self.bluetooth_monitor
            is_connected = self.bluetooth_connected

        # Default empty state
        playback_state = PlaybackState(status=PlaybackStatus.STOPPED, volume=0)
        track_info = None
        source_info = SourceInfo(source=self.source, device_name="Unknown", power=self.powered_on)

        if monitor and is_connected:
            try:
                playback_state = monitor.get_playback_state()
                track_info = monitor.get_track_info()
                source_info = monitor.get_source_info()
                if isinstance(source_info, SourceInfo):
                    source_info.source = self.source
                    source_info.power = self.powered_on
                elif isinstance(source_info, dict):
                    source_info['source'] = self.source.value
                    source_info['power'] = self.powered_on
            except Exception as e:
                self.logger.error(f"Error fetching state for update: {e}")

        # Emit generic change events
        self._emit_callback('client_changed', 'playback_state_changed', playback_state=playback_state)
        self._emit_callback('client_changed', 'track_changed', track_info=track_info)
        self._emit_callback('client_changed', 'source_info_changed', source_info=source_info)

        # Emit current source and available sources
        current_source = self.get_current_source()
        self._emit_callback('client_changed', 'current_source_changed', current_source=current_source.value if current_source else 'none')

        available_sources = [s.value for s in self.get_available_sources()]
        self._emit_callback('client_changed', 'available_sources_changed', available_sources=available_sources)

    def _handle_monitor_event(self, source_type: SourceType, event_name: str, **kwargs):
        """Handle events from any monitor"""
        # Enhanced debug logging with emoji for easy identification
        emoji = "🔵" if source_type == SourceType.BLUETOOTH else "🟢" if source_type == SourceType.LIBRESPOT else "🎵"
        self.logger.debug(f"{emoji} MONITOR EVENT RECEIVED: source={source_type.value}, event={event_name}, active_source={self.source.value if self.source else 'none'}, kwargs_keys={list(kwargs.keys())}")
        
        # 1. Auto-switching logic
        # Spotify: Auto-switch when playback starts
        if source_type == SourceType.LIBRESPOT and event_name == 'playback_state_changed':
             playback_state = kwargs.get('playback_state')
             # Handle both object and dict for backward compatibility during transition
             is_playing = False
             if isinstance(playback_state, PlaybackState):
                 is_playing = playback_state.status == PlaybackStatus.PLAYING
             elif isinstance(playback_state, dict):
                 is_playing = playback_state.get('status') == 'playing'
                 
             if is_playing:
                 if self.source != SourceType.LIBRESPOT:
                     self.logger.info("Auto-switching to Spotify")
                     self.set_source(SourceType.LIBRESPOT)
                     # set_source triggers update, so we can return or continue. 
                     # If we continue, we might send duplicate events, but that's usually fine.
        
        # Bluetooth: Auto-switch when device connects (but stay on Bluetooth when disconnected)
        if source_type == SourceType.BLUETOOTH and event_name == 'device_connected':
            self.logger.debug(f"🔵 Bluetooth device_connected event detected")
            if self.source != SourceType.BLUETOOTH:
                self.logger.info("🔵 Auto-switching to Bluetooth (device connected)")
                self.set_source(SourceType.BLUETOOTH)
            else:
                self.logger.debug(f"🔵 Already on Bluetooth source, no switch needed")
        
        # 2. Forwarding logic - only if active source
        if self.source == source_type:
            # Forward all events through unified client_changed callback
            self.logger.debug(f"✅ FORWARDING {source_type.value} event '{event_name}' to client_changed callbacks (active source matches)")
            self._emit_callback('client_changed', event_name, **kwargs)
        else:
            self.logger.debug(f"⏸️ NOT forwarding {source_type.value} event '{event_name}' (not active source: current={self.source.value if self.source else 'none'})")

    # =========================================================================
    # Event System
    # =========================================================================

    def add_callback(self, event_name: str, callback: Callable):
        """Add a callback for an event"""
        if event_name not in self._callbacks:
            self._callbacks[event_name] = []
        
        if callback not in self._callbacks[event_name]:
            self._callbacks[event_name].append(callback)
            self.logger.debug(f"Added callback for event: {event_name}")

    def remove_callback(self, event_name: str, callback: Callable):
        """Remove a callback for an event"""
        if event_name in self._callbacks and callback in self._callbacks[event_name]:
            self._callbacks[event_name].remove(callback)
            self.logger.debug(f"Removed callback for event: {event_name}")

    def _emit_callback(self, event_name: str, sub_event: str = None, **kwargs):
        """Emit an event to registered callbacks"""
        # Debug: Show what we're emitting
        event_desc = f"{event_name}" + (f"/{sub_event}" if sub_event else "")
        callback_count = len(self._callbacks.get(event_name, [])) + len(self._callbacks.get('any', []))
        self.logger.debug(f"📤 Emitting callback: {event_desc}, {callback_count} registered callbacks")
        
        # 1. Specific event callbacks
        if event_name in self._callbacks:
            for callback in self._callbacks[event_name]:
                try:
                    if sub_event:
                        # If sub_event provided, pass it (useful for 'client_changed')
                        self.logger.debug(f"  → Calling specific callback with sub_event={sub_event}")
                        callback(event=sub_event, **kwargs)
                    else:
                        self.logger.debug(f"  → Calling specific callback")
                        callback(**kwargs)
                except Exception as e:
                    self.logger.error(f"Error in callback for {event_name}: {e}")
        
        # 2. 'any' event callbacks (catch-all)
        if 'any' in self._callbacks:
            for callback in self._callbacks['any']:
                try:
                    # Pass the event name as 'event' kwarg
                    full_kwargs = kwargs.copy()
                    full_kwargs['event_type'] = event_name
                    if sub_event:
                        full_kwargs['sub_event'] = sub_event
                    
                    callback(**full_kwargs)
                except Exception as e:
                    self.logger.error(f"Error in 'any' callback: {e}")

    # =========================================================================
    # Monitoring
    # =========================================================================
    
    def start_monitoring(self, mpd_state_callback=None, librespot_state_callback=None, on_client_changed=None, on_spotify_track_started=None, bluetooth_callbacks=None):
        """
        Start monitoring for all connected backends.
        
        Args:
            mpd_state_callback: Callback for MPD state changes (legacy, maps to client_changed)
            librespot_state_callback: Callback for Librespot state changes (legacy, maps to client_changed)
            on_client_changed: Callback for any client change
            on_spotify_track_started: Callback for Spotify track started (legacy, maps to client_changed)
            bluetooth_callbacks: Dict with bluetooth callbacks (legacy, maps to client_changed) - DEPRECATED, use on_client_changed instead
        """
        # Register callbacks using unified system
        # All legacy callbacks are mapped to 'client_changed' for consistency
        
        if mpd_state_callback:
            self.add_callback('client_changed', mpd_state_callback)
            
        if librespot_state_callback:
            self.add_callback('client_changed', librespot_state_callback)
            
        if on_client_changed:
            self.add_callback('client_changed', on_client_changed)
            
        if on_spotify_track_started:
            self.add_callback('client_changed', on_spotify_track_started)
            
        if bluetooth_callbacks:
            # DEPRECATED: bluetooth_callbacks dict is now handled through unified client_changed callback
            # For backward compatibility, register the callbacks directly
            self.logger.warning("bluetooth_callbacks dict parameter is deprecated. Use on_client_changed instead.")
            
            # Map old bluetooth callback names to new unified system
            if isinstance(bluetooth_callbacks, dict):
                for event_name, callback in bluetooth_callbacks.items():
                    if callback:
                        # Register as client_changed callback
                        self.add_callback('client_changed', callback)
        
        self.logger.info("Starting monitoring for all backends...")
        
        # Start MPD monitoring
        if self.mpd_connected and self.mpd_monitor:
            # Register SourceController to receive monitor events
            # Monitor passes event='event_name' as kwarg, so extract it
            def mpd_callback(**kwargs):
                event_name = kwargs.pop('event', 'unknown')
                self._handle_monitor_event(SourceType.MPD, event_name, **kwargs)
            self.mpd_monitor.add_callback('any', mpd_callback)
            # only monitor when source = MPD to reduce load
            # self.mpd_monitor.start_monitoring()
            self.logger.info("✅ MPD monitoring started")
            
        # Start Librespot monitoring
        if self.librespot_connected and self.librespot_monitor:
            # Register SourceController to receive monitor events
            # Monitor passes event='event_name' as kwarg, so extract it
            def librespot_callback(**kwargs):
                event_name = kwargs.pop('event', 'unknown')
                self.logger.debug(f"📢 Librespot monitor event: {event_name}, kwargs: {list(kwargs.keys())}")
                self._handle_monitor_event(SourceType.LIBRESPOT, event_name, **kwargs)
            self.librespot_monitor.add_callback('any', librespot_callback)
            self.librespot_monitor.start_monitoring()
            self.logger.info("✅ Librespot monitoring started")
            
        # Start Bluetooth monitoring
        if self.bluetooth_connected and self.bluetooth_monitor:
            # Register SourceController to receive monitor events
            # Monitor passes event='event_name' as kwarg, so extract it
            def bluetooth_callback(**kwargs):
                event_name = kwargs.pop('event', 'unknown')
                self.logger.debug(f"🔵 Bluetooth monitor event received: {event_name}, kwargs: {list(kwargs.keys())}")
                self._handle_monitor_event(SourceType.BLUETOOTH, event_name, **kwargs)
            self.bluetooth_monitor.add_callback('any', bluetooth_callback)
            self.bluetooth_monitor.start_monitoring()
            self.logger.info("✅ Bluetooth monitoring started - callback registered for 'any' event")
