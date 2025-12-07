"""
Playback Controller - Control MPD playback
"""

import logging
from typing import Optional, List, Dict, Any
from .client import KitchenRadioClient
from .monitor import MPDMonitor

logger = logging.getLogger(__name__)


class PlaybackController:
    """
    Control MPD playback operations.
    """
    
    def __init__(self, host: str = "localhost", port: int = 6600, password: Optional[str] = None, timeout: int = 10):
        """
        Initialize controller with MPD connection details.
        
        Args:
            host: MPD host
            port: MPD port
            password: MPD password
            timeout: Connection timeout
        """
        self.client = KitchenRadioClient(host, port, password, timeout)
        self.monitor = MPDMonitor(self.client)

    def connect(self) -> bool:
        """Connect to MPD server"""
        return self.client.connect()
    
    def play(self, uri: Optional[str] = None) -> bool:
        """
        Start playback.
        
        Args:
            uri: URI to play (if None, resume current)
            
        Returns:
            True if successful
        """
        if uri:
            # Clear playlist and add new URI
            if not self.client.clear_playlist():
                return False
            if not self.client.add_to_playlist(uri):
                return False
        
        return self.client.play()

    def play_playlist(self, playlist: Optional[str] = None) -> bool:
        """
        Start playback.
        
        Args:
            uri: URI to play (if None, resume current)
            
        Returns:
            True if successful
        """
        if playlist:
            # Clear playlist and add new URI
            if not self.client.clear_playlist():
                return False
            if not self.client.load_playlist(playlist):
                return False
        
        return self.client.play()
    
    def pause(self) -> bool:
        """
        Pause playback.
        
        Returns:
            True if successful
        """
        return self.client.pause(True)
    
    def resume(self) -> bool:
        """
        Resume playback.
        
        Returns:
            True if successful
        """
        return self.client.pause(False)
    
    def playpause(self) -> bool:
        """
        Toggle between play and pause.
        
        Returns:
            True if successful
        """
        try:
            # Get current status to determine current state
            status = self.client.get_status()
            if not status:
                return False
            
            current_state = status.get('state', 'stop')
            
            if current_state == 'play':
                return self.pause()
            else:
                return self.client.play()
                
        except Exception as e:
            logger.error(f"Error in playpause: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Stop playback.
        
        Returns:
            True if successful
        """
        return self.client.stop()
    
    def next(self) -> bool:
        """
        Skip to next track.
        
        Returns:
            True if successful
        """
        return False
       # return self.client.next()
    
    def previous(self) -> bool:
        """
        Skip to previous track.
        
        Returns:
            True if successful
        """
        return False
      #  return self.client.previous()
    

    
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
    
    # def get_state(self) -> Optional[str]:
    #     """
    #     Get current playback state.
        
    #     Returns:
    #         State string ('play', 'pause', 'stop') or None
    #     """
    #     try:
    #         status = self.client.get_status()
    #         return status.get('state')
    #     except Exception as e:
    #         logger.error(f"Error getting state: {e}")
    #         return None
    
    def add_to_playlist(self, uri: str) -> bool:
        """
        Add URI to playlist.
        
        Args:
            uri: URI to add
            
        Returns:
            True if successful
        """
        return self.client.add_to_playlist(uri)
    
    def clear_playlist(self) -> bool:
        """
        Clear the playlist.
        
        Returns:
            True if successful
        """
        return self.client.clear_playlist()
    
    def get_playlist(self) -> List[Dict[str, Any]]:
        """
        Get current playlist.
        
        Returns:
            List of song dicts
        """
        return self.client.get_playlist()
    
    def get_playlists(self) -> List[str]:
        """
        Get all stored playlist names.
        
        Returns:
            List of playlist names (strings)
        """
        playlists_data = self.client.get_all_playlists()
        # Extract just the playlist names from the metadata and sort alphabetically
        names = [playlist.get('playlist', '') for playlist in playlists_data if 'playlist' in playlist]
        return sorted(names)
    

    # def get_current_song(self) -> Optional[Dict[str, Any]]:
    #     """
    #     Get current song info.
        
    #     Returns:
    #         Song info dict or None
    #     """
    #     return self.client.get_current_song()
    
    # def get_status(self) -> Dict[str, Any]:
    #     """
    #     Get player status.
        
    #     Returns:
    #         Status dict
    #     """
    #     return self.client.get_status()
