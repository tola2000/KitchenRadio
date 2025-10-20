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
            # Clear background
            draw.rectangle([(0, 0), (self.width, self.height)], fill=0)
            
            # Large volume bar on the left side (wider for volume-only display)
            bar_width = 16
            bar_height = self.height - 20  # Leave margin top/bottom
            bar_x = 10
            bar_y = 10
            
            # Draw volume bar background
            draw.rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)], outline=255, width=2)
            
            # Draw volume bar fill
            if volume > 0:
                fill_height = int((volume / max_volume) * (bar_height - 4))
                fill_y = bar_y + bar_height - 2 - fill_height  # Fill from bottom up
                draw.rectangle([(bar_x + 2, fill_y), (bar_x + bar_width - 2, bar_y + bar_height - 2)], fill=255)
            
            # Content area starts after the volume bar
            content_x = bar_x + bar_width + 15
            
            # Large volume text
            volume_text = f"VOLUME"
            draw.text((content_x, 15), volume_text, font=self.fonts['large'], fill=255)
            
            # Volume percentage
            volume_pct = f"{volume}%"
            draw.text((content_x, 35), volume_pct, font=self.fonts['medium'], fill=255)
            
            # Volume level indicators (small marks on the right)
            marks_x = self.width - 30
            marks_y = bar_y
            mark_spacing = bar_height // 10
            
            for i in range(11):  # 0%, 10%, 20%, ... 100%
                y = marks_y + (i * mark_spacing)
                if i * 10 <= volume:
                    # Filled mark
                    draw.rectangle([(marks_x, y), (marks_x + 8, y + 2)], fill=255)
                else:
                    # Empty mark
                    draw.rectangle([(marks_x, y), (marks_x + 8, y + 2)], outline=255)
            
            # Border around entire display
            draw.rectangle([(0, 0), (self.width-1, self.height-1)], outline=255)
        
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
            
            # Volume bar on the left side (vertical bar)
            bar_width = 8
            bar_height = self.height - 10  # Leave some margin top/bottom
            bar_x = 5
            bar_y = 5
            
            # Draw volume bar background (empty bar)
            draw.rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)], outline=255)
            
            # Draw volume bar fill (filled portion based on volume)
            if volume > 0:
                fill_height = int((volume / 100.0) * bar_height)
                fill_y = bar_y + bar_height - fill_height  # Fill from bottom up
                draw.rectangle([(bar_x + 1, fill_y), (bar_x + bar_width - 1, bar_y + bar_height - 1)], fill=255)
            
            # Volume percentage text below the bar
            vol_text = f"{volume}%"
            draw.text((bar_x - 2, bar_y + bar_height + 2), vol_text, font=self.fonts['small'], fill=255)
            
            # Content area starts after the volume bar
            content_x = bar_x + bar_width + 10
            content_width = self.width - content_x - 5
            
            # Title (main line) - truncate to fit in available space
            title_text = title if title else "No Track"
            title_max_width = content_width - 10
            title_truncated = self._truncate_text(title_text, title_max_width, self.fonts['medium'])
            draw.text((content_x, 5), title_truncated, font=self.fonts['medium'], fill=255)
            
            # Artist - truncate to fit
            if artist:
                artist_text = f"Artist: {artist}"
                artist_truncated = self._truncate_text(artist_text, content_width, self.fonts['small'])
                draw.text((content_x, 25), artist_truncated, font=self.fonts['small'], fill=255)
            
            # Album - truncate to fit
            if album:
                album_text = f"Album: {album}"
                album_truncated = self._truncate_text(album_text, content_width, self.fonts['small'])
                draw.text((content_x, 40), album_truncated, font=self.fonts['small'], fill=255)
            
            # Large play/pause/stop icon in bottom right corner
            play_icon = "▶" if playing else "⏸"
            icon_font = self.fonts['xlarge']  # Use extra large font for the icon
            
            # Calculate position for bottom right alignment
            # Get approximate icon size (this is rough estimation)
            icon_width = 20  # Approximate width of large icon
            icon_height = 24  # Approximate height of large icon
            icon_x = self.width - icon_width - 5  # 5px margin from right edge
            icon_y = self.height - icon_height - 5  # 5px margin from bottom edge
            
            draw.text((icon_x, icon_y), play_icon, font=icon_font, fill=255)
            
            # Border around entire display
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
