#!/usr/bin/env python3
import evdev
from evdev import InputDevice, ecodes

devices = [InputDevice(path) for path in evdev.list_devices()]
print("Available input devices:")
for device in devices:
    caps = device.capabilities()
    if ecodes.EV_KEY in caps:
        keys = caps[ecodes.EV_KEY]
        if ecodes.KEY_Q in keys and ecodes.KEY_A in keys:
            print(f"  ✓ {device.name} ({device.path}) - KEYBOARD")
        else:
            print(f"    {device.name} ({device.path}) - has keys but not keyboard")
    else:
        print(f"    {device.name} ({device.path}) - no keyboard")
