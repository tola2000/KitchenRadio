#!/usr/bin/env python3
"""
AVRCP State Model

Data classes to represent Bluetooth audio state including
track information, playback status, and device state.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime


class PlaybackStatus(Enum):
    """Playback status enumeration"""
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
    Track metadata from AVRCP.
    
    Represents a single music track with all available metadata.
    """
    title: str = "Unknown"
    artist: str = "Unknown"
    album: str = ""
    duration: int = 0  # milliseconds
    track_number: Optional[int] = None
    total_tracks: Optional[int] = None
    genre: Optional[str] = None
    
    # Timestamp when this track info was received
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        """String representation for display"""
        parts = [f'"{self.title}"']
        if self.artist != "Unknown":
            parts.append(f"by {self.artist}")
        if self.album:
            parts.append(f"from {self.album}")
        return " ".join(parts)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'duration': self.duration,
            'track_number': self.track_number,
            'total_tracks': self.total_tracks,
            'genre': self.genre,
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TrackInfo':
        """Create TrackInfo from dictionary"""
        return cls(
            title=data.get('title', 'Unknown'),
            artist=data.get('artist', 'Unknown'),
            album=data.get('album', ''),
            duration=data.get('duration', 0),
            track_number=data.get('track_number'),
            total_tracks=data.get('total_tracks'),
            genre=data.get('genre')
        )
    
    def get_duration_formatted(self) -> str:
        """Get duration as formatted string (MM:SS)"""
        if self.duration <= 0:
            return "0:00"
        
        seconds = self.duration / 1000
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def is_valid(self) -> bool:
        """Check if track has valid metadata"""
        return self.title != "Unknown" or self.artist != "Unknown"


@dataclass
class PlaybackState:
    """
    Current playback state.
    
    Represents the current state of audio playback including
    status, position, and timing information.
    """
    status: PlaybackStatus = PlaybackStatus.UNKNOWN
    position: int = 0  # milliseconds
    track: Optional[TrackInfo] = None
    
    # State tracking
    last_updated: datetime = field(default_factory=datetime.now)
    play_started_at: Optional[datetime] = None
    pause_started_at: Optional[datetime] = None
    
    def __str__(self) -> str:
        """String representation for display"""
        status_icons = {
            PlaybackStatus.PLAYING: "▶️",
            PlaybackStatus.PAUSED: "⏸️",
            PlaybackStatus.STOPPED: "⏹️",
            PlaybackStatus.FORWARD_SEEK: "⏩",
            PlaybackStatus.REVERSE_SEEK: "⏪",
        }
        icon = status_icons.get(self.status, "❓")
        return f"{icon} {self.status.value.upper()}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'status': self.status.value,
            'position': self.position,
            'track': self.track.to_dict() if self.track else None,
            'last_updated': self.last_updated.isoformat(),
            'play_started_at': self.play_started_at.isoformat() if self.play_started_at else None,
            'pause_started_at': self.pause_started_at.isoformat() if self.pause_started_at else None
        }
    
    def is_playing(self) -> bool:
        """Check if currently playing"""
        return self.status == PlaybackStatus.PLAYING
    
    def is_paused(self) -> bool:
        """Check if currently paused"""
        return self.status == PlaybackStatus.PAUSED
    
    def is_stopped(self) -> bool:
        """Check if stopped"""
        return self.status == PlaybackStatus.STOPPED
    
    def get_position_formatted(self) -> str:
        """Get position as formatted string (MM:SS)"""
        if self.position <= 0:
            return "0:00"
        
        seconds = self.position / 1000
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def get_progress_percentage(self) -> float:
        """Get playback progress as percentage (0-100)"""
        if not self.track or self.track.duration <= 0:
            return 0.0
        
        return min(100.0, (self.position / self.track.duration) * 100)
    
    def get_time_remaining(self) -> int:
        """Get remaining time in milliseconds"""
        if not self.track or self.track.duration <= 0:
            return 0
        
        return max(0, self.track.duration - self.position)
    
    def update_status(self, new_status: PlaybackStatus):
        """Update status and track timing"""
        if new_status != self.status:
            old_status = self.status
            self.status = new_status
            self.last_updated = datetime.now()
            
            # Track when play/pause started
            if new_status == PlaybackStatus.PLAYING:
                self.play_started_at = datetime.now()
                self.pause_started_at = None
            elif new_status == PlaybackStatus.PAUSED:
                self.pause_started_at = datetime.now()
            elif new_status == PlaybackStatus.STOPPED:
                self.play_started_at = None
                self.pause_started_at = None


@dataclass
class AVRCPState:
    """
    Complete AVRCP state model.
    
    Maintains the full state of AVRCP connection including
    device info, playback state, and connection status.
    """
    # Device information
    device_name: str = "Unknown Device"
    device_mac: str = ""
    device_path: str = ""
    
    # Connection state
    connected: bool = False
    avrcp_available: bool = False
    
    # Playback state
    playback: PlaybackState = field(default_factory=PlaybackState)
    
    # State tracking
    connected_at: Optional[datetime] = None
    disconnected_at: Optional[datetime] = None
    last_event: Optional[str] = None
    last_event_time: Optional[datetime] = None
    
    def __str__(self) -> str:
        """String representation for display"""
        parts = [f"Device: {self.device_name}"]
        if self.connected:
            parts.append("🟢 Connected")
            if self.avrcp_available:
                parts.append("📻 AVRCP Available")
            if self.playback.track and self.playback.track.is_valid():
                parts.append(f"\n  {self.playback.track}")
                parts.append(f"\n  {self.playback}")
        else:
            parts.append("🔴 Disconnected")
        return " | ".join(parts)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'device_name': self.device_name,
            'device_mac': self.device_mac,
            'device_path': self.device_path,
            'connected': self.connected,
            'avrcp_available': self.avrcp_available,
            'playback': self.playback.to_dict(),
            'connected_at': self.connected_at.isoformat() if self.connected_at else None,
            'disconnected_at': self.disconnected_at.isoformat() if self.disconnected_at else None,
            'last_event': self.last_event,
            'last_event_time': self.last_event_time.isoformat() if self.last_event_time else None
        }
    
    def connect(self, device_name: str, device_mac: str, device_path: str):
        """Mark device as connected"""
        self.device_name = device_name
        self.device_mac = device_mac
        self.device_path = device_path
        self.connected = True
        self.connected_at = datetime.now()
        self.disconnected_at = None
        self._record_event("connected")
    
    def disconnect(self):
        """Mark device as disconnected"""
        self.connected = False
        self.avrcp_available = False
        self.disconnected_at = datetime.now()
        self.playback.status = PlaybackStatus.STOPPED
        self._record_event("disconnected")
    
    def set_avrcp_available(self, available: bool):
        """Set AVRCP availability"""
        self.avrcp_available = available
        self._record_event("avrcp_available" if available else "avrcp_unavailable")
    
    def update_track(self, track: TrackInfo):
        """Update current track"""
        self.playback.track = track
        self.playback.position = 0  # Reset position on new track
        self._record_event("track_changed")
    
    def update_status(self, status: PlaybackStatus):
        """Update playback status"""
        self.playback.update_status(status)
        self._record_event(f"status_{status.value}")
    
    def update_position(self, position: int):
        """Update playback position"""
        self.playback.position = position
        self.playback.last_updated = datetime.now()
    
    def reset(self):
        """Reset all state"""
        self.device_name = "Unknown Device"
        self.device_mac = ""
        self.device_path = ""
        self.connected = False
        self.avrcp_available = False
        self.playback = PlaybackState()
        self.connected_at = None
        self.disconnected_at = None
        self.last_event = None
        self.last_event_time = None
    
    def _record_event(self, event: str):
        """Record an event in the state"""
        self.last_event = event
        self.last_event_time = datetime.now()
    
    def get_status_summary(self) -> dict:
        """Get a summary suitable for status display"""
        if not self.connected:
            return {
                'connected': False,
                'device_name': self.device_name,
                'message': 'Not connected'
            }
        
        summary = {
            'connected': True,
            'device_name': self.device_name,
            'device_mac': self.device_mac,
            'avrcp_available': self.avrcp_available,
            'playing': self.playback.is_playing(),
        }
        
        if self.playback.track and self.playback.track.is_valid():
            summary.update({
                'title': self.playback.track.title,
                'artist': self.playback.track.artist,
                'album': self.playback.track.album,
                'duration': self.playback.track.duration,
                'position': self.playback.position,
                'progress': self.playback.get_progress_percentage(),
                'status': self.playback.status.value
            })
        else:
            summary.update({
                'title': 'No track info',
                'artist': 'Bluetooth Audio',
                'album': '',
                'status': self.playback.status.value
            })
        
        return summary
    
    def is_active(self) -> bool:
        """Check if device is connected and playing"""
        return self.connected and self.playback.is_playing()


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("AVRCP State Model Examples")
    print("=" * 70)
    
    # Create state
    state = AVRCPState()
    print("\n1. Initial state:")
    print(state)
    
    # Connect device
    print("\n2. Device connected:")
    state.connect("iPhone 12", "AA:BB:CC:DD:EE:FF", "/org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF")
    print(state)
    
    # Set AVRCP available
    print("\n3. AVRCP available:")
    state.set_avrcp_available(True)
    print(state)
    
    # Update track
    print("\n4. New track playing:")
    track = TrackInfo(
        title="Bohemian Rhapsody",
        artist="Queen",
        album="A Night at the Opera",
        duration=354000,  # 5:54
        track_number=11,
        total_tracks=12
    )
    state.update_track(track)
    state.update_status(PlaybackStatus.PLAYING)
    print(state)
    print(f"   Duration: {track.get_duration_formatted()}")
    
    # Update position
    print("\n5. Playback progress:")
    state.update_position(90000)  # 1:30
    print(f"   Position: {state.playback.get_position_formatted()}")
    print(f"   Progress: {state.playback.get_progress_percentage():.1f}%")
    
    # Pause
    print("\n6. Paused:")
    state.update_status(PlaybackStatus.PAUSED)
    print(state)
    
    # Get status summary
    print("\n7. Status summary:")
    summary = state.get_status_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    # Convert to dict
    print("\n8. State as dictionary:")
    state_dict = state.to_dict()
    print(f"   Connected: {state_dict['connected']}")
    print(f"   Playing: {state_dict['playback']['status']}")
    print(f"   Track: {state_dict['playback']['track']['title']}")
    
    print("\n" + "=" * 70)
