#!/usr/bin/env python3
"""
BlueZ Client - Low-level D-Bus interface to BlueZ Bluetooth stack

Handles all D-Bus communication with BlueZ for:
- Adapter management (power, discovery, pairing)
- Device management (pairing, connection, trust)
- Property monitoring
- Agent registration
"""

import dbus
import dbus.mainloop.glib
import dbus.service
from gi.repository import GLib
import logging
from typing import Optional, Callable, Dict, Any, List

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


class BlueZClient:
    """
    Low-level BlueZ D-Bus client.
    
    Provides interface to BlueZ Bluetooth stack via D-Bus for:
    - Adapter control (power, discovery, pairing mode)
    - Device operations (pair, connect, disconnect, trust)
    - Property monitoring
    - Agent management
    """
    
    BLUEZ_SERVICE = 'org.bluez'
    ADAPTER_INTERFACE = 'org.bluez.Adapter1'
    DEVICE_INTERFACE = 'org.bluez.Device1'
    PROPERTIES_INTERFACE = 'org.freedesktop.DBus.Properties'
    OBJECT_MANAGER_INTERFACE = 'org.freedesktop.DBus.ObjectManager'
    AGENT_MANAGER_INTERFACE = 'org.bluez.AgentManager1'
    
    def __init__(self, adapter_path: str = '/org/bluez/hci0'):
        """
        Initialize BlueZ client.
        
        Args:
            adapter_path: D-Bus path to Bluetooth adapter
        """
        self.adapter_path = adapter_path
        self.bus: Optional[dbus.SystemBus] = None
        self.adapter = None
        self.adapter_props = None
        self.obj_manager = None
        self.agent: Optional[AutoPairAgent] = None
        
        # Callbacks
        self.on_properties_changed: Optional[Callable[[str, Dict, List, str], None]] = None
        
        # Initialize D-Bus
        self._setup_dbus()
    
    def _setup_dbus(self):
        """Setup D-Bus connection"""
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
                self._on_properties_changed_internal,
                signal_name='PropertiesChanged',
                dbus_interface=self.PROPERTIES_INTERFACE,
                path_keyword='path'
            )
            
            logger.info("✅ BlueZ D-Bus connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup BlueZ D-Bus: {e}")
            raise
    
    def _on_properties_changed_internal(self, interface, changed, invalidated, path):
        """Internal handler for property changes - forwards to callback"""
        if self.on_properties_changed:
            self.on_properties_changed(interface, dict(changed), list(invalidated), path)
    
    def register_agent(self) -> bool:
        """
        Register auto-pairing agent with BlueZ.
        
        Returns:
            True if successful
        """
        try:
            self.agent = AutoPairAgent(self.bus)
            
            agent_manager_obj = self.bus.get_object(self.BLUEZ_SERVICE, '/org/bluez')
            agent_manager = dbus.Interface(agent_manager_obj, self.AGENT_MANAGER_INTERFACE)
            
            # Register with NoInputNoOutput capability (auto-accept)
            agent_manager.RegisterAgent(AutoPairAgent.AGENT_PATH, 'NoInputNoOutput')
            agent_manager.RequestDefaultAgent(AutoPairAgent.AGENT_PATH)
            
            logger.info("✅ BlueZ pairing agent registered")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to register BlueZ agent: {e}")
            return False
    
    def unregister_agent(self) -> bool:
        """
        Unregister pairing agent.
        
        Returns:
            True if successful
        """
        if not self.agent or not self.bus:
            return False
        
        try:
            agent_manager_obj = self.bus.get_object(self.BLUEZ_SERVICE, '/org/bluez')
            agent_manager = dbus.Interface(agent_manager_obj, self.AGENT_MANAGER_INTERFACE)
            agent_manager.UnregisterAgent(AutoPairAgent.AGENT_PATH)
            logger.info("✅ BlueZ agent unregistered")
            return True
        except Exception as e:
            logger.error(f"Error unregistering agent: {e}")
            return False
    
    def set_adapter_property(self, property_name: str, value: Any) -> bool:
        """
        Set adapter property.
        
        Args:
            property_name: Property name (e.g., 'Powered', 'Discoverable')
            value: Property value
            
        Returns:
            True if successful
        """
        try:
            if property_name == 'Powered':
                value = dbus.Boolean(value)
            elif property_name in ['Discoverable', 'Pairable']:
                value = dbus.Boolean(value)
            elif property_name == 'DiscoverableTimeout':
                value = dbus.UInt32(value)
            
            self.adapter_props.Set(self.ADAPTER_INTERFACE, property_name, value)
            return True
        except Exception as e:
            logger.error(f"Error setting adapter property {property_name}: {e}")
            return False
    
    def get_adapter_property(self, property_name: str) -> Optional[Any]:
        """
        Get adapter property.
        
        Args:
            property_name: Property name
            
        Returns:
            Property value or None
        """
        try:
            return self.adapter_props.Get(self.ADAPTER_INTERFACE, property_name)
        except Exception as e:
            logger.debug(f"Could not get adapter property {property_name}: {e}")
            return None
    
    def get_managed_objects(self) -> Dict[str, Dict[str, Dict]]:
        """
        Get all managed objects from BlueZ.
        
        Returns:
            Dictionary of objects with their interfaces and properties
        """
        try:
            return self.obj_manager.GetManagedObjects()
        except Exception as e:
            logger.error(f"Error getting managed objects: {e}")
            return {}
    
    def get_device_properties(self, device_path: str) -> Optional[Dict[str, Any]]:
        """
        Get all properties for a device.
        
        Args:
            device_path: D-Bus path to device
            
        Returns:
            Dictionary of device properties or None
        """
        try:
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, device_path)
            device_props = dbus.Interface(device_obj, self.PROPERTIES_INTERFACE)
            return device_props.GetAll(self.DEVICE_INTERFACE)
        except Exception as e:
            logger.debug(f"Could not get device properties for {device_path}: {e}")
            return None
    
    def set_device_property(self, device_path: str, property_name: str, value: Any) -> bool:
        """
        Set device property.
        
        Args:
            device_path: D-Bus path to device
            property_name: Property name (e.g., 'Trusted')
            value: Property value
            
        Returns:
            True if successful
        """
        try:
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, device_path)
            device_props = dbus.Interface(device_obj, self.PROPERTIES_INTERFACE)
            
            if property_name == 'Trusted':
                value = dbus.Boolean(value)
            
            device_props.Set(self.DEVICE_INTERFACE, property_name, value)
            return True
        except Exception as e:
            logger.error(f"Error setting device property {property_name}: {e}")
            return False
    
    def connect_device(self, device_path: str) -> bool:
        """
        Connect to a device.
        
        Args:
            device_path: D-Bus path to device
            
        Returns:
            True if successful
        """
        try:
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, device_path)
            device = dbus.Interface(device_obj, self.DEVICE_INTERFACE)
            device.Connect()
            return True
        except dbus.exceptions.DBusException as e:
            error_name = e.get_dbus_name()
            if "AlreadyConnected" in error_name:
                logger.debug("Device already connected")
                return True
            logger.error(f"Error connecting device: {e}")
            return False
        except Exception as e:
            logger.error(f"Error connecting device: {e}")
            return False
    
    def disconnect_device(self, device_path: str) -> bool:
        """
        Disconnect a device.
        
        Args:
            device_path: D-Bus path to device
            
        Returns:
            True if successful
        """
        try:
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, device_path)
            device = dbus.Interface(device_obj, self.DEVICE_INTERFACE)
            device.Disconnect()
            return True
        except Exception as e:
            logger.error(f"Error disconnecting device: {e}")
            return False
    
    def pair_device(self, device_path: str) -> bool:
        """
        Pair with a device.
        
        Args:
            device_path: D-Bus path to device
            
        Returns:
            True if successful
        """
        try:
            device_obj = self.bus.get_object(self.BLUEZ_SERVICE, device_path)
            device = dbus.Interface(device_obj, self.DEVICE_INTERFACE)
            device.Pair()
            return True
        except Exception as e:
            logger.error(f"Error pairing device: {e}")
            return False
    
    def remove_device(self, device_path: str) -> bool:
        """
        Remove (unpair) a device.
        
        Args:
            device_path: D-Bus path to device
            
        Returns:
            True if successful
        """
        try:
            self.adapter.RemoveDevice(device_path)
            return True
        except Exception as e:
            logger.error(f"Error removing device: {e}")
            return False
    
    def start_discovery(self) -> bool:
        """
        Start device discovery.
        
        Returns:
            True if successful
        """
        try:
            self.adapter.StartDiscovery()
            return True
        except Exception as e:
            logger.error(f"Error starting discovery: {e}")
            return False
    
    def stop_discovery(self) -> bool:
        """
        Stop device discovery.
        
        Returns:
            True if successful
        """
        try:
            self.adapter.StopDiscovery()
            return True
        except Exception as e:
            logger.error(f"Error stopping discovery: {e}")
            return False
