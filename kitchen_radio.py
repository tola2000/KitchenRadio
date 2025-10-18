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

# Import project configuration
import project_config

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
    
    Manages connections to music backends (MPD, librespot) and provides
    a unified interface for controlling music playback.
    """
    
    def __init__(self, backend: BackendType = BackendType.MPD):
        """
        Initialize KitchenRadio daemon.
        
        Args:
            backend: Backend type to use (MPD or librespot)
        """
        self.backend_type = backend
        self.client = None
        self.controller = None
        self.monitor = None
        self.running = False
        self.monitor_thread = None
        
        # Configuration from environment
        self.config = self._load_config()
        
        # Setup logging
        self._setup_logging()
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"KitchenRadio daemon initialized with {backend.value} backend")
    
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
    
    def _initialize_backend(self) -> bool:
        """
        Initialize the selected backend.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.backend_type == BackendType.MPD:
                return self._initialize_mpd()
            elif self.backend_type == BackendType.LIBRESPOT:
                return self._initialize_librespot()
            else:
                self.logger.error(f"Unknown backend type: {self.backend_type}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.backend_type.value} backend: {e}")
            return False
    
    def _initialize_mpd(self) -> bool:
        """Initialize MPD backend"""
        self.logger.info("Initializing MPD backend...")
        
        self.client = MPDClient(
            host=self.config['mpd_host'],
            port=self.config['mpd_port'],
            password=self.config['mpd_password'],
            timeout=self.config['mpd_timeout']
        )
        
        if not self.client.connect():
            self.logger.error("Failed to connect to MPD")
            return False
        
        self.controller = MPDController(self.client)
        self.monitor = MPDMonitor(self.client)
        
        self.logger.info(f"MPD backend initialized successfully - {self.config['mpd_host']}:{self.config['mpd_port']}")
        return True
    
    def _initialize_librespot(self) -> bool:
        """Initialize librespot backend"""
        self.logger.info("Initializing librespot backend...")
        
        self.client = KitchenRadioLibrespotClient(
            host=self.config['librespot_host'],
            port=self.config['librespot_port'],
            timeout=self.config['librespot_timeout']
        )
        
        if not self.client.connect():
            self.logger.error("Failed to connect to librespot")
            return False
        
        self.controller = LibrespotController(self.client)
        self.monitor = LibrespotMonitor(self.client)
        
        self.logger.info(f"Librespot backend initialized successfully - {self.config['librespot_host']}:{self.config['librespot_port']}")
        return True
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        self.logger.info("Starting monitor loop...")
        
        last_track = None
        last_state = None
        last_volume = None
        
        while self.running:
            try:
                # Get current status
                if self.backend_type == BackendType.MPD:
                    current_track = self.monitor.get_current_song()
                    current_state = self.monitor.get_status().get('state', 'unknown')
                else:  # librespot
                    current_track = self.monitor.get_current_track()
                    current_state = self.monitor.get_player_state()
                
                current_volume = self.monitor.get_volume()
                
                # Check for changes
                if current_track != last_track:
                    self._on_track_change(current_track, last_track)
                    last_track = current_track
                
                if current_state != last_state:
                    self._on_state_change(current_state, last_state)
                    last_state = current_state
                
                if current_volume != last_volume:
                    self._on_volume_change(current_volume, last_volume)
                    last_volume = current_volume
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _on_track_change(self, current_track, last_track):
        """Handle track change events"""
        if current_track:
            if self.backend_type == BackendType.MPD:
                title = current_track.get('title', current_track.get('file', 'Unknown'))
                artist = current_track.get('artist', 'Unknown')
                album = current_track.get('album', 'Unknown')
            else:  # librespot
                title = current_track.get('name', 'Unknown')
                artists = current_track.get('artists', [])
                artist = ", ".join([a.get('name', 'Unknown') for a in artists]) if artists else 'Unknown'
                album = current_track.get('album', {}).get('name', 'Unknown')
            
            self.logger.info(f"🎵 Now playing: {artist} - {title} ({album})")
        else:
            self.logger.info("🔇 No track playing")
    
    def _on_state_change(self, current_state, last_state):
        """Handle playback state change events"""
        state_icons = {
            'play': '▶️',
            'Playing': '▶️',
            'pause': '⏸️',
            'Paused': '⏸️',
            'stop': '⏹️',
            'Stopped': '⏹️'
        }
        
        icon = state_icons.get(current_state, '❓')
        self.logger.info(f"{icon} State changed to: {current_state}")
    
    def _on_volume_change(self, current_volume, last_volume):
        """Handle volume change events"""
        if current_volume is not None and last_volume is not None:
            self.logger.info(f"🔊 Volume changed: {last_volume}% → {current_volume}%")
    
    def start(self) -> bool:
        """
        Start the KitchenRadio daemon.
        
        Returns:
            True if started successfully, False otherwise
        """
        self.logger.info("Starting KitchenRadio daemon...")
        
        # Initialize backend
        if not self._initialize_backend():
            return False
        
        # Set initial volume if specified
        if self.config['default_volume'] > 0:
            try:
                self.controller.set_volume(self.config['default_volume'])
                self.logger.info(f"Set initial volume to {self.config['default_volume']}%")
            except Exception as e:
                self.logger.warning(f"Failed to set initial volume: {e}")
        
        # Start monitoring
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("KitchenRadio daemon started successfully")
        return True
    
    def stop(self):
        """Stop the KitchenRadio daemon"""
        self.logger.info("Stopping KitchenRadio daemon...")
        
        # Stop monitoring
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        # Disconnect from backend
        if self.client:
            try:
                self.client.disconnect()
                self.logger.info("Disconnected from backend")
            except Exception as e:
                self.logger.warning(f"Error disconnecting from backend: {e}")
        
        self.logger.info("KitchenRadio daemon stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status information.
        
        Returns:
            Dictionary with current status
        """
        if not self.controller or not self.monitor:
            return {'error': 'Daemon not initialized'}
        
        try:
            status = {
                'backend': self.backend_type.value,
                'connected': self.running,
                'volume': self.monitor.get_volume(),
            }
            
            if self.backend_type == BackendType.MPD:
                mpd_status = self.monitor.get_status()
                current_song = self.monitor.get_current_song()
                
                status.update({
                    'state': mpd_status.get('state', 'unknown'),
                    'current_song': {
                        'title': current_song.get('title', current_song.get('file', 'Unknown')) if current_song else None,
                        'artist': current_song.get('artist', 'Unknown') if current_song else None,
                        'album': current_song.get('album', 'Unknown') if current_song else None,
                    } if current_song else None
                })
            
            else:  # librespot
                current_track = self.monitor.get_current_track()
                
                status.update({
                    'state': self.monitor.get_player_state(),
                    'current_track': {
                        'title': current_track.get('name', 'Unknown') if current_track else None,
                        'artist': ", ".join([a.get('name', 'Unknown') for a in current_track.get('artists', [])]) if current_track and current_track.get('artists') else None,
                        'album': current_track.get('album', {}).get('name', 'Unknown') if current_track else None,
                    } if current_track else None
                })
            
            return status
            
        except Exception as e:
            return {'error': str(e)}
    
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
    parser.add_argument('--backend', choices=['mpd', 'librespot'], default='mpd',
                       help='Music backend to use (default: mpd)')
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
    backend = BackendType.MPD if args.backend == 'mpd' else BackendType.LIBRESPOT
    daemon = KitchenRadioDaemon(backend=backend)
    
    # Handle status request
    if args.status:
        if daemon.start():
            status = daemon.get_status()
            print(f"KitchenRadio Status:")
            print(f"Backend: {status.get('backend', 'unknown')}")
            print(f"Connected: {status.get('connected', False)}")
            print(f"State: {status.get('state', 'unknown')}")
            print(f"Volume: {status.get('volume', 'unknown')}%")
            
            current = status.get('current_song') or status.get('current_track')
            if current and current.get('title'):
                print(f"Current: {current.get('artist', 'Unknown')} - {current.get('title', 'Unknown')}")
            else:
                print("Current: No track playing")
            
            daemon.stop()
            return 0
        else:
            print("Failed to connect to backend")
            return 1
    
    # Run daemon
    return daemon.run()


if __name__ == "__main__":
    sys.exit(main())
