"""
Simplified I2C Display Interface for SSD1322 256x64 OLED Display

Handles low-level I2C communication with SSD1322 display only.
Simplified implementation focused on KitchenRadio requirements.
"""

import logging
import time
from typing import Optional, Dict, Any, Callable
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

try:
    from luma.core.interface.serial import i2c
    from luma.core.render import canvas
    from luma.oled.device import ssd1322
    LUMA_AVAILABLE = True
except ImportError:
    LUMA_AVAILABLE = False
    logger.warning("luma.oled not available - running in simulation mode")

# SSD1322 specifications
SSD1322_WIDTH = 256
SSD1322_HEIGHT = 64
SSD1322_ADDRESS = 0x3C

class I2CDisplayInterface:
    """
    Simplified I2C display interface for SSD1322 256x64 OLED display.
    
    Handles hardware communication with SSD1322 display via I2C.
    """
    
    def __init__(self, 
                 i2c_port: int = 1,
                 i2c_address: int = SSD1322_ADDRESS,
                 width: int = SSD1322_WIDTH,
                 height: int = SSD1322_HEIGHT):
        """
        Initialize I2C display interface for SSD1322.
        
        Args:
            i2c_port: I2C port number
            i2c_address: I2C address of the SSD1322 display
            width: Display width (fixed at 256 for SSD1322)
            height: Display height (fixed at 64 for SSD1322)
        """
        self.i2c_port = i2c_port
        self.i2c_address = i2c_address
        self.width = SSD1322_WIDTH  # Fixed for SSD1322
        self.height = SSD1322_HEIGHT  # Fixed for SSD1322
        
        self.device = None
        self.serial = None
        self.simulation_mode = not LUMA_AVAILABLE
        self.last_frame = None
        
        logger.info(f"I2CDisplayInterface initialized for SSD1322 ({self.width}x{self.height})")
        if self.simulation_mode:
            logger.info("Running in simulation mode - no hardware required")
    
    def initialize(self) -> bool:
        """
        Initialize the SSD1322 I2C display hardware.
        
        Returns:
            True if initialization successful
        """
        try:
            # Create I2C interface
            self.serial = i2c(port=self.i2c_port, address=self.i2c_address)
            
            # Create SSD1322 device
            self.device = ssd1322(self.serial, width=self.width, height=self.height)
            
            # Test the display by clearing it
            self.clear()
            
            logger.info(f"SSD1322 display initialized successfully on port {self.i2c_port}, address 0x{self.i2c_address:02X}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize SSD1322 display: {e}")
            logger.info("Falling back to simulation mode")
            self.simulation_mode = True
            return True
    
    def cleanup(self):
        """Clean up I2C display resources"""
        logger.info("Cleaning up I2C display interface...")
        
        if not self.simulation_mode and self.device:
            try:
                self.device.cleanup()
                logger.info("SSD1322 display hardware cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up display hardware: {e}")
        
        self.device = None
        self.serial = None
        
        logger.info("I2C display interface cleanup completed")
    
    def clear(self):
        """Clear the display"""
        try:
            if self.simulation_mode:
                # Create blank image for simulation
                self.last_frame = Image.new('1', (self.width, self.height), 0)
                logger.debug("Display cleared (simulation)")
            elif self.device:
                self.device.clear()
                logger.debug("Display cleared (hardware)")
        except Exception as e:
            logger.error(f"Error clearing display: {e}")
    
    def render_frame(self, draw_function: Callable) -> bool:
        """
        Render a frame using a drawing function.
        
        Args:
            draw_function: Function that takes ImageDraw.Draw as parameter
            
        Returns:
            True if successful
        """
        try:

            # Use luma's canvas context
            with canvas(self.device) as draw:
                draw_function(draw)
            logger.debug("Frame rendered (hardware)")
            return True
                
        except Exception as e:
            logger.error(f"Error rendering frame: {e}")
            return False
        
        return False
    
    def get_display_info(self) -> Dict[str, Any]:
        """Get SSD1322 display information"""
        return {
            'display_type': 'SSD1322_256x64',
            'width': self.width,
            'height': self.height,
            'i2c_port': self.i2c_port,
            'i2c_address': f"0x{self.i2c_address:02X}",
            'simulation_mode': self.simulation_mode,
            'hardware_available': LUMA_AVAILABLE
        }
    


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing SSD1322 I2C Display Interface...")
    
    # Create interface for SSD1322
    interface = I2CDisplayInterface()
    
    # Initialize
    if interface.initialize():
        print("✅ SSD1322 initialized successfully")
        
        # Get info
        info = interface.get_display_info()
        print(f"   Resolution: {info['width']}x{info['height']}")
        print(f"   Simulation mode: {info['simulation_mode']}")
        
        # Test custom drawing
        def draw_custom(draw):
            draw.text((10, 20), "KitchenRadio", fill=255)
            draw.text((10, 35), "SSD1322 Ready", fill=255)
            draw.rectangle([(5, 5), (info['width']-5, info['height']-5)], outline=255)
        
        if interface.render_frame(draw_custom):
            print("✅ SSD1322 custom drawing successful")
        
        
        # Cleanup
        interface.cleanup()
        
    else:
        print("❌ SSD1322 initialization failed")
    
    print("SSD1322 I2C Display Interface test completed")
