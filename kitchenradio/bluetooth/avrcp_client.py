#!/usr/bin/env python3
"""
AVRCP Client for Bluetooth Audio Control

Implements AVRCP (Audio/Video Remote Control Profile) client to:
- Get track metadata (title, artist, album)
- Get playback status (playing, paused, stopped)
- Get playback position
- Control playback (play, pause, next, previous)
- Get volume information

This allows KitchenRadio to display what's playing from connected devices
like iPhones, Android phones, etc.
"""

import dbus
import logging
from typing import Optional, Dict, Any, Callable

from .monitor import AVRCPState, TrackInfo, PlaybackStatus

logger = logging.getLogger(__name__)


class AVRCPClient:
    """
    AVRCP Client for Bluetooth media control.
    
    Communicates with BlueZ MediaPlayer1 interface to get track info
    and control playback from connected Bluetooth devices.
    """
    
    BLUEZ_SERVICE = 'org.bluez'
    MEDIA_PLAYER_INTERFACE = 'org.bluez.MediaPlayer1'
    PROPERTIES_INTERFACE = 'org.freedesktop.DBus.Properties'
    OBJECT_MANAGER_INTERFACE = 'org.freedesktop.DBus.ObjectManager'
    
    def __init__(self, device_path: Optional[str] = None, device_name: str = "Unknown", device_mac: str = ""):
        """
        Initialize AVRCP client.
        
        Args:
            device_path: D-Bus path to Bluetooth device (optional)
            device_name: Device name for state tracking
            device_mac: Device MAC address for state tracking
        """
        self.player_path: Optional[str] = None
        self.bus: Optional[dbus.SystemBus] = None
        
        # State model - centralized state management
        self.state = AVRCPState()
        
        if device_path:
            self.state.connect(device_name, device_mac, device_path)
        
        # Callbacks
        self.on_track_changed: Optional[Callable[[TrackInfo], None]] = None
        self.on_status_changed: Optional[Callable[[PlaybackStatus], None]] = None
        self.on_state_changed: Optional[Callable[[AVRCPState], None]] = None
        
        self._connect_dbus()
    
    def _connect_dbus(self):
        """Connect to D-Bus"""
        try:
            self.bus = dbus.SystemBus()
            logger.debug("AVRCP client connected to D-Bus")
        except Exception as e:
            logger.error(f"Failed to connect to D-Bus: {e}")
    
    def set_device(self, device_path: str, device_name: str = "Unknown", device_mac: str = ""):
        """
        Set the Bluetooth device to monitor.
        
        Args:
            device_path: D-Bus path to device (e.g., /org/bluez/hci0/dev_XX_XX_XX_XX_XX_XX)
            device_name: Device name
            device_mac: Device MAC address
        """
        self.state.connect(device_name, device_mac, device_path)
        self.player_path = None
        self._find_media_player()
    
    def _find_media_player(self) -> bool:
        """
        Find MediaPlayer1 object for current device.
        
        Returns:
            True if player found, False otherwise
        """
        if not self.state.device_path or not self.bus:
            return False
        
        try:
            # Get object manager
            obj_manager_obj = self.bus.get_object(
                self.BLUEZ_SERVICE, 
                '/'
            )
            obj_manager = dbus.Interface(
                obj_manager_obj, 
                self.OBJECT_MANAGER_INTERFACE
            )
            
            # Find all media player objects
            objects = obj_manager.GetManagedObjects()
            
            for path, interfaces in objects.items():
                # Check if this is a media player for our device
                if (self.MEDIA_PLAYER_INTERFACE in interfaces and 
                    str(path).startswith(str(self.state.device_path))):
                    self.player_path = path
                    logger.info(f"📻 Found AVRCP media player: {path}")
                    
                    # Update state
                    self.state.set_avrcp_available(True)
                    
                    # Subscribe to property changes
                    self._subscribe_to_changes()
                    
                    # Trigger state change callback
                    if self.on_state_changed:
                        self.on_state_changed(self.state)
                    
                    return True
            
            logger.warning(f"No AVRCP media player found for {self.state.device_path}")
            self.state.set_avrcp_available(False)
            return False
            
        except Exception as e:
            logger.error(f"Error finding media player: {e}")
            return False
    
    def _subscribe_to_changes(self):
        """Subscribe to property changes on media player"""
        if not self.bus or not self.player_path:
            return
        
        try:
            self.bus.add_signal_receiver(
                self._on_properties_changed,
                signal_name='PropertiesChanged',
                dbus_interface=self.PROPERTIES_INTERFACE,
                path=self.player_path
            )
            logger.debug("Subscribed to AVRCP property changes")
        except Exception as e:
            logger.error(f"Failed to subscribe to AVRCP changes: {e}")
    
    def _on_properties_changed(self, interface, changed, invalidated):
        """Handle property changes from media player"""
        try:
            if interface != self.MEDIA_PLAYER_INTERFACE:
                return
            
            # Log ALL AVRCP data received
            logger.info(f"📡 AVRCP DATA RECEIVED - Properties changed: {dict(changed)}")
            if invalidated:
                logger.info(f"📡 AVRCP DATA RECEIVED - Invalidated properties: {list(invalidated)}")
            
            logger.debug(f"AVRCP property changed: {dict(changed)}")
            
            state_changed = False
            
            # Handle track changes
            if 'Track' in changed:
                logger.info(f"📡 AVRCP TRACK DATA: {changed['Track']}")
                track = self._parse_track_metadata(changed['Track'])
                self.state.update_track(track)
                logger.info(f"🎵 Track changed: {track.title} - {track.artist} ({track.album})")
                state_changed = True
                
                if self.on_track_changed:
                    self.on_track_changed(track)
            
            # Handle status changes
            if 'Status' in changed:
                logger.info(f"📡 AVRCP STATUS DATA: {changed['Status']}")
                status_str = str(changed['Status'])
                try:
                    status = PlaybackStatus(status_str)
                except ValueError:
                    status = PlaybackStatus.UNKNOWN
                
                self.state.update_status(status)
                logger.info(f"▶️ Status changed: {status.value}")
                state_changed = True
                
                if self.on_status_changed:
                    self.on_status_changed(status)
            
            # Handle position changes
            if 'Position' in changed:
                position = int(changed['Position'])
                self.state.update_position(position)
                logger.info(f"📡 AVRCP POSITION DATA: {position}ms")
                logger.debug(f"⏱️ Position: {position}ms")
                state_changed = True
            
            # Trigger state change callback if state was modified
            if state_changed and self.on_state_changed:
                self.on_state_changed(self.state)
                
        except Exception as e:
            logger.error(f"❌ Error handling AVRCP property change: {e}", exc_info=True)
    
    def _parse_track_metadata(self, track_data: Dict) -> TrackInfo:
        """
        Parse track metadata from D-Bus dictionary.
        
        Args:
            track_data: D-Bus dictionary with track info
            
        Returns:
            TrackInfo object with parsed metadata
        """
        try:
            # Extract common fields
            title = str(track_data.get('Title', 'Unknown'))
            artist = str(track_data.get('Artist', 'Unknown'))
            album = str(track_data.get('Album', ''))
            duration = int(track_data.get('Duration', 0))
            track_number = int(track_data.get('TrackNumber', 0))
            total_tracks = int(track_data.get('NumberOfTracks', 0))
            
            return TrackInfo(
                title=title,
                artist=artist,
                album=album,
                duration=duration,
                track_number=track_number,
                total_tracks=total_tracks
            )
                
        except Exception as e:
            logger.error(f"Error parsing track metadata: {e}")
            return TrackInfo(
                title="Unknown",
                artist="Unknown",
                album="",
                duration=0,
                track_number=0,
                total_tracks=0
            )
    
    def get_track_info(self) -> Optional[TrackInfo]:
        """
        Get current track information.
        
        Returns:
            TrackInfo object or None if not available
        """
        # Return cached if available
        if self.state.playback.track:
            logger.debug(f"📡 Returning cached track: {self.state.playback.track.title}")
            return self.state.playback.track
        
        # Try to get from device
        if not self.player_path or not self.bus:
            # Try to find player first
            if not self._find_media_player():
                logger.debug(f"📡 No media player available for track info")
                return None
        
        try:
            logger.info(f"📡 Fetching initial track info from AVRCP...")
            player_obj = self.bus.get_object(
                self.BLUEZ_SERVICE,
                self.player_path
            )
            player_props = dbus.Interface(
                player_obj,
                self.PROPERTIES_INTERFACE
            )
            
            track_data = player_props.Get(
                self.MEDIA_PLAYER_INTERFACE,
                'Track'
            )
            
            logger.info(f"📡 AVRCP INITIAL TRACK DATA: {track_data}")
            track = self._parse_track_metadata(track_data)
            self.state.update_track(track)
            logger.info(f"📡 Initial track loaded: {track.title} - {track.artist}")
            return track
            
        except dbus.exceptions.DBusException as e:
            logger.debug(f"Could not get track info: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error getting track info: {e}", exc_info=True)
            return None
    
    def get_status(self) -> Optional[PlaybackStatus]:
        """
        Get playback status.
        
        Returns:
            PlaybackStatus enum value or None
        """
        # Return cached if available
        if self.state.playback.status != PlaybackStatus.UNKNOWN:
            logger.debug(f"📡 Returning cached status: {self.state.playback.status.value}")
            return self.state.playback.status
        
        if not self.player_path or not self.bus:
            if not self._find_media_player():
                logger.debug(f"📡 No media player available for status")
                return None
        
        try:
            logger.info(f"📡 Fetching initial playback status from AVRCP...")
            player_obj = self.bus.get_object(
                self.BLUEZ_SERVICE,
                self.player_path
            )
            player_props = dbus.Interface(
                player_obj,
                self.PROPERTIES_INTERFACE
            )
            
            status_str = player_props.Get(
                self.MEDIA_PLAYER_INTERFACE,
                'Status'
            )
            
            logger.info(f"📡 AVRCP INITIAL STATUS DATA: {status_str}")
            
            try:
                status = PlaybackStatus(str(status_str))
            except ValueError:
                status = PlaybackStatus.UNKNOWN
                
            self.state.update_status(status)
            logger.info(f"📡 Initial status loaded: {status.value}")
            return status
            
        except dbus.exceptions.DBusException as e:
            logger.debug(f"Could not get status: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return None
    
    def get_position(self) -> Optional[int]:
        """
        Get current playback position.
        
        Returns:
            Position in milliseconds or None
        """
        if not self.player_path or not self.bus:
            if not self._find_media_player():
                return None
        
        try:
            player_obj = self.bus.get_object(
                self.BLUEZ_SERVICE,
                self.player_path
            )
            player_props = dbus.Interface(
                player_obj,
                self.PROPERTIES_INTERFACE
            )
            
            position = player_props.Get(
                self.MEDIA_PLAYER_INTERFACE,
                'Position'
            )
            
            position_ms = int(position)
            self.state.update_position(position_ms)
            return position_ms
            
        except dbus.exceptions.DBusException as e:
            logger.debug(f"Could not get position: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting position: {e}")
            return None
    
    def play(self) -> bool:
        """
        Send play command.
        
        Returns:
            True if successful
        """
        return self._send_control_command('Play')
    
    def pause(self) -> bool:
        """
        Send pause command.
        
        Returns:
            True if successful
        """
        return self._send_control_command('Pause')
    
    def stop(self) -> bool:
        """
        Send stop command.
        
        Returns:
            True if successful
        """
        return self._send_control_command('Stop')
    
    def next(self) -> bool:
        """
        Skip to next track.
        
        Returns:
            True if successful
        """
        logger.info(f"📡 AVRCP: Sending Next command to {self.device_name}")
        return self._send_control_command('Next')
    
    def previous(self) -> bool:
        """
        Skip to previous track.
        
        Returns:
            True if successful
        """
        logger.info(f"📡 AVRCP: Sending Previous command to {self.device_name}")
        return self._send_control_command('Previous')
    
    def fast_forward(self) -> bool:
        """
        Fast forward.
        
        Returns:
            True if successful
        """
        return self._send_control_command('FastForward')
    
    def rewind(self) -> bool:
        """
        Rewind.
        
        Returns:
            True if successful
        """
        return self._send_control_command('Rewind')
    
    def _send_control_command(self, command: str) -> bool:
        """
        Send control command to media player.
        
        Args:
            command: Command name (Play, Pause, Stop, Next, Previous, etc.)
            
        Returns:
            True if successful
        """
        if not self.player_path or not self.bus:
            if not self._find_media_player():
                logger.warning(f"Cannot send {command}: no media player")
                return False
        
        try:
            player_obj = self.bus.get_object(
                self.BLUEZ_SERVICE,
                self.player_path
            )
            player_interface = dbus.Interface(
                player_obj,
                self.MEDIA_PLAYER_INTERFACE
            )
            
            # Call the method
            method = getattr(player_interface, command)
            method()
            
            emoji = "⏭️" if command == "Next" else "⏮️" if command == "Previous" else "✅"
            logger.info(f"{emoji} AVRCP command sent successfully: {command}")
            return True
            
        except dbus.exceptions.DBusException as e:
            logger.warning(f"📡 AVRCP {command} failed (DBus): {e}")
            return False
        except Exception as e:
            logger.error(f"📡 AVRCP error sending {command}: {e}")
            return False
    
    def is_available(self) -> bool:
        """
        Check if AVRCP is available for current device.
        
        Returns:
            True if media player is available
        """
        if self.player_path:
            return True
        
        return self._find_media_player()
    
    def get_state(self) -> AVRCPState:
        """
        Get complete AVRCP state.
        
        Returns:
            AVRCPState object with all current state information
        """
        return self.state
    
    def clear_cache(self):
        """Clear cached track info and status"""
        self.state.reset()
        logger.info("AVRCP state cleared")


# Example usage
if __name__ == "__main__":
    import sys
    from gi.repository import GLib
    import dbus.mainloop.glib
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python3 avrcp_client.py <device_mac>")
        print("Example: python3 avrcp_client.py AA:BB:CC:DD:EE:FF")
        sys.exit(1)
    
    # Convert MAC to D-Bus path
    mac = sys.argv[1].replace(':', '_')
    device_path = f'/org/bluez/hci0/dev_{mac}'
    
    print(f"Testing AVRCP client with device: {device_path}\n")
    
    # Setup D-Bus main loop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    
    # Create client
    client = AVRCPClient(device_path)
    
    # Setup callbacks
    def on_track_changed(track):
        print(f"\n🎵 Track Changed:")
        print(f"   Title:  {track.get('title', 'Unknown')}")
        print(f"   Artist: {track.get('artist', 'Unknown')}")
        print(f"   Album:  {track.get('album', 'Unknown')}")
        if 'duration' in track:
            duration_sec = track['duration'] / 1000
            print(f"   Duration: {duration_sec:.1f}s")
    
    def on_status_changed(status):
        print(f"\n▶️ Status Changed: {status}")
    
    client.on_track_changed = on_track_changed
    client.on_status_changed = on_status_changed
    
    # Get initial state
    print("Getting initial state...")
    
    if client.is_available():
        print("✅ AVRCP media player is available\n")
        
        track = client.get_track_info()
        if track:
            print("Current Track:")
            print(f"  Title:  {track.get('title', 'Unknown')}")
            print(f"  Artist: {track.get('artist', 'Unknown')}")
            print(f"  Album:  {track.get('album', 'Unknown')}")
        
        status = client.get_status()
        if status:
            print(f"\nPlayback Status: {status}")
        
        position = client.get_position()
        if position:
            print(f"Position: {position}ms")
    else:
        print("❌ AVRCP media player not available")
        print("Make sure device is connected and playing audio")
    
    print("\nMonitoring for changes... (Ctrl+C to stop)")
    
    # Run main loop
    mainloop = GLib.MainLoop()
    try:
        mainloop.run()
    except KeyboardInterrupt:
        print("\nStopped")
        mainloop.quit()
