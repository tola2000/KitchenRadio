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
        
        # Try to load system fonts, fall back to default
        font_sizes = {'small': FONT_SMALL, 'medium': FONT_MEDIUM, 'large': FONT_LARGE, 'xlarge': FONT_XLARGE}
        
        for name, size in font_sizes.items():
            try:
                # Try to load a monospace font
                fonts[name] = ImageFont.truetype("consola.ttf", size)
            except (OSError, IOError):
                try:
                    # Try another common font
                    fonts[name] = ImageFont.truetype("arial.ttf", size)
                except (OSError, IOError):
                    # Fall back to default font
                    fonts[name] = default_font
        
        fonts['default'] = default_font
        return fonts
    
    def _truncate_text(self, text: str, max_width: int, font: ImageFont.ImageFont) -> str:
        """Truncate text to fit within max_width pixels"""
        if not text:
            return ""
        
        # Check if text fits as-is
        bbox = font.getbbox(text)
        if bbox[2] - bbox[0] <= max_width:
            return text
        
        # Truncate with ellipsis
        for i in range(len(text), 0, -1):
            truncated = text[:i] + "..."
            bbox = font.getbbox(truncated)
            if bbox[2] - bbox[0] <= max_width:
                return truncated
        return "..."
    
    def format_simple_text(self, main_text: str, sub_text: str = "") -> Callable:
        """
        Format simple text display.
        
        Args:
            main_text: Main text to display
            sub_text: Optional subtitle text
            
        Returns:
            Drawing function that can be used with display interface
        """
        def draw_simple_text(draw):
            font_main = self.fonts['medium']
            font_sub = self.fonts['small']
            
            # Main text
            main_truncated = self._truncate_text(main_text, self.width - 20, font_main)
            draw.text((10, 15), main_truncated, font=font_main, fill=255)
            
            # Sub text if provided
            if sub_text:
                sub_truncated = self._truncate_text(sub_text, self.width - 20, font_sub)
                draw.text((10, 35), sub_truncated, font=font_sub, fill=255)
        
        return draw_simple_text
    
    def format_status(self, status_data: Dict[str, Any]) -> Callable:
        """
        Format status display with current source and playback info.
        
        Args:
            status_data: Dictionary containing status information
            
        Returns:
            Drawing function that can be used with display interface
        """
        def draw_status(draw):
            y_pos = 5
            font_small = self.fonts['small']
            font_medium = self.fonts['medium']
            
            # Current source header
            current_source = status_data.get('current_source', 'None')
            source_text = f"Source: {current_source.upper()}"
            draw.text((5, y_pos), source_text, font=font_medium, fill=255)
            y_pos += 20
            
            # Source-specific information
            if current_source == 'mpd' and 'mpd' in status_data:
                mpd_info = status_data['mpd']
                if mpd_info.get('connected'):
                    state = mpd_info.get('state', 'unknown')
                    volume = mpd_info.get('volume', 'unknown')
                    
                    # State and volume
                    draw.text((5, y_pos), f"State: {state} | Vol: {volume}%", font=font_small, fill=255)
                    y_pos += 12
                    
                    # Current song if available
                    current_song = mpd_info.get('current_song')
                    if current_song and current_song.get('title'):
                        title = self._truncate_text(current_song.get('title', ''), self.width - 10, font_small)
                        artist = self._truncate_text(current_song.get('artist', ''), self.width - 10, font_small)
                        
                        draw.text((5, y_pos), title, font=font_small, fill=255)
                        y_pos += 12
                        if artist:
                            draw.text((5, y_pos), f"by {artist}", font=font_small, fill=200)
                else:
                    draw.text((5, y_pos), "MPD: Not connected", font=font_small, fill=128)
            
            elif current_source == 'librespot' and 'librespot' in status_data:
                spotify_info = status_data['librespot']
                if spotify_info.get('connected'):
                    state = spotify_info.get('state', 'unknown')
                    volume = spotify_info.get('volume', 'unknown')
                    
                    # State and volume
                    draw.text((5, y_pos), f"State: {state} | Vol: {volume}%", font=font_small, fill=255)
                    y_pos += 12
                    
                    # Current track if available
                    current_track = spotify_info.get('current_track')
                    if current_track and current_track.get('name'):
                        track = self._truncate_text(current_track.get('name', ''), self.width - 10, font_small)
                        artist = self._truncate_text(current_track.get('artist', ''), self.width - 10, font_small)
                        
                        draw.text((5, y_pos), track, font=font_small, fill=255)
                        y_pos += 12
                        if artist:
                            draw.text((5, y_pos), f"by {artist}", font=font_small, fill=200)
                else:
                    draw.text((5, y_pos), "Spotify: Not connected", font=font_small, fill=128)
            
            else:
                draw.text((5, y_pos), "Please select a source", font=font_small, fill=128)
            
            # Border
            draw.rectangle([(2, 2), (self.width-3, self.height-3)], outline=255)
        
        return draw_status
    
    def format_volume_display(self, volume: int, max_volume: int = 100) -> Callable:
        """
        Format volume display with progress bar.
        
        Args:
            volume: Current volume level
            max_volume: Maximum volume level
            
        Returns:
            Drawing function that can be used with display interface
        """
        def draw_volume(draw):
            font_large = self.fonts['large']
            font_medium = self.fonts['medium']
            
            # Volume text
            volume_text = f"Volume: {volume}%"
            draw.text((10, 10), volume_text, font=font_large, fill=255)
            
            # Progress bar
            bar_width = self.width - 40
            bar_height = 12
            bar_x = 20
            bar_y = 35
            
            # Background
            draw.rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)], outline=255)
            
            # Fill
            fill_width = int((volume / max_volume) * (bar_width - 2))
            if fill_width > 0:
                draw.rectangle([(bar_x + 1, bar_y + 1), (bar_x + 1 + fill_width, bar_y + bar_height - 1)], fill=255)
        
        return draw_volume
    
    def format_error_message(self, message: str, error_code: str = "") -> Callable:
        """
        Format error message display.
        
        Args:
            message: Error message to display
            error_code: Optional error code
            
        Returns:
            Drawing function that can be used with display interface
        """
        def draw_error(draw):
            font_medium = self.fonts['medium']
            font_small = self.fonts['small']
            
            # Error header
            draw.text((10, 5), "⚠ ERROR", font=font_medium, fill=255)
            
            # Error message
            message_truncated = self._truncate_text(message, self.width - 20, font_small)
            draw.text((10, 25), message_truncated, font=font_small, fill=255)
            
            # Error code if provided
            if error_code:
                code_text = f"Code: {error_code}"
                draw.text((10, 45), code_text, font=font_small, fill=200)
            
            # Border
            draw.rectangle([(5, 5), (self.width-6, self.height-6)], outline=255)
        
        return draw_error
    
    def format_default_display(self) -> Callable:
        """
        Format default display when no specific content is available.
        
        Returns:
            Drawing function that shows KitchenRadio welcome screen
        """
        def draw_default(draw):
            font_large = self.fonts['large']
            font_medium = self.fonts['medium']
            font_small = self.fonts['small']
            
            # Title
            draw.text((10, 8), "KitchenRadio", font=font_large, fill=255)
            
            # Status
            draw.text((10, 32), "Ready to Play", font=font_medium, fill=200)
            draw.text((10, 48), "Select a Source", font=font_small, fill=150)
            
            # Border
            draw.rectangle([(2, 2), (self.width-3, self.height-3)], outline=255)
        
        return draw_default
    
    def format_track_info(self, title: str, artist: str = "", album: str = "", 
                          playing: bool = False, volume: int = 50) -> Callable:
        """
        Format track information display.
        
        Args:
            title: Track title
            artist: Artist name
            album: Album name
            playing: Whether track is currently playing
            volume: Current volume level
            
        Returns:
            Drawing function for track info
        """
        def draw_track_info(draw: ImageDraw.Draw):
            # Clear background
            draw.rectangle([(0, 0), (self.width, self.height)], fill=0)
            
            # Playing indicator
            play_icon = "▶" if playing else "⏸"
            draw.text((5, 5), play_icon, font=self.fonts['medium'], fill=255)
            
            # Title (main line)
            title_text = title[:30] if title else "No Track"
            draw.text((25, 5), title_text, font=self.fonts['medium'], fill=255)
            
            # Artist
            if artist:
                artist_text = f"Artist: {artist[:25]}"
                draw.text((5, 25), artist_text, font=self.fonts['small'], fill=255)
            
            # Album
            if album:
                album_text = f"Album: {album[:25]}"
                draw.text((5, 40), album_text, font=self.fonts['small'], fill=255)
            
            # Volume indicator
            vol_text = f"Vol: {volume}%"
            draw.text((self.width - 60, 50), vol_text, font=self.fonts['small'], fill=255)
            
            # Border
            draw.rectangle([(0, 0), (self.width-1, self.height-1)], outline=255)
        
        return draw_track_info
    
    def format_status_message(self, message: str, icon: str = "", 
                             message_type: str = "info") -> Callable:
        """
        Format status message display.
        
        Args:
            message: Status message text
            icon: Optional icon character
            message_type: Type of message (info, warning, error)
            
        Returns:
            Drawing function for status message
        """
        def draw_status_message(draw: ImageDraw.Draw):
            # Clear background
            draw.rectangle([(0, 0), (self.width, self.height)], fill=0)
            
            # Icon
            if icon:
                draw.text((10, 15), icon, font=self.fonts['large'], fill=255)
                text_x = 40
            else:
                text_x = 10
            
            # Message text (split into lines if needed)
            max_chars = (self.width - text_x - 10) // 8  # Rough estimate
            if len(message) > max_chars:
                lines = [message[i:i+max_chars] for i in range(0, len(message), max_chars)]
            else:
                lines = [message]
            
            # Draw text lines
            y = 15
            for line in lines[:3]:  # Max 3 lines
                draw.text((text_x, y), line, font=self.fonts['medium'], fill=255)
                y += 16
            
            # Border color based on message type
            if message_type == "error":
                # Double border for errors
                draw.rectangle([(0, 0), (self.width-1, self.height-1)], outline=255)
                draw.rectangle([(1, 1), (self.width-2, self.height-2)], outline=255)
            elif message_type == "warning":
                # Dashed-style border for warnings
                for i in range(0, self.width, 4):
                    draw.point((i, 0), fill=255)
                    draw.point((i, self.height-1), fill=255)
                for i in range(0, self.height, 4):
                    draw.point((0, i), fill=255)
                    draw.point((self.width-1, i), fill=255)
            else:
                # Normal border for info
                draw.rectangle([(0, 0), (self.width-1, self.height-1)], outline=255)
        
        return draw_status_message
