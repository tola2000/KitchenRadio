# Bluetooth Integration for KitchenRadio

## Overview

Bluetooth has been integrated as a new audio source in KitchenRadio, allowing users to connect their phones or other Bluetooth devices for audio streaming.

## Features

- **Automatic Pairing**: When the Bluetooth source is selected without a connected device, the system enters pairing mode for 60 seconds
- **Auto-Switch on Connection**: When a Bluetooth device connects, KitchenRadio automatically switches to the Bluetooth source
- **Auto-Accept Pairing**: The system automatically accepts pairing requests without requiring confirmation on the Raspberry Pi
- **Device Trust**: Paired devices are trusted, allowing automatic reconnection in the future
- **Audio Profile Detection**: Waits for A2DP audio profile to establish before considering connection complete

## Architecture

### New Components

1. **`kitchenradio/bluetooth/bluetooth_controller.py`**
   - `BluetoothController`: Main controller class managing Bluetooth connections
   - `AutoPairAgent`: D-Bus agent that auto-accepts pairing requests
   - Runs in background thread with GLib main loop
   - Monitors D-Bus for device connection/disconnection events

2. **`kitchenradio/bluetooth/__init__.py`**
   - Package initialization exporting `BluetoothController`

### Updated Components

1. **`kitchenradio/radio/kitchen_radio.py`**
   - Added `BackendType.BLUETOOTH` to enum
   - Added `bluetooth_controller` and `bluetooth_connected` attributes
   - Added `_initialize_bluetooth()` method
   - Added callbacks: `_on_bluetooth_connected()` and `_on_bluetooth_disconnected()`
   - Updated `_set_source()` to handle Bluetooth source selection and pairing mode
   - Updated `_initialize_backends()` to include Bluetooth
   - Updated `stop()` to cleanup Bluetooth resources

2. **`kitchenradio/radio/hardware/button_controller.py`**
   - Added `ButtonType.SOURCE_BLUETOOTH` button type
   - Mapped button to pin 5 (was CD button)
   - Added `_select_bluetooth()` handler method

## How It Works

### Bluetooth Selection Flow

1. **User presses Bluetooth source button** → `button_controller._select_bluetooth()` called
2. **Set source to Bluetooth** → `kitchen_radio.set_source(BackendType.BLUETOOTH)` called
3. **Check connection status**:
   - If device already connected → Switch to Bluetooth source
   - If no device connected → Enter pairing mode for 60 seconds

### Pairing Mode

When pairing mode is activated:
1. Adapter becomes **discoverable** (visible to other devices)
2. **Auto-pair agent** is active (auto-accepts pairing requests)
3. System listens for devices trying to connect
4. When device pairs:
   - Device is automatically **trusted** (for auto-reconnect)
   - System waits 3 seconds for pairing to complete
   - System explicitly connects to device
   - Waits for **A2DP audio profile** to establish
   - Pairing mode exits

### Auto-Switch Behavior

- **When device connects**: If not already on Bluetooth source, auto-switches to it
- **When device disconnects**: If on Bluetooth source, switches back to MPD

## Hardware Configuration

### Button Mapping
- **Pin 5** (was CD button) → Bluetooth source button
- **Pin 6** → Spotify (AUX)
- **Pin 7** → MPD (TUNER)

You can modify the pin assignment in `BUTTON_PIN_MAP` in `button_controller.py`.

## Dependencies

The Bluetooth integration requires:
- `dbus-python>=1.2.0` - D-Bus communication with BlueZ
- `PyGObject>=3.42.0` - GLib main loop integration
- BlueZ - Linux Bluetooth stack (system package)
- PulseAudio with Bluetooth modules - Audio routing

Already added to `requirements.txt`.

## Usage

### Programmatic Control

```python
from kitchenradio.radio.kitchen_radio import KitchenRadio, BackendType

# Initialize KitchenRadio
radio = KitchenRadio()
radio.start()

# Switch to Bluetooth source (enters pairing mode if no device connected)
radio.set_source(BackendType.BLUETOOTH)

# Check if Bluetooth device is connected
if radio.bluetooth_controller and radio.bluetooth_controller.is_connected():
    device_name = radio.bluetooth_controller.get_connected_device_name()
    print(f"Connected to: {device_name}")

# Manually enter pairing mode
if radio.bluetooth_controller:
    radio.bluetooth_controller.enter_pairing_mode(timeout_seconds=120)

# Disconnect current device
if radio.bluetooth_controller:
    radio.bluetooth_controller.disconnect_current()
```

### Physical Button Control

1. **Press Bluetooth button** (pin 5) → Enters pairing mode if no device connected
2. **Pair device from phone/tablet** → Shows pairing code on phone, auto-accepts on Pi
3. **Device connects** → Audio plays through Raspberry Pi
4. **Press another source button** → Stops Bluetooth source, switches to that source

## Callbacks

The `BluetoothController` supports callbacks:

```python
def on_connected(name, mac):
    print(f"Device connected: {name} ({mac})")

def on_disconnected(name, mac):
    print(f"Device disconnected: {name} ({mac})")

def on_stream_started():
    print("Audio streaming started")

radio.bluetooth_controller.on_device_connected = on_connected
radio.bluetooth_controller.on_device_disconnected = on_disconnected
radio.bluetooth_controller.on_stream_started = on_stream_started
```

## Troubleshooting

### Pairing Code Shows But Doesn't Connect

**Cause**: Auto-pair agent may not be working
**Solution**: Check that agent is registered with `NoInputNoOutput` capability

### Device Connects But Disconnects After 30 Seconds

**Cause**: A2DP audio profile not establishing
**Solution**: 
- Ensure PulseAudio is running: `pulseaudio --start`
- Check Bluetooth modules: `pactl list modules | grep bluetooth`
- Load module if missing: `pactl load-module module-bluetooth-discover`

### Bluetooth Controller Fails to Initialize

**Cause**: D-Bus connection or BlueZ service issue
**Solution**:
- Check BlueZ service: `systemctl status bluetooth`
- Check adapter: `bluetoothctl show`
- Check Python packages: `pip list | grep -E "dbus|PyGObject"`

### No Audio When Connected

**Cause**: PulseAudio sink not configured
**Solution**: Run setup scripts from root directory to configure PulseAudio properly

## Technical Details

### D-Bus Interfaces Used

- `org.bluez.Adapter1` - Bluetooth adapter control (power, discoverable, pairable)
- `org.bluez.Device1` - Device management (pair, connect, trust)
- `org.bluez.Agent1` - Pairing agent (auto-accept)
- `org.bluez.AgentManager1` - Agent registration
- `org.freedesktop.DBus.Properties` - Property change monitoring
- `org.freedesktop.DBus.ObjectManager` - Device discovery

### A2DP UUIDs

The controller checks for these UUIDs to confirm audio profile:
- `0000110b-0000-1000-8000-00805f9b34fb` - A2DP Audio Sink
- `0000110a-0000-1000-8000-00805f9b34fb` - A2DP Audio Source

### Threading

The `BluetoothController` runs in a background daemon thread with its own GLib main loop. This keeps D-Bus event processing separate from the main KitchenRadio thread.

## Testing

Test the integration with these scenarios:

1. **Fresh Pairing**
   ```bash
   # Remove all paired devices
   bluetoothctl devices | cut -d' ' -f2 | xargs -I {} bluetoothctl remove {}
   
   # Start KitchenRadio and press Bluetooth button
   # Pair from phone
   ```

2. **Reconnection**
   ```bash
   # With previously paired device:
   # Turn off Bluetooth on phone
   # Press Bluetooth button on radio
   # Turn on Bluetooth on phone → Should auto-reconnect
   ```

3. **Source Switching**
   ```bash
   # With Bluetooth connected:
   # Press MPD button → Should disconnect Bluetooth and play MPD
   # Press Bluetooth button → Should reconnect to device
   ```

## Future Enhancements

Possible improvements:
- [ ] Multiple device support (device selection menu)
- [ ] Display device battery level
- [ ] Show pairing code on KitchenRadio display
- [ ] Bluetooth audio quality settings (codec selection)
- [ ] Integration with Bluetooth media control (AVRCP profile)
- [ ] Auto-detect when audio streaming starts (integrate `detect_bluez_stream.py`)
