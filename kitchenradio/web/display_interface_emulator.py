"""
Display Emulator for SSD1322 256x64 OLED Display

Provides the same interface as I2CDisplayInterface but without hardware dependencies.
Emulates the display in memory and provides methods to access the image data.
"""

import logging
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

# SSD1322 specifications
SSD1322_WIDTH = 256
SSD1322_HEIGHT = 64
SSD1322_ADDRESS = 0x3C


class SimpleImage:
    """Simple bitmap image representation for display emulation"""
    
    def __init__(self, width: int, height: int, mode: str = '1'):
        """Initialize image with given dimensions"""
        self.width = width
        self.height = height
        self.mode = mode
        self.size = (width, height)
        
        # Initialize pixel data (0 = black, 255 = white for mode '1')
        self.pixels = [[0 for _ in range(width)] for _ in range(height)]
    
    def getpixel(self, xy):
        """Get pixel value at (x, y)"""
        x, y = xy
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.pixels[y][x]
        return 0
    
    def putpixel(self, xy, value):
        """Set pixel value at (x, y)"""
        x, y = xy
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y][x] = min(255, max(0, value))
    
    def resize(self, size, resample=None):
        """Create a resized copy of the image"""
        new_width, new_height = size
        new_image = SimpleImage(new_width, new_height, self.mode)
        
        # Simple nearest neighbor scaling
        x_ratio = self.width / new_width
        y_ratio = self.height / new_height
        
        for y in range(new_height):
            for x in range(new_width):
                src_x = int(x * x_ratio)
                src_y = int(y * y_ratio)
                if 0 <= src_x < self.width and 0 <= src_y < self.height:
                    pixel_value = self.pixels[src_y][src_x]
                    new_image.putpixel((x, y), pixel_value)
        
        return new_image
    
    def convert(self, mode):
        """Convert image to different mode"""
        if mode == self.mode:
            return self
        
        new_image = SimpleImage(self.width, self.height, mode)
        for y in range(self.height):
            for x in range(self.width):
                pixel = self.pixels[y][x]
                if mode == 'RGB':
                    # Convert grayscale to RGB
                    new_image.pixels[y][x] = (pixel, pixel, pixel)
                else:
                    new_image.pixels[y][x] = pixel
        
        return new_image
    
    def save(self, filename):
        """Save image as text representation"""
        with open(filename, 'w') as f:
            f.write(f"Image: {self.width}x{self.height} mode={self.mode}\n")
            f.write("=" * 50 + "\n")
            for y in range(self.height):
                line = ""
                for x in range(self.width):
                    pixel = self.pixels[y][x]
                    line += "█" if pixel > 128 else " "
                f.write(line + "\n")


class SimpleDraw:
    """Simple drawing operations for the display emulator"""
    
    def __init__(self, image: SimpleImage):
        """Initialize drawing context"""
        self.image = image
    
    def rectangle(self, xy, fill=None, outline=None, width=1):
        """Draw a rectangle"""
        if len(xy) == 2:
            x1, y1 = xy[0]
            x2, y2 = xy[1]
        else:
            x1, y1, x2, y2 = xy
        
        # Ensure correct order
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        # Fill rectangle
        if fill is not None:
            for y in range(y1, y2 + 1):
                for x in range(x1, x2 + 1):
                    self.image.putpixel((x, y), fill)
        
        # Draw outline
        if outline is not None:
            # Top and bottom lines
            for x in range(x1, x2 + 1):
                for w in range(width):
                    if y1 + w <= y2:
                        self.image.putpixel((x, y1 + w), outline)
                    if y2 - w >= y1:
                        self.image.putpixel((x, y2 - w), outline)
            
            # Left and right lines
            for y in range(y1, y2 + 1):
                for w in range(width):
                    if x1 + w <= x2:
                        self.image.putpixel((x1 + w, y), outline)
                    if x2 - w >= x1:
                        self.image.putpixel((x2 - w, y), outline)
    
    def line(self, xy, fill=255, width=1):
        """Draw a line using Bresenham's algorithm"""
        if len(xy) == 2:
            x1, y1 = xy[0]
            x2, y2 = xy[1]
        else:
            x1, y1, x2, y2 = xy
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        
        while True:
            # Draw pixel(s) for line width
            for w in range(width):
                for h in range(width):
                    self.image.putpixel((x + w, y + h), fill)
            
            if x == x2 and y == y2:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
    
    def text(self, xy, text, fill=255, font=None):
        """Draw simple text using a basic bitmap font"""
        x, y = xy
        
        # Simple 5x7 font patterns for basic characters
        font_patterns = {
            'A': [0x70, 0x88, 0x88, 0xF8, 0x88, 0x88, 0x88],
            'B': [0xF0, 0x88, 0x88, 0xF0, 0x88, 0x88, 0xF0],
            'C': [0x70, 0x88, 0x80, 0x80, 0x80, 0x88, 0x70],
            'D': [0xF0, 0x88, 0x88, 0x88, 0x88, 0x88, 0xF0],
            'E': [0xF8, 0x80, 0x80, 0xF0, 0x80, 0x80, 0xF8],
            'F': [0xF8, 0x80, 0x80, 0xF0, 0x80, 0x80, 0x80],
            'G': [0x70, 0x88, 0x80, 0x98, 0x88, 0x88, 0x70],
            'H': [0x88, 0x88, 0x88, 0xF8, 0x88, 0x88, 0x88],
            'I': [0x70, 0x20, 0x20, 0x20, 0x20, 0x20, 0x70],
            'J': [0x38, 0x10, 0x10, 0x10, 0x10, 0x90, 0x60],
            'K': [0x88, 0x90, 0xA0, 0xC0, 0xA0, 0x90, 0x88],
            'L': [0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0xF8],
            'M': [0x88, 0xD8, 0xA8, 0xA8, 0x88, 0x88, 0x88],
            'N': [0x88, 0xC8, 0xA8, 0x98, 0x88, 0x88, 0x88],
            'O': [0x70, 0x88, 0x88, 0x88, 0x88, 0x88, 0x70],
            'P': [0xF0, 0x88, 0x88, 0xF0, 0x80, 0x80, 0x80],
            'Q': [0x70, 0x88, 0x88, 0x88, 0xA8, 0x90, 0x68],
            'R': [0xF0, 0x88, 0x88, 0xF0, 0xA0, 0x90, 0x88],
            'S': [0x70, 0x88, 0x80, 0x70, 0x08, 0x88, 0x70],
            'T': [0xF8, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20],
            'U': [0x88, 0x88, 0x88, 0x88, 0x88, 0x88, 0x70],
            'V': [0x88, 0x88, 0x88, 0x88, 0x50, 0x50, 0x20],
            'W': [0x88, 0x88, 0x88, 0xA8, 0xA8, 0xD8, 0x88],
            'X': [0x88, 0x50, 0x20, 0x20, 0x50, 0x88, 0x88],
            'Y': [0x88, 0x88, 0x50, 0x20, 0x20, 0x20, 0x20],
            'Z': [0xF8, 0x08, 0x10, 0x20, 0x40, 0x80, 0xF8],
            ' ': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            '0': [0x70, 0x88, 0x98, 0xA8, 0xC8, 0x88, 0x70],
            '1': [0x20, 0x60, 0x20, 0x20, 0x20, 0x20, 0x70],
            '2': [0x70, 0x88, 0x08, 0x70, 0x80, 0x80, 0xF8],
            '3': [0x70, 0x88, 0x08, 0x30, 0x08, 0x88, 0x70],
            '4': [0x10, 0x30, 0x50, 0x90, 0xF8, 0x10, 0x10],
            '5': [0xF8, 0x80, 0xF0, 0x08, 0x08, 0x88, 0x70],
            '6': [0x70, 0x80, 0x80, 0xF0, 0x88, 0x88, 0x70],
            '7': [0xF8, 0x08, 0x10, 0x20, 0x40, 0x40, 0x40],
            '8': [0x70, 0x88, 0x88, 0x70, 0x88, 0x88, 0x70],
            '9': [0x70, 0x88, 0x88, 0x78, 0x08, 0x08, 0x70],
            ':': [0x00, 0x20, 0x00, 0x00, 0x20, 0x00, 0x00],
            '%': [0x84, 0x88, 0x10, 0x20, 0x40, 0x88, 0x90],
            '!': [0x20, 0x20, 0x20, 0x20, 0x00, 0x20, 0x00],
            '?': [0x70, 0x88, 0x10, 0x20, 0x00, 0x20, 0x00],
            '-': [0x00, 0x00, 0x00, 0xF8, 0x00, 0x00, 0x00],
            '.': [0x00, 0x00, 0x00, 0x00, 0x00, 0x20, 0x00],
            # Icons
            '▶': [0x20, 0x30, 0x38, 0x3C, 0x38, 0x30, 0x20],
            '⏸': [0x6C, 0x6C, 0x6C, 0x6C, 0x6C, 0x6C, 0x6C],
            '♪': [0x18, 0x18, 0x18, 0x98, 0xF8, 0x70, 0x20],
            '♫': [0x36, 0x36, 0x36, 0xB6, 0xF6, 0x66, 0x06],
            '⚠': [0x10, 0x38, 0x54, 0x92, 0x92, 0xFE, 0x10],
            '✓': [0x02, 0x06, 0x04, 0x88, 0x50, 0x20, 0x00],
        }
        
        char_width = 6  # 5 pixels + 1 space
        
        for i, char in enumerate(text.upper()):
            if char in font_patterns:
                pattern = font_patterns[char]
                char_x = x + i * char_width
                
                for row in range(7):
                    if row < len(pattern):
                        byte = pattern[row]
                        for col in range(5):
                            if byte & (0x80 >> col):
                                pixel_x = char_x + col
                                pixel_y = y + row
                                self.image.putpixel((pixel_x, pixel_y), fill)


class DisplayEmulator:
    """
    Display emulator with the same interface as I2CDisplayInterface.
    
    Provides all the same methods but emulates the display in memory
    without any hardware dependencies.
    """
    
    def __init__(self, 
                 i2c_port: int = 1,
                 i2c_address: int = SSD1322_ADDRESS,
                 width: int = SSD1322_WIDTH,
                 height: int = SSD1322_HEIGHT):
        """
        Initialize display emulator for SSD1322.
        
        Args:
            i2c_port: I2C port number (ignored in emulation)
            i2c_address: I2C address (ignored in emulation)
            width: Display width (fixed at 256 for SSD1322)
            height: Display height (fixed at 64 for SSD1322)
        """
        self.i2c_port = i2c_port
        self.i2c_address = i2c_address
        self.width = SSD1322_WIDTH  # Fixed for SSD1322
        self.height = SSD1322_HEIGHT  # Fixed for SSD1322
        
        self.device = None
        self.serial = None
        self.simulation_mode = True  # Always true for emulator
        self.last_frame = SimpleImage(self.width, self.height)
        self.last_update = None
        
        logger.info(f"DisplayEmulator initialized for SSD1322 ({self.width}x{self.height})")
    
    def initialize(self) -> bool:
        """
        Initialize the SSD1322 display emulator.
        
        Returns:
            True if initialization successful (always succeeds)
        """
        self.clear()
        self.last_update = datetime.now()
        logger.info("SSD1322 display emulator initialized successfully")
        return True
    
    def cleanup(self):
        """Clean up display emulator resources"""
        logger.info("Cleaning up display emulator...")
        self.device = None
        self.serial = None
        logger.info("Display emulator cleanup completed")
    
    def clear(self):
        """Clear the display"""
        self.last_frame = SimpleImage(self.width, self.height)
        self.last_update = datetime.now()
        logger.debug("Display cleared (emulation)")
    
    def render_frame(self, draw_function: Callable) -> bool:
        """
        Render a frame using a drawing function.
        
        Args:
            draw_function: Function that takes ImageDraw.Draw as parameter
            
        Returns:
            True if successful
        """
        try:
            # Create image and draw
            image = SimpleImage(self.width, self.height)
            draw = SimpleDraw(image)
            draw_function(draw)
            self.last_frame = image
            self.last_update = datetime.now()
            
            logger.debug("Frame rendered (emulation)")
            return True
                
        except Exception as e:
            logger.error(f"Error rendering frame: {e}")
            return False
    
    def get_display_info(self) -> Dict[str, Any]:
        """Get SSD1322 display information"""
        return {
            'display_type': 'SSD1322_EMULATOR',
            'width': self.width,
            'height': self.height,
            'i2c_port': self.i2c_port,
            'i2c_address': f"0x{self.i2c_address:02X}",
            'simulation_mode': True,
            'hardware_available': False,
            'last_update': self.last_update.isoformat() if self.last_update else None
        }
    
    def test_display(self) -> bool:
        """
        Test SSD1322 display functionality with a simple pattern.
        
        Returns:
            True if test successful
        """
        try:
            def draw_test_pattern(draw):
                # Draw border
                draw.rectangle([(0, 0), (self.width-1, self.height-1)], outline=255)
                
                # Draw diagonal lines
                draw.line([(0, 0), (self.width-1, self.height-1)], fill=255)
                draw.line([(0, self.height-1), (self.width-1, 0)], fill=255)
                
                # Draw center cross
                mid_x, mid_y = self.width // 2, self.height // 2
                draw.line([(mid_x, 0), (mid_x, self.height-1)], fill=255)
                draw.line([(0, mid_y), (self.width-1, mid_y)], fill=255)
                
                # Draw text
                draw.text((10, 10), "EMULATOR", fill=255)
                draw.text((10, 50), "TEST OK", fill=255)
            
            result = self.render_frame(draw_test_pattern)
            
            if result:
                logger.info("SSD1322 test pattern rendered successfully (emulation)")
                # Show test pattern for a moment
                time.sleep(0.5)
                self.clear()
            
            return result
            
        except Exception as e:
            logger.error(f"SSD1322 display test failed: {e}")
            return False
    
    def save_last_frame(self, filename: str) -> bool:
        """
        Save the last rendered frame to a file.
        
        Args:
            filename: Filename to save the image
            
        Returns:
            True if successful
        """
        try:
            if self.last_frame:
                self.last_frame.save(filename)
                logger.info(f"SSD1322 frame saved to {filename}")
                return True
        except Exception as e:
            logger.error(f"Error saving SSD1322 frame: {e}")
        return False
    
    def get_last_frame(self) -> Optional[SimpleImage]:
        """Get the last rendered frame"""
        return self.last_frame
    
    # Additional emulator-specific methods
    
    def get_image(self) -> SimpleImage:
        """
        Get the current display image.
        
        Returns:
            SimpleImage: Current display content
        """
        return self.last_frame
    
    def get_image_data(self) -> list:
        """
        Get the current display image as 2D pixel array.
        
        Returns:
            list: 2D array of pixel values (0-255)
        """
        if self.last_frame:
            return self.last_frame.pixels
        return [[0 for _ in range(self.width)] for _ in range(self.height)]
    
    def get_ascii_representation(self) -> str:
        """
        Get ASCII art representation of the current display.
        
        Returns:
            str: ASCII art of the display content
        """
        if not self.last_frame:
            return ""
        
        ascii_art = []
        ascii_art.append(f"SSD1322 Display ({self.width}x{self.height})")
        ascii_art.append("=" * (self.width // 4))
        
        # Sample every 4th pixel for ASCII representation
        for y in range(0, self.height, 2):
            line = ""
            for x in range(0, self.width, 4):
                pixel = self.last_frame.getpixel((x, y))
                line += "█" if pixel > 128 else " "
            ascii_art.append(line)
        
        ascii_art.append("=" * (self.width // 4))
        return "\n".join(ascii_art)
    
    def display_image(self, image: SimpleImage) -> bool:
        """
        Display a SimpleImage directly.
        
        Args:
            image: SimpleImage to display
            
        Returns:
            True if successful
        """
        try:
            # Ensure image is correct size
            if image.size != (self.width, self.height):
                image = image.resize((self.width, self.height))
            
            self.last_frame = image
            self.last_update = datetime.now()
            logger.debug("Image displayed (emulation)")
            return True
                
        except Exception as e:
            logger.error(f"Error displaying image: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get emulator statistics"""
        total_pixels = self.width * self.height
        if self.last_frame:
            on_pixels = sum(1 for y in range(self.height) 
                          for x in range(self.width) 
                          if self.last_frame.getpixel((x, y)) > 128)
        else:
            on_pixels = 0
        
        return {
            'total_pixels': total_pixels,
            'on_pixels': on_pixels,
            'off_pixels': total_pixels - on_pixels,
            'fill_percentage': (on_pixels / total_pixels) * 100 if total_pixels > 0 else 0,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'emulation_mode': True
        }


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing SSD1322 Display Emulator...")
    
    # Create emulator
    emulator = DisplayEmulator()
    
    # Initialize
    if emulator.initialize():
        print("✅ SSD1322 emulator initialized successfully")
        
        # Get info
        info = emulator.get_display_info()
        print(f"   Resolution: {info['width']}x{info['height']}")
        print(f"   Emulation mode: {info['simulation_mode']}")
        
        # Test display
        if emulator.test_display():
            print("✅ SSD1322 test passed")
        else:
            print("❌ SSD1322 test failed")
        
        # Test custom drawing
        def draw_custom(draw):
            draw.text((10, 20), "KITCHENRADIO", fill=255)
            draw.text((10, 35), "SSD1322 READY", fill=255)
            draw.rectangle([(5, 5), (info['width']-5, info['height']-5)], outline=255)
        
        if emulator.render_frame(draw_custom):
            print("✅ SSD1322 custom drawing successful")
        
        # Show ASCII representation
        print("\nASCII representation:")
        print(emulator.get_ascii_representation())
        
        # Show statistics
        stats = emulator.get_statistics()
        print(f"\nStatistics:")
        print(f"   On pixels: {stats['on_pixels']}/{stats['total_pixels']} ({stats['fill_percentage']:.1f}%)")
        
        # Save frame
        filename = "ssd1322_emulator_test.txt"
        if emulator.save_last_frame(filename):
            print(f"✅ Frame saved to {filename}")
        
        # Test getting image data
        image_data = emulator.get_image_data()
        print(f"✅ Image data retrieved: {len(image_data)}x{len(image_data[0])} pixels")
        
        # Cleanup
        emulator.cleanup()
        
    else:
        print("❌ SSD1322 emulator initialization failed")
    
    print("SSD1322 Display Emulator test completed")
