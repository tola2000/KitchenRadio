#!/usr/bin/env python3
"""
Debug Bluetooth audio issues - check PulseAudio configuration
"""

import subprocess
import sys
import time

def run_command(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), -1

def check_pulseaudio_modules():
    """Check which PulseAudio Bluetooth modules are loaded"""
    print("=" * 60)
    print("CHECKING PULSEAUDIO BLUETOOTH MODULES")
    print("=" * 60)
    
    stdout, stderr, code = run_command("pactl list modules short")
    if code == 0:
        bt_modules = [line for line in stdout.split('\n') if 'bluetooth' in line.lower()]
        if bt_modules:
            print("✅ Bluetooth modules loaded:")
            for module in bt_modules:
                print(f"   {module}")
        else:
            print("❌ NO Bluetooth modules loaded!")
            print("\nYou may need to load:")
            print("   pactl load-module module-bluetooth-policy")
            print("   pactl load-module module-bluetooth-discover")
    else:
        print(f"❌ Error: {stderr}")
    
    print()

def check_bluetooth_sinks():
    """Check Bluetooth audio sinks"""
    print("=" * 60)
    print("CHECKING BLUETOOTH SINKS")
    print("=" * 60)
    
    stdout, stderr, code = run_command("pactl list sinks short")
    if code == 0:
        sinks = stdout.split('\n')
        bt_sinks = [line for line in sinks if 'bluez' in line.lower()]
        
        if bt_sinks:
            print("✅ Bluetooth sinks found:")
            for sink in bt_sinks:
                print(f"   {sink}")
        else:
            print("❌ NO Bluetooth sinks found!")
            print("\nMake sure:")
            print("   1. Bluetooth device is connected")
            print("   2. A2DP profile is active")
            print("   3. PulseAudio Bluetooth modules are loaded")
    else:
        print(f"❌ Error: {stderr}")
    
    print()

def check_bluetooth_sink_details():
    """Check detailed Bluetooth sink information"""
    print("=" * 60)
    print("BLUETOOTH SINK DETAILS")
    print("=" * 60)
    
    stdout, stderr, code = run_command("pactl list sinks")
    if code == 0:
        # Find bluez sinks
        lines = stdout.split('\n')
        in_bt_sink = False
        current_sink_info = []
        
        for line in lines:
            if 'bluez' in line.lower() or in_bt_sink:
                current_sink_info.append(line)
                
                # Check if we're in a Bluetooth sink section
                if 'Name:' in line and 'bluez' in line.lower():
                    in_bt_sink = True
                
                # End of sink section
                if in_bt_sink and line.strip().startswith('Sink #'):
                    in_bt_sink = False
                    
                # Look for suspend state
                if 'State:' in line:
                    if 'SUSPENDED' in line:
                        print(f"⚠️  SINK IS SUSPENDED: {line.strip()}")
                    elif 'RUNNING' in line:
                        print(f"✅ SINK IS RUNNING: {line.strip()}")
        
        if current_sink_info:
            print("\nFull Bluetooth sink info:")
            for line in current_sink_info[:30]:  # First 30 lines
                print(f"   {line}")
        else:
            print("❌ No Bluetooth sink details found")
    else:
        print(f"❌ Error: {stderr}")
    
    print()

def check_default_sink():
    """Check if Bluetooth is the default sink"""
    print("=" * 60)
    print("CHECKING DEFAULT SINK")
    print("=" * 60)
    
    stdout, stderr, code = run_command("pactl info")
    if code == 0:
        for line in stdout.split('\n'):
            if 'Default Sink:' in line:
                print(f"   {line.strip()}")
                if 'bluez' in line.lower():
                    print("   ✅ Bluetooth is default sink")
                else:
                    print("   ⚠️  Bluetooth is NOT default sink - audio might route elsewhere!")
    else:
        print(f"❌ Error: {stderr}")
    
    print()

def check_bluetooth_profiles():
    """Check which Bluetooth profiles are available/active"""
    print("=" * 60)
    print("CHECKING BLUETOOTH PROFILES (A2DP/HSP/HFP)")
    print("=" * 60)
    
    stdout, stderr, code = run_command("pactl list cards")
    if code == 0:
        lines = stdout.split('\n')
        in_bt_card = False
        
        for line in lines:
            if 'bluez' in line.lower():
                in_bt_card = True
            
            if in_bt_card:
                print(f"   {line}")
                
                # Stop at next card
                if line.strip().startswith('Card #') and 'bluez' not in line.lower():
                    break
        
        if not in_bt_card:
            print("❌ No Bluetooth card found")
    else:
        print(f"❌ Error: {stderr}")
    
    print()

def check_suspend_timeout():
    """Check PulseAudio module-suspend-on-idle settings"""
    print("=" * 60)
    print("CHECKING AUTO-SUSPEND SETTINGS")
    print("=" * 60)
    
    stdout, stderr, code = run_command("pactl list modules")
    if code == 0:
        lines = stdout.split('\n')
        for i, line in enumerate(lines):
            if 'module-suspend-on-idle' in line:
                print("⚠️  module-suspend-on-idle is loaded!")
                print(f"   {line}")
                # Print next few lines for timeout setting
                for j in range(1, min(5, len(lines) - i)):
                    print(f"   {lines[i + j]}")
                print("\n   This module can suspend sinks after idle timeout!")
                print("   Consider unloading it: pactl unload-module module-suspend-on-idle")
                break
        else:
            print("✅ module-suspend-on-idle is NOT loaded (good!)")
    else:
        print(f"❌ Error: {stderr}")
    
    print()

def monitor_bluetooth_audio():
    """Monitor Bluetooth audio in real-time"""
    print("=" * 60)
    print("MONITORING BLUETOOTH AUDIO (10 seconds)")
    print("=" * 60)
    print("Play audio from your iPhone now...\n")
    
    # Subscribe to PulseAudio events
    try:
        proc = subprocess.Popen(
            ["pactl", "subscribe"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        start_time = time.time()
        while time.time() - start_time < 10:
            line = proc.stdout.readline()
            if line:
                print(f"   [{time.time() - start_time:.1f}s] {line.strip()}")
        
        proc.terminate()
        
    except Exception as e:
        print(f"❌ Error monitoring: {e}")
    
    print()

def main():
    """Run all diagnostics"""
    print("\n" + "=" * 60)
    print("BLUETOOTH AUDIO DIAGNOSTICS")
    print("=" * 60)
    print()
    
    check_pulseaudio_modules()
    check_bluetooth_sinks()
    check_bluetooth_sink_details()
    check_default_sink()
    check_bluetooth_profiles()
    check_suspend_timeout()
    
    # Ask user if they want to monitor
    print("\n" + "=" * 60)
    print("Would you like to monitor audio events in real-time?")
    print("This will help identify when audio stops.")
    response = input("Monitor for 10 seconds? (y/n): ")
    
    if response.lower() == 'y':
        monitor_bluetooth_audio()
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)
    print("\nCommon issues and fixes:")
    print("1. If module-suspend-on-idle is loaded:")
    print("     pactl unload-module module-suspend-on-idle")
    print()
    print("2. If Bluetooth modules not loaded:")
    print("     pactl load-module module-bluetooth-policy")
    print("     pactl load-module module-bluetooth-discover")
    print()
    print("3. If Bluetooth sink is SUSPENDED:")
    print("     pactl suspend-sink <sink-name> 0")
    print()
    print("4. If Bluetooth is not default sink:")
    print("     pactl set-default-sink <bluez-sink-name>")
    print()

if __name__ == "__main__":
    main()
