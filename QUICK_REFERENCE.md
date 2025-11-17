# KitchenRadio Quick Reference

Quick commands and common operations for KitchenRadio.

## Starting the Daemon

### Hardware Only (Default)
```bash
python run_daemon.py
```

### With Web Interface
```bash
# Default port 5000
python run_daemon.py --web

# Custom port
python run_daemon.py --web --port 8080

# Web only (no hardware)
python run_daemon.py --web --no-hardware

# Custom combinations
python run_daemon.py --web --no-buttons    # Web + display only
python run_daemon.py --web --no-display    # Web + buttons only
```

### All Command-Line Options
```bash
python run_daemon.py --help

# Options:
#   --web              Enable web interface
#   --host HOST        Web server host (default: 0.0.0.0)
#   --port PORT        Web server port (default: 5000)
#   --no-hardware      Disable all hardware
#   --no-display       Disable display only
#   --no-buttons       Disable buttons only
#   --debug            Enable debug logging
```

## Stopping the Daemon

```bash
# Press Ctrl+C for graceful shutdown
```

## Configuration Commands

```bash
# View all configuration
python -m kitchenradio.config

# View pin assignments
python -m kitchenradio.config --pins

# View everything
python -m kitchenradio.config --all
```

## Systemd Service

```bash
# Start service
sudo systemctl start kitchenradio.service

# Stop service
sudo systemctl stop kitchenradio.service

# Restart service
sudo systemctl restart kitchenradio.service

# Check status
sudo systemctl status kitchenradio.service

# Enable auto-start on boot
sudo systemctl enable kitchenradio.service

# Disable auto-start
sudo systemctl disable kitchenradio.service

# View logs
sudo journalctl -u kitchenradio.service -f
```

## Web API Endpoints

All endpoints use `http://localhost:8080` (or your configured port)

### Status
```bash
curl http://localhost:8080/api/status
```

### Playback Control
```bash
# Play
curl -X POST http://localhost:8080/api/play

# Pause
curl -X POST http://localhost:8080/api/pause

# Stop
curl -X POST http://localhost:8080/api/stop

# Next track
curl -X POST http://localhost:8080/api/next

# Previous track
curl -X POST http://localhost:8080/api/previous
```

### Volume Control
```bash
# Set volume to 75%
curl -X POST http://localhost:8080/api/volume \
  -H "Content-Type: application/json" \
  -d '{"volume": 75}'

# Volume up
curl -X POST http://localhost:8080/api/volume/up

# Volume down
curl -X POST http://localhost:8080/api/volume/down
```

### Source Switching
```bash
# Switch to MPD
curl -X POST http://localhost:8080/api/source \
  -H "Content-Type: application/json" \
  -d '{"source": "mpd"}'

# Switch to Spotify
curl -X POST http://localhost:8080/api/source \
  -H "Content-Type: application/json" \
  -d '{"source": "librespot"}'

# Switch to Bluetooth
curl -X POST http://localhost:8080/api/source \
  -H "Content-Type: application/json" \
  -d '{"source": "bluetooth"}'
```

### Power Control
```bash
# Power on
curl -X POST http://localhost:8080/api/power/on

# Power off
curl -X POST http://localhost:8080/api/power/off

# Toggle power
curl -X POST http://localhost:8080/api/power/toggle
```

## Configuration Files

Quick edit locations:

```bash
# MPD settings
nano kitchenradio/config/mpd.py

# Spotify settings
nano kitchenradio/config/spotify.py

# Bluetooth settings
nano kitchenradio/config/bluetooth.py

# Display settings
nano kitchenradio/config/display.py

# Button pins
nano kitchenradio/config/buttons.py

# System settings
nano kitchenradio/config/system.py
```

## Common Configuration Changes

### Change MPD Server
Edit `kitchenradio/config/mpd.py`:
```python
HOST = '192.168.1.100'  # Your MPD server IP
PORT = 6600
```

### Disable Hardware (Development Mode)
Edit `kitchenradio/config/display.py`:
```python
USE_HARDWARE = False
```

Edit `kitchenradio/config/buttons.py`:
```python
USE_HARDWARE = False
```

### Change Default Source
Edit `kitchenradio/config/system.py`:
```python
DEFAULT_SOURCE = 'mpd'  # or 'librespot' or 'bluetooth'
```

### Enable Auto-Play on Startup
Edit `kitchenradio/config/system.py`:
```python
AUTO_START_PLAYBACK = True
POWER_ON_AT_STARTUP = True
```

## Troubleshooting Commands

### Check MPD Connection
```bash
telnet localhost 6600
# Should connect successfully
```

### Check I2C Devices
```bash
sudo i2cdetect -y 1
# Should show 0x27 (buttons) and 0x3C (display)
```

### Check SPI Devices
```bash
ls /dev/spidev*
# Should show /dev/spidev0.0 or similar
```

### Test Display Hardware
```bash
# Run with hardware disabled to test without physical display
python -c "from kitchenradio.config import display; print(display.USE_HARDWARE)"
```

### View Logs (Service Mode)
```bash
# Follow logs in real-time
sudo journalctl -u kitchenradio.service -f

# Last 50 lines
sudo journalctl -u kitchenradio.service -n 50

# Since specific time
sudo journalctl -u kitchenradio.service --since "10 minutes ago"
```

### Enable Debug Logging
Edit `kitchenradio/config/system.py`:
```python
LOG_LEVEL = 'DEBUG'  # Change from 'INFO'
```

## Hardware Button Functions

- **MPD / SPOTIFY / BLUETOOTH**: Switch audio source
- **POWER**: Short press = toggle power, Long press (3s) = system reboot
- **PLAY/PAUSE**: Toggle playback
- **STOP**: Stop playback
- **NEXT**: Next track
- **PREVIOUS**: Previous track
- **VOL+**: Increase volume
- **VOL-**: Decrease volume
- **MENU UP/DOWN**: Navigate menus
- **REPEAT**: Toggle repeat mode
- **SHUFFLE**: Toggle shuffle mode
- **SLEEP**: Set sleep timer
- **DISPLAY**: Cycle display modes

## Python API Quick Reference

```python
from kitchenradio.radio.kitchen_radio import KitchenRadio

# Initialize and start
radio = KitchenRadio()
radio.start()

# Source control
radio.switch_source('mpd')
radio.switch_source('librespot')
radio.switch_source('bluetooth')

# Playback control
radio.play()
radio.pause()
radio.stop()
radio.next()
radio.previous()

# Volume control
radio.set_volume(75)
radio.volume_up()
radio.volume_down()

# Status
status = radio.get_status()
print(status['title'])
print(status['artist'])
print(status['volume'])
print(status['state'])  # 'play', 'pause', or 'stop'

# Power
radio.power_on()
radio.power_off()
radio.toggle_power()

# Cleanup
radio.stop()
```

## File Locations

### Configuration
```
kitchenradio/config/
  ├── mpd.py
  ├── spotify.py
  ├── bluetooth.py
  ├── display.py
  ├── buttons.py
  └── system.py
```

### Main Scripts
```
run_daemon.py                          # Console daemon
kitchenradio/web/kitchen_radio_web.py  # Web interface
```

### Service File
```
/etc/systemd/system/kitchenradio.service
```

### Logs (when running as service)
```
sudo journalctl -u kitchenradio.service
```

## Quick Setup Checklist

- [ ] Install Python dependencies: `pip install -r requirements.txt`
- [ ] Configure MPD settings in `config/mpd.py`
- [ ] Configure Spotify settings in `config/spotify.py` (if using)
- [ ] Configure Bluetooth in `config/bluetooth.py` (if using)
- [ ] Test connection: `python run_daemon.py`
- [ ] Access web interface: `http://localhost:5000` (if using web mode)
- [ ] Set up systemd service (optional)
- [ ] Enable auto-start on boot (optional)

## Getting More Help

- Full documentation: See `USER_GUIDE.md`
- Configuration guide: See `CONFIG.md`
- Module documentation: See `kitchenradio/config/README.md`
- Issues: Check logs with `sudo journalctl -u kitchenradio.service -f`
