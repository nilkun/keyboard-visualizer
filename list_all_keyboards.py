#!/usr/bin/env python3
import evdev
from evdev import InputDevice, ecodes

devices = [InputDevice(path) for path in evdev.list_devices()]
print("All input devices with keyboard capabilities:\n")

for device in devices:
    caps = device.capabilities()
    if ecodes.EV_KEY in caps:
        keys = caps[ecodes.EV_KEY]
        has_letters = ecodes.KEY_Q in keys and ecodes.KEY_A in keys
        print(f"{'[KEYBOARD]' if has_letters else '[HAS KEYS]'} {device.name}")
        print(f"  Path: {device.path}")
        print(f"  Has Q and A keys: {has_letters}")
        print()
