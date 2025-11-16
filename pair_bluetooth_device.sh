#!/bin/bash
#
# Simple Bluetooth Pairing Helper
# Use this to pair and trust devices manually
#

echo "🔵 Bluetooth Pairing Helper"
echo "============================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

echo "Current paired devices:"
bluetoothctl devices
echo ""

echo "Starting scan for nearby devices..."
echo "(Press Ctrl+C when you see your device)"
echo ""

# Start scanning
bluetoothctl scan on &
SCAN_PID=$!

sleep 10

# Stop scanning
kill $SCAN_PID 2>/dev/null

echo ""
echo "Available devices:"
bluetoothctl devices
echo ""

read -p "Enter the MAC address of the device to pair (XX:XX:XX:XX:XX:XX): " MAC_ADDRESS

if [ -z "$MAC_ADDRESS" ]; then
    echo "❌ No MAC address provided"
    exit 1
fi

echo ""
echo "Pairing with $MAC_ADDRESS..."
echo ""

# Pair, trust, and connect
bluetoothctl << EOF
pair $MAC_ADDRESS
trust $MAC_ADDRESS
connect $MAC_ADDRESS
EOF

echo ""
echo "✅ Device should now be paired and trusted!"
echo ""
echo "To connect later:"
echo "  sudo bluetoothctl"
echo "  connect $MAC_ADDRESS"
echo ""
echo "Paired devices:"
bluetoothctl devices
echo ""
