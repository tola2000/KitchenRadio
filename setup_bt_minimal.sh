#!/bin/bash
#
# Minimal Bluetooth Audio Setup
# Since manual pairing works, this just ensures services stay running
#

set -e

echo "🔵 Minimal Bluetooth Audio Setup"
echo "================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

echo "1️⃣  Ensuring PulseAudio Bluetooth module..."

# Install if not present
apt-get update
apt-get install -y pulseaudio-module-bluetooth

echo ""
echo "2️⃣  Configuring Bluetooth to stay discoverable..."

# Backup config
cp /etc/bluetooth/main.conf /etc/bluetooth/main.conf.backup 2>/dev/null || true

# Simple config changes
sed -i 's/#DiscoverableTimeout = 0/DiscoverableTimeout = 0/' /etc/bluetooth/main.conf
sed -i 's/#PairableTimeout = 0/PairableTimeout = 0/' /etc/bluetooth/main.conf

echo ""
echo "3️⃣  Creating startup script to enable discoverable mode..."

cat > /usr/local/bin/bt-discoverable << 'EOF'
#!/bin/bash
# Keep Bluetooth discoverable

sleep 5

bluetoothctl << BTCTL
power on
discoverable on
pairable on
BTCTL

# Set audio device class
hciconfig hci0 class 0x200420
EOF

chmod +x /usr/local/bin/bt-discoverable

# Create systemd service
cat > /etc/systemd/system/bt-discoverable.service << 'EOF'
[Unit]
Description=Bluetooth Discoverable Mode
After=bluetooth.service
Requires=bluetooth.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/bt-discoverable
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable bt-discoverable.service

echo ""
echo "4️⃣  Restarting services..."

systemctl restart bluetooth
systemctl start bt-discoverable.service

# Restart PulseAudio
pulseaudio --kill 2>/dev/null || true
sleep 2
su - $SUDO_USER -c "pulseaudio --start" 2>/dev/null || pulseaudio --start

echo ""
echo "✅ Setup complete!"
echo ""
echo "📱 To pair your phone:"
echo "   1. Run: sudo ./pair_bluetooth_device.sh"
echo "   2. Or manually:"
echo "      sudo bluetoothctl"
echo "      scan on"
echo "      pair <MAC>"
echo "      trust <MAC>"
echo "      connect <MAC>"
echo ""
echo "🎵 To detect streaming:"
echo "   python3 detect_bluez_stream.py"
echo ""
