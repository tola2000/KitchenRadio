#!/usr/bin/env python3
"""
KitchenRadio Daemon - Main application daemon
"""

import sys
import os
import time
import signal
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum


# Import both backends
from kitchenradio.mpd import KitchenRadioClient as MPDClient, PlaybackController as MPDController, NowPlayingMonitor as MPDMonitor
from kitchenradio.librespot import KitchenRadioLibrespotClient, LibrespotController, LibrespotMonitor


class BackendType(Enum):
    """Supported backend types"""
    MPD = "mpd"
    LIBRESPOT = "librespot"


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

        self.source = None  # Current active source backend
        
        # Monitor threads
        self.mpd_monitor_thread = None
        self.librespot_monitor_thread = None
        
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
        Initialize both backends.
        
        Returns:
            True if at least one backend was initialized successfully
        """
        mpd_success = self._initialize_mpd()
        librespot_success = self._initialize_librespot()
        
        if not mpd_success and not librespot_success:
            self.logger.error("Failed to initialize any backend")
            return False
        
        if mpd_success:
            self.logger.info("✅ MPD backend available")
        else:
            self.logger.warning("❌ MPD backend unavailable")
            
        if librespot_success:
            self.logger.info("✅ Librespot backend available")
        else:
            self.logger.warning("❌ Librespot backend unavailable")
        
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
            
            self.logger.info(f"Librespot backend initialized successfully - {self.config['librespot_host']}:{self.config['librespot_port']}")
            return True
            
        except Exception as e:
            self.logger.warning(f"Librespot initialization failed: {e}")
            return False
    
    # def _mpd_monitor_loop(self):
    #     """Background monitoring loop for MPD"""
    #     self.logger.info("Starting MPD monitor loop...")
        
    #     last_track = None
    #     last_state = None
    #     last_volume = None
        
    #     while self.running and self.mpd_connected:
    #         try:
    #             # Get current status from MPD
    #             #current_track = self.mpd_monitor.get_current_song()
    #             current_state = self.mpd_monitor.get_status().get('state', 'unknown')
    #             current_volume = self.mpd_monitor.get_volume()
                
    #             # Check for changes
    #             if current_track != last_track:
    #                 self._on_mpd_track_change(current_track, last_track)
    #                 last_track = current_track
                
    #             if current_state != last_state:
    #                 self._on_mpd_state_change(current_state, last_state)
    #                 last_state = current_state
                
    #             if current_volume != last_volume:
    #                 self._on_mpd_volume_change(current_volume, last_volume)
    #                 last_volume = current_volume
                
    #             time.sleep(1)  # Check every second
                
    #         except Exception as e:
    #             self.logger.error(f"MPD monitor loop error: {e}")
    #             time.sleep(5)  # Wait longer on error
    
    # def _librespot_monitor_loop(self):
    #     """Background monitoring loop for librespot"""
    #     self.logger.info("Starting librespot monitor loop...")
        
    #     last_track = None
    #     last_state = None
    #     last_volume = None
        
    #     while self.running and self.librespot_connected:
    #         try:
    #             # Get current status from librespot
    #             current_track = self.librespot_monitor.get_current_track()
    #             current_state = self.librespot_monitor.get_player_state()
    #             current_volume = self.librespot_monitor.get_volume()
                
    #             # Check for changes
    #             if current_track != last_track:
    #                 self._on_librespot_track_change(current_track, last_track)
    #                 last_track = current_track
                
    #             if current_state != last_state:
    #                 self._on_librespot_state_change(current_state, last_state)
    #                 last_state = current_state
                
    #             if current_volume != last_volume:
    #                 self._on_librespot_volume_change(current_volume, last_volume)
    #                 last_volume = current_volume
                
    #             time.sleep(1)  # Check every second
                
    #         except Exception as e:
    #             self.logger.error(f"Librespot monitor loop error: {e}")
    #             time.sleep(5)  # Wait longer on error
    
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
    
    # Source management methods
    def set_source(self, source: BackendType) -> bool:
        """
        Set the active audio source, stopping the currently active one.
        
        Args:
            source: Backend type to activate (MPD or LIBRESPOT)
            
        Returns:
            True if source was set successfully
        """
        self.logger.info(f"Setting audio source to: {source.value}")
        
        # Validate source
        if source not in [BackendType.MPD, BackendType.LIBRESPOT]:
            self.logger.error(f"Invalid source: {source}")
            return False
        
        # Check if the requested backend is available
        if source == BackendType.MPD and not self.mpd_connected:
            self.logger.error("Cannot set source to MPD: not connected")
            return False
        
        if source == BackendType.LIBRESPOT and not self.librespot_connected:
            self.logger.error("Cannot set source to librespot: not connected")
            return False
        
        # Stop current source if different
        if self.source and self.source != source:
            self._stop_source(self.source)
        
        # Set new source
        self.source = source
        self.logger.info(f"✅ Active source set to: {source.value}")
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
        
        # Set initial volume if specified for available backends
        if self.config['default_volume'] > 0:
            if self.mpd_connected:
                try:
                    self.mpd_controller.set_volume(self.config['default_volume'])
                    self.logger.info(f"Set MPD initial volume to {self.config['default_volume']}%")
                    self.mpd_monitor.start_monitoring()
                    self.logger.info(f"Started MPD monitoring")
                except Exception as e:
                    self.logger.warning(f"Failed to set MPD initial volume: {e}")
            
            if self.librespot_connected:
                try:
                    self.librespot_controller.set_volume(self.config['default_volume'])
                    self.logger.info(f"Set librespot initial volume to {self.config['default_volume']}%")
                    self.librespot_monitor.start_monitoring()
                    self.logger.info(f"Started Librespot monitoring")
                except Exception as e:
                    self.logger.warning(f"Failed to set librespot initial volume: {e}")
        
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
        
        # Stop monitoring
        self.running = False
        
        # Wait for monitor threads to finish
        if self.mpd_monitor_thread and self.mpd_monitor_thread.is_alive():
            self.mpd_monitor_thread.join(timeout=5)
        
        if self.librespot_monitor_thread and self.librespot_monitor_thread.is_alive():
            self.librespot_monitor_thread.join(timeout=5)
        
        # Disconnect from backends
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
        
        self.logger.info("KitchenRadio daemon stopped")
    
    # Source management methods
    def set_source(self, source: BackendType) -> bool:
        """
        Set the active audio source, stopping the currently active one.
        
        Args:
            source: Backend type to activate (MPD or LIBRESPOT)
            
        Returns:
            True if source was set successfully
        """
        self.logger.info(f"Setting audio source to: {source.value}")
        
        # Validate source
        if source not in [BackendType.MPD, BackendType.LIBRESPOT]:
            self.logger.error(f"Invalid source: {source}")
            return False
        
        # Check if the requested backend is available
        if source == BackendType.MPD and not self.mpd_connected:
            self.logger.error("Cannot set source to MPD: not connected")
            return False
        
        if source == BackendType.LIBRESPOT and not self.librespot_connected:
            self.logger.error("Cannot set source to librespot: not connected")
            return False
        
        # Stop current source if different
        if self.source and self.source != source:
            self._stop_source(self.source)
        
        # Set new source
        self.source = source
        self.logger.info(f"✅ Active source set to: {source.value}")
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

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status information from both backends.
        
        Returns:
            Dictionary with current status from both backends
        """
        status = {
            'daemon_running': self.running,
            'current_source': self.source.value if self.source else None,
            'available_sources': [s.value for s in self.get_available_sources()],
            'mpd': {'connected': False},
            'librespot': {'connected': False}
        }
        
        # Get MPD status
        if self.mpd_connected and self.mpd_monitor:
            try:
                mpd_status = self.mpd_monitor.get_status()
                current_song = self.mpd_monitor.get_current_track()
                
                status['mpd'] = {
                    'connected': True,
                    'state': mpd_status.get('state', 'unknown'),
                    'volume': mpd_status.get('volume', 'unknown'),
                    'current_song': {
                        'title': current_song.get('title', current_song.get('name', 'Unknown')) if current_song else None,
                        'artist': current_song.get('artist', 'Unknown') if current_song else None,
                        'album': current_song.get('album', 'Unknown') if current_song else None,
                    } if current_song else None
                }
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
                current = mpd_status.get('current_song')
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
