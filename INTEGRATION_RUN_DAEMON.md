# KitchenRadio Class Integration - run_daemon.py Functionality

## Overview
Successfully integrated all run_daemon.py functionality directly into the KitchenRadio class, making it self-contained with optional UI component management.

## Changes Made

### 1. Updated KitchenRadio `__init__()` Constructor
**Added parameters for UI component control:**
```python
def __init__(self, 
             enable_display=False, 
             enable_buttons=False,
             enable_web=False,
             web_host='0.0.0.0',
             web_port=5000):
```

**New instance variables:**
- `enable_display`: Flag to enable/disable display controller
- `enable_buttons`: Flag to enable/disable button controller  
- `enable_web`: Flag to enable/disable web interface
- `web_host`: Web server host address
- `web_port`: Web server port
- `source_controller`: SourceController instance (handles all backends)
- `display_controller`: Optional DisplayController instance
- `button_controller`: Optional ButtonController instance
- `web_server`: Optional KitchenRadioWeb instance

### 2. Enhanced `start()` Method
**Integrated component initialization:**
- Logs detailed configuration on startup
- Initializes SourceController first
- Conditionally initializes Display Controller (if enabled)
- Conditionally initializes Button Controller (if enabled)
- Conditionally initializes Web Interface (if enabled)
- All UI components receive `source_controller` for direct backend access
- Proper error handling with graceful degradation

**Example startup log:**
```
================================================================================
Starting KitchenRadio Daemon
================================================================================
Configuration:
  MPD: localhost:6600
  Librespot: localhost:5030
  Bluetooth: KitchenRadio
  Default Source: mpd

Controllers:
  Display: Enabled
  Buttons: Enabled
  Web Interface: Enabled
  Web URL: http://0.0.0.0:5000
```

### 3. Enhanced `stop()` Method
**Integrated cleanup for all components:**
- Stops web server (if running)
- Cleans up button controller (if running)
- Cleans up display controller (if running)
- Stops SourceController monitoring
- Cleans up SourceController
- Proper error handling for each component

### 4. Added `reconnect_backends()` Method
Daemon-level operation to reconnect all backends:
- Attempts MPD reconnection
- Attempts Librespot reconnection
- Attempts Bluetooth reconnection
- Returns dict with success status for each backend

### 5. Enhanced `main()` Function
**Full command-line argument parsing:**

```bash
# Run daemon only (no UI)
python -m kitchenradio.kitchen_radio

# Run with web interface
python -m kitchenradio.kitchen_radio --web

# Run with web interface on custom port
python -m kitchenradio.kitchen_radio --web --port 8080

# Run with hardware controls
python -m kitchenradio.kitchen_radio --display --buttons

# Run with everything enabled
python -m kitchenradio.kitchen_radio --web --display --buttons

# Run with web, no hardware
python -m kitchenradio.kitchen_radio --web --no-hardware
```

**Available arguments:**
- `--web`: Enable web interface
- `--display`: Enable display controller
- `--buttons`: Enable button controller
- `--no-hardware`: Disable all hardware
- `--no-display`: Disable display only
- `--no-buttons`: Disable buttons only
- `--host HOST`: Web server host (default: 0.0.0.0)
- `--port PORT`: Web server port (default: 5000)
- `--debug`: Enable debug logging
- `--status`: Show status and exit

### 6. Status Command
Added `--status` flag to check daemon status without running full daemon:
```bash
python -m kitchenradio.kitchen_radio --status
```

**Output example:**
```
KitchenRadio Status:
  Current Source: mpd
  Available Sources: mpd, librespot
  Powered On: True

MPD:
  Connected: True
  State: playing
  Volume: 75%
  Current: Artist Name - Song Title

Spotify (librespot):
  Connected: True
  State: stopped
  Volume: 80%
```

## Architecture

### Component Hierarchy
```
KitchenRadio (Daemon Manager)
├── SourceController (Backend Operations)
│   ├── MPD Backend
│   ├── Librespot Backend
│   └── Bluetooth Backend
└── Optional UI Components
    ├── DisplayController → uses source_controller
    ├── ButtonController → uses source_controller
    └── KitchenRadioWeb → uses source_controller + kitchen_radio
```

### Initialization Flow
```
1. Parse command-line arguments
   ├── --web, --display, --buttons flags
   ├── --host, --port configuration
   └── --debug, --status options

2. Create KitchenRadio(enable_display, enable_buttons, enable_web, ...)
   ├── Load configuration
   ├── Setup logging
   ├── Create SourceController
   └── Register signal handlers

3. Call daemon.start()
   ├── Initialize SourceController
   ├── Start backend monitoring
   ├── Initialize DisplayController (if enabled)
   ├── Initialize ButtonController (if enabled)
   └── Initialize KitchenRadioWeb (if enabled)

4. Call daemon.run()
   ├── Main loop (blocking)
   └── Handle Ctrl+C gracefully

5. Automatic cleanup on exit
   ├── Stop web server
   ├── Cleanup button controller
   ├── Cleanup display controller
   └── Cleanup SourceController
```

## Benefits

### 1. **Simplified Deployment**
- Single entry point: `python -m kitchenradio.kitchen_radio`
- No separate run_daemon.py script needed
- All configuration via command-line arguments

### 2. **Flexible Configuration**
- Enable/disable any UI component
- Mix and match: web only, hardware only, or both
- Custom web server host/port

### 3. **Self-Contained**
- KitchenRadio class manages its own UI components
- Clean separation: daemon lifecycle vs backend operations
- Easy to test individual components

### 4. **Backward Compatible**
- Old run_daemon.py can still work (just creates KitchenRadio with flags)
- New module execution: `python -m kitchenradio.kitchen_radio`
- Both approaches supported

### 5. **Better Error Handling**
- Graceful degradation if UI components fail
- Detailed logging for each initialization step
- Clean shutdown even on errors

## Usage Examples

### Development (Web UI Only)
```bash
python -m kitchenradio.kitchen_radio --web --debug
```

### Production (All Features)
```bash
python -m kitchenradio.kitchen_radio --web --display --buttons
```

### Headless Server (No Hardware)
```bash
python -m kitchenradio.kitchen_radio --web --no-hardware --port 8080
```

### Hardware Only (No Web)
```bash
python -m kitchenradio.kitchen_radio --display --buttons
```

### Status Check
```bash
python -m kitchenradio.kitchen_radio --status
```

## Migration Path

### From Old run_daemon.py
**Old approach:**
```python
# run_daemon.py
kitchen_radio = KitchenRadio()
kitchen_radio.start()
# ... create UI controllers separately
```

**New approach (Option 1 - Use integrated main):**
```bash
python -m kitchenradio.kitchen_radio --web --display --buttons
```

**New approach (Option 2 - Programmatic):**
```python
from kitchenradio.kitchen_radio import KitchenRadio

daemon = KitchenRadio(
    enable_display=True,
    enable_buttons=True,
    enable_web=True,
    web_port=5000
)
daemon.run()
```

## Files Modified

1. **kitchenradio/kitchen_radio.py** (~350 lines)
   - Added UI component management
   - Integrated command-line parsing
   - Added reconnect_backends() method
   - Enhanced start() with component initialization
   - Enhanced stop() with component cleanup
   - Added comprehensive main() function

## Testing

Run the integrated daemon:
```bash
# Basic test
python -m kitchenradio.kitchen_radio

# With web interface
python -m kitchenradio.kitchen_radio --web

# Full featured
python -m kitchenradio.kitchen_radio --web --display --buttons --debug
```

## Summary

✅ **Successfully integrated run_daemon.py functionality into KitchenRadio class**
- Self-contained daemon with optional UI components
- Command-line argument parsing
- Flexible component enable/disable
- Graceful error handling
- Clean shutdown
- Status reporting

The KitchenRadio class is now a complete, self-contained daemon that can be run directly or imported and configured programmatically.
