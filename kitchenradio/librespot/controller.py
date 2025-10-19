"""
LibreSpot Controller - Control go-librespot playback
"""

import logging
from typing import Optional, Dict, Any
from .client import KitchenRadioLibrespotClient

logger = logging.getLogger(__name__)


class LibrespotController:
    """
    Control go-librespot playback operations.
    """
    
    def __init__(self, client: KitchenRadioLibrespotClient):
        """
        Initialize controller with KitchenRadio librespot client.
        
        Args:
            client: KitchenRadio librespot client instance
        """
        self.client = client
    
    def play(self) -> bool:
        """
        Start/resume playback.
        
        Returns:
            True if successful
        """
        return self.client.play()
    
    def pause(self) -> bool:
        """
        Pause playback.
        
        Returns:
            True if successful
        """
        return self.client.pause()
    
    def resume(self) -> bool:
        """
        Pause playback.
        
        Returns:
            True if successful
        """
        return self.client.resume()
    
    def playpause(self) -> bool:
        """
        Toggle between play and pause.
        
        Returns:
            True if successful
        """
        return self.client.playpause()

    
    def next_track(self) -> bool:
        """
        Skip to next track.
        
        Returns:
            True if successful
        """
        return self.client.next_track()
    
    def previous_track(self) -> bool:
        """
        Skip to previous track.
        
        Returns:
            True if successful
        """
        return self.client.previous_track()
    
    def set_volume(self, volume: int) -> bool:
        """
        Set volume level.
        
        Args:
            volume: Volume level (0-100)
            
        Returns:
            True if successful
        """
        return self.client.set_volume(volume)
    
    def get_volume(self) -> Optional[int]:
        """
        Get current volume level.
        
        Returns:
            Volume level (0-100) or None if error
        """
        return self.client.get_volume()
    
    def volume_up(self, step: int = 5) -> bool:
        """
        Increase volume by step.
        
        Args:
            step: Volume increase step (default 5)
            
        Returns:
            True if successful
        """
        try:
            current_volume = self.get_volume()
            if current_volume is not None:
                new_volume = min(100, current_volume + step)
                return self.set_volume(new_volume)
            return False
        except Exception as e:
            logger.error(f"Error increasing volume: {e}")
            return False
    
    def volume_down(self, step: int = 5) -> bool:
        """
        Decrease volume by step.
        
        Args:
            step: Volume decrease step (default 5)
            
        Returns:
            True if successful
        """
        try:
            current_volume = self.get_volume()
            if current_volume is not None:
                new_volume = max(0, current_volume - step)
                return self.set_volume(new_volume)
            return False
        except Exception as e:
            logger.error(f"Error decreasing volume: {e}")
            return False
    
    # def get_status(self) -> Optional[Dict[str, Any]]:
    #     """
    #     Get player status.
        
    #     Returns:
    #         Status dict or None if error
    #     """
    #     return self.client.get_status()
    
    # def get_current_track(self) -> Optional[Dict[str, Any]]:
    #     """
    #     Get current track info.
        
    #     Returns:
    #         Track info dict or None
    #     """
    #     return self.client.get_current_track()
    
    # def is_playing(self) -> bool:
    #     """
    #     Check if currently playing.
        
    #     Returns:
    #         True if playing
    #     """
    #     try:
    #         status = self.get_status()
    #         return status.get('is_playing', False) if status else False
    #     except Exception as e:
    #         logger.error(f"Error checking playback state: {e}")
    #         return False
    
    # def get_playback_state(self) -> str:
    #     """
    #     Get current playback state.
        
    #     Returns:
    #         State string ('play', 'pause', 'stop')
    #     """
    #     try:
    #         status = self.get_status()
    #         if not status:
    #             return 'stop'
            
    #         if status.get('is_playing'):
    #             return 'play'
    #         elif status.get('track'):
    #             return 'pause'
    #         else:
    #             return 'stop'
    #     except Exception as e:
    #         logger.error(f"Error getting playback state: {e}")
    #         return 'stop'
    
    # def get_track_info(self) -> Dict[str, Any]:
    #     """
    #     Get formatted track information.
        
    #     Returns:
    #         Formatted track info dict
    #     """
    #     try:
    #         status = self.get_status()
    #         if not status or not status.get('track'):
    #             return {'name': 'No Track', 'artists': '', 'album': '', 'uri': ''}
            
    #         track = status['track']
    #         return {
    #             'name': track.get('name', 'Unknown Track'),
    #             'artists': ', '.join([artist.get('name', 'Unknown') for artist in track.get('artists', [])]),
    #             'album': track.get('album', {}).get('name', 'Unknown Album'),
    #             'uri': track.get('uri', ''),
    #             'duration_ms': track.get('duration_ms', 0),
    #             'progress_ms': status.get('progress_ms', 0),
    #             'is_playing': status.get('is_playing', False)
    #         }
    #     except Exception as e:
    #         logger.error(f"Error getting track info: {e}")
    #         return {'name': 'Error', 'artists': '', 'album': '', 'uri': ''}
    
    def get_devices(self) -> Optional[Dict[str, Any]]:
        """
        Get available devices.
        
        Returns:
            Devices info dict or None
        """
        return self.client.get_devices()
    
    def print_status(self):
        """Print current status to console."""
        try:
            track_info = self.get_track_info()
            state = self.get_playback_state()
            volume = self.get_volume()
            
            if track_info['name'] != 'No Track':
                progress = track_info.get('progress_ms', 0) // 1000
                duration = track_info.get('duration_ms', 0) // 1000
                progress_str = f" ({progress//60}:{progress%60:02d}/{duration//60}:{duration%60:02d})"
                
                state_icon = "▶️" if state == 'play' else "⏸️" if state == 'pause' else "⏹️"
                
                print(f"🎵 {state_icon} {track_info['artists']} - {track_info['name']}{progress_str}")
                print(f"📀 Album: {track_info['album']}")
                print(f"🔊 Volume: {volume}%")
            else:
                print("🎵 No track currently playing")
                print(f"🔊 Volume: {volume}%")
                
        except Exception as e:
            logger.error(f"Error printing status: {e}")
            print("❌ Error getting status")
