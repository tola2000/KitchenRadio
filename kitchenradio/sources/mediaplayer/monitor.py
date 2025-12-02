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
        
        # Track expected values from commands (set by client events)
        self.expected_volume = None
        self.expected_volume_timestamp = None
        self.expected_state = None
        self.expected_state_timestamp = None
        self.expected_value_timeout = 2.0  # Expire expected values after 2 seconds
        
        # Subscribe to client command events
        self.client.add_callback('volume_command', self._on_volume_command)
        self.client.add_callback('playback_command', self._on_playback_command)
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
        Notifies monitor of expected state BEFORE MPD status updates.
        """
        logger.info(f"🎵 Client sent playback command: {command}, expected state: {expected_state}")
        self.expected_state = expected_state
        self.expected_state_timestamp = time.time()
        
        # Update current status immediately
        if self.current_status:
            if expected_state == 'play':
                self.current_status.status = PlaybackStatus.PLAYING
            elif expected_state == 'pause':
                self.current_status.status = PlaybackStatus.PAUSED
            elif expected_state == 'stop':
                self.current_status.status = PlaybackStatus.STOPPED
                
            self._trigger_callbacks('playback_state_changed', playback_state=self.get_playback_state())
    
    def _is_expected_volume_valid(self) -> bool:
        """Check if expected volume is still valid (not expired)."""
        if self.expected_volume is None or self.expected_volume_timestamp is None:
            return False
        return (time.time() - self.expected_volume_timestamp) < self.expected_value_timeout
    
    def _is_expected_state_valid(self) -> bool:
        """Check if expected state is still valid (not expired)."""
        if self.expected_state is None or self.expected_state_timestamp is None:
            return False
        return (time.time() - self.expected_state_timestamp) < self.expected_value_timeout
    
    def _clear_expired_expected_values(self):
        """Clear expected values that have expired."""
        if self.expected_volume is not None and not self._is_expected_volume_valid():
            logger.debug(f"⏱️ Expected volume expired: {self.expected_volume}")
            self.expected_volume = None
            self.expected_volume_timestamp = None
        
        if self.expected_state is not None and not self._is_expected_state_valid():
            logger.debug(f"⏱️ Expected state expired: {self.expected_state}")
            self.expected_state = None
            self.expected_state_timestamp = None
    
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
            file=song.get('file', '')
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
            
        # Handle expected state override
        if self._is_expected_state_valid():
            expected = self.expected_state
            if expected == 'play':
                playback_status = PlaybackStatus.PLAYING
            elif expected == 'pause':
                playback_status = PlaybackStatus.PAUSED
            elif expected == 'stop':
                playback_status = PlaybackStatus.STOPPED
        
        # Handle volume
        volume = 0
        try:
            volume = int(status.get('volume', 0))
        except (ValueError, TypeError):
            pass
            
        # Handle expected volume override
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
                # Log changes
                if status_changed:
                    logger.info(f"🎵 [MPD] Playback status changed: {self.current_status.status.value} → {mpd_status.value}")
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
            else:
                logger.debug(f"[MPD] Track unchanged: {new_track.title if new_track else 'None'}")
            
            # Logic to clear expected values:
            mpd_state = status_data.get('state')
            mpd_volume = int(status_data.get('volume', 0)) if status_data.get('volume') else 0
            
            if self._is_expected_state_valid():
                if mpd_state == self.expected_state:
                     self.expected_state = None # Matched
            
            if self._is_expected_volume_valid():
                if mpd_volume == self.expected_volume:
                    self.expected_volume = None # Matched
            
            self._clear_expired_expected_values()
                
        except Exception as e:
            logger.error(f"Error checking for changes: {e}", exc_info=True)
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        logger.info("Starting MPD monitoring loop")
        
        while not self._stop_event.is_set():
            try:
                # Check stop event before doing any work
                if self._stop_event.is_set():
                    break
                    
                if self.client.is_connected():
                    #changes = self.client.wait_for_changes()
                    # Check stop event again before checking for changes
                    if not self._stop_event.is_set():
                        self._check_for_changes()
                else:
                    # Don't try to reconnect if we're shutting down
                    if not self._stop_event.is_set():
                        logger.warning("MPD connection lost, try to reconnect")
                        self.client.connect()
            except Exception as e:
                logger.error(f"Error While Getting Changes {e} ")

            # Wait for next check (exit immediately if stop event is set)
            self._stop_event.wait(1.0)  # Check every second
        
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
        
    def get_playback_state(self) -> PlaybackState:
        """
        Get current playback state.
        
        Returns:
            Playback state object
        """
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
