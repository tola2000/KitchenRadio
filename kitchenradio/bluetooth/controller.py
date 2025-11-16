#!/usr/bin/env python3
"""
Bluetooth Controller for KitchenRadio

High-level Bluetooth audio management:
- Device pairing and connection
- Pairing mode control
- Volume management via PulseAudio
- Device state tracking
"""

from gi.repository import GLib
import logging
import threading
import time
import subprocess
import re
from typing import Optional, Callable, Set, Dict, Any

from .bluez_client import BlueZClient

logger = logging.getLogger(__name__)


class BluetoothController:
    """
    High-level Bluetooth audio controller for KitchenRadio.
    
    Manages Bluetooth device connections with on-demand pairing mode
    and PulseAudio integration for volume control.
    """
    
    def __init__(self, adapter_path='/org/bluez/hci0'):
        """
        Initialize Bluetooth controller.
        
        Args:
            adapter_path: Path to Bluetooth adapter (default: /org/bluez/hci0)
        """
        self.adapter_path = adapter_path
        self.client: Optional[BlueZClient] = None
        self.mainloop: Optional[GLib.MainLoop] = None
        self.mainloop_thread: Optional[threading.Thread] = None
        
        # State tracking
        self.connected_devices: Set[str] = set()  # MAC addresses
        self.paired_devices: Set[str] = set()
        self.pairing_mode = False
        self.running = False
        self.current_device_path: Optional[str] = None
        self.current_device_name: Optional[str] = None
        
        # Volume cache (to avoid constant PulseAudio polling)
        self._cached_volume: Optional[int] = None
        self._volume_cache_valid = False
        
        # Callbacks
        self.on_device_connected: Optional[Callable[[str, str], None]] = None  # (name, mac)
        self.on_device_disconnected: Optional[Callable[[str, str], None]] = None  # (name, mac)
        self.on_stream_started: Optional[Callable] = None
        
        # Initialize BlueZ client in separate thread
        self._setup_client_threaded()
    
    def _setup_client_threaded(self):
        """Setup BlueZ client in background thread with GLib main loop"""
        def setup_thread():
            try:
                # Create BlueZ client
                self.client = BlueZClient(self.adapter_path)
                
                # Set up property change callback
                self.client.on_properties_changed = self._on_properties_changed
                
                # Register agent
                self.client.register_agent()
                
                # Initialize adapter
                self._initialize_adapter()
                
                # Scan existing devices
                self._scan_existing_devices()
                
                logger.info("✅ BluetoothController: Client initialized")
                
                # Start GLib main loop
                self.mainloop = GLib.MainLoop()
                self.running = True
                self.mainloop.run()
                
            except Exception as e:
                logger.error(f"❌ BluetoothController: Failed to setup client: {e}")
                self.running = False
        
        self.mainloop_thread = threading.Thread(target=setup_thread, daemon=True)
        self.mainloop_thread.start()
        
        # Wait a bit for initialization
        time.sleep(1)
    
    def _initialize_adapter(self):
        """Initialize Bluetooth adapter"""
        if not self.client:
            return
        
        try:
            # Power on
            self.client.set_adapter_property('Powered', True)
            logger.info("🔵 Bluetooth powered ON")
            
            # Start in non-discoverable mode (will enable when pairing mode is activated)
            self.client.set_adapter_property('Discoverable', False)
            logger.info("👁️  Discoverable: OFF (use pairing mode to enable)")
            
            # Pairable with timeout
            self.client.set_adapter_property('Pairable', True)
            logger.info("🔓 Pairable: ON")
            
        except Exception as e:
            logger.error(f"❌ Error initializing adapter: {e}")
    
    def _scan_existing_devices(self):
        """Scan for already paired/connected devices"""
        if not self.client:
            return
        
        try:
            objects = self.client.get_managed_objects()
            
            for path, interfaces in objects.items():
                if 'org.bluez.Device1' in interfaces:
                    props = interfaces['org.bluez.Device1']
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
    
    def _on_properties_changed(self, interface: str, changed: Dict, invalidated: list, path: str):
        """Handle property changes from BlueZ client"""
        try:
            if interface != 'org.bluez.Device1':
                return
            
            # Debug logging
            logger.debug(f"🔍 D-Bus Property Change on {path}")
            logger.debug(f"   Changed properties: {changed}")
            if invalidated:
                logger.debug(f"   Invalidated: {invalidated}")
            
            # Get device info
            all_props = self.client.get_device_properties(path)
            if not all_props:
                return
            
            address = str(all_props.get('Address', ''))
            name = str(all_props.get('Name', 'Unknown'))
            
            # Debug logging
            logger.debug(f"   Device: {name} ({address})")
            logger.debug(f"   Connected: {all_props.get('Connected', False)}")
            logger.debug(f"   Paired: {all_props.get('Paired', False)}")
            logger.debug(f"   Trusted: {all_props.get('Trusted', False)}")
            
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
                        
                        # Prevent PulseAudio from auto-suspending the Bluetooth sink
                        self._unsuspend_bluetooth_sink()
                        
                        # Refresh volume cache on connection
                        GLib.timeout_add(2000, self.refresh_volume)  # Delay 2s for sink to be ready
                        
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
                        
                        # Invalidate volume cache on disconnection
                        self._volume_cache_valid = False
                        self._cached_volume = None
                        
                        # Trigger callback
                        if self.on_device_disconnected:
                            self.on_device_disconnected(name, address)
                            
        except Exception as e:
            logger.error(f"Error handling property change: {e}")
    
    def _trust_device(self, device_path: str):
        """Trust a device (enable auto-reconnect)"""
        if not self.client:
            return
        
        if self.client.set_device_property(device_path, 'Trusted', True):
            logger.info("✅ Device trusted (auto-reconnect enabled)")
    
    def _connect_device(self, device_path: str, name: str, address: str):
        """Connect to a device and wait for audio profile"""
        if not self.client:
            return False
        
        try:
            logger.info(f"🔌 Connecting to {name}...")
            
            # Check if already connected
            props = self.client.get_device_properties(device_path)
            if props and props.get('Connected', False):
                logger.info(f"✅ Already connected to {name}")
                return False
            
            # Connect
            if not self.client.connect_device(device_path):
                return False
            
            # Wait for audio profile
            logger.info(f"⏳ Waiting for audio profile to establish...")
            max_attempts = 10
            for attempt in range(max_attempts):
                time.sleep(1)
                props = self.client.get_device_properties(device_path)
                if not props:
                    continue
                
                # Check for A2DP audio UUIDs
                uuids = props.get('UUIDs', [])
                audio_uuids = [
                    '0000110b-0000-1000-8000-00805f9b34fb',  # A2DP Sink
                    '0000110a-0000-1000-8000-00805f9b34fb',  # A2DP Source
                ]
                
                if any(uuid.lower() in [str(u).lower() for u in uuids] for uuid in audio_uuids):
                    logger.info(f"✅ Audio profile established!")
                    logger.info(f"🎵 {name} ready for audio streaming")
                    
                    if self.on_stream_started:
                        self.on_stream_started()
                    
                    return False
            
            logger.warning(f"⚠️  Audio profile didn't establish after {max_attempts}s")
            
        except Exception as e:
            logger.error(f"❌ Error connecting to {name}: {e}")
        
        return False
    
    def enter_pairing_mode(self, timeout_seconds: int = 60) -> bool:
        """
        Enter pairing mode - make discoverable and accept next device.
        
        Args:
            timeout_seconds: How long to stay in pairing mode (default: 60s)
            
        Returns:
            True if successful
        """
        if not self.running or not self.client:
            logger.error("❌ Bluetooth not initialized")
            return False
        
        try:
            logger.info("=" * 60)
            logger.info("🔵 ENTERING PAIRING MODE")
            logger.info(f"   Ready to pair with new device for {timeout_seconds}s")
            logger.info("=" * 60)
            
            self.pairing_mode = True
            
            # Make discoverable
            self.client.set_adapter_property('Discoverable', True)
            self.client.set_adapter_property('DiscoverableTimeout', timeout_seconds)
            
            # Schedule exit from pairing mode
            GLib.timeout_add(timeout_seconds * 1000, self.exit_pairing_mode)
            
            logger.info("👁️  Bluetooth is now DISCOVERABLE")
            logger.info("📱 Pair your device now!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error entering pairing mode: {e}")
            return False
    
    def exit_pairing_mode(self) -> bool:
        """Exit pairing mode and make non-discoverable"""
        if not self.pairing_mode:
            return False
        
        try:
            self.pairing_mode = False
            
            if self.client:
                self.client.set_adapter_property('Discoverable', False)
                logger.info("👁️  Pairing mode ended - no longer discoverable")
            
        except Exception as e:
            logger.error(f"Error exiting pairing mode: {e}")
        
        return False  # Don't reschedule
    
    def disconnect_current(self) -> bool:
        """Disconnect currently connected device"""
        if not self.current_device_path or not self.client:
            logger.info("ℹ️  No device currently connected")
            return False
        
        if self.client.disconnect_device(self.current_device_path):
            logger.info(f"🔌 Disconnected: {self.current_device_name}")
            return True
        
        return False
    
    def is_connected(self) -> bool:
        """Check if any device is connected"""
        return len(self.connected_devices) > 0
    
    def get_connected_device_name(self) -> Optional[str]:
        """Get name of currently connected device"""
        return self.current_device_name
    
    def list_paired_devices(self) -> list:
        """
        Get list of paired devices.
        
        Returns:
            List of dicts with 'name', 'mac', 'connected' keys
        """
        if not self.client:
            return []
        
        devices = []
        try:
            objects = self.client.get_managed_objects()
            
            for path, interfaces in objects.items():
                if 'org.bluez.Device1' in interfaces:
                    props = interfaces['org.bluez.Device1']
                    
                    if props.get('Paired', False):
                        devices.append({
                            'name': str(props.get('Name', 'Unknown')),
                            'mac': str(props.get('Address', '')),
                            'connected': props.get('Connected', False)
                        })
        except Exception as e:
            logger.error(f"Error listing paired devices: {e}")
        
        return devices
    
    def get_volume(self) -> Optional[int]:
        """
        Get current volume of Bluetooth audio sink (cached to avoid PulseAudio polling).
        Call refresh_volume() to update the cache.
        
        Returns:
            Cached volume level (0-100) or default 50 if no cache available
        """
        # Skip if no device connected
        if not self.connected_devices:
            return None
        
        # Return cached value if available
        if self._volume_cache_valid and self._cached_volume is not None:
            return self._cached_volume
        
        # No cache - return default and refresh in background
        logger.debug("No volume cache, using default 50")
        return 50
    
    def refresh_volume(self) -> Optional[int]:
        """
        Refresh the volume cache by querying PulseAudio.
        This should be called sparingly to avoid performance issues.
        
        Returns:
            Updated volume level (0-100) or None if unable to get volume
        """
        # Skip if no device connected
        if not self.connected_devices:
            self._volume_cache_valid = False
            return None
            
        try:
            # Use shorter timeout and only get sink info (faster)
            result = subprocess.run(
                ['pactl', 'list', 'sinks', 'short'],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            if result.returncode != 0:
                return self._cached_volume
            
            # Find bluez sink name
            sink_name = None
            for line in result.stdout.split('\n'):
                if 'bluez' in line.lower():
                    parts = line.split()
                    if parts:
                        sink_name = parts[0]
                        break
            
            if not sink_name:
                return self._cached_volume
            
            # Get volume for specific sink (much faster than listing all sinks)
            result = subprocess.run(
                ['pactl', 'get-sink-volume', sink_name],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            if result.returncode == 0:
                # Parse volume: "Volume: front-left: 65536 / 100% ..."
                match = re.search(r'(\d+)%', result.stdout)
                if match:
                    volume = int(match.group(1))
                    self._cached_volume = volume
                    self._volume_cache_valid = True
                    logger.debug(f"Refreshed Bluetooth volume cache: {volume}%")
                    return volume
            
            return self._cached_volume
            
        except subprocess.TimeoutExpired:
            logger.debug("Timeout refreshing Bluetooth volume")
            return self._cached_volume
        except Exception as e:
            logger.debug(f"Could not refresh Bluetooth volume: {e}")
            return self._cached_volume
    
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
                # Update cache
                self._cached_volume = volume
                self._volume_cache_valid = True
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
    
    def _unsuspend_bluetooth_sink(self):
        """
        Prevent PulseAudio from suspending the Bluetooth sink.
        This fixes the issue where audio stops after 1 second due to auto-suspend.
        """
        try:
            # Find Bluetooth sink
            result = subprocess.run(
                ['pactl', 'list', 'sinks', 'short'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'bluez' in line.lower():
                        # Extract sink name (first column)
                        parts = line.split()
                        if parts:
                            sink_name = parts[0]
                            
                            # Unsuspend the sink
                            subprocess.run(
                                ['pactl', 'suspend-sink', sink_name, '0'],
                                capture_output=True,
                                timeout=2
                            )
                            logger.info(f"🔊 Unsuspended Bluetooth sink: {sink_name}")
                            
                            # Set as default sink to ensure audio routes here
                            subprocess.run(
                                ['pactl', 'set-default-sink', sink_name],
                                capture_output=True,
                                timeout=2
                            )
                            logger.info(f"🎯 Set Bluetooth as default sink: {sink_name}")
                            break
        except Exception as e:
            logger.warning(f"Could not unsuspend Bluetooth sink: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up BluetoothController...")
        
        if self.client:
            self.client.unregister_agent()
        
        if self.mainloop:
            self.mainloop.quit()
            self.running = False
        
        logger.info("✅ BluetoothController cleaned up")
