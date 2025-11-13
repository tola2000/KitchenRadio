# How to Start KitchenRadio Server

## Quick Start

### Method 1: Direct Python Execution (Recommended for Testing)

Run the web server directly using Python:

```powershell
# Navigate to the project directory
cd "c:\Users\ID980331\OneDrive - Proximus\Personal\Home\KitchenRadio"

# Start the server (emulator mode - no hardware required)
python -m kitchenradio.web.kitchen_radio_web
```

This will start the server on `http://127.0.0.1:5001` with:
- ✅ **Emulator mode** - No Raspberry Pi hardware required
- ✅ **GPIO disabled** - Safe for Windows/development
- ✅ **Display emulator** - View display in web browser

### Method 2: As a Python Module

```powershell
# Install the package (if not already done)
pip install -e .

# Run as module
python -m kitchenradio.web.kitchen_radio_web
```

### Method 3: Custom Python Script

Create a startup script `start_server.py`:

```python
import logging
from kitchenradio.web.kitchen_radio_web import KitchenRadioWeb

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create and start server
api = KitchenRadioWeb(
    kitchen_radio=None,      # Will create its own
    host='0.0.0.0',          # Listen on all interfaces (or '127.0.0.1' for localhost only)
    port=5001,               # Port number
    enable_gpio=False,       # Set to True on Raspberry Pi with buttons
    use_hardware_display=False  # Set to True for hardware SPI display
)

if api.start():
    print("✅ KitchenRadio Web API started successfully")
    print(f"📡 API available at: http://127.0.0.1:5001")
    print("\n📋 Available endpoints:")
    print("   GET  /api/status - Get system status")
    print("   GET  /api/display/image - View display (PNG)")
    print("   POST /api/button/<name> - Simulate button press")
    print("\n⚠️  Press Ctrl+C to stop")
    
    try:
        import time
        while api.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        api.stop()
else:
    print("❌ Failed to start KitchenRadio Web API")
    exit(1)
```

Then run:
```powershell
python start_server.py
```

## Configuration Options

### Server Configuration

When creating `KitchenRadioWeb`, you can customize:

```python
api = KitchenRadioWeb(
    kitchen_radio=None,           # Provide your own KitchenRadio instance or None
    host='127.0.0.1',            # Server host (use '0.0.0.0' to allow remote access)
    port=5001,                   # Server port
    enable_gpio=False,           # Enable GPIO buttons (Raspberry Pi only)
    use_hardware_display=False   # Use hardware SPI display or emulator
)
```

### Display Modes

**Emulator Mode** (Default for Windows/Testing):
```python
use_hardware_display=False
```
- ✅ Works on Windows/Mac/Linux
- ✅ No hardware required
- ✅ View display via `/api/display/image` endpoint
- ✅ Perfect for development

**Hardware Mode** (Raspberry Pi with SSD1322):
```python
use_hardware_display=True
```
- ✅ Uses real SPI display (SSD1322 256x64 OLED)
- ✅ Requires Raspberry Pi with proper wiring
- ⚠️  Falls back to emulator if SPI not available

### GPIO Buttons

**Disabled** (Default for Windows/Testing):
```python
enable_gpio=False
```
- ✅ Safe for non-Raspberry Pi systems
- ✅ Use web API to simulate buttons

**Enabled** (Raspberry Pi with hardware buttons):
```python
enable_gpio=True
```
- ✅ Physical buttons connected to GPIO pins
- ⚠️  Only works on Raspberry Pi

## Available API Endpoints

Once the server is running, you can access:

### System Status
- `GET /api/status` - Get API and radio status
- `GET /api/health` - Health check

### Display Control
- `GET /api/display/image` - Get display image (PNG) 📸
- `GET /api/display/ascii` - Get display as ASCII art
- `GET /api/display/status` - Get display status
- `GET /api/display/stats` - Get display statistics
- `POST /api/display/clear` - Clear display
- `POST /api/display/test` - Show test pattern

### Button Control
- `GET /api/buttons` - List all buttons
- `POST /api/button/<name>` - Press a button
- `GET /api/button/<name>/info` - Get button info
- `GET /api/buttons/stats` - Get button statistics
- `POST /api/buttons/reset-stats` - Reset statistics

### Button Names
Available buttons: `power`, `volume_up`, `volume_down`, `play_pause`, `next`, `previous`, `stop`, `source_mpd`, `source_spotify`, `menu_up`, `menu_down`, `menu_select`

## Testing the Server

### 1. Check Server Status
```powershell
curl http://127.0.0.1:5001/api/health
```

### 2. View Display Image
Open in browser: `http://127.0.0.1:5001/api/display/image`

### 3. Press a Button
```powershell
curl -X POST http://127.0.0.1:5001/api/button/volume_up
```

### 4. Get System Status
```powershell
curl http://127.0.0.1:5001/api/status
```

## Troubleshooting

### Server won't start
**Error**: "Address already in use"
- **Solution**: Port 5001 is already in use. Change the port:
  ```python
  api = KitchenRadioWeb(port=5002)  # Use different port
  ```

### Display not showing
**Error**: "Display not initialized"
- **Solution**: Make sure emulator mode is enabled:
  ```python
  use_hardware_display=False  # Use emulator
  ```

### Import errors
**Error**: "ModuleNotFoundError: No module named 'kitchenradio'"
- **Solution**: Install dependencies:
  ```powershell
  pip install -r requirements.txt
  ```

### GPIO warnings on Windows
**Warning**: "Button controller not available"
- **Solution**: This is normal on Windows. Use `enable_gpio=False`

## Running on Raspberry Pi

For production on Raspberry Pi with hardware:

```python
api = KitchenRadioWeb(
    kitchen_radio=None,
    host='0.0.0.0',              # Allow remote access
    port=5001,
    enable_gpio=True,            # Enable physical buttons
    use_hardware_display=True    # Use SPI display
)
```

## Environment Variables

You can configure via environment variables (optional):

```powershell
$env:KITCHEN_RADIO_HOST = "0.0.0.0"
$env:KITCHEN_RADIO_PORT = "5001"
$env:ENABLE_GPIO = "false"
$env:USE_HARDWARE_DISPLAY = "false"
```

## Logging

To see detailed logs:

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG, INFO, WARNING, ERROR
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Summary

**For Development (Windows/Mac):**
```powershell
cd "c:\Users\ID980331\OneDrive - Proximus\Personal\Home\KitchenRadio"
python -m kitchenradio.web.kitchen_radio_web
```

**For Production (Raspberry Pi):**
Create a script with `enable_gpio=True` and `use_hardware_display=True`, then run it as a service.

**Access the server:**
- Local: `http://127.0.0.1:5001`
- Display: `http://127.0.0.1:5001/api/display/image`
- Status: `http://127.0.0.1:5001/api/status`

🎉 That's it! Your KitchenRadio server should now be running!
