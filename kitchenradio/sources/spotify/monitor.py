"""
LibreSpot Monitor - Track monitoring functionality for go-librespot
"""

import time
import logging
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Dict, Any
from .client import KitchenRadioLibrespotClient
from kitchenradio.sources.source_model import PlaybackStatus, TrackInfo, SourceInfo, PlaybackState

logger = logging.getLogger(__name__)


class LibrespotMonitor:
    """
    Monitor now playing tracks and go-librespot status changes.
    """
    
    def __init__(self, client: KitchenRadioLibrespotClient):
        """
        Initialize monitor with KitchenRadio librespot client.
        
        Args:
            client: KitchenRadio librespot client instance
        """
        self.client = client
        self.callbacks = {}
        
        self.current_track: Optional[TrackInfo] = None
        self.current_status: PlaybackState = PlaybackState()
        self.current_source_info: SourceInfo = SourceInfo(device_name="Spotify Connect")
        self.current_volume: Optional[int] = None
        
        self.is_monitoring = False
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()
        
    def add_callback(self, event: str, callback: Callable):
        """
        Add callback for specific event.
        
        Args:
            event: Event name (track_started, track_paused, track_resumed, track_ended, volume_changed, state_changed, source_info_changed)
            callback: Callback function
        """
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
        logger.debug(f"Added callback for {event}")

    def _on_client_changed(self, **kwargs):
        """Handle WebSocket events from Spotify client"""
        try:
            self._wake_event.set()
        except Exception as e:
            logger.error(f"Error setting wake event: {e}")

    def _trigger_callbacks(self, event: str, **kwargs):
        """Trigger callbacks for event."""
        # logger.info(f"[DEBUG] Emitting event '{event}' with kwargs={kwargs}")
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
    
    def _parse_track_info(self, status_data: Dict[str, Any]) -> TrackInfo:
        """Parse track info from status data"""
        if not status_data:
            return TrackInfo()
            
        track_data = status_data.get('track', {})
        if not track_data:
            return TrackInfo()
            
        # Try to handle multiple formats
        title = track_data.get('title') or track_data.get('name') or track_data.get('track_name', 'Unknown')
        
        artist = track_data.get('artist')
        if not artist:
            artist_names = track_data.get('artist_names')
            if artist_names and isinstance(artist_names, list):
                artist = ", ".join(artist_names)
            else:
                artist = track_data.get('artist_name', 'Unknown')
                
        album = track_data.get('album') or track_data.get('album_name', '')
        duration = track_data.get('duration') or track_data.get('duration_ms', 0)
            
        return TrackInfo(
            title=title,
            artist=artist,
            album=album,
            duration=duration
        )

    def _parse_playback_status(self, status_data: Dict[str, Any]) -> PlaybackState:
        """Parse playback status from status data"""
        if not status_data:
            return PlaybackState(status=PlaybackStatus.STOPPED)
            
        # Determine status
        status = PlaybackStatus.UNKNOWN
        if status_data.get('stopped'):
            status = PlaybackStatus.STOPPED
        elif status_data.get('paused'):
            status = PlaybackStatus.PAUSED
        elif status_data.get('playing') or status_data.get('is_playing'):
            status = PlaybackStatus.PLAYING
        elif not status_data.get('stopped') and not status_data.get('paused') and status_data.get('track'):
            # If stopped=False, paused=False, and we have a track, then we're playing
            status = PlaybackStatus.PLAYING
        else:
            # Fallback logic
            state_str = str(status_data.get('state', '')).lower()
            if state_str == 'playing':
                status = PlaybackStatus.PLAYING
            elif state_str == 'paused':
                status = PlaybackStatus.PAUSED
            elif state_str == 'stopped':
                status = PlaybackStatus.STOPPED
            # If we have a track but status unclear, assume paused
            elif status_data.get('track'):
                status = PlaybackStatus.PAUSED
            else:
                status = PlaybackStatus.STOPPED
        
        # Try to get volume
        volume = status_data.get('volume')
        if volume is None:
             try:
                 volume = self.client.get_volume()
             except:
                 pass
        
        return PlaybackState(status=status, volume=volume)

    def _check_for_changes(self):
        """Check for status and track changes. Only emit events when state or track changes."""
        try:
            status = self.client.get_status()
            if not status or not isinstance(status, dict):
                logger.debug("[Spotify] No status data received")
                return
            
            # Check for playback state change
            new_state = self._parse_playback_status(status)
            logger.debug(f"[Spotify] Status check - Current: {self.current_status.status.value}, New: {new_state.status.value}, Vol: {self.current_status.volume}→{new_state.volume}")
            
 



            # Compare states (status and volume)
            status_changed = self.current_status.status != new_state.status
            volume_changed = self.current_status.volume != new_state.volume
            
            if status_changed or volume_changed:
                # Parse track info for logging
                # new_track = self._parse_track_info(status)
                
                # # If status changed (enum)
                # if status_changed:
                #     track_display = f"{new_track.artist} - {new_track.title}" if new_track and new_track.title != 'Unknown' else "No track"
                #     album_display = f" [{new_track.album}]" if new_track and new_track.album else ""
 
                self.current_status = new_state
                logger.info(f"🔊 [Spotify] Playback State changed: {self.current_status}")

                self._trigger_callbacks('playback_state_changed', playback_state=self.get_playback_state())

            # Check for track change
            new_track = self._parse_track_info(status)
            
            if self.current_track != new_track:
                # Format old and new track with full details
                old_display = f"{self.current_track.artist} - {self.current_track.title} [{self.current_track.album}]" if self.current_track and self.current_track.title != 'Unknown' else 'None'
                new_display = f"{new_track.artist} - {new_track.title} [{new_track.album}]" if new_track and new_track.title != 'Unknown' else 'None'
                logger.info(f"🎵 [Spotify] Track changed: {old_display} → {new_display}")
                self.current_track = new_track
                self._trigger_callbacks('track_changed', track_info=self.get_track_info())


            device  = status.get('device_name', {})
            device_changed = self.current_source_info.device_name != device

            if device_changed:
                old_device = self.current_source_info.device_name
                self.current_source_info.device_name = device
                logger.info(f"📱 [Spotify] Source device changed: {old_device} → {device}")
                self._trigger_callbacks('source_info_changed', source_info=self.get_source_info())


        except Exception as e:
            logger.error(f"Error checking for changes: {e}", exc_info=True)
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        logger.info("Starting go-librespot monitoring loop")
        
        while not self._stop_event.is_set():
            # Always check for changes - the client will handle reconnection internally
            self._check_for_changes()
                
            try:
                # Wait either for wake_event (set by callback) or timeout
                self._wake_event.wait(timeout=1)
                # Clear wake flag so next wait will block again until next callback
                self._wake_event.clear()
            except Exception as e:
                logger.error(f"[Spotify] Exception in monitor loop wait: {e}")
                # Fallback to small sleep if wait fails for any reason
                time.sleep(1.0)
        
        logger.info("go-librespot monitoring loop stopped")
    
    def start_monitoring(self):
        """Start monitoring go-librespot status changes."""
        if self.is_monitoring:
            logger.warning("Already monitoring")
            return
        
        logger.info("Starting go-librespot monitoring")
        
        # Reset reconnection state
        self._reconnect_attempts = 0
        self._last_reconnect_time = 0
        
        # Ensure connection
        if not self.client.is_connected():
            self.client.connect()
        
        # Initialize current status
        status = self.client.get_status()
        self.current_status = self._parse_playback_status(status)
        self.current_track = self._parse_track_info(status)
        
        logger.info(f"[Spotify] Initial state - Status: {self.current_status.status.value}, Track: {self.current_track.title if self.current_track else 'None'}")
        logger.debug(f"[Spotify] Raw status data: {status}")
        
        # Start monitoring thread
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        self.client.add_callback('any', self._on_client_changed)

        self.is_monitoring = True
    
    def stop_monitoring(self):
        """Stop monitoring go-librespot status changes."""
        logger.info("Stopping go-librespot monitoring")
        
        self.is_monitoring = False
        self._stop_event.set()
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.debug("Waiting for librespot monitor thread to exit...")
            self._monitor_thread.join(timeout=5.0)
            if self._monitor_thread.is_alive():
                logger.warning("Librespot monitor thread did not exit within timeout")
            else:
                logger.debug("Librespot monitor thread exited successfully")
    
    def get_track_info(self) -> Optional[TrackInfo]:
        """
        Get current track information.
        
        Returns:
            Formatted track info object or None
        """
        return self.current_track

    def get_source_info(self) -> SourceInfo:
        """
        Get current source information.
        
        Returns:
            Source info object
        """
        return self.current_source_info

    def get_playback_state(self, force_refresh: bool = False) -> PlaybackState:
        """
        Get current playback state.
        
        Args:
            force_refresh: If True, fetch fresh state from Spotify instead of using cached value
        
        Returns:
            Playback state object
        """
        # If force_refresh requested, get fresh state from Spotify
        if force_refresh:
            try:
                status = self.client.get_status()
                if status:
                    return self._parse_playback_status(status)
            except Exception as e:
                logger.debug(f"Error fetching fresh playback state: {e}")
        
        # Fall back to cached current_status
        if isinstance(self.current_status, PlaybackState):
            return self.current_status
            
        # Fallback if somehow it's not initialized or wrong type
        return PlaybackState(status=PlaybackStatus.UNKNOWN, volume=0)
    
    def reset_state(self):
        """
        Reset playback state and track info to default values.
        Called when device disconnects.
        """
        logger.info("🔄 Resetting Spotify state (device disconnected)")
        
        # Store previous state for comparison
        old_status = self.current_status
        old_track = self.current_track
        
        # Reset to stopped state with no track
        self.current_status = PlaybackState(status=PlaybackStatus.STOPPED, volume=None)
        self.current_track = None
        
        # Emit events if state changed
        if old_status.status != PlaybackStatus.STOPPED:
            logger.info(f"🎵 [Spotify] Playback status changed: {old_status.status.value} → stopped | Track: No track")
            self._trigger_callbacks('playback_state_changed', playback_state=self.current_status)
        
        if old_track is not None:
            logger.info(f"🎵 [Spotify] Track changed: {old_track.artist} - {old_track.title} → None")
            self._trigger_callbacks('track_changed', track_info=None)
    
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
