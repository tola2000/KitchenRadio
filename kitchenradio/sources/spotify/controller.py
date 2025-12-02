"""
LibreSpot Controller - Control go-librespot playback
"""

import logging
from typing import Optional, Dict, Any, List
from .client import KitchenRadioLibrespotClient
from .monitor import LibrespotMonitor

logger = logging.getLogger(__name__)


class LibrespotController:
    """
    Control go-librespot playback operations.
    """
    
    def __init__(self, host: str = "localhost", port: int = 24879, timeout: int = 10):
        """
        Initialize controller with Librespot connection details.
        
        Args:
            host: Librespot host
            port: Librespot port
            timeout: Connection timeout
        """
        self.client = KitchenRadioLibrespotClient(host, port, timeout)
        self.monitor = LibrespotMonitor(self.client)

    def connect(self) -> bool:
        """Connect to Librespot"""
        return self.client.connect()
    
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
    
    def stop(self) -> bool:
        """
        Pause playback.
        
        Returns:
            True if successful
        """
        return self.client.stop()
        
    def playpause(self) -> bool:
        """
        Toggle between play and pause.
        
        Returns:
            True if successful
        """
        return self.client.playpause()

    
    def next(self) -> bool:
        """
        Skip to next track.
        
        Returns:
            True if successful
        """
        return self.client.next_track()
    
    def previous(self) -> bool:
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
    
    def volume_up(self, step: int = 5) -> Optional[int]:
        """
        Increase volume by step.
        
        Args:
            step: Volume increase step (default 5)
            
        Returns:
            New volume level (0-100) if successful, None if error
        """
        try:
            current_volume = self.get_volume()
            if current_volume is not None:
                new_volume = min(100, current_volume + step)
                if self.set_volume(new_volume):
                    return new_volume
            return None
        except Exception as e:
            logger.error(f"Error increasing volume: {e}")
            return None
    
    def volume_down(self, step: int = 5) -> Optional[int]:
        """
        Decrease volume by step.
        
        Args:
            step: Volume decrease step (default 5)
            
        Returns:
            New volume level (0-100) if successful, None if error
        """
        try:
            current_volume = self.get_volume()
            if current_volume is not None:
                new_volume = max(0, current_volume - step)
                if self.set_volume(new_volume):
                    return new_volume
            return None
        except Exception as e:
            logger.error(f"Error decreasing volume: {e}")
            return None
    
    def set_shuffle(self, enabled: bool) -> bool:
        """
        Set shuffle mode.
        
        Args:
            enabled: True to enable shuffle, False to disable
            
        Returns:
            True if successful
        """
        return self.client.set_shuffle(enabled)
    
    def get_shuffle(self) -> Optional[bool]:
        """
        Get current shuffle state.
        
        Returns:
            True if shuffle is enabled, False if disabled, None if error
        """
        return self.client.get_shuffle()
    
    def set_repeat(self, mode: str) -> bool:
        """
        Set repeat mode.
        
        Args:
            mode: Repeat mode ('off', 'track', 'context')
            
        Returns:
            True if successful
        """
        return self.client.set_repeat(mode)
    
    def stop(self) -> bool:

        return self.client.stop()
    
    def get_repeat(self) -> Optional[str]:
        """
        Get current repeat mode.
        
        Returns:
            Current repeat mode or None if error
        """
        return self.client.get_repeat()
    
    def toggle_shuffle(self) -> bool:
        """
        Toggle shuffle mode.
        
        Returns:
            True if successful
        """
        current_shuffle = self.get_shuffle()
        if current_shuffle is not None:
            return self.set_shuffle(not current_shuffle)
        return False
    
    def toggle_repeat(self) -> bool:
        """
        Toggle repeat mode (off -> track -> context -> off).
        
        Returns:
            True if successful
        """
        current_repeat = self.get_repeat()
        if current_repeat is not None:
            next_mode = {
                'off': 'track',
                'track': 'context', 
                'context': 'off'
            }.get(current_repeat, 'off')
            return self.set_repeat(next_mode)
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
    
    # Playlist methods (dummy implementations for Spotify)
    def get_all_playlists(self) -> List[str]:
        """
        Get all stored playlist names.
        Note: Spotify playlists are managed through the Spotify app.
        
        Returns:
            Empty list (Spotify doesn't support local playlists)
        """
        logger.info("Spotify playlists are managed through the Spotify app")
        return []
    
    def play_playlist(self, playlist: str) -> bool:
        """
        Load and play a playlist.
        Note: Spotify playlists are managed through the Spotify app.
        
        Args:
            playlist: Playlist name (ignored for Spotify)
            
        Returns:
            False (Spotify doesn't support loading local playlists)
        """
        logger.warning(f"Cannot load playlist '{playlist}' - Spotify playlists are managed through the Spotify app")
        return False

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
