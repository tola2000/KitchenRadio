# Bluetooth Pairing Mode Display Feature

## Summary

Added `pairing_mode` parameter to `SourceInfo` to indicate when Bluetooth is in discoverable/pairing mode, allowing the display controller to show a dedicated pairing screen.

## Changes Made

### 1. Added `pairing_mode` to SourceInfo Model

**File**: `kitchenradio/sources/source_model.py`

```python
@dataclass
class SourceInfo:
    source: SourceType = SourceType.NONE
    device_name: str = "Unknown"
    device_mac: str = ""
    path: str = ""
    power: bool = False
    pairing_mode: bool = False  # ✨ NEW: True when Bluetooth is in pairing/discoverable mode
```

**Benefit**: Centralized pairing state in the source info model, consistent with event-driven architecture.

### 2. Updated BluetoothMonitor

**File**: `kitchenradio/sources/bluetooth/monitor.py`

#### Added Controller Reference
- Monitor now accepts `controller` parameter in `__init__`
- Allows monitor to access controller's `pairing_mode` state

#### New Method: `update_pairing_mode()`
```python
def update_pairing_mode(self, pairing_mode: bool):
    """
    Update pairing mode status and trigger source_info_changed event.
    
    Args:
        pairing_mode: True when entering pairing mode, False when exiting
    """
    old_pairing = self.current_source_info.pairing_mode
    self.current_source_info.pairing_mode = pairing_mode
    
    if old_pairing != pairing_mode:
        logger.info(f"📡 Pairing mode changed: {old_pairing} → {pairing_mode}")
        self._trigger_callbacks('source_info_changed', source_info=self.current_source_info)
```

**Benefit**: Triggers display update immediately when pairing mode changes.

#### Updated `get_source_info()`
- Now updates `pairing_mode` from controller before returning
- Ensures fresh state even for polling queries

### 3. Updated BluetoothController

**File**: `kitchenradio/sources/bluetooth/controller.py`

#### Pass Controller to Monitor
```python
# Initialize monitor with controller reference for pairing_mode status
self.monitor = BluetoothMonitor(self.client, controller=self)
```

#### Notify Monitor on Pairing Mode Change
**In `enter_pairing_mode()`**:
```python
# Notify monitor to update source_info and trigger display update
if self.monitor:
    self.monitor.update_pairing_mode(True)
```

**In `exit_pairing_mode()`**:
```python
# Notify monitor to update source_info and trigger display update
if self.monitor:
    self.monitor.update_pairing_mode(False)
```

**Benefit**: Display updates automatically when entering/exiting pairing mode via event system.

### 4. Updated DisplayController

**File**: `kitchenradio/interfaces/hardware/display_controller.py`

#### Read pairing_mode from source_info
```python
# Check if we have a connected device
if isinstance(source_info, SourceInfo):
    device_name = source_info.device_name
    device_mac = source_info.device_mac
    pairing_mode = source_info.pairing_mode  # ✨ NEW
else:
    device_name = source_info.get('device_name', 'Unknown')
    device_mac = source_info.get('device_mac', '')
    pairing_mode = source_info.get('pairing_mode', False)  # ✨ NEW
    
is_connected = device_mac != ''

# Use pairing_mode from source_info (more reliable than polling controller state)
is_discoverable = pairing_mode
```

**Benefit**: 
- Uses event-driven approach (source_info) instead of polling controller
- Consistent with overall architecture
- More reliable and responsive

## Event Flow

### Entering Pairing Mode:

```
1. User presses Bluetooth button while on Bluetooth (no device connected)
2. SourceController.set_source() detects second BT press → calls controller.enter_pairing_mode()
3. BluetoothController.enter_pairing_mode():
   - Sets self.pairing_mode = True
   - Calls self.monitor.update_pairing_mode(True)
4. BluetoothMonitor.update_pairing_mode():
   - Updates current_source_info.pairing_mode = True
   - Triggers 'source_info_changed' callback
5. SourceController receives event → forwards to DisplayController
6. DisplayController._on_client_changed():
   - Detects source_info changed
   - Refreshes cache
7. DisplayController._render_bluetooth_display():
   - Checks source_info.pairing_mode == True
   - Shows: "Koppelen Actief / Koppel Nieuw Apperaat"
```

### Exiting Pairing Mode:

```
1. Device connects OR timeout expires OR source changes
2. BluetoothController.exit_pairing_mode():
   - Sets self.pairing_mode = False
   - Calls self.monitor.update_pairing_mode(False)
3. BluetoothMonitor.update_pairing_mode():
   - Updates current_source_info.pairing_mode = False
   - Triggers 'source_info_changed' callback
4. SourceController → DisplayController (same as above)
5. DisplayController shows normal screen based on connection state
```

## Expected Log Output

### Entering Pairing Mode:
```
🔵 ENTERING PAIRING MODE
   Ready to pair - stays active until source changes
👁️  Bluetooth is now DISCOVERABLE
📱 Pair your device now!
📡 Pairing mode changed: False → True
🔵 Device changed in display: Bluetooth (MAC:none) → Bluetooth (MAC:none)
🔵 Refreshing display cache for device change...
[BluetoothDisplay] pairing_mode=True, connected=False, device=Bluetooth
Rendering Bluetooth display after status/power change
```

### Exiting Pairing Mode (Device Connects):
```
🟢 Device connected: IPhone Tola (10:2F:CA:87:66:7A)
📡 BlueZ monitoring for AVRCP MediaPlayer...
📡 Pairing mode changed: True → False
🔵 Device changed in display: Bluetooth (MAC:none) → IPhone Tola (MAC:10:2F:...)
[BluetoothDisplay] pairing_mode=False, connected=True, device=IPhone Tola
Rendering Bluetooth display after status/power change
```

## Display Screens

### Pairing Mode (No Device):
```
┌──────────────────────┐
│  Koppelen Actief     │
│  Koppel Nieuw        │
│  Apperaat            │
│                      │
│  [Volume Bar Dimmed] │
└──────────────────────┘
```

### Pairing Mode (Device Already Connected):
```
┌──────────────────────┐
│  IPhone Tola         │
│  Bluetooth Connected │
│  MAC: 10:2F:CA:...   │
│                      │
│  [Volume Bar Active] │
└──────────────────────┘
```

### Normal Mode (No Device):
```
┌──────────────────────┐
│  BT Actief           │
│  Verbind Apparaat    │
│                      │
│                      │
│  [Volume Bar Dimmed] │
└──────────────────────┘
```

## Benefits

✅ **Event-Driven**: Pairing mode changes trigger immediate display updates
✅ **Consistent Architecture**: Uses same event flow as device connect/disconnect
✅ **Reliable**: No polling required - state is pushed to display
✅ **Clear User Feedback**: Dedicated pairing screen shows when system is discoverable
✅ **Centralized State**: pairing_mode is part of SourceInfo, easy to access anywhere

## Testing

1. **Start with Bluetooth source, no device connected**
   - Should show "BT Actief / Verbind Apparaat"

2. **Press Bluetooth button again**
   - Should show "Koppelen Actief / Koppel Nieuw Apperaat"
   - Bluetooth should be discoverable on phone

3. **Connect a device while in pairing mode**
   - Should exit pairing mode automatically
   - Should show device name and "Ready for streaming"

4. **Disconnect device and press Bluetooth button**
   - Should re-enter pairing mode
   - Should show pairing screen again

5. **Switch to different source while in pairing mode**
   - Should exit pairing mode automatically
   - Should stop being discoverable

## Related Files

- `kitchenradio/sources/source_model.py` - Added pairing_mode to SourceInfo
- `kitchenradio/sources/bluetooth/monitor.py` - Added update_pairing_mode() method
- `kitchenradio/sources/bluetooth/controller.py` - Calls monitor.update_pairing_mode()
- `kitchenradio/interfaces/hardware/display_controller.py` - Reads pairing_mode from source_info
