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
FONT_SMALL = 12
FONT_MEDIUM = 14
FONT_LARGE = 16
FONT_XLARGE = 18
FONT_XXLARGE = 28

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
        
        # Scrolling state tracking
        self.scroll_offset = 0
        self.scroll_speed = 2  # pixels per update
        self.scroll_pause_time = 30  # frames to pause at start/end
        self.scroll_pause_counter = 0
        self.scrolling_enabled = True
        
        # For compatibility with existing display_controller.py
        self.pages = {}
        self.current_page = None
        
        logger.info(f"DisplayFormatter initialized for {self.width}x{self.height} display")
    
    def _load_fonts(self) -> Dict[str, ImageFont.ImageFont]:
        """Load HomeVideo font for retro kitchen radio aesthetic"""
        import os
        
        fonts = {}
        default_font = ImageFont.load_default()
        
        # Project font paths for HomeVideo font
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        font_paths = [
            os.path.join(project_root, "frontend", "static", "fonts"),
            os.path.join(project_root, "static", "fonts"),
            os.path.join(project_root, "fonts"),
            os.path.join(os.path.dirname(__file__), "fonts"),
        ]
        
        # HomeVideo font variations
        homevideo_fonts = [
            "homevideo.ttf", "HomeVideo.ttf", "homevideo-regular.ttf", "HomeVideo-Regular.ttf",
            "homevideo.otf", "HomeVideo.otf", "homevideo-regular.otf", "HomeVideo-Regular.otf",
        ]
        
        # Try to find HomeVideo font
        homevideo_path = None
        for font_name in homevideo_fonts:
            # Try direct name first
            try:
                ImageFont.truetype(font_name, 12)  # Test load
                homevideo_path = font_name
                break
            except (OSError, IOError):
                pass
            
            # Search in project font paths
            for path in font_paths:
                if os.path.exists(path):
                    font_file = os.path.join(path, font_name)
                    if os.path.exists(font_file):
                        homevideo_path = font_file
                        break
            
            if homevideo_path:
                break
        
        # Load fonts for all sizes
        font_sizes = {'small': FONT_SMALL, 'medium': FONT_MEDIUM, 'large': FONT_LARGE, 'xlarge': FONT_XLARGE, 'xxlarge': FONT_XXLARGE}
        
        for name, size in font_sizes.items():
            if homevideo_path:
                try:
                    fonts[name] = ImageFont.truetype(homevideo_path, size)
                    logger.info(f"Loaded HomeVideo font '{homevideo_path}' for size '{name}' ({size}px)")
                except (OSError, IOError) as e:
                    logger.warning(f"Failed to load HomeVideo font: {e}")
                    fonts[name] = default_font
            else:
                fonts[name] = default_font
                logger.warning(f"HomeVideo font not found, using default font for size '{name}'")
        
        fonts['default'] = default_font
        
        if homevideo_path:
            logger.info("HomeVideo font loaded successfully for retro kitchen radio display")
        else:
            logger.warning("HomeVideo font not found - place homevideo.ttf in frontend/static/fonts/ folder")
        
        return fonts
    
    def _format_text(self, text: str, max_width: int, font: ImageFont.ImageFont, 
                     scroll_offset: int = 0, font_size: str = 'small', return_info: bool = False):
        """
        Unified text formatting function that handles both truncation and scrolling.
        
        Args:
            text: Original text to format
            max_width: Maximum width in pixels
            font: Font to use for measurement
            scroll_offset: Scroll position in pixels (0 = no scrolling, use truncation)
            font_size: Font size identifier for truncation info
            return_info: If True, return truncation info structure
            
        Returns:
            If return_info=False: Formatted text string
            If return_info=True: Dict with truncation info structure:
                {
                    'displayed': str,
                    'truncated': bool,
                    'original_width': int,
                    'max_width': int,
                    'scroll_offset': int,
                    'font_size': str
                }
        """
        if not text:
            if return_info:
                return {
                    'displayed': "",
                    'truncated': False,
                    'original_width': 0,
                    'max_width': max_width,
                    'scroll_offset': scroll_offset,
                    'font_size': font_size
                }
            return ""
        
        # Get full text width
        bbox = font.getbbox(text)
        full_width = bbox[2] - bbox[0]
        
        # If text fits within max_width, return as-is
        if full_width <= max_width:
            if return_info:
                return {
                    'displayed': text,
                    'truncated': False,
                    'original_width': full_width,
                    'max_width': max_width,
                    'scroll_offset': scroll_offset,
                    'font_size': font_size
                }
            return text
        
        # Handle scrolling mode (scroll_offset > 0)
        if scroll_offset > 0:
            # Add padding for smooth scrolling loop
            padding = "    "  # 4 spaces padding
            scrolling_text = text + padding + text
            
            # Calculate scroll position with wraparound
            scroll_pos = scroll_offset % (full_width + len(padding) * 8)  # Approximate space width
            
            # Find the starting character position
            current_width = 0
            start_char = 0
            
            for i, char in enumerate(scrolling_text):
                char_bbox = font.getbbox(char)
                char_width = char_bbox[2] - char_bbox[0]
                if current_width >= scroll_pos:
                    start_char = i
                    break
                current_width += char_width
            
            # Get visible portion that fits in max_width
            visible_text = ""
            current_width = 0
            
            for char in scrolling_text[start_char:]:
                test_text = visible_text + char
                test_bbox = font.getbbox(test_text)
                test_width = test_bbox[2] - test_bbox[0]
                if test_width > max_width:
                    break
                visible_text = test_text
            
            if return_info:
                return {
                    'displayed': visible_text,
                    'truncated': True,  # Scrolling implies text was too long
                    'original_width': full_width,
                    'max_width': max_width,
                    'scroll_offset': scroll_offset,
                    'font_size': font_size
                }
            return visible_text
        
        # Handle truncation mode (scroll_offset = 0)
        else:
            # Truncate with ellipsis
            for i in range(len(text), 0, -1):
                truncated = text[:i] + "..."
                bbox = font.getbbox(truncated)
                if bbox[2] - bbox[0] <= max_width:
                    if return_info:
                        return {
                            'displayed': truncated,
                            'truncated': True,
                            'original_width': full_width,
                            'max_width': max_width,
                            'scroll_offset': scroll_offset,
                            'font_size': font_size
                        }
                    return truncated
            
            # Fallback if even "..." doesn't fit
            if return_info:
                return {
                    'displayed': "...",
                    'truncated': True,
                    'original_width': full_width,
                    'max_width': max_width,
                    'scroll_offset': scroll_offset,
                    'font_size': font_size
                }
            return "..."
    
    def format_simple_text(self, text_data: Dict[str, Any]) -> Callable:
        """
        Format simple text display using JSON structure input.
        
        Args:
            text_data: Dictionary containing:
                {
                    "main_text": str,
                    "sub_text": str (optional),
                    "scroll_offsets": {
                        "main_text": int,
                        "sub_text": int
                    } (optional)
                }
            
        Returns:
            Drawing function that can be used with display interface
        """
        # Extract data from JSON structure
        main_text = text_data.get('main_text', '')
        sub_text = text_data.get('sub_text', '')
        scroll_offsets = text_data.get('scroll_offsets', {})
        
        font_main = self.fonts['large']
        font_sub = self.fonts['small']
        max_width = self.width - 20
        
        # Process all text at start of method
        main_offset = scroll_offsets.get('main_text', 0)
        main_displayed = self._format_text(main_text, max_width, font_main, main_offset, 'medium')
        
        sub_displayed = None
        if sub_text:
            sub_offset = scroll_offsets.get('sub_text', 0)
            sub_displayed = self._format_text(sub_text, max_width, font_sub, sub_offset, 'small')
        
        def draw_simple_text(draw):
            # Draw pre-processed text
            draw.text((10, 15), main_displayed, font=font_main, fill=255)
            
            if sub_displayed:
                draw.text((10, 35), sub_displayed, font=font_sub, fill=255)
        
        return draw_simple_text
    
    def format_status(self, status_data: Dict[str, Any]) -> Callable:
        """
        Format status display with current source and playback info using JSON structure input.
        
        Args:
            status_data: Dictionary containing:
                {
                    "current_source": str,
                    "mpd": dict (optional),
                    "librespot": dict (optional),
                    "scroll_offsets": {
                        "mpd_title": int,
                        "mpd_artist": int,
                        "spotify_track": int,
                        "spotify_artist": int
                    } (optional)
                }
            
        Returns:
            Drawing function that can be used with display interface
        """
        # Extract data from JSON structure
        current_source = status_data.get('current_source', 'None')
        offsets = status_data.get('scroll_offsets', {})
        font_small = self.fonts['small']
        font_medium = self.fonts['medium']
        max_width = self.width - 10
        
        # Pre-process all text elements
        source_text = f"Source: {current_source.upper()}"
        
        # Initialize processed text variables
        mpd_title_displayed = None
        mpd_artist_displayed = None
        spotify_track_displayed = None
        spotify_artist_displayed = None
        mpd_connected = False
        spotify_connected = False
        mpd_state_volume = None
        spotify_state_volume = None
        
        # Process MPD text if available
        if current_source == 'mpd' and 'mpd' in status_data:
            mpd_info = status_data['mpd']
            mpd_connected = mpd_info.get('connected', False)
            if mpd_connected:
                state = mpd_info.get('state', 'unknown')
                volume = mpd_info.get('volume', 'unknown')
                mpd_state_volume = f"State: {state} | Vol: {volume}%"
                
                current_song = mpd_info.get('current_song')
                if current_song and current_song.get('title'):
                    title_text = current_song.get('title', '')
                    artist_text = current_song.get('artist', '')
                    
                    title_offset = offsets.get('mpd_title', 0)
                    mpd_title_displayed = self._format_text(title_text, max_width, font_small, title_offset, 'small')
                    
                    artist_offset = offsets.get('mpd_artist', 0)
                    mpd_artist_displayed = self._format_text(artist_text, max_width, font_small, artist_offset, 'small')
        
        # Process Spotify text if available
        elif current_source == 'librespot' and 'librespot' in status_data:
            spotify_info = status_data['librespot']
            spotify_connected = spotify_info.get('connected', False)
            if spotify_connected:
                state = spotify_info.get('state', 'unknown')
                volume = spotify_info.get('volume', 'unknown')
                spotify_state_volume = f"State: {state} | Vol: {volume}%"
                
                current_track = spotify_info.get('current_track')
                if current_track and current_track.get('name'):
                    track_text = current_track.get('name', '')
                    artist_text = current_track.get('artist', '')
                    
                    track_offset = offsets.get('spotify_track', 0)
                    spotify_track_displayed = self._format_text(track_text, max_width, font_small, track_offset, 'small')
                    
                    artist_offset = offsets.get('spotify_artist', 0)
                    spotify_artist_displayed = self._format_text(artist_text, max_width, font_small, artist_offset, 'small')
        
        def draw_status(draw):
            y_pos = 5
            
            # Draw source header
            draw.text((5, y_pos), source_text, font=font_medium, fill=255)
            y_pos += 20
            
            # Draw source-specific information using pre-processed text
            if current_source == 'mpd':
                if mpd_connected:
                    draw.text((5, y_pos), mpd_state_volume, font=font_small, fill=255)
                    y_pos += 12
                    
                    if mpd_title_displayed:
                        draw.text((5, y_pos), mpd_title_displayed, font=font_small, fill=255)
                        y_pos += 12
                        if mpd_artist_displayed:
                            draw.text((5, y_pos), f"by {mpd_artist_displayed}", font=font_small, fill=200)
                else:
                    draw.text((5, y_pos), "MPD: Not connected", font=font_small, fill=128)
            
            elif current_source == 'librespot':
                if spotify_connected:
                    draw.text((5, y_pos), spotify_state_volume, font=font_small, fill=255)
                    y_pos += 12
                    
                    if spotify_track_displayed:
                        draw.text((5, y_pos), spotify_track_displayed, font=font_small, fill=255)
                        y_pos += 12
                        if spotify_artist_displayed:
                            draw.text((5, y_pos), f"by {spotify_artist_displayed}", font=font_small, fill=200)
                else:
                    draw.text((5, y_pos), "Spotify: Not connected", font=font_small, fill=128)
            
            else:
                draw.text((5, y_pos), "Please select a source", font=font_small, fill=128)
        
        return draw_status
    
    
    def format_error_message(self, error_data: Dict[str, Any]) -> Callable:
        """
        Format error message display using JSON structure input.
        
        Args:
            error_data: Dictionary containing:
                {
                    "message": str,
                    "error_code": str (optional),
                    "scroll_offsets": {
                        "error_message": int
                    } (optional)
                }
            
        Returns:
            Drawing function that can be used with display interface
        """
        # Extract and process data at start
        message = error_data.get('message', '')
        error_code = error_data.get('error_code', '')
        scroll_offsets = error_data.get('scroll_offsets', {})
        
        font_medium = self.fonts['medium']
        font_small = self.fonts['small']
        max_width = self.width - 20
        
        # Pre-process message text
        message_offset = scroll_offsets.get('error_message', 0)
        message_displayed = self._format_text(message, max_width, font_small, message_offset, 'small')
        
        # Pre-process error code text
        code_text = f"Code: {error_code}" if error_code else None
        
        def draw_error(draw):
            # Error header
            draw.text((10, 5), "⚠ ERROR", font=font_medium, fill=255)
            
            # Error message
            draw.text((10, 25), message_displayed, font=font_small, fill=255)
            
            # Error code if provided
            if code_text:
                draw.text((10, 45), code_text, font=font_small, fill=200)
        
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
        
        return draw_default
    
    def format_status_message(self, message_data: Dict[str, Any]) -> tuple:
        """
        Format status message display using JSON structure input.
        
        Args:
            message_data: Dictionary containing:
                {
                    "message": str,
                    "icon": str (optional),
                    "message_type": str (optional, default: "info"),
                    "scroll_offsets": {
                        "message": int
                    } (optional)
                }
            
        Returns:
            Tuple of (drawing_function, truncation_info_dict)
        """
        # Extract and process data at start
        message = message_data.get('message', '')
        icon = message_data.get('icon', '')
        message_type = message_data.get('message_type', 'info')
        scroll_offsets = message_data.get('scroll_offsets', {})
        
        # Calculate layout
        text_x = 40 if icon else 10
        max_width = self.width - text_x - 10
        
        # Track truncation information
        truncation_info = {}
        
        # Pre-process message text
        message_offset = scroll_offsets.get('message', 0)
        message_info = self._format_text(message, max_width, self.fonts['medium'], message_offset, 'medium', return_info=True)
        message_displayed = message_info['displayed']
        # Use fixed key for truncation info
        truncation_info['message'] = message_info
        
        def draw_status_message(draw: ImageDraw.Draw):
            # Clear background
            draw.rectangle([(0, 0), (self.width, self.height)], fill=0)
            
            # Icon
            if icon:
                draw.text((10, 15), icon, font=self.fonts['large'], fill=255)
            
            # Message text
            if message_offset > 0:
                # Single line with scrolling
                draw.text((text_x, 20), message_displayed, font=self.fonts['medium'], fill=255)
            else:
                # Split into lines if needed
                max_chars = max_width // 8  # Rough estimate
                if len(message_displayed) > max_chars:
                    lines = [message_displayed[i:i+max_chars] for i in range(0, len(message_displayed), max_chars)]
                else:
                    lines = [message_displayed]
                
                # Draw text lines
                y = 15
                for line in lines[:3]:  # Max 3 lines
                    draw.text((text_x, y), line, font=self.fonts['medium'], fill=255)
                    y += 16
        
        return draw_status_message, truncation_info
    
    def format_volume_display(self, volume_data: Dict[str, Any]) -> Callable:
        """
        Format full screen volume display with large bar spanning entire display using JSON structure input.
        
        Args:
            volume_data: Dictionary containing:
                {
                    "volume": int,
                    "max_volume": int (optional, default 100),
                    "title": str (optional, default "VOLUME"),
                    "show_percentage": bool (optional, default True),
                    "show_numeric": bool (optional, default False)
                }
            
        Returns:
            Drawing function for full screen volume display
        """
        def draw_volume(draw):
            # Extract data from JSON structure
            volume = int(volume_data.get('volume', 0))
            max_volume = volume_data.get('max_volume', 100)
            title = volume_data.get('title', 'VOLUME')
            show_percentage = volume_data.get('show_percentage', True)
            show_numeric = volume_data.get('show_numeric', False)
            
            # Clear background
            draw.rectangle([(0, 0), (self.width, self.height)], fill=0)
            
            # Full screen volume bar
            bar_margin = 8
            bar_width = self.width - (2 * bar_margin)
            bar_height = self.height - 30  # Leave space for text at top
            bar_x = bar_margin
            bar_y = 25
            
            # Draw title text at top center
            text_width = len(title) * 12  # Estimate width
            text_x = (self.width - text_width) // 2
            draw.text((text_x, 5), title, font=self.fonts['large'], fill=255)
            
            # Draw outer border of volume bar
            draw.rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)], outline=255, width=3)
            
            # Calculate fill area
            volume_integer = int(volume)
            if volume_integer and volume_integer > 0:
                fill_width = int((volume_integer / max_volume) * (bar_width - 6))
                if fill_width > 0:
                    # Draw filled portion from left
                    draw.rectangle([
                        (bar_x + 3, bar_y + 3), 
                        (bar_x + 3 + fill_width, bar_y + bar_height - 3)
                    ], fill=255)
            
            # Add percentage or numeric display if requested
            if show_percentage or show_numeric:
                info_y = bar_y + bar_height + 5
                if show_percentage:
                    percentage = int((volume / max_volume) * 100)
                    percentage_text = f"{percentage}%"
                    info_x = (self.width - len(percentage_text) * 8) // 2
                    draw.text((info_x, info_y), percentage_text, font=self.fonts['medium'], fill=255)
                elif show_numeric:
                    numeric_text = f"{volume}/{max_volume}"
                    info_x = (self.width - len(numeric_text) * 8) // 2
                    draw.text((info_x, info_y), numeric_text, font=self.fonts['medium'], fill=255)
            

 
        
        return draw_volume
    
    def format_track_info(self, track_data: Dict[str, Any]) -> tuple:
        """
        Format track information display using JSON structure input.
        
        Args:
            track_data: Dictionary containing:
                {
                    "title": str,
                    "artist": str,
                    "album": str,
                    "length": int (optional),
                    "time_position": int (optional),
                    "playing": bool (optional, default: False),
                    "volume": int (optional, default: 50),
                    "scroll_offsets": {
                        "title": int,
                        "artist_album": int
                    } (optional)
                }
            
        Returns:
            Tuple of (drawing_function, truncation_info_dict)
            truncation_info_dict structure:
            {
                "original_string": {
                    "displayed": "formatted_string",
                    "truncated": bool,
                    "original_width": int,
                    "max_width": int,
                    "scroll_offset": int,
                    "font_size": str
                }
            }
        """
        # Extract data from JSON structure - now expecting flat structure
        title = track_data.get('title', 'No Track')
        artist = track_data.get('artist', 'Unknown')
        album = track_data.get('album', 'Unknown')
        playing = track_data.get('playing', False)
        volume = track_data.get('volume', 50)
        scroll_offsets = track_data.get('scroll_offsets', {})
        
        # Calculate dimensions
        bar_width = 8
        bar_height = self.height - 10
        bar_x = 5
        bar_y = 5
        content_x = bar_x + bar_width + 10
        content_width = self.width - content_x - 5
        title_max_width = content_width - 10
        
        # Track truncation information - dynamic structure with original strings as keys
        truncation_info = {}
        
        # Pre-process all text elements
        # Process title
        title_offset = scroll_offsets.get('title', 0)
        title_info = self._format_text(
            title, title_max_width, self.fonts['xlarge'], title_offset, 'xlarge', return_info=True)
        
        title_displayed = title_info['displayed']
        truncation_info['title'] = title_info
        
        # Process artist/album
        if not artist == 'Unknown' and not album == 'Unknown':
            artist_album_text = f"{artist} : {album}"
        elif not album == 'Unknown':
            artist_album_text = album
        else:
            artist_album_text = artist
        
        artist_album_offset = scroll_offsets.get('artist_album', 0)
        artist_album_info = self._format_text(
            artist_album_text, content_width, self.fonts['small'], artist_album_offset, 'small', return_info=True)
        
        artist_album_displayed = artist_album_info['displayed']
        truncation_info['artist_album'] = artist_album_info
        
        # Pre-calculate volume bar dimensions
        volume_number = int(volume)
        fill_height = 0
        fill_y = 0
        if volume_number and volume_number > 0:
            fill_height = int((volume_number / 100.0) * bar_height)
            fill_y = bar_y + bar_height - fill_height
        
        # Pre-calculate play icon
        play_icon = "▶" if playing else "⏸"
        icon_size = 28
        icon_x = self.width - icon_size + 2
        icon_y = self.height - icon_size + 2
        
        def draw_track_info_with_progress(draw: ImageDraw.Draw):
            # Clear background
            draw.rectangle([(0, 0), (self.width, self.height)], fill=0)
            
            # Draw volume bar background (empty bar)
            draw.rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)], outline=255)
            
            # Draw volume bar fill (filled portion based on volume)
            if fill_height > 0:
                draw.rectangle([(bar_x + 1, fill_y), (bar_x + bar_width - 1, bar_y + bar_height - 1)], fill=255)
            
            # Draw pre-processed text
            draw.text((content_x, 5), title_displayed, font=self.fonts['xlarge'], fill=255)
            if artist_album_displayed:
                draw.text((content_x, 28), artist_album_displayed, font=self.fonts['small'], fill=255)
            
            # Draw play icon
            draw.text((icon_x, icon_y), play_icon, font=self.fonts['xxlarge'], fill=255)
        
        return draw_track_info_with_progress, truncation_info
    
    def format_menu_display(self, menu_data: Dict[str, Any]) -> Callable:
        """
        Format scrollable menu display with current selection centered using JSON structure input.
        
        Args:
            menu_data: Dictionary containing:
                {
                    "title": str,
                    "menu_items": list,
                    "selected_index": int (optional, default 0),
                    "scroll_offsets": {
                        "selected_item": int
                    } (optional)
                }
            
        Returns:
            Drawing function for scrollable menu display
        """
        # Extract data from JSON structure and pre-calculate constants
        title = menu_data.get('title', '')
        menu_items = menu_data.get('menu_items', [])
        selected_index = menu_data.get('selected_index', 0)
        offsets = menu_data.get('scroll_offsets', {})
        
        # Pre-calculate layout constants
        menu_start_y = 0
        menu_end_y = self.height
        menu_height = menu_end_y - menu_start_y
        line_height = 20
        max_visible_items = menu_height // line_height
        scroll_bar_width = 12
        scroll_bar_margin = 8
        content_right_edge = self.width - scroll_bar_width - scroll_bar_margin - 10
        
        # Pre-calculate menu layout
        total_items = len(menu_items)
        half_visible = max_visible_items // 2
        center_y = menu_start_y + (menu_height // 2) - (line_height // 2)
        
        # Pre-calculate scrollbar dimensions if needed
        bar_width = scroll_bar_width
        bar_height = menu_height - 16
        bar_x = self.width - bar_width - scroll_bar_margin
        bar_y = menu_start_y + 4
        item_height = (bar_height - 4) / total_items if total_items > 0 else 0
        current_item_y = bar_y + 2 + int(selected_index * item_height) if total_items > 0 else 0
        
        def draw_menu(draw: ImageDraw.Draw):
                
            # Clear background
            draw.rectangle([(0, 0), (self.width, self.height)], fill=0)
            
            if not menu_items:
                # No items to display
                draw.text((15, menu_start_y + 10), "No items", font=self.fonts['small'], fill=128)
                return
            
            # Draw fixed selection background in center (don't extend over scroll bar area)
            draw.rectangle([
                (12, center_y - 2), 
                (content_right_edge, center_y + line_height + 1)
            ], fill=255)
            
            
            # Calculate which items to show around the selection
            if total_items <= max_visible_items:
                # All items fit on screen - center them around selection
                start_idx = 0
                items_above_center = selected_index
                items_below_center = total_items - selected_index - 1
                
                # Calculate offset to center the entire list
                total_list_height = total_items * line_height
                available_above = center_y - menu_start_y
                available_below = menu_end_y - (center_y + line_height)
                
                # Offset to center the list when all items fit
                if total_list_height <= menu_height:
                    base_y_offset = (menu_height - total_list_height) // 2
                else:
                    base_y_offset = 0
                    
                # Draw all items with selected item at center
                for i, item in enumerate(menu_items):
                    offset_from_selected = i - selected_index
                    y_pos = center_y + (offset_from_selected * line_height) + base_y_offset
                    
                    # Only draw if within display bounds
                    if menu_start_y <= y_pos <= menu_end_y - line_height:
                        max_item_width = content_right_edge - 40  # Account for arrow and margins
                        
                        # Use scrolling for selected item if offset provided
                        selected_item_offset = offsets.get('selected_item', 0)
                        scroll_offset = selected_item_offset if i == selected_index else 0
                        item_displayed = self._format_text(item, max_item_width, self.fonts['small'], scroll_offset, 'small')
                        
                        if i == selected_index:
                            # Selected item (drawn on white background) - 5 pixels higher
                            draw.text((35, y_pos + 6 ), item_displayed, font=self.fonts['small'], fill=0)
                        else:
                            # Regular item - 5 pixels higher
                            draw.text((35, y_pos + 6), item_displayed, font=self.fonts['small'], fill=255)
            else:
                # Need scrolling - show items around selected with selection fixed at center
                visible_above = half_visible
                visible_below = max_visible_items - visible_above - 1  # -1 for the selected item itself
                
                # Calculate which items to show
                start_idx = max(0, selected_index - visible_above)
                end_idx = min(total_items, selected_index + visible_below + 1)
                
                # Adjust if we're near the boundaries
                if start_idx == 0:
                    end_idx = min(total_items, max_visible_items)
                elif end_idx == total_items:
                    start_idx = max(0, total_items - max_visible_items)
                
                # Draw visible items with selected item always at center
                for i, item_idx in enumerate(range(start_idx, end_idx)):
                    item = menu_items[item_idx]
                    offset_from_selected = item_idx - selected_index
                    y_pos = center_y + (offset_from_selected * line_height)
                    
                    # Only draw if within display bounds
                    if menu_start_y <= y_pos <= menu_end_y - line_height:
                        max_item_width = content_right_edge - 20  # Account for arrow and margins
                        
                        # Use scrolling for selected item if offset provided
                        selected_item_offset = offsets.get('selected_item', 0)
                        scroll_offset = selected_item_offset if item_idx == selected_index else 0
                        item_displayed = self._format_text(item, max_item_width, self.fonts['small'], scroll_offset, 'small')
                        
                        if item_idx == selected_index:
                            # Selected item (drawn on white background) - 5 pixels higher
                            draw.text((15, y_pos + 6), item_displayed, font=self.fonts['small'], fill=0)
                        else:
                            # Regular item - 5 pixels higher
                            draw.text((15, y_pos + 6), item_displayed, font=self.fonts['small'], fill=255)
            
            # Draw scroll position indicator bar (volume bar style)
            if total_items > 1:
                # Draw scroll bar background (outline)
                draw.rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)], outline=255, width=2)
                
                # Draw filled area only for the current selected item
                if item_height > 0:
                    draw.rectangle([
                        (bar_x + 2, current_item_y), 
                        (bar_x + bar_width - 2, current_item_y + int(item_height))
                    ], fill=255)
        return draw_menu
    

    def format_clock_display(self, time_data: Dict[str, Any]) -> Callable:
        """
        Format a retro-style clock display.
        
        Accepts time_data:
            {
                "time": "HH:MM" (preferred),
                "hour": "HH",
                "minute": "MM",
                "date": "Mon 01 Jan" (optional),
                "ampm": True/False (optional, show AM/PM)
            }
        Returns a drawing function for the clock screen.
        """
        # Extract time pieces
        time_str = time_data.get('time')
        hour = time_data.get('hour')
        minute = time_data.get('minute')
        date_str = time_data.get('date', '')
        show_ampm = time_data.get('ampm', False)
        
        if not time_str:
            if hour is None or minute is None:
                # fallback: use empty clock
                hour_text = "--"
                minute_text = "--"
            else:
                hour_text = f"{int(hour):02d}"
                minute_text = f"{int(minute):02d}"
        else:
            parts = str(time_str).split(':')
            hour_text = parts[0].zfill(2)
            minute_text = parts[1].zfill(2) if len(parts) > 1 else "00"
        
        # Optionally determine AM/PM suffix
        ampm_text = ""
        if show_ampm:
            try:
                h = int(hour_text)
                ampm_text = "AM" if h < 12 else "PM"
            except Exception:
                ampm_text = ""
        
        # Choose fonts
        font_hour = self.fonts.get('xxlarge', self.fonts['default'])
        font_min = self.fonts.get('xxlarge', self.fonts['default'])
        font_date = self.fonts.get('medium', self.fonts['default'])
        font_ampm = self.fonts.get('small', self.fonts['default'])
        
        # Pre-calc widths/heights
        # Compose big hour/minute with colon
        colon = ":"
        # Pre-render text widths via getbbox
        hour_bbox = font_hour.getbbox(hour_text)
        hour_w = hour_bbox[2] - hour_bbox[0]
        hour_h = hour_bbox[3] - hour_bbox[1]
        min_bbox = font_min.getbbox(minute_text)
        min_w = min_bbox[2] - min_bbox[0]
        min_h = min_bbox[3] - min_bbox[1]
        colon_bbox = font_hour.getbbox(colon)
        colon_w = colon_bbox[2] - colon_bbox[0]
        colon_h = colon_bbox[3] - colon_bbox[1]
        
        total_width = hour_w + colon_w + min_w
        # center horizontally
        start_x = max(0, (self.width - total_width) // 2)
        hour_x = start_x
        colon_x = hour_x + hour_w
        min_x = colon_x + colon_w
        
        # vertical positions
        clock_top = 6
        hour_y = clock_top
        # align minute baseline a bit lower for visual balance
        min_y = hour_y + (hour_h - min_h)
        date_y = hour_y + max(hour_h, min_h) + 6
        
        def draw_clock(draw: ImageDraw.Draw):
            # Clear background
            draw.rectangle([(0, 0), (self.width, self.height)], fill=0)
            
            # Optional retro shadow: draw slightly offset dark shadow then bright text
            shadow_offset = 1
            # shadow
            draw.text((hour_x + shadow_offset, hour_y + shadow_offset), hour_text, font=font_hour, fill=40)
            draw.text((colon_x + shadow_offset, hour_y + shadow_offset), colon, font=font_hour, fill=40)
            draw.text((min_x + shadow_offset, min_y + shadow_offset), minute_text, font=font_min, fill=40)
            
            # main text (bright)
            draw.text((hour_x, hour_y), hour_text, font=font_hour, fill=255)
            draw.text((colon_x, hour_y), colon, font=font_hour, fill=255)
            draw.text((min_x, min_y), minute_text, font=font_min, fill=255)
            
            # AM/PM if requested
            if ampm_text:
                ampm_bbox = font_ampm.getbbox(ampm_text)
                ampm_w = ampm_bbox[2] - ampm_bbox[0]
                # place AM/PM to the right of minutes
                ampm_x = min(self.width - ampm_w - 6, min_x + min_w + 6)
                ampm_y = hour_y + (hour_h - (ampm_bbox[3] - ampm_bbox[1])) // 2
                draw.text((ampm_x, ampm_y), ampm_text, font=font_ampm, fill=200)
            
            # Date line centered below clock
            if date_str:
                date_bbox = font_date.getbbox(date_str)
                date_w = date_bbox[2] - date_bbox[0]
                date_x = max(0, (self.width - date_w) // 2)
                draw.text((date_x, date_y), date_str, font=font_date, fill=180)
            
            # Small decorative retro line below date
            draw.line([(20, date_y + 18), (self.width - 20, date_y + 18)], fill=60, width=1)
        
        return draw_clock

