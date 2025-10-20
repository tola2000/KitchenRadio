# Button Controller REST API

A REST API wrapper for the KitchenRadio Button Controller that exposes HTTP endpoints for button control instead of using Raspberry Pi GPIO pins.

## Features

- **REST API Interface**: HTTP endpoints for all button functions
- **Dual Mode Support**: Can run with or without GPIO buttons
- **Button Statistics**: Track button press counts and usage
- **Multiple Button Presses**: Press multiple buttons in sequence
- **Real-time Status**: Get current API and KitchenRadio status
- **Easy Integration**: Simple JSON-based API for external applications

## Quick Start

### 1. Start the API Server

```bash
python start_button_api.py
```

The API will be available at `http://localhost:5001`

### 2. Test the API

```bash
python test_button_controller_api.py
```

For interactive testing:
```bash
python test_button_controller_api.py --interactive
```

## API Endpoints

### Button Control

#### `POST /api/button/<button_name>`
Press a specific button.

**Example:**
```bash
curl -X POST http://localhost:5001/api/button/transport_play_pause
```

**Response:**
```json
{
  "success": true,
  "button": "transport_play_pause",
  "timestamp": 1697812345.67,
  "message": "Button transport_play_pause pressed successfully"
}
```

#### `POST /api/buttons/press-multiple`
Press multiple buttons in sequence.

**Request Body:**
```json
{
  "buttons": ["source_mpd", "volume_up", "transport_play_pause"],
  "delay": 0.5
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {"button": "source_mpd", "success": true, "timestamp": 1697812345.67},
    {"button": "volume_up", "success": true, "timestamp": 1697812346.17},
    {"button": "transport_play_pause", "success": true, "timestamp": 1697812346.67}
  ],
  "total_buttons": 3,
  "successful_presses": 3,
  "failed_presses": 0
}
```

### Information & Status

#### `GET /api/buttons`
List all available buttons.

**Response:**
```json
{
  "buttons": [
    {
      "name": "source_mpd",
      "description": "Switch to MPD music source",
      "category": "source",
      "press_count": 5
    },
    ...
  ],
  "total_buttons": 15,
  "gpio_enabled": false
}
```

#### `GET /api/button/<button_name>/info`
Get detailed information about a specific button.

#### `GET /api/buttons/stats`
Get button press statistics.

**Response:**
```json
{
  "button_stats": {
    "source_mpd": 3,
    "transport_play_pause": 7,
    "volume_up": 12,
    ...
  },
  "total_presses": 45,
  "last_button_press": {
    "button": "volume_up",
    "timestamp": 1697812345.67,
    "success": true
  },
  "api_uptime": 1234.56,
  "gpio_enabled": false
}
```

#### `POST /api/buttons/reset-stats`
Reset button press statistics.

#### `GET /api/status`
Get comprehensive API and KitchenRadio status.

#### `GET /api/health`
Health check endpoint.

## Available Buttons

### Source Control
- `source_mpd` - Switch to MPD music source
- `source_spotify` - Switch to Spotify music source

### Transport Control
- `transport_play_pause` - Toggle play/pause
- `transport_stop` - Stop playback
- `transport_next` - Next track
- `transport_previous` - Previous track

### Volume Control
- `volume_up` - Increase volume
- `volume_down` - Decrease volume

### Menu Navigation
- `menu_up` - Navigate menu up
- `menu_down` - Navigate menu down
- `menu_ok` - Select menu item
- `menu_exit` - Exit menu
- `menu_toggle` - Toggle menu display
- `menu_set` - Confirm menu selection

### Power
- `power` - Power button (stop all playback)

## Configuration

Set these environment variables before starting:

- `API_HOST=0.0.0.0` - API server host (default: 0.0.0.0)
- `API_PORT=5001` - API server port (default: 5001)
- `ENABLE_GPIO=false` - Enable GPIO buttons alongside API (default: false)
- `DEBUG=false` - Enable debug logging (default: false)

## Usage Examples

### Python Client Example

```python
import requests

# Press a button
response = requests.post('http://localhost:5001/api/button/transport_play_pause')
if response.json()['success']:
    print("Button pressed successfully!")

# Get button statistics
stats = requests.get('http://localhost:5001/api/buttons/stats').json()
print(f"Total button presses: {stats['total_presses']}")

# Press multiple buttons
requests.post('http://localhost:5001/api/buttons/press-multiple', json={
    'buttons': ['source_mpd', 'transport_play_pause'],
    'delay': 1.0
})
```

### curl Examples

```bash
# Health check
curl http://localhost:5001/api/health

# List all buttons
curl http://localhost:5001/api/buttons

# Press play/pause button
curl -X POST http://localhost:5001/api/button/transport_play_pause

# Get button info
curl http://localhost:5001/api/button/volume_up/info

# Get statistics
curl http://localhost:5001/api/buttons/stats

# Press multiple buttons
curl -X POST http://localhost:5001/api/buttons/press-multiple \
  -H "Content-Type: application/json" \
  -d '{"buttons": ["volume_up", "volume_up", "transport_play_pause"], "delay": 0.5}'

# Get overall status  
curl http://localhost:5001/api/status
```

### JavaScript/Browser Example

```javascript
// Press a button
fetch('/api/button/transport_play_pause', {method: 'POST'})
  .then(response => response.json())
  .then(data => console.log('Button pressed:', data.success));

// Get button list
fetch('/api/buttons')
  .then(response => response.json())
  .then(data => {
    data.buttons.forEach(button => {
      console.log(`${button.name}: ${button.description}`);
    });
  });
```

## Integration with Physical Radio Emulator

The Button Controller API can be used alongside the Physical Radio Emulator:

1. **Standalone Mode**: Run just the API for remote control
2. **Hybrid Mode**: API + GPIO buttons for both physical and remote control
3. **Web Integration**: Use the API from web interfaces

## Architecture

```
┌─────────────────────┐
│   REST API Client   │ (curl, Python, JavaScript, etc.)
└─────────────────────┘
           │ HTTP
           ▼
┌─────────────────────┐
│ ButtonControllerAPI │ (Flask REST server)
└─────────────────────┘
           │ Direct calls
           ▼
┌─────────────────────┐
│  ButtonController   │ (Button action handler)
└─────────────────────┘
           │ Direct calls
           ▼
┌─────────────────────┐
│   KitchenRadio      │ (Main daemon)
└─────────────────────┘
```

## Files

- `kitchenradio/radio/hardware/button_controller_api.py` - Main API implementation
- `start_button_api.py` - Startup script
- `test_button_controller_api.py` - Test script and examples
- `README_BUTTON_API.md` - This documentation

## Error Handling

The API returns appropriate HTTP status codes:

- `200` - Success
- `400` - Bad request (invalid button name, missing parameters)
- `404` - Not found (button doesn't exist)
- `500` - Internal server error

Error responses include details:

```json
{
  "success": false,
  "error": "Unknown button: invalid_button_name",
  "available_buttons": ["source_mpd", "transport_play_pause", ...]
}
```

## Security Considerations

- The API runs on all interfaces by default (`0.0.0.0`) - restrict access as needed
- No authentication is implemented - add authentication for production use
- Consider rate limiting for public deployments
- Use HTTPS in production environments
