"""
AVRCP Model - Data models for AVRCP state management

This module defines the data models used to represent AVRCP device state,
playback information, and track metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from kitchenradio.sources.source_model import PlaybackStatus, TrackInfo, SourceInfo, PlaybackState


# ============================================================================
# BluetoothMonitor Class (aligns with LibrespotMonitor and NowPlayingMonitor)
# ============================================================================

import logging
import threading
import time
from typing import Optional, Callable, Dict, Any, Set

from .bluez_client import BlueZClient

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
    
    def __init__(self, client: BlueZClient, display_controller=None):
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
        self.current_status = None

        # Set up callbacks on the client
        self.client.on_track_changed = self._on_track_changed
        self.client.on_status_changed = self._on_status_changed

        self.is_monitoring = False
        self._monitor_thread = None
        self._stop_event = threading.Event()

        # Track connected devices
        self.connected_devices = set()  # MAC addresses
        self.current_source_info = SourceInfo()
        
    def add_callback(self, event: str, callback: Callable):
        """
        Add callback for specific event.
        
        Args:
            event: Event name (device_connected, device_disconnected, 
                   track_started, track_paused, track_resumed, 
                   status_changed, state_changed, source_info_changed, any)
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
    
    def _on_device_connected(self, device_path: str, device_name: str, device_mac: str):
        """
        Handle device connection event.
        
        Called by BlueZ client when a Bluetooth device connects. 
        BlueZ will automatically detect MediaPlayer interface when it appears
        and send property change events for track/status.
        
        Args:
            device_path: D-Bus path to the device
            device_name: Human-readable device name
            device_mac: Device MAC address
        """
        try:
            # Track the connected device
            self.connected_devices.add(device_mac)
            self.current_source_info = SourceInfo(
                device_name=device_name,
                device_mac=device_mac,
                path=device_path
            )
            
            logger.info(f"🟢 Device connected: {device_name} ({device_mac})")
            
            # Set active player path (BlueZ will auto-detect MediaPlayer when it appears)
            self.client.set_active_player(device_path)
            logger.info(f"📡 BlueZ monitoring for AVRCP MediaPlayer...")
            
            # Trigger callbacks to update display
            # Note: Track/status info will come via property change events when AVRCP becomes available
            self._trigger_callbacks('device_connected', name=device_name, mac=device_mac)
            self._trigger_callbacks('source_info_changed', source_info=self.current_source_info)
            
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
            
            if self.current_source_info.path == device_path:
                self.current_source_info = SourceInfo()
                self._trigger_callbacks('source_info_changed', source_info=self.current_source_info)
                
            logger.info(f"🔴 Device disconnected: {device_name} ({device_mac})")
            
            # Clean up AVRCP client
            if self.client.active_player_path == device_path:
                logger.info("🧹 Cleaning up AVRCP connection...")
                self.client.set_active_player(None)
            
            self.current_track = None
            self.current_status = None
            
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
        
        # Log with full track details including album
        album_display = f" [{track_info_obj.album}]" if track_info_obj.album else ""
        logger.info(f"🎵 [Bluetooth] Track changed: {track_info_obj.artist} - {track_info_obj.title}{album_display}")

        self._trigger_callbacks('track_changed', track_info=track_info_obj)

        # Update the display when track changes
        if self.display_controller:
            try:
                self.display_controller.render_bluetooth_track(track_info_obj.to_dict())
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

        # Log with full track details
        if self.current_track:
            track_display = f"{self.current_track.artist} - {self.current_track.title}" if self.current_track.title != 'Unknown' else "No track"
            album_display = f" [{self.current_track.album}]" if self.current_track.album else ""
            logger.info(f"🎵 [Bluetooth] Playback status changed: {old_status.value if old_status else 'None'} → {status_enum.value} | Track: {track_display}{album_display}")
        else:
            logger.info(f"🎵 [Bluetooth] Playback status changed: {old_status.value if old_status else 'None'} → {status_enum.value}")

        # Always trigger playback_state_changed
        self._trigger_callbacks('playback_state_changed', playback_state=self.get_playback_state())

        # Update the display when status changes
        if self.display_controller:
            try:
                self.display_controller.render_bluetooth_status(status_enum.value)
            except Exception as e:
                logger.error(f"Error updating Bluetooth display on status change: {e}")
    
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
        
        # Clean up AVRCP connection
        if self.client.active_player_path:
            self.client.set_active_player(None)
        
        logger.info("✅ Bluetooth monitor stopped")
    
    def get_track_info(self) -> Optional[TrackInfo]:
        """
        Get current track information.
        
        Returns:
            Formatted track info object or None
        """
        return self.current_track

    def get_source_info(self) -> SourceInfo:
        """
        Get current source information.
        
        Returns:
            Source info object
        """
        return self.current_source_info

    def get_playback_state(self) -> PlaybackState:
        """
        Get current playback state.
        
        Returns:
            Playback state object
        """
        volume = self.client.get_volume()
        status = self.current_status if self.current_status else PlaybackStatus.UNKNOWN
        return PlaybackState(status=status, volume=volume)
    
