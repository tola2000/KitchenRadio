# KitchenRadio - MPD Controller

A Python library for controlling MPD (Music Player Daemon) servers, designed for kitchen/home automation use.

## Features

- 🎵 Monitor now playing tracks
- 🔊 Volume control
- ⏯️ Playback control
- 📻 Radio stream support
- 🌐 Remote host support
- 🔄 Real-time status monitoring

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd KitchenRadio

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

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
