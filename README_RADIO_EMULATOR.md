# Physical Radio Emulator

A single unified server app that simulates a physical radio by directly integrating KitchenRadio, button controller, and display controller.

## Features

- **Unified Architecture**: Single app that wraps KitchenRadio directly
- **Button Controller**: Maps physical button presses to KitchenRadio actions
- **Display Controller**: Real-time display updates based on KitchenRadio status
- **Web Interface**: Clean HTML interface for controlling the physical radio
- **Direct Integration**: No intermediate emulation layers - controllers wrap KitchenRadio directly

## Quick Start

### 1. Start the Radio Emulator

```bash
python start_radio_emulator.py
```

This will:
- Start the KitchenRadio daemon with both MPD and Spotify backends
- Initialize the button and display controllers
- Launch a web server on `http://localhost:5000`

### 2. Open Web Interface

Navigate to `http://localhost:5000` in your browser to see the physical radio interface.

### 3. Control the Radio

Use the web interface buttons to:
- **Source Selection**: Switch between MPD and Spotify
- **Transport Controls**: Play/pause, stop, next, previous
- **Volume Controls**: Volume up/down
- **Menu Navigation**: Menu buttons (basic implementation)
- **Power**: Stop all playback

## API Endpoints

### GET /api/status
Returns the current radio status including:
- Radio running state
- Display lines (4-line display content)
- Full KitchenRadio status (backends, playback, etc.)

### POST /api/button/<button_name>
Triggers a button press. Supported buttons:
- `source_mpd`, `source_spotify`
- `transport_play_pause`, `transport_stop`, `transport_next`, `transport_previous`
- `volume_up`, `volume_down`
- `menu_up`, `menu_down`, `menu_ok`, `menu_exit`, `menu_toggle`, `menu_set`
- `power`

## Architecture

```
┌─────────────────────┐
│   Web Interface     │ (Flask + HTML)
│   Physical Radio    │
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│   ButtonController  │ ──┐
└─────────────────────┘   │
                          │   Direct wrapper
┌─────────────────────┐   │   (no emulation layers)
│  DisplayController  │ ──┤
└─────────────────────┘   │
                          │
                          ▼
┌─────────────────────┐
│    KitchenRadio     │ (Main daemon)
│    - MPD Backend    │
│    - Spotify Backend│
└─────────────────────┘
```

### Components

1. **PhysicalRadio**: Main coordinator class
   - Manages KitchenRadio daemon
   - Coordinates button and display controllers
   - Provides unified status interface

2. **ButtonController**: Direct KitchenRadio wrapper
   - Maps button names to KitchenRadio methods
   - No intermediate emulation - direct method calls
   - Handles source switching, transport, volume, etc.

3. **DisplayController**: Real-time display updater
   - Polls KitchenRadio status every second
   - Formats status into 4-line display
   - Shows current source, playback state, track info

4. **Flask Web App**: Simple REST API + HTML interface
   - Status endpoint for current state
   - Button endpoints for user interactions
   - Clean, responsive web interface

## Configuration

Set these environment variables:

- `DEBUG=true` - Enable debug logging
- `FLASK_HOST=0.0.0.0` - Web server host
- `FLASK_PORT=5000` - Web server port
- KitchenRadio settings (MPD_HOST, etc.) - See main KitchenRadio docs

## Testing

Run the test script to verify functionality:

```bash
python test_radio_emulator.py
```

This will:
- Start the radio
- Test various button presses
- Show display content
- Verify the integration works

## Files

- `radio_emulator.py` - Main unified emulator app
- `start_radio_emulator.py` - Easy startup script
- `test_radio_emulator.py` - Test script
- `frontend/templates/physical_radio.html` - Web interface
- `README_RADIO_EMULATOR.md` - This documentation

## Removed Files

The following legacy/test files have been removed in favor of this unified approach:
- `test_hardware_emulator.py`
- `hardware_emulator_app.py`
- `templates/emulator/` (old templates)
- `static/emulator/` (old static files)

## Next Steps

Optional enhancements:
- WebSocket support for real-time updates (currently uses polling)
- Enhanced menu system with playlist navigation
- Advanced display formatting options
- Button press visual feedback improvements
