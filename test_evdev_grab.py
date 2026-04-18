#!/usr/bin/env python3
import evdev
from evdev import InputDevice, ecodes, categorize
import time

# Find keyboard
devices = [InputDevice(path) for path in evdev.list_devices()]
keyboard = None
for device in devices:
    caps = device.capabilities()
    if ecodes.EV_KEY in caps:
        keys = caps[ecodes.EV_KEY]
        if ecodes.KEY_Q in keys and ecodes.KEY_A in keys:
            keyboard = device
            break

if not keyboard:
    print("No keyboard found!")
    exit(1)

print(f"Found: {keyboard.name} ({keyboard.path})")
print("Attempting to grab...")

try:
    keyboard.grab()
    print("SUCCESS! Keyboard is grabbed. Press keys (they should NOT appear). Press Ctrl+C to exit.")
    
    for event in keyboard.read_loop():
        if event.type == ecodes.EV_KEY:
            key_event = categorize(event)
            if event.value == 1:  # Key down
                print(f"Key pressed: {key_event.keycode}")
                
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    keyboard.ungrab()
    print("Released keyboard")
