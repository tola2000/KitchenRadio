#!/usr/bin/env python3
"""
Bluetooth Event Monitor - Run this alongside KitchenRadio to track Bluetooth events

Usage:
    python3 monitor_bluetooth.py

This will show:
- Device connections/disconnections
- Property changes (paired, trusted, connected)
- Audio profile changes (A2DP, HSP, HFP)
- Signal strength (RSSI)
"""

import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import logging
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class BluetoothMonitor:
    """Monitor Bluetooth events via D-Bus"""
    
    BLUEZ_SERVICE = 'org.bluez'
    ADAPTER_INTERFACE = 'org.bluez.Adapter1'
    DEVICE_INTERFACE = 'org.bluez.Device1'
    PROPERTIES_INTERFACE = 'org.freedesktop.DBus.Properties'
    
    def __init__(self):
        """Initialize Bluetooth monitor"""
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        self.mainloop = GLib.MainLoop()
        
        # Subscribe to property changes
        self.bus.add_signal_receiver(
            self.on_properties_changed,
            signal_name='PropertiesChanged',
            dbus_interface=self.PROPERTIES_INTERFACE,
            path_keyword='path'
        )
        
        logger.info("=" * 70)
        logger.info("BLUETOOTH EVENT MONITOR STARTED")
        logger.info("=" * 70)
        logger.info("Monitoring all Bluetooth events...")
        logger.info("Press Ctrl+C to stop\n")
        
    def on_properties_changed(self, interface, changed, invalidated, path):
        """Handle property changes on Bluetooth devices"""
        try:
            # Filter for device changes
            if interface == self.DEVICE_INTERFACE:
                self._handle_device_change(path, changed, invalidated)
            elif interface == self.ADAPTER_INTERFACE:
                self._handle_adapter_change(path, changed)
                
        except Exception as e:
            logger.error(f"Error handling property change: {e}")
    
    def _handle_device_change(self, path, changed, invalidated):
        """Handle device property changes"""
        try:
            # Get device info
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, path)
            device_props = dbus.Interface(device_obj, self.PROPERTIES_INTERFACE)
            all_props = device_props.GetAll(self.DEVICE_INTERFACE)
            
            name = str(all_props.get('Name', 'Unknown'))
            address = str(all_props.get('Address', ''))
            
            # Show header
            logger.info(f"\n{'=' * 70}")
            logger.info(f"DEVICE EVENT: {name} ({address})")
            logger.info(f"Path: {path}")
            logger.info(f"{'-' * 70}")
            
            # Show changed properties
            for prop, value in changed.items():
                prop_str = str(prop)
                
                if prop_str == 'Connected':
                    icon = "🟢" if value else "🔴"
                    state = "CONNECTED" if value else "DISCONNECTED"
                    logger.info(f"{icon} {state}")
                    
                elif prop_str == 'Paired':
                    icon = "✅" if value else "❌"
                    state = "PAIRED" if value else "UNPAIRED"
                    logger.info(f"{icon} {state}")
                    
                elif prop_str == 'Trusted':
                    icon = "🔐" if value else "🔓"
                    state = "TRUSTED" if value else "UNTRUSTED"
                    logger.info(f"{icon} {state}")
                    
                elif prop_str == 'RSSI':
                    signal_strength = int(value)
                    bars = "▰" * max(0, (signal_strength + 100) // 20)
                    logger.info(f"📶 Signal Strength: {signal_strength} dBm {bars}")
                    
                elif prop_str == 'UUIDs':
                    logger.info(f"🔌 Service UUIDs changed:")
                    for uuid in value:
                        service_name = self._uuid_to_service_name(str(uuid))
                        logger.info(f"     {uuid} - {service_name}")
                        
                elif prop_str == 'ServicesResolved':
                    icon = "✅" if value else "⏳"
                    state = "RESOLVED" if value else "RESOLVING"
                    logger.info(f"{icon} Services {state}")
                    
                else:
                    logger.info(f"   {prop_str}: {value}")
            
            # Show current state summary
            logger.info(f"{'-' * 70}")
            logger.info("Current State:")
            logger.info(f"  Connected:  {all_props.get('Connected', False)}")
            logger.info(f"  Paired:     {all_props.get('Paired', False)}")
            logger.info(f"  Trusted:    {all_props.get('Trusted', False)}")
            logger.info(f"  Services:   {all_props.get('ServicesResolved', False)}")
            
            if all_props.get('RSSI'):
                logger.info(f"  RSSI:       {all_props.get('RSSI')} dBm")
            
            logger.info(f"{'=' * 70}\n")
            
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
    
    def _handle_adapter_change(self, path, changed):
        """Handle adapter property changes"""
        logger.info(f"\n{'=' * 70}")
        logger.info(f"ADAPTER EVENT: {path}")
        logger.info(f"{'-' * 70}")
        
        for prop, value in changed.items():
            prop_str = str(prop)
            
            if prop_str == 'Discoverable':
                icon = "👁️" if value else "🙈"
                state = "ON" if value else "OFF"
                logger.info(f"{icon} Discoverable: {state}")
                
            elif prop_str == 'Pairable':
                icon = "🔓" if value else "🔒"
                state = "ON" if value else "OFF"
                logger.info(f"{icon} Pairable: {state}")
                
            elif prop_str == 'Powered':
                icon = "⚡" if value else "💤"
                state = "ON" if value else "OFF"
                logger.info(f"{icon} Powered: {state}")
                
            else:
                logger.info(f"   {prop_str}: {value}")
        
        logger.info(f"{'=' * 70}\n")
    
    def _uuid_to_service_name(self, uuid):
        """Convert UUID to human-readable service name"""
        # Common Bluetooth UUIDs
        uuid_map = {
            '0000110a-0000-1000-8000-00805f9b34fb': 'A2DP Source (Audio)',
            '0000110b-0000-1000-8000-00805f9b34fb': 'A2DP Sink (Audio)',
            '0000110c-0000-1000-8000-00805f9b34fb': 'AVRCP Remote Control',
            '0000110e-0000-1000-8000-00805f9b34fb': 'AVRCP Target',
            '0000111e-0000-1000-8000-00805f9b34fb': 'Handsfree',
            '00001108-0000-1000-8000-00805f9b34fb': 'Headset',
            '0000111f-0000-1000-8000-00805f9b34fb': 'Handsfree Audio Gateway',
            '00001112-0000-1000-8000-00805f9b34fb': 'Headset Audio Gateway',
        }
        
        return uuid_map.get(uuid.lower(), 'Unknown Service')
    
    def run(self):
        """Run the monitor"""
        try:
            self.mainloop.run()
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 70)
            logger.info("BLUETOOTH MONITOR STOPPED")
            logger.info("=" * 70)
            self.mainloop.quit()


def main():
    """Main entry point"""
    try:
        monitor = BluetoothMonitor()
        monitor.run()
    except Exception as e:
        logger.error(f"Failed to start monitor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
