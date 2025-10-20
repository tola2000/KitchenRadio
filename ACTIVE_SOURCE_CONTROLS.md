# KitchenRadio Active Source Playback Controls

## Overview
Added unified playback control methods to the KitchenRadio daemon that automatically send commands to the currently active source (MPD or Spotify).

## New KitchenRadio Daemon Methods

### `play_pause() -> bool`
- Toggles between play and pause on the active source
- Automatically detects current playback state and switches accordingly
- Returns `True` if successful, `False` if failed or no active source

### `play() -> bool`
- Starts playback on the active source
- Returns `True` if successful, `False` if failed or no active source

### `pause() -> bool`
- Pauses playback on the active source
- Returns `True` if successful, `False` if failed or no active source

### `stop() -> bool`
- Stops playback on the active source
- Returns `True` if successful, `False` if failed or no active source

### `next() -> bool`
- Skips to next track on the active source
- Returns `True` if successful, `False` if failed or no active source

### `previous() -> bool`
- Skips to previous track on the active source
- Returns `True` if successful, `False` if failed or no active source

## New Web API Endpoint

### `POST /api/control/<action>`
Controls playback on the currently active source.

**Actions:**
- `play` - Start playback
- `pause` - Pause playback
- `stop` - Stop playback
- `next` - Next track
- `previous` - Previous track
- `play_pause` - Toggle play/pause

**Response Format:**
```json
{
    "success": true,
    "message": "Play command sent to mpd",
    "active_source": "mpd"
}
```

**Error Response:**
```json
{
    "success": false,
    "error": "No active source set. Please select a source first."
}
```

## Usage Examples

### Python (Direct Daemon)
```python
from kitchenradio.radio.kitchen_radio import KitchenRadio, BackendType

daemon = KitchenRadio()
daemon.start()

# Set active source
daemon.set_source(BackendType.MPD)

# Control playback
daemon.play()          # Start playing
daemon.pause()         # Pause
daemon.play_pause()    # Toggle play/pause
daemon.next()          # Next track
daemon.previous()      # Previous track
daemon.stop()          # Stop
```

### HTTP API
```bash
# Set source first
curl -X POST http://localhost:5000/api/source/mpd

# Control playback
curl -X POST http://localhost:5000/api/control/play
curl -X POST http://localhost:5000/api/control/pause
curl -X POST http://localhost:5000/api/control/play_pause
curl -X POST http://localhost:5000/api/control/next
curl -X POST http://localhost:5000/api/control/previous
curl -X POST http://localhost:5000/api/control/stop
```

## Features

### ✅ Smart State Detection
- `play_pause()` automatically detects current playback state
- Works with both MPD (play/pause/stop) and Spotify (Playing/Paused/Stopped) state formats

### ✅ Source Validation
- All methods check if an active source is set
- Verify the active source backend is connected
- Graceful error handling for disconnected backends

### ✅ Comprehensive Logging
- Clear log messages with emoji icons (▶️ ⏸️ ⏹️ ⏭️ ⏮️)
- Source identification in log messages
- Error logging for troubleshooting

### ✅ Error Handling
- Returns `False` for failed operations
- Warns when no active source is set
- Handles backend connection issues gracefully

## Test Scripts
- `test_active_source_controls.py` - Test daemon methods directly
- `test_api_active_controls.py` - Test HTTP API endpoints

## Benefits
1. **Unified Interface**: Single set of methods works with any active backend
2. **Source Awareness**: Commands automatically go to the correct backend
3. **State Intelligence**: Play/pause toggle works correctly with different state formats
4. **Web Ready**: HTTP API enables web interface integration
5. **Robust**: Comprehensive error handling and validation
