# Bluetooth Event Handling Refactoring

## Summary
Refactored the `SourceController` to handle Bluetooth events through the unified `client_changed` callback system, matching the pattern used for Spotify (Librespot) and MPD sources.

## Changes Made

### 1. Simplified `_handle_monitor_event()` Method
**Location**: `kitchenradio/sources/source_controller.py`

**Before:**
- Had special handling for Bluetooth events
- Tried to call bluetooth-specific callbacks from a dict (`self._callbacks['bluetooth']`)
- Duplicated event forwarding logic

**After:**
- Unified event forwarding for all sources (MPD, Spotify, Bluetooth)
- All events go through `client_changed` callback with sub-event name
- Cleaner, more maintainable code

### 2. Updated `start_monitoring()` Method
**Location**: `kitchenradio/sources/source_controller.py`

**Before:**
```python
if bluetooth_callbacks:
    if 'bluetooth' not in self._callbacks:
        self._callbacks['bluetooth'] = {}
    if isinstance(self._callbacks['bluetooth'], dict):
        self._callbacks['bluetooth'].update(bluetooth_callbacks)
```

**After:**
```python
if bluetooth_callbacks:
    # DEPRECATED: bluetooth_callbacks dict is now handled through unified client_changed callback
    self.logger.warning("bluetooth_callbacks dict parameter is deprecated. Use on_client_changed instead.")
    
    # Map old bluetooth callback names to new unified system
    if isinstance(bluetooth_callbacks, dict):
        for event_name, callback in bluetooth_callbacks.items():
            if callback:
                # Register as client_changed callback
                self.add_callback('client_changed', callback)
```

## Benefits

1. **Consistency**: All sources (MPD, Spotify, Bluetooth) now use the same event handling pattern
2. **Simplified Code**: Removed special-case handling for Bluetooth
3. **Better Maintainability**: Single unified callback system is easier to understand and maintain
4. **Backward Compatibility**: Old `bluetooth_callbacks` dict parameter still works but logs deprecation warning

## Event Flow

### Before:
```
Bluetooth Monitor → _handle_monitor_event() → Special Bluetooth dict callbacks
                                             → client_changed callbacks
```

### After:
```
Bluetooth Monitor → _handle_monitor_event() → client_changed callbacks (only)
MPD Monitor       ↗
Spotify Monitor   ↗
```

## Migration Guide

If you were using the `bluetooth_callbacks` parameter:

**Old way (deprecated):**
```python
bluetooth_callbacks = {
    'track_changed': my_track_handler,
    'status_changed': my_status_handler,
}
source_controller.start_monitoring(bluetooth_callbacks=bluetooth_callbacks)
```

**New way (recommended):**
```python
def my_unified_handler(event, **kwargs):
    if event == 'track_changed':
        track_info = kwargs.get('track_info')
        # Handle track change
    elif event == 'playback_state_changed':
        playback_state = kwargs.get('playback_state')
        # Handle status change

source_controller.start_monitoring(on_client_changed=my_unified_handler)
```

## Testing Recommendations

1. Test Bluetooth device connection/disconnection
2. Verify track change events are received
3. Verify playback status change events are received
4. Confirm auto-switching to Bluetooth still works when device connects
5. Ensure display updates correctly for all Bluetooth states

## Related Files
- `kitchenradio/sources/source_controller.py` - Main refactored file
- `kitchenradio/sources/bluetooth/monitor.py` - Bluetooth monitor (unchanged, already used unified pattern)
- `kitchenradio/sources/mediaplayer/monitor.py` - MPD monitor (reference pattern)
- `kitchenradio/sources/spotify/monitor.py` - Spotify monitor (reference pattern)
