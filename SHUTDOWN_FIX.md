# Fix: MPD Client Trying to Reconnect During Shutdown

## Problem
When shutting down the KitchenRadio server, the MPD and Librespot monitors were trying to reconnect even though the system was shutting down, causing errors and delayed shutdown.

## Root Cause

### Monitor Loop Reconnect Logic
The monitor loops checked if the client was disconnected and automatically tried to reconnect:

```python
# mpd/monitor.py - OLD CODE (BROKEN)
while not self._stop_event.is_set():
    if self.client.is_connected():
        self._check_for_changes()
    else:
        logger.warning("MPD connection lost, try to reconnect")
        self.client.connect()  # ❌ Tries to reconnect even during shutdown!
```

### Problem Flow
1. User presses Ctrl+C to stop server
2. `kitchen_radio.stop()` called
3. Sets `self.running = False`
4. Tries to disconnect MPD client
5. **Monitor loop detects disconnection**
6. **Monitor tries to reconnect** ❌
7. Disconnect and reconnect fight each other
8. Delayed or messy shutdown

## Fixes Applied

### Fix 1: Check Stop Event Before Reconnecting

**File**: `kitchenradio/mpd/monitor.py`

```python
# NEW CODE (FIXED)
while not self._stop_event.is_set():
    if self.client.is_connected():
        self._check_for_changes()
    else:
        # Don't try to reconnect if we're shutting down ✅
        if not self._stop_event.is_set():
            logger.warning("MPD connection lost, try to reconnect")
            self.client.connect()
```

**File**: `kitchenradio/librespot/monitor.py`

```python
# NEW CODE (FIXED)
while not self._stop_event.is_set():
    if self.client.is_connected():
        self._check_for_changes()
    else:
        # Don't try to reconnect if we're shutting down ✅
        if not self._stop_event.is_set():
            logger.warning("go-librespot connection lost")
            self.client.connect()
```

### Fix 2: Properly Stop Monitors Before Disconnecting

**File**: `kitchenradio/radio/kitchen_radio.py`

```python
# OLD CODE (INCOMPLETE)
def stop(self):
    self.running = False
    
    # Wait for threads to finish
    if self.mpd_monitor_thread:
        self.mpd_monitor_thread.join(timeout=5)
    
    # Disconnect
    if self.mpd_client:
        self.mpd_client.disconnect()
```

**Problem**: Threads were still running when disconnect was called!

```python
# NEW CODE (FIXED)
def stop(self):
    self.running = False
    
    # Stop monitor instances (sets their _stop_event) ✅
    if self.mpd_monitor:
        self.mpd_monitor.stop_monitoring()
    
    if self.librespot_monitor:
        self.librespot_monitor.stop_monitoring()
    
    # Wait for threads to finish (they exit quickly now) ✅
    if self.mpd_monitor_thread:
        self.mpd_monitor_thread.join(timeout=5)
    
    # NOW safe to disconnect (monitors are stopped) ✅
    if self.mpd_client:
        self.mpd_client.disconnect()
```

## How It Works Now

### Correct Shutdown Flow

1. **User presses Ctrl+C**
   ```
   KeyboardInterrupt caught
   ```

2. **`kitchen_radio.stop()` called**
   ```python
   self.running = False
   ```

3. **Stop monitors explicitly**
   ```python
   self.mpd_monitor.stop_monitoring()     # Sets _stop_event
   self.librespot_monitor.stop_monitoring()  # Sets _stop_event
   ```

4. **Monitor loops see stop event**
   ```python
   while not self._stop_event.is_set():  # ✅ Exits immediately
   ```

5. **Wait for threads to finish**
   ```python
   self.mpd_monitor_thread.join(timeout=5)  # ✅ Quick exit
   ```

6. **Disconnect clients** (no reconnect attempts)
   ```python
   self.mpd_client.disconnect()  # ✅ Clean disconnect
   ```

7. **Clean shutdown** ✅

## Benefits

✅ **No reconnect attempts during shutdown**
✅ **Faster, cleaner shutdown**
✅ **No error messages about reconnection**
✅ **Proper thread cleanup**
✅ **Graceful exit**

## Testing

### Before Fix
```
^C
Stopping KitchenRadio daemon...
MPD connection lost, try to reconnect  ❌
Error connecting to MPD: Connection refused  ❌
Disconnected from MPD
go-librespot connection lost  ❌
Error: connection refused  ❌
KitchenRadio daemon stopped
```

### After Fix
```
^C
Stopping KitchenRadio daemon...
Stopped MPD monitor  ✅
Stopped librespot monitor  ✅
Disconnected from MPD  ✅
Disconnected from librespot  ✅
KitchenRadio daemon stopped  ✅
```

## Summary

**Changed Files:**
1. `kitchenradio/mpd/monitor.py` - Added stop event check before reconnect
2. `kitchenradio/librespot/monitor.py` - Added stop event check before reconnect
3. `kitchenradio/radio/kitchen_radio.py` - Call stop_monitoring() before disconnect

**Result:** Clean, fast shutdown with no reconnection attempts! 🎉
