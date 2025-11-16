# Bluetooth Debugging Guide for KitchenRadio

This guide shows you how to track Bluetooth events and debug audio issues.

## Quick Start: 3-Terminal Setup

### Terminal 1: Run KitchenRadio
```bash
cd ~/KitchenRadio
python3 -m kitchenradio.daemon
```

### Terminal 2: Monitor Bluetooth Events
```bash
cd ~/KitchenRadio
python3 monitor_bluetooth.py
```

### Terminal 3: Watch Logs
```bash
tail -f /var/log/syslog | grep -i bluetooth
# or
journalctl -f | grep -i blue
```

## Debugging Tools

### 1. Python Bluetooth Monitor (Recommended)
Our custom monitor shows high-level events:

```bash
python3 monitor_bluetooth.py
```

**What it shows:**
- Device connections/disconnections (🟢/🔴)
- Pairing events (✅/❌)
- Service profile changes (A2DP, HSP, etc.)
- Signal strength (📶)
- Trust status changes (🔐/🔓)

### 2. bluetoothctl (Interactive)
Built-in Bluetooth control utility:

```bash
# Start interactive mode
bluetoothctl

# Inside bluetoothctl:
devices                  # List all devices
paired-devices          # List paired devices
info <MAC>              # Show device details
show                    # Show adapter info

# Monitor mode (separate terminal)
bluetoothctl --monitor
```

### 3. btmon (Low-Level HCI Traffic)
Shows raw Bluetooth HCI commands:

```bash
# Install if needed
sudo apt-get install bluez

# Monitor all HCI traffic
sudo btmon

# Filter for your device
sudo btmon | grep -i "iphone"
```

**What it shows:**
- Connection requests
- Authentication/pairing
- Profile negotiations (A2DP, AVRCP)
- Audio codec selection

### 4. PulseAudio Monitoring
Track audio sink changes:

```bash
# Monitor PulseAudio events
pactl subscribe

# List Bluetooth sinks
pactl list sinks short | grep bluez

# Get detailed sink info
pactl list sinks | grep -A 20 bluez

# Check module status
pactl list modules short | grep bluetooth
```

### 5. D-Bus Monitor
Watch D-Bus messages (very verbose):

```bash
# Monitor all BlueZ messages
dbus-monitor --system "sender='org.bluez'"

# Monitor specific interface
dbus-monitor --system "interface='org.bluez.Device1'"
```

## Common Issues and How to Debug

### Issue: Audio Stops After 1 Second

**Debug steps:**
1. Check if sink is suspended:
```bash
pactl list sinks | grep -A 5 "State:"
```
If you see `State: SUSPENDED`, that's the problem!

2. Monitor PulseAudio events while playing:
```bash
pactl subscribe
```
Then play audio and watch for "suspend" events.

3. Check for module-suspend-on-idle:
```bash
pactl list modules short | grep suspend
```

**Fix:**
```bash
pactl unload-module module-suspend-on-idle
```

### Issue: Volume Not Working

**Debug steps:**
1. Check if Bluetooth sink exists:
```bash
pactl list sinks short | grep bluez
```

2. Try setting volume manually:
```bash
pactl set-sink-volume <sink-name> 50%
```

3. Check if sink is muted:
```bash
pactl list sinks | grep -A 2 "Mute:"
```

### Issue: Device Connects But No Audio

**Debug steps:**
1. Check A2DP profile is active:
```bash
pactl list cards | grep -A 20 bluez
```
Look for `Active Profile: a2dp_sink`

2. Switch profile if needed:
```bash
pactl set-card-profile <card-name> a2dp_sink
```

3. Check if default sink is correct:
```bash
pactl info | grep "Default Sink"
```

## Enable Debug Logging

### KitchenRadio Debug Mode
Edit your config and set:
```python
LOG_LEVEL = 'DEBUG'
```

Or run with debug flag:
```bash
python3 -m kitchenradio.daemon --log-level DEBUG
```

### BlueZ Debug Logging
Edit `/lib/systemd/system/bluetooth.service`:
```ini
ExecStart=/usr/lib/bluetooth/bluetoothd -d
```

Then restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart bluetooth
```

### PulseAudio Debug Logging
Edit `/etc/pulse/daemon.conf`:
```ini
log-level = debug
```

Restart:
```bash
pulseaudio -k
pulseaudio --start
```

## Useful Commands Reference

### Bluetooth
```bash
# Check Bluetooth status
systemctl status bluetooth
hciconfig -a

# Restart Bluetooth
sudo systemctl restart bluetooth

# Check paired devices
bluetoothctl paired-devices

# Remove device
bluetoothctl remove <MAC>
```

### Audio
```bash
# Check audio is playing
pactl list sink-inputs short

# Force audio to Bluetooth
pactl set-default-sink <bluez-sink-name>

# Check volume
pactl get-sink-volume <sink-name>

# List audio cards
pactl list cards short
```

### System
```bash
# Check for errors
journalctl -xe | grep -i bluetooth
dmesg | grep -i bluetooth

# Monitor system load
htop
```

## Log Files to Check

```bash
# System log
/var/log/syslog

# Bluetooth messages
/var/log/messages | grep blue

# PulseAudio log
~/.config/pulse/*.log

# KitchenRadio log (if configured)
/var/log/kitchenradio.log
```

## Pro Tips

1. **Use tmux/screen** to manage multiple terminals:
```bash
tmux new -s debug
# Ctrl+B then C to create new window
# Ctrl+B then number to switch
```

2. **Save logs for analysis**:
```bash
python3 monitor_bluetooth.py > bluetooth_events.log 2>&1
```

3. **Filter noise**:
```bash
pactl subscribe | grep -v "on client"
```

4. **Test audio**:
```bash
# Generate test tone
speaker-test -t sine -f 440 -c 2
```

## Example Debug Session

```bash
# Terminal 1: Start monitoring
python3 monitor_bluetooth.py

# Terminal 2: Watch PulseAudio
pactl subscribe | grep -v "on client"

# Terminal 3: Run KitchenRadio
python3 -m kitchenradio.daemon --log-level DEBUG

# Now connect your iPhone and play music
# Watch all three terminals for events
```

## Getting Help

If issues persist, capture:
1. Output from `monitor_bluetooth.py`
2. Output from `pactl subscribe`
3. KitchenRadio debug logs
4. Output from `bluetoothctl info <MAC>`
5. Output from `pactl list sinks | grep -A 30 bluez`

Then share these logs for analysis.
