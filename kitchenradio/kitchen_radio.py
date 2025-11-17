#!/usr/bin/env python3
"""
KitchenRadio Daemon - Main application daemon
"""

import sys
import os
import time
import signal
import logging
import subprocess
import platform
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from enum import Enum

# Import configuration
from kitchenradio import config

# Import SourceController
from kitchenradio.sources.source_controller import SourceController, BackendType


class KitchenRadio:
    """
    Main KitchenRadio daemon class with integrated UI controller management.
    
    This daemon can run with or without optional UI components:
    - DisplayController (hardware OLED display)
    - ButtonController (hardware buttons via GPIO)
    - Web interface (Flask REST API)
    """
    
    def __init__(self, 
                 enable_display=False, 
                 enable_buttons=False,
                 enable_web=False,
                 web_host='0.0.0.0',
                 web_port=5000):
        """
        Initialize KitchenRadio daemon with optional UI components.
        
        Args:
            enable_display: Enable hardware display controller
            enable_buttons: Enable hardware button controller
            enable_web: Enable web interface
            web_host: Web server host (default: 0.0.0.0)
            web_port: Web server port (default: 5000)
        """
        self.running = False
        
        # Store UI component flags
        self.enable_display = enable_display
        self.enable_buttons = enable_buttons
        self.enable_web = enable_web
        self.web_host = web_host
        self.web_port = web_port
        
        # Configuration from environment
        self.config = self._load_config()
        
        # Setup logging
        self._setup_logging()
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("KitchenRadio daemon initialized")
        
        # Create SourceController (handles all backend operations)
        self.source_controller = SourceController(self.config)
        
        # UI Controllers (initialized in start())
        self.display_controller = None
        self.button_controller = None
        self.web_server = None
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables with fallback to config.py defaults.
        
        Environment variables take precedence over config.py values.
        """
        return {
            # MPD configuration
            'mpd_host': getattr(config, 'MPD_HOST', 'localhost'),
            'mpd_port': getattr(config, 'MPD_PORT', 6600),
            'mpd_password': getattr(config, 'MPD_PASSWORD', None),
            
            # Librespot configuration
            'librespot_host': getattr(config, 'LIBRESPOT_HOST', 'localhost'),
            'librespot_port': getattr(config, 'LIBRESPOT_PORT', 5030),
            
            # Bluetooth configuration
            'bluetooth_device_name': getattr(config, 'BLUETOOTH_DEVICE_NAME', 'KitchenRadio'),
            'bluetooth_discoverable': getattr(config, 'BLUETOOTH_DISCOVERABLE', True),
            
            # System configuration
            'default_source': getattr(config, 'DEFAULT_SOURCE', 'mpd'),
            'power_on_at_startup': getattr(config, 'POWER_ON_AT_STARTUP', True),
            'volume_step': getattr(config, 'VOLUME_STEP', 5),
            
            # General settings
            'log_level': os.getenv('LOG_LEVEL', config.LOG_LEVEL),
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
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def start(self) -> bool:
        """
        Start the KitchenRadio daemon with optional UI components.
        
        Returns:
            True if started successfully, False otherwise
        """
        self.logger.info("=" * 80)
        self.logger.info("Starting KitchenRadio Daemon")
        self.logger.info("=" * 80)
        
        # Print configuration
        self.logger.info("Configuration:")
        self.logger.info(f"  MPD: {self.config.get('mpd_host')}:{self.config.get('mpd_port')}")
        self.logger.info(f"  Librespot: {self.config.get('librespot_host')}:{self.config.get('librespot_port')}")
        self.logger.info(f"  Bluetooth: {self.config.get('bluetooth_device_name')}")
        self.logger.info(f"  Default Source: {self.config.get('default_source')}")
        self.logger.info("")
        self.logger.info("Controllers:")
        self.logger.info(f"  Display: {'Enabled' if self.enable_display else 'Disabled'}")
        self.logger.info(f"  Buttons: {'Enabled' if self.enable_buttons else 'Disabled'}")
        self.logger.info(f"  Web Interface: {'Enabled' if self.enable_web else 'Disabled'}")
        if self.enable_web:
            self.logger.info(f"  Web URL: http://{self.web_host}:{self.web_port}")
        self.logger.info("")
        
        # Initialize SourceController
        self.logger.info("Initializing SourceController...")
        if not self.source_controller.initialize():
            self.logger.error("Failed to initialize SourceController")
            return False
        
        # Start monitoring backends
        self.source_controller.start_monitoring()
        self.logger.info("[OK] SourceController initialized")
        
        # Initialize Display Controller (if enabled)
        if self.enable_display:
            self.logger.info("Initializing Display Controller...")
            try:
                from kitchenradio.interfaces.hardware.display_controller import DisplayController
                self.display_controller = DisplayController(
                    source_controller=self.source_controller,
                    refresh_rate=getattr(config, 'DISPLAY_REFRESH_RATE', 1.0),
                    use_hardware_display=getattr(config, 'DISPLAY_USE_HARDWARE', True)
                )
                if not self.display_controller.initialize():
                    self.logger.warning("Display Controller initialization failed - continuing without display")
                    self.display_controller = None
                else:
                    self.logger.info("[OK] Display Controller initialized")
            except Exception as e:
                self.logger.error(f"Failed to load Display Controller: {e}")
                self.display_controller = None
        
        # Initialize Button Controller (if enabled)
        if self.enable_buttons:
            self.logger.info("Initializing Button Controller...")
            try:
                from kitchenradio.interfaces.hardware.button_controller import ButtonController
                self.button_controller = ButtonController(
                    source_controller=self.source_controller,
                    debounce_time=getattr(config, 'BUTTON_DEBOUNCE_TIME', 0.2),
                    long_press_time=getattr(config, 'BUTTON_LONG_PRESS_TIME', 1.0),
                    display_controller=self.display_controller,
                    use_hardware=getattr(config, 'BUTTON_USE_HARDWARE', True),
                    i2c_address=getattr(config, 'BUTTON_I2C_ADDRESS', 0x20)
                )
                if not self.button_controller.initialize():
                    self.logger.warning("Button Controller initialization failed - continuing without buttons")
                    self.button_controller = None
                else:
                    self.logger.info("[OK] Button Controller initialized")
            except Exception as e:
                self.logger.error(f"Failed to load Button Controller: {e}")
                self.button_controller = None
        
        # Initialize Web Interface (if enabled)
        if self.enable_web:
            self.logger.info("Initializing Web Interface...")
            try:
                from kitchenradio.interfaces.web.kitchen_radio_web import KitchenRadioWeb
                self.web_server = KitchenRadioWeb(
                    source_controller=self.source_controller,
                    display_controller=self.display_controller,
                    button_controller=self.button_controller,
                    kitchen_radio=self,  # For system operations like reconnect_backends
                    host=self.web_host,
                    port=self.web_port
                )
                if not self.web_server.start():
                    self.logger.error("Failed to start web server")
                    self.web_server = None
                else:
                    self.logger.info(f"[OK] Web Interface initialized at http://{self.web_host}:{self.web_port}")
            except Exception as e:
                self.logger.error(f"Failed to load Web Interface: {e}")
                self.web_server = None
        
        self.running = True
        self.logger.info("=" * 80)
        self.logger.info("[OK] KitchenRadio daemon started successfully")
        self.logger.info("=" * 80)
        return True
    
    def stop(self):
        """Stop the KitchenRadio daemon and cleanup all resources."""
        self.logger.info("Stopping KitchenRadio daemon...")
        
        try:
            self.running = False
            
            # Stop web server
            if self.web_server:
                try:
                    self.logger.info("Stopping web interface...")
                    self.web_server.stop()
                except Exception as e:
                    self.logger.error(f"Error stopping web interface: {e}")
            
            # Stop button controller
            if self.button_controller:
                try:
                    self.logger.info("Stopping button controller...")
                    self.button_controller.cleanup()
                except Exception as e:
                    self.logger.error(f"Error stopping button controller: {e}")
            
            # Stop display controller
            if self.display_controller:
                try:
                    self.logger.info("Stopping display controller...")
                    self.display_controller.cleanup()
                except Exception as e:
                    self.logger.error(f"Error stopping display controller: {e}")
            
            # Stop SourceController
            self.source_controller.stop_monitoring()
            self.source_controller.cleanup()
            
            self.logger.info("✓ KitchenRadio daemon stopped")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}", exc_info=True)
    
    def reconnect_backends(self) -> Dict[str, bool]:
        """
        Attempt to reconnect to all disconnected backends.
        
        Returns:
            dict: Dictionary with backend names as keys and success status as values
        """
        self.logger.info("Reconnecting backends...")
        results = {}
        
        try:
            # MPD reconnection
            if hasattr(self.source_controller, 'mpd_controller'):
                try:
                    results['mpd'] = self.source_controller.mpd_controller.reconnect()
                except Exception as e:
                    self.logger.error(f"MPD reconnection failed: {e}")
                    results['mpd'] = False
            
            # Librespot reconnection
            if hasattr(self.source_controller, 'librespot_controller'):
                try:
                    results['librespot'] = self.source_controller.librespot_controller.reconnect()
                except Exception as e:
                    self.logger.error(f"Librespot reconnection failed: {e}")
                    results['librespot'] = False
            
            # Bluetooth reconnection
            if hasattr(self.source_controller, 'bluetooth_controller'):
                try:
                    results['bluetooth'] = self.source_controller.bluetooth_controller.reconnect()
                except Exception as e:
                    self.logger.error(f"Bluetooth reconnection failed: {e}")
                    results['bluetooth'] = False
            
            self.logger.info(f"Reconnection results: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error during backend reconnection: {e}", exc_info=True)
            return {'error': str(e)}
    
    def shutdown(self):
        """
        Shutdown KitchenRadio and reboot the operating system.
        
        This is a clean shutdown that:
        1. Stops all audio playback
        2. Disconnects from all backends
        3. Cleans up all resources
        4. Initiates system reboot
        """
        self.logger.warning("System shutdown requested")
        
        # Stop all KitchenRadio services
        self.stop()
        
        # Initiate system reboot
        try:
            if platform.system() == 'Linux':
                self.logger.info("Executing Linux reboot command...")
                subprocess.run(['sudo', 'shutdown', '-h', 'now'])
            elif platform.system() == 'Windows':
                self.logger.info("Executing Windows reboot command...")
                subprocess.run(['shutdown', '/r', '/t', '0'])
            else:
                self.logger.warning("Shutdown only supported on Linux/Windows")
        except Exception as e:
            self.logger.error(f"Failed to shutdown system: {e}")
    
    def run(self):
        """
        Run the daemon main loop (blocking).
        
        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        if not self.start():
            return 1
        
        try:
            self.logger.info("Press Ctrl+C to stop")
            
            # Main loop - keep daemon running
            if self.enable_web and self.web_server:
                # Web server runs in background thread
                while self.running and self.web_server.running:
                    time.sleep(1)
            else:
                # Console mode
                while self.running:
                    time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("\nKeyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            return 1
        finally:
            self.stop()
        
        return 0


def main():
    """Main entry point with command-line argument parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='KitchenRadio Daemon - Multi-source audio controller',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run daemon only (no UI)
  python -m kitchenradio.kitchen_radio
  
  # Run with web interface
  python -m kitchenradio.kitchen_radio --web
  
  # Run with web interface on custom port
  python -m kitchenradio.kitchen_radio --web --port 8080
  
  # Run with hardware controls (display + buttons)
  python -m kitchenradio.kitchen_radio --display --buttons
  
  # Run with everything enabled
  python -m kitchenradio.kitchen_radio --web --display --buttons
  
  # Run with web interface, no hardware
  python -m kitchenradio.kitchen_radio --web --no-hardware
        """
    )
    
    # UI component options
    parser.add_argument('--web', action='store_true',
                        help='Enable web interface')
    parser.add_argument('--display', action='store_true',
                        help='Enable display controller')
    parser.add_argument('--buttons', action='store_true',
                        help='Enable button controller')
    parser.add_argument('--no-hardware', action='store_true',
                        help='Disable all hardware (display + buttons)')
    parser.add_argument('--no-display', action='store_true',
                        help='Disable display controller')
    parser.add_argument('--no-buttons', action='store_true',
                        help='Disable button controller')
    
    # Web server options
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Web server host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000,
                        help='Web server port (default: 5000)')
    
    # Other options
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--status', action='store_true',
                        help='Show status and exit')
    
    args = parser.parse_args()
    
    # Override debug setting if specified
    if args.debug:
        os.environ['DEBUG'] = 'true'
        os.environ['LOG_LEVEL'] = 'DEBUG'
    
    # Determine what to enable
    enable_display = (args.display) and not (args.no_hardware or args.no_display)
    enable_buttons = (args.buttons) and not (args.no_hardware or args.no_buttons)
    enable_web = args.web
    
    # Create daemon with optional UI components
    daemon = KitchenRadio(
        enable_display=enable_display,
        enable_buttons=enable_buttons,
        enable_web=enable_web,
        web_host=args.host,
        web_port=args.port
    )
    
    # Handle status request
    if args.status:
        if daemon.start():
            status = daemon.source_controller.get_status()
            print(f"KitchenRadio Status:")
            print(f"  Current Source: {status.get('current_source', 'none')}")
            print(f"  Available Sources: {', '.join(status.get('available_sources', []))}")
            print(f"  Powered On: {status.get('powered_on', False)}")
            
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
            
            daemon.stop()
            return 0
        else:
            print("Failed to start daemon")
            return 1
    
    # Run daemon
    return daemon.run()


if __name__ == "__main__":
    sys.exit(main())