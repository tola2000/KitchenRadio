"""
Bluetooth package for KitchenRadio

Provides Bluetooth audio connectivity with auto-pairing support and AVRCP media control.
"""

from .controller import BluetoothController
from .avrcp_client import AVRCPClient
from .bluez_client import BlueZClient
from .monitor import (
    AVRCPState,
    PlaybackState,
    PlaybackStatus,
    TrackInfo
)

__all__ = [
    'BluetoothController',
    'AVRCPClient',
    'BlueZClient',
    'AVRCPState',
    'PlaybackState',
    'PlaybackStatus',
    'TrackInfo'
]
