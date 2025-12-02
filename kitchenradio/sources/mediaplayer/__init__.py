"""
KitchenRadio - Mopidy Controller Package

A Python package for controlling Mopidy music server with support for
remote hosts, event monitoring, and playback control.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .client import KitchenRadioClient
from .monitor import MPDMonitor
from .controller import PlaybackController

__all__ = [
    "KitchenRadioClient",
    "MPDMonitor", 
    "PlaybackController"
]
