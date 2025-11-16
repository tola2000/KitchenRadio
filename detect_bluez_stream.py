#!/usr/bin/env python3
"""
BlueZ Stream Detection Script

Monitors BlueZ D-Bus interface to detect when a new Bluetooth device
starts streaming audio (A2DP connection).
"""

import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BlueZStreamDetector:
    """Monitor BlueZ for new audio streaming devices"""
    
    BLUEZ_SERVICE = 'org.bluez'
    ADAPTER_INTERFACE = 'org.bluez.Adapter1'
    DEVICE_INTERFACE = 'org.bluez.Device1'
    MEDIA_TRANSPORT_INTERFACE = 'org.bluez.MediaTransport1'
    PROPERTIES_INTERFACE = 'org.freedesktop.DBus.Properties'
    OBJECT_MANAGER_INTERFACE = 'org.freedesktop.DBus.ObjectManager'
    
    def __init__(self):
        """Initialize the BlueZ stream detector"""
        self.bus = None
        self.active_devices = set()
        self.setup_dbus()
    
    def setup_dbus(self):
        """Setup D-Bus connection and signal handlers"""
        try:
            # Initialize D-Bus main loop
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            
            # Get system bus
            self.bus = dbus.SystemBus()
            
            # Get BlueZ object manager
            self.obj_manager = dbus.Interface(
                self.bus.get_object(self.BLUEZ_SERVICE, '/'),
                self.OBJECT_MANAGER_INTERFACE
            )
            
            # Subscribe to interface changes
            self.obj_manager.connect_to_signal(
                'InterfacesAdded',
                self.on_interfaces_added
            )
            
            self.obj_manager.connect_to_signal(
                'InterfacesRemoved',
                self.on_interfaces_removed
            )
            
            # Subscribe to property changes for all objects
            self.bus.add_signal_receiver(
                self.on_properties_changed,
                signal_name='PropertiesChanged',
                dbus_interface=self.PROPERTIES_INTERFACE,
                path_keyword='path'
            )
            
            logger.info("✅ D-Bus connection established")
            
            # Check for already connected devices
            self.scan_existing_devices()
            
        except Exception as e:
            logger.error(f"Failed to setup D-Bus: {e}")
            sys.exit(1)
    
    def scan_existing_devices(self):
        """Scan for already connected/streaming devices"""
        try:
            objects = self.obj_manager.GetManagedObjects()
            
            for path, interfaces in objects.items():
                # Check for connected devices
                if self.DEVICE_INTERFACE in interfaces:
                    props = interfaces[self.DEVICE_INTERFACE]
                    if props.get('Connected', False):
                        device_name = props.get('Name', 'Unknown')
                        device_address = props.get('Address', 'Unknown')
                        logger.info(f"📱 Found connected device: {device_name} ({device_address})")
                
                # Check for active media transports
                if self.MEDIA_TRANSPORT_INTERFACE in interfaces:
                    props = interfaces[self.MEDIA_TRANSPORT_INTERFACE]
                    state = props.get('State', 'idle')
                    if state == 'active':
                        self.on_stream_started(path, props)
                        
        except Exception as e:
            logger.error(f"Error scanning existing devices: {e}")
    
    def on_interfaces_added(self, path, interfaces):
        """Handle new interfaces being added"""
        try:
            # Check if a MediaTransport interface was added
            if self.MEDIA_TRANSPORT_INTERFACE in interfaces:
                props = interfaces[self.MEDIA_TRANSPORT_INTERFACE]
                state = props.get('State', 'idle')
                
                if state == 'active':
                    self.on_stream_started(path, props)
                    
            # Check if a device was added
            if self.DEVICE_INTERFACE in interfaces:
                props = interfaces[self.DEVICE_INTERFACE]
                if props.get('Connected', False):
                    device_name = props.get('Name', 'Unknown')
                    device_address = props.get('Address', 'Unknown')
                    logger.info(f"📱 New device connected: {device_name} ({device_address})")
                    
        except Exception as e:
            logger.error(f"Error handling interfaces added: {e}")
    
    def on_interfaces_removed(self, path, interfaces):
        """Handle interfaces being removed"""
        try:
            if self.MEDIA_TRANSPORT_INTERFACE in interfaces:
                if path in self.active_devices:
                    self.on_stream_stopped(path)
                    
        except Exception as e:
            logger.error(f"Error handling interfaces removed: {e}")
    
    def on_properties_changed(self, interface, changed, invalidated, path):
        """Handle property changes on D-Bus objects"""
        try:
            # Monitor MediaTransport state changes
            if interface == self.MEDIA_TRANSPORT_INTERFACE:
                if 'State' in changed:
                    new_state = changed['State']
                    
                    if new_state == 'active' and path not in self.active_devices:
                        self.on_stream_started(path, changed)
                    elif new_state in ['idle', 'pending'] and path in self.active_devices:
                        self.on_stream_stopped(path)
            
            # Monitor device connection state
            elif interface == self.DEVICE_INTERFACE:
                if 'Connected' in changed:
                    if changed['Connected']:
                        device_obj = self.bus.get_object(self.BLUEZ_SERVICE, path)
                        device_props = dbus.Interface(
                            device_obj, self.PROPERTIES_INTERFACE
                        )
                        props = device_props.GetAll(self.DEVICE_INTERFACE)
                        device_name = props.get('Name', 'Unknown')
                        device_address = props.get('Address', 'Unknown')
                        logger.info(f"📱 Device connected: {device_name} ({device_address})")
                    else:
                        logger.info(f"📱 Device disconnected: {path}")
                        
        except Exception as e:
            logger.error(f"Error handling property change: {e}")
    
    def on_stream_started(self, path, props):
        """Handle when a device starts streaming audio"""
        try:
            if path in self.active_devices:
                return  # Already tracking this stream
            
            self.active_devices.add(path)
            
            # Get device information
            device_path = self.get_device_path(path)
            device_info = self.get_device_info(device_path)
            
            codec = props.get('Codec', 'Unknown')
            volume = props.get('Volume', 'Unknown')
            
            logger.info("=" * 60)
            logger.info("🎵 NEW BLUETOOTH AUDIO STREAM DETECTED")
            logger.info("=" * 60)
            logger.info(f"Device Name: {device_info.get('name', 'Unknown')}")
            logger.info(f"Device Address: {device_info.get('address', 'Unknown')}")
            logger.info(f"Device Alias: {device_info.get('alias', 'Unknown')}")
            logger.info(f"Transport: {path}")
            logger.info(f"Codec: {codec}")
            logger.info(f"Volume: {volume}")
            logger.info("=" * 60)
            
            # You can add custom actions here when a new stream is detected
            # For example: switch audio source, display notification, etc.
            
        except Exception as e:
            logger.error(f"Error handling stream start: {e}")
    
    def on_stream_stopped(self, path):
        """Handle when a device stops streaming audio"""
        try:
            if path not in self.active_devices:
                return
            
            self.active_devices.remove(path)
            
            logger.info("=" * 60)
            logger.info("🔇 BLUETOOTH AUDIO STREAM STOPPED")
            logger.info("=" * 60)
            logger.info(f"Transport: {path}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error handling stream stop: {e}")
    
    def get_device_path(self, transport_path):
        """Extract device path from transport path"""
        # Transport path is typically: /org/bluez/hci0/dev_XX_XX_XX_XX_XX_XX/fdX
        # Device path is: /org/bluez/hci0/dev_XX_XX_XX_XX_XX_XX
        parts = transport_path.split('/')
        if len(parts) >= 5:
            return '/'.join(parts[:5])
        return None
    
    def get_device_info(self, device_path):
        """Get device information from D-Bus"""
        try:
            if not device_path:
                return {}
            
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, device_path)
            device_props = dbus.Interface(device_obj, self.PROPERTIES_INTERFACE)
            props = device_props.GetAll(self.DEVICE_INTERFACE)
            
            return {
                'name': str(props.get('Name', 'Unknown')),
                'address': str(props.get('Address', 'Unknown')),
                'alias': str(props.get('Alias', 'Unknown')),
                'connected': bool(props.get('Connected', False)),
                'paired': bool(props.get('Paired', False))
            }
            
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return {}
    
    def run(self):
        """Start monitoring for BlueZ stream events"""
        logger.info("🎧 Starting BlueZ stream detector...")
        logger.info("Waiting for Bluetooth audio streams...")
        logger.info("Press Ctrl+C to stop")
        
        try:
            # Start GLib main loop
            loop = GLib.MainLoop()
            loop.run()
            
        except KeyboardInterrupt:
            logger.info("\n👋 Stopping BlueZ stream detector...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            sys.exit(1)


def main():
    """Main entry point"""
    detector = BlueZStreamDetector()
    detector.run()


if __name__ == '__main__':
    main()
