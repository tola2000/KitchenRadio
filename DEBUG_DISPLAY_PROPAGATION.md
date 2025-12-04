# Display Controller Event Propagation Debug Guide

## What Was Added

Debug logging has been added to **both** SourceController and DisplayController to trace Bluetooth event propagation from source → display.

## Debug Output to Look For

### 1. SourceController Receives Bluetooth Event
```
🔵 Bluetooth monitor event received: <event_name>, kwargs: [<keys>]
🔵 MONITOR EVENT RECEIVED: source=bluetooth, event=<event_name>, active_source=bluetooth, kwargs_keys=[...]
```

### 2. SourceController Forwards Event
```
✅ FORWARDING bluetooth event '<event_name>' to client_changed callbacks (active source matches)
```

### 3. SourceController Emits Callback
```
📤 Emitting callback: client_changed/<event_name>, 2 registered callbacks
  → Calling specific callback with sub_event=<event_name>
```

### 4. **NEW** - DisplayController Receives Callback
```
📺 DisplayController received callback: event_type=client_changed, sub_event=<event_name>, kwargs_keys=[...]
```

### 5. DisplayController Processes Event
```
Display cache updated: playback_state = ...
📀 Display cache updated: track_info = <Title>
🔄 Source changed in display: <old_source> → <new_source>
```

## Complete Event Flow for Bluetooth Disconnect

Expected log sequence:

```
1. 🔴 Device disconnected: IPhone Tola (10:2F:CA:87:66:7A)
2. 🔵 Bluetooth monitor event received: source_info_changed, kwargs: ['source_info']
3. 🔵 MONITOR EVENT RECEIVED: source=bluetooth, event=source_info_changed, ...
4. ✅ FORWARDING bluetooth event 'source_info_changed' to client_changed callbacks
5. 📤 Emitting callback: client_changed/source_info_changed, 2 registered callbacks
6. 📺 DisplayController received callback: event_type=client_changed, sub_event=source_info_changed, kwargs_keys=[...]
7. Display cache updated: source_info = ...
```

## What We're Testing

The question is: **Does step 6 appear in the logs?**

- ✅ **If YES**: DisplayController IS receiving events from SourceController
  - Then check if it's processing them correctly (step 7)
  - Look for "Display cache updated" or "Rendering Bluetooth display" messages

- ❌ **If NO**: DisplayController is NOT receiving events
  - Check if callback is properly registered: look for "Registered display callback with SourceController"
  - Verify 'any' callback count: should show "2 registered callbacks" in step 5
  - Check if callback registration happens before events start firing

## Key Questions to Answer

1. **Are events reaching DisplayController?**
   - Look for `📺 DisplayController received callback` messages

2. **What parameters is DisplayController receiving?**
   - Check the `kwargs_keys` in the DisplayController debug log
   - Should include: `event_type`, `sub_event`, and event-specific keys like `source_info`, `track_info`, etc.

3. **Is DisplayController processing the events?**
   - After `📺` log, should see cache updates or rendering messages
   - If not, there may be an issue in the `_on_client_changed` method logic

## How to Test

1. **Restart KitchenRadio** to load the debug-enabled code
2. **Connect a Bluetooth device** and play music
3. **Disconnect the device** or switch tracks
4. **Check logs** for the complete event flow above

## Common Issues

### Issue: DisplayController receives events but doesn't process them
**Symptom**: See step 6 (`📺`) but not step 7 (cache updates)
**Cause**: `_on_client_changed` method may not be handling the event parameters correctly
**Fix**: Check if method is looking for the right kwargs (e.g., `source_info`, `track_info`)

### Issue: DisplayController doesn't receive events at all
**Symptom**: See steps 1-5 but never step 6
**Cause**: Callback not registered or registered to wrong event
**Fix**: Verify `add_callback('any', self._on_client_changed)` is called during initialization

### Issue: Events arrive but display doesn't update
**Symptom**: See steps 6-7 but display shows old info
**Cause**: Display rendering thread may not be triggered or _wake_event not working
**Fix**: Check if `self._wake_event.set()` is called in `_on_client_changed`

## Next Steps After Debugging

Once we confirm whether DisplayController is receiving events (step 6), we can:

1. **If receiving**: Focus on fixing event processing logic
2. **If NOT receiving**: Focus on callback registration timing or event routing
3. **Disable debug** once issue is identified and fixed
