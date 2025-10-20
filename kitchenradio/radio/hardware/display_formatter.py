"""
Simplified Display Formatter for SSD1322 256x64 OLED Display

Optimized for KitchenRadio with SSD1322 display only.
Simple, focused implementation without unnecessary complexity.
"""

import logging
from typing import Dict, Optional, Any, Callable
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# SSD1322 Display specifications
DISPLAY_WIDTH = 256  
DISPLAY_HEIGHT = 64

# Font sizes optimized for SSD1322
FONT_SMALL = 10
FONT_MEDIUM = 14
FONT_LARGE = 18
FONT_XLARGE = 24


class DisplayFormatter:
    """
    Simplified display formatter for SSD1322 256x64 OLED display.
    
    Returns drawing functions that can be used with I2C display interface.
    Much simpler than the previous complex element-based system.
    """
    
    def __init__(self, width: int = DISPLAY_WIDTH, height: int = DISPLAY_HEIGHT):
        """Initialize the formatter"""
        self.width = width
        self.height = height
        self.fonts = self._load_fonts()
        self.current_content = None
        
        # For compatibility with existing display_controller.py
        self.pages = {}
        self.current_page = None
        
        logger.info(f"DisplayFormatter initialized for {self.width}x{self.height} display")
    
    def _load_fonts(self) -> Dict[str, ImageFont.ImageFont]:
        """Load fonts optimized for SSD1322"""
        fonts = {}
        default_font = ImageFont.load_default()
        
        try:
            # Try system fonts (Linux/Windows)
            for size_name, size in [('small', FONT_SMALL), ('medium', FONT_MEDIUM), 
                                   ('large', FONT_LARGE), ('xlarge', FONT_XLARGE)]:
                try:
                    fonts[size_name] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
                except (OSError, IOError):
                    try:
                        fonts[size_name] = ImageFont.truetype("arial.ttf", size)
                    except (OSError, IOError):
                        fonts[size_name] = default_font
        except Exception as e:
            logger.warning(f"Font loading failed: {e}")
        
        # Set aliases
        fonts['default'] = fonts.get('medium', default_font)
        return fonts
    
    def _truncate_text(self, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
        """Truncate text to fit within max_width pixels"""
        if not text:
            return ""
        
        bbox = font.getbbox(text)
        if bbox[2] - bbox[0] <= max_width:
            return text
        
        # Truncate with ellipsis
        for i in range(len(text) - 1, 0, -1):
            truncated = text[:i] + "..."
            bbox = font.getbbox(truncated)
            if bbox[2] - bbox[0] <= max_width:
                return truncated
        return "..."
    
    def add_text(self, text: str, x: int, y: int, font_size: int = 12, 
                 font_name: str = "default", color: int = 255, anchor: str = "la",
                 element_id: str = None, scrollable: bool = False):
        """Add text element to the page"""
        element = DisplayElement('text',
            text=text, x=x, y=y, font_size=font_size,
            font_name=font_name, color=color, anchor=anchor,
            id=element_id or f"text_{len(self.elements)}",
            scrollable=scrollable
        )
        self.elements.append(element)
        return element
    
    def add_line(self, x1: int, y1: int, x2: int, y2: int, color: int = 255, width: int = 1):
        """Add line element to the page"""
        element = DisplayElement('line',
            x1=x1, y1=y1, x2=x2, y2=y2, color=color, width=width
        )
        self.elements.append(element)
        return element
    
    def add_rectangle(self, x1: int, y1: int, x2: int, y2: int, 
                     fill: Optional[int] = None, outline: int = 255, width: int = 1):
        """Add rectangle element to the page"""
        element = DisplayElement('rectangle',
            x1=x1, y1=y1, x2=x2, y2=y2, fill=fill, outline=outline, width=width
        )
        self.elements.append(element)
        return element
    
    def add_progress_bar(self, x: int, y: int, width: int, height: int, 
                        value: float, max_value: float = 100.0, 
                        fill_color: int = 255, bg_color: int = 64):
        """Add progress bar element to the page"""
        element = DisplayElement('progress_bar',
            x=x, y=y, width=width, height=height,
            value=value, max_value=max_value,
            fill_color=fill_color, bg_color=bg_color
        )
        self.elements.append(element)
        return element
    
    def add_icon(self, icon: str, x: int, y: int, font_name: str = "large"):
        """Add icon element to the page"""
        element = DisplayElement('icon',
            icon=icon, x=x, y=y, font_name=font_name
        )
        self.elements.append(element)
        return element
    
    def clear(self):
        """Clear all elements from the page"""
        self.elements.clear()
    
    def find_element(self, element_id: str) -> Optional[DisplayElement]:
        """Find element by ID"""
        for element in self.elements:
            if element.id == element_id:
                return element
        return None
    
    def update_element(self, element_id: str, **kwargs) -> bool:
        """Update element by ID"""
        element = self.find_element(element_id)
        if element:
            element.update(**kwargs)
            return True
        return False


class DisplayFormatter:
    """
    Handles display content formatting and layout logic.
    
    Separated from hardware interface for easier testing and flexibility.
    """
    
    def __init__(self, width: int = 128, height: int = 64):
        """
        Initialize display formatter.
        
        Args:
            width: Display width in pixels
            height: Display height in pixels
        """
        self.width = width
        self.height = height
        
        # Content pages
        self.pages: Dict[str, DisplayPage] = {}
        self.current_page = None
        
        # Font management
        self.fonts: Dict[str, ImageFont.ImageFont] = {}
        self._load_default_fonts()
        
        # Animation and scrolling state
        self.scroll_positions: Dict[str, int] = {}
        self.animation_frame = 0
        
        logger.info(f"DisplayFormatter initialized for {width}x{height} display")
    
    def _load_default_fonts(self):
        """Load default fonts for different sizes"""
        try:
            font_sizes = [8, 10, 12, 14, 16, 18, 20, 24]
            
            for size in font_sizes:
                try:
                    # Try monospace font first
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size)
                    self.fonts[f"mono_{size}"] = font
                except (OSError, IOError):
                    try:
                        # Try regular font
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
                        self.fonts[f"default_{size}"] = font
                    except (OSError, IOError):
                        # Fall back to PIL default
                        self.fonts[f"default_{size}"] = ImageFont.load_default()
            
            # Set font aliases
            self.fonts["default"] = self.fonts.get("default_12", ImageFont.load_default())
            self.fonts["small"] = self.fonts.get("default_8", ImageFont.load_default())
            self.fonts["large"] = self.fonts.get("default_16", ImageFont.load_default())
            self.fonts["xlarge"] = self.fonts.get("default_24", ImageFont.load_default())
            self.fonts["mono"] = self.fonts.get("mono_12", ImageFont.load_default())
            
            logger.debug(f"Loaded {len(self.fonts)} fonts")
            
        except Exception as e:
            logger.warning(f"Error loading fonts: {e}")
            self.fonts["default"] = ImageFont.load_default()
    
    def create_page(self, name: str, layout: DisplayLayout = None) -> DisplayPage:
        """Create a new display page"""
        page = DisplayPage(name, layout)
        self.pages[name] = page
        logger.debug(f"Created page '{name}' with layout {layout}")
        return page
    
    def get_page(self, name: str) -> Optional[DisplayPage]:
        """Get existing page by name"""
        return self.pages.get(name)
    
    def set_current_page(self, name: str) -> bool:
        """Set the current active page"""
        if name in self.pages:
            self.current_page = name
            logger.debug(f"Switched to page '{name}'")
            return True
        else:
            logger.warning(f"Page '{name}' not found")
            return False
    
    def get_current_page(self) -> Optional[DisplayPage]:
        """Get the current active page"""
        if self.current_page and self.current_page in self.pages:
            return self.pages[self.current_page]
        return None
    
    def calculate_text_dimensions(self, text: str, font_name: str = "default") -> Tuple[int, int]:
        """Calculate text dimensions"""
        font = self.fonts.get(font_name, self.fonts["default"])
        
        # Create temporary image to measure text
        temp_image = Image.new('1', (1, 1))
        temp_draw = ImageDraw.Draw(temp_image)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        
        return width, height
    
    def format_track_info(self, title: str, artist: str, album: str = "", 
                         playing: bool = False, volume: int = None) -> DisplayPage:
        """Format track information display"""
        page_name = "track_info"
        
        if page_name in self.pages:
            page = self.pages[page_name]
            page.clear()
        else:
            page = self.create_page(page_name, DisplayLayout.TRACK_INFO)
        
        # Status icon
        status_icon = "♪" if playing else "⏸" if not playing else "■"
        page.add_icon(status_icon, 0, 0, "large")
        
        # Track title (with scrolling if needed)
        title_width, _ = self.calculate_text_dimensions(title, "default")
        scrollable = title_width > (self.width - 20)
        page.add_text(title, 20, 0, font_name="default", element_id="title", 
                     scrollable=scrollable)
        
        # Artist
        page.add_text(f"♫ {artist}", 0, 16, font_name="small", element_id="artist")
        
        # Album (if provided)
        if album:
            page.add_text(f"♬ {album}", 0, 28, font_name="small", element_id="album")
        
        # Separator line
        page.add_line(0, 40, self.width - 1, 40)
        
        # Volume indicator if provided
        if volume is not None:
            vol_text = f"Vol: {volume}%"
            vol_width, _ = self.calculate_text_dimensions(vol_text, "small")
            page.add_text(vol_text, self.width - vol_width, self.height - 10, 
                         font_name="small", element_id="volume")
        
        return page
    
    def format_volume_display(self, volume: int, max_volume: int = 100, 
                            muted: bool = False) -> DisplayPage:
        """Format volume display"""
        page_name = "volume"
        
        if page_name in self.pages:
            page = self.pages[page_name]
            page.clear()
        else:
            page = self.create_page(page_name, DisplayLayout.VOLUME)
        
        # Volume icon and label
        vol_icon = "🔇" if muted else "🔊" if volume > 50 else "🔉"
        page.add_icon(vol_icon, 0, 5, "large")
        
        # Volume percentage
        vol_text = "MUTED" if muted else f"{volume}%"
        page.add_text(vol_text, 30, 8, font_name="large", element_id="volume_text")
        
        # Volume bar
        bar_y = 30
        bar_height = 10
        bar_width = self.width - 4
        
        # Background bar
        page.add_rectangle(2, bar_y, 2 + bar_width, bar_y + bar_height, 
                          fill=None, outline=255)
        
        # Volume fill bar
        if not muted and volume > 0:
            fill_width = int((volume / max_volume) * (bar_width - 2))
            page.add_rectangle(3, bar_y + 1, 3 + fill_width, bar_y + bar_height - 1, 
                              fill=255)
        
        # Volume scale markers
        for i in range(0, 101, 25):
            x = 2 + int((i / 100) * bar_width)
            page.add_line(x, bar_y + bar_height + 2, x, bar_y + bar_height + 5)
            if i % 50 == 0:
                page.add_text(str(i), x - 5, bar_y + bar_height + 8, font_name="small")
        
        return page
    
    def format_menu_display(self, title: str, options: List[str], 
                           selected_index: int = 0, show_all: bool = False) -> DisplayPage:
        """Format menu display"""
        page_name = "menu"
        
        if page_name in self.pages:
            page = self.pages[page_name]
            page.clear()
        else:
            page = self.create_page(page_name, DisplayLayout.MENU)
        
        # Menu title
        page.add_text(title, self.width // 2, 0, font_name="default", 
                     anchor="mt", element_id="menu_title")
        page.add_line(0, 12, self.width - 1, 12)
        
        if show_all and len(options) <= 4:
            # Show all options (for small lists)
            start_y = 20
            for i, option in enumerate(options):
                marker = "► " if i == selected_index else "  "
                font_name = "default" if i == selected_index else "small"
                page.add_text(f"{marker}{option}", 2, start_y + i * 12, 
                             font_name=font_name, element_id=f"option_{i}")
        else:
            # Show only current option (centered)
            if 0 <= selected_index < len(options):
                option_text = options[selected_index]
                page.add_text(option_text, self.width // 2, self.height // 2, 
                             font_name="large", anchor="mm", element_id="current_option")
                
                # Navigation arrows
                if selected_index > 0:
                    page.add_text("▲", self.width // 2, 20, font_name="large", anchor="mt")
                if selected_index < len(options) - 1:
                    page.add_text("▼", self.width // 2, self.height - 5, font_name="large", anchor="mb")
        
        # Page indicator
        nav_text = f"{selected_index + 1}/{len(options)}"
        page.add_text(nav_text, self.width - 2, self.height - 2, 
                     font_name="small", anchor="rb", element_id="page_indicator")
        
        return page
    
    def format_source_display(self, sources: List[str], current_source: str, 
                            available_sources: List[str]) -> DisplayPage:
        """Format source selection display"""
        page_name = "source_select"
        
        if page_name in self.pages:
            page = self.pages[page_name]
            page.clear()
        else:
            page = self.create_page(page_name, DisplayLayout.SOURCE_SELECT)
        
        # Title
        page.add_text("AUDIO SOURCE", self.width // 2, 0, font_name="default", 
                     anchor="mt")
        page.add_line(0, 12, self.width - 1, 12)
        
        # Current source (highlighted)
        page.add_text(f"► {current_source.upper()}", self.width // 2, 25, 
                     font_name="large", anchor="mm", element_id="current_source")
        
        # Available sources status
        start_y = 45
        for i, source in enumerate(sources):
            status = "●" if source in available_sources else "○"
            color = 255 if source in available_sources else 64
            page.add_text(f"{status} {source}", 10 + (i * 40), start_y, 
                         font_name="small", color=color, element_id=f"source_{source}")
        
        return page
    
    def format_status_message(self, message: str, icon: str = "ℹ", 
                            message_type: str = "info") -> DisplayPage:
        """Format status message display"""
        page_name = "status"
        
        if page_name in self.pages:
            page = self.pages[page_name]
            page.clear()
        else:
            page = self.create_page(page_name, DisplayLayout.STATUS)
        
        # Icon based on message type
        type_icons = {
            "info": "ℹ",
            "success": "✓",
            "warning": "⚠",
            "error": "✗",
            "connecting": "⟳"
        }
        display_icon = type_icons.get(message_type, icon)
        
        # Icon
        page.add_icon(display_icon, 5, 5, "xlarge")
        
        # Message text (with word wrapping if needed)
        message_lines = self._wrap_text(message, "default", self.width - 35)
        start_y = 8
        
        for i, line in enumerate(message_lines):
            page.add_text(line, 35, start_y + i * 12, font_name="default", 
                         element_id=f"message_line_{i}")
        
        return page
    
    def format_clock_display(self, time_str: str, date_str: str = None) -> DisplayPage:
        """Format clock display"""
        page_name = "clock"
        
        if page_name in self.pages:
            page = self.pages[page_name]
            page.clear()
        else:
            page = self.create_page(page_name, DisplayLayout.CLOCK)
        
        # Time (large, centered)
        page.add_text(time_str, self.width // 2, self.height // 2 - 5, 
                     font_name="xlarge", anchor="mm", element_id="time")
        
        # Date (smaller, below time)
        if date_str:
            page.add_text(date_str, self.width // 2, self.height // 2 + 15, 
                         font_name="default", anchor="mt", element_id="date")
        
        return page
    
    def _wrap_text(self, text: str, font_name: str, max_width: int) -> List[str]:
        """Wrap text to fit within specified width"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            text_width, _ = self.calculate_text_dimensions(test_line, font_name)
            
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def get_scrollable_text(self, element_id: str, text: str) -> str:
        """Get scrolled text for scrollable elements"""
        if element_id not in self.scroll_positions:
            self.scroll_positions[element_id] = 0
        
        text_len = len(text)
        if text_len <= 20:  # No need to scroll short text
            return text
        
        scroll_pos = self.scroll_positions[element_id]
        
        # Create scrolling effect with padding
        scrolled_text = text[scroll_pos:] + "   " + text[:scroll_pos]
        
        # Update scroll position (slow scroll)
        self.animation_frame += 1
        if self.animation_frame % 10 == 0:  # Update every 10 frames
            self.scroll_positions[element_id] = (scroll_pos + 1) % text_len
        
        return scrolled_text[:20]  # Return first 20 characters
    
    def update_animation_frame(self):
        """Update animation frame counter"""
        self.animation_frame += 1
    
    def reset_scroll_positions(self):
        """Reset all scroll positions"""
        self.scroll_positions.clear()


# Example usage and testing
if __name__ == "__main__":
    # Create formatter
    formatter = DisplayFormatter(128, 64)
    
    # Test track info formatting
    page = formatter.format_track_info(
        "This is a very long song title that should scroll",
        "Artist Name",
        "Album Name",
        playing=True,
        volume=85
    )
    
    print(f"Track info page created with {len(page.elements)} elements")
    
    # Test volume formatting
    vol_page = formatter.format_volume_display(75, muted=False)
    print(f"Volume page created with {len(vol_page.elements)} elements")
    
    # Test menu formatting
    menu_page = formatter.format_menu_display(
        "Playlists",
        ["Rock Classics", "Jazz Collection", "Electronic Music", "Classical"],
        selected_index=1
    )
    print(f"Menu page created with {len(menu_page.elements)} elements")
    
    print("DisplayFormatter test completed successfully")
