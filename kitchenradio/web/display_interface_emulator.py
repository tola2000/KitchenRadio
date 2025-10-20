"""
Simplified Display Interface Emulator for SSD1322 256x64 OLED Display

Provides a display interface that stores content as BMP images instead of using hardware.
Perfect for web-based emulation and testing without hardware dependencies.
"""

import logging
import time
import io
from typing import Optional, Dict, Any, Callable
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

# SSD1322 specifications
SSD1322_WIDTH = 256
SSD1322_HEIGHT = 64
SSD1322_ADDRESS = 0x3C

class EmulatorDisplayInterface:
    """
    Display interface emulator for SSD1322 256x64 OLED display.
    
    Stores display content as BMP images instead of using hardware.
    Perfect for web-based emulation and testing without hardware dependencies.
    """
    
    def __init__(self, 
                 i2c_port: int = 1,
                 i2c_address: int = SSD1322_ADDRESS,
                 width: int = SSD1322_WIDTH,
                 height: int = SSD1322_HEIGHT):
        """
        Initialize display interface emulator for SSD1322.
        
        Args:
            i2c_port: I2C port number (unused in emulation)
            i2c_address: I2C address (unused in emulation)
            width: Display width (fixed at 256 for SSD1322)
            height: Display height (fixed at 64 for SSD1322)
        """
        self.i2c_port = i2c_port
        self.i2c_address = i2c_address
        self.width = SSD1322_WIDTH  # Fixed for SSD1322
        self.height = SSD1322_HEIGHT  # Fixed for SSD1322
        
        # BMP image storage
        self.current_image = None
        self.bmp_data = None
        self.last_update = time.time()
        
        # Create initial blank image
        self.clear()
        
        logger.info(f"DisplayEmulator initialized for SSD1322 ({self.width}x{self.height})")
    
    def initialize(self) -> bool:
        """
        Initialize the display emulator (always successful).
        
        Returns:
            True (always successful in emulation)
        """
        try:
            # Create initial blank display
            self.clear()
            logger.info(f"Display emulator initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize display emulator: {e}")
            return False
    
    def cleanup(self):
        """Clean up display emulator resources"""
        logger.info("Cleaning up display emulator...")
        self.current_image = None
        self.bmp_data = None
        logger.info("Display emulator cleanup completed")
    
    def clear(self):
        """Clear the display"""
        try:
            # Create blank image (black background)
            self.current_image = Image.new('1', (self.width, self.height), 0)
            self._update_bmp_data()
            self.last_update = time.time()
            logger.debug("Display cleared")
        except Exception as e:
            logger.error(f"Error clearing display: {e}")
    
    def render_frame(self, draw_function: Callable) -> bool:
        """
        Render a frame using a drawing function and store as BMP.
        
        Args:
            draw_function: Function that takes ImageDraw.Draw as parameter
            
        Returns:
            True if successful
        """
        try:
            # Create new image
            self.current_image = Image.new('1', (self.width, self.height), 0)
            
            # Create drawing context
            draw = ImageDraw.Draw(self.current_image)
            
            # Call the drawing function
            draw_function(draw)
            
            # Update BMP data
            self._update_bmp_data()
            self.last_update = time.time()
            
            logger.debug("Frame rendered and stored as BMP")
            return True
                
        except Exception as e:
            logger.error(f"Error rendering frame: {e}")
            return False
    
    def _update_bmp_data(self):
        """Convert current image to BMP data"""
        try:
            if self.current_image:
                # Convert to BMP format in memory
                bmp_buffer = io.BytesIO()
                self.current_image.save(bmp_buffer, format='BMP')
                self.bmp_data = bmp_buffer.getvalue()
                bmp_buffer.close()
        except Exception as e:
            logger.error(f"Error updating BMP data: {e}")
            self.bmp_data = None
    
    def getDisplayImage(self) -> Optional[bytes]:
        """
        Get the current display image as BMP data.
        
        Returns:
            BMP image data as bytes, or None if no image available
        """
        return self.bmp_data
    
    
    def get_display_info(self) -> Dict[str, Any]:
        """Get display emulator information"""
        return {
            'display_type': 'SSD1322_256x64_Emulator',
            'width': self.width,
            'height': self.height,
            'i2c_port': self.i2c_port,
            'i2c_address': f"0x{self.i2c_address:02X}",
            'emulation_mode': True,
            'last_update': self.last_update,
            'has_image': self.current_image is not None,
            'bmp_size': len(self.bmp_data) if self.bmp_data else 0
        }
    


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing SSD1322 Display Interface Emulator...")
    
    # Create interface emulator for SSD1322
    interface = EmulatorDisplayInterface()
    
    # Initialize
    if interface.initialize():
        print("✅ SSD1322 emulator initialized successfully")
        
        # Get info
        info = interface.get_display_info()
        print(f"   Resolution: {info['width']}x{info['height']}")
        print(f"   Emulation mode: {info['emulation_mode']}")
        
        # Test custom drawing
        def draw_custom(draw):
            draw.text((10, 20), "KitchenRadio", fill=255)
            draw.text((10, 35), "SSD1322 Ready", fill=255)
            draw.rectangle([(5, 5), (info['width']-5, info['height']-5)], outline=255)
        
        if interface.render_frame(draw_custom):
            print("✅ SSD1322 custom drawing successful")
            
            # Test BMP data retrieval
            bmp_data = interface.getDisplayImage()
            if bmp_data:
                print(f"✅ BMP data generated ({len(bmp_data)} bytes)")
            else:
                print("❌ No BMP data available")
        
        # Cleanup
        interface.cleanup()
        
    else:
        print("❌ SSD1322 emulator initialization failed")
    
    print("SSD1322 Display Interface Emulator test completed")
