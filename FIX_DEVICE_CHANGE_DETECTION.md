# Display Controller Device Change Detection - Fix

## Problem Identified

The DisplayController was **not detecting Bluetooth device changes** when the source remained the same. 

### Scenario:
- User has Bluetooth as active source
- Device connects (MAC address set)
- Device disconnects (MAC address cleared to "")
- **Source stays "bluetooth"** throughout
- Display should update to show "Verbind Apparaat" but didn't

### Root Causes:

1. **No device_mac comparison in `_on_client_changed`**:
   - Only checked if source TYPE changed (mpd → bluetooth)
   - Didn't check if device changed WITHIN same source

2. **Missing source_info in status change detection**:
   - `_update_display` only compared: current_source, playback_state, track_info
   - **Never compared source_info** (which contains device_mac, device_name, etc.)
   - When device disconnected, source_info changed but status_changed stayed False

## Fixes Applied

### Fix 1: Added Device Change Detection in `_on_client_changed`

**File**: `display_controller.py` (lines ~187-206)

Added detection for device changes within the same source:

```python
# Check if device changed (within same source - important for Bluetooth)
old_device_mac = self.cached_source_info.device_mac if hasattr(self.cached_source_info, 'device_mac') else None
new_device_mac = new_source_info.device_mac if hasattr(new_source_info, 'device_mac') else None
if old_device_mac != new_device_mac:
    device_changed = True
    logger.info(f"🔵 Device changed in display: {old_device_name} (MAC:{old_device_mac or 'none'}) → {new_device_name} (MAC:{new_device_mac or 'none'})")
```

**Result**: Now logs when device connects/disconnects even if source stays the same.

### Fix 2: Refresh Display Cache on Device Change

**File**: `display_controller.py` (lines ~208-226)

Changed condition to refresh on EITHER source OR device change:

```python
# If source OR device changed, fetch fresh state from SourceController
if (source_changed or device_changed) and self.source_controller:
    if source_changed:
        logger.info("🔄 Refreshing display cache for new source...")
    elif device_changed:
        logger.info("🔵 Refreshing display cache for device change...")
    # ... refresh cache ...
```

**Result**: Display cache refreshes when device connects/disconnects.

### Fix 3: Added source_info to Status Change Detection

**File**: `display_controller.py` (lines ~488-501)

Added source_info comparison to detect status changes:

```python
elif current_status.get('source_info') != self.last_status.get('source_info'):
    status_changed = True
    logger.info(f"🔵 Source info changed (device connect/disconnect or source details)")
```

**Result**: Display re-renders when source_info changes (device connect/disconnect, device name change, etc.).

## What This Fixes

### Before:
```
1. 🔴 Device disconnected: IPhone Tola (10:2F:CA:87:66:7A)
2. 🔵 Bluetooth monitor event received: source_info_changed
3. 🔵 MONITOR EVENT RECEIVED: source=bluetooth, event=source_info_changed
4. ✅ FORWARDING bluetooth event 'source_info_changed'
5. 📤 Emitting callback: client_changed/source_info_changed
6. 📺 DisplayController received callback: event_type=client_changed, sub_event=source_info_changed
7. ❌ No refresh - source type didn't change (still bluetooth)
8. ❌ No re-render - source_info not checked in status_changed
9. ❌ Display shows old device name / wrong screen
```

### After:
```
1. 🔴 Device disconnected: IPhone Tola (10:2F:CA:87:66:7A)
2. 🔵 Bluetooth monitor event received: source_info_changed
3. 🔵 MONITOR EVENT RECEIVED: source=bluetooth, event=source_info_changed
4. ✅ FORWARDING bluetooth event 'source_info_changed'
5. 📤 Emitting callback: client_changed/source_info_changed
6. 📺 DisplayController received callback: event_type=client_changed, sub_event=source_info_changed
7. ✅ Device changed detected: IPhone Tola (MAC:10:2F:...) → Bluetooth (MAC:none)
8. ✅ Refreshing display cache for device change
9. ✅ Source info changed detected in status comparison
10. ✅ Display re-renders to show "BT Actief / Verbind Apparaat"
```

## Expected Log Output

When device disconnects, you should now see:

```
🔵 Device changed in display: IPhone Tola (MAC:10:2F:CA:87:66:7A) → Bluetooth (MAC:none)
🔵 Refreshing display cache for device change...
✅ Display cache refreshed - Status: stopped, Track: None
🔵 Source info changed (device connect/disconnect or source details)
Rendering Bluetooth display after status/power change
```

## Testing

1. **Restart KitchenRadio** to load the fixed code
2. **Connect a Bluetooth device** - should show device name and "Ready for streaming"
3. **Disconnect the device** - should immediately show "BT Actief / Verbind Apparaat"
4. **Check logs** for the 🔵 emoji markers showing device change detection

## Benefits

- ✅ Display now updates correctly when Bluetooth device connects/disconnects
- ✅ Works for any source_info changes (device name, MAC address, path, etc.)
- ✅ Clear logging with 🔵 emoji for easy debugging
- ✅ Maintains backward compatibility with existing source change logic
- ✅ Fixes the exact issue reported by user

## Related Files

- `kitchenradio/interfaces/hardware/display_controller.py` - Main fix location
- `kitchenradio/sources/bluetooth/monitor.py` - Emits source_info_changed events
- `kitchenradio/sources/source_controller.py` - Forwards events to display
