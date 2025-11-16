# Setup Raspberry Pi as Bluetooth Speaker (A2DP Sink)

This guide will configure your Raspberry Pi to act as a Bluetooth speaker, allowing devices to stream audio to it.

## Prerequisites

- Raspberry Pi with Bluetooth (Pi 3, Pi 4, Pi Zero W, etc.)
- Audio output configured (3.5mm jack, HDMI, USB audio, or DAC)
- Raspbian/Raspberry Pi OS

## Step 1: Install Required Packages

```bash
sudo apt-get update
sudo apt-get install -y \
    pulseaudio \
    pulseaudio-module-bluetooth \
    bluez \
    bluez-tools
```

## Step 2: Configure PulseAudio

### Edit PulseAudio daemon configuration:

```bash
sudo nano /etc/pulse/daemon.conf
```

Ensure these lines are uncommented and set:
```
resample-method = ffmpeg
enable-remixing = no
enable-lfe-remixing = no
default-sample-format = s32le
default-sample-rate = 48000
alternate-sample-rate = 44100
```

### Edit PulseAudio system mode (for headless operation):

```bash
sudo nano /etc/pulse/system.pa
```

Add at the end:
```
### Automatically switch to newly-connected devices
load-module module-switch-on-connect

### Enable Bluetooth A2DP Sink
load-module module-bluetooth-policy
load-module module-bluetooth-discover
```

## Step 3: Configure Bluetooth

### Make Bluetooth discoverable and pairable:

```bash
sudo bluetoothctl
```

In bluetoothctl, run:
```
power on
discoverable on
pairable on
agent on
default-agent
```

Type `exit` to leave bluetoothctl.

## Step 4: Auto-discover Mode

Create a script to keep Bluetooth always discoverable:

```bash
sudo nano /usr/local/bin/bt-speaker-setup
```

Paste the content (see `bt-speaker-setup.sh` script).

Make it executable:
```bash
sudo chmod +x /usr/local/bin/bt-speaker-setup
```

## Step 5: Create Systemd Service

Create a service to run at boot:

```bash
sudo nano /etc/systemd/system/bt-speaker.service
```

Paste the content (see `bt-speaker.service` file).

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bt-speaker.service
sudo systemctl start bt-speaker.service
```

## Step 6: Configure Audio Output

### For 3.5mm jack:
```bash
amixer cset numid=3 1
```

### For HDMI:
```bash
amixer cset numid=3 2
```

### Set volume:
```bash
amixer set Master 100%
```

## Step 7: Restart Services

```bash
sudo systemctl restart bluetooth
pulseaudio --kill
pulseaudio --start
```

## Step 8: Test Connection

1. Make your Pi discoverable:
   ```bash
   sudo bluetoothctl
   discoverable on
   ```

2. On your phone:
   - Go to Bluetooth settings
   - Find your Raspberry Pi (default name: `raspberrypi`)
   - Pair with it
   - Select it as audio output
   - Play music

3. Audio should now stream to your Pi!

## Troubleshooting

### Check Bluetooth status:
```bash
systemctl status bluetooth
```

### Check PulseAudio status:
```bash
pulseaudio --check -v
```

### List Bluetooth devices:
```bash
bluetoothctl devices
```

### Check audio devices:
```bash
pactl list sinks short
```

### View PulseAudio logs:
```bash
pulseaudio -vvv
```

### Reconnect Bluetooth:
```bash
sudo systemctl restart bluetooth
pulseaudio --kill
pulseaudio --start
```

## Integration with KitchenRadio

Once set up, you can use the `detect_bluez_stream.py` script to automatically:
- Detect when a device starts streaming
- Switch KitchenRadio source to Bluetooth
- Show Bluetooth device info on display

## Change Bluetooth Device Name

To make your Pi easier to find:

```bash
sudo nano /etc/hostname
```

Change to your desired name (e.g., `KitchenRadio`).

Also update:
```bash
sudo nano /etc/hosts
```

Replace `raspberrypi` with your new name.

Reboot:
```bash
sudo reboot
```

## Notes

- PulseAudio needs to be running for Bluetooth audio
- The Pi will appear as "KitchenRadio" (or whatever hostname you set) in Bluetooth devices
- Audio quality depends on your output device (DAC recommended for best quality)
- You can pair multiple devices, but only one can stream at a time
