"""
Display Controller for KitchenRadio Physical Interface

Controls I2C OLED displays connected to Raspberry Pi.
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image, ImageDraw, ImageFont
import io
import os

logger = logging.getLogger(__name__)

try:
    from luma.core.interface.serial import i2c
    from luma.core.render import canvas
    from luma.oled.device import ssd1306, ssd1322, ssd1325, ssd1327, ssd1351, ssd1362
    LUMA_AVAILABLE = True
except ImportError:
    LUMA_AVAILABLE = False
    logger.warning("luma.oled not available - running in simulation mode")


class DisplayType:
    """Supported OLED display types"""
    SSD1306_128x64 = "ssd1306_128x64"
    SSD1306_128x32 = "ssd1306_128x32"
    SSD1322_256x64 = "ssd1322_256x64"
    SSD1325_128x64 = "ssd1325_128x64"
    SSD1327_128x128 = "ssd1327_128x128"


class DisplayPage:
    """Represents a page/screen on the display"""
    def __init__(self, name: str):
        self.name = name
        self.elements: List[Dict[str, Any]] = []
    
    def add_text(self, text: str, x: int, y: int, font_size: int = 12, 
                 font_name: str = "default", color: int = 255, anchor: str = "la"):
        """Add text element to the page"""
        self.elements.append({
            'type': 'text',
            'text': text,
            'x': x,
            'y': y,
            'font_size': font_size,
            'font_name': font_name,
            'color': color,
            'anchor': anchor
        })
    
    def add_line(self, x1: int, y1: int, x2: int, y2: int, color: int = 255, width: int = 1):
        """Add line element to the page"""
        self.elements.append({
            'type': 'line',
            'x1': x1,
            'y1': y1,
            'x2': x2,
            'y2': y2,
            'color': color,
            'width': width
        })
    
    def add_rectangle(self, x1: int, y1: int, x2: int, y2: int, 
                     fill: Optional[int] = None, outline: int = 255, width: int = 1):
        """Add rectangle element to the page"""
        self.elements.append({
            'type': 'rectangle',
            'x1': x1,
            'y1': y1,
            'x2': x2,
            'y2': y2,
            'fill': fill,
            'outline': outline,
            'width': width
        })
    
    def add_progress_bar(self, x: int, y: int, width: int, height: int, 
                        value: float, max_value: float = 100.0, 
                        fill_color: int = 255, bg_color: int = 64):
        """Add progress bar element to the page"""
        self.elements.append({
            'type': 'progress_bar',
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'value': value,
            'max_value': max_value,
            'fill_color': fill_color,
            'bg_color': bg_color
        })
    
    def clear(self):
        """Clear all elements from the page"""
        self.elements.clear()


class DisplayController:
    """
    Controls I2C OLED displays for the KitchenRadio interface.
    
    Features:
    - Multiple display type support
    - Page-based content management
    - Scrolling text support
    - Graphics primitives (text, lines, rectangles)
    - Progress bars
    - Animation support
    - Font management
    """
    
    def __init__(self, 
                 display_type: str = DisplayType.SSD1306_128x64,
                 i2c_port: int = 1,
                 i2c_address: int = 0x3C,
                 width: int = None,
                 height: int = None):
        """
        Initialize display controller.
        
        Args:
            display_type: Type of OLED display
            i2c_port: I2C port number (usually 1 on Raspberry Pi)
            i2c_address: I2C address of the display (usually 0x3C or 0x3D)
            width: Display width in pixels (auto-detected if None)
            height: Display height in pixels (auto-detected if None)
        """
        self.display_type = display_type
        self.i2c_port = i2c_port
        self.i2c_address = i2c_address
        
        # Display dimensions
        self._parse_display_dimensions(display_type, width, height)
        
        # Hardware interface
        self.device = None
        self.interface = None
        self.initialized = False
        
        # Content management
        self.pages: Dict[str, DisplayPage] = {}
        self.current_page = None
        
        # Animation and updates
        self.update_thread = None
        self.running = False
        self.refresh_rate = 10  # Hz
        self.scroll_speed = 2   # pixels per frame
        
        # Fonts
        self.fonts: Dict[str, ImageFont.ImageFont] = {}
        self._load_default_fonts()
        
        # Scrolling text state
        self.scroll_positions: Dict[str, int] = {}
        
        logger.info(f"DisplayController initialized for {display_type} ({self.width}x{self.height})")
    
    def _parse_display_dimensions(self, display_type: str, width: int = None, height: int = None):
        """Parse display dimensions from type string or parameters"""
        if width and height:
            self.width = width
            self.height = height
            return
        
        # Extract dimensions from display type
        dimension_map = {
            DisplayType.SSD1306_128x64: (128, 64),
            DisplayType.SSD1306_128x32: (128, 32),
            DisplayType.SSD1322_256x64: (256, 64),
            DisplayType.SSD1325_128x64: (128, 64),
            DisplayType.SSD1327_128x128: (128, 128),
        }
        
        self.width, self.height = dimension_map.get(display_type, (128, 64))
    
    def _load_default_fonts(self):
        """Load default fonts"""
        try:
            # Try to load different font sizes
            font_sizes = [8, 10, 12, 14, 16, 18, 20, 24]
            
            for size in font_sizes:
                try:
                    # Try to load a monospace font first
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size)
                    self.fonts[f"mono_{size}"] = font
                except (OSError, IOError):
                    try:
                        # Fall back to default font
                        font = ImageFont.truetype("arial.ttf", size)
                        self.fonts[f"default_{size}"] = font
                    except (OSError, IOError):
                        # Use PIL default font
                        self.fonts[f"default_{size}"] = ImageFont.load_default()
            
            # Set default font aliases
            self.fonts["default"] = self.fonts.get("default_12", ImageFont.load_default())
            self.fonts["small"] = self.fonts.get("default_8", ImageFont.load_default())
            self.fonts["large"] = self.fonts.get("default_16", ImageFont.load_default())
            self.fonts["mono"] = self.fonts.get("mono_12", ImageFont.load_default())
            
            logger.debug(f"Loaded {len(self.fonts)} fonts")
            
        except Exception as e:
            logger.warning(f"Error loading fonts: {e}")
            self.fonts["default"] = ImageFont.load_default()
    
    def initialize(self) -> bool:
        """
        Initialize the I2C display.
        
        Returns:
            True if initialization successful
        """
        if not LUMA_AVAILABLE:
            logger.warning("luma.oled not available - running in simulation mode")
            self.initialized = True
            return True
        
        try:
            # Create I2C interface
            self.interface = i2c(port=self.i2c_port, address=self.i2c_address)
            
            # Create device based on display type
            device_map = {
                DisplayType.SSD1306_128x64: ssd1306,
                DisplayType.SSD1306_128x32: ssd1306,
                DisplayType.SSD1322_256x64: ssd1322,
                DisplayType.SSD1325_128x64: ssd1325,
                DisplayType.SSD1327_128x128: ssd1327,
            }
            
            device_class = device_map.get(self.display_type, ssd1306)
            self.device = device_class(self.interface, width=self.width, height=self.height)
            
            # Clear display
            self.clear()
            
            # Start update thread
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            
            self.initialized = True
            logger.info(f"Display initialized successfully on I2C {self.i2c_port}:0x{self.i2c_address:02X}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize display: {e}")
            return False
    
    def cleanup(self):
        """Clean up display resources"""
        self.running = False
        
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)
        
        if self.device and LUMA_AVAILABLE:
            try:
                self.clear()
                logger.info("Display cleanup completed")
            except Exception as e:
                logger.warning(f"Error during display cleanup: {e}")
    
    def clear(self):
        """Clear the display"""
        if self.device and LUMA_AVAILABLE:
            self.device.clear()
        logger.debug("Display cleared")
    
    def create_page(self, name: str) -> DisplayPage:
        """
        Create a new display page.
        
        Args:
            name: Name of the page
            
        Returns:
            DisplayPage object
        """
        page = DisplayPage(name)
        self.pages[name] = page
        logger.debug(f"Created page '{name}'")
        return page
    
    def show_page(self, name: str):
        """
        Show a specific page.
        
        Args:
            name: Name of the page to show
        """
        if name in self.pages:
            self.current_page = name
            logger.debug(f"Switched to page '{name}'")
        else:
            logger.warning(f"Page '{name}' not found")
    
    def update_page_element(self, page_name: str, element_index: int, **kwargs):
        """
        Update an element on a page.
        
        Args:
            page_name: Name of the page
            element_index: Index of the element to update
            **kwargs: Properties to update
        """
        if page_name in self.pages:
            page = self.pages[page_name]
            if 0 <= element_index < len(page.elements):
                page.elements[element_index].update(kwargs)
                logger.debug(f"Updated element {element_index} on page '{page_name}'")
    
    def _update_loop(self):
        """Main update loop for display refresh"""
        frame_time = 1.0 / self.refresh_rate
        
        while self.running:
            try:
                start_time = time.time()
                
                if self.current_page and self.current_page in self.pages:
                    self._render_page(self.pages[self.current_page])
                
                # Sleep to maintain refresh rate
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_time - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in display update loop: {e}")
                time.sleep(0.1)
    
    def _render_page(self, page: DisplayPage):
        """Render a page to the display"""
        if not self.device:
            return
        
        if LUMA_AVAILABLE:
            with canvas(self.device) as draw:
                self._draw_page_elements(draw, page)
        else:
            # Simulation mode - create virtual canvas
            image = Image.new('1', (self.width, self.height), 0)
            draw = ImageDraw.Draw(image)
            self._draw_page_elements(draw, page)
            
            # In simulation mode, you could save the image or display it
            # For now, we'll just log that we're rendering
            logger.debug(f"Simulated rendering page '{page.name}' with {len(page.elements)} elements")
    
    def _draw_page_elements(self, draw: ImageDraw.ImageDraw, page: DisplayPage):
        """Draw all elements of a page"""
        for element in page.elements:
            try:
                if element['type'] == 'text':
                    self._draw_text(draw, element)
                elif element['type'] == 'line':
                    self._draw_line(draw, element)
                elif element['type'] == 'rectangle':
                    self._draw_rectangle(draw, element)
                elif element['type'] == 'progress_bar':
                    self._draw_progress_bar(draw, element)
            except Exception as e:
                logger.error(f"Error drawing element {element['type']}: {e}")
    
    def _draw_text(self, draw: ImageDraw.ImageDraw, element: Dict[str, Any]):
        """Draw text element"""
        text = str(element['text'])
        x, y = element['x'], element['y']
        color = element.get('color', 255)
        font_name = element.get('font_name', 'default')
        
        # Get font
        font = self.fonts.get(font_name, self.fonts['default'])
        
        # Handle scrolling text
        text_id = f"{element.get('id', text)}_{x}_{y}"
        if text_id not in self.scroll_positions:
            self.scroll_positions[text_id] = 0
        
        # Check if text needs scrolling
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width > self.width - x:
            # Scroll the text
            scroll_pos = self.scroll_positions[text_id]
            text = text[scroll_pos:] + "  " + text[:scroll_pos]
            
            # Update scroll position
            self.scroll_positions[text_id] = (scroll_pos + 1) % len(text)
        
        # Draw text
        draw.text((x, y), text, fill=color, font=font)
    
    def _draw_line(self, draw: ImageDraw.ImageDraw, element: Dict[str, Any]):
        """Draw line element"""
        x1, y1 = element['x1'], element['y1']
        x2, y2 = element['x2'], element['y2']
        color = element.get('color', 255)
        width = element.get('width', 1)
        
        draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    
    def _draw_rectangle(self, draw: ImageDraw.ImageDraw, element: Dict[str, Any]):
        """Draw rectangle element"""
        x1, y1 = element['x1'], element['y1']
        x2, y2 = element['x2'], element['y2']
        fill = element.get('fill')
        outline = element.get('outline', 255)
        width = element.get('width', 1)
        
        draw.rectangle([(x1, y1), (x2, y2)], fill=fill, outline=outline, width=width)
    
    def _draw_progress_bar(self, draw: ImageDraw.ImageDraw, element: Dict[str, Any]):
        """Draw progress bar element"""
        x, y = element['x'], element['y']
        width, height = element['width'], element['height']
        value = element['value']
        max_value = element.get('max_value', 100.0)
        fill_color = element.get('fill_color', 255)
        bg_color = element.get('bg_color', 64)
        
        # Draw background
        draw.rectangle([(x, y), (x + width, y + height)], fill=bg_color, outline=255)
        
        # Draw fill
        if value > 0 and max_value > 0:
            fill_width = int((value / max_value) * width)
            if fill_width > 0:
                draw.rectangle([(x, y), (x + fill_width, y + height)], fill=fill_color)
    
    # Convenience methods for common radio interface elements
    def show_track_info(self, title: str, artist: str, album: str = "", playing: bool = False):
        """Show track information on the display"""
        if "track_info" not in self.pages:
            page = self.create_page("track_info")
        else:
            page = self.pages["track_info"]
            page.clear()
        
        # Status icon
        status_icon = "♪" if playing else "■"
        page.add_text(status_icon, 0, 0, font_name="large")
        
        # Track title (scrolling if too long)
        page.add_text(title, 16, 0, font_name="default", id="title")
        
        # Artist
        page.add_text(artist, 0, 16, font_name="small")
        
        # Album (if provided)
        if album:
            page.add_text(album, 0, 28, font_name="small")
        
        # Show separator line
        page.add_line(0, 40, self.width, 40)
        
        self.show_page("track_info")
    
    def show_volume(self, volume: int, max_volume: int = 100):
        """Show volume level with progress bar"""
        if "volume" not in self.pages:
            page = self.create_page("volume")
        else:
            page = self.pages["volume"]
            page.clear()
        
        # Volume label
        page.add_text("Volume", 0, 0, font_name="default")
        
        # Volume percentage
        page.add_text(f"{volume}%", self.width - 30, 0, font_name="default")
        
        # Volume bar
        bar_width = self.width - 4
        page.add_progress_bar(2, 20, bar_width, 8, volume, max_volume)
        
        self.show_page("volume")
    
    def show_menu(self, title: str, options: List[str], selected_index: int = 0):
        """Show menu with options"""
        if "menu" not in self.pages:
            page = self.create_page("menu")
        else:
            page = self.pages["menu"]
            page.clear()
        
        # Menu title
        page.add_text(title, 0, 0, font_name="default")
        page.add_line(0, 12, self.width, 12)
        
        # Show current option (centered)
        if 0 <= selected_index < len(options):
            option_text = options[selected_index]
            page.add_text(option_text, self.width // 2, 25, font_name="large", anchor="mm")
            
            # Show navigation info
            nav_text = f"{selected_index + 1}/{len(options)}"
            page.add_text(nav_text, self.width - 1, self.height - 10, font_name="small", anchor="rb")
        
        self.show_page("menu")
    
    def show_status_message(self, message: str, icon: str = "i"):
        """Show a status message"""
        if "status" not in self.pages:
            page = self.create_page("status")
        else:
            page = self.pages["status"]
            page.clear()
        
        # Icon
        page.add_text(icon, 0, 0, font_name="large")
        
        # Message
        page.add_text(message, 20, 8, font_name="default", id="status_msg")
        
        self.show_page("status")


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Create and initialize display
    display = DisplayController(DisplayType.SSD1306_128x64)
    
    if display.initialize():
        print("DisplayController initialized successfully")
        
        try:
            # Test different display modes
            print("Testing track info display...")
            display.show_track_info("Long Song Title That Should Scroll", "Artist Name", "Album Name", True)
            time.sleep(3)
            
            print("Testing volume display...")
            display.show_volume(75)
            time.sleep(2)
            
            print("Testing menu display...")
            display.show_menu("Playlists", ["Rock Classics", "Jazz Collection", "Electronic"], 1)
            time.sleep(2)
            
            print("Testing status message...")
            display.show_status_message("Connected to Spotify", "♪")
            time.sleep(2)
            
            print("Test completed successfully")
            
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            display.cleanup()
    else:
        print("Failed to initialize DisplayController")
        sys.exit(1)
