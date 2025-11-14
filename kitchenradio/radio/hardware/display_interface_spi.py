"""
SPI Display Interface for KitchenRadio using 4-wire SPI

Hardware SPI interface for SSD1322 OLED display using luma.oled library.
Uses 4-wire SPI with dedicated D/C and RST pins.

Hardware Connections:
- MOSI: GPIO10 (SPI0 MOSI)
- SCLK: GPIO11 (SPI0 SCLK)
- CE0:  GPIO8  (SPI0 CE0)
- D/C:  GPIO25 (Data/Command select)
- RST:  GPIO24 (Reset)
- GND:  Ground
- VCC:  3.3V or 5V (depending on display module)
"""

import logging
import time
from typing import Callable, Optional, Tuple
from PIL import Image, ImageDraw

try:
    from luma.core.interface.serial import spi
    from luma.oled.device import ssd1322
    from luma.core.render import canvas
    LUMA_AVAILABLE = True
except ImportError:
    LUMA_AVAILABLE = False
    logging.warning("luma.oled not available - display will not work")

logger = logging.getLogger(__name__)


class DisplayInterfaceSPI:
    """
    Hardware SPI display interface for SSD1322 OLED using 4-wire SPI.
    
    Features:
    - Hardware SPI communication (faster than I2C)
    - 256x64 grayscale display support
    - Configurable SPI bus speed
    - Frame buffering and rendering
    """
    
    # Display specifications
    WIDTH = 256
    HEIGHT = 64
    
    # Default SPI configuration
    DEFAULT_SPI_BUS_SPEED = 4_000_000  # 4 MHz (stable default)
    MAX_SPI_BUS_SPEED = 10_000_000     # 10 MHz (maximum tested)
    
    # GPIO pin assignments
    GPIO_DC = 25   # Data/Command select pin
    GPIO_RST = 24  # Reset pin
    SPI_PORT = 0   # SPI0
    SPI_DEVICE = 0 # CE0
    
    def __init__(self, 
                 bus_speed_hz: int = DEFAULT_SPI_BUS_SPEED,
                 gpio_dc: int = GPIO_DC,
                 gpio_rst: int = GPIO_RST,
                 spi_port: int = SPI_PORT,
                 spi_device: int = SPI_DEVICE):
        """
        Initialize SPI display interface.
        
        Args:
            bus_speed_hz: SPI bus speed in Hz (default: 4 MHz)
            gpio_dc: GPIO pin for D/C signal (default: 25)
            gpio_rst: GPIO pin for RST signal (default: 24)
            spi_port: SPI port number (default: 0 for SPI0)
            spi_device: SPI device/CE number (default: 0 for CE0)
        """
        self.bus_speed_hz = bus_speed_hz
        self.gpio_dc = gpio_dc
        self.gpio_rst = gpio_rst
        self.spi_port = spi_port
        self.spi_device = spi_device
        
        self.device = None
        self.serial = None
        self.initialized = False
        
        # Frame buffer for rendering
        self.current_frame = None
        
    def initialize(self) -> bool:
        """
        Initialize the SPI display hardware.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if not LUMA_AVAILABLE:
            logger.error("luma.oled library not available - cannot initialize display")
            return False
        
        try:
            logger.info(f"Initializing SPI interface at {self.bus_speed_hz / 1e6:.1f} MHz")
            logger.info(f"GPIO pins - D/C: {self.gpio_dc}, RST: {self.gpio_rst}")
            
            # Create SPI serial interface
            self.serial = spi(
                port=self.spi_port,
                device=self.spi_device,
                gpio_DC=self.gpio_dc,
                gpio_RST=self.gpio_rst,
                bus_speed_hz=self.bus_speed_hz
            )
            
            # Initialize SSD1322 device
            self.device = ssd1322(
                self.serial,
                width=self.WIDTH,
                height=self.HEIGHT,
                rotate=2  # 180 degree rotation
            )
            
            # Set maximum contrast for full brightness
            self.device.contrast(255)
            
            # Clear display on startup
            self.clear()
            
            self.initialized = True
            logger.info("SSD1322 display initialized successfully via SPI")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize SPI display: {e}")
            self.initialized = False
            return False
    
    def cleanup(self):
        """Clean up display resources"""
        try:
            if self.device:
                self.clear()
                self.device.cleanup()
                logger.info("Display cleanup completed")
        except Exception as e:
            logger.error(f"Error during display cleanup: {e}")
        finally:
            self.initialized = False
            self.device = None
            self.serial = None
    
    def clear(self):
        """Clear the display (all black)"""
        if not self.initialized or not self.device:
            return
        
        try:
            with canvas(self.device) as draw:
                draw.rectangle(self.device.bounding_box, outline="black", fill="black")
            self.current_frame = None
        except Exception as e:
            logger.error(f"Error clearing display: {e}")
    
    def render_frame(self, draw_func: Callable[[ImageDraw.Draw], None]):
        """
        Render a frame to the display using a drawing function.
        
        Args:
            draw_func: Function that takes ImageDraw.Draw and draws content
        """
        if not self.initialized or not self.device:
            logger.warning("Display not initialized - cannot render frame")
            return
        
        try:
            with canvas(self.device) as draw:
                # Call the drawing function
                draw_func(draw)
            
            # Store reference to current frame (if needed for debugging)
            self.current_frame = time.time()
            
        except Exception as e:
            logger.error(f"Error rendering frame: {e}")
    
    def display_text(self, text: str, x: int = 10, y: int = 10):
        """
        Display simple text on the screen (convenience method).
        
        Args:
            text: Text to display
            x: X coordinate
            y: Y coordinate
        """
        def draw_text(draw: ImageDraw.Draw):
            draw.rectangle(self.device.bounding_box, outline="black", fill="black")
            draw.text((x, y), text, fill="white")
        
        self.render_frame(draw_text)
    
    def display_test_pattern(self):
        """Display a test pattern to verify display is working"""
        if not self.initialized:
            logger.warning("Display not initialized - cannot show test pattern")
            return
        
        try:
            logger.info("Displaying test pattern")
            
            # Test 1: Text
            with canvas(self.device) as draw:
                draw.rectangle(self.device.bounding_box, outline="white", fill="black")
                draw.text((10, 10), "SSD1322 SPI TEST", fill="white")
                draw.text((10, 30), "4-Wire SPI Interface", fill="white")
                draw.text((10, 50), f"Speed: {self.bus_speed_hz / 1e6:.1f} MHz", fill="white")
            
            time.sleep(2)
            
            # Test 2: Moving dot animation (brief)
            logger.info("Running brief animation test")
            for i in range(50):
                x = int((i / 50) * (self.WIDTH - 10))
                with canvas(self.device) as draw:
                    draw.text((10, 10), "Animation Test", fill="white")
                    draw.ellipse((x, 40, x + 6, 46), fill="white")
                time.sleep(0.02)
            
            # Test 3: Grid pattern
            with canvas(self.device) as draw:
                draw.rectangle(self.device.bounding_box, outline="white", fill="black")
                # Draw grid
                for x in range(0, self.WIDTH, 32):
                    draw.line((x, 0, x, self.HEIGHT), fill="white")
                for y in range(0, self.HEIGHT, 16):
                    draw.line((0, y, self.WIDTH, y), fill="white")
                draw.text((80, 25), "GRID TEST", fill="white")
            
            time.sleep(2)
            self.clear()
            logger.info("Test pattern completed")
            
        except Exception as e:
            logger.error(f"Error displaying test pattern: {e}")
    
    def get_size(self) -> Tuple[int, int]:
        """
        Get display dimensions.
        
        Returns:
            Tuple of (width, height)
        """
        return (self.WIDTH, self.HEIGHT)
    
    def is_initialized(self) -> bool:
        """Check if display is initialized"""
        return self.initialized
    
    def set_bus_speed(self, bus_speed_hz: int) -> bool:
        """
        Change SPI bus speed (requires re-initialization).
        
        Args:
            bus_speed_hz: New bus speed in Hz
            
        Returns:
            True if successful
        """
        if bus_speed_hz > self.MAX_SPI_BUS_SPEED:
            logger.warning(f"Bus speed {bus_speed_hz / 1e6:.1f} MHz exceeds maximum "
                          f"{self.MAX_SPI_BUS_SPEED / 1e6:.1f} MHz - capping")
            bus_speed_hz = self.MAX_SPI_BUS_SPEED
        
        logger.info(f"Changing SPI bus speed to {bus_speed_hz / 1e6:.1f} MHz")
        
        # Store new speed
        self.bus_speed_hz = bus_speed_hz
        
        # Re-initialize with new speed
        if self.initialized:
            self.cleanup()
            return self.initialize()
        
        return True


# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Create and initialize display
    display = DisplayInterfaceSPI()
    
    if display.initialize():
        print("Display initialized successfully")
        
        try:
            # Run test pattern
            display.display_test_pattern()
            
            # Display some text
            display.display_text("Hello from SPI!", 50, 25)
            time.sleep(2)
            
            # Test custom drawing
            def custom_draw(draw):
                draw.rectangle(display.device.bounding_box, outline="black", fill="black")
                draw.text((20, 10), "Custom Drawing", fill="white")
                draw.rectangle((20, 30, 100, 50), outline="white", fill="black")
                draw.ellipse((120, 30, 160, 50), outline="white", fill="white")
            
            display.render_frame(custom_draw)
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            display.cleanup()
    else:
        print("Failed to initialize display")
