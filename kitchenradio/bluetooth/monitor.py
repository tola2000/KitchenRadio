""""""

Bluetooth Monitor - Device and AVRCP monitoring functionalityAVRCP Model - Data models for AVRCP state management



Contains:This module defines the data models used to represent AVRCP device state,

- Data models: PlaybackStatus, TrackInfo, PlaybackState, AVRCPStateplayback information, and track metadata.

- BluetoothMonitor: Main monitoring class (aligns with LibrespotMonitor and NowPlayingMonitor)"""

"""

from dataclasses import dataclass, field

import loggingfrom datetime import datetime

import threadingfrom enum import Enum

import timefrom typing import Optional, Dict, Any

from dataclasses import dataclass, field

from datetime import datetime

from enum import Enumclass PlaybackStatus(Enum):

from typing import Optional, Callable, Dict, Any, Set    """Playback status enum matching AVRCP/BlueZ status values"""

    STOPPED = "stopped"

from .bluez_client import BlueZClient    PLAYING = "playing"

from .avrcp_client import AVRCPClient    PAUSED = "paused"

    FORWARD_SEEK = "forward-seek"

logger = logging.getLogger(__name__)    REVERSE_SEEK = "reverse-seek"

    ERROR = "error"

    UNKNOWN = "unknown"

# ============================================================================

# Data Models

# ============================================================================@dataclass

class TrackInfo:

class PlaybackStatus(Enum):    """

    """Playback status enum matching AVRCP/BlueZ status values"""    Track metadata information.

    STOPPED = "stopped"    

    PLAYING = "playing"    Represents metadata for a single track from AVRCP/BlueZ MediaPlayer1 interface.

    PAUSED = "paused"    """

    FORWARD_SEEK = "forward-seek"    title: str = "Unknown"

    REVERSE_SEEK = "reverse-seek"    artist: str = "Unknown"

    ERROR = "error"    album: str = ""

    UNKNOWN = "unknown"    duration: int = 0  # Duration in milliseconds

    track_number: int = 0

    total_tracks: int = 0

@dataclass    

class TrackInfo:    def to_dict(self) -> Dict[str, Any]:

    """        """Convert to dictionary for serialization"""

    Track metadata information.        return {

                'title': self.title,

    Represents metadata for a single track from AVRCP/BlueZ MediaPlayer1 interface.            'artist': self.artist,

    """            'album': self.album,

    title: str = "Unknown"            'duration': self.duration,

    artist: str = "Unknown"            'track_number': self.track_number,

    album: str = ""            'total_tracks': self.total_tracks

    duration: int = 0  # Duration in milliseconds        }

    track_number: int = 0    

    total_tracks: int = 0    def get_duration_formatted(self) -> str:

            """

    def to_dict(self) -> Dict[str, Any]:        Get formatted duration string (MM:SS).

        """Convert to dictionary for serialization"""        

        return {        Returns:

            'title': self.title,            String in format "M:SS" or "MM:SS"

            'artist': self.artist,        """

            'album': self.album,        if self.duration <= 0:

            'duration': self.duration,            return "0:00"

            'track_number': self.track_number,        

            'total_tracks': self.total_tracks        total_seconds = self.duration // 1000

        }        minutes = total_seconds // 60

            seconds = total_seconds % 60

    def get_duration_formatted(self) -> str:        

        """        return f"{minutes}:{seconds:02d}"

        Get formatted duration string (MM:SS).

        

        Returns:@dataclass

            String in format "M:SS" or "MM:SS"class PlaybackState:

        """    """

        if self.duration <= 0:    Current playback state.

            return "0:00"    

            Tracks playback status, position, and current track information.

        total_seconds = self.duration // 1000    """

        minutes = total_seconds // 60    status: PlaybackStatus = PlaybackStatus.UNKNOWN

        seconds = total_seconds % 60    position: int = 0  # Position in milliseconds

            track: Optional[TrackInfo] = None

        return f"{minutes}:{seconds:02d}"    play_started_at: Optional[datetime] = None

    pause_started_at: Optional[datetime] = None

    

@dataclass    def to_dict(self) -> Dict[str, Any]:

class PlaybackState:        """Convert to dictionary for serialization"""

    """        return {

    Current playback state.            'status': self.status.value,

                'position': self.position,

    Tracks playback status, position, and current track information.            'track': self.track.to_dict() if self.track else None,

    """            'play_started_at': self.play_started_at.isoformat() if self.play_started_at else None,

    status: PlaybackStatus = PlaybackStatus.UNKNOWN            'pause_started_at': self.pause_started_at.isoformat() if self.pause_started_at else None

    position: int = 0  # Position in milliseconds        }

    track: Optional[TrackInfo] = None    

    play_started_at: Optional[datetime] = None    def get_progress_percentage(self) -> float:

    pause_started_at: Optional[datetime] = None        """

            Calculate playback progress as percentage.

    def to_dict(self) -> Dict[str, Any]:        

        """Convert to dictionary for serialization"""        Returns:

        return {            Progress from 0.0 to 100.0, or 0.0 if no track or no duration

            'status': self.status.value,        """

            'position': self.position,        if not self.track or self.track.duration <= 0:

            'track': self.track.to_dict() if self.track else None,            return 0.0

            'play_started_at': self.play_started_at.isoformat() if self.play_started_at else None,        

            'pause_started_at': self.pause_started_at.isoformat() if self.pause_started_at else None        return (self.position / self.track.duration) * 100.0

        }

    

    def get_progress_percentage(self) -> float:@dataclass

        """class AVRCPState:

        Calculate playback progress as percentage.    """

            Complete AVRCP device state.

        Returns:    

            Progress from 0.0 to 100.0, or 0.0 if no track or no duration    Represents the complete state of an AVRCP-enabled Bluetooth device,

        """    including connection status, device information, and playback state.

        if not self.track or self.track.duration <= 0:    """

            return 0.0    device_name: str = ""

            device_mac: str = ""

        return (self.position / self.track.duration) * 100.0    device_path: str = ""

    connected: bool = False

    avrcp_available: bool = False

@dataclass    playback: PlaybackState = field(default_factory=PlaybackState)

class AVRCPState:    last_updated: Optional[datetime] = None

    """    state_changes: int = 0

    Complete AVRCP device state.    

        def connect(self, device_name: str, device_mac: str, device_path: str):

    Represents the complete state of an AVRCP-enabled Bluetooth device,        """

    including connection status, device information, and playback state.        Mark device as connected.

    """        

    device_name: str = ""        Args:

    device_mac: str = ""            device_name: Human-readable device name

    device_path: str = ""            device_mac: Device MAC address

    connected: bool = False            device_path: D-Bus object path

    avrcp_available: bool = False        """

    playback: PlaybackState = field(default_factory=PlaybackState)        self.device_name = device_name

    last_updated: Optional[datetime] = None        self.device_mac = device_mac

    state_changes: int = 0        self.device_path = device_path

            self.connected = True

    def connect(self, device_name: str, device_mac: str, device_path: str):        self.last_updated = datetime.now()

        """        self.state_changes += 1

        Mark device as connected.    

            def disconnect(self):

        Args:        """Mark device as disconnected and reset playback state"""

            device_name: Human-readable device name        self.connected = False

            device_mac: Device MAC address        self.avrcp_available = False

            device_path: D-Bus object path        self.playback = PlaybackState()

        """        self.last_updated = datetime.now()

        self.device_name = device_name        self.state_changes += 1

        self.device_mac = device_mac    

        self.device_path = device_path    def set_avrcp_available(self, available: bool):

        self.connected = True        """

        self.last_updated = datetime.now()        Set AVRCP availability status.

        self.state_changes += 1        

            Args:

    def disconnect(self):            available: True if AVRCP media player is available

        """Mark device as disconnected and reset playback state"""        """

        self.connected = False        self.avrcp_available = available

        self.avrcp_available = False        self.last_updated = datetime.now()

        self.playback = PlaybackState()        self.state_changes += 1

        self.last_updated = datetime.now()    

        self.state_changes += 1    def update_track(self, track: TrackInfo):

            """

    def set_avrcp_available(self, available: bool):        Update current track information.

        """        

        Set AVRCP availability status.        Args:

                    track: TrackInfo object with new track data

        Args:        """

            available: True if AVRCP media player is available        self.playback.track = track

        """        self.last_updated = datetime.now()

        self.avrcp_available = available        self.state_changes += 1

        self.last_updated = datetime.now()    

        self.state_changes += 1    def update_status(self, status: PlaybackStatus):

            """

    def update_track(self, track: TrackInfo):        Update playback status.

        """        

        Update current track information.        Args:

                    status: New playback status

        Args:        """

            track: TrackInfo object with new track data        old_status = self.playback.status

        """        self.playback.status = status

        self.playback.track = track        

        self.last_updated = datetime.now()        # Track timing for play/pause events

        self.state_changes += 1        if status == PlaybackStatus.PLAYING and old_status != PlaybackStatus.PLAYING:

                self.playback.play_started_at = datetime.now()

    def update_status(self, status: PlaybackStatus):            self.playback.pause_started_at = None

        """        elif status == PlaybackStatus.PAUSED and old_status != PlaybackStatus.PAUSED:

        Update playback status.            self.playback.pause_started_at = datetime.now()

                

        Args:        self.last_updated = datetime.now()

            status: New playback status        self.state_changes += 1

        """    

        old_status = self.playback.status    def update_position(self, position: int):

        self.playback.status = status        """

                Update playback position.

        # Track timing for play/pause events        

        if status == PlaybackStatus.PLAYING and old_status != PlaybackStatus.PLAYING:        Args:

            self.playback.play_started_at = datetime.now()            position: Position in milliseconds

            self.playback.pause_started_at = None        """

        elif status == PlaybackStatus.PAUSED and old_status != PlaybackStatus.PAUSED:        self.playback.position = position

            self.playback.pause_started_at = datetime.now()        self.last_updated = datetime.now()

                self.state_changes += 1

        self.last_updated = datetime.now()    

        self.state_changes += 1    def reset(self):

            """Reset all state to initial values"""

    def update_position(self, position: int):        self.device_name = ""

        """        self.device_mac = ""

        Update playback position.        self.device_path = ""

                self.connected = False

        Args:        self.avrcp_available = False

            position: Position in milliseconds        self.playback = PlaybackState()

        """        self.last_updated = None

        self.playback.position = position        self.state_changes = 0

        self.last_updated = datetime.now()    

        self.state_changes += 1    def to_dict(self) -> Dict[str, Any]:

            """Convert complete state to dictionary for serialization"""

    def reset(self):        return {

        """Reset all state to initial values"""            'device_name': self.device_name,

        self.device_name = ""            'device_mac': self.device_mac,

        self.device_mac = ""            'device_path': self.device_path,

        self.device_path = ""            'connected': self.connected,

        self.connected = False            'avrcp_available': self.avrcp_available,

        self.avrcp_available = False            'playback': self.playback.to_dict(),

        self.playback = PlaybackState()            'last_updated': self.last_updated.isoformat() if self.last_updated else None,

        self.last_updated = None            'state_changes': self.state_changes

        self.state_changes = 0        }

        

    def to_dict(self) -> Dict[str, Any]:    @classmethod

        """Convert complete state to dictionary for serialization"""    def from_dict(cls, data: Dict[str, Any]) -> 'AVRCPState':

        return {        """

            'device_name': self.device_name,        Create AVRCPState from dictionary.

            'device_mac': self.device_mac,        

            'device_path': self.device_path,        Args:

            'connected': self.connected,            data: Dictionary with state data

            'avrcp_available': self.avrcp_available,            

            'playback': self.playback.to_dict(),        Returns:

            'last_updated': self.last_updated.isoformat() if self.last_updated else None,            New AVRCPState instance

            'state_changes': self.state_changes        """

        }        state = cls(

                device_name=data.get('device_name', ''),

    @classmethod            device_mac=data.get('device_mac', ''),

    def from_dict(cls, data: Dict[str, Any]) -> 'AVRCPState':            device_path=data.get('device_path', ''),

        """            connected=data.get('connected', False),

        Create AVRCPState from dictionary.            avrcp_available=data.get('avrcp_available', False),

                    state_changes=data.get('state_changes', 0)

        Args:        )

            data: Dictionary with state data        

                    # Restore playback state

        Returns:        playback_data = data.get('playback', {})

            New AVRCPState instance        if playback_data:

        """            track_data = playback_data.get('track')

        state = cls(            if track_data:

            device_name=data.get('device_name', ''),                state.playback.track = TrackInfo(**track_data)

            device_mac=data.get('device_mac', ''),            

            device_path=data.get('device_path', ''),            status_str = playback_data.get('status', 'unknown')

            connected=data.get('connected', False),            try:

            avrcp_available=data.get('avrcp_available', False),                state.playback.status = PlaybackStatus(status_str)

            state_changes=data.get('state_changes', 0)            except ValueError:

        )                state.playback.status = PlaybackStatus.UNKNOWN

                    

        # Restore playback state            state.playback.position = playback_data.get('position', 0)

        playback_data = data.get('playback', {})        

        if playback_data:        # Restore timestamps

            track_data = playback_data.get('track')        last_updated_str = data.get('last_updated')

            if track_data:        if last_updated_str:

                state.playback.track = TrackInfo(**track_data)            state.last_updated = datetime.fromisoformat(last_updated_str)

                    

            status_str = playback_data.get('status', 'unknown')        return state

            try:    

                state.playback.status = PlaybackStatus(status_str)    def get_status_summary(self) -> str:

            except ValueError:        """

                state.playback.status = PlaybackStatus.UNKNOWN        Get human-readable status summary.

                    

            state.playback.position = playback_data.get('position', 0)        Returns:

                    String describing current state

        # Restore timestamps        """

        last_updated_str = data.get('last_updated')        if not self.connected:

        if last_updated_str:            return "Not connected"

            state.last_updated = datetime.fromisoformat(last_updated_str)        

                parts = [f"Device '{self.device_name}' connected"]

        return state        

            if self.avrcp_available:

    def get_status_summary(self) -> str:            parts.append("AVRCP available")

        """            

        Get human-readable status summary.            if self.playback.track:

                        status_str = self.playback.status.value

        Returns:                parts.append(f"{status_str} \"{self.playback.track.title}\" by {self.playback.track.artist}")

            String describing current state            else:

        """                parts.append("no track info")

        if not self.connected:        else:

            return "Not connected"            parts.append("AVRCP not available")

                

        parts = [f"Device '{self.device_name}' connected"]        return ", ".join(parts)

        
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

class BluetoothMonitor:
    """
    Monitor Bluetooth device connections and AVRCP media playback.
    
    Provides callbacks for:
    - Device connection/disconnection
    - Track changes
    - Playback status changes
    - AVRCP state changes
    """
    
    def __init__(self, bluez_client: BlueZClient):
        """
        Initialize monitor with BlueZ client.
        
        Args:
            bluez_client: BlueZ D-Bus client instance
        """
        self.client = bluez_client
        self.callbacks = {}
        self.current_track: Optional[TrackInfo] = None
        self.current_status: PlaybackStatus = PlaybackStatus.UNKNOWN
        self.current_state: Optional[AVRCPState] = None
        self.avrcp_client: Optional[AVRCPClient] = None
        self.is_monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Track connected devices
        self.connected_devices: Set[str] = set()  # MAC addresses
        self.current_device_path: Optional[str] = None
        self.current_device_name: Optional[str] = None
        
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
    
    def _on_device_properties_changed(self, interface: str, changed: Dict, 
                                     invalidated: list, path: str):
        """Handle device property changes from BlueZ client"""
        try:
            if interface != 'org.bluez.Device1':
                return
            
            # Get device info
            props = self.client.get_device_properties(path)
            if not props:
                return
            
            address = str(props.get('Address', ''))
            name = str(props.get('Name', 'Unknown'))
            
            # Handle connection events
            if 'Connected' in changed:
                if changed['Connected']:
                    if address not in self.connected_devices:
                        self.connected_devices.add(address)
                        self.current_device_path = path
                        self.current_device_name = name
                        
                        logger.info(f"🟢 Device connected: {name} ({address})")
                        
                        # Create AVRCP client for this device
                        self._setup_avrcp_client(path, name, address)
                        
                        # Trigger callback
                        self._trigger_callbacks('device_connected', name=name, mac=address)
                else:
                    if address in self.connected_devices:
                        self.connected_devices.remove(address)
                        if self.current_device_path == path:
                            self.current_device_path = None
                            self.current_device_name = None
                            
                        logger.info(f"🔴 Device disconnected: {name} ({address})")
                        
                        # Clean up AVRCP client
                        if self.avrcp_client:
                            self.avrcp_client.clear_cache()
                            self.avrcp_client = None
                        
                        self.current_track = None
                        self.current_status = PlaybackStatus.UNKNOWN
                        
                        # Trigger callback
                        self._trigger_callbacks('device_disconnected', name=name, mac=address)
                        
        except Exception as e:
            logger.error(f"Error handling device property change: {e}")
    
    def _setup_avrcp_client(self, device_path: str, name: str, address: str):
        """Setup AVRCP client for connected device"""
        try:
            # Wait a moment for MediaPlayer1 to be available
            time.sleep(1)
            
            self.avrcp_client = AVRCPClient(device_path, name, address)
            
            # Set up AVRCP callbacks
            self.avrcp_client.on_track_changed = self._on_track_changed
            self.avrcp_client.on_status_changed = self._on_status_changed
            self.avrcp_client.on_state_changed = self._on_state_changed
            
            # Get initial state
            if self.avrcp_client.is_available():
                logger.info("✅ AVRCP available")
                self.current_state = self.avrcp_client.get_state()
                self.current_track = self.avrcp_client.get_track_info()
                self.current_status = self.avrcp_client.get_status() or PlaybackStatus.UNKNOWN
            else:
                logger.info("⏳ AVRCP not yet available - will be available when playback starts")
                
        except Exception as e:
            logger.error(f"Error setting up AVRCP client: {e}")
    
    def _on_track_changed(self, track: TrackInfo):
        """Handle track change from AVRCP"""
        self.current_track = track
        logger.info(f"🎵 Track changed: {track.title} - {track.artist}")
        
        track_info = self._format_track_info(track)
        self._trigger_callbacks('track_changed', track=track_info)
        
        # Also trigger as track_started if we have a new track
        if track.title != 'Unknown':
            self._trigger_callbacks('track_started', track=track_info)
    
    def _on_status_changed(self, status: PlaybackStatus):
        """Handle playback status change from AVRCP"""
        old_status = self.current_status
        self.current_status = status
        
        logger.info(f"▶️  Status changed: {old_status.value} → {status.value}")
        
        # Trigger specific events based on status transition
        if status == PlaybackStatus.PLAYING and old_status != PlaybackStatus.PLAYING:
            if old_status == PlaybackStatus.PAUSED:
                logger.info("Track resumed")
                self._trigger_callbacks('track_resumed', track=self._format_track_info(self.current_track))
            else:
                logger.info("Track started")
                self._trigger_callbacks('track_started', track=self._format_track_info(self.current_track))
        elif status == PlaybackStatus.PAUSED and old_status == PlaybackStatus.PLAYING:
            logger.info("Track paused")
            self._trigger_callbacks('track_paused', track=self._format_track_info(self.current_track))
        elif status == PlaybackStatus.STOPPED:
            logger.info("Playback stopped")
            self._trigger_callbacks('track_ended', track=self._format_track_info(self.current_track))
        
        # Always trigger status_changed
        self._trigger_callbacks('status_changed', 
                               old_status=old_status.value, 
                               new_status=status.value)
    
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
        self.client.on_properties_changed = self._on_device_properties_changed
        
        # Scan for already connected devices
        self._scan_existing_devices()
        
        self.is_monitoring = True
        logger.info("✅ Bluetooth monitor started")
    
    def _scan_existing_devices(self):
        """Scan for already connected devices"""
        try:
            objects = self.client.get_managed_objects()
            
            for path, interfaces in objects.items():
                if 'org.bluez.Device1' in interfaces:
                    props = interfaces['org.bluez.Device1']
                    
                    if props.get('Connected', False):
                        address = str(props.get('Address', ''))
                        name = str(props.get('Name', 'Unknown'))
                        
                        self.connected_devices.add(address)
                        self.current_device_path = path
                        self.current_device_name = name
                        
                        logger.info(f"🟢 Already connected: {name} ({address})")
                        
                        # Setup AVRCP for this device
                        self._setup_avrcp_client(path, name, address)
                        
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
