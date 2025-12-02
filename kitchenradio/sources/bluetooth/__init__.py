"""
Bluetooth package for KitchenRadio

Provides Bluetooth audio connectivity with auto-pairing support and AVRCP media control.
"""

from .controller import BluetoothController
from .avrcp_client import AVRCPClient, AVRCPState
from .bluez_client import BlueZClient
from .monitor import (
    BluetoothMonitor,
    PlaybackState,
    PlaybackStatus,
    TrackInfo
)

__all__ = [
    'BluetoothController',
    'BluetoothMonitor',
    'AVRCPClient',
    'BlueZClient',
    'AVRCPState',
    'PlaybackState',
    'PlaybackStatus',
    'TrackInfo'
]
