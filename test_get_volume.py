#!/usr/bin/env python3
"""
Test script to get volume from Bluetooth device via DBus
"""

import dbus
import dbus.mainloop.glib
import sys

def get_volume_from_media_player(device_mac):
    """Try to get volume from MediaPlayer1 interface"""
    try:
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SystemBus()
        
        # Convert MAC to device path format
        device_path = f"/org/bluez/hci0/dev_{device_mac.replace(':', '_')}"
        
        # Get all objects
        obj_manager = dbus.Interface(
            bus.get_object('org.bluez', '/'),
            'org.freedesktop.DBus.ObjectManager'
        )
        objects = obj_manager.GetManagedObjects()
        
        print(f"\n🔍 Looking for volume on device: {device_mac}")
        print(f"   Device path: {device_path}")
        print("=" * 80)
        
        # Find MediaPlayer path
        player_path = None
        for path, interfaces in objects.items():
            if path.startswith(device_path) and 'org.bluez.MediaPlayer1' in interfaces:
                player_path = path
                print(f"\n✅ Found MediaPlayer1: {path}")
                props = interfaces['org.bluez.MediaPlayer1']
                print(f"   Properties: {list(props.keys())}")
                
                # Check if Volume exists
                if 'Volume' in props:
                    print(f"   📢 Volume on MediaPlayer1: {props['Volume']}")
                else:
                    print(f"   ❌ No 'Volume' property on MediaPlayer1")
                break
        
        if not player_path:
            print(f"\n❌ No MediaPlayer1 found for device {device_mac}")
        
        # Find MediaTransport path
        print("\n" + "=" * 80)
        transport_path = None
        for path, interfaces in objects.items():
            if path.startswith(device_path) and 'org.bluez.MediaTransport1' in interfaces:
                transport_path = path
                print(f"\n✅ Found MediaTransport1: {path}")
                props = interfaces['org.bluez.MediaTransport1']
                print(f"   Properties: {list(props.keys())}")
                
                # Check if Volume exists
                if 'Volume' in props:
                    print(f"   🔊 Volume on MediaTransport1: {props['Volume']}")
                else:
                    print(f"   ❌ No 'Volume' property on MediaTransport1")
        
        if not transport_path:
            print(f"\n❌ No MediaTransport1 found for device {device_mac}")
        
        # Try to get volume directly from MediaTransport1
        if transport_path:
            print("\n" + "=" * 80)
            print(f"\n🔊 Trying to get Volume from MediaTransport1...")
            try:
                transport_obj = bus.get_object('org.bluez', transport_path)
                props_iface = dbus.Interface(transport_obj, 'org.freedesktop.DBus.Properties')
                volume = props_iface.Get('org.bluez.MediaTransport1', 'Volume')
                print(f"   ✅ SUCCESS: Volume = {volume}")
                return int(volume)
            except dbus.exceptions.DBusException as e:
                print(f"   ❌ DBus error: {e}")
        
        print("\n" + "=" * 80)
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Default to the iPhone MAC from logs
    device_mac = "10:2F:CA:87:66:7A" if len(sys.argv) < 2 else sys.argv[1]
    
    volume = get_volume_from_media_player(device_mac)
    
    if volume is not None:
        print(f"\n✅ Final result: Volume = {volume}")
    else:
        print(f"\n❌ Could not retrieve volume")
