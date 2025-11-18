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
    
    def __init__(self):
        """
        Initialize AVRCP client (device-independent).
        Tracks all MediaPlayer1 objects and listens globally for events.
        """
        logger.debug("[TEST] AVRCPClient.__init__ called - DEBUG log should appear if logger is configured correctly.")
        logger.info("Initializing AVRCPClient (device-independent mode)")
        self.bus: Optional[dbus.SystemBus] = None

        # Track all MediaPlayer1 objects
        self.media_players: Dict[str, Dict[str, Any]] = {}

        # Callbacks
        self.on_track_changed: Optional[Callable[[str, TrackInfo], None]] = None  # device_path, track_info
        self.on_status_changed: Optional[Callable[[str, PlaybackStatus], None]] = None  # device_path, status

        self._connect_dbus()
        self._register_global_media_player_listener()

    def _register_global_media_player_listener(self):
        """
        Register a global DBus signal receiver for MediaPlayer1 PropertiesChanged events (all devices).
        """
        if not self.bus:
            return
        def on_properties_changed(interface, changed, invalidated, path=None, **kwargs):
            logger.debug(f"[AVRCPClient] PropertiesChanged on {interface} at {path}")
            logger.debug(f"  Changed: {dict(changed)}")
            logger.debug(f"  Invalidated: {list(invalidated)}")
            # Track state for each player
            if path:
                if path not in self.media_players:
                    self.media_players[path] = {}
                self.media_players[path].update(changed)
                # Callbacks for track/status changes
                if self.on_track_changed and 'Track' in changed:
                    self.on_track_changed(path, changed['Track'])
                if self.on_status_changed and 'Status' in changed:
                    self.on_status_changed(path, changed['Status'])
            # Track the current active player path (for control commands)
            self.player_path = None
            # Track the current active player path (for control commands)
            self.player_path: Optional[str] = None
        self.bus.add_signal_receiver(
            on_properties_changed,
            signal_name='PropertiesChanged',
            dbus_interface=self.PROPERTIES_INTERFACE,
            path=None,
            arg0=self.MEDIA_PLAYER_INTERFACE,
            sender_keyword='sender',
            path_keyword='path',
        )
        logger.info("[AVRCPClient] Global DBus listener for MediaPlayer1 PropertiesChanged events registered.")
    
    def _connect_dbus(self):
        """Connect to D-Bus"""
        try:
            self.bus = dbus.SystemBus()

            logger.debug("AVRCP client connected to D-Bus")
        except Exception as e:
            logger.error(f"Failed to connect to D-Bus: {e}")
    
    # Device-specific methods removed; now tracks all devices globally
    
    # Device-specific media player finding removed; now tracks all players globally
        
    def _on_properties_changed(self, interface, changed, invalidated):
        """Handle property changes from media player"""
        logger.debug(f"_on_properties_changed called with interface={interface}, changed={changed}, invalidated={invalidated}")
        if interface != self.MEDIA_PLAYER_INTERFACE:
            logger.debug(f"Ignoring property change for interface {interface}")
            return

        logger.info(f"📡 AVRCP DATA RECEIVED - Properties changed: {dict(changed)}")
        if invalidated:
            logger.info(f"📡 AVRCP DATA RECEIVED - Invalidated properties: {list(invalidated)}")

        logger.debug(f"AVRCP property changed: {dict(changed)}")

        state_changed = False

        # Extra debug: log all keys in changed
        logger.debug(f"AVRCP changed keys: {list(changed.keys())}")

        # Handle track changes
        if 'Track' in changed:
            logger.info(f"📡 AVRCP TRACK DATA: {changed['Track']}")
            logger.debug(f"Raw track dict: {changed['Track']}")
            track = self._parse_track_metadata(changed['Track'])
            logger.debug(f"Parsed track: title={track.title}, artist={track.artist}, album={track.album}, duration={track.duration}, track_number={track.track_number}, total_tracks={track.total_tracks}")
            self.state.update_track(track)
            logger.info(f"🎵 Track changed: {track.title} - {track.artist} ({track.album})")
            state_changed = True

            if self.on_track_changed:
                logger.debug("Calling on_track_changed callback")
                self.on_track_changed(track)

        # Handle status changes
        if 'Status' in changed:
            logger.info(f"📡 AVRCP STATUS DATA: {changed['Status']}")
            status_str = str(changed['Status'])
            logger.debug(f"Raw status string: {status_str}")
            try:
                status = PlaybackStatus(status_str)
            except ValueError:
                logger.warning(f"Unknown PlaybackStatus value: {status_str}")
                status = PlaybackStatus.UNKNOWN

            self.state.update_status(status)
            logger.info(f"▶️ Status changed: {status.value}")
            state_changed = True

            if self.on_status_changed:
                logger.debug("Calling on_status_changed callback")
                self.on_status_changed(status)

        # Handle position changes
        if 'Position' in changed:
            position = int(changed['Position'])
            logger.info(f"📡 AVRCP POSITION DATA: {position}ms")
            logger.debug(f"⏱️ Position: {position}ms")
            self.state.update_position(position)
            state_changed = True

        # Trigger state change callback if state was modified
        if state_changed and self.on_state_changed:
            logger.debug("Calling on_state_changed callback")
            self.on_state_changed(self.state)

    
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
      #  logger.info(f"📡 AVRCP: Sending Play command to {self.state.device_name}")
      #  return self._send_control_command('Play')
        return True
    
    def pause(self) -> bool:
        """
        Send pause command.
        
        Returns:
            True if successful
        """
        logger.info(f"📡 AVRCP: Sending Pause command to {self.state.device_name}")
        return self._send_control_command('Pause')
    
    def stop(self) -> bool:
        """
        Send stop command.
        
        Returns:
            True if successful
        """
        logger.info(f"📡 AVRCP: Sending Stop command to {self.state.device_name}")
        return self._send_control_command('Stop')
    
    def next(self) -> bool:
        """
        Skip to next track.
        
        Returns:
            True if successful
        """
        logger.info(f"📡 AVRCP: Sending Next command to {self.state.device_name}")
        return self._send_control_command('Next')
    
    def previous(self) -> bool:
        """
        Skip to previous track.
        
        Returns:
            True if successful
        """
        logger.info(f"📡 AVRCP: Sending Previous command to {self.state.device_name}")
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
    
    def get_volume(self) -> Optional[int]:
        """
        Get current volume from AVRCP MediaPlayer.
        
        Returns:
            Volume level (0-127) or None if not available
        """
        if not self.player_path or not self.bus:
            if not self._find_media_player():
                logger.debug("No media player for volume query")
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
            
            # Check if Volume property exists
            try:
                volume = player_props.Get(
                    self.MEDIA_PLAYER_INTERFACE,
                    'Volume'
                )
                
                volume_level = int(volume)
                logger.debug(f"📡 AVRCP Volume: {volume_level}")
                return volume_level
                
            except dbus.exceptions.DBusException as e:
                # Volume property not supported - this is common on iOS devices
                if "Unknown property" in str(e) or "does not exist" in str(e):
                    logger.debug(f"📡 AVRCP Volume property not supported by {self.state.device_name}")
                else:
                    logger.debug(f"Could not get AVRCP volume: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Error getting AVRCP volume: {e}")
            return None
    
    def set_volume(self, volume: int) -> bool:
        """
        Set volume via AVRCP MediaPlayer.
        
        Args:
            volume: Volume level (0-127)
            
        Returns:
            True if successful
        """
        if not self.player_path or not self.bus:
            if not self._find_media_player():
                logger.warning(f"Cannot set volume: no media player")
                return False
        
        try:
            # Clamp volume to valid range
            volume = max(0, min(127, volume))
            
            player_obj = self.bus.get_object(
                self.BLUEZ_SERVICE,
                self.player_path
            )
            player_props = dbus.Interface(
                player_obj,
                self.PROPERTIES_INTERFACE
            )
            
            logger.info(f"📡 AVRCP: Setting volume to {volume} on {self.state.device_name}")
            
            player_props.Set(
                self.MEDIA_PLAYER_INTERFACE,
                'Volume',
                dbus.UInt16(volume)
            )
            
            logger.info(f"🔊 AVRCP volume set to {volume}")
            
        except dbus.exceptions.DBusException as e:
            logger.warning(f"📡 AVRCP set volume failed (DBus): {e}")
            return False
        except Exception as e:
            logger.error(f"📡 AVRCP error setting volume: {e}")
            return False
    
    def volume_up(self, step: int = 10) -> bool:
        """
        Increase volume on the Bluetooth device via AVRCP.
        
        Note: Many devices (especially iOS) don't support absolute volume control.
        For such devices, this command may not work or may be ignored.
        
        Args:
            step: Volume increase step (default 10, AVRCP uses 0-127 range)
            
        Returns:
            True if successful
        """
        logger.info(f"📡 AVRCP: Increasing volume on {self.state.device_name}")
        
        # Try to get current volume
        current = self.get_volume()
        if current is not None:
            # Device supports absolute volume - use it
            new_volume = min(127, current + step)
            logger.debug(f"Using absolute volume: {current} → {new_volume}")
            return self.set_volume(new_volume)
        else:
            # Device doesn't support absolute volume
            # iOS and some Android devices don't expose volume control via AVRCP
            logger.info(f"📡 AVRCP Volume control not supported by {self.state.device_name}")
            logger.info(f"   Use device's physical volume buttons or control from device")
            return False
    
    def volume_down(self, step: int = 10) -> bool:
        """
        Decrease volume on the Bluetooth device via AVRCP.
        
        Note: Many devices (especially iOS) don't support absolute volume control.
        For such devices, this command may not work or may be ignored.
        
        Args:
            step: Volume decrease step (default 10, AVRCP uses 0-127 range)
            
        Returns:
            True if successful
        """
        logger.info(f"📡 AVRCP: Decreasing volume on {self.state.device_name}")
        
        # Try to get current volume
        current = self.get_volume()
        if current is not None:
            # Device supports absolute volume - use it
            new_volume = max(0, current - step)
            logger.debug(f"Using absolute volume: {current} → {new_volume}")
            return self.set_volume(new_volume)
        else:
            # Device doesn't support absolute volume
            # iOS and some Android devices don't expose volume control via AVRCP
            logger.info(f"📡 AVRCP Volume control not supported by {self.state.device_name}")
            logger.info(f"   Use device's physical volume buttons or control from device")
            return False
    
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
            
            # Log available methods for debugging (only first time)
            if not hasattr(self, '_logged_methods'):
                try:
                    introspection = player_obj.Introspect(dbus_interface='org.freedesktop.DBus.Introspectable')
                    logger.info(f"📡 AVRCP MediaPlayer methods available:\n{introspection}")
                    self._logged_methods = True
                except:
                    pass
            
            logger.info(f"📡 Calling AVRCP method: {command} on path {self.player_path}")
            
            # Call the method
            method = getattr(player_interface, command)
            method()
            
            # Select appropriate emoji based on command
            emoji_map = {
                "Next": "⏭️",
                "Previous": "⏮️",
                "Play": "▶️",
                "Pause": "⏸️",
                "Stop": "⏹️",
                "VolumeUp": "🔊",
                "VolumeDown": "🔉"
            }
            emoji = emoji_map.get(command, "✅")
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
