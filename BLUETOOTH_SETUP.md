# Bluetooth Setup for KitchenRadio

## Quick Installation (Raspberry Pi)

### 1. Install System Dependencies
```bash
sudo apt-get update
sudo apt-get install -y \
    python3-dbus \
    python3-gi \
    python3-gi-cairo \
    gir1.2-glib-2.0 \
    bluez \
    pulseaudio \
    pulseaudio-module-bluetooth
```

### 2. Install Python Dependencies
```bash
cd /home/tola2000/KitchenRadio
source venv/bin/activate  # If using virtual environment
pip install -r requirements.txt
```

### 3. Restart KitchenRadio
```bash
# Stop current instance (Ctrl+C if running)
# Then restart:
venv/bin/python3 -m kitchenradio.web.kitchen_radio_web
```

### 4. Verify Bluetooth is Available
Look for this in the startup logs:
```
INFO:kitchenradio.radio.kitchen_radio:Initializing Bluetooth backend...
✅ BluetoothController: D-Bus connection established
🔵 Bluetooth powered ON
INFO:kitchenradio.radio.kitchen_radio:✅ Bluetooth backend available
```

## Usage

1. **Press the Bluetooth source button** (pin 5 on MCP23017)
2. System enters **pairing mode** (discoverable for 60 seconds)
3. **Pair from your phone/device** - finds "KitchenRadio" or Pi hostname
4. Pairing code appears on phone - **automatically accepted** on Pi
5. Device connects and audio streams! 🎵

## Troubleshooting

### "No module named 'dbus'" Error
**Solution**: Install system packages first (step 1 above), then Python packages

### Bluetooth Backend Not Available
**Check**:
```bash
# Check if BlueZ service is running
systemctl status bluetooth

# Check if adapter is available
bluetoothctl show

# Check PulseAudio
pulseaudio --check
pactl list modules | grep bluetooth
```

### Device Pairs But Disconnects
**Solution**: Ensure PulseAudio Bluetooth modules are loaded:
```bash
pactl load-module module-bluetooth-discover
pactl load-module module-bluetooth-policy
```

## One-Line Install (All Steps)
```bash
sudo apt-get update && \
sudo apt-get install -y python3-dbus python3-gi python3-gi-cairo gir1.2-glib-2.0 bluez pulseaudio pulseaudio-module-bluetooth && \
cd /home/tola2000/KitchenRadio && \
source venv/bin/activate && \
pip install -r requirements.txt && \
echo "✅ Bluetooth dependencies installed! Restart KitchenRadio now."
```

## See Also
- [BLUETOOTH_INTEGRATION.md](BLUETOOTH_INTEGRATION.md) - Complete Bluetooth integration documentation
- [requirements.txt](requirements.txt) - Python package dependencies
