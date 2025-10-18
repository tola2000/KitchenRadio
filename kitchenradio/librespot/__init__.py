"""
KitchenRadio LibreSpot Package

A Python package for controlling go-librespot music server with support for
remote hosts, event monitoring, and playback control.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .client import KitchenRadioLibrespotClient
from .monitor import LibrespotMonitor
from .controller import LibrespotController

__all__ = [
    "KitchenRadioLibrespotClient",
    "LibrespotMonitor", 
    "LibrespotController"
]
