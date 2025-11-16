#!/usr/bin/env python3
"""
Check Bluetooth and Audio Status
Diagnoses why Bluetooth devices might be disconnecting
"""

import subprocess
import sys

def run_command(cmd, description):
    """Run a command and display output"""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⏱️  Command timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🔧 Bluetooth & Audio System Diagnostics")
    print("="*60)
    
    checks = [
        # PulseAudio checks
        ("pactl info", "PulseAudio Status"),
        ("pactl list modules short | grep -i bluetooth", "PulseAudio Bluetooth Modules"),
        ("pactl list sinks short", "Available Audio Sinks"),
        
        # Bluetooth checks
        ("systemctl status bluetooth --no-pager | head -20", "Bluetooth Service Status"),
        ("hciconfig -a", "Bluetooth Adapter Info"),
        
        # BlueZ checks
        ("bluetoothctl show", "Bluetooth Adapter Settings"),
        ("bluetoothctl devices", "Paired Devices"),
        
        # Check if modules are loaded
        ("lsmod | grep -i bluetooth", "Bluetooth Kernel Modules"),
        
        # Check PulseAudio config
        ("cat /etc/pulse/default.pa | grep -i bluetooth", "PulseAudio Bluetooth Config"),
        
        # Recent system logs
        ("journalctl -u bluetooth -n 20 --no-pager", "Recent Bluetooth Logs"),
    ]
    
    results = {}
    for cmd, desc in checks:
        success = run_command(cmd, desc)
        results[desc] = "✅ OK" if success else "❌ FAILED"
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    for desc, status in results.items():
        print(f"{status} {desc}")
    
    print("\n" + "="*60)
    print("💡 RECOMMENDATIONS")
    print("="*60)
    
    if not results.get("PulseAudio Status", "").startswith("✅"):
        print("⚠️  PulseAudio is not running!")
        print("   Fix: pulseaudio --start")
        print("   Or: systemctl --user start pulseaudio")
    
    if not results.get("PulseAudio Bluetooth Modules", "").startswith("✅"):
        print("⚠️  PulseAudio Bluetooth modules not loaded!")
        print("   Fix: pactl load-module module-bluetooth-discover")
        print("   Or: Add 'load-module module-bluetooth-discover' to /etc/pulse/default.pa")
    
    print("\n🔄 To restart everything:")
    print("   pulseaudio --kill")
    print("   pulseaudio --start")
    print("   sudo systemctl restart bluetooth")

if __name__ == '__main__':
    main()
