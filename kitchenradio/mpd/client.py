"""
KitchenRadio Client - Main client class for MPD interaction
"""

import logging
import mpd
from typing import Optional, Callable, Dict, Any, List

logger = logging.getLogger(__name__)


class KitchenRadioClient:
    """
    MPD client with KitchenRadio-specific functionality.
    """
    
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 6600,  # MPD default port
                 password: Optional[str] = None,
                 timeout: int = 10):
        """
        Initialize KitchenRadio MPD client.
        
        Args:
            host: MPD server hostname
            port: MPD server port (default 6600)
            password: MPD password if required
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self._connected = False
        
        # Create MPD client
        self.client = mpd.MPDClient()
        self.client.timeout = timeout
        self.client.idletimeout = None

        # Create MPD client_status
        self.client_status = mpd.MPDClient()
        self.client_status.timeout = timeout
        self.client_status.idletimeout = None
        
        logger.info(f"KitchenRadio MPD client initialized for {host}:{port}")
    
    def connect(self) -> bool:
        """
        Connect to MPD server.
        
        Returns:
            True if connected successfully
        """
        try:
            logger.info(f"Connecting to MPD at {self.host}:{self.port}")
            self.client.connect(self.host, self.port)
            
            if self.password:
                self.client.password(self.password)


            self.client_status.connect(self.host, self.port)
            
            if self.password:
                self.client_status.password(self.password)
            
            self._connected = True
            logger.info("Connected to MPD successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MPD: {e}")
            if(e.args and isinstance(e.args[0], str) and "Already connected" in e.args[0]):
                logger.error("Already Connected to MPD")
                return True
            self._connected = False
            return False
    
    def disconnect(self):
        """Disconnect from MPD server."""
        try:
            if self._connected:
                logger.info("Disconnecting from MPD")
                self.client.close()
                self.client.disconnect()
                self._connected = False
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            self._connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to MPD server."""
        return self._connected
    
    # Playback control methods
    def play(self, songpos: Optional[int] = None) -> bool:
        """Start playback from current or specified position."""
        try:
            if songpos is not None:
                self.client.play(songpos)
            else:
                self.client.play()
            return True
        except Exception as e:
            logger.error(f"Error starting playback: {e}")
            self.check_connection_error(e)
            return False
    
    def pause(self, state: Optional[bool] = None) -> bool:
        """Pause or unpause playback."""
        try:
            if state is None:
                self.client.pause()
            else:
                self.client.pause(1 if state else 0)
            return True
        except Exception as e:
            logger.error(f"Error pausing: {e}")
            self.check_connection_error(e)
            return False
    
    def stop(self) -> bool:
        """Stop playback."""
        try:
            self.client.stop()
            return True
        except Exception as e:
            logger.error(f"Error stopping: {e}")
            self.check_connection_error(e)
            return False
    
    def next(self) -> bool:
        """Skip to next track."""
        try:
            self.client.next()
            return True
        except Exception as e:
            logger.error(f"Error skipping to next: {e}")
            self.check_connection_error(e)
            return False
    
    def previous(self) -> bool:
        """Skip to previous track."""
        try:
            self.client.previous()
            return True
        except Exception as e:
            logger.error(f"Error skipping to previous: {e}")
            self.check_connection_error(e)
            return False
    
    # Volume control
    def set_volume(self, volume: int) -> bool:
        """Set volume (0-100)."""
        try:
            if not 0 <= volume <= 100:
                raise ValueError("Volume must be between 0 and 100")
            self.client.setvol(volume)
            return True
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            self.check_connection_error(e)
            return False
    
    def get_volume(self) -> Optional[int]:
        """Get current volume."""
        try:
            status = self.client.status()
            return int(status.get('volume', 0))
        except Exception as e:
            logger.error(f"Error getting volume: {e}")
            self.check_connection_error(e)
            return None
    
    # Status and info
    def get_status(self) -> Dict[str, Any]:
        """Get player status."""
        try:
            return dict(self.client.status())
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            self.check_connection_error(e)
            return {}
        
    
    def check_connection_error(self, error: Exception):
        """Check if error indicates a lost connection and update state."""
        if isinstance(error, (mpd.ConnectionError, mpd.CommandError)):
            logger.warning("MPD connection lost")
        try:
            self.client.disconnect()
        except:
            logger.warning("Already Disconnected")

        try:
            self.client_status.disconnect()
        except:
            logger.warning("Already Disconnected")
   
        self._connected = False
    
    def wait_for_changes(self) -> Dict[str, Any]:
        """Get player status."""
        try:

            return self.client_status.idle()
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            self.check_connection_error(e)
            return {}
        
    def get_current_song(self) -> Optional[Dict[str, Any]]:
        """Get current song info."""
        try:
            return dict(self.client.currentsong())
        except Exception as e:
            logger.error(f"Error getting current song: {e}")
            self.check_connection_error(e)
            return None
    
    # Playlist management
    def clear_playlist(self) -> bool:
        """Clear the current playlist."""
        try:
            self.client.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing playlist: {e}")
            self.check_connection_error(e)
            return False
    
    def add_to_playlist(self, uri: str) -> bool:
        """Add URI to playlist."""
        try:
            self.client.add(uri)
            return True
        except Exception as e:
            logger.error(f"Error adding to playlist: {e}")
            self.check_connection_error(e)
            return False
    
    def get_playlist(self) -> List[Dict[str, Any]]:
        """Get current playlist."""
        try:
            return [dict(song) for song in self.client.playlistinfo()]
        except Exception as e:
            logger.error(f"Error getting playlist: {e}")
            self.check_connection_error(e)
            return []
