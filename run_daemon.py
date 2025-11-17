#!/usr/bin/env python3
"""
KitchenRadio Daemon Startup Script

Unified daemon that can run with or without web interface.
All controllers (display, buttons, web) are optional and configured via command-line.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from kitchenradio import config
from kitchenradio.radio.kitchen_radio import KitchenRadio
from kitchenradio.radio.hardware.button_controller import ButtonController
from kitchenradio.radio.hardware.display_controller import DisplayController

logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='KitchenRadio Daemon - Multi-source audio controller',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with hardware controls only (default)
  python run_daemon.py
  
  # Run with web interface on port 8080
  python run_daemon.py --web --port 8080
  
  # Run with web interface, no hardware
  python run_daemon.py --web --no-hardware
  
  # Run web only (no display, no buttons)
  python run_daemon.py --web --no-display --no-buttons
  
  # Custom web host and port
  python run_daemon.py --web --host 0.0.0.0 --port 5000
        """
    )
    
    # Web interface options
    parser.add_argument('--web', action='store_true',
                        help='Enable web interface')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Web server host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000,
                        help='Web server port (default: 5000)')
    
    # Hardware control options
    parser.add_argument('--no-hardware', action='store_true',
                        help='Disable all hardware (display + buttons)')
    parser.add_argument('--no-display', action='store_true',
                        help='Disable display controller')
    parser.add_argument('--no-buttons', action='store_true',
                        help='Disable button controller')
    
    # Logging options
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    
    return parser.parse_args()


def main():
    """Main entry point for KitchenRadio daemon"""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else getattr(logging, config.LOG_LEVEL)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Determine what to enable
    enable_display = not (args.no_hardware or args.no_display)
    enable_buttons = not (args.no_hardware or args.no_buttons)
    enable_web = args.web
    
    logger.info("=" * 80)
    logger.info("KitchenRadio Daemon Starting")
    logger.info("=" * 80)
    
    # Print configuration
    logger.info("Configuration:")
    logger.info(f"  MPD: {config.MPD_HOST}:{config.MPD_PORT}")
    logger.info(f"  Librespot: {config.LIBRESPOT_HOST}:{config.LIBRESPOT_PORT}")
    logger.info(f"  Bluetooth: {config.BLUETOOTH_DEVICE_NAME}")
    logger.info(f"  Default Source: {config.DEFAULT_SOURCE}")
    logger.info(f"  Power on at startup: {config.POWER_ON_AT_STARTUP}")
    logger.info("")
    logger.info("Controllers:")
    logger.info(f"  Display: {'Enabled' if enable_display else 'Disabled'}")
    logger.info(f"  Buttons: {'Enabled' if enable_buttons else 'Disabled'}")
    logger.info(f"  Web Interface: {'Enabled' if enable_web else 'Disabled'}")
    if enable_web:
        logger.info(f"  Web URL: http://{args.host}:{args.port}")
    logger.info("")
    
    # Initialize KitchenRadio core
    logger.info("Initializing KitchenRadio core...")
    kitchen_radio = KitchenRadio()
    
    if not kitchen_radio.start():
        logger.error("Failed to start KitchenRadio daemon")
        return 1
    
    logger.info("✓ KitchenRadio core initialized")
    
    # Initialize Display Controller (if enabled)
    display_controller = None
    if enable_display:
        logger.info("Initializing Display Controller...")
        display_controller = DisplayController(
            kitchen_radio=kitchen_radio,
            refresh_rate=config.DISPLAY_REFRESH_RATE,
            use_hardware_display=config.DISPLAY_USE_HARDWARE
        )
        
        if not display_controller.initialize():
            logger.warning("Display Controller initialization failed - continuing without display")
            display_controller = None
        else:
            logger.info("✓ Display Controller initialized")
    
    # Initialize Button Controller (if enabled)
    button_controller = None
    if enable_buttons:
        logger.info("Initializing Button Controller...")
        button_controller = ButtonController(
            kitchen_radio=kitchen_radio,
            debounce_time=config.BUTTON_DEBOUNCE_TIME,
            long_press_time=config.BUTTON_LONG_PRESS_TIME,
            display_controller=display_controller,
            use_hardware=config.BUTTON_USE_HARDWARE,
            i2c_address=config.BUTTON_I2C_ADDRESS
        )
        
        if not button_controller.initialize():
            logger.warning("Button Controller initialization failed - continuing without buttons")
            button_controller = None
        else:
            logger.info("✓ Button Controller initialized")
    
    # Initialize Web Interface (if enabled)
    web_server = None
    if enable_web:
        logger.info("Initializing Web Interface...")
        try:
            from kitchenradio.web.kitchen_radio_web import KitchenRadioWeb
            
            # KitchenRadioWeb is now a wrapper - pass existing controllers
            web_server = KitchenRadioWeb(
                kitchen_radio=kitchen_radio,
                display_controller=display_controller,  # Pass existing controller (or None)
                button_controller=button_controller,    # Pass existing controller (or None)
                host=args.host,
                port=args.port
            )
            logger.info("✓ Web Interface initialized as wrapper around existing controllers")
            logger.info(f"  Access at: http://{args.host}:{args.port}")
        except Exception as e:
            logger.error(f"Failed to initialize Web Interface: {e}")
            logger.warning("Continuing without web interface")
            web_server = None
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("KitchenRadio Daemon Running")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80)
    
    try:
        if enable_web and web_server:
            # Start web server in background
            if not web_server.start():
                logger.error("Failed to start web server")
                raise RuntimeError("Web server failed to start")
            
            # Keep daemon running (web server runs in background thread)
            import time
            logger.info("Web server running in background...")
            while web_server.running:
                time.sleep(1)
        else:
            # Keep daemon running
            import time
            logger.info("Running in console mode...")
            while True:
                time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("\nShutdown requested...")
    
    finally:
        # Cleanup
        logger.info("Stopping KitchenRadio daemon...")
        
        # Stop web server
        if web_server:
            try:
                logger.info("Stopping web interface...")
                web_server.stop()
            except Exception as e:
                logger.error(f"Error stopping web interface: {e}")
        
        # Stop button controller
        if button_controller:
            try:
                logger.info("Stopping button controller...")
                button_controller.cleanup()
            except Exception as e:
                logger.error(f"Error stopping button controller: {e}")
        
        # Stop display controller
        if display_controller:
            try:
                logger.info("Stopping display controller...")
                display_controller.cleanup()
            except Exception as e:
                logger.error(f"Error stopping display controller: {e}")
        
        # Stop KitchenRadio core
        try:
            logger.info("Stopping KitchenRadio core...")
            kitchen_radio.stop()
        except Exception as e:
            logger.error(f"Error stopping KitchenRadio: {e}")
        
        logger.info("=" * 80)
        logger.info("KitchenRadio daemon stopped")
        logger.info("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
