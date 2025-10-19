"""
Playback Controller - Control MPD playback
"""

import logging
from typing import Optional, List, Dict, Any
from .client import KitchenRadioClient

logger = logging.getLogger(__name__)


class PlaybackController:
    """
    Control MPD playback operations.
    """
    
    def __init__(self, client: KitchenRadioClient):
        """
        Initialize controller with KitchenRadio client.
        
        Args:
            client: KitchenRadio client instance
        """
        self.client = client
    
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
    
    def stop(self) -> bool:
        """
        Stop playback.
        
        Returns:
            True if successful
        """
        return self.client.stop()
    
    def next_track(self) -> bool:
        """
        Skip to next track.
        
        Returns:
            True if successful
        """
        return self.client.next()
    
    def previous_track(self) -> bool:
        """
        Skip to previous track.
        
        Returns:
            True if successful
        """
        return self.client.previous()
    
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
    
    def get_state(self) -> Optional[str]:
        """
        Get current playback state.
        
        Returns:
            State string ('play', 'pause', 'stop') or None
        """
        try:
            status = self.client.get_status()
            return status.get('state')
        except Exception as e:
            logger.error(f"Error getting state: {e}")
            return None
    
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
    
    def get_all_playlists(self) -> List[Dict[str, Any]]:
        """
        Get all stored playlists.
        
        Returns:
            List of playlist dicts with name and metadata
        """
        return self.client.get_all_playlists()
    
    def get_current_song(self) -> Optional[Dict[str, Any]]:
        """
        Get current song info.
        
        Returns:
            Song info dict or None
        """
        return self.client.get_current_song()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get player status.
        
        Returns:
            Status dict
        """
        return self.client.get_status()
