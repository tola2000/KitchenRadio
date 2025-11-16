#!/usr/bin/env python3
"""
Example: Using AVRCP Client with BluetoothController

This example shows how to integrate AVRCP media control with
the existing BluetoothController to display track information
from connected devices.
"""

import logging
import time
from kitchenradio.bluetooth import BluetoothController, AVRCPClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class BluetoothWithAVRCP:
    """
    Example integration of BluetoothController with AVRCP client.
    
    This shows how to:
    1. Connect a Bluetooth device
    2. Monitor for track changes
    3. Display what's playing
    4. Control playback
    """
    
    def __init__(self):
        """Initialize Bluetooth with AVRCP"""
        self.bt_controller = BluetoothController()
        self.avrcp_client: AVRCPClient = None
        
        # Set up callbacks
        self.bt_controller.on_device_connected = self._on_device_connected
        self.bt_controller.on_device_disconnected = self._on_device_disconnected
        
        logger.info("Bluetooth with AVRCP initialized")
    
    def _on_device_connected(self, name: str, mac: str):
        """Handle device connection"""
        logger.info(f"🟢 Device connected: {name} ({mac})")
        
        # Convert MAC to D-Bus path
        mac_path = mac.replace(':', '_')
        device_path = f'/org/bluez/hci0/dev_{mac_path}'
        
        # Create AVRCP client for this device
        self.avrcp_client = AVRCPClient(device_path)
        
        # Set up AVRCP callbacks
        self.avrcp_client.on_track_changed = self._on_track_changed
        self.avrcp_client.on_status_changed = self._on_status_changed
        
        # Wait a moment for media player to be available
        time.sleep(2)
        
        # Get initial track info
        if self.avrcp_client.is_available():
            logger.info("✅ AVRCP media player available")
            self._display_current_track()
        else:
            logger.warning("⚠️  AVRCP not available - start playing music to enable")
    
    def _on_device_disconnected(self, name: str, mac: str):
        """Handle device disconnection"""
        logger.info(f"🔴 Device disconnected: {name} ({mac})")
        
        if self.avrcp_client:
            self.avrcp_client.clear_cache()
            self.avrcp_client = None
    
    def _on_track_changed(self, track: dict):
        """Handle track change from AVRCP"""
        logger.info("=" * 60)
        logger.info("🎵 NOW PLAYING:")
        logger.info(f"   Title:  {track.get('title', 'Unknown')}")
        logger.info(f"   Artist: {track.get('artist', 'Unknown')}")
        logger.info(f"   Album:  {track.get('album', 'Unknown')}")
        
        if 'duration' in track:
            duration_sec = track['duration'] / 1000
            minutes = int(duration_sec // 60)
            seconds = int(duration_sec % 60)
            logger.info(f"   Duration: {minutes}:{seconds:02d}")
        
        logger.info("=" * 60)
    
    def _on_status_changed(self, status: str):
        """Handle playback status change"""
        icon = {
            'playing': '▶️',
            'paused': '⏸️',
            'stopped': '⏹️'
        }.get(status, '❓')
        
        logger.info(f"{icon} Playback Status: {status.upper()}")
    
    def _display_current_track(self):
        """Display currently playing track"""
        if not self.avrcp_client:
            logger.warning("No AVRCP client available")
            return
        
        track = self.avrcp_client.get_track_info()
        status = self.avrcp_client.get_status()
        
        if track:
            logger.info("\nCurrent Track:")
            logger.info(f"  Title:  {track.get('title', 'Unknown')}")
            logger.info(f"  Artist: {track.get('artist', 'Unknown')}")
            logger.info(f"  Album:  {track.get('album', 'Unknown')}")
        
        if status:
            logger.info(f"  Status: {status}")
    
    def get_current_track_for_display(self) -> dict:
        """
        Get current track info formatted for display.
        
        This is what you'd call from KitchenRadio to update the display.
        
        Returns:
            Dictionary with title, artist, album, playing status
        """
        if not self.avrcp_client or not self.avrcp_client.is_available():
            return {
                'title': 'No track info',
                'artist': 'Bluetooth Audio',
                'album': '',
                'playing': False
            }
        
        track = self.avrcp_client.get_track_info()
        status = self.avrcp_client.get_status()
        
        return {
            'title': track.get('title', 'Unknown') if track else 'Unknown',
            'artist': track.get('artist', 'Unknown') if track else 'Unknown',
            'album': track.get('album', '') if track else '',
            'playing': status == 'playing' if status else False,
            'duration': track.get('duration', 0) if track else 0
        }
    
    def enter_pairing_mode(self, timeout_seconds: int = 60):
        """Enter pairing mode to pair new device"""
        logger.info(f"📱 Entering pairing mode for {timeout_seconds}s")
        self.bt_controller.enter_pairing_mode(timeout_seconds)
    
    def play(self):
        """Send play command via AVRCP"""
        if self.avrcp_client:
            self.avrcp_client.play()
    
    def pause(self):
        """Send pause command via AVRCP"""
        if self.avrcp_client:
            self.avrcp_client.pause()
    
    def next_track(self):
        """Skip to next track via AVRCP"""
        if self.avrcp_client:
            self.avrcp_client.next()
    
    def previous_track(self):
        """Skip to previous track via AVRCP"""
        if self.avrcp_client:
            self.avrcp_client.previous()


def main():
    """Example usage"""
    print("=" * 70)
    print("Bluetooth with AVRCP Example")
    print("=" * 70)
    print("\nThis example will:")
    print("1. Start Bluetooth controller")
    print("2. Monitor for device connections")
    print("3. Display track info from connected devices")
    print("4. Allow playback control\n")
    
    # Create integrated controller
    bt = BluetoothWithAVRCP()
    
    # Initialize
    if not bt.bt_controller.initialize():
        print("❌ Failed to initialize Bluetooth")
        return
    
    print("✅ Bluetooth initialized")
    print("\nOptions:")
    print("  p - Enter pairing mode")
    print("  d - Display current track")
    print("  play - Send play command")
    print("  pause - Send pause command")
    print("  next - Next track")
    print("  prev - Previous track")
    print("  q - Quit\n")
    
    # Command loop
    try:
        while True:
            cmd = input("> ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 'p':
                bt.enter_pairing_mode(60)
            elif cmd == 'd':
                track = bt.get_current_track_for_display()
                print(f"\nCurrent Track:")
                print(f"  {track['title']}")
                print(f"  by {track['artist']}")
                print(f"  Status: {'Playing' if track['playing'] else 'Not playing'}\n")
            elif cmd == 'play':
                bt.play()
            elif cmd == 'pause':
                bt.pause()
            elif cmd == 'next':
                bt.next_track()
            elif cmd == 'prev':
                bt.previous_track()
            else:
                print("Unknown command")
    
    except KeyboardInterrupt:
        print("\nExiting...")
    
    finally:
        bt.bt_controller.cleanup()
        print("✅ Cleaned up")


if __name__ == "__main__":
    main()
