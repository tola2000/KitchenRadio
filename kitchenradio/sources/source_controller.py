

import logging
import time
from typing import Optional, Dict, Any, Callable
from enum import Enum

# Import configuration
from kitchenradio import config

# Import backends
from kitchenradio.sources.mediaplayer import KitchenRadioClient as MPDClient, PlaybackController as MPDController, NowPlayingMonitor as MPDMonitor
from kitchenradio.sources.spotify import KitchenRadioLibrespotClient, LibrespotController, LibrespotMonitor

# Bluetooth imports are optional (Linux only)
try:
    from kitchenradio.sources.bluetooth import BlueZClient, BluetoothController, BluetoothMonitor
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False
    BlueZClient = None
    BluetoothController = None
    BluetoothMonitor = None


class BackendType(Enum):
    """Supported backend types"""
    MPD = "mpd"
    LIBRESPOT = "librespot"
    BLUETOOTH = "bluetooth"
    NONE = "none"


class SourceController:
    """
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
        
        self.bluetooth_controller = None
        self.bluetooth_connected = False
        
        # Current active source
        self.source = BackendType.NONE
        self.previous_source = BackendType.NONE
        
        # Power state
        self.powered_on = False
        
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
        
        # Power on at startup if configured
        if self.config['power_on_at_startup']:
            self.logger.info("Auto-powering on at startup...")
            self.power()
        
        return True
    
    def _initialize_mpd(self) -> bool:
        """Initialize MPD backend"""
        self.logger.info("Initializing MPD backend...")
        
        try:
            self.mpd_client = MPDClient(
                host=self.config.get('mpd_host', config.MPD_HOST),
                port=self.config.get('mpd_port', config.MPD_PORT),
                password=self.config.get('mpd_password', config.MPD_PASSWORD),
                timeout=self.config.get('mpd_timeout', config.MPD_TIMEOUT)
            )
            
            if not self.mpd_client.connect():
                self.logger.warning("Failed to connect to MPD")
                return False
            
            self.mpd_controller = MPDController(self.mpd_client)
            self.mpd_monitor = MPDMonitor(self.mpd_client)
            self.mpd_connected = True
            
            self.logger.info(f"MPD backend initialized - {self.config['mpd_host']}:{self.config['mpd_port']}")
            return True
            
        except Exception as e:
            self.logger.warning(f"MPD initialization failed: {e}")
            return False
    
    def _initialize_librespot(self) -> bool:
        """Initialize librespot backend"""
        self.logger.info("Initializing librespot backend...")
        
        try:
            self.librespot_client = KitchenRadioLibrespotClient(
                host=self.config.get('librespot_host', config.LIBRESPOT_HOST),
                port=self.config.get('librespot_port', config.LIBRESPOT_PORT),
                timeout=self.config.get('librespot_timeout', config.MPD_TIMEOUT)
            )
            
            if not self.librespot_client.connect():
                self.logger.warning("Failed to connect to librespot")
                return False
            
            self.librespot_controller = LibrespotController(self.librespot_client)
            self.librespot_monitor = LibrespotMonitor(self.librespot_client)
            self.librespot_connected = True
            
            self.logger.info(f"Librespot backend initialized - {self.config['librespot_host']}:{self.config['librespot_port']}")
            return True
            
        except Exception as e:
            self.logger.warning(f"Librespot initialization failed: {e}")
            return False
    
    def _initialize_bluetooth(self) -> bool:
        """Initialize Bluetooth backend"""
        self.logger.info("Initializing Bluetooth backend...")
        
        if not BLUETOOTH_AVAILABLE:
            self.logger.warning("Bluetooth module not available (Linux only)")
            return False
        
        try:
            self.bluetooth_controller = BluetoothController()
            
            # Give it time to initialize
            time.sleep(0.5)
            
            self.bluetooth_connected = True
            self.logger.info("Bluetooth backend initialized")
            return True
            
        except Exception as e:
            self.logger.warning(f"Bluetooth initialization failed: {e}")
            return False
    
    # =========================================================================
    # Source Management
    # =========================================================================
    
    def get_current_source(self) -> BackendType:
        """Get currently active source"""
        return self.source
    
    def get_available_sources(self) -> list:
        """Get list of available (connected) sources"""
        sources = []
        if self.mpd_connected:
            sources.append(BackendType.MPD)
        if self.librespot_connected:
            sources.append(BackendType.LIBRESPOT)
        if self.bluetooth_connected:
            sources.append(BackendType.BLUETOOTH)
        return sources
    
    def set_source(self, source: BackendType) -> bool:
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
            self.power()
        
        self.logger.info(f"Setting audio source to: {source.value}")
        
        # Validate source
        if source not in [BackendType.MPD, BackendType.LIBRESPOT, BackendType.BLUETOOTH, BackendType.NONE]:
            self.logger.error(f"Invalid source: {source}")
            return False
        
        # Store previous source
        previous_source = self.source
        
        # Stop current source if different
        if self.source and self.source != source and self.source != BackendType.NONE:
            self._stop_source(self.source)
        
        # Set new source
        self.source = source
        
        # Handle source-specific logic
        if source == BackendType.BLUETOOTH:
            if not self.bluetooth_connected:
                self.logger.warning(f"Source set to {source.value} but backend is not available")
            elif self.bluetooth_controller:
                if self.bluetooth_controller.is_connected():
                    self.logger.info(f"✅ Active source set to: {source.value} (device connected)")
                else:
                    # Enter pairing mode if BT pressed again while already on BT
                    if previous_source == BackendType.BLUETOOTH:
                        self.logger.info(f"BT button pressed while already on BT - entering pairing mode")
                        self.bluetooth_controller.enter_pairing_mode(timeout_seconds=60)
                    else:
                        self.logger.info(f"✅ Source set to {source.value} - showing disconnected state")
        else:
            # MPD or Librespot - check if connected
            if source == BackendType.MPD and not self.mpd_connected:
                self.logger.warning(f"Source set to {source.value} but backend is not connected")
            elif source == BackendType.LIBRESPOT and not self.librespot_connected:
                self.logger.warning(f"Source set to {source.value} but backend is not connected")
            else:
                self.logger.info(f"✅ Active source set to: {source.value}")
                
                # Auto-play when switching sources
                try:
                    if source == BackendType.MPD and self.mpd_monitor:
                        mpd_status = self.mpd_monitor.get_status()
                        if mpd_status and mpd_status.get('state') in ['pause', 'stop']:
                            self.logger.info(f"Auto-starting playback on {source.value}")
                            self.play()
                    elif source == BackendType.LIBRESPOT:
                        self.logger.info(f"Auto-starting playback on {source.value}")
                        self.play()
                except Exception as e:
                    self.logger.warning(f"Could not auto-start playback on {source.value}: {e}")
        
        return True
    
    def switch_to_mpd(self) -> bool:
        """Switch to MPD source"""
        return self.set_source(BackendType.MPD)
    
    def switch_to_spotify(self) -> bool:
        """Switch to Spotify (librespot) source"""
        return self.set_source(BackendType.LIBRESPOT)
    
    def switch_to_bluetooth(self) -> bool:
        """Switch to Bluetooth source"""
        return self.set_source(BackendType.BLUETOOTH)
    
    def _stop_source(self, source: BackendType):
        """Stop playback on specified source"""
        self.logger.info(f"Stopping playback on: {source.value}")
        
        try:
            if source == BackendType.MPD and self.mpd_connected and self.mpd_controller:
                self.mpd_controller.stop()
                self.logger.info("🛑 Stopped MPD playback")
            elif source == BackendType.LIBRESPOT and self.librespot_connected and self.librespot_controller:
                self.librespot_controller.stop()
                self.logger.info("🛑 Stopped Spotify playback")
            elif source == BackendType.BLUETOOTH and self.bluetooth_connected and self.bluetooth_controller:
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
        if self.source == BackendType.MPD:
            return self.mpd_controller, "MPD", self.mpd_connected
        elif self.source == BackendType.LIBRESPOT:
            return self.librespot_controller, "Spotify", self.librespot_connected
        elif self.source == BackendType.BLUETOOTH:
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
            self.logger.error(f"Error in play command: {e}")
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
            self.logger.error(f"Error in pause command: {e}")
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
            self.logger.error(f"Error in stop command: {e}")
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
            self.logger.error(f"Error in play/pause command: {e}")
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
        
        if self.source == BackendType.NONE:
            self.logger.warning("No active source selected for next command")
            return False
        
        try:
            result = controller.next()
            if result:
                self.logger.info(f"⏭️ [{source_name}] Next track")
            return result
        except Exception as e:
            self.logger.error(f"Error in next command: {e}")
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
        
        if self.source == BackendType.NONE:
            self.logger.warning("No active source selected for previous command")
            return False
        
        try:
            result = controller.previous()
            if result:
                self.logger.info(f"⏮️ [{source_name}] Previous track")
            return result
        except Exception as e:
            self.logger.error(f"Error in previous command: {e}")
            return False
    
    # =========================================================================
    # Volume Control
    # =========================================================================
    
    def get_volume(self) -> Optional[int]:
        """Get current volume level from active source"""
        controller, source_name, is_connected = self._get_active_controller()
        
        if not controller or not is_connected:
            return None
        
        if self.source == BackendType.NONE:
            return None
        
        try:
            return controller.get_volume()
        except Exception as e:
            self.logger.error(f"Error getting volume: {e}")
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
        
        if self.source == BackendType.NONE:
            self.logger.warning("No active source selected for set volume")
            return False
        
        if not 0 <= volume <= 100:
            self.logger.error(f"Invalid volume: {volume}. Must be 0-100")
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
        
        if self.source == BackendType.NONE:
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
        
        if self.source == BackendType.NONE:
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
    
    def power_on(self) -> bool:
        """Power on - restore source and start playback"""
        if self.powered_on:
            self.logger.info("Already powered on")
            return True
        
        self.powered_on = True
        self.logger.info("Powering on...")
        
        # Determine source to use
        source_to_use = None
        if self.previous_source and self.previous_source != BackendType.NONE:
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
            return True
        
        self.logger.warning("No sources available for power on")
        return False
    
    def power_off(self) -> bool:
        """Power off - save source and stop playback"""
        if not self.powered_on:
            self.logger.info("Already powered off")
            return True
        
        self.logger.info("Powering off...")
        
        # Save current source
        if self.source and self.source != BackendType.NONE:
            self.previous_source = self.source
            self.logger.info(f"Saving current source: {self.previous_source.value}")
        
        # Stop all playback
        self._stop_source(BackendType.MPD)
        self._stop_source(BackendType.LIBRESPOT)
        self._stop_source(BackendType.BLUETOOTH)
        
        # Clear source
        self.source = BackendType.NONE
        self.powered_on = False
        
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
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status from all backends.
        
        Returns:
            Dictionary with status from all sources
        """
        status = {
            'powered_on': self.powered_on,
            'current_source': self.source.value if self.source else 'none',
            'previous_source': self.previous_source.value if self.previous_source else 'none',
            'available_sources': [s.value for s in self.get_available_sources()],
        }
        
        # MPD status
        if self.mpd_connected and self.mpd_monitor:
            try:
                if self.source == BackendType.MPD:
                    mpd_status = self.mpd_monitor.get_status()
                    current_song = self.mpd_monitor.get_current_track()
                    
                    status['mpd'] = {
                        'connected': True,
                        'state': mpd_status.get('state', 'unknown'),
                        'volume': mpd_status.get('volume', 'unknown'),
                        'current_track': {
                            'title': current_song.get('title', 'Unknown') if current_song else None,
                            'artist': current_song.get('artist', 'Unknown') if current_song else None,
                            'album': current_song.get('album', 'Unknown') if current_song else None,
                        } if current_song else None
                    }
                else:
                    status['mpd'] = {'connected': True, 'state': 'idle'}
            except Exception as e:
                status['mpd'] = {'connected': True, 'error': str(e)}
        else:
            status['mpd'] = {'connected': False}
        
        # Librespot status
        if self.librespot_connected and self.librespot_monitor:
            try:
                current_track = self.librespot_monitor.get_current_track()
                librespot_status = self.librespot_monitor.get_status()
                
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
                status['librespot'] = {'connected': True, 'error': str(e)}
        elif self.source == BackendType.LIBRESPOT:
            status['librespot'] = {
                'connected': False,
                'state': 'stopped',
                'volume': 50,
                'current_track': None
            }
        else:
            status['librespot'] = {'connected': False}
        
        # Bluetooth status
        if self.bluetooth_connected and self.bluetooth_controller:
            try:
                connected_devices = []
                if hasattr(self.bluetooth_controller, 'current_device_name') and self.bluetooth_controller.current_device_name:
                    device_mac = list(self.bluetooth_controller.connected_devices)[0] if hasattr(self.bluetooth_controller, 'connected_devices') and self.bluetooth_controller.connected_devices else 'Unknown'
                    connected_devices.append({
                        'name': self.bluetooth_controller.current_device_name,
                        'mac': device_mac
                    })
                
                bluetooth_volume = self.bluetooth_controller.get_volume() if hasattr(self.bluetooth_controller, 'get_volume') else None
                current_track = self.bluetooth_controller.get_current_track() if hasattr(self.bluetooth_controller, 'get_current_track') else None
                playback_status = self.bluetooth_controller.get_playback_status() if hasattr(self.bluetooth_controller, 'get_playback_status') else None
                
                status['bluetooth'] = {
                    'connected': True,
                    'discoverable': self.bluetooth_controller.pairing_mode if hasattr(self.bluetooth_controller, 'pairing_mode') else False,
                    'connected_devices': connected_devices,
                    'volume': bluetooth_volume,
                    'current_track': current_track,
                    'playback_status': playback_status,
                }
            except Exception as e:
                status['bluetooth'] = {'connected': False, 'error': str(e)}
        else:
            status['bluetooth'] = {'connected': False}
        
        return status
    
    # =========================================================================
    # Monitoring
    # =========================================================================
    
    def start_monitoring(self, mpd_state_callback=None, librespot_state_callback=None, on_client_changed=None, on_spotify_track_started=None, bluetooth_callbacks=None):
        """
        Start monitoring for all connected backends.
        
        Args:
            mpd_state_callback: Callback for MPD state changes
            librespot_state_callback: Callback for Librespot state changes
            on_client_changed: Callback for any client change
            on_spotify_track_started: Callback for Spotify track started
            bluetooth_callbacks: Dict with bluetooth callbacks (connected, disconnected, track_changed, status_changed)
        """
        # MPD monitoring
        if self.mpd_connected and self.mpd_monitor:
            if mpd_state_callback:
                self.mpd_monitor.add_callback('state_changed', mpd_state_callback)
            if on_client_changed:
                self.mpd_monitor.add_callback('any', on_client_changed)
            self.mpd_monitor.start_monitoring()
            self.logger.info("Started MPD monitoring")
        
        # Librespot monitoring
        if self.librespot_connected and self.librespot_monitor:
            if librespot_state_callback:
                self.librespot_monitor.add_callback('state_changed', librespot_state_callback)
            if on_client_changed:
                self.librespot_monitor.add_callback('any', on_client_changed)
            # Always add internal callback to switch source on playback or resume
            self.librespot_monitor.add_callback('track_started', self._on_librespot_track_started)
            self.librespot_monitor.add_callback('track_resumed', self._on_librespot_track_started)
            if on_spotify_track_started:
                self.librespot_monitor.add_callback('track_started', on_spotify_track_started)
            self.librespot_monitor.start_monitoring()
            self.logger.info("Started Librespot monitoring")
        
        # Bluetooth monitoring
        if self.bluetooth_connected and self.bluetooth_controller:
            def _on_bluetooth_device_connected(*args, **kwargs):
                self.logger.info("Bluetooth device connected event received. Switching source to Bluetooth.")
                self.set_source(BackendType.BLUETOOTH)

            # Register internal callback for device connected
            self.bluetooth_controller.on_device_connected = _on_bluetooth_device_connected

            # Register any user-provided callbacks
            if bluetooth_callbacks:
                if 'connected' in bluetooth_callbacks:
                    # Chain user callback after internal
                    orig_cb = self.bluetooth_controller.on_device_connected
                    def chained_cb(*args, **kwargs):
                        orig_cb(*args, **kwargs)
                        bluetooth_callbacks['connected'](*args, **kwargs)
                    self.bluetooth_controller.on_device_connected = chained_cb
                if 'disconnected' in bluetooth_callbacks:
                    self.bluetooth_controller.on_device_disconnected = bluetooth_callbacks['disconnected']
                if self.bluetooth_controller.monitor:
                    if 'track_changed' in bluetooth_callbacks:
                        self.bluetooth_controller.monitor.register_callback('track_changed', bluetooth_callbacks['track_changed'])
                    if 'status_changed' in bluetooth_callbacks:
                        self.bluetooth_controller.monitor.register_callback('status_changed', bluetooth_callbacks['status_changed'])
            self.logger.info("Started Bluetooth monitoring")
    
    def stop_monitoring(self):
        """Stop monitoring for all backends"""
        if self.mpd_monitor:
            self.mpd_monitor.stop_monitoring()
            self.logger.info("Stopped MPD monitoring")
        # Do NOT stop librespot monitoring here; only stop on full shutdown/cleanup

    def _on_librespot_track_started(self, *args, **kwargs):
        """
        Callback for Librespot 'track_started' event.
        Switches source to Librespot automatically when playback starts.
        """
        self.logger.info("[DEBUG] _on_librespot_track_started called with args=%s kwargs=%s", args, kwargs)
        self.logger.info("Librespot track started event received. Switching source to Spotify (Librespot).")
        self.set_source(BackendType.LIBRESPOT)
    
    # =========================================================================
    # Cleanup
    # =========================================================================
    
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
            return self._get_spotify_menu_options()
        else:
            return {
                'has_menu': False,
                'options': [],
                'message': 'No menu available for this source'
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
        # Spotify menu disabled for now
        return {
            'has_menu': False,
            'options': [],
            'message': 'Spotify menu not available'
        }
    
    def execute_menu_action(self, action: str, option_id: str = None) -> Dict[str, Any]:
        """
        Execute menu action for the currently active source.
        
        Args:
            action: Action to execute
            option_id: Optional ID for the menu item
            
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
                'error': 'Menu action not supported for this source'
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
            option_id: Option ID
            
        Returns:
            Dictionary with execution result
        """
        # Spotify menu actions disabled for now
        return {
            'success': False,
            'error': 'Spotify menu actions not available'
        }
    
    def cleanup(self):
        """Clean up all backend connections"""
        self.logger.info("Cleaning up SourceController...")
        
        # Stop monitoring
        self.stop_monitoring()
        
        # Disconnect backends
        if self.mpd_client:
            try:
                self.mpd_client.disconnect()
                self.logger.info("Disconnected from MPD")
            except Exception as e:
                self.logger.warning(f"Error disconnecting from MPD: {e}")
        
        if self.librespot_client:
            try:
                self.librespot_client.disconnect()
                self.logger.info("Disconnected from librespot")
            except Exception as e:
                self.logger.warning(f"Error disconnecting from librespot: {e}")
        
        if self.bluetooth_controller:
            try:
                if hasattr(self.bluetooth_controller, 'is_connected') and self.bluetooth_controller.is_connected():
                    self.bluetooth_controller.disconnect_current()
                if hasattr(self.bluetooth_controller, 'cleanup'):
                    self.bluetooth_controller.cleanup()
                self.logger.info("Bluetooth controller cleaned up")
            except Exception as e:
                self.logger.warning(f"Error cleaning up Bluetooth: {e}")
        
        self.logger.info("[OK] SourceController cleanup complete")
