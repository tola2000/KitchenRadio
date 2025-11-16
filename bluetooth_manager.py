#!/usr/bin/env python3
"""
Bluetooth Device Manager for Raspberry Pi
Handles pairing, trusting, and connecting Bluetooth devices via Python
"""

import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import logging
import sys
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BluetoothManager:
    """Manage Bluetooth devices using D-Bus"""
    
    BLUEZ_SERVICE = 'org.bluez'
    ADAPTER_INTERFACE = 'org.bluez.Adapter1'
    DEVICE_INTERFACE = 'org.bluez.Device1'
    PROPERTIES_INTERFACE = 'org.freedesktop.DBus.Properties'
    OBJECT_MANAGER_INTERFACE = 'org.freedesktop.DBus.ObjectManager'
    
    def __init__(self, adapter_path='/org/bluez/hci0'):
        """Initialize Bluetooth manager"""
        self.adapter_path = adapter_path
        self.bus = None
        self.adapter = None
        self.setup_dbus()
    
    def setup_dbus(self):
        """Setup D-Bus connection"""
        try:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SystemBus()
            
            # Get adapter
            adapter_obj = self.bus.get_object(self.BLUEZ_SERVICE, self.adapter_path)
            self.adapter = dbus.Interface(adapter_obj, self.ADAPTER_INTERFACE)
            self.adapter_props = dbus.Interface(adapter_obj, self.PROPERTIES_INTERFACE)
            
            logger.info("✅ D-Bus connection established")
            
        except Exception as e:
            logger.error(f"Failed to setup D-Bus: {e}")
            sys.exit(1)
    
    def power_on(self):
        """Power on the Bluetooth adapter"""
        try:
            self.adapter_props.Set(self.ADAPTER_INTERFACE, 'Powered', dbus.Boolean(True))
            logger.info("🔵 Bluetooth powered ON")
            return True
        except Exception as e:
            logger.error(f"Error powering on: {e}")
            return False
    
    def set_discoverable(self, discoverable=True, timeout=0):
        """
        Make adapter discoverable.
        
        Args:
            discoverable: True to make discoverable
            timeout: Timeout in seconds (0 = always discoverable)
        """
        try:
            self.adapter_props.Set(self.ADAPTER_INTERFACE, 'Discoverable', dbus.Boolean(discoverable))
            self.adapter_props.Set(self.ADAPTER_INTERFACE, 'DiscoverableTimeout', dbus.UInt32(timeout))
            
            status = "ON (always)" if discoverable and timeout == 0 else "ON" if discoverable else "OFF"
            logger.info(f"👁️  Discoverable: {status}")
            return True
        except Exception as e:
            logger.error(f"Error setting discoverable: {e}")
            return False
    
    def set_pairable(self, pairable=True, timeout=0):
        """
        Make adapter pairable.
        
        Args:
            pairable: True to make pairable
            timeout: Timeout in seconds (0 = always pairable)
        """
        try:
            self.adapter_props.Set(self.ADAPTER_INTERFACE, 'Pairable', dbus.Boolean(pairable))
            self.adapter_props.Set(self.ADAPTER_INTERFACE, 'PairableTimeout', dbus.UInt32(timeout))
            
            status = "ON (always)" if pairable and timeout == 0 else "ON" if pairable else "OFF"
            logger.info(f"🔓 Pairable: {status}")
            return True
        except Exception as e:
            logger.error(f"Error setting pairable: {e}")
            return False
    
    def start_discovery(self):
        """Start device discovery"""
        try:
            self.adapter.StartDiscovery()
            logger.info("🔍 Discovery started...")
            return True
        except Exception as e:
            logger.error(f"Error starting discovery: {e}")
            return False
    
    def stop_discovery(self):
        """Stop device discovery"""
        try:
            self.adapter.StopDiscovery()
            logger.info("⏹️  Discovery stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping discovery: {e}")
            return False
    
    def get_devices(self):
        """Get list of known devices"""
        try:
            obj_manager = dbus.Interface(
                self.bus.get_object(self.BLUEZ_SERVICE, '/'),
                self.OBJECT_MANAGER_INTERFACE
            )
            
            objects = obj_manager.GetManagedObjects()
            devices = []
            
            for path, interfaces in objects.items():
                if self.DEVICE_INTERFACE in interfaces:
                    props = interfaces[self.DEVICE_INTERFACE]
                    device = {
                        'path': str(path),
                        'address': str(props.get('Address', 'Unknown')),
                        'name': str(props.get('Name', 'Unknown')),
                        'alias': str(props.get('Alias', 'Unknown')),
                        'paired': bool(props.get('Paired', False)),
                        'trusted': bool(props.get('Trusted', False)),
                        'connected': bool(props.get('Connected', False)),
                        'rssi': int(props.get('RSSI', 0)) if 'RSSI' in props else None
                    }
                    devices.append(device)
            
            return devices
            
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            return []
    
    def find_device_by_address(self, address):
        """Find device by MAC address"""
        devices = self.get_devices()
        for device in devices:
            if device['address'].upper() == address.upper():
                return device
        return None
    
    def pair_device(self, device_path):
        """Pair with a device"""
        try:
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, device_path)
            device = dbus.Interface(device_obj, self.DEVICE_INTERFACE)
            
            logger.info(f"🔗 Pairing with device...")
            device.Pair()
            logger.info("✅ Paired successfully!")
            return True
            
        except dbus.exceptions.DBusException as e:
            if "AlreadyExists" in str(e):
                logger.info("ℹ️  Device already paired")
                return True
            else:
                logger.error(f"Error pairing: {e}")
                return False
        except Exception as e:
            logger.error(f"Error pairing: {e}")
            return False
    
    def trust_device(self, device_path):
        """Trust a device (allow auto-reconnect)"""
        try:
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, device_path)
            device_props = dbus.Interface(device_obj, self.PROPERTIES_INTERFACE)
            
            device_props.Set(self.DEVICE_INTERFACE, 'Trusted', dbus.Boolean(True))
            logger.info("✅ Device trusted!")
            return True
            
        except Exception as e:
            logger.error(f"Error trusting device: {e}")
            return False
    
    def connect_device(self, device_path):
        """Connect to a device"""
        try:
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, device_path)
            device = dbus.Interface(device_obj, self.DEVICE_INTERFACE)
            
            logger.info(f"📡 Connecting to device...")
            device.Connect()
            logger.info("✅ Connected successfully!")
            return True
            
        except dbus.exceptions.DBusException as e:
            if "AlreadyConnected" in str(e):
                logger.info("ℹ️  Device already connected")
                return True
            else:
                logger.error(f"Error connecting: {e}")
                return False
        except Exception as e:
            logger.error(f"Error connecting: {e}")
            return False
    
    def disconnect_device(self, device_path):
        """Disconnect from a device"""
        try:
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, device_path)
            device = dbus.Interface(device_obj, self.DEVICE_INTERFACE)
            
            device.Disconnect()
            logger.info("🔌 Device disconnected")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            return False
    
    def remove_device(self, device_path):
        """Remove/unpair a device"""
        try:
            self.adapter.RemoveDevice(device_path)
            logger.info("🗑️  Device removed")
            return True
            
        except Exception as e:
            logger.error(f"Error removing device: {e}")
            return False
    
    def pair_and_trust(self, address):
        """
        Complete pairing workflow: find, pair, trust, and connect.
        
        Args:
            address: MAC address of device (XX:XX:XX:XX:XX:XX)
        """
        logger.info(f"Starting pairing process for {address}")
        
        # Find device
        device = self.find_device_by_address(address)
        
        if not device:
            logger.error(f"❌ Device {address} not found. Make sure it's visible and try discovery first.")
            return False
        
        logger.info(f"📱 Found device: {device['name']} ({device['address']})")
        device_path = device['path']
        
        # Pair if not already paired
        if not device['paired']:
            if not self.pair_device(device_path):
                return False
        else:
            logger.info("ℹ️  Device already paired")
        
        # Trust the device
        if not device['trusted']:
            if not self.trust_device(device_path):
                return False
        else:
            logger.info("ℹ️  Device already trusted")
        
        # Connect
        if not device['connected']:
            time.sleep(1)  # Brief pause
            if not self.connect_device(device_path):
                return False
        else:
            logger.info("ℹ️  Device already connected")
        
        logger.info("=" * 60)
        logger.info("✅ Device fully configured and connected!")
        logger.info("=" * 60)
        return True
    
    def list_devices(self, show_all=False):
        """List all known devices"""
        devices = self.get_devices()
        
        if not devices:
            logger.info("No devices found")
            return
        
        logger.info("=" * 80)
        logger.info("BLUETOOTH DEVICES")
        logger.info("=" * 80)
        
        for device in devices:
            if not show_all and not (device['paired'] or device['connected'] or device.get('rssi')):
                continue
            
            status_icons = []
            if device['connected']:
                status_icons.append("🟢 Connected")
            if device['paired']:
                status_icons.append("🔗 Paired")
            if device['trusted']:
                status_icons.append("✅ Trusted")
            
            status = " | ".join(status_icons) if status_icons else "⚪ Not paired"
            
            logger.info(f"\n📱 {device['name']}")
            logger.info(f"   Address: {device['address']}")
            logger.info(f"   Status: {status}")
            if device.get('rssi'):
                logger.info(f"   Signal: {device['rssi']} dBm")
        
        logger.info("=" * 80)


def interactive_menu():
    """Interactive menu for Bluetooth management"""
    manager = BluetoothManager()
    
    # Initialize adapter
    manager.power_on()
    manager.set_discoverable(True, timeout=0)
    manager.set_pairable(True, timeout=0)
    
    while True:
        print("\n" + "=" * 60)
        print("🔵 BLUETOOTH MANAGER")
        print("=" * 60)
        print("1. List devices")
        print("2. Start discovery (scan for new devices)")
        print("3. Stop discovery")
        print("4. Pair and trust device (by MAC address)")
        print("5. Connect to device")
        print("6. Disconnect device")
        print("7. Remove device")
        print("8. Make discoverable")
        print("9. Exit")
        print("=" * 60)
        
        choice = input("Select option: ").strip()
        
        if choice == '1':
            show_all = input("Show all devices? (y/n): ").lower() == 'y'
            manager.list_devices(show_all=show_all)
            
        elif choice == '2':
            manager.start_discovery()
            print("\n🔍 Scanning for 10 seconds...")
            time.sleep(10)
            manager.stop_discovery()
            manager.list_devices(show_all=True)
            
        elif choice == '3':
            manager.stop_discovery()
            
        elif choice == '4':
            mac = input("Enter MAC address (XX:XX:XX:XX:XX:XX): ").strip()
            if mac:
                manager.pair_and_trust(mac)
            
        elif choice == '5':
            mac = input("Enter MAC address: ").strip()
            device = manager.find_device_by_address(mac)
            if device:
                manager.connect_device(device['path'])
            else:
                print("❌ Device not found")
                
        elif choice == '6':
            mac = input("Enter MAC address: ").strip()
            device = manager.find_device_by_address(mac)
            if device:
                manager.disconnect_device(device['path'])
            else:
                print("❌ Device not found")
                
        elif choice == '7':
            mac = input("Enter MAC address: ").strip()
            device = manager.find_device_by_address(mac)
            if device:
                confirm = input(f"Remove {device['name']}? (y/n): ")
                if confirm.lower() == 'y':
                    manager.remove_device(device['path'])
            else:
                print("❌ Device not found")
                
        elif choice == '8':
            manager.set_discoverable(True, timeout=0)
            manager.set_pairable(True, timeout=0)
            
        elif choice == '9':
            print("👋 Goodbye!")
            break


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bluetooth Device Manager')
    parser.add_argument('--list', action='store_true', help='List all devices')
    parser.add_argument('--pair', metavar='MAC', help='Pair with device by MAC address')
    parser.add_argument('--connect', metavar='MAC', help='Connect to device by MAC address')
    parser.add_argument('--disconnect', metavar='MAC', help='Disconnect from device')
    parser.add_argument('--remove', metavar='MAC', help='Remove device')
    parser.add_argument('--scan', action='store_true', help='Scan for devices')
    parser.add_argument('--discoverable', action='store_true', help='Make adapter discoverable')
    
    args = parser.parse_args()
    
    manager = BluetoothManager()
    manager.power_on()
    
    if args.list:
        manager.list_devices(show_all=True)
        
    elif args.pair:
        manager.set_discoverable(True, timeout=0)
        manager.set_pairable(True, timeout=0)
        manager.pair_and_trust(args.pair)
        
    elif args.connect:
        device = manager.find_device_by_address(args.connect)
        if device:
            manager.connect_device(device['path'])
        else:
            logger.error("Device not found")
            
    elif args.disconnect:
        device = manager.find_device_by_address(args.disconnect)
        if device:
            manager.disconnect_device(device['path'])
        else:
            logger.error("Device not found")
            
    elif args.remove:
        device = manager.find_device_by_address(args.remove)
        if device:
            manager.remove_device(device['path'])
        else:
            logger.error("Device not found")
            
    elif args.scan:
        manager.start_discovery()
        logger.info("Scanning for 10 seconds...")
        time.sleep(10)
        manager.stop_discovery()
        manager.list_devices(show_all=True)
        
    elif args.discoverable:
        manager.set_discoverable(True, timeout=0)
        manager.set_pairable(True, timeout=0)
        logger.info("Adapter is now discoverable")
        
    else:
        # Interactive mode
        interactive_menu()


if __name__ == '__main__':
    main()
