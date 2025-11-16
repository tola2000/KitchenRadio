# AVRCP Client for KitchenRadio

## Overview

The AVRCP (Audio/Video Remote Control Profile) client allows KitchenRadio to:
- 🎵 **Display track metadata** from connected Bluetooth devices (iPhone, Android, etc.)
- ▶️ **Control playback** (play, pause, next, previous)
- ⏱️ **Get playback position** and duration
- 📊 **Monitor playback status** changes

## Features

### Track Information
- Title, artist, album
- Track number and total tracks
- Duration in milliseconds
- Real-time updates when track changes

### Playback Control
- Play/Pause/Stop
- Next/Previous track
- Fast forward/Rewind
- Status monitoring (playing, paused, stopped)

### Position Tracking
- Current playback position
- Duration of current track
- Position updates

## Usage

### Basic Usage

```python
from kitchenradio.bluetooth import AVRCPClient

# Create client for a device
device_path = '/org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF'
client = AVRCPClient(device_path)

# Check if AVRCP is available
if client.is_available():
    # Get track info
    track = client.get_track_info()
    print(f"Now playing: {track['title']} by {track['artist']}")
    
    # Get playback status
    status = client.get_status()  # 'playing', 'paused', 'stopped'
    
    # Control playback
    client.pause()
    client.next()
    client.play()
```

### With Callbacks

```python
client = AVRCPClient(device_path)

# Set up callbacks for real-time updates
def on_track_changed(track):
    print(f"New track: {track['title']}")

def on_status_changed(status):
    print(f"Status: {status}")

client.on_track_changed = on_track_changed
client.on_status_changed = on_status_changed
```

### Integration with BluetoothController

```python
from kitchenradio.bluetooth import BluetoothController, AVRCPClient

controller = BluetoothController()
avrcp_client = None

def on_connected(name, mac):
    global avrcp_client
    # Convert MAC to device path
    mac_path = mac.replace(':', '_')
    device_path = f'/org/bluez/hci0/dev_{mac_path}'
    
    # Create AVRCP client
    avrcp_client = AVRCPClient(device_path)
    
    # Display what's playing
    if avrcp_client.is_available():
        track = avrcp_client.get_track_info()
        print(f"Playing: {track['title']}")

controller.on_device_connected = on_connected
controller.initialize()
```

## API Reference

### AVRCPClient Class

#### Constructor
```python
AVRCPClient(device_path: Optional[str] = None)
```
- `device_path`: D-Bus path to Bluetooth device (e.g., `/org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF`)

#### Methods

**Track Information**
```python
get_track_info() -> Optional[Dict[str, Any]]
```
Returns dictionary with:
- `title` (str): Track title
- `artist` (str): Artist name
- `album` (str): Album name
- `duration` (int): Duration in milliseconds
- `track_number` (int): Track number (optional)
- `total_tracks` (int): Total tracks (optional)

**Playback Status**
```python
get_status() -> Optional[str]
```
Returns: `'playing'`, `'paused'`, `'stopped'`, `'forward-seek'`, `'reverse-seek'`, or `None`

**Playback Position**
```python
get_position() -> Optional[int]
```
Returns: Position in milliseconds or `None`

**Playback Control**
```python
play() -> bool           # Start playback
pause() -> bool          # Pause playback
stop() -> bool           # Stop playback
next() -> bool           # Skip to next track
previous() -> bool       # Skip to previous track
fast_forward() -> bool   # Fast forward
rewind() -> bool         # Rewind
```
All return `True` if command was sent successfully.

**Availability**
```python
is_available() -> bool
```
Returns `True` if AVRCP media player is available for the device.

**Device Management**
```python
set_device(device_path: str)
```
Change the device being monitored.

```python
clear_cache()
```
Clear cached track info and status.

#### Callbacks

```python
on_track_changed: Optional[Callable[[Dict[str, Any]], None]]
```
Called when track changes. Receives track info dictionary.

```python
on_status_changed: Optional[Callable[[str], None]]
```
Called when playback status changes. Receives status string.

## Examples

### Example 1: Display Current Track

```python
from kitchenradio.bluetooth import AVRCPClient

# Connect to device
client = AVRCPClient('/org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF')

if client.is_available():
    track = client.get_track_info()
    status = client.get_status()
    
    print(f"Title:  {track['title']}")
    print(f"Artist: {track['artist']}")
    print(f"Album:  {track['album']}")
    print(f"Status: {status}")
    
    if 'duration' in track:
        duration_sec = track['duration'] / 1000
        print(f"Duration: {duration_sec:.1f}s")
```

### Example 2: Monitor Track Changes

```python
import dbus.mainloop.glib
from gi.repository import GLib
from kitchenradio.bluetooth import AVRCPClient

# Setup D-Bus main loop
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

client = AVRCPClient('/org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF')

def on_track_changed(track):
    print(f"\n🎵 Now playing:")
    print(f"   {track['title']}")
    print(f"   by {track['artist']}")

client.on_track_changed = on_track_changed

# Run event loop
mainloop = GLib.MainLoop()
mainloop.run()
```

### Example 3: Playback Control

```python
from kitchenradio.bluetooth import AVRCPClient
import time

client = AVRCPClient('/org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF')

# Pause for 3 seconds, then resume
client.pause()
time.sleep(3)
client.play()

# Skip to next track
time.sleep(5)
client.next()
```

## Testing

### Test with Real Device

1. **Pair and connect your device:**
```bash
bluetoothctl
pair AA:BB:CC:DD:EE:FF
connect AA:BB:CC:DD:EE:FF
```

2. **Start playing music** on your phone/device

3. **Run the test script:**
```bash
python3 -m kitchenradio.bluetooth.avrcp_client AA:BB:CC:DD:EE:FF
```

### Test with Example Integration

```bash
python3 example_avrcp_integration.py
```

Commands:
- `p` - Enter pairing mode
- `d` - Display current track
- `play` - Send play command
- `pause` - Send pause command
- `next` - Next track
- `prev` - Previous track

## Integration with KitchenRadio Display

To display Bluetooth track info on the OLED:

```python
# In bluetooth_controller.py or kitchen_radio.py

from kitchenradio.bluetooth import AVRCPClient

class BluetoothController:
    def __init__(self):
        self.avrcp_client = None
    
    def _on_bluetooth_connected(self, name: str, mac: str):
        # Create AVRCP client
        mac_path = mac.replace(':', '_')
        device_path = f'/org/bluez/hci0/dev_{mac_path}'
        self.avrcp_client = AVRCPClient(device_path)
        
        # Set up callback to update display
        def on_track_changed(track):
            # Update display with new track
            self.display_controller.show_track_info(
                title=track['title'],
                artist=track['artist'],
                album=track['album'],
                playing=True
            )
        
        self.avrcp_client.on_track_changed = on_track_changed
    
    def get_bluetooth_status(self):
        """Get status for display"""
        if not self.avrcp_client or not self.avrcp_client.is_available():
            return {
                'title': 'Bluetooth Audio',
                'artist': 'Ready for streaming',
                'playing': False
            }
        
        track = self.avrcp_client.get_track_info()
        status = self.avrcp_client.get_status()
        
        return {
            'title': track.get('title', 'Unknown') if track else 'Unknown',
            'artist': track.get('artist', 'Unknown') if track else 'Unknown',
            'album': track.get('album', '') if track else '',
            'playing': status == 'playing' if status else False
        }
```

## Troubleshooting

### AVRCP Not Available

If `is_available()` returns `False`:

1. **Make sure device is connected:**
```bash
bluetoothctl info AA:BB:CC:DD:EE:FF
```
Check that `Connected: yes`

2. **Start playing music** on the device - AVRCP media player appears when playback starts

3. **Check for media player:**
```bash
gdbus introspect --system --dest org.bluez --object-path /org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF
```
Look for `org.bluez.MediaPlayer1` interface

4. **Check BlueZ version:**
```bash
bluetoothd --version
```
AVRCP requires BlueZ 5.0 or later

### No Track Metadata

Some devices don't send all metadata. Check what's available:

```python
track = client.get_track_info()
print("Available fields:", list(track.keys()))
```

### Commands Not Working

1. **Check if device supports control:**
Not all devices accept control commands (some are source-only)

2. **Check device settings:**
Some phones require permission to allow remote control

3. **Enable debug logging:**
```python
import logging
logging.getLogger('kitchenradio.bluetooth').setLevel(logging.DEBUG)
```

## Requirements

- BlueZ 5.0 or later
- python3-dbus
- PyGObject (for GLib main loop)
- Connected Bluetooth device with A2DP and AVRCP support

## Related

- [BluetoothController](./bluetooth_controller.py) - Device pairing and connection
- [BLUETOOTH_DEBUG.md](../BLUETOOTH_DEBUG.md) - Debugging guide
- [monitor_bluetooth.py](../monitor_bluetooth.py) - Event monitoring tool
