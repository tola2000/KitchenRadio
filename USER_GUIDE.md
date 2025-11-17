# KitchenRadio - Multi-Source Audio Controller

A comprehensive Python-based audio controller supporting multiple audio sources with physical hardware interface for Raspberry Pi. Perfect for building your own kitchen or home radio system.

## Features

- 🎵 **Multi-Source Audio**: MPD, Spotify (Librespot), and Bluetooth
- 🔊 **Volume Control**: Unified volume control across all sources
- ⏯️ **Playback Control**: Play, pause, stop, next, previous
- 📻 **Radio Streams**: Support for internet radio via MPD
- 🔵 **Bluetooth Audio**: Auto-pairing and A2DP streaming
- 🎚️ **Physical Controls**: Button interface via MCP23017 GPIO expander
- 🖥️ **OLED Display**: Real-time status on SSD1322 256x64 OLED
- 🌐 **Web Frontend**: Optional web-based control interface
- 🔄 **Real-Time Monitoring**: Live status updates and event notifications
- 🔌 **Modular Configuration**: Easy customization via config files

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Daemon](#running-the-daemon)
  - [Without Web Frontend](#without-web-frontend)
  - [With Web Frontend](#with-web-frontend)
- [Hardware Setup](#hardware-setup)
- [Usage Examples](#usage-examples)
- [Development](#development)
- [Documentation](#documentation)

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure (edit config files)
# See kitchenradio/config/ directory

# 3. Run daemon (hardware controls only)
python run_daemon.py

# OR run with web frontend
python run_daemon.py --web --port 8080

# OR run web only (no hardware)
python run_daemon.py --web --no-hardware --port 8080
```

## Installation

### System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux (Raspberry Pi OS recommended) or Windows (for development)
- **Hardware** (optional):
  - Raspberry Pi (3/4/Zero 2 W recommended)
  - SSD1322 256x64 OLED display (SPI)
  - MCP23017 GPIO expander (I2C)
  - Physical buttons

### Dependencies Installation

#### Basic Installation (All Platforms)

```bash
# Clone the repository
git clone https://github.com/yourusername/KitchenRadio.git
cd KitchenRadio

# Install Python dependencies
pip install -r requirements.txt
```

#### Raspberry Pi with Hardware Support

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev python3-smbus \
    i2c-tools python3-pil python3-numpy

# For Bluetooth support
sudo apt-get install -y python3-dbus python3-gi python3-gi-cairo \
    gir1.2-glib-2.0 bluez pulseaudio pulseaudio-module-bluetooth

# Install Python dependencies
pip install -r requirements.txt

# Enable I2C and SPI
sudo raspi-config
# Navigate to: Interface Options -> I2C -> Enable
# Navigate to: Interface Options -> SPI -> Enable
```

#### Verify Hardware Detection

```bash
# Check I2C devices
sudo i2cdetect -y 1

# You should see:
# - 0x27: MCP23017 (button controller)
# - 0x3C: SSD1322 (display)
```

## Configuration

KitchenRadio uses a modular configuration system. Configuration files are in `kitchenradio/config/`:

### Quick Configuration

```bash
# View current configuration
python -m kitchenradio.config

# View pin assignments
python -m kitchenradio.config --pins

# View everything
python -m kitchenradio.config --all
```

### Configuration Files

Edit these files to customize your setup:

- **`config/mpd.py`** - MPD server settings
- **`config/spotify.py`** - Spotify/Librespot settings
- **`config/bluetooth.py`** - Bluetooth settings
- **`config/display.py`** - Display hardware settings
- **`config/buttons.py`** - Button pin assignments
- **`config/system.py`** - System-wide settings

### Example: MPD Configuration

Edit `kitchenradio/config/mpd.py`:

```python
HOST = '192.168.1.100'  # Your MPD server IP
PORT = 6600
PASSWORD = None         # Set if MPD requires authentication
DEFAULT_VOLUME = 50
TIMEOUT = 10
```

### Example: Enable/Disable Features

Edit `kitchenradio/config/system.py`:

```python
ENABLE_MPD = True
ENABLE_SPOTIFY = True
ENABLE_BLUETOOTH = False  # Disable if not using Bluetooth

DEFAULT_SOURCE = 'mpd'  # Default audio source on startup
POWER_ON_AT_STARTUP = True
```

See [CONFIG.md](CONFIG.md) for detailed configuration documentation.

## Running the Daemon

The daemon now has unified startup with command-line options to enable/disable components.

### Mode 1: Hardware Controls Only (Default)

Run the daemon with physical hardware controls only (buttons + display):

```bash
python run_daemon.py
```

**Output:**
```
================================================================================
KitchenRadio Daemon Starting
================================================================================
Configuration:
  MPD: localhost:6600
  Librespot: localhost:4370
  Bluetooth: KitchenRadio
  Default Source: mpd
  Power on at startup: True

Controllers:
  Display: Enabled
  Buttons: Enabled
  Web Interface: Disabled

Initializing KitchenRadio core...
✓ KitchenRadio core initialized
Initializing Display Controller...
✓ Display Controller initialized
Initializing Button Controller...
✓ Button Controller initialized

================================================================================
KitchenRadio Daemon Running
Press Ctrl+C to stop
================================================================================
```

**Features Available:**
- ✅ Physical button controls
- ✅ OLED display
- ✅ All audio sources (MPD, Spotify, Bluetooth)
- ❌ No web interface

### Mode 2: With Web Frontend

Run the daemon with web-based control interface:

```bash
# Run with web interface on default port 5000
python run_daemon.py --web

# Run on custom port
python run_daemon.py --web --port 8080

# Run on all network interfaces
python run_daemon.py --web --host 0.0.0.0 --port 8080
```

**Output:**
```
================================================================================
KitchenRadio Daemon Starting
================================================================================
Configuration:
  MPD: localhost:6600
  Librespot: localhost:4370
  Bluetooth: KitchenRadio
  Default Source: mpd
  Power on at startup: True

Controllers:
  Display: Enabled
  Buttons: Enabled
  Web Interface: Enabled
  Web URL: http://0.0.0.0:8080

Initializing KitchenRadio core...
✓ KitchenRadio core initialized
Initializing Display Controller...
✓ Display Controller initialized
Initializing Button Controller...
✓ Button Controller initialized
Initializing Web Interface...
✓ Web Interface initialized
  Access at: http://0.0.0.0:8080

================================================================================
KitchenRadio Daemon Running
Press Ctrl+C to stop
================================================================================
```

**Features Available:**
- ✅ Physical button controls
- ✅ OLED display
- ✅ Web interface on http://localhost:8080
- ✅ REST API for remote control
- ✅ All audio sources (MPD, Spotify, Bluetooth)

**Web Interface Features:**
- 🎵 Source selection (MPD, Spotify, Bluetooth)
- ⏯️ Playback controls (play, pause, stop, next, previous)
- 🔊 Volume control
- 📊 Real-time status display
- 🎚️ Now playing information
- 📱 Mobile-friendly responsive design

**Accessing the Web Interface:**
- **Local**: http://localhost:8080
- **Network**: http://YOUR_PI_IP:8080
- **Example**: http://192.168.1.100:8080

### Mode 3: Web Only (No Hardware)

Run daemon with web interface only, no physical hardware:

```bash
python run_daemon.py --web --no-hardware --port 8080
```

**Features Available:**
- ❌ No physical button controls
- ❌ No OLED display
- ✅ Web interface
- ✅ REST API
- ✅ All audio sources

### Mode 4: Custom Combinations

You can mix and match components:

```bash
# Web + Display, no buttons
python run_daemon.py --web --no-buttons

# Web + Buttons, no display
python run_daemon.py --web --no-display

# Hardware only, no web
python run_daemon.py

# Everything enabled (default with --web)
python run_daemon.py --web --port 8080
```

### Command-Line Options

```bash
# View all options
python run_daemon.py --help

Options:
  --web                 Enable web interface
  --host HOST           Web server host (default: 0.0.0.0)
  --port PORT           Web server port (default: 5000)
  --no-hardware         Disable all hardware (display + buttons)
  --no-display          Disable display controller
  --no-buttons          Disable button controller
  --debug               Enable debug logging
  --help                Show help message

Examples:
  python run_daemon.py                          # Hardware only
  python run_daemon.py --web                    # Hardware + Web
  python run_daemon.py --web --no-hardware      # Web only
  python run_daemon.py --web --port 8080        # Custom port
```

### Running as a System Service (Linux)

For automatic startup on boot:

1. **Create service file:**

```bash
sudo nano /etc/systemd/system/kitchenradio.service
```

2. **Add service configuration:**

```ini
[Unit]
Description=KitchenRadio Audio Controller
After=network.target mpd.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/KitchenRadio
ExecStart=/usr/bin/python3 /home/pi/KitchenRadio/run_daemon.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

3. **Enable and start service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable kitchenradio.service
sudo systemctl start kitchenradio.service

# Check status
sudo systemctl status kitchenradio.service

# View logs
sudo journalctl -u kitchenradio.service -f
```

### Running with Web Frontend as Service

For web interface as a service:

```ini
[Unit]
Description=KitchenRadio Web Interface
After=network.target mpd.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/KitchenRadio
ExecStart=/usr/bin/python3 -m kitchenradio.web.kitchen_radio_web --port 8080
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Hardware Setup

### Required Components

- **Raspberry Pi** (3/4/Zero 2 W)
- **SSD1322 256x64 OLED Display** (SPI interface)
- **MCP23017 GPIO Expander** (I2C interface)
- **17 Push Buttons** (connected to MCP23017)
- **Power Supply** (5V, 3A recommended)

### Pin Connections

See [CONFIG.md](CONFIG.md) for detailed pin assignments.

**Display (SPI):**
- DC (Data/Command): GPIO 25
- RST (Reset): GPIO 24
- SPI Port: 0, Device: 0

**Button Controller (I2C):**
- I2C Address: 0x27 (MCP23017)
- 17 buttons on pins 0-15

### Button Layout

```
┌─────────────────────────────────────┐
│  [MPD]  [SPOTIFY]  [BLUETOOTH]      │  Source Selection
├─────────────────────────────────────┤
│  [▲]           DISPLAY          [▼]  │  Menu Navigation
├─────────────────────────────────────┤
│  [SLEEP] [REPEAT] [SHUFFLE] [MODE]  │  Functions
├─────────────────────────────────────┤
│  [|◄]    [▶||]    [■]    [►|]      │  Transport
├─────────────────────────────────────┤
│  [VOL-]       [POWER]       [VOL+]  │  Volume & Power
└─────────────────────────────────────┘
```

## Usage Examples

### Python API Usage

```python
from kitchenradio.radio.kitchen_radio import KitchenRadio

# Initialize
radio = KitchenRadio()
radio.start()

# Switch to MPD
radio.switch_source('mpd')
radio.play()
radio.set_volume(75)

# Switch to Spotify
radio.switch_source('librespot')

# Switch to Bluetooth
radio.switch_source('bluetooth')

# Get status
status = radio.get_status()
print(f"Playing: {status['title']} by {status['artist']}")
print(f"Volume: {status['volume']}%")

# Cleanup
radio.stop()
```

### Web API Examples

```bash
# Get status
curl http://localhost:8080/api/status

# Play
curl -X POST http://localhost:8080/api/play

# Pause
curl -X POST http://localhost:8080/api/pause

# Set volume
curl -X POST http://localhost:8080/api/volume -d '{"volume": 75}'

# Switch source
curl -X POST http://localhost:8080/api/source -d '{"source": "mpd"}'

# Next track
curl -X POST http://localhost:8080/api/next

# Previous track
curl -X POST http://localhost:8080/api/previous
```

## Development

### Project Structure

```
KitchenRadio/
├── kitchenradio/
│   ├── config/              # Modular configuration
│   │   ├── mpd.py
│   │   ├── spotify.py
│   │   ├── bluetooth.py
│   │   ├── display.py
│   │   ├── buttons.py
│   │   └── system.py
│   ├── mpd/                 # MPD client and controller
│   ├── spotify/             # Librespot client
│   ├── bluetooth/           # Bluetooth audio controller
│   ├── radio/               # Main radio daemon
│   │   ├── kitchen_radio.py
│   │   └── hardware/        # Hardware controllers
│   │       ├── button_controller.py
│   │       ├── display_controller.py
│   │       └── display_interface.py
│   └── web/                 # Web interface
│       └── kitchen_radio_web.py
├── run_daemon.py            # Main daemon script
├── requirements.txt         # Python dependencies
├── CONFIG.md                # Configuration guide
└── README.md                # This file
```

### Running Tests

```bash
# Test MPD connection
python test_moode.py

# Test volume control
python test_volume.py

# Debug status
python debug_status.py
```

### Development Mode (No Hardware)

For development without physical hardware:

Edit `kitchenradio/config/display.py`:
```python
USE_HARDWARE = False  # Use display emulator
```

Edit `kitchenradio/config/buttons.py`:
```python
USE_HARDWARE = False  # Software-only mode
```

Then run:
```bash
python run_daemon.py  # No hardware required
```

## Documentation

- **[CONFIG.md](CONFIG.md)** - Complete configuration guide
- **[config/README.md](kitchenradio/config/README.md)** - Modular config documentation
- **[CONFIGURATION_REFACTORING.md](CONFIGURATION_REFACTORING.md)** - Config architecture
- **[BLUETOOTH_SETUP.md](BLUETOOTH_SETUP.md)** - Bluetooth setup guide

## Troubleshooting

### Common Issues

**1. Cannot connect to MPD**
```bash
# Check MPD is running
systemctl status mpd

# Test connection
telnet localhost 6600
```

**2. Display not working**
```bash
# Check SPI is enabled
ls /dev/spidev*

# Test with emulator mode
# Set USE_HARDWARE = False in config/display.py
```

**3. Buttons not responding**
```bash
# Check I2C devices
sudo i2cdetect -y 1

# Verify MCP23017 at address 0x27
```

**4. Web interface not accessible**
```bash
# Check firewall
sudo ufw allow 8080/tcp

# Test locally first
curl http://localhost:8080
```

### Getting Help

- Check the logs: `sudo journalctl -u kitchenradio.service -f`
- Enable debug mode: Set `LOG_LEVEL = 'DEBUG'` in `config/system.py`
- Run in console mode to see output: `python run_daemon.py`

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

MIT License - see LICENSE file for details.

## Credits

Created for home automation and kitchen radio systems. Inspired by vintage radios with modern technology.
