"""
KitchenRadio Client - Main client class for MPD interaction
"""

import logging
import mpd
import threading
from typing import Optional, Callable, Dict, Any, List

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class KitchenRadioClient:
    """
    Thread-safe MPD client with KitchenRadio-specific functionality.
    
    This client uses threading locks to ensure safe concurrent access from multiple threads:
    - Command lock: Protects all MPD command operations
    - Connection lock: Protects connection state management
    - Separate client_status for idle operations to avoid blocking regular commands
    
    All public methods are thread-safe and can be called from multiple threads simultaneously.
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
        
        # Event callbacks for command events (notifying monitor of expected changes)
        self.callbacks = {}
        
        # Thread safety locks
        self._command_lock = threading.RLock()  # Reentrant lock for nested calls
        self._connection_lock = threading.RLock()
        
        # Create MPD client (single connection for polling)
        self.client = mpd.MPDClient()
        self.client.timeout = timeout
        
        logger.info(f"KitchenRadio MPD client initialized for {host}:{port}")
    
    def connect(self) -> bool:
        """
        Connect to MPD server (thread-safe).
        
        Returns:
            True if connected successfully
        """
        with self._connection_lock:
            try:
                logger.info(f"Connecting to MPD at {self.host}:{self.port}")
                self.client.connect(self.host, self.port)
                
                if self.password:
                    self.client.password(self.password)
                
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
        """Disconnect from MPD server (thread-safe)."""
        with self._connection_lock:
            if not self._connected:
                logger.debug("Already disconnected from MPD")
                return
                
            try:
                logger.info("Disconnecting from MPD")
                self._connected = False  # Set this FIRST to prevent reconnect attempts
                
                # Close the client connection
                try:
                    self.client.close()
                except Exception as e:
                    logger.debug(f"Error closing MPD client: {e}")
                
                # Disconnect the client
                try:
                    self.client.disconnect()
                except Exception as e:
                    logger.debug(f"Error disconnecting MPD client: {e}")
                    
                logger.info("Disconnected from MPD successfully")
                
            except Exception as e:
                logger.error(f"Error during MPD disconnect: {e}")
                self._connected = False
    
    def add_callback(self, event: str, callback: Callable):
        """
        Add callback for command events.
        
        Args:
            event: Event name ('command_sent', 'volume_command', 'playback_command', etc.)
            callback: Callback function
        """
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
        logger.debug(f"Added client callback for {event}")
    
    def _trigger_callbacks(self, event: str, **kwargs):
        """Trigger callbacks for event."""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(**kwargs)
                except Exception as e:
                    logger.error(f"Error in client callback for {event}: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to MPD server (thread-safe)."""
        with self._connection_lock:
            return self._connected
    
    # Playback control methods
    def play(self, songpos: Optional[int] = None) -> bool:
        """Start playback from current or specified position (thread-safe)."""
        with self._command_lock:
            try:
                # Emit event BEFORE sending command so monitor knows expected state
                self._trigger_callbacks('playback_command', command='play', expected_state='play', songpos=songpos)
                
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
        """Pause or unpause playback (thread-safe)."""
        with self._command_lock:
            try:
                # Emit event BEFORE sending command
                expected_state = 'pause' if (state is None or state) else 'play'
                self._trigger_callbacks('playback_command', command='pause', expected_state=expected_state, pause_state=state)
                
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
        """Stop playback (thread-safe)."""
        with self._command_lock:
            try:
                # Emit event BEFORE sending command
                self._trigger_callbacks('playback_command', command='stop', expected_state='stop')
                
                self.client.stop()
                return True
            except Exception as e:
                logger.error(f"Error stopping: {e}")
                self.check_connection_error(e)
                return False
    
    def next(self) -> bool:
        """Skip to next track (thread-safe)."""
        with self._command_lock:
            try:
                self.client.next()
                return True
            except Exception as e:
                logger.error(f"Error skipping to next: {e}")
                self.check_connection_error(e)
                return False
    
    def previous(self) -> bool:
        """Skip to previous track (thread-safe)."""
        with self._command_lock:
            try:
                self.client.previous()
                return True
            except Exception as e:
                logger.error(f"Error skipping to previous: {e}")
                self.check_connection_error(e)
                return False
    
    # Volume control
    def set_volume(self, volume: int) -> bool:
        """Set volume (0-100) (thread-safe)."""
        with self._command_lock:
            try:
                if not 0 <= volume <= 100:
                    raise ValueError("Volume must be between 0 and 100")
                
                # Emit event BEFORE sending command so monitor knows expected volume
                self._trigger_callbacks('volume_command', command='set_volume', expected_volume=volume)
                
                self.client.setvol(volume)
                return True
            except Exception as e:
                logger.error(f"Error setting volume: {e}")
                self.check_connection_error(e)
                return False
    
    def get_volume(self) -> Optional[int]:
        """Get current volume (thread-safe)."""
        with self._command_lock:
            try:
                status = self.client.status()
                return int(status.get('volume', 0))
            except Exception as e:
                logger.error(f"Error getting volume: {e}")
                self.check_connection_error(e)
                return None
    
    # Status and info
    def get_status(self) -> Dict[str, Any]:
        """Get player status (thread-safe)."""
        with self._command_lock:
            try:
                status = dict(self.client.status())
                logger.debug(f"[MDP] Got status: {status}")
                return status
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                self.check_connection_error(e)
                return {}
        
    
    def check_connection_error(self, error: Exception):
        """Check if error indicates a lost connection and update state (thread-safe)."""
        with self._connection_lock:
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
    
    def get_current_song(self) -> Optional[Dict[str, Any]]:
        """Get current song info (thread-safe)."""
        with self._command_lock:
            try:
                return dict(self.client.currentsong())
            except Exception as e:
                import traceback
                logger.error(f"Error getting current song: {e}")
                logger.error(f"Call stack:\n{''.join(traceback.format_stack())}")
                self.check_connection_error(e)
                return None
    
    # Playlist management
    def clear_playlist(self) -> bool:
        """Clear the current playlist (thread-safe)."""
        with self._command_lock:
            try:
                self.client.clear()
                # Trigger callback to notify monitor that playlist was cleared
                self._trigger_callbacks('playlist_command', command='clear', playlist_name='')
                logger.info("🎵 Playlist cleared, notifying monitor")
                return True
            except Exception as e:
                logger.error(f"Error clearing playlist: {e}")
                self.check_connection_error(e)
                return False
    
    def load_playlist(self, playlist: str) -> bool:
        """Load the playlist (thread-safe)."""
        with self._command_lock:
            try:
                self.client.load(playlist)
                # Trigger callback to notify monitor of the loaded playlist
                self._trigger_callbacks('playlist_command', command='load', playlist_name=playlist)
                logger.info(f"🎵 Playlist '{playlist}' loaded, notifying monitor")
                return True
            except Exception as e:
                logger.error(f"Error loading playlist: {e}")
                self.check_connection_error(e)
                return False

    def add_to_playlist(self, uri: str) -> bool:
        """Add URI to playlist (thread-safe)."""
        with self._command_lock:
            try:
                self.client.add(uri)
                #for streaming show the uri instead of the playlist name
                playlist = uri
                self._trigger_callbacks('playlist_command', command='load', playlist_name=playlist)
                return True
            except Exception as e:
                logger.error(f"Error adding to playlist: {e}")
                self.check_connection_error(e)
                return False
    
    def get_playlist(self) -> List[Dict[str, Any]]:
        """Get current playlist (thread-safe)."""
        with self._command_lock:
            try:
                return [dict(song) for song in self.client.playlistinfo()]
            except Exception as e:
                logger.error(f"Error getting playlist: {e}")
                self.check_connection_error(e)
                return []
    
    def get_all_playlists(self) -> List[Dict[str, Any]]:
        """
        Get all stored playlists with metadata (thread-safe).
        
        Returns:
            List of playlist dicts with 'playlist' and 'last-modified' keys
            Note: Controller layer strips metadata and returns just names
        """
        with self._command_lock:
            try:
                return [dict(playlist) for playlist in self.client.listplaylists()]
            except Exception as e:
                logger.error(f"Error getting playlists: {e}")
                self.check_connection_error(e)
                return []
