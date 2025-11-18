"""
AVRCP Model - Data models for AVRCP state management

This module defines the data models used to represent AVRCP device state,
playback information, and track metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class PlaybackStatus(Enum):
    """Playback status enum matching AVRCP/BlueZ status values"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    FORWARD_SEEK = "forward-seek"
    REVERSE_SEEK = "reverse-seek"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class TrackInfo:
    """
    Track metadata information.
    
    Represents metadata for a single track from AVRCP/BlueZ MediaPlayer1 interface.
    """
    title: str = "Unknown"
    artist: str = "Unknown"
    album: str = ""
    duration: int = 0  # Duration in milliseconds
    track_number: int = 0
    total_tracks: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'duration': self.duration,
            'track_number': self.track_number,
            'total_tracks': self.total_tracks
        }
    
    def get_duration_formatted(self) -> str:
        """
        Get formatted duration string (MM:SS).
        
        Returns:
            String in format "M:SS" or "MM:SS"
        """
        if self.duration <= 0:
            return "0:00"
        
        total_seconds = self.duration // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        return f"{minutes}:{seconds:02d}"


@dataclass
class PlaybackState:
    """
    Current playback state.
    
    Tracks playback status, position, and current track information.
    """
    status: PlaybackStatus = PlaybackStatus.UNKNOWN
    position: int = 0  # Position in milliseconds
    track: Optional[TrackInfo] = None
    play_started_at: Optional[datetime] = None
    pause_started_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'status': self.status.value,
            'position': self.position,
            'track': self.track.to_dict() if self.track else None,
            'play_started_at': self.play_started_at.isoformat() if self.play_started_at else None,
            'pause_started_at': self.pause_started_at.isoformat() if self.pause_started_at else None
        }
    
    def get_progress_percentage(self) -> float:
        """
        Calculate playback progress as percentage.
        
        Returns:
            Progress from 0.0 to 100.0, or 0.0 if no track or no duration
        """
        if not self.track or self.track.duration <= 0:
            return 0.0
        
        return (self.position / self.track.duration) * 100.0


@dataclass
class AVRCPState:
    """
    Complete AVRCP device state.
    
    Represents the complete state of an AVRCP-enabled Bluetooth device,
    including connection status, device information, and playback state.
    """
    device_name: str = ""
    device_mac: str = ""
    device_path: str = ""
    connected: bool = False
    avrcp_available: bool = False
    playback: PlaybackState = field(default_factory=PlaybackState)
    last_updated: Optional[datetime] = None
    state_changes: int = 0
    
    def connect(self, device_name: str, device_mac: str, device_path: str):
        """
        Mark device as connected.
        
        Args:
            device_name: Human-readable device name
            device_mac: Device MAC address
            device_path: D-Bus object path
        """
        self.device_name = device_name
        self.device_mac = device_mac
        self.device_path = device_path
        self.connected = True
        self.last_updated = datetime.now()
        self.state_changes += 1
    
    def disconnect(self):
        """Mark device as disconnected and reset playback state"""
        self.connected = False
        self.avrcp_available = False
        self.playback = PlaybackState()
        self.last_updated = datetime.now()
        self.state_changes += 1
    
    def set_avrcp_available(self, available: bool):
        """
        Set AVRCP availability status.
        
        Args:
            available: True if AVRCP media player is available
        """
        self.avrcp_available = available
        self.last_updated = datetime.now()
        self.state_changes += 1
    
    def update_track(self, track: TrackInfo):
        """
        Update current track information.
        
        Args:
            track: TrackInfo object with new track data
        """
        self.playback.track = track
        self.last_updated = datetime.now()
        self.state_changes += 1
    
    def update_status(self, status: PlaybackStatus):
        """
        Update playback status.
        
        Args:
            status: New playback status
        """
        old_status = self.playback.status
        self.playback.status = status
        
        # Track timing for play/pause events
        if status == PlaybackStatus.PLAYING and old_status != PlaybackStatus.PLAYING:
            self.playback.play_started_at = datetime.now()
            self.playback.pause_started_at = None
        elif status == PlaybackStatus.PAUSED and old_status != PlaybackStatus.PAUSED:
            self.playback.pause_started_at = datetime.now()
        
        self.last_updated = datetime.now()
        self.state_changes += 1
    
    def update_position(self, position: int):
        """
        Update playback position.
        
        Args:
            position: Position in milliseconds
        """
        self.playback.position = position
        self.last_updated = datetime.now()
        self.state_changes += 1
    
    def reset(self):
        """Reset all state to initial values"""
        self.device_name = ""
        self.device_mac = ""
        self.device_path = ""
        self.connected = False
        self.avrcp_available = False
        self.playback = PlaybackState()
        self.last_updated = None
        self.state_changes = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert complete state to dictionary for serialization"""
        return {
            'device_name': self.device_name,
            'device_mac': self.device_mac,
            'device_path': self.device_path,
            'connected': self.connected,
            'avrcp_available': self.avrcp_available,
            'playback': self.playback.to_dict(),
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'state_changes': self.state_changes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AVRCPState':
        """
        Create AVRCPState from dictionary.
        
        Args:
            data: Dictionary with state data
            
        Returns:
            New AVRCPState instance
        """
        state = cls(
            device_name=data.get('device_name', ''),
            device_mac=data.get('device_mac', ''),
            device_path=data.get('device_path', ''),
            connected=data.get('connected', False),
            avrcp_available=data.get('avrcp_available', False),
            state_changes=data.get('state_changes', 0)
        )
        
        # Restore playback state
        playback_data = data.get('playback', {})
        if playback_data:
            track_data = playback_data.get('track')
            if track_data:
                state.playback.track = TrackInfo(**track_data)
            
            status_str = playback_data.get('status', 'unknown')
            try:
                state.playback.status = PlaybackStatus(status_str)
            except ValueError:
                state.playback.status = PlaybackStatus.UNKNOWN
            
            state.playback.position = playback_data.get('position', 0)
        
        # Restore timestamps
        last_updated_str = data.get('last_updated')
        if last_updated_str:
            state.last_updated = datetime.fromisoformat(last_updated_str)
        
        return state
    
    def get_status_summary(self) -> str:
        """
        Get human-readable status summary.
        
        Returns:
            String describing current state
        """
        if not self.connected:
            return "Not connected"
        
        parts = [f"Device '{self.device_name}' connected"]
        
        if self.avrcp_available:
            parts.append("AVRCP available")
            
            if self.playback.track:
                status_str = self.playback.status.value
                parts.append(f"{status_str} \"{self.playback.track.title}\" by {self.playback.track.artist}")
            else:
                parts.append("no track info")
        else:
            parts.append("AVRCP not available")
        
        return ", ".join(parts)


# ============================================================================
# BluetoothMonitor Class (aligns with LibrespotMonitor and NowPlayingMonitor)
# ============================================================================

import logging
import threading
import time
from typing import Optional, Callable, Dict, Any, Set

from .bluez_client import BlueZClient
from .avrcp_client import AVRCPClient

logger = logging.getLogger(__name__)


class BluetoothMonitor:
    """
    Monitor Bluetooth device connections and AVRCP media playback.
    
    Similar to LibrespotMonitor and NowPlayingMonitor, this class monitors
    Bluetooth device events and AVRCP media playback. When a device connects,
    it automatically attempts to establish an AVRCP connection to get track info.
    
    Provides callbacks for:
    - Device connection/disconnection
    - Track changes
    - Playback status changes
    - AVRCP state changes
    """
    
    def __init__(self, client, display_controller=None):
        """
        Initialize monitor with BlueZ client.
        
        Args:
            client: BlueZ D-Bus client instance
            display_controller: DisplayController instance (optional)
        """
        self.client = client
        self.display_controller = display_controller
        self.callbacks = {}
        self.current_track = None
        self.current_status = PlaybackStatus.UNKNOWN
        self.current_state = None
        from .avrcp_client import AVRCPClient
        self.avrcp_client = AVRCPClient()
        self.avrcp_client.on_track_changed = self._on_track_changed
        self.avrcp_client.on_status_changed = self._on_status_changed
        self.avrcp_client.on_state_changed = self._on_state_changed
        self.is_monitoring = False
        self._monitor_thread = None
        self._stop_event = threading.Event()

        # Track connected devices
        self.connected_devices = set()  # MAC addresses
        self.current_device_path = None
        self.current_device_name = None
        
    def add_callback(self, event: str, callback: Callable):
        """
        Add callback for specific event.
        
        Args:
            event: Event name (device_connected, device_disconnected, 
                   track_started, track_paused, track_resumed, 
                   status_changed, state_changed, any)
            callback: Callback function
        """
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
        logger.debug(f"Added callback for {event}")
    
    def _trigger_callbacks(self, event: str, **kwargs):
        """Trigger callbacks for event."""
        
        # Trigger 'any' callbacks
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
    
    def _format_track_info(self, track: Optional[TrackInfo]) -> Dict[str, Any]:
        """
        Format track information for display.
        
        Args:
            track: TrackInfo object
            
        Returns:
            Formatted track info dict
        """
        if not track:
            return {
                'title': 'Unknown',
                'artist': 'Unknown',
                'album': '',
                'duration': 0
            }
        
        return {
            'title': track.title,
            'artist': track.artist,
            'album': track.album,
            'duration': track.duration,
            'duration_formatted': track.get_duration_formatted()
        }
    
    def _on_device_connected(self, device_path: str, device_name: str, device_mac: str):
        """
        Handle device connection event.
        
        Called by BlueZ client when a Bluetooth device connects. 
        Attempts to establish AVRCP connection to get track information.
        
        Args:
            device_path: D-Bus path to the device
            device_name: Human-readable device name
            device_mac: Device MAC address
        """
        try:
            # Track the connected device
            self.connected_devices.add(device_mac)
            self.current_device_path = device_path
            self.current_device_name = device_name
            
            logger.info(f"🟢 Device connected: {device_name} ({device_mac})")
            
            # Try to establish AVRCP connection for track info
            logger.info(f"📡 Attempting to establish AVRCP connection...")
            self._setup_avrcp_client(device_path, device_name, device_mac)
            
            # Trigger callback
            self._trigger_callbacks('device_connected', name=device_name, mac=device_mac)
            
        except Exception as e:
            logger.error(f"Error handling device connection: {e}")
    
    def _on_device_disconnected(self, device_path: str, device_name: str, device_mac: str):
        """
        Handle device disconnection event.
        
        Args:
            device_path: D-Bus path to the device
            device_name: Human-readable device name
            device_mac: Device MAC address
        """
        try:
            # Remove from tracked devices
            if device_mac in self.connected_devices:
                self.connected_devices.remove(device_mac)
            
            if self.current_device_path == device_path:
                self.current_device_path = None
                self.current_device_name = None
                
            logger.info(f"🔴 Device disconnected: {device_name} ({device_mac})")
            
            # Clean up AVRCP client
            if self.avrcp_client:
                logger.info("🧹 Cleaning up AVRCP connection...")
                self.avrcp_client.clear_cache()
                self.avrcp_client = None
            
            self.current_track = None
            self.current_status = PlaybackStatus.UNKNOWN
            
            # Trigger callback
            self._trigger_callbacks('device_disconnected', name=device_name, mac=device_mac)
            
        except Exception as e:
            logger.error(f"Error handling device disconnection: {e}")
    
    def _on_device_properties_changed(self, interface: str, changed: Dict, 
                                     invalidated: list, path: str):
        """
        Handle device property changes from BlueZ client.
        
        This is the callback registered with BlueZClient that receives all
        D-Bus property change signals. When a device connects/disconnects,
        this method triggers the appropriate handler to establish or clean up
        the AVRCP connection.
        """
        try:
            if interface != 'org.bluez.Device1':
                return
            
            # Get device info
            props = self.client.get_device_properties(path)
            if not props:
                return
            
            address = str(props.get('Address', ''))
            name = str(props.get('Name', 'Unknown'))
            
            # Handle connection state changes
            if 'Connected' in changed:
                if changed['Connected']:
                    # Device connected - establish AVRCP connection
                    if address not in self.connected_devices:
                        self._on_device_connected(path, name, address)
                else:
                    # Device disconnected
                    if address in self.connected_devices:
                        self._on_device_disconnected(path, name, address)
                        
        except Exception as e:
            logger.error(f"Error handling device property change: {e}")
    
    def _setup_avrcp_client(self, device_path: str, name: str, address: str):
        """
        Setup AVRCP client for connected device.
        
        Waits for MediaPlayer1 interface to become available, then creates
        AVRCP client to monitor track information and playback status.
        Uses retry logic to handle devices that take time to expose AVRCP.
        
        Args:
            device_path: D-Bus path to the device
            name: Device name
            address: Device MAC address
        """
        try:
            # Create AVRCP client immediately
            self.avrcp_client = AVRCPClient(device_path, name, address)
            
            # Set up AVRCP callbacks
            self.avrcp_client.on_track_changed = self._on_track_changed
            self.avrcp_client.on_status_changed = self._on_status_changed
            self.avrcp_client.on_state_changed = self._on_state_changed
            
            # Try to establish AVRCP connection with retries
            logger.info("⏳ Attempting to establish AVRCP MediaPlayer connection...")
            max_retries = 10  # Try for ~10 seconds
            retry_delay = 1.0  # 1 second between retries
            
            for attempt in range(max_retries):
                if self.avrcp_client.is_available():
                    logger.info(f"✅ AVRCP connection established on attempt {attempt + 1}")
                    self.current_state = self.avrcp_client.get_state()
                    self.current_track = self.avrcp_client.get_track_info()
                    self.current_status = self.avrcp_client.get_status() or PlaybackStatus.UNKNOWN
                    
                    # Log initial track info if available
                    if self.current_track and self.current_track.title != 'Unknown':
                        logger.info(f"🎵 Current track: {self.current_track.title} - {self.current_track.artist}")
                    
                    return  # Success!
                
                # Not available yet - wait and retry
                if attempt < max_retries - 1:  # Don't sleep on last attempt
                    logger.info(f"⏳ AVRCP not available yet (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    logger.info(f"⏳ AVRCP still not available after attempt {attempt + 1}/{max_retries}")
            
            # After all retries, AVRCP still not available
            logger.info("⏳ AVRCP not available after retries - will be activated when playback starts")
                
        except Exception as e:
            logger.error(f"Error setting up AVRCP client: {e}")
    
    def _on_track_changed(self, path: str, track: TrackInfo):
        """Handle track change from AVRCP"""
        # Convert dbus.Dictionary to TrackInfo if needed
        if hasattr(track, 'title'):
            track_info_obj = track
        else:
            # Extract fields from dbus.Dictionary
            title = str(track.get('Title', 'Unknown'))
            artist = str(track.get('Artist', 'Unknown'))
            album = str(track.get('Album', ''))
            duration = int(track.get('Duration', 0))
            track_info_obj = TrackInfo(title=title, artist=artist, album=album, duration=duration)
        self.current_track = track_info_obj
        logger.info(f"🎵 Track changed: {track_info_obj.title} - {track_info_obj.artist}")

        track_info = self._format_track_info(track_info_obj)
        self._trigger_callbacks('track_changed', track=track_info)

        # Also trigger as track_started if we have a new track
        if track_info_obj.title != 'Unknown':
            self._trigger_callbacks('track_started', track=track_info)

        # Update the display when track changes
        if self.display_controller:
            try:
                self.display_controller.render_bluetooth_track(track_info)
            except Exception as e:
                logger.error(f"Error updating Bluetooth display on track change: {e}")
    
    def _on_status_changed(self, path: str, status: PlaybackStatus):
        """Handle playback status change from AVRCP"""
        # Convert dbus.String or str to PlaybackStatus if needed
        if isinstance(status, PlaybackStatus):
            status_enum = status
        else:
            status_str = str(status)
            try:
                status_enum = PlaybackStatus(status_str)
            except ValueError:
                status_enum = PlaybackStatus.UNKNOWN
        old_status = self.current_status
        self.current_status = status_enum

        logger.info(f"▶️  Status changed: {old_status.value} → {status_enum.value}")

        # Trigger specific events based on status transition
        if status_enum == PlaybackStatus.PLAYING and old_status != PlaybackStatus.PLAYING:
            if old_status == PlaybackStatus.PAUSED:
                logger.info("⏯️  Track resumed")
                self._trigger_callbacks('track_resumed', track=self._format_track_info(self.current_track))
            else:
                logger.info("▶️  Track started")
                self._trigger_callbacks('track_started', track=self._format_track_info(self.current_track))
        elif status_enum == PlaybackStatus.PAUSED and old_status == PlaybackStatus.PLAYING:
            logger.info("⏸️  Track paused")
            self._trigger_callbacks('track_paused', track=self._format_track_info(self.current_track))
        elif status_enum == PlaybackStatus.STOPPED:
            logger.info("⏹️  Playback stopped")
            self._trigger_callbacks('track_ended', track=self._format_track_info(self.current_track))

        # Always trigger status_changed
        self._trigger_callbacks('status_changed', 
                               old_status=old_status.value, 
                               new_status=status_enum.value)

        # Update the display when status changes
        if self.display_controller:
            try:
                self.display_controller.render_bluetooth_status(status_enum.value)
            except Exception as e:
                logger.error(f"Error updating Bluetooth display on status change: {e}")
    
    def _on_state_changed(self, state: AVRCPState):
        """Handle complete state change from AVRCP"""
        self.current_state = state
        logger.debug(f"State changed: {state.get_status_summary()}")
        self._trigger_callbacks('state_changed', state=state)
    
    def start_monitoring(self):
        """Start monitoring Bluetooth devices and AVRCP"""
        if self.is_monitoring:
            logger.warning("Already monitoring")
            return
        
        logger.info("🔵 Starting Bluetooth monitor...")
        
        # Set up BlueZ property change callback
        # This allows the BlueZ client to notify us of device connections
        self.client.on_properties_changed = self._on_device_properties_changed
        
        # Scan for already connected devices
        self._scan_existing_devices()
        
        self.is_monitoring = True
        logger.info("✅ Bluetooth monitor started")
    
    def _scan_existing_devices(self):
        """
        Scan for already connected devices.
        
        Checks if any Bluetooth devices are already connected when monitoring
        starts, and attempts to establish AVRCP connections with them.
        """
        try:
            logger.info("🔍 Scanning for already connected devices...")
            objects = self.client.get_managed_objects()
            
            for path, interfaces in objects.items():
                if 'org.bluez.Device1' in interfaces:
                    props = interfaces['org.bluez.Device1']
                    
                    if props.get('Connected', False):
                        address = str(props.get('Address', ''))
                        name = str(props.get('Name', 'Unknown'))
                        
                        logger.info(f"🟢 Found already connected device: {name} ({address})")
                        
                        # Handle as a new connection
                        self._on_device_connected(path, name, address)
                        
        except Exception as e:
            logger.error(f"Error scanning existing devices: {e}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        if not self.is_monitoring:
            return
        
        logger.info("🔵 Stopping Bluetooth monitor...")
        
        self.is_monitoring = False
        
        # Clean up AVRCP client
        if self.avrcp_client:
            self.avrcp_client.clear_cache()
            self.avrcp_client = None
        
        logger.info("✅ Bluetooth monitor stopped")
    
    def get_current_track(self) -> Optional[Dict[str, Any]]:
        """
        Get current track information.
        
        Returns:
            Formatted track info dict or None
        """
        if self.current_track:
            return self._format_track_info(self.current_track)
        return None
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """
        Get current playback status.
        
        Returns:
            Status dict with state, device info, etc.
        """
        if not self.current_device_name:
            return {
                'connected': False,
                'state': 'stopped',
                'device': None
            }
        
        return {
            'connected': True,
            'state': self.current_status.value,
            'device': {
                'name': self.current_device_name,
                'path': self.current_device_path
            },
            'avrcp_available': self.avrcp_client is not None and self.avrcp_client.is_available()
        }
    
    def print_current_track(self):
        """Print current track to console"""
        track = self.get_current_track()
        if track:
            print(f"🎵 Now Playing:")
            print(f"   Title:  {track['title']}")
            print(f"   Artist: {track['artist']}")
            print(f"   Album:  {track['album']}")
            if track['duration'] > 0:
                print(f"   Duration: {track['duration_formatted']}")
        else:
            print("🔇 No track playing")
