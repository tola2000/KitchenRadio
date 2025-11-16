#!/bin/bash
#
# Quick Bluetooth Speaker Test Script
# Tests if Bluetooth audio is working on Raspberry Pi
#

echo "🔍 Bluetooth Speaker Diagnostics"
echo "=================================="
echo ""

echo "1. Bluetooth Service Status:"
systemctl status bluetooth --no-pager | head -n 5
echo ""

echo "2. Bluetooth Controller Status:"
hciconfig hci0
echo ""

echo "3. Discoverable Status:"
bluetoothctl show | grep -E "Powered|Discoverable|Pairable"
echo ""

echo "4. Paired Devices:"
bluetoothctl devices
echo ""

echo "5. Connected Devices:"
bluetoothctl info | grep -E "Name|Connected|UUID"
echo ""

echo "6. PulseAudio Status:"
if pulseaudio --check; then
    echo "✅ PulseAudio is running"
else
    echo "❌ PulseAudio is NOT running"
fi
echo ""

echo "7. Audio Sinks:"
pactl list sinks short 2>/dev/null || echo "⚠️  Could not list sinks"
echo ""

echo "8. Bluetooth Audio Modules:"
pactl list modules | grep -i bluetooth
echo ""

echo "9. Audio Output Device:"
amixer cget numid=3 2>/dev/null || echo "⚠️  Could not get audio output"
echo ""

echo "10. Volume Level:"
amixer get Master 2>/dev/null || echo "⚠️  Could not get volume"
echo ""

echo "=================================="
echo "Troubleshooting Tips:"
echo ""
echo "If Bluetooth is not discoverable:"
echo "  sudo bluetoothctl"
echo "  power on"
echo "  discoverable on"
echo "  pairable on"
echo ""
echo "If audio not working:"
echo "  pulseaudio --kill"
echo "  pulseaudio --start"
echo "  sudo systemctl restart bluetooth"
echo ""
echo "Check PulseAudio logs:"
echo "  pulseaudio -vvv"
echo ""
