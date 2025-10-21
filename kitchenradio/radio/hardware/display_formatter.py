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
        font_sizes = {'small': FONT_SMALL, 'medium': FONT_MEDIUM, 'large': FONT_LARGE, 'xlarge': FONT_XLARGE}
        
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
            
            # Large volume bar on the left side (covers full height)
            bar_width = 16
            bar_height = self.height - 10  # Full height with small margin
            bar_x = 10
            bar_y = 5
            
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
    
    # def format_track_info(self, track, artist: str = "", album: str = "", 
    #                       playing: bool = False, volume: int = 50) -> Callable:
    #     """
    #     Format track information display.
        
    #     Args:
    #         title: Track title
    #         artist: Artist name
    #         album: Album name
    #         playing: Whether track is currently playing
    #         volume: Current volume level
            
    #     Returns:
    #         Drawing function for track info
    #     """
    #     def draw_track_info(draw: ImageDraw.Draw):
    #         # Clear background
    #         draw.rectangle([(0, 0), (self.width, self.height)], fill=0)
            
    #         # Volume bar on the left side (vertical bar)
    #         bar_width = 8
    #         bar_height = self.height - 10  # Leave some margin top/bottom
    #         bar_x = 5
    #         bar_y = 5
            
    #         # Draw volume bar background (empty bar)
    #         draw.rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)], outline=255)
            
    #         # Draw volume bar fill (filled portion based on volume)

    #         if volume and  volume > 0:
    #             fill_height = int((volume / 100.0) * bar_height)
    #             fill_y = bar_y + bar_height - fill_height  # Fill from bottom up
    #             draw.rectangle([(bar_x + 1, fill_y), (bar_x + bar_width - 1, bar_y + bar_height - 1)], fill=255)
            
    #         # Content area starts after the volume bar
    #         content_x = bar_x + bar_width + 10
    #         content_width = self.width - content_x - 5
            
    #         # Title (main line) - larger font and truncate to fit in available space
    #         if track:
    #             title_text = track.get('title', 'No Track')
    #             title_max_width = content_width - 10
    #             title_truncated = self._truncate_text(title_text, title_max_width, self.fonts['xlarge'])
    #             draw.text((content_x, 5), title_truncated, font=self.fonts['xlarge'], fill=255)
            
    #             album_text =  track.get('album', 'Unknown')
    #             artist_text =  track.get('artist', 'Unknown')
    #             if not artist_text=='Unknown' and not album_text=='Unknown':
    #                 artist_album_text = f"{artist_text} : {album_text}"
    #             elif not album_text=='Unknown':
    #                 artist_album_text = album_text
    #             else:
    #                 artist_album_text = artist_text
                

    #             artist_album_truncated = self._truncate_text(artist_album_text, content_width, self.fonts['small'])
    #             draw.text((content_x, 28), artist_album_truncated, font=self.fonts['small'], fill=255)
            
    #         # Large play/pause/stop icon in bottom right corner
    #         play_icon = "▶" if playing else "⏸"
    #         icon_font = self.fonts['xlarge']  # Use extra large font for the icon
            
    #         # Calculate position for bottom right alignment
    #         # Get approximate icon size (this is rough estimation)
    #         icon_width = 20  # Approximate width of large icon
    #         icon_height = 24  # Approximate height of large icon
    #         icon_x = self.width - icon_width - 5  # 5px margin from right edge
    #         icon_y = self.height - icon_height - 5  # 5px margin from bottom edge
            
    #         draw.text((icon_x, icon_y), play_icon, font=icon_font, fill=255)
        
    #     return draw_track_info
    
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
        
        return draw_status_message
    
    def format_fullscreen_volume(self, volume: int, max_volume: int = 100) -> Callable:
        """
        Format full screen volume display with large bar spanning entire display.
        
        Args:
            volume: Current volume level
            max_volume: Maximum volume level
            
        Returns:
            Drawing function for full screen volume display
        """
        def draw_fullscreen_volume(draw):
            # Clear background
            draw.rectangle([(0, 0), (self.width, self.height)], fill=0)
            
            # Full screen volume bar
            bar_margin = 8
            bar_width = self.width - (2 * bar_margin)
            bar_height = self.height - 30  # Leave space for text at top
            bar_x = bar_margin
            bar_y = 25
            
            # Draw "VOLUME" text at top center
            volume_text = "VOLUME"
            text_width = len(volume_text) * 12  # Estimate width
            text_x = (self.width - text_width) // 2
            draw.text((text_x, 5), volume_text, font=self.fonts['large'], fill=255)
            
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
            

            # Draw volume scale marks along the bottom
            num_marks = 11  # 0%, 10%, 20%, ... 100%
            mark_spacing = bar_width / (num_marks - 1)
            
            for i in range(num_marks):
                mark_x = bar_x + int(i * mark_spacing)
                mark_y = bar_y + bar_height + 2
                
                # Draw tick mark
                draw.line([(mark_x, mark_y), (mark_x, mark_y + 4)], fill=255, width=1)
                
                # Draw percentage labels at 0%, 50%, 100%
                if i in [0, 5, 10]:
                    label = f"{i * 10}"
                    label_width = len(label) * 6
                    label_x = mark_x - (label_width // 2)
                    draw.text((label_x, mark_y + 6), label, font=self.fonts['small'], fill=255)
            
 
        
        return draw_fullscreen_volume
    
    def format_track_info(self, track, playing: bool = False, volume: int = 50) -> Callable:
        """
        Format track information display with optional progress bar at bottom.
        
        Args:
            title: Track title
            artist: Artist name
            album: Album name
            playing: Whether track is currently playing
            volume: Current volume level
            progress_ms: Current progress in milliseconds
            duration_ms: Total track duration in milliseconds
            showProgress: Whether to show the progress bar (default True)
            
        Returns:
            Drawing function for track info with optional progress bar
        """
        def draw_track_info_with_progress(draw: ImageDraw.Draw):
            # Clear background
            draw.rectangle([(0, 0), (self.width, self.height)], fill=0)
            
            # Volume bar on the left side (vertical bar - full height)
            bar_width = 8
            bar_height = self.height - 10  # Full height with small margin
            bar_x = 5
            bar_y = 5
            
            # Draw volume bar background (empty bar)
            draw.rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)], outline=255)
            
            # Draw volume bar fill (filled portion based on volume)
            volume_number = int(volume)
            if volume_number and  volume_number > 0:
                fill_height = int((volume_number / 100.0) * bar_height)
                fill_y = bar_y + bar_height - fill_height  # Fill from bottom up
                draw.rectangle([(bar_x + 1, fill_y), (bar_x + bar_width - 1, bar_y + bar_height - 1)], fill=255)
            
            # Content area starts after the volume bar
            content_x = bar_x + bar_width + 10
            content_width = self.width - content_x - 5
            

            # Title (main line) - larger font and truncate to fit in available space
            if track:
                title_text = track.get('title', 'No Track')
                title_max_width = content_width - 10
                title_truncated = self._truncate_text(title_text, title_max_width, self.fonts['xlarge'])
                draw.text((content_x, 5), title_truncated, font=self.fonts['xlarge'], fill=255)
            
                album_text =  track.get('album', 'Unknown')
                artist_text =  track.get('artist', 'Unknown')
                if not artist_text=='Unknown' and not album_text=='Unknown':
                    artist_album_text = f"{artist_text} : {album_text}"
                elif not album_text=='Unknown':
                    artist_album_text = album_text
                else:
                    artist_album_text = artist_text
                
                artist_album_truncated = self._truncate_text(artist_album_text, content_width, self.fonts['small'])
                draw.text((content_x, 28), artist_album_truncated, font=self.fonts['small'], fill=255)
            
            # # Progress bar at the bottom - only if showProgress is True
            # if showProgress:
            #     progress_bar_height = 4
            #     # Align progress bar bottom with volume bar bottom, but one pixel lower
            #     volume_bar_bottom = bar_y + bar_height - 1
            #     progress_bar_y = volume_bar_bottom - progress_bar_height + 1  # One pixel lower
            #     progress_bar_x = bar_x + bar_width + 5  # Start after volume bar with gap
            #     progress_bar_width = self.width - progress_bar_x - 25  # Leave space for icon
                
            #     # Debug logging
            #     logger.debug(f"Progress bar: showProgress={showProgress}, progress_ms={progress_ms}, duration_ms={duration_ms}")
            #     logger.debug(f"Progress bar position: x={progress_bar_x}, y={progress_bar_y}, width={progress_bar_width}, height={progress_bar_height}")
                
            #     # Draw progress bar background
            #     draw.rectangle([
            #         (progress_bar_x, progress_bar_y), 
            #         (progress_bar_x + progress_bar_width, progress_bar_y + progress_bar_height)
            #     ], outline=255)
                
            #     # Draw progress bar fill
            #     if duration_ms > 0 and progress_ms >= 0:
            #         progress_ratio = min(progress_ms / duration_ms, 1.0)
            #         fill_width = int(progress_ratio * (progress_bar_width - 2))
            #         logger.debug(f"Progress fill: ratio={progress_ratio:.2f}, fill_width={fill_width}")
            #         if fill_width > 0:
            #             draw.rectangle([
            #                 (progress_bar_x + 1, progress_bar_y + 1),
            #                 (progress_bar_x + 1 + fill_width, progress_bar_y + progress_bar_height - 1)
            #             ], fill=255)
            #     else:
            #         logger.debug(f"No progress fill: duration_ms={duration_ms}, progress_ms={progress_ms}")
            # else:
            #     logger.debug(f"Progress bar disabled: showProgress={showProgress}")
            
            # Playing icon in bottom right corner
            icon_size = 12
            icon_x = self.width - icon_size - 5
            icon_y = self.height - icon_size - 2
            play_icon = "▶" if playing else "⏸"
            draw.text((icon_x, icon_y), play_icon, font=self.fonts['large'], fill=255)
        
        return draw_track_info_with_progress
    
    def format_menu_display(self, title: str, menu_items: list, selected_index: int = 0) -> Callable:
        """
        Format scrollable menu display with current selection centered.
        
        Args:
            title: Menu title
            menu_items: List of menu items
            selected_index: Index of currently selected item
            
        Returns:
            Drawing function for scrollable menu display
        """
        def draw_menu(draw: ImageDraw.Draw):
            # Clear background
            draw.rectangle([(0, 0), (self.width, self.height)], fill=0)
            
            # Menu area dimensions (use full display height)
            menu_start_y = 0  # Start at top of display
            menu_end_y = self.height  # End at bottom of display
            menu_height = menu_end_y - menu_start_y
            line_height = 20  # Further increased line height for more spacing between items
            max_visible_items = menu_height // line_height
            
            # Reserve space for scroll bar on the right
            scroll_bar_width = 12
            scroll_bar_margin = 8
            content_right_edge = self.width - scroll_bar_width - scroll_bar_margin - 10  # Extra margin
            
            if not menu_items:
                # No items to display
                draw.text((15, menu_start_y + 10), "No items", font=self.fonts['small'], fill=128)
                return
            
            # Calculate menu layout with fixed center selection
            total_items = len(menu_items)
            half_visible = max_visible_items // 2
            
            # Fixed selection bar position (center of menu area)
            center_y = menu_start_y + (menu_height // 2) - (line_height // 2)
            
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
                        item_truncated = self._truncate_text(item, max_item_width, self.fonts['small'])
                        
                        if i == selected_index:
                            # Selected item (drawn on white background) - 5 pixels higher
                            draw.text((35, y_pos + 6 ), item_truncated, font=self.fonts['small'], fill=0)
                        else:
                            # Regular item - 5 pixels higher
                            draw.text((35, y_pos + 6), item_truncated, font=self.fonts['small'], fill=255)
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
                        item_truncated = self._truncate_text(item, max_item_width, self.fonts['small'])
                        
                        if item_idx == selected_index:
                            # Selected item (drawn on white background) - 5 pixels higher
                            draw.text((15, y_pos + 6), item_truncated, font=self.fonts['small'], fill=0)
                        else:
                            # Regular item - 5 pixels higher
                            draw.text((15, y_pos + 6), item_truncated, font=self.fonts['small'], fill=255)
            
            # Draw scroll position indicator bar (volume bar style)
            if total_items > 1:
                # Position bar on the right side (using defined dimensions)
                bar_width = scroll_bar_width
                bar_height = menu_height - 16  # Small margin for outline thickness
                bar_x = self.width - bar_width - scroll_bar_margin
                bar_y = menu_start_y + 4  # Small top margin
                
                # Draw scroll bar background (outline)
                draw.rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)], outline=255, width=2)
                
                # Calculate position for current item only (no cumulative fill)
                item_height = (bar_height - 4) / total_items if total_items > 0 else 0
                current_item_y = bar_y + 2 + int(selected_index * item_height)
                
                # Draw filled area only for the current selected item
                if item_height > 0:
                    draw.rectangle([
                        (bar_x + 2, current_item_y), 
                        (bar_x + bar_width - 2, current_item_y + int(item_height))
                    ], fill=255)
                
                # Optional: Add small tick marks to show discrete positions
                if total_items <= 8:  # Reduced threshold for cleaner look
                    tick_spacing = (bar_height - 4) / (total_items - 1) if total_items > 1 else 0
                    for i in range(total_items):
                        tick_y = bar_y + 2 + int(i * tick_spacing)
                        tick_x = bar_x + bar_width + 2
                        if i == selected_index:
                            # Highlight current position tick
                            draw.rectangle([(tick_x, tick_y - 0), (tick_x + 4, tick_y + 1)], fill=255)
                        else:
                            # Regular position tick
                            draw.rectangle([(tick_x, tick_y), (tick_x + 2, tick_y)], fill=128)
            
            # # Show item count at bottom right (overlay on display)
            # count_text = f"{selected_index + 1}/{total_items}"
            # count_width = len(count_text) * 5  # Approximate width
            # count_x = self.width - count_width - 5
            # count_y = self.height - 12  # Position at bottom edge
            # draw.text((count_x, count_y), count_text, font=self.fonts['small'], fill=128)
        
        return draw_menu
