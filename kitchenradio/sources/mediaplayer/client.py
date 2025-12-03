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
        self._idle_lock = threading.Lock()  # Lock to coordinate idle state
        self._in_idle = False  # Track if idle is currently active
        
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
    def _ensure_idle_cancelled(self):
        """Ensure idle is cancelled before sending commands."""
        with self._idle_lock:
            if self._in_idle:
                logger.debug("Cancelling idle before command")
                try:
                    # Send noidle command using raw interface
                    self.client_status._write_command("noidle")
                    # Read the response (changed subsystems or empty list)
                    try:
                        self.client_status._read_list()
                    except AttributeError:
                        # Fallback if _read_list doesn't exist
                        self.client_status._fetch_list()
                    self._in_idle = False
                    logger.debug("Idle cancelled successfully")
                except Exception as e:
                    logger.debug(f"Error cancelling idle: {e}")
                    self._in_idle = False  # Reset flag even on error
    
    def play(self, songpos: Optional[int] = None) -> bool:
        """Start playback from current or specified position (thread-safe)."""
        self._ensure_idle_cancelled()
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
        self._ensure_idle_cancelled()
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
        self._ensure_idle_cancelled()
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
        self._ensure_idle_cancelled()
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
        self._ensure_idle_cancelled()
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
        self._ensure_idle_cancelled()
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
                return dict(self.client.status())
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
    
    def idle(self, subsystems: Optional[List[str]] = None) -> List[str]:
        """
        Wait for changes in MPD subsystems (blocking).
        
        Args:
            subsystems: List of subsystems to watch. If None, watches all.
            
        Returns:
            List of subsystems that changed.
        """
        # Note: This method uses client_status which should not be locked with command_lock
        # as it's designed for blocking idle operations
        try:
            with self._idle_lock:
                self._in_idle = True
            
            if subsystems:
                result = self.client_status.idle(*subsystems)
            else:
                result = self.client_status.idle()
            
            with self._idle_lock:
                self._in_idle = False
            
            return result
        except Exception as e:
            with self._idle_lock:
                self._in_idle = False
            
            # Don't log error if it's just a connection lost during shutdown
            if not self._connected:
                return []
            logger.debug(f"Idle interrupted or error: {e}")
            self.check_connection_error(e)
            return []

    def noidle(self):
        """Cancel the current idle wait."""
        with self._idle_lock:
            if not self._in_idle:
                return  # No idle active, nothing to cancel
        
        try:
            # Send noidle command - this will cause idle() to return immediately
            # We need to use the raw command interface
            self.client_status._write_command("noidle")
            # Read the response (changed subsystems or empty list)
            try:
                self.client_status._read_list()
            except AttributeError:
                # Fallback if _read_list doesn't exist
                self.client_status._fetch_list()
            logger.debug("Sent noidle to cancel idle wait")
        except Exception as e:
            logger.debug(f"Error in noidle: {e}")
        
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
