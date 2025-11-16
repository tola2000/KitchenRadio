#!/bin/bash
#
# Bluetooth Speaker Setup Script for Raspberry Pi
# Configures the Pi as an A2DP Bluetooth audio sink
#

set -e

echo "================================================"
echo "Raspberry Pi Bluetooth Speaker Setup"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

echo "📦 Step 1: Installing required packages..."
apt-get update
apt-get install -y \
    pulseaudio \
    pulseaudio-module-bluetooth \
    bluez \
    bluez-tools

echo ""
echo "⚙️  Step 2: Configuring PulseAudio..."

# Backup original configs
cp /etc/pulse/daemon.conf /etc/pulse/daemon.conf.backup 2>/dev/null || true
cp /etc/pulse/system.pa /etc/pulse/system.pa.backup 2>/dev/null || true

# Configure daemon.conf
cat >> /etc/pulse/daemon.conf << 'EOF'

# Bluetooth Audio Optimization
resample-method = ffmpeg
enable-remixing = no
enable-lfe-remixing = no
default-sample-format = s32le
default-sample-rate = 48000
alternate-sample-rate = 44100
EOF

# Configure system.pa for Bluetooth
cat >> /etc/pulse/system.pa << 'EOF'

### Bluetooth Audio Configuration
# Automatically switch to newly-connected devices
load-module module-switch-on-connect

# Enable Bluetooth A2DP Sink
load-module module-bluetooth-policy
load-module module-bluetooth-discover
EOF

echo ""
echo "🔧 Step 3: Creating Bluetooth speaker service script..."

# Create the bluetooth speaker setup script
cat > /usr/local/bin/bt-speaker-setup << 'EOF'
#!/bin/bash
# Initialize Bluetooth for speaker mode

# Wait for Bluetooth to be ready
sleep 5

# Configure Bluetooth
bluetoothctl << BTCTL
power on
discoverable on
pairable on
agent on
default-agent
BTCTL

# Set device class to audio
hciconfig hci0 class 0x200420

# Restart PulseAudio
pulseaudio --kill 2>/dev/null || true
sleep 2
pulseaudio --start --log-target=syslog

echo "Bluetooth speaker mode activated"
EOF

chmod +x /usr/local/bin/bt-speaker-setup

echo ""
echo "🚀 Step 4: Creating systemd service..."

# Create systemd service
cat > /etc/systemd/system/bt-speaker.service << 'EOF'
[Unit]
Description=Bluetooth Speaker Service
After=bluetooth.service pulseaudio.service
Requires=bluetooth.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/bt-speaker-setup
RemainAfterExit=yes
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable bt-speaker.service

echo ""
echo "🔊 Step 5: Configuring audio output..."

# Set audio output to 3.5mm jack (change to 2 for HDMI)
amixer cset numid=3 1 2>/dev/null || echo "⚠️  Could not set audio output (may need manual configuration)"

# Set volume
amixer set Master 80% 2>/dev/null || echo "⚠️  Could not set volume"

echo ""
echo "♻️  Step 6: Restarting services..."

# Restart Bluetooth
systemctl restart bluetooth

# Kill and restart PulseAudio
pulseaudio --kill 2>/dev/null || true
sleep 2
su - $SUDO_USER -c "pulseaudio --start" 2>/dev/null || pulseaudio --start

# Start the bt-speaker service
systemctl start bt-speaker.service

echo ""
echo "================================================"
echo "✅ Bluetooth Speaker Setup Complete!"
echo "================================================"
echo ""
echo "Your Raspberry Pi is now configured as a Bluetooth speaker."
echo ""
echo "Next steps:"
echo "1. On your phone/device, search for Bluetooth devices"
echo "2. Look for 'raspberrypi' (or your hostname)"
echo "3. Pair with the device"
echo "4. Select it as audio output"
echo "5. Play music - it should stream to your Pi!"
echo ""
echo "To check status:"
echo "  sudo systemctl status bt-speaker"
echo "  sudo systemctl status bluetooth"
echo ""
echo "To make always discoverable:"
echo "  sudo bluetoothctl"
echo "  discoverable on"
echo "  pairable on"
echo ""
echo "To change device name, edit /etc/hostname and /etc/hosts"
echo ""
echo "⚠️  You may need to reboot for all changes to take effect:"
echo "  sudo reboot"
echo ""
