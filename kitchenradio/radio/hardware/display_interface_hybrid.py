"""
Hybrid Display Interface for KitchenRadio

Supports both hardware SPI display and web emulation mode.
Automatically falls back to emulation if hardware is not available.

This allows the same code to work in both development (emulator) and
production (hardware SPI) environments.
"""

import logging
import time
from typing import Callable, Optional, Tuple
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

# Try to import hardware SPI support
try:
    from luma.core.interface.serial import spi
    from luma.oled.device import ssd1322
    from luma.core.render import canvas
    SPI_AVAILABLE = True
except ImportError:
    SPI_AVAILABLE = False
    logger.info("luma.oled not available - SPI hardware mode disabled")

# Try to import emulator support
try:
    from kitchenradio.web.display_interface_emulator import DisplayInterfaceEmulator
    EMULATOR_AVAILABLE = True
except ImportError:
    EMULATOR_AVAILABLE = False
    logger.info("Display emulator not available")


class DisplayInterfaceHybrid:
    """
    Hybrid display interface that supports both SPI hardware and emulation.
    
    Automatically selects the best available mode:
    1. Hardware SPI (if use_hardware=True and available)
    2. Emulator (fallback or if use_hardware=False)
    
    Provides a unified interface regardless of the underlying implementation.
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
        Initialize hybrid display interface.
        
        Args:
            use_hardware: Try to use hardware SPI instead of emulator
            bus_speed_hz: SPI bus speed in Hz (hardware mode only)
            gpio_dc: GPIO pin for D/C signal (hardware mode only)
            gpio_rst: GPIO pin for RST signal (hardware mode only)
            spi_port: SPI port number (hardware mode only)
            spi_device: SPI device/CE number (hardware mode only)
        """
        self.use_hardware = use_hardware
        self.bus_speed_hz = bus_speed_hz
        self.gpio_dc = gpio_dc
        self.gpio_rst = gpio_rst
        self.spi_port = spi_port
        self.spi_device = spi_device
        
        # Active display interface
        self.display = None
        self.mode = None  # 'hardware' or 'emulator'
        self.initialized = False
        
        # Hardware SPI components (if using hardware)
        self.serial = None
        self.device = None
        
    def initialize(self) -> bool:
        """
        Initialize the display interface.
        Tries hardware first if requested, falls back to emulator.
        
        Returns:
            True if initialization successful
        """
        # Try hardware mode if requested and available
        if self.use_hardware and SPI_AVAILABLE:
            if self._initialize_hardware():
                self.mode = 'hardware'
                self.initialized = True
                logger.info("Hybrid display initialized in HARDWARE SPI mode")
                return True
            else:
                logger.warning("Hardware initialization failed, falling back to emulator")
        
        # Fall back to emulator mode
        if EMULATOR_AVAILABLE:
            if self._initialize_emulator():
                self.mode = 'emulator'
                self.initialized = True
                logger.info("Hybrid display initialized in EMULATOR mode")
                return True
            else:
                logger.error("Emulator initialization failed")
                return False
        else:
            logger.error("No display mode available (neither hardware nor emulator)")
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
            
            self.display = self.device
            
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
        """Initialize display emulator"""
        try:
            self.display = DisplayInterfaceEmulator()
            return self.display.initialize()
        except Exception as e:
            logger.error(f"Emulator initialization failed: {e}")
            self.display = None
            return False
    
    def cleanup(self):
        """Clean up display resources"""
        try:
            if self.display:
                if self.mode == 'hardware' and self.device:
                    # Clear hardware display
                    with canvas(self.device) as draw:
                        draw.rectangle(self.device.bounding_box, outline="black", fill="black")
                    self.device.cleanup()
                elif self.mode == 'emulator':
                    # Clean up emulator
                    self.display.cleanup()
                
                logger.info(f"Display cleanup completed ({self.mode} mode)")
        except Exception as e:
            logger.error(f"Error during display cleanup: {e}")
        finally:
            self.initialized = False
            self.display = None
            self.device = None
            self.serial = None
    
    def clear(self):
        """Clear the display (all black)"""
        if not self.initialized or not self.display:
            return
        
        try:
            if self.mode == 'hardware':
                with canvas(self.device) as draw:
                    draw.rectangle(self.device.bounding_box, outline="black", fill="black")
            else:  # emulator
                self.display.clear()
        except Exception as e:
            logger.error(f"Error clearing display: {e}")
    
    def render_frame(self, draw_func: Callable[[ImageDraw.Draw], None]):
        """
        Render a frame to the display using a drawing function.
        
        Args:
            draw_func: Function that takes ImageDraw.Draw and draws content
        """
        if not self.initialized or not self.display:
            logger.warning("Display not initialized - cannot render frame")
            return
        
        try:
            if self.mode == 'hardware':
                # Hardware mode - use luma canvas
                with canvas(self.device) as draw:
                    draw_func(draw)
            else:  # emulator
                # Emulator mode - delegate to emulator
                self.display.render_frame(draw_func)
                
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
            return
        
        try:
            logger.info(f"Displaying test pattern ({self.mode} mode)")
            
            if self.mode == 'emulator':
                # Use emulator's test pattern
                return self.display.test_display()
            
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
        elif self.mode == 'emulator' and hasattr(self.display, 'get_display_info'):
            # Merge emulator info
            info.update(self.display.get_display_info())
        
        return info
    
    def get_statistics(self) -> dict:
        """Get display statistics (emulator mode only)"""
        if self.mode == 'emulator' and hasattr(self.display, 'get_statistics'):
            return self.display.get_statistics()
        else:
            return {
                'mode': self.mode,
                'stats_available': False,
                'message': 'Statistics only available in emulator mode'
            }
    
    def getDisplayImage(self):
        """Get display image as BMP data (emulator mode only)"""
        if self.mode == 'emulator' and hasattr(self.display, 'getDisplayImage'):
            return self.display.getDisplayImage()
        else:
            logger.warning("Display image export only available in emulator mode")
            return None
    
    def get_ascii_representation(self) -> str:
        """Get ASCII art representation of display (emulator mode only)"""
        if self.mode == 'emulator' and hasattr(self.display, 'get_ascii_representation'):
            return self.display.get_ascii_representation()
        else:
            return f"[ASCII representation only available in emulator mode - current mode: {self.mode}]"
    
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
    
    print(f"Initializing hybrid display (hardware mode: {use_hardware})...")
    
    # Create hybrid display
    display = DisplayInterfaceHybrid(use_hardware=use_hardware)
    
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
