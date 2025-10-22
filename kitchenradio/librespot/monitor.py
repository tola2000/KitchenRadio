"""
LibreSpot Monitor - Track monitoring functionality for go-librespot
"""

import time
import logging
import threading
from typing import Optional, Callable, Dict, Any
from .client import KitchenRadioLibrespotClient

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
        self.current_track = None
        self.current_status = {}
        self.is_monitoring = False
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()
        
    def add_callback(self, event: str, callback: Callable):
        """
        Add callback for specific event.
        
        Args:
            event: Event name (track_started, track_paused, track_resumed, track_ended, volume_changed, state_changed)
            callback: Callback function
        """
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
        logger.debug(f"Added callback for {event}")

    def _on_client_changed(self, **kwargs):
        try:
            self._wake_event.set()
        except Exception:
            pass

    def _trigger_callbacks(self, event: str, **kwargs):
        """Trigger callbacks for event."""

        for callback in self.callbacks['any']:
            try:
                callback(**kwargs)
            except Exception as e:
                logger.error(f"Error in 'any' callback for {event}: {e}")

        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(**kwargs)
                except Exception as e:
                    logger.error(f"Error in callback for {event}: {e}")
    
    def _format_track_info(self, status: Optional[Dict]) -> Dict[str, Any]:
        """
        Format go-librespot status information for track display.
        
        Args:
            status: go-librespot status dict
            
        Returns:
            Formatted track info dict
        """
        if not status:
            return {'name': 'No Track', 'artists': '', 'album': '', 'uri': ''}
        
        # Extract track info from status
        track = status.get('track', {})
        if not track:
            return {'name': 'No Track', 'artists': '', 'album': '', 'uri': ''}
        
        return {
            'name': track.get('name', 'Unknown Track'),
            'uri': track.get('uri', ''),
            'title': track.get('name', 'Unknown') if track else None,
            'artist': ", ".join(track.get('artist_names', [])) if track and track.get('artist_names') else None,
            'album': track.get('album_name', 'Unknown') if track else None, 
            'duration_ms': track.get('duration_ms', 0),
            'progress_ms': status.get('progress_ms', 0),
            'is_playing': status.get('is_playing', False)
        }
    
    def _on_mpd_state_changed(self, data):
        """Handle MPD state change events."""
        logger.info(f"MPD state changed: {data}")

    
    def _check_for_changes(self):
        """Check for status and track changes."""
        try:
            # Get current status
            status = self.client.get_status()
            if not status:
                return
            
            # Check for playing state changes
            old_paused = self.current_status.get('paused', False)
            new_paused = status.get('paused', False)
            old_stopped = self.current_status.get('stopped', False)
            new_stopped = status.get('stopped', False)     
            old_playing = not old_paused and not old_stopped
            new_playing = not new_paused and not new_stopped

            if old_playing != new_playing:
                logger.info(f"Playback state changed: {'playing' if new_playing else 'paused'}")
                self._trigger_callbacks('state_changed', 
                                      old_state='play' if old_playing else 'pause', 
                                      new_state='play' if new_playing else 'pause')
                
                track_info = self._format_track_info(status)
                
                if new_playing and not old_playing:
                    # Started or resumed playing
                    if self._is_same_track(status, self.current_status):
                        logger.info(f"Track resumed: {track_info['artist']} - {track_info['name']}")
                        self._trigger_callbacks('track_resumed', track=track_info)
                    else:
                        logger.info(f"Track started: {track_info['artist']} - {track_info['name']}")
                        self._trigger_callbacks('track_started', track=track_info)
                        
                elif not new_playing and old_playing:
                    # Paused
                    logger.info("Track paused")
                    self._trigger_callbacks('track_paused', track=track_info)
            
            # Check for track changes (different track URI)
            if self._is_different_track(status, self.current_status) and new_playing:
                track_info = self._format_track_info(status)
                self.current_track = track_info
                logger.info(f"New track: {track_info}")
                self._trigger_callbacks('track_started', track=track_info)
            
            # Check for volume changes
            old_volume = self.current_status.get('device', {}).get('volume_percent', 0)
            new_volume = status.get('device', {}).get('volume_percent', 0)
            
            if old_volume != new_volume:
                logger.info(f"Volume changed: {old_volume}% → {new_volume}%")
                self._trigger_callbacks('volume_changed', volume=new_volume)
            
            # Update current status
            self.current_status = status
            if status.get('track'):
                self.current_track = self._format_track_info(status)
                
        except Exception as e:
            logger.error(f"Error checking for changes: {e}")
    
    def _is_same_track(self, status1: Dict, status2: Dict) -> bool:
        """Check if two status objects represent the same track."""
        track1 = status1.get('track', {}).get('uri', '')
        track2 = status2.get('track', {}).get('uri', '')
        return track1 == track2 and track1 != ''
    
    def _is_different_track(self, status1: Dict, status2: Dict) -> bool:
        """Check if two status objects represent different tracks."""
        track1 = status1.get('track', {}).get('uri', '')
        track2 = status2.get('track', {}).get('uri', '')
        return track1 != track2 and track1 != ''
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        logger.info("Starting go-librespot monitoring loop")
        
        while not self._stop_event.is_set():
            if self.client.is_connected():
                self._check_for_changes()
            else:
                logger.warning("go-librespot connection lost")
                # Try to reconnect
                self.client.connect()
                
            try:
                # Wait either for wake_event (set by callback) or timeout
                self._wake_event.wait(timeout=1)
                # Clear wake flag so next wait will block again until next callback
                self._wake_event.clear()
            except Exception as e:
                # Fallback to small sleep if wait fails for any reason
               time.sleep(1.0)
        
        logger.info("go-librespot monitoring loop stopped")
    
    def start_monitoring(self):
        """Start monitoring go-librespot status changes."""
        if self.is_monitoring:
            logger.warning("Already monitoring")
            return
        
        logger.info("Starting go-librespot monitoring")
        
        # Ensure connection
        if not self.client.is_connected():
            self.client.connect()
        


        # Initialize current status
        self.current_status = self.client.get_status() or {}
        self.current_track = self._format_track_info(self.current_status)
        
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
            self._monitor_thread.join(timeout=5.0)
    
    def get_current_track(self) -> Optional[Dict[str, Any]]:
        """
        Get currently playing track info.
        
        Returns:
            Current track info dict or None
        """
        try:
            status = self.client.get_status()
            return self._format_track_info(status)
        except Exception as e:
            logger.error(f"Error getting current track: {e}")
            return None
        
    def get_status(self) -> Optional[Dict[str, Any]]:
        "Gets current status"
        try:
            return self.current_status
        except Exception as e:
            logger.error(f"Error getting current status: {e}")
            return None
           
    def print_current_track(self):
        """Print current track to console."""
        track = self.get_current_track()
        if track and track['name'] != 'No Track':
            progress = track.get('progress_ms', 0) // 1000
            duration = track.get('duration_ms', 0) // 1000
            progress_str = f" ({progress//60}:{progress%60:02d}/{duration//60}:{duration%60:02d})"
            playing_status = "▶️" if track.get('is_playing') else "⏸️"
            print(f"🎵 {playing_status} Now playing: {track['artists']} - {track['name']}{progress_str}")
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
