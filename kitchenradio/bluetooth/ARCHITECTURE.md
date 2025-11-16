# Bluetooth Module Architecture

## Overview
The Bluetooth module provides comprehensive Bluetooth audio support for KitchenRadio with:
- Device pairing and connection management
- AVRCP media control (track info, playback control)
- PulseAudio volume integration
- Clean separation between low-level BlueZ communication and high-level control

## Module Structure

The module follows the same pattern as MPD and Librespot with clear separation of concerns:

```
kitchenradio/bluetooth/
├── model.py           # Data models (TrackInfo, PlaybackStatus, AVRCPState)
├── bluez_client.py    # Low-level BlueZ D-Bus client
├── avrcp_client.py    # AVRCP media control client
├── controller.py      # High-level Bluetooth controller
├── test_model.py      # Unit tests
└── __init__.py        # Package exports
```

### 1. `model.py` - Data Models
Pure data structures with no external dependencies.

**Classes:**
- `PlaybackStatus` (Enum): Status values (PLAYING, PAUSED, STOPPED, etc.)
- `TrackInfo`: Track metadata (title, artist, album, duration)
- `PlaybackState`: Playback state (status, position, track, timing)
- `AVRCPState`: Complete device state

**Features:**
- Type-safe data representation
- JSON serialization (`to_dict()`, `from_dict()`)
- No I/O or external dependencies
- Easy to test and reuse

### 2. `bluez_client.py` - BlueZ D-Bus Client
Low-level interface to BlueZ Bluetooth stack via D-Bus.

**Responsibilities:**
- D-Bus connection management
- Adapter control (power, discovery, pairing)
- Device operations (pair, connect, disconnect, trust)
- Property monitoring
- Auto-pairing agent registration

**Key Methods:**
```python
# Adapter management
set_adapter_property(property, value)
get_adapter_property(property)

# Device operations
connect_device(device_path)
disconnect_device(device_path)
pair_device(device_path)
remove_device(device_path)

# Device properties
get_device_properties(device_path)
set_device_property(device_path, property, value)

# Discovery
start_discovery()
stop_discovery()

# Object management
get_managed_objects()

# Agent
register_agent()
unregister_agent()
```

**Callbacks:**
- `on_properties_changed(interface, changed, invalidated, path)` - D-Bus property changes

**Design Philosophy:**
- Pure D-Bus operations
- No business logic
- No PulseAudio interaction
- Thin wrapper around BlueZ API

### 3. `avrcp_client.py` - AVRCP Client
AVRCP media control via BlueZ MediaPlayer1 interface.

**Responsibilities:**
- Find MediaPlayer1 objects for devices
- Get track metadata
- Get playback status and position
- Send control commands (play, pause, next, previous)
- Monitor property changes
- Maintain state using `AVRCPState` model

**Key Methods:**
```python
# Setup
set_device(device_path, device_name, device_mac)

# Track info
get_track_info() → TrackInfo
get_status() → PlaybackStatus
get_position() → int
get_state() → AVRCPState

# Playback control
play(), pause(), stop()
next(), previous()
fast_forward(), rewind()

# State management
clear_cache()
is_available()
```

**Callbacks:**
- `on_track_changed(TrackInfo)` - Track metadata changed
- `on_status_changed(PlaybackStatus)` - Playback status changed
- `on_state_changed(AVRCPState)` - Complete state changed

**Design Philosophy:**
- Uses BlueZ MediaPlayer1 interface
- Maintains centralized state model
- Type-safe callbacks
- Separate from device connection management

### 4. `controller.py` - Bluetooth Controller
High-level Bluetooth audio management.

**Responsibilities:**
- Device connection lifecycle
- Pairing mode management
- PulseAudio volume control
- Device state tracking
- Callback coordination

**Key Methods:**
```python
# Pairing
enter_pairing_mode(timeout_seconds)
exit_pairing_mode()

# Connection
disconnect_current()
is_connected()
get_connected_device_name()
list_paired_devices()

# Volume (PulseAudio)
get_volume()
set_volume(volume)
volume_up(step), volume_down(step)
refresh_volume()

# Lifecycle
cleanup()
```

**Callbacks:**
- `on_device_connected(name, mac)` - Device connected
- `on_device_disconnected(name, mac)` - Device disconnected
- `on_stream_started()` - Audio stream ready

**Design Philosophy:**
- Uses `BlueZClient` for all D-Bus operations
- Manages PulseAudio integration
- Coordinates state across BlueZ and PulseAudio
- Business logic layer

## Architecture Pattern

### Comparison with Other Modules

#### MPD Module:
```
mpd/
├── client.py          # MPD protocol client
├── controller.py      # High-level control
├── monitor.py         # Status monitoring
└── __init__.py
```

#### Librespot Module:
```
librespot/
├── client.py          # go-librespot API client
├── controller.py      # High-level control
├── monitor.py         # Status monitoring
└── __init__.py
```

#### Bluetooth Module (NEW):
```
bluetooth/
├── model.py           # Data models
├── bluez_client.py    # BlueZ D-Bus client
├── avrcp_client.py    # AVRCP media control
├── controller.py      # High-level control
└── __init__.py
```

### Design Principles

1. **Separation of Concerns**
   - Model: Data only
   - Client: Protocol communication
   - Controller: Business logic

2. **Type Safety**
   - Dataclasses for structured data
   - Enums for known values
   - Proper type hints

3. **Testability**
   - Models have no dependencies
   - Clients can be mocked
   - Clear boundaries

4. **Maintainability**
   - Each file has single responsibility
   - Easy to locate functionality
   - Consistent with other modules

## Usage Examples

### Basic Controller Usage

```python
from kitchenradio.bluetooth import BluetoothController

# Create controller
bt = BluetoothController()

# Set up callbacks
def on_connected(name, mac):
    print(f"Connected: {name}")

bt.on_device_connected = on_connected

# Enter pairing mode
bt.enter_pairing_mode(timeout_seconds=60)

# Control volume
bt.set_volume(75)
bt.volume_up(5)

# Cleanup
bt.cleanup()
```

### AVRCP Media Control

```python
from kitchenradio.bluetooth import AVRCPClient, PlaybackStatus

# Create AVRCP client
device_path = '/org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF'
avrcp = AVRCPClient(device_path, "My Phone", "AA:BB:CC:DD:EE:FF")

# Set up callbacks
def on_track_changed(track):
    print(f"Now playing: {track.title} by {track.artist}")

avrcp.on_track_changed = on_track_changed

# Get track info
track = avrcp.get_track_info()
if track:
    print(f"{track.title} - {track.artist}")
    print(f"Duration: {track.get_duration_formatted()}")

# Control playback
status = avrcp.get_status()
if status == PlaybackStatus.PLAYING:
    avrcp.pause()
else:
    avrcp.play()

# Get complete state
state = avrcp.get_state()
print(state.get_status_summary())
```

### Advanced: Direct BlueZ Client Usage

```python
from kitchenradio.bluetooth import BlueZClient

# Create BlueZ client
client = BlueZClient('/org/bluez/hci0')

# Register agent
client.register_agent()

# Set up property monitoring
def on_props_changed(interface, changed, invalidated, path):
    print(f"Property changed: {changed}")

client.on_properties_changed = on_props_changed

# Adapter control
client.set_adapter_property('Powered', True)
client.set_adapter_property('Discoverable', True)

# Device operations
device_path = '/org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF'
client.connect_device(device_path)
client.set_device_property(device_path, 'Trusted', True)

# Get device info
props = client.get_device_properties(device_path)
print(f"Device: {props['Name']} - {props['Connected']}")
```

### Integrated Usage

```python
from kitchenradio.bluetooth import BluetoothController, AVRCPClient

# Create controller
bt = BluetoothController()

# Wait for connection
# ... device connects ...

# Create AVRCP client for connected device
if bt.current_device_path:
    avrcp = AVRCPClient(
        bt.current_device_path,
        bt.current_device_name,
        list(bt.connected_devices)[0]
    )
    
    # Use both together
    bt.set_volume(50)  # PulseAudio volume
    avrcp.next()       # Skip track via AVRCP
```

## Benefits of Refactored Architecture

### 1. **Modularity**
- BlueZ client can be used standalone
- AVRCP client is independent
- Controller coordinates both

### 2. **Testability**
- Mock BlueZClient for controller tests
- Test AVRCP client with mock D-Bus
- Models test without any dependencies

### 3. **Reusability**
- BlueZClient useful for any BlueZ application
- AVRCP client reusable across projects
- Models can be serialized/deserialized

### 4. **Maintainability**
- Clear file boundaries
- Easy to locate bugs
- Simple to add features

### 5. **Consistency**
- Matches MPD/Librespot pattern
- Familiar to developers
- Predictable structure

## Integration with KitchenRadio

The Bluetooth module integrates with the main KitchenRadio daemon:

```python
# In kitchen_radio.py
from kitchenradio.bluetooth import BluetoothController, AVRCPClient

class KitchenRadio:
    def __init__(self):
        # Create Bluetooth controller
        self.bluetooth_controller = BluetoothController()
        self.bluetooth_controller.on_device_connected = self._on_bluetooth_connected
        self.bluetooth_controller.on_device_disconnected = self._on_bluetooth_disconnected
        
        # AVRCP client (created on connection)
        self.avrcp_client = None
    
    def _on_bluetooth_connected(self, name, mac):
        # Create AVRCP client
        device_path = self.bluetooth_controller.current_device_path
        self.avrcp_client = AVRCPClient(device_path, name, mac)
        self.avrcp_client.on_track_changed = self._on_bluetooth_track_changed
        
        # Switch to Bluetooth source
        self.set_source('bluetooth')
    
    def _on_bluetooth_disconnected(self, name, mac):
        self.avrcp_client = None
        # Switch away from Bluetooth
        self.set_source('mpd')
```

## Migration from Old Structure

### Before:
- All BlueZ logic in `controller.py`
- ~700 lines in single file
- D-Bus calls mixed with business logic
- Hard to test
- Hard to reuse

### After:
- `bluez_client.py`: ~450 lines of pure D-Bus operations
- `controller.py`: ~450 lines of business logic
- Clear separation
- Easy to test each component
- Reusable BlueZ client
- Consistent with project structure

### Breaking Changes:
**None!** The public API remains identical:
```python
# These still work exactly the same
from kitchenradio.bluetooth import BluetoothController
bt = BluetoothController()
bt.enter_pairing_mode(60)
bt.set_volume(75)
```

The refactoring is purely internal organization.

## Future Enhancements

### Potential Additions:
1. **`monitor.py`**: Background monitoring like MPD/Librespot
2. **Multiple Devices**: Support simultaneous connections
3. **Advanced Metadata**: Album art, lyrics, ratings
4. **AVRCP Volume**: Control device volume (separate from PulseAudio)
5. **Battery Status**: Monitor device battery levels
6. **Profile Management**: A2DP, HFP, HSP profile control

### Integration Opportunities:
- Hardware button integration for AVRCP controls
- Web UI for AVRCP metadata display
- Display controller integration
- State persistence across restarts
