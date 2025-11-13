"""
Unified Display Interface for KitchenRadio

Provides both emulation (always available) and hardware SPI (optional).
Built-in emulator with BMP export for web viewing.

Design Philosophy:
- Emulation is built-in and always works (baseline)
- Hardware SPI is optional (requires luma.oled on Raspberry Pi)
- Single unified class for both modes
- BMP export support for web visualization
"""

import logging
import time
import io
from typing import Callable, Optional, Tuple, Dict, Any
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

# Hardware SPI support is OPTIONAL - only available on Raspberry Pi
try:
    from luma.core.interface.serial import spi
    from luma.oled.device import ssd1322
    from luma.core.render import canvas
    SPI_AVAILABLE = True
    logger.info("Hardware SPI support available (luma.oled detected)")
except ImportError:
    SPI_AVAILABLE = False
    logger.info("Hardware SPI not available - will use emulator mode only")


class DisplayInterface:
    """
    Unified display interface with built-in emulation and optional hardware SPI.
    
    Features:
    - Built-in emulator (always available, no external dependencies)
    - Optional hardware SPI (requires luma.oled on Raspberry Pi)
    - BMP export for web visualization (emulator mode)
    - Same API for both modes with automatic fallback
    
    Perfect for development (emulator) and production (hardware).
    """
    
    # Display specifications (same for both modes)
    WIDTH = 256
    HEIGHT = 64
    
    # SPI configuration (for hardware mode)
    DEFAULT_SPI_BUS_SPEED = 4_000_000  # 4 MHz
    MAX_SPI_BUS_SPEED = 10_000_000     # 10 MHz
    GPIO_DC = 25
    GPIO_RST = 24
    SPI_PORT = 0
    SPI_DEVICE = 0
    
    def __init__(self,
                 use_hardware: bool = False,
                 bus_speed_hz: int = DEFAULT_SPI_BUS_SPEED,
                 gpio_dc: int = GPIO_DC,
                 gpio_rst: int = GPIO_RST,
                 spi_port: int = SPI_PORT,
                 spi_device: int = SPI_DEVICE):
        """
        Initialize display interface.
        
        Emulator is built-in and always available.
        Hardware SPI used only if explicitly requested AND available.
        
        Args:
            use_hardware: Try to use hardware SPI (default: False = emulator)
            bus_speed_hz: SPI bus speed in Hz (hardware only, default: 4 MHz)
            gpio_dc: D/C GPIO pin (hardware only, default: 25)
            gpio_rst: RST GPIO pin (hardware only, default: 24)
            spi_port: SPI port (hardware only, default: 0)
            spi_device: SPI device/CE (hardware only, default: 0)
        """
        self.use_hardware = use_hardware
        self.bus_speed_hz = bus_speed_hz
        self.gpio_dc = gpio_dc
        self.gpio_rst = gpio_rst
        self.spi_port = spi_port
        self.spi_device = spi_device
        
        # Display state
        self.mode = None  # 'hardware' or 'emulator'
        self.initialized = False
        
        # Hardware SPI components (hardware mode only)
        self.serial = None
        self.device = None
        
        # Emulator components (emulator mode only) - for BMP export
        self.current_image = None
        self.bmp_data = None
        self.last_update = None
        
    def initialize(self) -> bool:
        """
        Initialize the display interface.
        
        Strategy:
        1. If use_hardware=True and SPI available: try hardware, fall back to emulator
        2. Otherwise: use emulator (guaranteed to work)
        
        Returns:
            True if initialization successful (always True - emulator is guaranteed)
        """
        # Try hardware mode if requested and available
        if self.use_hardware and SPI_AVAILABLE:
            if self._initialize_hardware():
                self.mode = 'hardware'
                self.initialized = True
                logger.info("Display initialized in HARDWARE SPI mode")
                return True
            else:
                logger.warning("Hardware SPI initialization failed, falling back to emulator")
        
        # Use emulator mode (always available)
        if self._initialize_emulator():
            self.mode = 'emulator'
            self.initialized = True
            logger.info("Display initialized in EMULATOR mode")
            return True
        else:
            # This should never happen since emulator is guaranteed
            logger.error("CRITICAL: Emulator initialization failed - this should not happen!")
            return False
    
    def _initialize_hardware(self) -> bool:
        """Initialize hardware SPI display"""
        try:
            logger.info(f"Initializing SPI hardware at {self.bus_speed_hz / 1e6:.1f} MHz")
            
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
                height=self.HEIGHT
            )
            
            # Clear display
            with canvas(self.device) as draw:
                draw.rectangle(self.device.bounding_box, outline="black", fill="black")
            
            return True
            
        except Exception as e:
            logger.error(f"Hardware SPI initialization failed: {e}")
            self.device = None
            self.serial = None
            return False
    
    def _initialize_emulator(self) -> bool:
        """
        Initialize built-in emulator mode.
        
        This should always succeed since emulator uses only PIL.
        """
        try:
            # Initialize emulator state
            self.current_image = Image.new('1', (self.WIDTH, self.HEIGHT), 0)
            self._update_bmp_data()
            self.last_update = time.time()
            logger.debug("Built-in emulator initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Emulator initialization failed (unexpected): {e}")
            return False
    
    def _update_bmp_data(self):
        """Convert current image to BMP bytes (emulator mode only)."""
        try:
            if self.current_image:
                bmp_buffer = io.BytesIO()
                self.current_image.save(bmp_buffer, format='BMP')
                self.bmp_data = bmp_buffer.getvalue()
                bmp_buffer.close()
        except Exception as e:
            logger.error(f"BMP conversion error: {e}")
            self.bmp_data = None
    
    def cleanup(self):
        """Clean up display resources"""
        try:
            if self.mode == 'hardware' and self.device:
                # Clear and cleanup hardware display
                with canvas(self.device) as draw:
                    draw.rectangle(self.device.bounding_box, outline="black", fill="black")
                self.device.cleanup()
            elif self.mode == 'emulator':
                # Clean up emulator resources
                self.current_image = None
                self.bmp_data = None
            
            logger.info(f"Display cleanup completed ({self.mode} mode)")
        except Exception as e:
            logger.error(f"Error during display cleanup: {e}")
        finally:
            self.initialized = False
            self.mode = None
            self.device = None
            self.serial = None
            self.current_image = None
            self.bmp_data = None
    
    def clear(self):
        """Clear the display (all black)"""
        if not self.initialized:
            return
        
        try:
            if self.mode == 'hardware':
                with canvas(self.device) as draw:
                    draw.rectangle(self.device.bounding_box, outline="black", fill="black")
            else:  # emulator
                self.current_image = Image.new('1', (self.WIDTH, self.HEIGHT), 0)
                self._update_bmp_data()
                self.last_update = time.time()
        except Exception as e:
            logger.error(f"Error clearing display: {e}")
    
    def render_frame(self, draw_func: Callable[[ImageDraw.Draw], None]):
        """
        Render a frame to the display using a drawing function.
        
        Args:
            draw_func: Function that takes ImageDraw.Draw and draws content
        """
        if not self.initialized:
            logger.warning("Display not initialized - cannot render frame")
            return
        
        try:
            if self.mode == 'hardware':
                # Hardware mode - render to real SPI display
                with canvas(self.device) as draw:
                    draw_func(draw)
                
                # Also render to PIL image for BMP export (web viewing)
                self.current_image = Image.new('1', (self.WIDTH, self.HEIGHT), 0)
                draw = ImageDraw.Draw(self.current_image)
                draw_func(draw)
                self._update_bmp_data()
                self.last_update = time.time()
                
            else:  # emulator
                # Emulator mode - render to PIL image only
                self.current_image = Image.new('1', (self.WIDTH, self.HEIGHT), 0)
                draw = ImageDraw.Draw(self.current_image)
                draw_func(draw)
                self._update_bmp_data()
                self.last_update = time.time()
                
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
            if self.mode == 'hardware':
                draw.rectangle(self.device.bounding_box, outline="black", fill="black")
            draw.text((x, y), text, fill="white")
        
        self.render_frame(draw_text)
    
    def display_test_pattern(self):
        """Display a test pattern to verify display is working"""
        if not self.initialized:
            logger.warning("Display not initialized - cannot show test pattern")
            return False
        
        try:
            logger.info(f"Displaying test pattern ({self.mode} mode)")
            
            if self.mode == 'emulator':
                # Emulator test pattern
                def draw_test(draw):
                    draw.rectangle([(0, 0), (self.WIDTH-1, self.HEIGHT-1)], outline=255)
                    draw.text((10, 10), "EMULATOR TEST", fill=255)
                    draw.text((10, 25), f"{self.WIDTH}x{self.HEIGHT}", fill=255)
                    draw.line([(0, 0), (self.WIDTH-1, self.HEIGHT-1)], fill=255)
                
                self.render_frame(draw_test)
                return True
            
            # Hardware mode - custom test pattern
            # Test 1: Text
            with canvas(self.device) as draw:
                draw.rectangle(self.device.bounding_box, outline="white", fill="black")
                draw.text((10, 10), "SSD1322 HYBRID TEST", fill="white")
                draw.text((10, 30), f"Mode: {self.mode.upper()}", fill="white")
                draw.text((10, 50), f"Speed: {self.bus_speed_hz / 1e6:.1f} MHz", fill="white")
            
            time.sleep(2)
            
            # Test 2: Moving dot animation (brief)
            for i in range(50):
                x = int((i / 50) * (self.WIDTH - 10))
                with canvas(self.device) as draw:
                    draw.text((10, 10), "Animation Test", fill="white")
                    draw.ellipse((x, 40, x + 6, 46), fill="white")
                time.sleep(0.02)
            
            # Test 3: Grid pattern
            with canvas(self.device) as draw:
                draw.rectangle(self.device.bounding_box, outline="white", fill="black")
                for x in range(0, self.WIDTH, 32):
                    draw.line((x, 0, x, self.HEIGHT), fill="white")
                for y in range(0, self.HEIGHT, 16):
                    draw.line((0, y, self.WIDTH, y), fill="white")
                draw.text((80, 25), "GRID TEST", fill="white")
            
            time.sleep(2)
            self.clear()
            logger.info("Test pattern completed")
            return True
            
        except Exception as e:
            logger.error(f"Error displaying test pattern: {e}")
            return False
    
    def get_size(self) -> Tuple[int, int]:
        """Get display dimensions"""
        return (self.WIDTH, self.HEIGHT)
    
    def is_initialized(self) -> bool:
        """Check if display is initialized"""
        return self.initialized
    
    def get_mode(self) -> Optional[str]:
        """Get current display mode ('hardware' or 'emulator')"""
        return self.mode
    
    def is_hardware_mode(self) -> bool:
        """Check if using hardware SPI mode"""
        return self.mode == 'hardware'
    
    def is_emulator_mode(self) -> bool:
        """Check if using emulator mode"""
        return self.mode == 'emulator'
    
    def get_display_info(self) -> dict:
        """Get display information"""
        info = {
            'mode': self.mode,
            'initialized': self.initialized,
            'width': self.WIDTH,
            'height': self.HEIGHT,
        }
        
        if self.mode == 'hardware':
            info.update({
                'bus_speed_hz': self.bus_speed_hz,
                'gpio_dc': self.gpio_dc,
                'gpio_rst': self.gpio_rst,
                'spi_port': self.spi_port,
                'spi_device': self.spi_device
            })
        elif self.mode == 'emulator':
            info.update({
                'display_type': 'Emulator',
                'emulation_mode': True,
                'last_update': self.last_update,
                'has_image': self.current_image is not None,
                'bmp_size': len(self.bmp_data) if self.bmp_data else 0
            })
        
        return info
    
    def get_statistics(self) -> dict:
        """Get display statistics (emulator mode only)"""
        if self.mode == 'emulator':
            return {
                'mode': 'emulator',
                'last_update': self.last_update,
                'image_size': len(self.bmp_data) if self.bmp_data else 0
            }
        else:
            return {
                'mode': self.mode,
                'stats_available': False,
                'message': 'Statistics only available in emulator mode'
            }
    
    def getDisplayImage(self):
        """Get display image as BMP data (available in both hardware and emulator mode)"""
        return self.bmp_data
    
    def get_ascii_representation(self) -> str:
        """Get ASCII art representation of display (available in both hardware and emulator mode)"""
        if not self.current_image:
            return f"[No image available - mode: {self.mode}]"
        
        try:
            ascii_chars = [" ", ".", ":", "+", "*", "#", "@"]
            width, height = 64, 16
            resized = self.current_image.resize((width, height))
            
            result = []
            for y in range(height):
                line = ""
                for x in range(width):
                    pixel = resized.getpixel((x, y))
                    char_index = int(pixel * (len(ascii_chars) - 1) / 255)
                    line += ascii_chars[char_index]
                result.append(line)
            
            return "\n".join(result)
        except Exception as e:
            return f"ASCII conversion error: {e}"
    
    def set_bus_speed(self, bus_speed_hz: int) -> bool:
        """
        Change SPI bus speed (hardware mode only, requires re-initialization).
        
        Args:
            bus_speed_hz: New bus speed in Hz
            
        Returns:
            True if successful
        """
        if self.mode != 'hardware':
            logger.warning("Bus speed can only be changed in hardware mode")
            return False
        
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
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Parse command line argument for mode
    use_hardware = '--hardware' in sys.argv or '-hw' in sys.argv
    
    print(f"Initializing unified display interface...")
    print(f"  Hardware mode requested: {use_hardware}")
    print(f"  SPI hardware available: {SPI_AVAILABLE}")
    print(f"  Emulator: Built-in (always available)")
    
    # Create display interface
    display = DisplayInterface(use_hardware=use_hardware)
    
    if display.initialize():
        print(f"Display initialized successfully in {display.get_mode()} mode")
        print(f"Display info: {display.get_display_info()}")
        
        try:
            # Run test pattern
            print("\nRunning test pattern...")
            display.display_test_pattern()
            
            # Display some text
            print("\nDisplaying custom text...")
            display.display_text("Hybrid Display!", 50, 25)
            time.sleep(2)
            
            # Test custom drawing
            print("\nTesting custom drawing...")
            def custom_draw(draw):
                if display.is_hardware_mode():
                    draw.rectangle(display.device.bounding_box, outline="black", fill="black")
                draw.text((20, 10), "Custom Drawing Test", fill="white")
                draw.rectangle((20, 30, 100, 50), outline="white", fill="black")
                draw.ellipse((120, 30, 160, 50), outline="white", fill="white")
                draw.text((170, 35), f"Mode: {display.get_mode()}", fill="white")
            
            display.render_frame(custom_draw)
            time.sleep(2)
            
            # Get stats if available
            if display.is_emulator_mode():
                print("\nDisplay statistics:")
                stats = display.get_statistics()
                for key, value in stats.items():
                    print(f"  {key}: {value}")
            
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            display.cleanup()
            print("Display cleaned up")
    else:
        print("Failed to initialize display")
        sys.exit(1)
