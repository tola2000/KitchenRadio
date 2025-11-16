#!/bin/bash
#
# Bluetooth Pairing Fix Script
# Fixes immediate disconnection after pairing
#

set -e

echo "================================================"
echo "Bluetooth Pairing Fix for Raspberry Pi"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

echo "🔧 Fixing Bluetooth pairing issues..."
echo ""

# Step 1: Stop services
echo "1️⃣  Stopping services..."
systemctl stop bluetooth
pulseaudio --kill 2>/dev/null || true
sleep 2

# Step 2: Clear pairing cache
echo "2️⃣  Clearing Bluetooth pairing cache..."
rm -rf /var/lib/bluetooth/*/cache 2>/dev/null || true
echo "   Cache cleared"

# Step 3: Configure Bluetooth for audio
echo "3️⃣  Configuring Bluetooth daemon..."

# Backup original config
cp /etc/bluetooth/main.conf /etc/bluetooth/main.conf.backup 2>/dev/null || true

# Configure main.conf for better compatibility
cat > /etc/bluetooth/main.conf << 'EOF'
[General]
Name = KitchenRadio
Class = 0x200420
DiscoverableTimeout = 0
PairableTimeout = 0
AlwaysPairable = true
FastConnectable = true

[Policy]
AutoEnable = true
ReconnectAttempts = 7
ReconnectIntervals = 1, 2, 4, 8, 16, 32, 64

[GATT]
Cache = always
EOF

echo "   Bluetooth daemon configured"

# Step 4: Configure PulseAudio for Bluetooth
echo "4️⃣  Configuring PulseAudio..."

# Create PulseAudio config directory if it doesn't exist
mkdir -p /home/$SUDO_USER/.config/pulse

# Configure default.pa
cat > /home/$SUDO_USER/.config/pulse/default.pa << 'EOF'
#!/usr/bin/pulseaudio -nF

# Load driver modules
.include /etc/pulse/default.pa

# Bluetooth support
.ifexists module-bluetooth-discover.so
load-module module-bluetooth-discover
.endif

.ifexists module-bluetooth-policy.so
load-module module-bluetooth-policy auto_switch=2
.endif

# Automatically switch to newly connected devices
load-module module-switch-on-connect

# Trust Bluetooth devices after pairing
load-module module-bluetooth-discover trust=yes
EOF

chown -R $SUDO_USER:$SUDO_USER /home/$SUDO_USER/.config/pulse

# Also configure system-wide
cat >> /etc/pulse/system.pa << 'EOF'

# Bluetooth fixes
.ifexists module-bluetooth-discover.so
load-module module-bluetooth-discover trust=yes
.endif

.ifexists module-bluetooth-policy.so
load-module module-bluetooth-policy auto_switch=2
.endif

load-module module-switch-on-connect
EOF

echo "   PulseAudio configured"

# Step 5: Set up udev rule for automatic trust
echo "5️⃣  Setting up automatic Bluetooth device trust..."

cat > /etc/udev/rules.d/99-bluetooth-trust.rules << 'EOF'
# Automatically trust Bluetooth devices after pairing
ACTION=="add", SUBSYSTEM=="bluetooth", RUN+="/usr/local/bin/bluetooth-trust-device"
EOF

cat > /usr/local/bin/bluetooth-trust-device << 'EOF'
#!/bin/bash
# Trust newly paired Bluetooth devices

DEVICE_MAC=$1

if [ -n "$DEVICE_MAC" ]; then
    echo "Trusting device: $DEVICE_MAC"
    bluetoothctl trust "$DEVICE_MAC" 2>/dev/null || true
fi
EOF

chmod +x /usr/local/bin/bluetooth-trust-device

echo "   Auto-trust configured"

# Step 6: Create Bluetooth agent service
echo "6️⃣  Creating Bluetooth pairing agent..."

cat > /usr/local/bin/bt-agent-auto-accept << 'EOF'
#!/bin/bash
# Bluetooth auto-accept agent for easier pairing

bt-agent --capability=NoInputNoOutput &
EOF

chmod +x /usr/local/bin/bt-agent-auto-accept

cat > /etc/systemd/system/bt-agent.service << 'EOF'
[Unit]
Description=Bluetooth Pairing Agent
After=bluetooth.service
Requires=bluetooth.service

[Service]
Type=simple
ExecStart=/usr/bin/bt-agent --capability=DisplayYesNo
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable bt-agent.service

echo "   Pairing agent configured"

# Step 7: Reload udev rules
echo "7️⃣  Reloading udev rules..."
udevadm control --reload-rules
udevadm trigger

# Step 8: Start services
echo "8️⃣  Starting services..."
systemctl start bluetooth
sleep 2

# Start PulseAudio as user
su - $SUDO_USER -c "pulseaudio --start" 2>/dev/null || pulseaudio --start

sleep 2

# Start agent
systemctl start bt-agent.service

# Step 9: Configure Bluetooth controller
echo "9️⃣  Configuring Bluetooth controller..."

bluetoothctl << BTCTL
power on
pairable on
discoverable on
agent on
default-agent
BTCTL

# Set device class to audio
hciconfig hci0 class 0x200420
hciconfig hci0 piscan

echo ""
echo "================================================"
echo "✅ Bluetooth Pairing Fix Complete!"
echo "================================================"
echo ""
echo "📱 Now try pairing from your phone:"
echo ""
echo "1. Forget/Remove 'KitchenRadio' from your phone if already paired"
echo "2. Search for Bluetooth devices"
echo "3. Select 'KitchenRadio'"
echo "4. Confirm the pairing code"
echo "5. Wait for connection (should stay connected now!)"
echo ""
echo "🔍 Check status:"
echo "   sudo systemctl status bluetooth"
echo "   sudo systemctl status bt-agent"
echo ""
echo "🔧 Manual pairing commands:"
echo "   sudo bluetoothctl"
echo "   scan on"
echo "   pair <MAC_ADDRESS>"
echo "   trust <MAC_ADDRESS>"
echo "   connect <MAC_ADDRESS>"
echo ""
echo "⚠️  If still having issues, reboot:"
echo "   sudo reboot"
echo ""
