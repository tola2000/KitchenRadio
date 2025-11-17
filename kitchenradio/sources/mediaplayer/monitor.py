"""
Now Playing Monitor - Track monitoring functionality for MPD
"""

import time
import logging
import threading
from typing import Optional, Callable, Dict, Any
from .client import KitchenRadioClient

logger = logging.getLogger(__name__)


class NowPlayingMonitor:
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
        self.current_track = None
        self.current_volume = None
        self.current_isPlaying = None
        self.current_status = {}
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
        
        # Immediately trigger callback with expected volume
        self._trigger_callbacks('volume_command_sent', expected_volume=expected_volume)
        # Also trigger volume_changed with expected value for immediate display update
        self._trigger_callbacks('volume_changed', volume=expected_volume)
    
    def _on_playback_command(self, command: str, expected_state: str, **kwargs):
        """
        Handle playback command from client.
        Notifies monitor of expected state BEFORE MPD status updates.
        """
        logger.info(f"🎵 Client sent playback command: {command}, expected state: {expected_state}")
        self.expected_state = expected_state
        self.expected_state_timestamp = time.time()
        
        # Immediately trigger callback with expected state
        self._trigger_callbacks('playback_command_sent', command=command, expected_state=expected_state)
        # Also trigger state_changed with expected value for immediate display update
        old_state = self.current_status.get('state')
        self._trigger_callbacks('state_changed', old_state=old_state, new_state=expected_state)
    
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
    
    def _format_track_info(self, song: Optional[Dict]) -> Dict[str, Any]:
        """
        Format MPD song information for display.
        
        Args:
            song: MPD song dict
            
        Returns:
            Formatted track info dict
        """
        if not song:
            return {'name': 'No Track', 'artist': '', 'album': '', 'file': ''}
        
        title = song.get('title', 'Unknown')
        artist = song.get('artist', 'Unknown')
            
        return {
            'title': song.get('title', 'Unknown'),
            'artist': song.get('artist', 'Unknown'),
            'album': song.get('album', song.get('name', 'Unknown')),
            'file': song.get('file', ''),
            'time': song.get('time', '0'),
            'pos': song.get('pos', '0')
        }
    
    def _check_for_changes(self):
        """Check for status and song changes."""
        try:
            # Get current status and song
            status = self.client.get_status()
            song = self.client.get_current_song()
            
            # Check for state changes
            old_state = self.current_status.get('state')
            new_state = status.get('state')
            
            if old_state != new_state:
                logger.info(f"State changed: {old_state} → {new_state}")
                self._trigger_callbacks('state_changed', old_state=old_state, new_state=new_state)
                
                # Trigger specific events based on state
                if new_state == 'play' and old_state != 'play':
                    track_info = self._format_track_info(song)
                    if old_state == 'pause':
                        logger.info(f"Track resumed: {str(track_info)}")
                        self._trigger_callbacks('track_resumed', track=track_info)
                    else:
                        logger.info(f"Track started: {str(track_info)}")
                        self._trigger_callbacks('track_started', track=track_info)
                        
                elif new_state == 'pause':
                    logger.info("Track paused")
                    self._trigger_callbacks('track_paused', track=self.current_track)
                    
                elif new_state == 'stop':
                    logger.info("Playback stopped")
                    self._trigger_callbacks('track_ended', track=self.current_track)
            
            # Check for song changes (different song ID or position reset)
            old_songid = self.current_status.get('songid')
            new_songid = status.get('songid')
            
            if old_songid != new_songid and new_state == 'play':
                track_info = self._format_track_info(song)
                self.current_track = track_info
                logger.info(f"New track: {str(track_info)}")
                self._trigger_callbacks('track_started', track=track_info)
            
            # Check for volume changes
            old_volume = self.current_status.get('volume')
            new_volume = status.get('volume')
            
            if old_volume != new_volume:
                # Check if this matches expected volume from command
                if self._is_expected_volume_valid():
                    if int(new_volume) == self.expected_volume:
                        logger.info(f"✅ Volume confirmed: {old_volume} → {new_volume} (matched expected {self.expected_volume})")
                        # Clear expected value - MPD has caught up
                        self.expected_volume = None
                        self.expected_volume_timestamp = None
                    else:
                        logger.warning(f"⚠️ Volume mismatch: got {new_volume}, expected {self.expected_volume}")
                        # Still trigger callback with actual value since it differs
                        self._trigger_callbacks('volume_changed', volume=int(new_volume) if new_volume else 0)
                else:
                    # No expected value or expired - this is a new change
                    logger.info(f"Volume changed: {old_volume} → {new_volume} (external change)")
                    self._trigger_callbacks('volume_changed', volume=int(new_volume) if new_volume else 0)
            
            # Check if state matches expected state from command
            if new_state != old_state and self._is_expected_state_valid():
                if new_state == self.expected_state:
                    logger.info(f"✅ Playback state confirmed: {new_state} (matched expected)")
                    # Clear expected value - MPD has caught up
                    self.expected_state = None
                    self.expected_state_timestamp = None
                else:
                    logger.warning(f"⚠️ State mismatch: got {new_state}, expected {self.expected_state}")
            
            # Clear expired expected values
            self._clear_expired_expected_values()
            
            # Update current status
            self.current_status = status
            if song:
                self.current_track = self._format_track_info(song)
                
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
        self.current_status = self.client.get_status()
        self.current_track = self._format_track_info(self.client.get_current_song())
        
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
    
    def get_current_track(self) -> Optional[Dict[str, Any]]:
        """
        Get currently playing track info.
        
        Returns:
            Current track info dict or None
        """
        try:
            song = self.client.get_current_song()
            return self._format_track_info(song)
        except Exception as e:
            logger.error(f"Error getting current track: {e}")
            return None
        
    def get_status(self) -> Optional[Dict[str, Any]]:
        """
        Get current status with expected values override.
        
        Returns status with expected values (if valid and not expired) instead of actual MPD values.
        This ensures immediate UI feedback while waiting for MPD to update.
        
        Expected values expire after 2 seconds and revert to actual MPD values.
        """
        try:
            # Clear any expired expected values
            self._clear_expired_expected_values()
            
            # Start with current MPD status
            status = self.current_status.copy() if self.current_status else {}
            
            # Override with expected volume if valid
            if self._is_expected_volume_valid():
                status['volume'] = str(self.expected_volume)
                logger.debug(f"⚡ Returning expected volume: {self.expected_volume} (not yet confirmed by MPD)")
            
            # Override with expected state if valid
            if self._is_expected_state_valid():
                status['state'] = self.expected_state
                logger.debug(f"⚡ Returning expected state: {self.expected_state} (not yet confirmed by MPD)")
            
            return status
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return None
    
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
