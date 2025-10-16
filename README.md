# MoOde Audio REST Controller

A Python library and command-line interface for controlling [MoOde Audio](https://moodeaudio.org/) servers through their REST API.

## Features

- **Complete API Coverage**: Control playback, volume, playlists, and more
- **CLI Interface**: Easy-to-use command-line tools for quick control
- **Python Library**: Integrate MoOde control into your own applications
- **Error Handling**: Robust error handling and connection management
- **Type Hints**: Full type annotation support for better IDE integration

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Make CLI executable (optional):**
   ```bash
   chmod +x moode_cli.py
   ```

## Quick Start

### Command Line Interface

The CLI provides simple commands for common operations:

```bash
# Basic playback control
python moode_cli_v2.py play
python moode_cli_v2.py pause
python moode_cli_v2.py stop
python moode_cli_v2.py next
python moode_cli_v2.py previous

# Volume control
python moode_cli_v2.py volume 75        # Set volume to 75%
python moode_cli_v2.py volume           # Show current volume

# Status and information
python moode_cli_v2.py status           # Show player status
python moode_cli_v2.py current          # Show current song
python moode_cli_v2.py playlist         # Show current playlist
python moode_cli_v2.py connection       # Test connection

# Remote server control
python moode_cli_v2.py --host 192.168.1.100 play
```

### Python Library

```python
from moode_controller_v2 import MoOdeAudioController

# Connect to MoOde server
controller = MoOdeAudioController("192.168.1.100")

# Check connection
if controller.is_connected():
    print("Connected to MoOde Audio")
    
    # Control playback
    controller.play()
    controller.set_volume(75)
    
    # Get information
    status = controller.get_status()
    current_song = controller.get_current_song()
    
    print(f"Now playing: {current_song.get('title', 'Unknown')}")
else:
    print("Failed to connect")
```

## CLI Commands

### Playback Control
- `play` - Start playback
- `pause` - Pause playback  
- `stop` - Stop playback
- `next` - Skip to next track
- `previous` - Skip to previous track
- `toggle` - Toggle between play and pause

### Volume Control
- `volume` - Show current volume
- `volume <level>` - Set volume (0-100)

### Information
- `status` - Show player status
- `current` - Show current song information
- `playlist` - Show current playlist
- `info` - Show system information

### Advanced
- `seek <seconds>` - Seek to position in current track

### Options
- `--host <hostname>` - Specify MoOde server address
- `--port <port>` - Specify MoOde server port
- `--json` - Output in JSON format (for status commands)

## Library API

### MoOdeAudioController Class

#### Connection
- `__init__(host, port, timeout)` - Initialize controller
- `is_connected()` - Check server connectivity
- `wait_for_connection(max_attempts, delay)` - Wait for server

#### Playback Control
- `play()` - Start playback
- `pause()` - Pause playback
- `stop()` - Stop playback
- `next_track()` - Skip to next track
- `previous_track()` - Skip to previous track
- `toggle_playback()` - Toggle play/pause
- `seek(position)` - Seek to position

#### Volume Control
- `get_volume()` - Get current volume
- `set_volume(level)` - Set volume level

#### Information
- `get_status()` - Get player status
- `get_current_song()` - Get current song info
- `get_playlist()` - Get current playlist
- `get_system_info()` - Get system information

## Configuration

### Default Settings
- Host: `localhost`
- Port: `80`
- Timeout: `10` seconds

### Custom Configuration
Create a `config.py` file based on `config_example.py`:

```python
MOODE_HOST = "192.168.1.100"
MOODE_PORT = 80
TIMEOUT = 15
```

## Examples

### Basic Usage
```bash
# Start playing music
python moode_cli_v2.py play

# Set volume to 50%
python moode_cli_v2.py volume 50

# Show what's currently playing
python moode_cli_v2.py current

# Test connection
python moode_cli_v2.py connection
```

### Remote Control
```bash
# Control a MoOde server on your network
python moode_cli_v2.py --host 192.168.1.100 status
python moode_cli_v2.py --host moode.local next
```

### Scripting
```bash
#!/bin/bash
# Simple script to start your morning playlist
python moode_cli_v2.py --host kitchen.local play
python moode_cli_v2.py --host kitchen.local volume 60
```

### Python Integration
```python
import time
from moode_controller_v2 import MoOdeAudioController

# Create controller
moode = MoOdeAudioController("192.168.1.100")

# Play for 30 seconds then pause
if moode.play():
    print("Started playback")
    time.sleep(30)
    moode.pause()
    print("Paused playback")

# Show current song info
song = moode.get_current_song()
if song:
    print(f"Title: {song.get('title')}")
    print(f"Artist: {song.get('artist')}")
    print(f"Album: {song.get('album')}")
```

## MoOde Audio Setup

This library works with [MoOde Audio](https://moodeaudio.org/), a popular audiophile-quality music player for Raspberry Pi.

### Requirements
- MoOde Audio 8.0+ (with REST API enabled)
- Network connectivity to MoOde server
- Python 3.7+

### MoOde Configuration
1. Ensure MoOde's web interface is accessible
2. Check that the REST API is enabled (usually enabled by default)
3. Note your MoOde server's IP address or hostname

## Troubleshooting

### Connection Issues
```bash
# Test basic connectivity
python moode_cli_v2.py connection

# Test with specific host
python moode_cli_v2.py --host 192.168.1.100 connection
```

### Common Problems

**"Cannot connect to MoOde server"**
- Verify MoOde is running and accessible
- Check IP address/hostname
- Ensure no firewall blocking port 80
- Try accessing MoOde web interface in browser

**"Command failed"**
- Check MoOde server logs
- Verify MoOde is not in an error state
- Try basic commands first (status, play)

**"Import errors"**
- Install required packages: `pip install -r requirements.txt`
- Check Python version (3.7+ required)

## Development

### Project Structure
```
├── moode_controller.py       # Original library
├── moode_controller_v2.py    # Updated library (recommended)
├── moode_cli.py             # Original CLI
├── moode_cli_v2.py          # Updated CLI (recommended)
├── test_moode.py            # Test script
├── requirements.txt         # Python dependencies
├── config_example.py        # Configuration template
├── README.md               # This file
└── hello_world.py          # Original sample file
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

### Testing
```python
# Test library functionality
python -c "from moode_controller_v2 import MoOdeAudioController; print('Import successful')"

# Test CLI
python moode_cli_v2.py --help

# Test connection
python moode_cli_v2.py connection
```

## License

This project is open source. Feel free to use, modify, and distribute.

## Related Projects

- [MoOde Audio](https://moodeaudio.org/) - The audio player this library controls
- [MPD](https://www.musicpd.org/) - The underlying music player daemon
- [Volumio](https://volumio.org/) - Alternative audiophile music player

## Support

For issues related to:
- **This library**: Create an issue in this repository
- **MoOde Audio**: Visit the [MoOde community forum](https://moodeaudio.org/forum/)
- **General setup**: Check the troubleshooting section above
