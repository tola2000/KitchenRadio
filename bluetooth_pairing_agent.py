#!/usr/bin/env python3
"""
Bluetooth Pairing Agent with Auto-Accept
Automatically accepts pairing requests to prevent timeout
"""

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
import logging
import sys
import signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


AGENT_PATH = "/test/agent"


class Agent(dbus.service.Object):
    """Bluetooth pairing agent that auto-accepts pairing requests"""
    
    def __init__(self, bus, path):
        """Initialize agent"""
        super().__init__(bus, path)
        self.bus = bus
        logger.info("🤖 Pairing agent initialized")
    
    @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
    def Release(self):
        """Release agent"""
        logger.info("Agent released")
    
    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        """Auto-authorize services"""
        logger.info(f"✅ Auto-authorizing service for device {device}")
        return
    
    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
        """Request PIN code - use default"""
        logger.info(f"📱 PIN requested for {device}")
        return "0000"
    
    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        """Request passkey - use default"""
        logger.info(f"🔑 Passkey requested for {device}")
        return dbus.UInt32(0)
    
    @dbus.service.method("org.bluez.Agent1", in_signature="ouq", out_signature="")
    def DisplayPasskey(self, device, passkey, entered):
        """Display passkey"""
        logger.info("=" * 60)
        logger.info(f"🔢 PAIRING CODE: {passkey:06d}")
        logger.info(f"   Device: {device}")
        logger.info(f"   Confirm this code on your device!")
        logger.info("=" * 60)
    
    @dbus.service.method("org.bluez.Agent1", in_signature="os", out_signature="")
    def DisplayPinCode(self, device, pincode):
        """Display PIN code"""
        logger.info("=" * 60)
        logger.info(f"🔢 PAIRING PIN: {pincode}")
        logger.info(f"   Device: {device}")
        logger.info(f"   Confirm this PIN on your device!")
        logger.info("=" * 60)
    
    @dbus.service.method("org.bluez.Agent1", in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        """Auto-confirm pairing"""
        logger.info("=" * 60)
        logger.info(f"✅ AUTO-CONFIRMING PAIRING")
        logger.info(f"   Device: {device}")
        logger.info(f"   Passkey: {passkey:06d}")
        logger.info(f"   Pairing accepted automatically!")
        logger.info("=" * 60)
        # Auto-accept by returning (no exception)
        return
    
    @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        """Auto-authorize"""
        logger.info(f"✅ Auto-authorizing device {device}")
        return
    
    @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
    def Cancel(self):
        """Cancel pairing"""
        logger.warning("⚠️  Pairing cancelled")


class BluetoothPairingService:
    """Bluetooth pairing service with agent"""
    
    def __init__(self):
        """Initialize service"""
        self.bus = None
        self.agent = None
        self.agent_manager = None
        self.running = False
        
        self.setup()
    
    def setup(self):
        """Setup D-Bus and agent"""
        try:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SystemBus()
            
            # Create agent
            self.agent = Agent(self.bus, AGENT_PATH)
            
            # Get agent manager
            obj = self.bus.get_object('org.bluez', '/org/bluez')
            self.agent_manager = dbus.Interface(obj, 'org.bluez.AgentManager1')
            
            # Register agent
            self.agent_manager.RegisterAgent(AGENT_PATH, "NoInputNoOutput")
            logger.info("✅ Agent registered with NoInputNoOutput capability")
            
            # Request default agent
            self.agent_manager.RequestDefaultAgent(AGENT_PATH)
            logger.info("✅ Set as default agent")
            
            # Configure adapter
            self.configure_adapter()
            
        except Exception as e:
            logger.error(f"Failed to setup: {e}")
            sys.exit(1)
    
    def configure_adapter(self):
        """Configure Bluetooth adapter"""
        try:
            adapter = dbus.Interface(
                self.bus.get_object('org.bluez', '/org/bluez/hci0'),
                'org.bluez.Adapter1'
            )
            
            props = dbus.Interface(
                self.bus.get_object('org.bluez', '/org/bluez/hci0'),
                'org.freedesktop.DBus.Properties'
            )
            
            # Power on
            props.Set('org.bluez.Adapter1', 'Powered', dbus.Boolean(True))
            logger.info("🔵 Bluetooth powered ON")
            
            # Always discoverable
            props.Set('org.bluez.Adapter1', 'Discoverable', dbus.Boolean(True))
            props.Set('org.bluez.Adapter1', 'DiscoverableTimeout', dbus.UInt32(0))
            logger.info("👁️  Discoverable: ON (always)")
            
            # Always pairable
            props.Set('org.bluez.Adapter1', 'Pairable', dbus.Boolean(True))
            props.Set('org.bluez.Adapter1', 'PairableTimeout', dbus.UInt32(0))
            logger.info("🔓 Pairable: ON (always)")
            
            # Monitor device connections
            self.bus.add_signal_receiver(
                self.on_properties_changed,
                signal_name='PropertiesChanged',
                dbus_interface='org.freedesktop.DBus.Properties',
                path_keyword='path'
            )
            
        except Exception as e:
            logger.error(f"Error configuring adapter: {e}")
    
    def on_properties_changed(self, interface, changed, invalidated, path):
        """Monitor device property changes"""
        try:
            if interface != 'org.bluez.Device1':
                return
            
            if 'Connected' in changed:
                device_obj = self.bus.get_object('org.bluez', path)
                device_props = dbus.Interface(device_obj, 'org.freedesktop.DBus.Properties')
                all_props = device_props.GetAll('org.bluez.Device1')
                
                name = str(all_props.get('Name', 'Unknown'))
                address = str(all_props.get('Address', 'Unknown'))
                
                if changed['Connected']:
                    logger.info("=" * 60)
                    logger.info(f"🟢 DEVICE CONNECTED")
                    logger.info(f"   Name: {name}")
                    logger.info(f"   Address: {address}")
                    logger.info("=" * 60)
                    
                    # Auto-trust the device
                    try:
                        device_props.Set('org.bluez.Device1', 'Trusted', dbus.Boolean(True))
                        logger.info("✅ Device auto-trusted")
                    except Exception as e:
                        logger.warning(f"Could not trust device: {e}")
                else:
                    logger.info(f"🔴 Device disconnected: {name} ({address})")
                    
        except Exception as e:
            logger.error(f"Error in property change handler: {e}")
    
    def run(self):
        """Run the service"""
        logger.info("=" * 60)
        logger.info("🔵 BLUETOOTH PAIRING SERVICE")
        logger.info("=" * 60)
        logger.info("🤖 Auto-accepting all pairing requests")
        logger.info("📱 Pairing codes will be automatically confirmed")
        logger.info("")
        logger.info("Your device is now ready to pair!")
        logger.info("Look for 'raspberrypi' or 'KitchenRadio' on your phone")
        logger.info("")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        self.running = True
        
        try:
            loop = GLib.MainLoop()
            loop.run()
        except KeyboardInterrupt:
            logger.info("\n👋 Stopping pairing service...")
            self.running = False
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            return 1
        
        return 0
    
    def cleanup(self):
        """Cleanup on exit"""
        try:
            if self.agent_manager:
                self.agent_manager.UnregisterAgent(AGENT_PATH)
                logger.info("Agent unregistered")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"\nReceived signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run service
    service = BluetoothPairingService()
    
    try:
        return service.run()
    finally:
        service.cleanup()


if __name__ == '__main__':
    sys.exit(main())
