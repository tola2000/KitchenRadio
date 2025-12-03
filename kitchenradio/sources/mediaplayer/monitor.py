"""
Now Playing Monitor - Track monitoring functionality for MPD
"""

import time
import logging
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Dict, Any
from .client import KitchenRadioClient
from kitchenradio.sources.source_model import PlaybackStatus, TrackInfo, SourceInfo, PlaybackState

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class MPDMonitor:
    """
    Monitor now playing tracks and MPD status changes.
    """
    
    def __init__(self, client: KitchenRadioClient):
        """
        Initialize monitor with KitchenRadio client.
        
        Args:
            client: KitchenRadio client instance
        """
        self.client = client
        self.callbacks = {}
        
        self.current_track: Optional[TrackInfo] = None
        self.current_status: PlaybackState = PlaybackState()
        self.current_source_info: SourceInfo = SourceInfo(device_name="MPD")
        
        self.is_monitoring = False
        self._monitor_thread = None
        self._stop_event = threading.Event()
        
        # Track expected volume from commands (set by client events)
        self.expected_volume = None
        self.expected_volume_timestamp = None
        self.expected_value_timeout = 2.0  # Expire expected volume after 2 seconds
        
        # Track current playlist name (cached from load/clear events)
        self.current_playlist: str = ""
        
        # Subscribe to client command events
        self.client.add_callback('volume_command', self._on_volume_command)
        self.client.add_callback('playback_command', self._on_playback_command)
        self.client.add_callback('playlist_command', self._on_playlist_command)
        logger.debug("Monitor subscribed to client command events")
        
    def add_callback(self, event: str, callback: Callable):
        """
        Add callback for specific event.
        
        Args:
            event: Event name (track_started, track_paused, etc.)
            callback: Callback function
        """
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
        logger.debug(f"Added callback for {event}")
    
    def _on_volume_command(self, command: str, expected_volume: int, **kwargs):
        """
        Handle volume command from client.
        Notifies monitor of expected volume BEFORE MPD status updates.
        """
        logger.info(f"📢 Client sent volume command: {command}, expected volume: {expected_volume}")
        self.expected_volume = expected_volume
        self.expected_volume_timestamp = time.time()
        
        # Update current status immediately
        if self.current_status:
            self.current_status.volume = expected_volume
            self._trigger_callbacks('playback_state_changed', playback_state=self.get_playback_state())
    
    def _on_playback_command(self, command: str, expected_state: str, **kwargs):
        """
        Handle playback command from client.
        Log the command but don't update state - let actual MPD status drive display.
        """
        logger.info(f"🎵 Client sent playback command: {command}, will wait for MPD status update")
    
    def _on_playlist_command(self, command: str, playlist_name: str, **kwargs):
        """
        Handle playlist command from client.
        Caches the playlist name when loaded, clears it when playlist is cleared.
        """
        if command == 'load':
            self.current_playlist = playlist_name
            logger.info(f"📋 Playlist loaded: '{playlist_name}' - cached in monitor")
        elif command == 'clear':
            self.current_playlist = ""
            logger.info(f"📋 Playlist cleared - cache cleared in monitor")
        
        # Update current track with new playlist info if track exists
        if self.current_track:
            self.current_track.playlist = self.current_playlist
            self._trigger_callbacks('track_info_changed', track_info=self.current_track)
    
    def _is_expected_volume_valid(self) -> bool:
        """Check if expected volume is still valid (not expired)."""
        if self.expected_volume is None or self.expected_volume_timestamp is None:
            return False
        return (time.time() - self.expected_volume_timestamp) < self.expected_value_timeout
    
    def _clear_expired_expected_values(self):
        """Clear expected volume if it has expired."""
        if self.expected_volume is not None and not self._is_expected_volume_valid():
            logger.debug(f"⏱️ Expected volume expired: {self.expected_volume}")
            self.expected_volume = None
            self.expected_volume_timestamp = None
    
    def _trigger_callbacks(self, event: str, **kwargs):
        """Trigger callbacks for event."""
        
        # Trigger 'any' callbacks if registered
        if 'any' in self.callbacks:
            for callback in self.callbacks['any']:
                try:
                    callback(event=event, **kwargs)
                except Exception as e:
                    logger.error(f"Error in 'any' callback for {event}: {e}")
                
        # Trigger specific event callbacks
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(**kwargs)
                except Exception as e:
                    logger.error(f"Error in callback for {event}: {e}")
    
    def _parse_track_info(self, song: Optional[Dict]) -> TrackInfo:
        """Parse MPD song info into TrackInfo"""
        if not song:
            return TrackInfo()
        
        # Parse duration (time is usually in seconds)
        duration_sec = 0
        try:
            duration_sec = float(song.get('time', 0))
        except (ValueError, TypeError):
            pass
            
        return TrackInfo(
            title=song.get('title', 'Unknown'),
            artist=song.get('artist', 'Unknown'),
            album=song.get('album', song.get('name', '')),
            duration=int(duration_sec * 1000),
            file=song.get('file', ''),
            playlist=self.current_playlist  # Include cached playlist name
        )

    def _parse_playback_status(self, status: Dict[str, Any]) -> PlaybackState:
        """Parse MPD status into PlaybackState"""
        if not status:
            return PlaybackState(status=PlaybackStatus.STOPPED)
            
        state_str = status.get('state', 'stop')
        playback_status = PlaybackStatus.STOPPED
        
        if state_str == 'play':
            playback_status = PlaybackStatus.PLAYING
        elif state_str == 'pause':
            playback_status = PlaybackStatus.PAUSED
        
        # Handle volume
        volume = 0
        try:
            volume = int(status.get('volume', 0))
        except (ValueError, TypeError):
            pass
            
        # Handle expected volume override for immediate UI feedback
        if self._is_expected_volume_valid():
            volume = self.expected_volume
            
        return PlaybackState(status=playback_status, volume=volume)
    
    def _check_for_changes(self):
        """Check for status and song changes."""
        try:
            # Get current status and song
            status_data = self.client.get_status()
            song_data = self.client.get_current_song()
            
            # Parse new state from actual MPD data (without expected value overrides for comparison)
            state_str = status_data.get('state', 'stop') if status_data else 'stop'
            mpd_status = PlaybackStatus.STOPPED
            if state_str == 'play':
                mpd_status = PlaybackStatus.PLAYING
            elif state_str == 'pause':
                mpd_status = PlaybackStatus.PAUSED
            
            mpd_volume = 0
            try:
                mpd_volume = int(status_data.get('volume', 0)) if status_data else 0
            except (ValueError, TypeError):
                pass
            
            # Check for playback state change (compare against actual MPD state)
            status_changed = self.current_status.status != mpd_status
            volume_changed = self.current_status.volume != mpd_volume
            
            if status_changed or volume_changed:
                # Parse track info for logging
                new_track = self._parse_track_info(song_data)
                
                # Log changes with full track details
                if status_changed:
                    track_display = f"{new_track.artist} - {new_track.title}" if new_track and new_track.title != 'Unknown' else "No track"
                    album_display = f" [{new_track.album}]" if new_track and new_track.album else ""
                    logger.info(f"🎵 [MPD] Playback status changed: {self.current_status.status.value} → {mpd_status.value} | Track: {track_display}{album_display}")
                if volume_changed:
                    logger.info(f"🔊 [MPD] Volume changed: {self.current_status.volume} → {mpd_volume}")
                
                # Update current status with actual MPD values
                self.current_status = PlaybackState(status=mpd_status, volume=mpd_volume)
                self._trigger_callbacks('playback_state_changed', playback_state=self.get_playback_state())
                
            # Check for track change
            new_track = self._parse_track_info(song_data)
            
            # Check if track actually changed by comparing key fields
            # Handle None vs TrackInfo comparison properly
            track_changed = False
            
            if self.current_track is None and new_track is not None:
                track_changed = True
                logger.debug(f"[MPD] Track change: None → {new_track.title}")
            elif self.current_track is not None and new_track is None:
                track_changed = True
                logger.debug(f"[MPD] Track change: {self.current_track.title} → None")
            elif self.current_track != new_track:
                # Both are TrackInfo objects - check if they're different
                track_changed = True
                logger.debug(f"[MPD] Track objects differ: {self.current_track.title} vs {new_track.title}")
            
            if track_changed:
                logger.info(f"🎵 [MPD] Track changed: {self.current_track.title if self.current_track else 'None'} → {new_track.title if new_track else 'None'}")
                self.current_track = new_track
                self._trigger_callbacks('track_changed', track_info=self.get_track_info())
                logger.debug(f"[MPD] Emitted track_changed callback with track: {new_track.title if new_track else 'None'}")
            # else:
            #     logger.debug(f"[MPD] Track unchanged: {new_track.title if new_track else 'None'}")
            
            # Clear expected volume if it matches actual MPD volume
            if self._is_expected_volume_valid():
                mpd_volume = int(status_data.get('volume', 0)) if status_data.get('volume') else 0
                if mpd_volume == self.expected_volume:
                    self.expected_volume = None  # Matched, clear expected value
                    logger.debug(f"✅ Expected volume matched MPD volume: {mpd_volume}")
            
            self._clear_expired_expected_values()
                
        except Exception as e:
            logger.error(f"Error checking for changes: {e}", exc_info=True)
    
    def _monitor_loop(self):
        """Main monitoring loop - uses polling instead of idle."""
        logger.info("Starting MPD monitoring loop (polling mode)")
        
        poll_interval = 0.5  # Poll every 500ms
        
        while not self._stop_event.is_set():
            try:
                if self.client.is_connected():
                    # Check for changes by comparing current state
                    self._check_for_changes()
                    
                    # Wait before next poll (with interruptible sleep)
                    self._stop_event.wait(poll_interval)
                else:
                    # Don't try to reconnect if we're shutting down
                    if not self._stop_event.is_set():
                        logger.warning("MPD connection lost, try to reconnect")
                        if not self.client.connect():
                            self._stop_event.wait(5.0)  # Wait longer before retry if failed
                        
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                self._stop_event.wait(1.0)  # Avoid tight loop on error
        
        logger.info("MPD monitoring loop stopped")
    
    def start_monitoring(self):
        """Start monitoring MPD status changes."""
        if self.is_monitoring:
            logger.warning("Already monitoring")
            return
        
        logger.info("Starting MPD monitoring")
        
        # Initialize current status
        status = self.client.get_status()
        self.current_status = self._parse_playback_status(status)
        song_data = self.client.get_current_song()
        self.current_track = self._parse_track_info(song_data)
        
        logger.info(f"[MPD] Initial state - Status: {self.current_status.status.value}, Track: {self.current_track.title if self.current_track else 'None'}")
        logger.debug(f"[MPD] Raw song data: {song_data}")
        
        # Start monitoring thread
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        self.is_monitoring = True
    
    def stop_monitoring(self):
        """Stop monitoring MPD status changes."""
        logger.info("Stopping MPD monitoring")
        
        self.is_monitoring = False
        self._stop_event.set()
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.debug("Waiting for MPD monitor thread to exit...")
            self._monitor_thread.join(timeout=5.0)
            if self._monitor_thread.is_alive():
                logger.warning("MPD monitor thread did not exit within timeout")
            else:
                logger.debug("MPD monitor thread exited successfully")
    
    def get_track_info(self) -> Optional[TrackInfo]:
        """
        Get currently playing track info.
        
        Returns:
            Current track info object or None
        """
        return self.current_track
        
    def get_playback_state(self, force_refresh: bool = False) -> PlaybackState:
        """
        Get current playback state.
        
        Args:
            force_refresh: If True, fetch fresh state from MPD instead of using cached value
        
        Returns:
            Playback state object
        """
        # If force_refresh requested, get fresh state from MPD
        if force_refresh:
            try:
                status_data = self.client.get_status()
                if status_data:
                    # Parse actual MPD state
                    state_str = status_data.get('state', 'stop')
                    mpd_status = PlaybackStatus.STOPPED
                    if state_str == 'play':
                        mpd_status = PlaybackStatus.PLAYING
                    elif state_str == 'pause':
                        mpd_status = PlaybackStatus.PAUSED
                    
                    mpd_volume = 0
                    try:
                        mpd_volume = int(status_data.get('volume', 0))
                    except (ValueError, TypeError):
                        pass
                    
                    return PlaybackState(status=mpd_status, volume=mpd_volume)
            except Exception as e:
                logger.debug(f"Error fetching fresh playback state: {e}")
        
        # Fall back to cached current_status
        if isinstance(self.current_status, PlaybackState):
            return self.current_status
        return PlaybackState(status=PlaybackStatus.UNKNOWN, volume=0)

    def get_source_info(self) -> SourceInfo:
        """
        Get source information.
        """
        return self.current_source_info
    
    def print_current_track(self):
        """Print current track to console."""
        track = self.get_current_track()
        if track and track['name'] != 'No Track':
            print(f"🎵 Now playing: {track['artist']} - {track['name']}")
        else:
            print("🎵 No track currently playing")
    
    def run_forever(self):
        """Run monitoring loop forever."""
        if not self.is_monitoring:
            self.start_monitoring()
        
        try:
            logger.info("Starting monitoring loop")
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        finally:
            self.stop_monitoring()
