#!/usr/bin/env python3
"""
Bluetooth Controller for KitchenRadio

Manages Bluetooth audio connections with pairing and auto-connect support.
Can be triggered to accept pairing from new devices on-demand.
"""

import dbus
import dbus.mainloop.glib
import dbus.service
from gi.repository import GLib
import logging
import threading
import time
import subprocess
import re
from typing import Optional, Callable, Set

logger = logging.getLogger(__name__)


class AutoPairAgent(dbus.service.Object):
    """Bluetooth pairing agent that auto-accepts all pairing requests"""
    
    AGENT_INTERFACE = 'org.bluez.Agent1'
    AGENT_PATH = '/org/bluez/kitchenradio_agent'
    
    def __init__(self, bus):
        super().__init__(bus, self.AGENT_PATH)
        self.bus = bus
        logger.info("🤖 Auto-pair agent initialized")
    
    @dbus.service.method(AGENT_INTERFACE, in_signature='os', out_signature='')
    def AuthorizeService(self, device, uuid):
        """Auto-authorize all services"""
        logger.info(f"✅ Auto-authorizing service {uuid} for {device}")
        return
    
    @dbus.service.method(AGENT_INTERFACE, in_signature='o', out_signature='u')
    def RequestPasskey(self, device):
        """Return passkey (for older pairing methods)"""
        logger.info(f"🔑 Passkey requested for {device}, returning 0")
        return dbus.UInt32(0)
    
    @dbus.service.method(AGENT_INTERFACE, in_signature='ouq', out_signature='')
    def DisplayPasskey(self, device, passkey, entered):
        """Display passkey (for confirmation)"""
        logger.info(f"🔢 Display passkey {passkey:06d} for {device}")
        return
    
    @dbus.service.method(AGENT_INTERFACE, in_signature='os', out_signature='')
    def DisplayPinCode(self, device, pincode):
        """Display PIN code"""
        logger.info(f"🔢 Display PIN {pincode} for {device}")
        return
    
    @dbus.service.method(AGENT_INTERFACE, in_signature='ou', out_signature='')
    def RequestConfirmation(self, device, passkey):
        """Auto-confirm passkey"""
        logger.info(f"✅ Auto-confirming passkey {passkey:06d} for {device}")
        return
    
    @dbus.service.method(AGENT_INTERFACE, in_signature='o', out_signature='')
    def RequestAuthorization(self, device):
        """Auto-authorize device"""
        logger.info(f"✅ Auto-authorizing {device}")
        return
    
    @dbus.service.method(AGENT_INTERFACE, in_signature='', out_signature='')
    def Cancel(self):
        """Handle cancellation"""
        logger.warning("⚠️  Pairing cancelled")
        return


class BluetoothController:
    """
    Bluetooth audio controller for KitchenRadio.
    
    Manages Bluetooth connections with on-demand pairing mode.
    """
    
    BLUEZ_SERVICE = 'org.bluez'
    ADAPTER_INTERFACE = 'org.bluez.Adapter1'
    DEVICE_INTERFACE = 'org.bluez.Device1'
    PROPERTIES_INTERFACE = 'org.freedesktop.DBus.Properties'
    OBJECT_MANAGER_INTERFACE = 'org.freedesktop.DBus.ObjectManager'
    AGENT_MANAGER_INTERFACE = 'org.bluez.AgentManager1'
    
    def __init__(self, adapter_path='/org/bluez/hci0'):
        """
        Initialize Bluetooth controller.
        
        Args:
            adapter_path: Path to Bluetooth adapter (default: /org/bluez/hci0)
        """
        self.adapter_path = adapter_path
        self.bus: Optional[dbus.SystemBus] = None
        self.adapter = None
        self.adapter_props = None
        self.obj_manager = None
        self.agent: Optional[AutoPairAgent] = None
        self.mainloop: Optional[GLib.MainLoop] = None
        self.mainloop_thread: Optional[threading.Thread] = None
        
        # State tracking
        self.connected_devices: Set[str] = set()  # MAC addresses
        self.paired_devices: Set[str] = set()
        self.pairing_mode = False
        self.running = False
        self.current_device_path: Optional[str] = None
        self.current_device_name: Optional[str] = None
        
        # Callbacks
        self.on_device_connected: Optional[Callable[[str, str], None]] = None  # (name, mac)
        self.on_device_disconnected: Optional[Callable[[str, str], None]] = None  # (name, mac)
        self.on_stream_started: Optional[Callable, None] = None
        
        # Initialize D-Bus in separate thread
        self._setup_dbus_threaded()
    
    def _setup_dbus_threaded(self):
        """Setup D-Bus connection in background thread"""
        def setup_thread():
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
                
                # Subscribe to property changes
                self.bus.add_signal_receiver(
                    self.on_properties_changed,
                    signal_name='PropertiesChanged',
                    dbus_interface=self.PROPERTIES_INTERFACE,
                    path_keyword='path'
                )
                
                # Register agent
                self._register_agent()
                
                # Initialize adapter
                self._initialize_adapter()
                
                # Scan existing devices
                self._scan_existing_devices()
                
                logger.info("✅ BluetoothController: D-Bus connection established")
                
                # Start GLib main loop
                self.mainloop = GLib.MainLoop()
                self.running = True
                self.mainloop.run()
                
            except Exception as e:
                logger.error(f"❌ BluetoothController: Failed to setup D-Bus: {e}")
                self.running = False
        
        self.mainloop_thread = threading.Thread(target=setup_thread, daemon=True)
        self.mainloop_thread.start()
        
        # Wait a bit for initialization
        time.sleep(1)
    
    def _register_agent(self):
        """Register auto-pairing agent"""
        try:
            self.agent = AutoPairAgent(self.bus)
            
            agent_manager_obj = self.bus.get_object(self.BLUEZ_SERVICE, '/org/bluez')
            agent_manager = dbus.Interface(agent_manager_obj, self.AGENT_MANAGER_INTERFACE)
            
            # Register with NoInputNoOutput capability (auto-accept)
            agent_manager.RegisterAgent(AutoPairAgent.AGENT_PATH, 'NoInputNoOutput')
            agent_manager.RequestDefaultAgent(AutoPairAgent.AGENT_PATH)
            
            logger.info("✅ BluetoothController: Pairing agent registered")
            
        except Exception as e:
            logger.error(f"❌ BluetoothController: Failed to register agent: {e}")
            raise
    
    def _initialize_adapter(self):
        """Initialize Bluetooth adapter"""
        try:
            # Power on
            self.adapter_props.Set(self.ADAPTER_INTERFACE, 'Powered', dbus.Boolean(True))
            logger.info("🔵 Bluetooth powered ON")
            
            # Start in non-discoverable mode (will enable when pairing mode is activated)
            self.adapter_props.Set(self.ADAPTER_INTERFACE, 'Discoverable', dbus.Boolean(False))
            logger.info("👁️  Discoverable: OFF (use pairing mode to enable)")
            
            # Pairable with timeout
            self.adapter_props.Set(self.ADAPTER_INTERFACE, 'Pairable', dbus.Boolean(True))
            logger.info("🔓 Pairable: ON")
            
        except Exception as e:
            logger.error(f"❌ Error initializing adapter: {e}")
    
    def _scan_existing_devices(self):
        """Scan for already paired/connected devices"""
        try:
            objects = self.obj_manager.GetManagedObjects()
            
            for path, interfaces in objects.items():
                if self.DEVICE_INTERFACE in interfaces:
                    props = interfaces[self.DEVICE_INTERFACE]
                    address = str(props.get('Address', ''))
                    name = str(props.get('Name', 'Unknown'))
                    
                    if props.get('Paired', False):
                        self.paired_devices.add(address)
                        logger.info(f"📱 Already paired: {name} ({address})")
                    
                    if props.get('Connected', False):
                        self.connected_devices.add(address)
                        self.current_device_path = path
                        self.current_device_name = name
                        logger.info(f"🟢 Already connected: {name} ({address})")
                        
        except Exception as e:
            logger.error(f"Error scanning existing devices: {e}")
    
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
            
            # Handle pairing
            if 'Paired' in changed and changed['Paired']:
                if address not in self.paired_devices:
                    self.paired_devices.add(address)
                    logger.info(f"✅ Device paired: {name} ({address})")
                    
                    # Trust the device
                    self._trust_device(path)
                    
                    # If in pairing mode, connect after a delay
                    if self.pairing_mode:
                        logger.info("⏳ Waiting 3s before connecting...")
                        GLib.timeout_add(3000, self._connect_device, path, name, address)
                        # Exit pairing mode
                        self.exit_pairing_mode()
            
            # Handle connection
            if 'Connected' in changed:
                if changed['Connected']:
                    if address not in self.connected_devices:
                        self.connected_devices.add(address)
                        self.current_device_path = path
                        self.current_device_name = name
                        logger.info(f"🟢 DEVICE CONNECTED: {name} ({address})")
                        
                        # Trigger callback
                        if self.on_device_connected:
                            self.on_device_connected(name, address)
                else:
                    if address in self.connected_devices:
                        self.connected_devices.remove(address)
                        if self.current_device_path == path:
                            self.current_device_path = None
                            self.current_device_name = None
                        logger.info(f"🔴 DEVICE DISCONNECTED: {name} ({address})")
                        
                        # Trigger callback
                        if self.on_device_disconnected:
                            self.on_device_disconnected(name, address)
                            
        except Exception as e:
            logger.error(f"Error handling property change: {e}")
    
    def _trust_device(self, device_path):
        """Trust a device (enable auto-reconnect)"""
        try:
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, device_path)
            device_props = dbus.Interface(device_obj, self.PROPERTIES_INTERFACE)
            device_props.Set(self.DEVICE_INTERFACE, 'Trusted', dbus.Boolean(True))
            logger.info("✅ Device trusted (auto-reconnect enabled)")
        except Exception as e:
            logger.error(f"Error trusting device: {e}")
    
    def _connect_device(self, device_path, name, address):
        """Connect to a device and wait for audio profile"""
        try:
            logger.info(f"🔌 Connecting to {name}...")
            
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, device_path)
            device = dbus.Interface(device_obj, self.DEVICE_INTERFACE)
            device_props = dbus.Interface(device_obj, self.PROPERTIES_INTERFACE)
            
            # Check if already connected
            props = device_props.GetAll(self.DEVICE_INTERFACE)
            if props.get('Connected', False):
                logger.info(f"✅ Already connected to {name}")
                return False
            
            # Connect
            device.Connect()
            
            # Wait for audio profile
            logger.info(f"⏳ Waiting for audio profile to establish...")
            max_attempts = 10
            for attempt in range(max_attempts):
                time.sleep(1)
                props = device_props.GetAll(self.DEVICE_INTERFACE)
                
                # Check for A2DP audio UUIDs
                uuids = props.get('UUIDs', [])
                audio_uuids = [
                    '0000110b-0000-1000-8000-00805f9b34fb',  # A2DP Sink
                    '0000110a-0000-1000-8000-00805f9b34fb',  # A2DP Source
                ]
                
                if any(uuid.lower() in [u.lower() for u in uuids] for uuid in audio_uuids):
                    logger.info(f"✅ Audio profile established!")
                    logger.info(f"🎵 {name} ready for audio streaming")
                    
                    if self.on_stream_started:
                        self.on_stream_started()
                    
                    return False
            
            logger.warning(f"⚠️  Audio profile didn't establish after {max_attempts}s")
            
        except dbus.exceptions.DBusException as e:
            error_name = e.get_dbus_name()
            if "AlreadyConnected" in error_name:
                logger.info(f"✅ Already connected to {name}")
            else:
                logger.error(f"❌ Error connecting to {name}: {e}")
        except Exception as e:
            logger.error(f"❌ Error connecting to {name}: {e}")
        
        return False
    
    def enter_pairing_mode(self, timeout_seconds=60):
        """
        Enter pairing mode - make discoverable and accept next device.
        
        Args:
            timeout_seconds: How long to stay in pairing mode (default: 60s)
        """
        if not self.running or not self.adapter_props:
            logger.error("❌ Bluetooth not initialized")
            return False
        
        try:
            logger.info("=" * 60)
            logger.info("🔵 ENTERING PAIRING MODE")
            logger.info(f"   Ready to pair with new device for {timeout_seconds}s")
            logger.info("=" * 60)
            
            self.pairing_mode = True
            
            # Make discoverable
            self.adapter_props.Set(self.ADAPTER_INTERFACE, 'Discoverable', dbus.Boolean(True))
            self.adapter_props.Set(self.ADAPTER_INTERFACE, 'DiscoverableTimeout', dbus.UInt32(timeout_seconds))
            
            # Schedule exit from pairing mode
            GLib.timeout_add(timeout_seconds * 1000, self.exit_pairing_mode)
            
            logger.info("👁️  Bluetooth is now DISCOVERABLE")
            logger.info("📱 Pair your device now!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error entering pairing mode: {e}")
            return False
    
    def exit_pairing_mode(self):
        """Exit pairing mode and make non-discoverable"""
        if not self.pairing_mode:
            return False
        
        try:
            self.pairing_mode = False
            
            if self.adapter_props:
                self.adapter_props.Set(self.ADAPTER_INTERFACE, 'Discoverable', dbus.Boolean(False))
                logger.info("👁️  Pairing mode ended - no longer discoverable")
            
        except Exception as e:
            logger.error(f"Error exiting pairing mode: {e}")
        
        return False  # Don't reschedule
    
    def disconnect_current(self):
        """Disconnect currently connected device"""
        if not self.current_device_path:
            logger.info("ℹ️  No device currently connected")
            return False
        
        try:
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, self.current_device_path)
            device = dbus.Interface(device_obj, self.DEVICE_INTERFACE)
            device.Disconnect()
            logger.info(f"🔌 Disconnected: {self.current_device_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting device: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if any device is connected"""
        return len(self.connected_devices) > 0
    
    def get_connected_device_name(self) -> Optional[str]:
        """Get name of currently connected device"""
        return self.current_device_name
    
    def get_volume(self) -> Optional[int]:
        """
        Get current volume of Bluetooth audio sink from PulseAudio.
        
        Returns:
            Volume level (0-100) or None if unable to get volume
        """
        try:
            # Get list of sinks with their volumes
            result = subprocess.run(
                ['pactl', 'list', 'sinks'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode != 0:
                logger.debug("pactl command failed")
                return None
            
            # Parse output to find bluez sink and its volume
            lines = result.stdout.split('\n')
            in_bluez_sink = False
            
            for i, line in enumerate(lines):
                # Look for bluez sink
                if 'Name:' in line and 'bluez' in line.lower():
                    in_bluez_sink = True
                    logger.debug(f"Found Bluetooth sink: {line.strip()}")
                elif in_bluez_sink:
                    # Look for Volume line after finding bluez sink
                    if 'Volume:' in line:
                        # Extract percentage: "Volume: front-left: 65536 / 100% ..."
                        # Use regex to find percentage
                        match = re.search(r'(\d+)%', line)
                        if match:
                            volume = int(match.group(1))
                            logger.debug(f"Bluetooth volume: {volume}%")
                            return volume
                    # Stop looking if we hit the next sink
                    elif 'Sink #' in line or 'Name:' in line:
                        break
            
            logger.debug("No Bluetooth sink volume found")
            return None
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout getting Bluetooth volume")
            return None
        except Exception as e:
            logger.error(f"Error getting Bluetooth volume: {e}")
            return None
    
    def set_volume(self, volume: int) -> bool:
        """
        Set volume of Bluetooth audio sink in PulseAudio.
        
        Args:
            volume: Volume level (0-100)
            
        Returns:
            True if successful, False otherwise
        """
        if not 0 <= volume <= 100:
            logger.error(f"Invalid volume: {volume}. Must be 0-100")
            return False
        
        try:
            # First, find the bluez sink name
            result = subprocess.run(
                ['pactl', 'list', 'sinks', 'short'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode != 0:
                return False
            
            # Find bluez sink
            bluez_sink = None
            for line in result.stdout.split('\n'):
                if 'bluez' in line.lower():
                    # Extract sink name (second column)
                    parts = line.split()
                    if len(parts) >= 2:
                        bluez_sink = parts[1]
                        break
            
            if not bluez_sink:
                logger.warning("No Bluetooth sink found")
                return False
            
            # Set volume
            result = subprocess.run(
                ['pactl', 'set-sink-volume', bluez_sink, f'{volume}%'],
                capture_output=True,
                timeout=2
            )
            
            if result.returncode == 0:
                logger.info(f"🔊 Bluetooth volume set to {volume}%")
                return True
            else:
                logger.error("Failed to set Bluetooth volume")
                return False
                
        except Exception as e:
            logger.error(f"Error setting Bluetooth volume: {e}")
            return False
    
    def volume_up(self, step: int = 5) -> bool:
        """
        Increase Bluetooth volume by specified step.
        
        Args:
            step: Volume increase step (default 5)
            
        Returns:
            True if successful
        """
        current = self.get_volume()
        if current is None:
            return False
        
        new_volume = min(100, current + step)
        return self.set_volume(new_volume)
    
    def volume_down(self, step: int = 5) -> bool:
        """
        Decrease Bluetooth volume by specified step.
        
        Args:
            step: Volume decrease step (default 5)
            
        Returns:
            True if successful
        """
        current = self.get_volume()
        if current is None:
            return False
        
        new_volume = max(0, current - step)
        return self.set_volume(new_volume)
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up BluetoothController...")
        
        if self.agent and self.bus:
            try:
                agent_manager_obj = self.bus.get_object(self.BLUEZ_SERVICE, '/org/bluez')
                agent_manager = dbus.Interface(agent_manager_obj, self.AGENT_MANAGER_INTERFACE)
                agent_manager.UnregisterAgent(AutoPairAgent.AGENT_PATH)
                logger.info("✅ Agent unregistered")
            except Exception as e:
                logger.error(f"Error unregistering agent: {e}")
        
        if self.mainloop:
            self.mainloop.quit()
            self.running = False
        
        logger.info("✅ BluetoothController cleaned up")
