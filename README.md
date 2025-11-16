# KitchenRadio - MPD Controller

A Python library for controlling MPD (Music Player Daemon) servers, designed for kitchen/home automation use.

## Features

- 🎵 **Multi-Source Audio**: MPD, Spotify (Librespot), and Bluetooth
- 🔊 Volume control across all sources
- ⏯️ Unified playback control
- 📻 Radio stream support (MPD)
- 🔵 **Bluetooth Audio**: Auto-pairing and streaming
- 🌐 Remote host support
- 🔄 Real-time status monitoring
- 🖥️ Hardware display and button support (Raspberry Pi)

## Installation

### Basic Installation
```bash
# Clone the repository
git clone <repository-url>
cd KitchenRadio

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Bluetooth Support (Raspberry Pi)
For Bluetooth audio source, install system dependencies first:
```bash
sudo apt-get install -y python3-dbus python3-gi python3-gi-cairo gir1.2-glib-2.0 bluez pulseaudio pulseaudio-module-bluetooth
pip install -r requirements.txt
```

See [BLUETOOTH_SETUP.md](BLUETOOTH_SETUP.md) for detailed setup instructions.

## Usage

```python
from kitchenradio import KitchenRadioClient, PlaybackController, NowPlayingMonitor

# Create client and connect
client = KitchenRadioClient(host="192.168.1.4", port=6600)
client.connect()

# Control playback
controller = PlaybackController(client)
controller.play("http://stream.example.com/radio.mp3")
controller.set_volume(50)

# Monitor now playing
monitor = NowPlayingMonitor(client)
monitor.add_callback('track_started', lambda track: print(f"Now playing: {track['name']}"))
monitor.start_monitoring()
```

## Configuration

Copy `config/config_example.py` to `config/config.py` and customize:

```python
MPD_HOST = "192.168.1.4"
MPD_PORT = 6600
MPD_PASSWORD = None  # Set if required
DEFAULT_VOLUME = 50
```

## Project Structure

```
KitchenRadio/
├── src/kitchenradio/          # Main package
│   └── mpd/                   # MPD client modules
│       ├── client.py          # MPD client wrapper
│       ├── controller.py      # Playback controller
│       ├── monitor.py         # Status monitor
│       └── __init__.py        # Module exports
├── tests/                     # Test suite
├── examples/                  # Example scripts
├── config/                    # Configuration files
├── requirements.txt           # Dependencies
├── setup.py                   # Package setup
└── README.md                  # This file
```

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python tests/test_mpd_basic.py

# Test connection
python examples/test_mpd_connection.py

# Run linting
flake8 src/

# Format code
black src/
```

## License

MIT License - see LICENSE file for details.
