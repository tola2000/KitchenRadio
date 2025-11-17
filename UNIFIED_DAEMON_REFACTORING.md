# Unified Daemon Refactoring

## Summary

Refactored `run_daemon.py` to provide a unified entry point for KitchenRadio with flexible component initialization. The web interface, display controller, and button controller are now optional components that can be enabled/disabled via command-line arguments.

## What Changed

### Before

**Two separate entry points:**

1. **Console daemon** (`run_daemon.py`):
   - Always enabled display + buttons
   - No web interface
   - Hardcoded configuration

2. **Web daemon** (`python -m kitchenradio.web.kitchen_radio_web`):
   - Separate startup script
   - Own argument parsing
   - Duplicate initialization code

### After

**Single unified entry point** (`run_daemon.py`):

- ✅ Flexible component initialization
- ✅ Command-line argument support
- ✅ Enable/disable any combination of components
- ✅ Consistent initialization pattern
- ✅ Proper cleanup sequence

## Architecture

### Component Structure

```
KitchenRadio Daemon
├── Core (Always Required)
│   └── KitchenRadio (audio source management)
│
├── Display Controller (Optional)
│   ├── Enabled by default
│   ├── Disabled with --no-display or --no-hardware
│   └── Manages OLED display
│
├── Button Controller (Optional)
│   ├── Enabled by default
│   ├── Disabled with --no-buttons or --no-hardware
│   └── Manages physical buttons via MCP23017
│
└── Web Interface (Optional)
    ├── Disabled by default
    ├── Enabled with --web
    └── Provides REST API + web UI
```

### Initialization Order

1. **Parse Arguments** - Determine which components to enable
2. **Setup Logging** - Configure logging level
3. **Initialize Core** - Start KitchenRadio (required)
4. **Initialize Display** - If enabled
5. **Initialize Buttons** - If enabled (depends on display)
6. **Initialize Web** - If enabled
7. **Run Main Loop** - Keep daemon running
8. **Cleanup** - Stop all components in reverse order

## Usage Modes

### Mode 1: Hardware Only (Default)
```bash
python run_daemon.py
```
- ✅ Display Controller
- ✅ Button Controller
- ❌ Web Interface

**Use Case**: Physical radio with hardware controls

### Mode 2: Hardware + Web
```bash
python run_daemon.py --web --port 8080
```
- ✅ Display Controller
- ✅ Button Controller
- ✅ Web Interface

**Use Case**: Physical radio with remote web control

### Mode 3: Web Only
```bash
python run_daemon.py --web --no-hardware
```
- ❌ Display Controller
- ❌ Button Controller
- ✅ Web Interface

**Use Case**: Headless server, remote control only

### Mode 4: Custom Combinations
```bash
# Web + Display only (no buttons)
python run_daemon.py --web --no-buttons

# Web + Buttons only (no display)
python run_daemon.py --web --no-display

# Display only (no buttons, no web)
python run_daemon.py --no-buttons
```

**Use Case**: Testing, development, custom setups

## Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--web` | Enable web interface | Disabled |
| `--host HOST` | Web server host address | `0.0.0.0` |
| `--port PORT` | Web server port | `5000` |
| `--no-hardware` | Disable all hardware (display + buttons) | Enabled |
| `--no-display` | Disable display controller only | Enabled |
| `--no-buttons` | Disable button controller only | Enabled |
| `--debug` | Enable debug logging | INFO level |
| `--help` | Show help message | - |

## Code Changes

### File: `run_daemon.py`

**Added:**
- ✅ `parse_arguments()` - Command-line argument parsing
- ✅ Component enable/disable logic
- ✅ Optional component initialization
- ✅ Conditional web server startup
- ✅ Proper cleanup for all components
- ✅ Error handling for each component

**Improved:**
- Better logging output
- Clear status reporting
- Graceful degradation (continue if component fails)
- Consistent initialization pattern

### Example: Component Initialization

```python
# Before (always initialized)
display_controller = DisplayController(...)
display_controller.initialize()

# After (conditional)
display_controller = None
if enable_display:
    display_controller = DisplayController(...)
    if not display_controller.initialize():
        logger.warning("Display failed - continuing without it")
        display_controller = None
```

## Benefits

### 1. **Flexibility**
- Run any combination of components
- Easy to test individual components
- Adapt to different deployment scenarios

### 2. **Simplicity**
- Single entry point instead of multiple scripts
- Consistent command-line interface
- Clear component dependencies

### 3. **Maintainability**
- Centralized initialization logic
- Easier to add new components
- Consistent error handling

### 4. **Development**
- Test without hardware: `--no-hardware`
- Test web only: `--web --no-hardware`
- Debug specific components: `--debug --no-buttons`

### 5. **Production**
- Run as systemd service with specific config
- Easy to switch between modes
- Graceful degradation if hardware fails

## Migration Guide

### Old Way

```bash
# Console daemon
python run_daemon.py

# Web interface (separate script)
python -m kitchenradio.web.kitchen_radio_web --port 8080
```

### New Way

```bash
# Console daemon (same)
python run_daemon.py

# Web interface (now integrated)
python run_daemon.py --web --port 8080
```

### Systemd Service Files

**Old:**
```ini
# Two separate services
/etc/systemd/system/kitchenradio.service
/etc/systemd/system/kitchenradio-web.service
```

**New:**
```ini
# Single service with options
[Service]
ExecStart=/usr/bin/python3 /path/to/run_daemon.py --web --port 8080
```

## Testing

### Test All Modes

```bash
# 1. Hardware only
python run_daemon.py

# 2. Hardware + Web
python run_daemon.py --web

# 3. Web only
python run_daemon.py --web --no-hardware

# 4. Display only
python run_daemon.py --no-buttons

# 5. Buttons only
python run_daemon.py --no-display

# 6. Debug mode
python run_daemon.py --debug

# 7. Custom port
python run_daemon.py --web --port 9000
```

### Verify Graceful Degradation

```bash
# Should continue running even if components fail
python run_daemon.py --web

# Manually disconnect hardware
# Daemon should log warnings but keep running
```

## Future Enhancements

Possible additions:

1. **Config File Support**
   ```bash
   python run_daemon.py --config /path/to/config.yaml
   ```

2. **Environment Variables**
   ```bash
   KITCHENRADIO_WEB_PORT=8080 python run_daemon.py --web
   ```

3. **Multiple Web Ports**
   ```bash
   python run_daemon.py --web --api-port 5000 --ui-port 8080
   ```

4. **MQTT Integration**
   ```bash
   python run_daemon.py --mqtt --mqtt-broker localhost
   ```

5. **Component Status API**
   ```bash
   curl http://localhost:5000/api/components
   {
     "display": {"enabled": true, "status": "running"},
     "buttons": {"enabled": true, "status": "running"},
     "web": {"enabled": true, "status": "running"}
   }
   ```

## Documentation Updates

Updated files:
- ✅ `USER_GUIDE.md` - Running the Daemon section
- ✅ `QUICK_REFERENCE.md` - Starting commands
- ✅ `UNIFIED_DAEMON_REFACTORING.md` - This file

## Backward Compatibility

✅ **Fully backward compatible!**

Old command still works:
```bash
python run_daemon.py  # Same behavior as before
```

Web interface can still be run separately:
```bash
python -m kitchenradio.web.kitchen_radio_web  # Still works
```

## Summary

The unified daemon provides:
- 🎯 **Single entry point** for all modes
- 🔧 **Flexible configuration** via command-line
- 📦 **Modular architecture** with optional components
- 🛡️ **Graceful degradation** if components fail
- 📝 **Clear logging** and status reporting
- 🔄 **Proper cleanup** on shutdown
- ✅ **Full backward compatibility**

This makes KitchenRadio easier to use, test, deploy, and maintain! 🎉
