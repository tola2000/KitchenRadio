"""
Bluetooth package for KitchenRadio

Provides Bluetooth audio connectivity with auto-pairing support and AVRCP media control.
"""

from .controller import BluetoothController
from .avrcp_client import AVRCPClient, PlaybackStatus

__all__ = ['BluetoothController', 'AVRCPClient', 'PlaybackStatus']
