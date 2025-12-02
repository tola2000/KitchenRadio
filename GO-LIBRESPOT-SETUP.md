# go-librespot systemd service setup

## Problem
go-librespot crashes when Spotify marks the device as inactive, causing the KitchenRadio to lose Spotify connectivity.

## Solution
Configure go-librespot as a systemd service with automatic restart.

## Installation Steps

### 1. Copy the service file
```bash
sudo cp go-librespot.service /etc/systemd/system/
```

### 2. Update the service file with your configuration
Edit `/etc/systemd/system/go-librespot.service` and update:
- `User=tola2000` - Your username
- `ExecStart=/usr/local/bin/go-librespot` - Path to your go-librespot binary
- `--config-dir /home/tola2000/.config/go-librespot` - Your config directory

### 3. Reload systemd
```bash
sudo systemctl daemon-reload
```

### 4. Enable and start the service
```bash
# Enable auto-start on boot
sudo systemctl enable go-librespot

# Start the service now
sudo systemctl start go-librespot
```

### 5. Check status
```bash
# Check if service is running
sudo systemctl status go-librespot

# View logs
sudo journalctl -u go-librespot -f
```

## Service Features

- **Automatic Restart**: If go-librespot crashes, systemd will automatically restart it after 3 seconds
- **Boot Persistence**: Service starts automatically on system boot
- **Centralized Logging**: Logs are available via `journalctl`
- **Security Hardening**: Runs with limited privileges

## Monitoring

### Check service status:
```bash
sudo systemctl status go-librespot
```

### View recent logs:
```bash
sudo journalctl -u go-librespot -n 50
```

### Follow logs in real-time:
```bash
sudo journalctl -u go-librespot -f
```

### Restart service manually:
```bash
sudo systemctl restart go-librespot
```

## Troubleshooting

### Service won't start
1. Check the ExecStart path is correct: `which go-librespot`
2. Verify config directory exists
3. Check logs: `sudo journalctl -u go-librespot -n 100`

### Still getting crashes
The service will automatically restart, but you may want to:
1. Update go-librespot to the latest version
2. Check go-librespot GitHub issues for known bugs
3. Consider using a different Spotify Connect implementation

## Alternative: Run from command line with auto-restart

If you don't want to use systemd:

```bash
#!/bin/bash
while true; do
    go-librespot --config-dir ~/.config/go-librespot
    echo "go-librespot crashed, restarting in 3 seconds..."
    sleep 3
done
```

Save as `run-librespot.sh`, make executable (`chmod +x run-librespot.sh`), and run in a screen/tmux session.
