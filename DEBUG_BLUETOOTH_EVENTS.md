# Debug Logging for Bluetooth Events - Quick Reference

## What Was Enabled

Debug logging has been enabled in `source_controller.py` to trace Bluetooth event flow through the system.

## Debug Output to Look For

### 1. When Bluetooth Monitor Starts
```
✅ Bluetooth monitoring started - callback registered for 'any' event
```

### 2. When Bluetooth Monitor Emits an Event
```
🔵 Bluetooth monitor event received: <event_name>, kwargs: [<list_of_kwargs>]
```

### 3. When SourceController Receives Event
```
🔵 MONITOR EVENT RECEIVED: source=bluetooth, event=<event_name>, active_source=<current_source>, kwargs_keys=[<keys>]
```

### 4. Device Connection Detection
```
🔵 Bluetooth device_connected event detected
```

### 5. Auto-Switch Logic
```
🔵 Auto-switching to Bluetooth (device connected)
```
OR
```
🔵 Already on Bluetooth source, no switch needed
```

### 6. Event Forwarding Decision
**If Bluetooth is active source:**
```
✅ FORWARDING bluetooth event '<event_name>' to client_changed callbacks (active source matches)
```

**If Bluetooth is NOT active source:**
```
⏸️ NOT forwarding bluetooth event '<event_name>' (not active source: current=<source>)
```

### 7. Callback Emission
```
📤 Emitting callback: client_changed/<event_name>, <N> registered callbacks
  → Calling specific callback with sub_event=<event_name>
```

## Common Bluetooth Events to Watch For

- `device_connected` - Device pairs/connects
- `device_disconnected` - Device disconnects
- `track_changed` - New track starts playing
- `playback_state_changed` - Play/pause/stop status changes
- `source_info_changed` - Source information updated

## How to Use This

1. **Restart the KitchenRadio service** to load the debug-enabled code
2. **Connect a Bluetooth device** and watch the logs
3. **Play music** from the Bluetooth device
4. **Look for the emoji markers** (🔵 for Bluetooth events)

## Expected Event Flow for Device Connection

```
1. 🔵 Bluetooth monitor event received: device_connected, kwargs: [...]
2. 🔵 MONITOR EVENT RECEIVED: source=bluetooth, event=device_connected, ...
3. 🔵 Bluetooth device_connected event detected
4. 🔵 Auto-switching to Bluetooth (device connected)
5. ✅ FORWARDING bluetooth event 'device_connected' to client_changed callbacks
6. 📤 Emitting callback: client_changed/device_connected, X registered callbacks
```

## Expected Event Flow for Track Change

```
1. 🔵 Bluetooth monitor event received: track_changed, kwargs: [track_info]
2. 🔵 MONITOR EVENT RECEIVED: source=bluetooth, event=track_changed, ...
3. ✅ FORWARDING bluetooth event 'track_changed' to client_changed callbacks
4. 📤 Emitting callback: client_changed/track_changed, X registered callbacks
```

## Troubleshooting

### If you don't see ANY Bluetooth events:
- Check if Bluetooth monitor is started (look for "✅ Bluetooth monitoring started")
- Verify BlueZ is running: `systemctl status bluetooth`
- Check Bluetooth monitor logs for errors

### If events are received but NOT forwarded:
- Look for "⏸️ NOT forwarding" messages
- Check current active source (should be "bluetooth")
- Verify auto-switch logic is working

### If events are forwarded but callbacks aren't called:
- Look for "📤 Emitting callback" with 0 registered callbacks
- Check if display_controller registered its callback properly
- Verify callback registration in start_monitoring()

## Disable Debug Later

To disable debug logging after troubleshooting, remove or comment out this line in `source_controller.py`:

```python
# self.logger.setLevel(logging.DEBUG)
```
