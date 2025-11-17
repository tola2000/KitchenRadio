#!/usr/bin/env python3
"""
KitchenRadio Daemon Startup Script

Example script showing how to initialize KitchenRadio with config.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from kitchenradio import config
from kitchenradio.radio.kitchen_radio import KitchenRadio
from kitchenradio.radio.hardware.button_controller import ButtonController
from kitchenradio.radio.hardware.display_controller import DisplayController

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for KitchenRadio daemon"""
    logger.info("=" * 80)
    logger.info("KitchenRadio Daemon Starting")
    logger.info("=" * 80)
    
    # Print configuration
    logger.info("Loading configuration from config.py...")
    logger.info(f"  MPD: {config.MPD_HOST}:{config.MPD_PORT}")
    logger.info(f"  Librespot: {config.LIBRESPOT_HOST}:{config.LIBRESPOT_PORT}")
    logger.info(f"  Display: {config.DISPLAY_WIDTH}x{config.DISPLAY_HEIGHT} @ {config.DISPLAY_REFRESH_RATE}Hz")
    logger.info(f"  Buttons: Hardware={'Enabled' if config.BUTTON_USE_HARDWARE else 'Disabled'}")
    logger.info(f"  Default Source: {config.DEFAULT_SOURCE}")
    logger.info(f"  Power on at startup: {config.POWER_ON_AT_STARTUP}")
    
    # Initialize KitchenRadio
    logger.info("\nInitializing KitchenRadio daemon...")
    kitchen_radio = KitchenRadio()
    
    if not kitchen_radio.start():
        logger.error("Failed to start KitchenRadio daemon")
        return 1
    
    # Initialize Display Controller with config
    logger.info("Initializing Display Controller...")
    display_controller = DisplayController(
        kitchen_radio=kitchen_radio,
        refresh_rate=config.DISPLAY_REFRESH_RATE,
        use_hardware_display=config.DISPLAY_USE_HARDWARE
    )
    
    if not display_controller.initialize():
        logger.error("Failed to initialize Display Controller")
        kitchen_radio.stop()
        return 1
    
    # Initialize Button Controller with config
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
        logger.warning("Button Controller initialization failed - continuing without hardware buttons")
    
    logger.info("=" * 80)
    logger.info("KitchenRadio Daemon Running")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80)
    
    try:
        # Keep running
        import time
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("\nShutdown requested...")
    
    finally:
        # Cleanup
        logger.info("Stopping KitchenRadio daemon...")
        button_controller.cleanup()
        display_controller.cleanup()
        kitchen_radio.stop()
        logger.info("KitchenRadio daemon stopped")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
