#!/usr/bin/env python3
"""
DBus Event Listener Test

This script registers to DBus and listens for all PropertiesChanged events on org.bluez.MediaPlayer1.
It prints any events received to the console for debugging DBus event delivery.
"""

import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dbus_test_listener")

def on_properties_changed(interface, changed, invalidated):
    print(f"[DBUS EVENT] PropertiesChanged on {interface}")
    print(f"  Changed: {dict(changed)}")
    print(f"  Invalidated: {list(invalidated)}")

if __name__ == "__main__":
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()


    # Listen for PropertiesChanged on any MediaPlayer1 object
    bus.add_signal_receiver(
        on_properties_changed,
        signal_name='PropertiesChanged',
        dbus_interface='org.freedesktop.DBus.Properties',
        path=None,  # Listen globally
        arg0='org.bluez.MediaPlayer1',
    )

    # Listen specifically for volume changes on MediaPlayer1
    def on_volume_changed(interface, changed, invalidated):
        if 'Volume' in changed:
            print(f"[DBUS EVENT] Volume changed on {interface}: {changed['Volume']}")

    bus.add_signal_receiver(
        on_volume_changed,
        signal_name='PropertiesChanged',
        dbus_interface='org.freedesktop.DBus.Properties',
        path=None,
        arg0='org.bluez.MediaTransport1',
    )

    print("Listening for DBus PropertiesChanged events on org.bluez.MediaPlayer1...")
    print("Press Ctrl+C to exit.")
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("Stopped.")
        loop.quit()
