#!/usr/bin/env python3
"""
Keyboard Visualizer - Display keyboard presses in real-time
"""
import sys
import json
import os
from pynput import keyboard
import threading
import time
try:
    from pynput.keyboard import Controller, Key
except ImportError:
    Controller = None

# Try to import evdev for true input blocking (requires sudo)
try:
    import evdev
    from evdev import InputDevice, categorize, ecodes
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False

class KeyboardVisualizer:
    def __init__(self, config_path='keyboard_config.json', use_evdev=False):
        self.config = self.load_config(config_path)
        self.pressed_keys = {}  # Now stores key -> actual output character
        self.modifier_keys = set()  # Track shift, ctrl, etc
        self.lock = threading.Lock()
        self.running = True
        self.use_evdev = use_evdev and EVDEV_AVAILABLE
        self.keyboard_device = None
        
    def load_config(self, path):
        """Load keyboard layout configuration from JSON file"""
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        else:
            return self.get_default_config()
    
    def get_default_config(self):
        """Return default QWERTY keyboard layout"""
        return {
            "layout": [
                ["Esc", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"],
                ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "Backspace"],
                ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\"],
                ["Caps", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "Enter"],
                ["Shift", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "Shift"],
                ["Ctrl", "Win", "Alt", "Space", "Alt", "Fn", "Ctrl"]
            ],
            "key_width": 5,
            "highlight_char": "█",
            "normal_char": "░",
            "border_char": "─",
            "highlight_color": "orange"
        }
    
    def normalize_key(self, key):
        """Normalize key representation - returns (normalized_name, actual_output)"""
        try:
            # Handle special keys
            if hasattr(key, 'char') and key.char is not None:
                char = key.char
                normalized = char.upper()
                return (normalized, char)
            elif hasattr(key, 'name'):
                key_map = {
                    'space': 'Space',
                    'enter': 'Enter',
                    'tab': 'Tab',
                    'backspace': 'Backspace',
                    'esc': 'Esc',
                    'shift': 'Shift',
                    'shift_l': 'Shift',
                    'shift_r': 'Shift',
                    'ctrl': 'Ctrl',
                    'ctrl_l': 'Ctrl',
                    'ctrl_r': 'Ctrl',
                    'alt': 'Alt',
                    'alt_l': 'Alt',
                    'alt_r': 'Alt',
                    'caps_lock': 'Caps',
                    'cmd': 'Win',
                    'cmd_l': 'Win',
                    'cmd_r': 'Win'
                }
                name = key.name.lower()
                if name in key_map:
                    return (key_map[name], key_map[name])
                if name.startswith('f') and name[1:].isdigit():
                    return (name.upper(), name.upper())
                return (name.capitalize(), name.capitalize())
        except:
            pass
        normalized = str(key).replace('Key.', '').capitalize()
        return (normalized, normalized)
    
    def get_color_code(self, color_name):
        """Convert color name to ANSI color code"""
        colors = {
            'orange': '\033[38;5;208m',
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'bright_red': '\033[38;5;196m',
            'bright_green': '\033[38;5;46m',
            'bright_yellow': '\033[38;5;226m',
            'bright_blue': '\033[38;5;21m',
            'bright_magenta': '\033[38;5;201m',
            'bright_cyan': '\033[38;5;51m',
        }
        return colors.get(color_name.lower(), '\033[38;5;208m')  # Default to orange
    
    def render_keyboard(self):
        """Render the keyboard layout with highlighted pressed keys"""
        config = self.config
        layout = config['layout']
        width = config['key_width']
        highlight = config['highlight_char']
        normal = config['normal_char']
        border = config['border_char']
        color = self.get_color_code(config.get('highlight_color', 'orange'))
        reset = '\033[0m'
        
        output = []
        output.append("\033[2J\033[H")  # Clear screen and move cursor to top
        output.append("Keyboard Visualizer - Press 'q' to quit\n")
        output.append(border * 80 + "\n")
        
        with self.lock:
            pressed = self.pressed_keys.copy()
        
        for row in layout:
            line_top = ""
            line_mid = ""
            line_bot = ""
            
            for key in row:
                is_pressed = key in pressed
                actual_char = pressed.get(key, key) if is_pressed else key
                char = highlight if is_pressed else normal
                
                # Apply color to pressed keys
                key_color = color if is_pressed else ""
                key_reset = reset if is_pressed else ""
                
                # Adjust key width based on key name
                key_display_width = width
                if key in ["Backspace", "Enter", "Shift", "Space"]:
                    key_display_width = width + 2
                elif key == "Tab" or key == "Caps":
                    key_display_width = width + 1
                
                # Display actual output character for pressed keys
                display_text = actual_char if is_pressed else key
                
                # Create key representation
                padding = key_display_width - len(display_text)
                left_pad = padding // 2
                right_pad = padding - left_pad
                
                line_top += key_color + "┌" + (char * key_display_width) + "┐" + key_reset
                line_mid += key_color + "│" + (" " * left_pad) + display_text + (" " * right_pad) + "│" + key_reset
                line_bot += key_color + "└" + (char * key_display_width) + "┘" + key_reset
            
            output.append(line_top + "\n")
            output.append(line_mid + "\n")
            output.append(line_bot + "\n")
        
        output.append(border * 80 + "\n")
        
        # Show actual output characters
        if pressed:
            outputs = [f"{k}='{v}'" for k, v in sorted(pressed.items())]
            output.append(f"Pressed keys: {', '.join(outputs)}\n")
        else:
            output.append("Pressed keys: None\n")
        
        sys.stdout.write(''.join(output))
        sys.stdout.flush()
    
    def on_press(self, key):
        """Handle key press event"""
        # Check for 'q' key to quit
        try:
            if hasattr(key, 'char') and key.char == 'q':
                self.running = False
                return False  # Stop listener only when quitting
        except:
            pass
        
        normalized, actual_output = self.normalize_key(key)
        
        # Track modifier keys
        if normalized in ['Shift', 'Ctrl', 'Alt', 'Win']:
            with self.lock:
                self.modifier_keys.add(normalized)
        
        with self.lock:
            self.pressed_keys[normalized] = actual_output
    
    def on_release(self, key):
        """Handle key release event"""
        normalized, _ = self.normalize_key(key)
        
        # Remove modifier keys
        if normalized in ['Shift', 'Ctrl', 'Alt', 'Win']:
            with self.lock:
                self.modifier_keys.discard(normalized)
        
        with self.lock:
            self.pressed_keys.pop(normalized, None)
    
    def find_keyboard_device(self):
        """Find keyboard input device for evdev"""
        if not EVDEV_AVAILABLE:
            return None
        
        devices = [InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            # Look for a device with keyboard capabilities
            capabilities = device.capabilities()
            if ecodes.EV_KEY in capabilities:
                # Check if it has typical keyboard keys
                keys = capabilities[ecodes.EV_KEY]
                if ecodes.KEY_Q in keys and ecodes.KEY_A in keys:
                    print(f"Using keyboard device: {device.name} ({device.path})")
                    return device
        return None
    
    def normalize_evdev_key(self, event):
        """Normalize evdev key event - returns (normalized_name, actual_output)"""
        keycode = event.code
        
        # Map evdev keycodes to our key names
        evdev_map = {
            ecodes.KEY_ESC: ('Esc', 'Esc'),
            ecodes.KEY_1: ('1', '!') if 'Shift' in self.modifier_keys else ('1', '1'),
            ecodes.KEY_2: ('2', '@') if 'Shift' in self.modifier_keys else ('2', '2'),
            ecodes.KEY_3: ('3', '#') if 'Shift' in self.modifier_keys else ('3', '3'),
            ecodes.KEY_4: ('4', '$') if 'Shift' in self.modifier_keys else ('4', '4'),
            ecodes.KEY_5: ('5', '%') if 'Shift' in self.modifier_keys else ('5', '5'),
            ecodes.KEY_6: ('6', '^') if 'Shift' in self.modifier_keys else ('6', '6'),
            ecodes.KEY_7: ('7', '&') if 'Shift' in self.modifier_keys else ('7', '7'),
            ecodes.KEY_8: ('8', '*') if 'Shift' in self.modifier_keys else ('8', '8'),
            ecodes.KEY_9: ('9', '(') if 'Shift' in self.modifier_keys else ('9', '9'),
            ecodes.KEY_0: ('0', ')') if 'Shift' in self.modifier_keys else ('0', '0'),
            ecodes.KEY_MINUS: ('-', '_') if 'Shift' in self.modifier_keys else ('-', '-'),
            ecodes.KEY_EQUAL: ('=', '+') if 'Shift' in self.modifier_keys else ('=', '='),
            ecodes.KEY_BACKSPACE: ('Backspace', 'Backspace'),
            ecodes.KEY_TAB: ('Tab', 'Tab'),
            ecodes.KEY_ENTER: ('Enter', 'Enter'),
            ecodes.KEY_LEFTCTRL: ('Ctrl', 'Ctrl'),
            ecodes.KEY_RIGHTCTRL: ('Ctrl', 'Ctrl'),
            ecodes.KEY_LEFTSHIFT: ('Shift', 'Shift'),
            ecodes.KEY_RIGHTSHIFT: ('Shift', 'Shift'),
            ecodes.KEY_LEFTALT: ('Alt', 'Alt'),
            ecodes.KEY_RIGHTALT: ('Alt', 'Alt'),
            ecodes.KEY_LEFTMETA: ('Win', 'Win'),
            ecodes.KEY_RIGHTMETA: ('Win', 'Win'),
            ecodes.KEY_SPACE: ('Space', ' '),
            ecodes.KEY_CAPSLOCK: ('Caps', 'Caps'),
            ecodes.KEY_GRAVE: ('`', '~') if 'Shift' in self.modifier_keys else ('`', '`'),
            ecodes.KEY_LEFTBRACE: ('[', '{') if 'Shift' in self.modifier_keys else ('[', '['),
            ecodes.KEY_RIGHTBRACE: (']', '}') if 'Shift' in self.modifier_keys else (']', ']'),
            ecodes.KEY_BACKSLASH: ('\\', '|') if 'Shift' in self.modifier_keys else ('\\', '\\'),
            ecodes.KEY_SEMICOLON: (';', ':') if 'Shift' in self.modifier_keys else (';', ';'),
            ecodes.KEY_APOSTROPHE: ("'", '"') if 'Shift' in self.modifier_keys else ("'", "'"),
            ecodes.KEY_COMMA: (',', '<') if 'Shift' in self.modifier_keys else (',', ','),
            ecodes.KEY_DOT: ('.', '>') if 'Shift' in self.modifier_keys else ('.', '.'),
            ecodes.KEY_SLASH: ('/', '?') if 'Shift' in self.modifier_keys else ('/', '/'),
        }
        
        # Add F-keys
        for i in range(1, 13):
            fkey = getattr(ecodes, f'KEY_F{i}')
            evdev_map[fkey] = (f'F{i}', f'F{i}')
        
        # Add letter keys
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            key_code = getattr(ecodes, f'KEY_{letter}')
            if 'Shift' in self.modifier_keys:
                evdev_map[key_code] = (letter, letter)
            else:
                evdev_map[key_code] = (letter, letter.lower())
        
        return evdev_map.get(keycode, (f'Key{keycode}', f'Key{keycode}'))
    
    def evdev_loop(self):
        """Event loop for evdev input grabbing"""
        self.keyboard_device = self.find_keyboard_device()
        if not self.keyboard_device:
            print("Error: No keyboard device found!")
            self.running = False
            return
        
        # Grab the device to block input
        try:
            self.keyboard_device.grab()
            print(f"Grabbed keyboard device - input is now blocked (except 'q' to quit)")
        except Exception as e:
            print(f"Error grabbing device (are you running with sudo?): {e}")
            self.running = False
            return
        
        try:
            for event in self.keyboard_device.read_loop():
                if not self.running:
                    break
                
                if event.type == ecodes.EV_KEY:
                    key_event = categorize(event)
                    
                    # Check for 'q' to quit
                    if event.code == ecodes.KEY_Q and event.value == 1:  # Key down
                        self.running = False
                        break
                    
                    normalized, actual_output = self.normalize_evdev_key(event)
                    
                    if event.value == 1:  # Key down
                        # Track modifier keys
                        if normalized in ['Shift', 'Ctrl', 'Alt', 'Win']:
                            with self.lock:
                                self.modifier_keys.add(normalized)
                        
                        with self.lock:
                            self.pressed_keys[normalized] = actual_output
                    
                    elif event.value == 0:  # Key up
                        # Remove modifier keys
                        if normalized in ['Shift', 'Ctrl', 'Alt', 'Win']:
                            with self.lock:
                                self.modifier_keys.discard(normalized)
                        
                        with self.lock:
                            self.pressed_keys.pop(normalized, None)
        
        finally:
            if self.keyboard_device:
                self.keyboard_device.ungrab()
                print("\nReleased keyboard device")
    
    def render_loop(self):
        """Continuous rendering loop"""
        while self.running:
            self.render_keyboard()
            time.sleep(0.05)  # 20 FPS
    
    def run(self):
        """Start the keyboard visualizer"""
        # Start render thread
        render_thread = threading.Thread(target=self.render_loop, daemon=True)
        render_thread.start()
        
        if self.use_evdev:
            # Use evdev for true input blocking
            print("Running with evdev (true input blocking enabled)")
            self.evdev_loop()
        else:
            # Use pynput (no true blocking)
            if EVDEV_AVAILABLE and os.geteuid() == 0:
                print("Running as root but evdev not enabled. Use --evdev flag for true blocking.")
            elif EVDEV_AVAILABLE:
                print("Running with pynput (no input blocking). Run with sudo and --evdev for true blocking.")
            else:
                print("Running with pynput (evdev not available). Install python-evdev for true blocking.")
            
            # Start keyboard listener
            with keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release) as listener:
                listener.join()
        
        print("\nExiting...")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Keyboard Visualizer - Display keyboard presses in real-time')
    parser.add_argument('config', nargs='?', default='keyboard_config.json',
                        help='Path to keyboard configuration JSON file (default: keyboard_config.json)')
    parser.add_argument('--evdev', action='store_true',
                        help='Use evdev for true input blocking (requires sudo on Linux)')
    
    args = parser.parse_args()
    
    # Check if running as root when evdev is requested
    if args.evdev and not EVDEV_AVAILABLE:
        print("Error: evdev is not available. Install with: pip install evdev")
        sys.exit(1)
    
    if args.evdev and os.geteuid() != 0:
        print("Warning: --evdev requires root permissions. Please run with sudo.")
        print("Falling back to pynput mode...")
        args.evdev = False
    
    visualizer = KeyboardVisualizer(args.config, use_evdev=args.evdev)
    visualizer.run()

if __name__ == '__main__':
    main()
