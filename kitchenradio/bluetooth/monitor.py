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
