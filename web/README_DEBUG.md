# KitchenRadio Flask Debug Setup

This guide explains how to set up and debug the KitchenRadio web interface using Flask's debug mode.

## Prerequisites

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure Backend Services are Running**:
   - **MPD**: Should be running on `192.168.1.4:6600` (or configured host/port)
   - **go-librespot**: Should be running on `192.168.1.4:3678` (or configured host/port)

## Quick Start (Debug Mode)

### Option 1: PowerShell (Recommended for Windows)
```powershell
.\debug_flask.ps1
```

### Option 2: Command Prompt (Windows)
```cmd
debug_flask.bat
```

### Option 3: Python Direct
```bash
python debug_flask.py
```

### Option 4: Manual Flask Command
```bash
# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1
export DEBUG=true
export LOG_LEVEL=DEBUG

# Add project to Python path
export PYTHONPATH=.:src:web:$PYTHONPATH

# Run Flask app
cd web
python kitchen_radio_web.py --debug
```

## Debug Features Enabled

When running in debug mode, you get:

- **🔄 Auto-reload**: Flask automatically restarts when you modify Python files
- **🐛 Debug toolbar**: Interactive debugger in the browser for errors
- **📝 Verbose logging**: Detailed logs from both Flask and KitchenRadio daemon
- **🔍 Error pages**: Detailed error information with stack traces
- **📊 Request logging**: All HTTP requests logged to console

## Web Interface Access

Once started, the web interface will be available at:
- **Local access**: http://localhost:5000
- **Network access**: http://127.0.0.1:5000

## Debug Configuration

### Environment Variables

The debug setup automatically configures these environment variables:

```bash
FLASK_ENV=development          # Enable Flask development mode
FLASK_DEBUG=1                 # Enable Flask debugger
DEBUG=true                    # Enable KitchenRadio debug logging
LOG_LEVEL=DEBUG              # Set detailed logging level
```

### File Structure

```
KitchenRadio/
├── debug_flask.py           # Python debug script
├── debug_flask.ps1          # PowerShell debug script  
├── debug_flask.bat          # Batch debug script
├── web/
│   ├── kitchen_radio_web.py # Flask web server
│   ├── templates/
│   │   └── index.html       # Main web interface
│   └── static/
│       ├── css/
│       │   └── style.css    # Styles
│       └── js/
│           └── app.js       # JavaScript application
└── requirements.txt         # Dependencies (includes Flask)
```

## Development Workflow

1. **Start Debug Mode**:
   ```powershell
   .\debug_flask.ps1
   ```

2. **Make Changes**: Edit any Python, HTML, CSS, or JavaScript files

3. **See Changes**: 
   - Python changes: Flask auto-reloads
   - Frontend changes: Refresh browser

4. **Debug Issues**:
   - Check console for detailed logs
   - Use browser developer tools for frontend debugging
   - Flask will show interactive debugger for Python errors

## API Endpoints (for debugging)

The web interface provides these API endpoints:

- `GET /api/status` - Get current status of both backends
- `POST /api/mpd/<action>` - Control MPD (play, pause, stop, next, previous, volume)
- `POST /api/librespot/<action>` - Control librespot (play, pause, stop, next, previous, volume)
- `POST /api/volume/<backend>/<action>` - Quick volume control (up/down)

### Example API Calls

```bash
# Get status
curl http://localhost:5000/api/status

# Play MPD
curl -X POST http://localhost:5000/api/mpd/play

# Set librespot volume
curl -X POST http://localhost:5000/api/librespot/volume \
  -H "Content-Type: application/json" \
  -d '{"level": 75}'

# Volume up on MPD
curl -X POST http://localhost:5000/api/volume/mpd/up
```

## Common Debug Issues

### 1. "ModuleNotFoundError"
Make sure all paths are in PYTHONPATH:
```bash
export PYTHONPATH=.:src:web:$PYTHONPATH
```

### 2. "Connection refused" to backends
- Check if MPD is running: `telnet 192.168.1.4 6600`
- Check if librespot is running: `curl http://192.168.1.4:3678/status`
- Verify .env configuration

### 3. Port 5000 already in use
Change the port in debug script:
```python
server = KitchenRadioWebServer(host='127.0.0.1', port=5001, debug=True)
```

### 4. Frontend not updating
- Hard refresh browser (Ctrl+F5)
- Check browser console for errors
- Verify static files are being served correctly

## Production vs Debug

| Feature | Debug Mode | Production Mode |
|---------|------------|-----------------|
| Auto-reload | ✅ Enabled | ❌ Disabled |
| Error pages | 🐛 Detailed | 🔒 Generic |
| Logging | 📝 Verbose | 📊 Essential |
| Performance | 🐌 Slower | ⚡ Optimized |
| Security | ⚠️ Exposed | 🔒 Secure |

## Next Steps

1. **Test Backend Connections**: Verify both MPD and librespot are accessible
2. **Test Web Interface**: Open http://localhost:5000 and test all controls
3. **Check Logs**: Monitor console output for errors or issues
4. **Customize**: Modify HTML/CSS/JS files to customize the interface
5. **Deploy**: When ready, use production mode for deployment

## Troubleshooting

If you encounter issues:

1. Check the console output for error messages
2. Verify your .env configuration
3. Test backend connections separately using the CLI tools
4. Check network connectivity to MPD and librespot servers
5. Review the Flask and KitchenRadio logs for detailed error information
