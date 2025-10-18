# KitchenRadio systemd service files

## Installation

1. Copy the service file to systemd directory:
```bash
sudo cp kitchenradio.service /etc/systemd/system/
```

2. Create user and directories:
```bash
sudo useradd -r -s /bin/false -d /opt/kitchenradio kitchenradio
sudo usermod -a -G audio kitchenradio
sudo mkdir -p /opt/kitchenradio
sudo chown -R kitchenradio:audio /opt/kitchenradio
```

3. Install KitchenRadio to /opt/kitchenradio:
```bash
sudo cp -r /path/to/your/kitchenradio/* /opt/kitchenradio/
sudo chown -R kitchenradio:audio /opt/kitchenradio
```

4. Install Python dependencies:
```bash
cd /opt/kitchenradio
sudo -u kitchenradio pip3 install -r requirements.txt
```

5. Configure environment:
```bash
sudo -u kitchenradio cp .env.example .env
sudo -u kitchenradio nano .env  # Edit configuration
```

6. Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable kitchenradio
sudo systemctl start kitchenradio
```

## Service Management

### Start/Stop/Restart
```bash
sudo systemctl start kitchenradio
sudo systemctl stop kitchenradio
sudo systemctl restart kitchenradio
```

### Check Status
```bash
sudo systemctl status kitchenradio
```

### View Logs
```bash
sudo journalctl -u kitchenradio -f
```

### Check Service Configuration
```bash
sudo systemctl show kitchenradio
```

## Configuration

The service reads configuration from `/opt/kitchenradio/.env`.

### For MPD Backend
```bash
sudo systemctl edit kitchenradio
```

Add:
```ini
[Service]
ExecStart=
ExecStart=/usr/bin/python3 /opt/kitchenradio/kitchen_radio.py --backend mpd
```

### For Librespot Backend
```bash
sudo systemctl edit kitchenradio
```

Add:
```ini
[Service]
ExecStart=
ExecStart=/usr/bin/python3 /opt/kitchenradio/kitchen_radio.py --backend librespot
```

## Troubleshooting

### Check if service is running
```bash
sudo systemctl is-active kitchenradio
```

### Check service logs for errors
```bash
sudo journalctl -u kitchenradio --since "1 hour ago"
```

### Test daemon manually
```bash
sudo -u kitchenradio python3 /opt/kitchenradio/kitchen_radio.py --debug
```

### Check permissions
```bash
sudo -u kitchenradio ls -la /opt/kitchenradio/
```
