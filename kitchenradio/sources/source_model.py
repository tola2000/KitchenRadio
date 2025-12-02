"""
Source Model - Centralized data models for audio sources

This module defines the data models used to represent device state,
playback information, and track metadata across different audio sources
(Bluetooth, MPD, Spotify/Librespot).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any


class SourceType(Enum):
    """Supported source types"""
    MPD = "mpd"
    LIBRESPOT = "librespot"
    BLUETOOTH = "bluetooth"
    NONE = "none"


class PlaybackStatus(Enum):
    """Playback status enum matching AVRCP/BlueZ/Librespot status values"""
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
    
    Represents metadata for a single track.
    """
    title: str = "Unknown"
    artist: str = "Unknown"
    album: str = ""
    duration: int = 0  # Duration in milliseconds
    file: str = ""     # File path (used by MPD)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'duration': self.duration,
            'duration_formatted': self.get_duration_formatted(),
            'file': self.file
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
class SourceInfo:
    """
    Source device information.
    """
    source: SourceType = SourceType.NONE
    device_name: str = "Unknown"
    device_mac: str = ""
    path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source.value,
            'device_name': self.device_name,
            'device_mac': self.device_mac,
            'path': self.path
        }


@dataclass
class PlaybackState:
    """
    Current playback state.
    
    Tracks playback status and volume.
    """
    status: PlaybackStatus = PlaybackStatus.UNKNOWN
    volume: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'status': self.status.value,
            'volume': self.volume
        }
