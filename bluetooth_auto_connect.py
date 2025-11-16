#!/usr/bin/env python3
"""
Bluetooth Auto-Connect Service
Automatically pairs and connects to the first Bluetooth device that tries to connect
"""

import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import logging
import sys
import signal
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BluetoothAutoConnect:
    """Automatically connect to new Bluetooth devices"""
    
    BLUEZ_SERVICE = 'org.bluez'
    ADAPTER_INTERFACE = 'org.bluez.Adapter1'
    DEVICE_INTERFACE = 'org.bluez.Device1'
    PROPERTIES_INTERFACE = 'org.freedesktop.DBus.Properties'
    OBJECT_MANAGER_INTERFACE = 'org.freedesktop.DBus.ObjectManager'
    
    def __init__(self, adapter_path='/org/bluez/hci0', auto_pair_first=True):
        """
        Initialize auto-connect service.
        
        Args:
            adapter_path: Path to Bluetooth adapter
            auto_pair_first: If True, auto-pair first device that appears
        """
        self.adapter_path = adapter_path
        self.auto_pair_first = auto_pair_first
        self.bus = None
        self.adapter = None
        self.connected_devices = set()
        self.paired_devices = set()
        self.running = False
        
        # Track if we've already auto-paired
        self.has_auto_paired = False
        
        self.setup_dbus()
    
    def setup_dbus(self):
        """Setup D-Bus connection and signal handlers"""
        try:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SystemBus()
            
            # Get adapter
            adapter_obj = self.bus.get_object(self.BLUEZ_SERVICE, self.adapter_path)
            self.adapter = dbus.Interface(adapter_obj, self.ADAPTER_INTERFACE)
            self.adapter_props = dbus.Interface(adapter_obj, self.PROPERTIES_INTERFACE)
            
            # Get object manager
            self.obj_manager = dbus.Interface(
                self.bus.get_object(self.BLUEZ_SERVICE, '/'),
                self.OBJECT_MANAGER_INTERFACE
            )
            
            # Subscribe to interface changes
            self.obj_manager.connect_to_signal(
                'InterfacesAdded',
                self.on_interfaces_added
            )
            
            # Subscribe to property changes
            self.bus.add_signal_receiver(
                self.on_properties_changed,
                signal_name='PropertiesChanged',
                dbus_interface=self.PROPERTIES_INTERFACE,
                path_keyword='path'
            )
            
            logger.info("✅ D-Bus connection established")
            
            # Get already paired devices
            self.scan_existing_devices()
            
        except Exception as e:
            logger.error(f"Failed to setup D-Bus: {e}")
            sys.exit(1)
    
    def scan_existing_devices(self):
        """Scan for already paired devices"""
        try:
            objects = self.obj_manager.GetManagedObjects()
            
            for path, interfaces in objects.items():
                if self.DEVICE_INTERFACE in interfaces:
                    props = interfaces[self.DEVICE_INTERFACE]
                    
                    if props.get('Paired', False):
                        address = str(props.get('Address', ''))
                        self.paired_devices.add(address)
                        logger.info(f"📱 Already paired: {props.get('Name', 'Unknown')} ({address})")
                        
                        if not self.auto_pair_first:
                            self.has_auto_paired = True  # Disable auto-pair if devices exist
                    
                    if props.get('Connected', False):
                        address = str(props.get('Address', ''))
                        self.connected_devices.add(address)
                        logger.info(f"🟢 Already connected: {props.get('Name', 'Unknown')} ({address})")
                        
        except Exception as e:
            logger.error(f"Error scanning existing devices: {e}")
    
    def initialize_adapter(self):
        """Initialize adapter for auto-connect mode"""
        try:
            # Power on
            self.adapter_props.Set(self.ADAPTER_INTERFACE, 'Powered', dbus.Boolean(True))
            logger.info("🔵 Bluetooth powered ON")
            
            # Make discoverable (always)
            self.adapter_props.Set(self.ADAPTER_INTERFACE, 'Discoverable', dbus.Boolean(True))
            self.adapter_props.Set(self.ADAPTER_INTERFACE, 'DiscoverableTimeout', dbus.UInt32(0))
            logger.info("👁️  Discoverable: ON (always)")
            
            # Make pairable (always)
            self.adapter_props.Set(self.ADAPTER_INTERFACE, 'Pairable', dbus.Boolean(True))
            self.adapter_props.Set(self.ADAPTER_INTERFACE, 'PairableTimeout', dbus.UInt32(0))
            logger.info("🔓 Pairable: ON (always)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing adapter: {e}")
            return False
    
    def on_interfaces_added(self, path, interfaces):
        """Handle new device detected"""
        try:
            if self.DEVICE_INTERFACE not in interfaces:
                return
            
            props = interfaces[self.DEVICE_INTERFACE]
            address = str(props.get('Address', ''))
            name = str(props.get('Name', 'Unknown'))
            
            logger.info("=" * 60)
            logger.info(f"🆕 NEW DEVICE DETECTED")
            logger.info(f"   Name: {name}")
            logger.info(f"   Address: {address}")
            logger.info("=" * 60)
            
            # Auto-pair first device if enabled and we haven't paired yet
            if self.auto_pair_first and not self.has_auto_paired:
                logger.info("🤖 Auto-pairing first device...")
                if self.pair_and_trust_device(path, name, address):
                    self.has_auto_paired = True
                    
                    # Give time for pairing to complete, then connect
                    logger.info("⏳ Waiting for pairing to complete...")
                    GLib.timeout_add(3000, self.connect_device, path, name, address)
                    
        except Exception as e:
            logger.error(f"Error handling new device: {e}")
    
    def on_properties_changed(self, interface, changed, invalidated, path):
        """Handle property changes on devices"""
        try:
            if interface != self.DEVICE_INTERFACE:
                return
            
            # Get device info
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, path)
            device_props = dbus.Interface(device_obj, self.PROPERTIES_INTERFACE)
            all_props = device_props.GetAll(self.DEVICE_INTERFACE)
            
            address = str(all_props.get('Address', ''))
            name = str(all_props.get('Name', 'Unknown'))
            
            # Check if device just got paired
            if 'Paired' in changed and changed['Paired']:
                if address not in self.paired_devices:
                    self.paired_devices.add(address)
                    logger.info(f"✅ Device paired: {name} ({address})")
                    
                    # Auto-trust newly paired device
                    self.trust_device(path)
            
            # Check if device connected
            if 'Connected' in changed:
                if changed['Connected']:
                    if address not in self.connected_devices:
                        self.connected_devices.add(address)
                        logger.info("=" * 60)
                        logger.info(f"🟢 DEVICE CONNECTED")
                        logger.info(f"   Name: {name}")
                        logger.info(f"   Address: {address}")
                        logger.info("=" * 60)
                else:
                    if address in self.connected_devices:
                        self.connected_devices.remove(address)
                        logger.info(f"🔴 Device disconnected: {name} ({address})")
                        
        except Exception as e:
            logger.error(f"Error handling property change: {e}")
    
    def pair_and_trust_device(self, device_path, name, address):
        """
        Pair and trust a device.
        
        Args:
            device_path: D-Bus path to device
            name: Device name
            address: Device MAC address
        """
        try:
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, device_path)
            device = dbus.Interface(device_obj, self.DEVICE_INTERFACE)
            device_props = dbus.Interface(device_obj, self.PROPERTIES_INTERFACE)
            
            # Check if already paired
            props = device_props.GetAll(self.DEVICE_INTERFACE)
            if props.get('Paired', False):
                logger.info(f"ℹ️  Device already paired: {name}")
                self.paired_devices.add(address)
                
                # Make sure it's trusted
                if not props.get('Trusted', False):
                    self.trust_device(device_path)
                
                return True
            
            # Try to pair
            logger.info(f"🔗 Pairing with {name}...")
            device.Pair()
            logger.info(f"✅ Paired successfully!")
            
            self.paired_devices.add(address)
            
            # Trust the device
            self.trust_device(device_path)
            
            return True
            
        except dbus.exceptions.DBusException as e:
            error_name = e.get_dbus_name()
            
            if "AlreadyExists" in error_name:
                logger.info(f"ℹ️  Device already paired: {name}")
                self.paired_devices.add(address)
                return True
            elif "AuthenticationCanceled" in error_name:
                logger.warning(f"⚠️  Pairing cancelled by user for {name}")
                return False
            elif "AuthenticationFailed" in error_name:
                logger.warning(f"⚠️  Pairing failed for {name} (wrong PIN/rejection)")
                return False
            else:
                logger.error(f"❌ Error pairing with {name}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error pairing with {name}: {e}")
            return False
    
    def trust_device(self, device_path):
        """Trust a device (allow auto-reconnect)"""
        try:
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, device_path)
            device_props = dbus.Interface(device_obj, self.PROPERTIES_INTERFACE)
            
            device_props.Set(self.DEVICE_INTERFACE, 'Trusted', dbus.Boolean(True))
            logger.info(f"✅ Device trusted (auto-reconnect enabled)")
            return True
            
        except Exception as e:
            logger.error(f"Error trusting device: {e}")
            return False
    
    def connect_device(self, device_path, name, address):
        """
        Connect to a paired device and wait for audio profile.
        
        Args:
            device_path: D-Bus path to device
            name: Device name
            address: Device MAC address
        """
        try:
            logger.info(f"🔌 Connecting to {name}...")
            
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, device_path)
            device = dbus.Interface(device_obj, self.DEVICE_INTERFACE)
            device_props = dbus.Interface(device_obj, self.PROPERTIES_INTERFACE)
            
            # Check if already connected
            props = device_props.GetAll(self.DEVICE_INTERFACE)
            if props.get('Connected', False):
                logger.info(f"✅ Already connected to {name}")
                return False  # Don't reschedule
            
            # Connect
            device.Connect()
            
            # Wait for audio profile to establish
            logger.info(f"⏳ Waiting for audio profile to establish...")
            max_attempts = 10
            for attempt in range(max_attempts):
                time.sleep(1)
                props = device_props.GetAll(self.DEVICE_INTERFACE)
                
                # Check if we have audio UUID (A2DP Sink)
                uuids = props.get('UUIDs', [])
                audio_uuids = [
                    '0000110b-0000-1000-8000-00805f9b34fb',  # A2DP Audio Sink
                    '0000110a-0000-1000-8000-00805f9b34fb',  # A2DP Audio Source
                ]
                
                if any(uuid.lower() in [u.lower() for u in uuids] for uuid in audio_uuids):
                    logger.info(f"✅ Audio profile established!")
                    logger.info(f"🎵 {name} is now connected and ready for audio streaming")
                    return False  # Don't reschedule
            
            logger.warning(f"⚠️  Audio profile didn't establish after {max_attempts}s")
            return False  # Don't reschedule
            
        except dbus.exceptions.DBusException as e:
            error_name = e.get_dbus_name()
            
            if "AlreadyConnected" in error_name:
                logger.info(f"✅ Already connected to {name}")
            elif "InProgress" in error_name:
                logger.info(f"⏳ Connection already in progress for {name}")
            elif "NotReady" in error_name:
                logger.warning(f"⚠️  Device not ready yet, retrying in 2s...")
                return True  # Reschedule
            else:
                logger.error(f"❌ Error connecting to {name}: {e}")
            
            return False  # Don't reschedule
            
        except Exception as e:
            logger.error(f"❌ Error connecting to {name}: {e}")
            return False  # Don't reschedule
    
    def run(self):
        """Start the auto-connect service"""
        logger.info("=" * 60)
        logger.info("🔵 BLUETOOTH AUTO-CONNECT SERVICE")
        logger.info("=" * 60)
        
        if not self.initialize_adapter():
            logger.error("Failed to initialize adapter")
            return 1
        
        if self.auto_pair_first and not self.has_auto_paired:
            logger.info("🤖 Auto-pair mode: Will pair with FIRST device that appears")
        else:
            logger.info("📱 Listening mode: Will accept connections from paired devices")
        
        logger.info("")
        logger.info("Waiting for Bluetooth devices...")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        self.running = True
        
        try:
            # Start GLib main loop
            loop = GLib.MainLoop()
            loop.run()
            
        except KeyboardInterrupt:
            logger.info("\n👋 Stopping auto-connect service...")
            self.running = False
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            return 1
        
        return 0
    
    def stop(self):
        """Stop the service"""
        self.running = False


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"\nReceived signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Bluetooth Auto-Connect Service',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-pair with first device that appears
  python3 bluetooth_auto_connect.py --auto-pair-first
  
  # Just listen for already paired devices
  python3 bluetooth_auto_connect.py
  
  # Run as background service
  nohup python3 bluetooth_auto_connect.py --auto-pair-first > bt-auto.log 2>&1 &
        """
    )
    
    parser.add_argument(
        '--auto-pair-first',
        action='store_true',
        help='Automatically pair with the first device that appears'
    )
    
    parser.add_argument(
        '--adapter',
        default='/org/bluez/hci0',
        help='Bluetooth adapter path (default: /org/bluez/hci0)'
    )
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run service
    service = BluetoothAutoConnect(
        adapter_path=args.adapter,
        auto_pair_first=args.auto_pair_first
    )
    
    return service.run()


if __name__ == '__main__':
    sys.exit(main())
