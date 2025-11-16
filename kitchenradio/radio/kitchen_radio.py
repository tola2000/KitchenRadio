#!/usr/bin/env python3
"""
KitchenRadio Daemon - Main application daemon
"""

from pickle import NONE
import sys
import os
import time
import signal
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from enum import Enum


# Import both backends
from kitchenradio.mpd import KitchenRadioClient as MPDClient, PlaybackController as MPDController, NowPlayingMonitor as MPDMonitor
from kitchenradio.librespot import KitchenRadioLibrespotClient, LibrespotController, LibrespotMonitor


class BackendType(Enum):
    """Supported backend types"""
    MPD = "mpd"
    LIBRESPOT = "librespot"
    BLUETOOTH = "bluetooth"
    NONE = "none"


class KitchenRadio:
    """
    Main KitchenRadio daemon class.
    
    Manages connections to both music backends (MPD and librespot) simultaneously
    and provides a unified interface for controlling music playback.
    """
    
    def __init__(self):
        """
        Initialize KitchenRadio daemon with both backends.
        """
        self.running = False
        
        # Backend clients and controllers
        self.mpd_client = None
        self.mpd_controller = None
        self.mpd_monitor = None
        self.mpd_connected = False
        
        self.librespot_client = None
        self.librespot_controller = None
        self.librespot_monitor = None
        self.librespot_connected = False
        
        self.bluetooth_controller = None
        self.bluetooth_connected = False

        self.source = None  # Current active source backend
        self.previous_source = None  # Store source before power off
        
        # Monitor threads
        self.mpd_monitor_thread = None
        self.librespot_monitor_thread = None

        self.callbacks = {}

        self.powered_on = False
        
        # Configuration from environment
        self.config = self._load_config()
        
        # Setup logging
        self._setup_logging()
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("KitchenRadio daemon initialized with both MPD and librespot backends")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            # MPD settings
            'mpd_host': os.getenv('MPD_HOST', '192.168.1.4'),
            'mpd_port': int(os.getenv('MPD_PORT', '6600')),
            'mpd_password': os.getenv('MPD_PASSWORD', ''),
            'mpd_timeout': int(os.getenv('MPD_TIMEOUT', '10')),
            
            # Librespot settings
            'librespot_host': os.getenv('LIBRESPOT_HOST', '192.168.1.4'),
            'librespot_port': int(os.getenv('LIBRESPOT_PORT', '3678')),
            'librespot_timeout': int(os.getenv('LIBRESPOT_TIMEOUT', '10')),
            
            # General settings
            'default_volume': int(os.getenv('DEFAULT_VOLUME', '50')),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'debug': os.getenv('DEBUG', 'false').lower() == 'true',
            'dev_mode': os.getenv('DEV_MODE', 'false').lower() == 'true',
        }
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config['log_level'].upper(), logging.INFO)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('kitchenradio.log') if not self.config['debug'] else logging.NullHandler()
            ]
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger = logging.getLogger(__name__)
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
    
    def _initialize_backends(self) -> bool:
        """
        Initialize all backends.
        
        Returns:
            Always True - daemon can start even if backends are unavailable
        """
        mpd_success = self._initialize_mpd()
        librespot_success = self._initialize_librespot()
        bluetooth_success = self._initialize_bluetooth()
        
        if not mpd_success and not librespot_success and not bluetooth_success:
            self.logger.warning("⚠️  No backends available - daemon starting in offline mode")
            self.logger.info("   Backends can be connected later when services are available")
        
        if mpd_success:
            self.logger.info("✅ MPD backend available")
        else:
            self.logger.warning("❌ MPD backend unavailable")
            
        if librespot_success:
            self.logger.info("✅ Librespot backend available")
        else:
            self.logger.warning("❌ Librespot backend unavailable")
        
        if bluetooth_success:
            self.logger.info("✅ Bluetooth backend available")
        else:
            self.logger.warning("❌ Bluetooth backend unavailable")
        
        # Always return True - daemon can start without backends
        return True
    
    def _initialize_mpd(self) -> bool:
        """Initialize MPD backend"""
        self.logger.info("Initializing MPD backend...")
        
        try:
            self.mpd_client = MPDClient(
                host=self.config['mpd_host'],
                port=self.config['mpd_port'],
                password=self.config['mpd_password'],
                timeout=self.config['mpd_timeout']
            )
            
            if not self.mpd_client.connect():
                self.logger.warning("Failed to connect to MPD")
                return False
            
            self.mpd_controller = MPDController(self.mpd_client)
            self.mpd_monitor = MPDMonitor(self.mpd_client)
            self.mpd_connected = True
            
            self.mpd_monitor.add_callback('any', self._on_client_changed)
            
            self.logger.info(f"MPD backend initialized successfully - {self.config['mpd_host']}:{self.config['mpd_port']}")
            return True
            
        except Exception as e:
            self.logger.warning(f"MPD initialization failed: {e}")
            return False
    
    def _initialize_librespot(self) -> bool:
        """Initialize librespot backend"""
        self.logger.info("Initializing librespot backend...")
        
        try:
            self.librespot_client = KitchenRadioLibrespotClient(
                host=self.config['librespot_host'],
                port=self.config['librespot_port'],
                timeout=self.config['librespot_timeout']
            )
            
            if not self.librespot_client.connect():
                self.logger.warning("Failed to connect to librespot")
                return False
            
            self.librespot_controller = LibrespotController(self.librespot_client)
            self.librespot_monitor = LibrespotMonitor(self.librespot_client)
            self.librespot_connected = True

            self.librespot_monitor.add_callback('any', self._on_client_changed)
            
            self.logger.info(f"Librespot backend initialized successfully - {self.config['librespot_host']}:{self.config['librespot_port']}")
            return True
            
        except Exception as e:
            self.logger.warning(f"Librespot initialization failed: {e}")
            return False
    
    def _initialize_bluetooth(self) -> bool:
        """Initialize Bluetooth backend"""
        self.logger.info("Initializing Bluetooth backend...")
        
        try:
            from kitchenradio.bluetooth import BluetoothController
            
            self.bluetooth_controller = BluetoothController()
            
            # Set up callbacks
            self.bluetooth_controller.on_device_connected = self._on_bluetooth_connected
            self.bluetooth_controller.on_device_disconnected = self._on_bluetooth_disconnected
            
            # Give it time to initialize
            import time
            time.sleep(1)
            
            if not self.bluetooth_controller.running:
                self.logger.warning("Bluetooth controller failed to start")
                return False
            
            self.bluetooth_connected = True
            self.logger.info("Bluetooth backend initialized successfully")
            return True
            
        except Exception as e:
            self.logger.warning(f"Bluetooth initialization failed: {e}")
            return False
    
    def _on_bluetooth_connected(self, name: str, mac: str):
        """Handle Bluetooth device connection"""
        self.logger.info(f"🔵 Bluetooth device connected: {name} ({mac})")
        
        # Auto-switch to Bluetooth source if not already
        if self.source != BackendType.BLUETOOTH:
            self.logger.info("Auto-switching to Bluetooth source")
            self.set_source(BackendType.BLUETOOTH)
    
    def _on_bluetooth_disconnected(self, name: str, mac: str):
        """Handle Bluetooth device disconnection"""
        self.logger.info(f"🔴 Bluetooth device disconnected: {name} ({mac})")
        
        # Switch to previous source if we were on Bluetooth
        if self.source == BackendType.BLUETOOTH:
            self.logger.info("Bluetooth disconnected, switching to MPD source")
            self.set_source(BackendType.MPD)

    def add_callback(self, event: str, callback: Callable):
        """
        Add callback for specific event.
        
        Args:
            event: Event name (track_started, track_paused, track_resumed, track_ended, volume_changed, state_changed)
            callback: Callback function
        """
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
        self.logger.debug(f"Added callback for {event}")

    def _on_client_changed(self, **kwargs):
        # Remove 'event' from kwargs if present to avoid conflict
        callback_kwargs = {k: v for k, v in kwargs.items() if k != 'event'}
        self._trigger_callbacks(event='any', **callback_kwargs)

    def _trigger_callbacks(self, event: str, **kwargs):
        """Trigger callbacks for event."""

        for callback in self.callbacks['any']:
            try:
                callback(**kwargs)
            except Exception as e:
                self.logger.error(f"Error in 'any' callback for {event}: {e}")

        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(**kwargs)
                except Exception as e:
                    self.logger.error(f"Error in callback for {event}: {e}")


    def _on_mpd_track_change(self, current_track, last_track):
        """Handle MPD track change events"""
        if current_track:
            title = current_track.get('title', current_track.get('file', 'Unknown'))
            artist = current_track.get('artist', 'Unknown')
            album = current_track.get('album', 'Unknown')
            self.logger.info(f"🎵 [MPD] Now playing: {artist} - {title} ({album})")
        else:
            self.logger.info("🔇 [MPD] No track playing")
    
    def _on_mpd_state_change(self, current_state, last_state):
        """Handle MPD playback state change events"""
        state_icons = {
            'play': '▶️',
            'pause': '⏸️',
            'stop': '⏹️'
        }
        
        icon = state_icons.get(current_state, '❓')
        self.logger.info(f"{icon} [MPD] State changed to: {current_state}")
    
    def _on_mpd_volume_change(self, current_volume, last_volume):
        """Handle MPD volume change events"""
        if current_volume is not None and last_volume is not None:
            self.logger.info(f"🔊 [MPD] Volume changed: {last_volume}% → {current_volume}%")
    
    def _on_librespot_track_change(self, current_track, last_track):
        """Handle librespot track change events"""
        if current_track:
            title = current_track.get('name', 'Unknown')
            artists = current_track.get('artists', [])
            artist = ", ".join([a.get('name', 'Unknown') for a in artists]) if artists else 'Unknown'
            album = current_track.get('album', {}).get('name', 'Unknown')
            self.logger.info(f"🎵 [Spotify] Now playing: {artist} - {title} ({album})")
        else:
            self.logger.info("🔇 [Spotify] No track playing")
    
    def _on_librespot_state_change(self, current_state, last_state):
        """Handle librespot playback state change events"""
        state_icons = {
            'Playing': '▶️',
            'Paused': '⏸️',
            'Stopped': '⏹️'
        }
        
        icon = state_icons.get(current_state, '❓')
        self.logger.info(f"{icon} [Spotify] State changed to: {current_state}")
    
    def _on_librespot_volume_change(self, current_volume, last_volume):
        """Handle librespot volume change events"""
        if current_volume is not None and last_volume is not None:
            self.logger.info(f"🔊 [Spotify] Volume changed: {last_volume}% → {current_volume}%")
    
    def _on_mpd_state_changed(self, **kwargs):
        """
        Handle MPD state changed events from monitor callback.
        
        Args:
            **kwargs: Event data containing new_state, old_state, etc.
        """
        new_state = kwargs.get('new_state', 'unknown')
        old_state = kwargs.get('old_state', 'unknown')
        
        state_icons = {
            'play': '▶️',
            'pause': '⏸️',
            'stop': '⏹️'
        }
        
        icon = state_icons.get(new_state, '❓')
        self.logger.info(f"{icon} [MPD] State changed: {old_state} → {new_state}")
        
        # If source switching is enabled, handle exclusive playback
        # Don't auto-switch if Bluetooth is already active (to avoid interrupting Bluetooth audio)
        if new_state == 'play' and self.source != BackendType.BLUETOOTH:
            self.set_source(BackendType.MPD)
           
    
    def _on_librespot_state_changed(self, **kwargs):
        """
        Handle librespot state changed events from monitor callback.
        
        Args:
            **kwargs: Event data containing new_state, old_state, etc.
        """
        new_state = kwargs.get('new_state', 'unknown')
        old_state = kwargs.get('old_state', 'unknown')
        
        state_icons = {
            'Playing': '▶️',
            'Paused': '⏸️',
            'Stopped': '⏹️'
        }
        
        icon = state_icons.get(new_state, '❓')
        self.logger.info(f"{icon} [Spotify] State changed: {old_state} → {new_state}")
        
        # If source switching is enabled, handle exclusive playback
        # Don't auto-switch if Bluetooth is already active (to avoid interrupting Bluetooth audio)
        if new_state == 'play' and self.source != BackendType.BLUETOOTH:
            self.set_source(BackendType.LIBRESPOT)
    
    def get_current_source(self) -> Optional[BackendType]:
        """
        Get the currently active audio source.
        
        Returns:
            Current source or None if no source is active
        """
        return self.source
    
    def get_available_sources(self) -> list[BackendType]:
        """
        Get list of available (connected) audio sources.
        
        Returns:
            List of available backend types
        """
        sources = []
        if self.mpd_connected:
            sources.append(BackendType.MPD)
        if self.librespot_connected:
            sources.append(BackendType.LIBRESPOT)
        return sources
    
    def _stop_source(self, source: BackendType):
        """
        Stop playback on the specified source.
        
        Args:
            source: Backend type to stop
        """
        self.logger.info(f"Stopping playback on: {source.value}")
        
        try:
            if source == BackendType.MPD and self.mpd_connected:
                self.mpd_controller.stop()
                self.logger.info("🛑 Stopped MPD playback")
                
            elif source == BackendType.LIBRESPOT and self.librespot_connected:
                self.librespot_controller.stop()
                self.logger.info("🛑 Stopped Spotify playback")
            
            elif source == BackendType.BLUETOOTH and self.bluetooth_connected:
                if self.bluetooth_controller and self.bluetooth_controller.is_connected():
                    self.bluetooth_controller.disconnect_current()
                    self.logger.info("🛑 Disconnected Bluetooth device")
                
        except Exception as e:
            self.logger.warning(f"Error stopping {source.value}: {e}")
    
    def switch_to_mpd(self) -> bool:
        """
        Switch active source to MPD.
        
        Returns:
            True if successful
        """
        return self.set_source(BackendType.MPD)
    
    def switch_to_spotify(self) -> bool:
        """
        Switch active source to Spotify (librespot).
        
        Returns:
            True if successful
        """
        return self.set_source(BackendType.LIBRESPOT)

    # Helper method for getting active controller
    def _get_active_controller(self):
        """
        Get the controller for the currently active source.
        
        Returns:
            Tuple of (controller, source_name, is_connected) or (None, None, False) if no active source
        """
        if not self.source:
            return None, None, False
        
        if self.source == BackendType.MPD:
            return self.mpd_controller, "MPD", self.mpd_connected
        elif self.source == BackendType.LIBRESPOT:
            return self.librespot_controller, "Spotify", self.librespot_connected
        elif self.source == BackendType.BLUETOOTH:
            return self.bluetooth_controller, "Bluetooth", self.bluetooth_connected
        else:
            return None, None, False

    # Playback control methods for active source
    def play_pause(self) -> bool:
        """
        Toggle play/pause on the currently active source.
        
        Returns:
            True if successful, False if no active source or command failed
        """
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
                self.logger.info(f"▶️ [{source_name}] Started playback")
            return result
                
        except Exception as e:
            self.logger.error(f"Error in play/pause command on {source_name}: {e}")
            return False
    
    
    def _power_on(self) -> bool:
        """Power on the KitchenRadio daemon, restore previous source, and start playback"""
        if not self.powered_on:
            self.powered_on = True
            
            # Determine which source to use
            source_to_use = None
            if self.previous_source and self.previous_source != BackendType.NONE:
                # Restore previous source if available
                source_to_use = self.previous_source
                self.logger.info(f"Restoring previous source: {source_to_use.value}")
            else:
                # No previous source - select first available backend
                available_sources = self.get_available_sources()
                if available_sources:
                    source_to_use = available_sources[0]
                    self.logger.info(f"No previous source, selecting first available: {source_to_use.value}")
            
            # Set source and start playback if we have one
            if source_to_use:
                self._set_source(source_to_use)
                # Start playback after setting source
                try:
                    self.logger.info(f"Auto-starting playback on power on")
                    self.play()
                except Exception as e:
                    self.logger.warning(f"Could not auto-start playback on power on: {e}")
            else:
                self.logger.warning("No sources available to power on")
                
        return True
    
    def _power_off(self) -> bool:
        """Power off the KitchenRadio daemon and save current source"""
        if self.powered_on:
            # Save current source before powering off (but not NONE)
            if self.source and self.source != BackendType.NONE:
                self.previous_source = self.source
                self.logger.info(f"Saving current source for next power on: {self.previous_source.value}")
            
            self.powered_on = False
            self._stop_source(BackendType.MPD)
            self._stop_source(BackendType.LIBRESPOT)
            
            # Disconnect Bluetooth if connected
            if self.bluetooth_controller and self.bluetooth_controller.is_connected():
                self.logger.info("Disconnecting Bluetooth device (power off)")
                self.bluetooth_controller.disconnect_current()
            
            self._set_source(BackendType.NONE)
        return True    

    def power(self):
        if not self.powered_on:
            return self._power_on()
        else:
            return self._power_off()
    
    def play(self) -> bool:
        """
        Start playback on the currently active source.
        
        Returns:
            True if successful, False if no active source or command failed
        """
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
                self.logger.info(f"▶️ [{source_name}] Started playback")
            return result
                
        except Exception as e:
            self.logger.error(f"Error in play command on {source_name}: {e}")
            return False
    
    def pause(self) -> bool:
        """
        Pause playback on the currently active source.
        
        Returns:
            True if successful, False if no active source or command failed
        """
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
                self.logger.info(f"⏸️ [{source_name}] Paused playback")
            return result
                
        except Exception as e:
            self.logger.error(f"Error in pause command on {source_name}: {e}")
            return False
    
    def stop_play(self) -> bool:
        """
        Stop playback on the currently active source.
        
        Returns:
            True if successful, False if no active source or command failed
        """
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
                self.logger.info(f"⏹️ [{source_name}] Stopped playback")
            return result
                
        except Exception as e:
            self.logger.error(f"Error in stop command on {source_name}: {e}")
            return False
    
    def next(self) -> bool:
        """
        Skip to next track on the currently active source.
        
        Returns:
            True if successful, False if no active source or command failed
        """
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller:
            self.logger.warning("No active source set for next command")
            return False
        
        if not is_connected:
            self.logger.warning(f"Active source {source_name} is not connected")
            return False

        if self.source == BackendType.NONE:
            self.logger.warning(f"No active source selected for next command")
            return False

        try:
            result = controller.next()
            if result:
                self.logger.info(f"⏭️ [{source_name}] Skipped to next track")
            return result
                
        except Exception as e:
            self.logger.error(f"Error in next command on {source_name}: {e}")
            return False
    
    def previous(self) -> bool:
        """
        Skip to previous track on the currently active source.
        
        Returns:
            True if successful, False if no active source or command failed
        """
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller:
            self.logger.warning("No active source set for previous command")
            return False
        
        if not is_connected:
            self.logger.warning(f"Active source {source_name} is not connected")
            return False

        if self.source == BackendType.NONE:
            self.logger.warning(f"No active source selected for next command")
            return False
               
        try:
            result = controller.previous()
            if result:
                self.logger.info(f"⏮️ [{source_name}] Skipped to previous track")
            return result
                
        except Exception as e:
            self.logger.error(f"Error in previous command on {source_name}: {e}")
            return False

    # Volume control methods for active source
    def set_volume(self, volume: int) -> bool:
        """
        Set volume level on the currently active source.
        
        Args:
            volume: Volume level (0-100)
            
        Returns:
            True if successful, False if no active source or command failed
        """
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller:
            self.logger.warning("No active source set for volume command")
            return False
        
        if not is_connected:
            self.logger.warning(f"Active source {source_name} is not connected")
            return False

        if self.source == BackendType.NONE:
            self.logger.warning(f"No active source selected for next command")
            return False
               
        # Validate volume range
        if not 0 <= volume <= 100:
            self.logger.error(f"Invalid volume level: {volume}. Must be 0-100")
            return False
        
        try:
            result = controller.set_volume(volume)
            if result:
                self.logger.info(f"🔊 [{source_name}] Volume set to {volume}%")
            return result
                
        except Exception as e:
            self.logger.error(f"Error setting volume on {source_name}: {e}")
            return False
    
    def get_volume(self) -> Optional[int]:
        """
        Get current volume level from the currently active source.
        
        Returns:
            Volume level (0-100) or None if no active source or command failed
        """
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller:
            self.logger.warning("No active source set for get volume command")
            return None
        
        if not is_connected:
            self.logger.warning(f"Active source {source_name} is not connected")
            return None
        
        if self.source == BackendType.NONE:
            self.logger.warning(f"No active source selected for next command")
            return False

        try:
            volume = controller.get_volume()
            return volume
                
        except Exception as e:
            self.logger.error(f"Error getting volume from {source_name}: {e}")
            return None
    
    def volume_up(self, step: int = 5) -> bool:
        """
        Increase volume by specified step on the currently active source.
        
        Args:
            step: Volume increase step (default 5)
            
        Returns:
            True if successful, False if no active source or command failed
        """
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller:
            self.logger.warning("No active source set for volume up command")
            return False
        
        if not is_connected:
            self.logger.warning(f"Active source {source_name} is not connected")
            return False
        
        if self.source == BackendType.NONE:
            self.logger.warning(f"No active source selected for next command")
            return False
               
        try:
            result = controller.volume_up(step)
            if result:
                self.logger.info(f"🔊 [{source_name}] Volume increased by {step}%")
            return result
                
        except Exception as e:
            self.logger.error(f"Error increasing volume on {source_name}: {e}")
            return False
    
    def volume_down(self, step: int = 5) -> bool:
        """
        Decrease volume by specified step on the currently active source.
        
        Args:
            step: Volume decrease step (default 5)
            
        Returns:
            True if successful, False if no active source or command failed
        """
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller:
            self.logger.warning("No active source set for volume down command")
            return False
        
        if not is_connected:
            self.logger.warning(f"Active source {source_name} is not connected")
            return False
        
        if self.source == BackendType.NONE:
            self.logger.warning(f"No active source selected for next command")
            return False       
        try:
            result = controller.volume_down(step)
            if result:
                self.logger.info(f"🔊 [{source_name}] Volume decreased by {step}%")
            return result
                
        except Exception as e:
            self.logger.error(f"Error decreasing volume on {source_name}: {e}")
            return False

    def start(self) -> bool:
        """
        Start the KitchenRadio daemon.
        
        Returns:
            True if started successfully, False otherwise
        """
        self.logger.info("Starting KitchenRadio daemon...")
        
        # Initialize both backends
        if not self._initialize_backends():
            return False
        
        # Set initial volume if specified
        if self.config['default_volume'] > 0:
            if self.mpd_connected:
                try:
                    self.mpd_controller.set_volume(self.config['default_volume'])
                    self.logger.info(f"Set MPD initial volume to {self.config['default_volume']}%")
                except Exception as e:
                    self.logger.warning(f"Failed to set MPD initial volume: {e}")
            
            if self.librespot_connected:
                try:
                    self.librespot_controller.set_volume(self.config['default_volume'])
                    self.logger.info(f"Set librespot initial volume to {self.config['default_volume']}%")
                except Exception as e:
                    self.logger.warning(f"Failed to set librespot initial volume: {e}")
        
        # Start monitoring for available backends (always, regardless of volume setting)
        if self.mpd_connected:
            try:
                # Add state change listener before starting monitoring
                self.mpd_monitor.add_callback('state_changed', self._on_mpd_state_changed)
                self.mpd_monitor.start_monitoring()
                self.logger.info(f"Started MPD monitoring with state change listener")
            except Exception as e:
                self.logger.warning(f"Failed to start MPD monitoring: {e}")
        
        if self.librespot_connected:
            try:
                # Add state change listener before starting monitoring
                self.librespot_monitor.add_callback('state_changed', self._on_librespot_state_changed)
                self.librespot_monitor.start_monitoring()
                self.logger.info(f"Started Librespot monitoring with state change listener")
            except Exception as e:
                self.logger.warning(f"Failed to start librespot monitoring: {e}")
        
        # Start monitoring
        self.running = True
        
        # # Start MPD monitor if connected
        # if self.mpd_connected:
        #     self.mpd_monitor_thread = threading.Thread(target=self._mpd_monitor_loop, daemon=True)
        #     self.mpd_monitor_thread.start()
        
        # # Start librespot monitor if connected
        # if self.librespot_connected:
        #     self.librespot_monitor_thread = threading.Thread(target=self._librespot_monitor_loop, daemon=True)
        #     self.librespot_monitor_thread.start()
        
        self.logger.info("KitchenRadio daemon started successfully")
        return True
    
    def stop(self):
        """Stop the KitchenRadio daemon"""
        self.logger.info("Stopping KitchenRadio daemon...")
        
        # Stop monitoring FIRST (sets stop event so monitors won't try to reconnect)
        self.running = False
        
        # Stop monitor instances (sets their _stop_event)
        if self.mpd_monitor:
            try:
                self.mpd_monitor.stop_monitoring()
                self.logger.info("Stopped MPD monitor")
            except Exception as e:
                self.logger.warning(f"Error stopping MPD monitor: {e}")
        
        if self.librespot_monitor:
            try:
                self.librespot_monitor.stop_monitoring()
                self.logger.info("Stopped librespot monitor")
            except Exception as e:
                self.logger.warning(f"Error stopping librespot monitor: {e}")
        
        # Wait for monitor threads to finish (should exit quickly now)
        if self.mpd_monitor_thread and self.mpd_monitor_thread.is_alive():
            self.mpd_monitor_thread.join(timeout=5)
        
        if self.librespot_monitor_thread and self.librespot_monitor_thread.is_alive():
            self.librespot_monitor_thread.join(timeout=5)
        
        # Disconnect from backends (monitors are stopped, so no reconnect attempts)
        if self.mpd_client and self.mpd_connected:
            try:
                self.mpd_client.disconnect()
                self.logger.info("Disconnected from MPD")
            except Exception as e:
                self.logger.warning(f"Error disconnecting from MPD: {e}")
        
        if self.librespot_client and self.librespot_connected:
            try:
                self.librespot_client.disconnect()
                self.logger.info("Disconnected from librespot")
            except Exception as e:
                self.logger.warning(f"Error disconnecting from librespot: {e}")
        
        # Cleanup Bluetooth
        if self.bluetooth_controller and self.bluetooth_connected:
            try:
                self.bluetooth_controller.cleanup()
                self.logger.info("Bluetooth controller cleaned up")
            except Exception as e:
                self.logger.warning(f"Error cleaning up Bluetooth: {e}")
        
        self.logger.info("KitchenRadio daemon stopped")
    

    def set_source(self, source: BackendType) -> bool:
        if not self.powered_on:
            # Power on without auto-selecting a source
            self.powered_on = True
            self.logger.info(f"Powered on via source selection: {source.value}")
        return self._set_source(source)


    # Source management methods
    def _set_source(self, source: BackendType) -> bool:
        """
        Set the active audio source, stopping the currently active one.
        
        Args:
            source: Backend type to activate (MPD or LIBRESPOT)
            
        Returns:
            True if source was set successfully
        """


        self.logger.info(f"Setting audio source to: {source.value}")
        
        # Validate source
        if source not in [BackendType.MPD, BackendType.LIBRESPOT, BackendType.BLUETOOTH, BackendType.NONE]:
            self.logger.error(f"Invalid source: {source}")
            return False
        
        # Always allow source selection for display purposes, even if backend is disconnected
        # We'll store the selected source and use it when the backend connects
        
        # Stop current source if different and connected
        if self.source and self.source != source:
            if ((self.source == BackendType.MPD and self.mpd_connected) or 
                (self.source == BackendType.LIBRESPOT and self.librespot_connected)):
                self._stop_source(self.source)
            elif self.source == BackendType.BLUETOOTH and self.bluetooth_connected:
                # Disconnect Bluetooth device when switching away
                if self.bluetooth_controller and self.bluetooth_controller.is_connected():
                    self.logger.info("Disconnecting Bluetooth device (switching sources)")
                    self.bluetooth_controller.disconnect_current()
        
        # Set new source (always successful for display purposes)
        self.source = source
        
        # Check if the requested backend is available for actual playback
        if source == BackendType.MPD and not self.mpd_connected:
            self.logger.warning(f"Source set to {source.value} but backend is not connected")
        elif source == BackendType.LIBRESPOT and not self.librespot_connected:
            self.logger.warning(f"Source set to {source.value} but backend is not connected")
        elif source == BackendType.BLUETOOTH:
            # Handle Bluetooth source selection
            if not self.bluetooth_connected:
                self.logger.warning(f"Source set to {source.value} but backend is not available")
            elif self.bluetooth_controller and self.bluetooth_controller.is_connected():
                self.logger.info(f"✅ Active source set to: {source.value} (device connected)")
            else:
                # Enter pairing mode when selecting Bluetooth with no device connected
                self.logger.info(f"✅ Source set to {source.value} - entering pairing mode")
                if self.bluetooth_controller:
                    self.bluetooth_controller.enter_pairing_mode(timeout_seconds=60)
        else:
            self.logger.info(f"✅ Active source set to: {source.value} (backend connected)")
            
            # Auto-play when switching sources
            try:
                if source == BackendType.MPD and self.mpd_monitor:
                    mpd_status = self.mpd_monitor.get_status()
                    if mpd_status and mpd_status.get('state') in ['pause', 'stop']:
                        self.logger.info(f"Auto-starting playback on {source.value} (was {mpd_status.get('state')})")
                        self.play()
                elif source == BackendType.LIBRESPOT:
                    # Always try to start Spotify playback when switching to it
                    self.logger.info(f"Auto-starting playback on {source.value}")
                    self.play()
            except Exception as e:
                self.logger.warning(f"Could not auto-start playback on {source.value}: {e}")
        
        # Always return True so the display updates
        self.logger.info(f"✅ Source selection set to: {source.value}")
        return True
    
    def get_current_source(self) -> Optional[BackendType]:
        """
        Get the currently active audio source.
        
        Returns:
            Current source or None if no source is active
        """
        return self.source
    
    def get_available_sources(self) -> list[BackendType]:
        """
        Get list of available (connected) audio sources.
        
        Returns:
            List of available backend types
        """
        sources = []
        if self.mpd_connected:
            sources.append(BackendType.MPD)
        if self.librespot_connected:
            sources.append(BackendType.LIBRESPOT)
        return sources
    
    def switch_to_mpd(self) -> bool:
        """
        Switch active source to MPD.
        
        Returns:
            True if successful
        """
        return self.set_source(BackendType.MPD)
    
    def switch_to_spotify(self) -> bool:
        """
        Switch active source to Spotify (librespot).
        
        Returns:
            True if successful
        """
        return self.set_source(BackendType.LIBRESPOT)

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status information from both backends.
        
        Returns:
            Dictionary with current status from both backends
        """
        status = {
            'daemon_running': self.running,
            'powered_on': self.powered_on,
            'current_source': self.source.value if self.source else None,
            'available_sources': [s.value for s in self.get_available_sources()],
            'mpd': {'connected': False},
            'librespot': {'connected': False}
        }
        
        # Get MPD status (only if it's the active source to avoid unnecessary queries)
        if self.mpd_connected and self.mpd_monitor:
            try:
                # Only get detailed status if MPD is the active source
                if self.source == BackendType.MPD:
                    mpd_status = self.mpd_monitor.get_status()
                    current_song = self.mpd_monitor.get_current_track()
                    
                    status['mpd'] = {
                        'connected': True,
                        'state': mpd_status.get('state', 'unknown'),
                        'volume': mpd_status.get('volume', 'unknown'),
                        'current_track': {
                            'title': current_song.get('title', current_song.get('title', 'Unknown')) if current_song else None,
                            'artist': current_song.get('artist', 'Unknown') if current_song else None,
                            'album': current_song.get('album', 'Unknown') if current_song else None,
                        } if current_song else None
                    }
                else:
                    # Just show connected status
                    status['mpd'] = {'connected': True, 'state': 'idle'}
            except Exception as e:
                status['mpd']['error'] = str(e)
        
        # Get librespot status
        if self.librespot_connected and self.librespot_monitor:
            try:
                current_track = self.librespot_monitor.get_current_track()
                librespot_status = self.librespot_monitor.get_status()
                
                # Debug logging
                self.logger.debug(f"Librespot current_track: {current_track}")
                self.logger.debug(f"Librespot status: {librespot_status}")
                
                status['librespot'] = {
                    'connected': True,
                    'state': (
                        'stopped' if librespot_status.get('stopped') else
                        'paused' if librespot_status.get('paused') else
                        'playing'
                    ) if librespot_status else 'unknown',
                    'volume': librespot_status.get('volume', 'unknown') if librespot_status else 'unknown',
                    'current_track': {
                        'title': current_track.get('title', 'Unknown') if current_track else None,
                        'artist': current_track.get('artist', 'Unknown') if current_track else None,
                        'album': current_track.get('album', 'Unknown') if current_track else None, 
                    } if current_track else None,

                }
            except Exception as e:
                self.logger.error(f"Error getting librespot status: {e}")
                status['librespot']['error'] = str(e)
        
        # Get Bluetooth status
        if self.bluetooth_connected and self.bluetooth_controller:
            try:
                connected_devices = []
                if self.bluetooth_controller.current_device_name:
                    connected_devices.append({
                        'name': self.bluetooth_controller.current_device_name,
                        'mac': list(self.bluetooth_controller.connected_devices)[0] if self.bluetooth_controller.connected_devices else 'Unknown'
                    })
                
                # Get Bluetooth volume
                bluetooth_volume = self.bluetooth_controller.get_volume()
                
                # Get track info from monitor
                current_track = self.bluetooth_controller.get_current_track()
                playback_status = self.bluetooth_controller.get_playback_status()
                
                status['bluetooth'] = {
                    'connected': True,
                    'discoverable': self.bluetooth_controller.pairing_mode,
                    'connected_devices': connected_devices,
                    'is_connected': self.bluetooth_controller.is_connected(),
                    'volume': bluetooth_volume if bluetooth_volume is not None else 50,
                    'state': playback_status if playback_status else 'stopped',
                    'current_track': current_track
                }
            except Exception as e:
                self.logger.error(f"Error getting Bluetooth status: {e}")
                status['bluetooth'] = {'connected': False, 'error': str(e)}
        else:
            status['bluetooth'] = {'connected': False}
        
        return status
    
    def run(self):
        """Run the daemon (blocking)"""
        if not self.start():
            return 1
        
        try:
            self.logger.info("KitchenRadio daemon running... (Press Ctrl+C to stop)")
            
            # Main loop
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return 1
        finally:
            self.stop()
        
        return 0

    def get_menu_options(self) -> Dict[str, Any]:
        """
        Get menu options for the currently active source.
        
        Returns:
            Dictionary with menu options based on the active provider
        """
        if not self.source:
            return {
                'has_menu': False,
                'options': [],
                'message': 'No active source selected'
            }
        
        if self.source == BackendType.MPD:
            return self._get_mpd_menu_options()
        elif self.source == BackendType.LIBRESPOT:
            # Spotify menu disabled
            return {
                'has_menu': False,
                'options': [],
                'message': 'Spotify menu disabled'
            }
        else:
            return {
                'has_menu': False,
                'options': [],
                'message': 'Unknown source type'
            }
    
    def _get_mpd_menu_options(self) -> Dict[str, Any]:
        """
        Get menu options for MPD (playlists).
        
        Returns:
            Dictionary with MPD menu options
        """
        if not self.mpd_connected or not self.mpd_controller:
            return {
                'has_menu': False,
                'options': [],
                'message': 'MPD not connected'
            }
        
        try:
            # Get available playlists
            playlists = self.mpd_controller.get_playlists()
            if not playlists:
                return {
                    'has_menu': True,
                    'menu_type': 'playlists',
                    'options': [],
                    'message': 'No playlists available'
                }
            
            playlist_options = []
            for playlist in playlists:
                playlist_options.append({
                    'id': playlist,
                    'label': playlist,
                    'type': 'playlist',
                    'action': 'load_playlist'
                })
            
            return {
                'has_menu': True,
                'menu_type': 'playlists',
                'options': playlist_options,
                'message': f'{len(playlist_options)} playlists available'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting MPD menu options: {e}")
            return {
                'has_menu': False,
                'options': [],
                'message': 'Error retrieving playlists'
            }
    
    def _get_spotify_menu_options(self) -> Dict[str, Any]:
        """
        Get menu options for Spotify (shuffle, repeat).
        
        Returns:
            Dictionary with Spotify menu options
        """
        if not self.librespot_connected or not self.librespot_controller:
            return {
                'has_menu': False,
                'options': [],
                'message': 'Spotify not connected'
            }
        
        try:
            # Get current shuffle and repeat states
            current_shuffle = self.librespot_controller.get_shuffle()
            current_repeat = self.librespot_controller.get_repeat()
            
            # Create menu options based on actual states
            options = [
                {
                    'id': 'shuffle',
                    'label': f'Shuffle: {"ON" if current_shuffle else "OFF"}',
                    'type': 'toggle',
                    'action': 'toggle_shuffle',
                    'state': current_shuffle if current_shuffle is not None else False
                },
                {
                    'id': 'repeat',
                    'label': f'Repeat: {(current_repeat or "OFF").upper()}',
                    'type': 'toggle', 
                    'action': 'toggle_repeat',
                    'state': current_repeat != 'off' if current_repeat is not None else False
                }
            ]
            
            return {
                'has_menu': True,
                'menu_type': 'playback_options',
                'options': options,
                'message': 'Playback options'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Spotify menu options: {e}")
            return {
                'has_menu': False,
                'options': [],
                'message': 'Error retrieving playback options'
            }
    
    def execute_menu_action(self, action: str, option_id: str = None) -> Dict[str, Any]:
        """
        Execute a menu action based on the active provider.
        
        Args:
            action: The action to execute
            option_id: Optional ID for the specific option
            
        Returns:
            Dictionary with execution result
        """
        if not self.source:
            return {
                'success': False,
                'error': 'No active source selected'
            }
        
        if self.source == BackendType.MPD:
            return self._execute_mpd_menu_action(action, option_id)
        elif self.source == BackendType.LIBRESPOT:
            return self._execute_spotify_menu_action(action, option_id)
        else:
            return {
                'success': False,
                'error': 'Unknown source type'
            }
    
    def _execute_mpd_menu_action(self, action: str, option_id: str = None) -> Dict[str, Any]:
        """
        Execute MPD menu action.
        
        Args:
            action: Action to execute
            option_id: Playlist name
            
        Returns:
            Dictionary with execution result
        """
        if not self.mpd_connected or not self.mpd_controller:
            return {
                'success': False,
                'error': 'MPD not connected'
            }
        
        try:

            result = self.mpd_controller.play_playlist(option_id)
            if result:
                return {
                    'success': True,
                        'message': f'Loaded and started playlist: {option_id}'
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to load playlist: {option_id}'
                }

                
        except Exception as e:
            self.logger.error(f"Error executing MPD menu action: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _execute_spotify_menu_action(self, action: str, option_id: str = None) -> Dict[str, Any]:
        """
        Execute Spotify menu action.
        
        Args:
            action: Action to execute
            option_id: Option identifier
            
        Returns:
            Dictionary with execution result
        """
        if not self.librespot_connected or not self.librespot_controller:
            return {
                'success': False,
                'error': 'Spotify not connected'
            }
        
        try:
            if action == 'toggle_shuffle':
                result = self.librespot_controller.toggle_shuffle()
                if result:
                    current_shuffle = self.librespot_controller.get_shuffle()
                    state = "enabled" if current_shuffle else "disabled"
                    return {
                        'success': True,
                        'message': f'Shuffle {state}'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Failed to toggle shuffle'
                    }
            elif action == 'toggle_repeat':
                result = self.librespot_controller.toggle_repeat()
                if result:
                    current_repeat = self.librespot_controller.get_repeat()
                    return {
                        'success': True,
                        'message': f'Repeat mode: {current_repeat or "off"}'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Failed to toggle repeat'
                    }
            else:
                return {
                    'success': False,
                    'error': f'Unknown Spotify action: {action}'
                }
                
        except Exception as e:
            self.logger.error(f"Error executing Spotify menu action: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def reconnect_backends(self) -> Dict[str, bool]:
        """
        Attempt to reconnect to disconnected backends.
        
        Returns:
            Dictionary with reconnection results for each backend
        """
        results = {'mpd': False, 'librespot': False}
        
        # Try to reconnect MPD if not connected
        if not self.mpd_connected:
            self.logger.info("Attempting to reconnect to MPD...")
            try:
                results['mpd'] = self._initialize_mpd()
                if results['mpd']:
                    # Start monitoring if reconnected
                    self.mpd_monitor.add_callback('state_changed', self._on_mpd_state_changed)
                    self.mpd_monitor.start_monitoring()
                    self.logger.info("MPD reconnected and monitoring started")
            except Exception as e:
                self.logger.warning(f"MPD reconnection failed: {e}")
        else:
            results['mpd'] = True  # Already connected
        
        # Try to reconnect librespot if not connected  
        if not self.librespot_connected:
            self.logger.info("Attempting to reconnect to librespot...")
            try:
                results['librespot'] = self._initialize_librespot()
                if results['librespot']:
                    # Start monitoring if reconnected
                    self.librespot_monitor.add_callback('state_changed', self._on_librespot_state_changed)
                    self.librespot_monitor.start_monitoring()
                    self.logger.info("Librespot reconnected and monitoring started")
            except Exception as e:
                self.logger.warning(f"Librespot reconnection failed: {e}")
        else:
            results['librespot'] = True  # Already connected
        
        return results

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='KitchenRadio Music Daemon')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--status', action='store_true',
                       help='Show status and exit')
    
    args = parser.parse_args()
    
    # Override debug setting if specified
    if args.debug:
        os.environ['DEBUG'] = 'true'
        os.environ['LOG_LEVEL'] = 'DEBUG'
    
    # Create daemon
    daemon = KitchenRadio()
    
    # Handle status request
    if args.status:
        if daemon.start():
            status = daemon.get_status()
            print(f"KitchenRadio Status:")
            print(f"Daemon running: {status.get('daemon_running', False)}")
            
            # MPD Status
            mpd_status = status.get('mpd', {})
            print(f"\nMPD:")
            print(f"  Connected: {mpd_status.get('connected', False)}")
            if mpd_status.get('connected'):
                print(f"  State: {mpd_status.get('state', 'unknown')}")
                print(f"  Volume: {mpd_status.get('volume', 'unknown')}%")
                current = mpd_status.get('current_track')
                if current and current.get('title'):
                    print(f"  Current: {current.get('artist', 'Unknown')} - {current.get('title', 'Unknown')}")
                else:
                    print(f"  Current: No track playing")
            
            # Librespot Status
            librespot_status = status.get('librespot', {})
            print(f"\nSpotify (librespot):")
            print(f"  Connected: {librespot_status.get('connected', False)}")
            if librespot_status.get('connected'):
                print(f"  State: {librespot_status.get('state', 'unknown')}")
                print(f"  Volume: {librespot_status.get('volume', 'unknown')}%")
                current = librespot_status.get('current_track')
                if current and current.get('title'):
                    print(f"  Current: {current.get('artist', 'Unknown')} - {current.get('title', 'Unknown')}")
                else:
                    print(f"  Current: No track playing")
            
            daemon.stop()
            return 0
        else:
            print("Failed to start daemon")
            return 1
    
    # Run daemon
    return daemon.run()


if __name__ == "__main__":
    sys.exit(main())