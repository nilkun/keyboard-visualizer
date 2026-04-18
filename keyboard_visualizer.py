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
        self.needs_render = True  # Flag to track if re-render is needed
        
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
            "default_key_width": 5,
            "key_widths": {},
            "highlight_char": "█",
            "normal_char": "░",
            "border_char": "─",
            "highlight_color": "orange",
            "key_labels": {},
            "key_colors": {},
            "display_mode": "base",
            "key_alternatives": {}
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
                    'shift_l': 'ShiftL',  # Left Shift
                    'shift_r': 'ShiftR',  # Right Shift
                    'ctrl': 'Ctrl',
                    'ctrl_l': 'CtrlL',
                    'ctrl_r': 'CtrlR',
                    'alt': 'Alt',
                    'alt_l': 'Alt',
                    'alt_r': 'AltGr',  # Right Alt is AltGr on many keyboards
                    'alt_gr': 'AltGr',
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
            'purple': '\033[38;5;129m',
            'pink': '\033[38;5;213m',
            'lime': '\033[38;5;118m',
            'teal': '\033[38;5;37m',
            'gold': '\033[38;5;220m',
            'gray': '\033[90m',
            'light_gray': '\033[37m',
        }
        return colors.get(color_name.lower(), '\033[38;5;208m')  # Default to orange
    
    def parse_colored_text(self, text):
        """Parse text with color tags like 'W{red}A{blue}S{green}D' 
        Returns list of (char, color) tuples"""
        result = []
        i = 0
        current_color = None
        
        while i < len(text):
            if text[i] == '{' and i > 0:
                # Find closing brace
                end = text.find('}', i)
                if end != -1:
                    color = text[i+1:end]
                    current_color = color
                    i = end + 1
                    continue
            
            result.append((text[i], current_color))
            i += 1
        
        return result
    
    def render_colored_text(self, text, default_color=None):
        """Render text with embedded color codes"""
        parsed = self.parse_colored_text(text)
        result = []
        reset = '\033[0m'
        
        for char, color in parsed:
            if color:
                result.append(self.get_color_code(color) + char + reset)
            elif default_color:
                result.append(default_color + char + reset)
            else:
                result.append(char)
        
        return ''.join(result)
    
    def get_display_text_for_key(self, key, is_pressed, actual_char):
        """Get the display text for a key based on display mode and modifier state"""
        config = self.config
        display_mode = config.get('display_mode', 'base')
        key_alternatives = config.get('key_alternatives', {})
        key_labels = config.get('key_labels', {})
        
        # If custom label is defined, use it
        if key in key_labels:
            return key_labels[key]
        
        # Handle ShiftL/ShiftR display
        if key == 'ShiftL':
            return 'Shift' if not is_pressed else 'Shift'
        elif key == 'ShiftR':
            return 'Shift' if not is_pressed else 'Shift'
        elif key == 'CtrlL':
            return 'Ctrl' if not is_pressed else 'Ctrl'
        elif key == 'CtrlR':
            return 'Ctrl' if not is_pressed else 'Ctrl'
        
        # Check if this is a letter key (A-Z) and auto-generate alternatives
        if key in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz':
            key_upper = key.upper()
            if key_upper not in key_alternatives:
                # Auto-generate shift/base alternatives for letters
                key_alternatives[key_upper] = {
                    'base': key_upper.lower(),
                    'shift': key_upper
                }
        
        # If pressed, return actual character for base mode
        if is_pressed and display_mode == 'base':
            return actual_char
        
        # For non-pressed keys or other modes, check alternatives
        if key in key_alternatives:
            alternatives = key_alternatives[key]
            
            if display_mode == 'base':
                # Show base character, or alternative if modifier is pressed
                # Priority: Shift > AltGr > Alt > Ctrl
                if 'Shift' in self.modifier_keys and 'shift' in alternatives:
                    return alternatives['shift']
                elif 'AltGr' in self.modifier_keys and 'altgr' in alternatives:
                    return alternatives['altgr']
                elif 'Alt' in self.modifier_keys and 'alt' in alternatives:
                    return alternatives['alt']
                elif 'Ctrl' in self.modifier_keys and 'ctrl' in alternatives:
                    return alternatives['ctrl']
                else:
                    return alternatives.get('base', key)
            
            elif display_mode == 'all':
                # Show all alternatives with the active one highlighted
                parts = []
                base = alternatives.get('base', key)
                shift = alternatives.get('shift', '')
                alt = alternatives.get('alt', '')
                altgr = alternatives.get('altgr', '')
                ctrl = alternatives.get('ctrl', '')
                
                # Determine which is active
                active = None
                if is_pressed:
                    active = actual_char
                elif 'Shift' in self.modifier_keys and shift:
                    active = shift
                elif 'AltGr' in self.modifier_keys and altgr:
                    active = altgr
                elif 'Alt' in self.modifier_keys and alt:
                    active = alt
                elif 'Ctrl' in self.modifier_keys and ctrl:
                    active = ctrl
                else:
                    active = base
                
                # Build display string with highlighting
                # Order: Shift, Base, Alt, AltGr, Ctrl
                if shift:
                    if shift == active:
                        parts.append(f"{shift}{{{config.get('highlight_color', 'orange')}}}")
                    else:
                        parts.append(f"{shift}{{gray}}")
                
                if base == active:
                    parts.append(f"{base}{{{config.get('highlight_color', 'orange')}}}")
                else:
                    parts.append(base)
                
                if alt:
                    if alt == active:
                        parts.append(f"{alt}{{{config.get('highlight_color', 'orange')}}}")
                    else:
                        parts.append(f"{alt}{{gray}}")
                
                if altgr:
                    if altgr == active:
                        parts.append(f"{altgr}{{{config.get('highlight_color', 'orange')}}}")
                    else:
                        parts.append(f"{altgr}{{gray}}")
                
                if ctrl:
                    if ctrl == active:
                        parts.append(f"{ctrl}{{{config.get('highlight_color', 'orange')}}}")
                    else:
                        parts.append(f"{ctrl}{{gray}}")
                
                return ''.join(parts)
            
            elif display_mode == 'alternative':
                # Only show alternative when modifier is pressed
                if 'Shift' in self.modifier_keys and 'shift' in alternatives:
                    return alternatives['shift']
                elif 'AltGr' in self.modifier_keys and 'altgr' in alternatives:
                    return alternatives['altgr']
                elif 'Alt' in self.modifier_keys and 'alt' in alternatives:
                    return alternatives['alt']
                elif 'Ctrl' in self.modifier_keys and 'ctrl' in alternatives:
                    return alternatives['ctrl']
                else:
                    return alternatives.get('base', key)
        
        # Default: return actual char if pressed, otherwise key name
        return actual_char if is_pressed else key
    
    def render_keyboard(self):
        """Render the keyboard layout with highlighted pressed keys"""
        config = self.config
        layout = config['layout']
        # Support both old 'key_width' and new 'default_key_width'
        default_width = config.get('default_key_width', config.get('key_width', 5))
        key_widths = config.get('key_widths', {})
        highlight = config['highlight_char']
        normal = config['normal_char']
        border = config['border_char']
        default_highlight_color = self.get_color_code(config.get('highlight_color', 'orange'))
        key_labels = config.get('key_labels', {})
        key_colors = config.get('key_colors', {})
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
                
                # Get display text based on mode and modifier state
                display_text = self.get_display_text_for_key(key, is_pressed, actual_char)
                
                # Get custom color for this key (or use default)
                if is_pressed:
                    key_color = self.get_color_code(key_colors.get(key, config.get('highlight_color', 'orange')))
                else:
                    key_color = ""
                
                key_reset = reset if is_pressed else ""
                
                # Get key width - custom width or default
                key_display_width = key_widths.get(key, default_width)
                
                # Calculate visual length (excluding color codes)
                visual_text = display_text
                # Remove color codes from length calculation
                import re
                visual_length = len(re.sub(r'\{[^}]+\}', '', visual_text))
                
                # Create key representation
                padding = key_display_width - visual_length
                left_pad = padding // 2
                right_pad = padding - left_pad
                
                line_top += key_color + "┌" + (char * key_display_width) + "┐" + key_reset
                
                # Render colored text if it has color tags
                if '{' in display_text and '}' in display_text:
                    rendered_text = self.render_colored_text(display_text, key_color if is_pressed else None)
                    line_mid += key_color + "│" + reset + (" " * left_pad) + rendered_text + (" " * right_pad) + key_color + "│" + key_reset
                else:
                    line_mid += key_color + "│" + (" " * left_pad) + display_text + (" " * right_pad) + "│" + key_reset
                
                line_bot += key_color + "└" + (char * key_display_width) + "┘" + key_reset
            
            output.append(line_top + "\n")
            output.append(line_mid + "\n")
            output.append(line_bot + "\n")
        
        output.append(border * 80 + "\n")
        
        # Show actual output characters
        output.append("Output: ")
        
        # Collect non-modifier keys that would produce output
        output_chars = []
        for k, v in sorted(pressed.items()):
            # Skip modifier keys and special keys
            if k not in ['Shift', 'ShiftL', 'ShiftR', 'Ctrl', 'CtrlL', 'CtrlR', 
                         'Alt', 'AltGr', 'Win', 'Caps', 'Tab', 'Enter', 
                         'Backspace', 'Esc', 'Fn']:
                output_chars.append(v)
        
        if output_chars:
            output.append(f"'{' '.join(output_chars)}'\n")
        else:
            output.append("(none)\n")
        
        # Show pressed keys with their output
        if pressed:
            outputs = [f"{k}='{v}'" for k, v in sorted(pressed.items())]
            output.append(f"Pressed: {', '.join(outputs)}\n")
        else:
            output.append("Pressed: None\n")
        
        # Show active modifiers
        with self.lock:
            mods = self.modifier_keys.copy()
        if mods:
            output.append(f"Modifiers: {', '.join(sorted(mods))}\n")
        
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
        
        # Track modifier keys (including left/right variants)
        if normalized in ['Shift', 'ShiftL', 'ShiftR', 'Ctrl', 'CtrlL', 'CtrlR', 'Alt', 'AltGr', 'Win']:
            with self.lock:
                self.modifier_keys.add(normalized)
                # Also add generic modifier for compatibility
                if normalized in ['ShiftL', 'ShiftR']:
                    self.modifier_keys.add('Shift')
                elif normalized in ['CtrlL', 'CtrlR']:
                    self.modifier_keys.add('Ctrl')
                self.needs_render = True
        
        with self.lock:
            self.pressed_keys[normalized] = actual_output
            self.needs_render = True
    
    def on_release(self, key):
        """Handle key release event"""
        normalized, _ = self.normalize_key(key)
        
        # Remove modifier keys (including left/right variants)
        if normalized in ['Shift', 'ShiftL', 'ShiftR', 'Ctrl', 'CtrlL', 'CtrlR', 'Alt', 'AltGr', 'Win']:
            with self.lock:
                self.modifier_keys.discard(normalized)
                # Also remove generic modifier
                if normalized in ['ShiftL', 'ShiftR']:
                    # Only remove 'Shift' if both left and right are released
                    if 'ShiftL' not in self.modifier_keys and 'ShiftR' not in self.modifier_keys:
                        self.modifier_keys.discard('Shift')
                elif normalized in ['CtrlL', 'CtrlR']:
                    if 'CtrlL' not in self.modifier_keys and 'CtrlR' not in self.modifier_keys:
                        self.modifier_keys.discard('Ctrl')
                self.needs_render = True
        
        with self.lock:
            self.pressed_keys.pop(normalized, None)
            self.needs_render = True
    
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
            ecodes.KEY_RIGHTALT: ('AltGr', 'AltGr'),  # Right Alt is AltGr
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
                        if normalized in ['Shift', 'ShiftL', 'ShiftR', 'Ctrl', 'CtrlL', 'CtrlR', 'Alt', 'AltGr', 'Win']:
                            with self.lock:
                                self.modifier_keys.add(normalized)
                                # Also add generic modifier for compatibility
                                if normalized in ['ShiftL', 'ShiftR']:
                                    self.modifier_keys.add('Shift')
                                elif normalized in ['CtrlL', 'CtrlR']:
                                    self.modifier_keys.add('Ctrl')
                                self.needs_render = True
                        
                        with self.lock:
                            self.pressed_keys[normalized] = actual_output
                            self.needs_render = True
                    
                    elif event.value == 0:  # Key up
                        # Remove modifier keys
                        if normalized in ['Shift', 'ShiftL', 'ShiftR', 'Ctrl', 'CtrlL', 'CtrlR', 'Alt', 'AltGr', 'Win']:
                            with self.lock:
                                self.modifier_keys.discard(normalized)
                                # Also remove generic modifier
                                if normalized in ['ShiftL', 'ShiftR']:
                                    # Only remove 'Shift' if both left and right are released
                                    if 'ShiftL' not in self.modifier_keys and 'ShiftR' not in self.modifier_keys:
                                        self.modifier_keys.discard('Shift')
                                elif normalized in ['CtrlL', 'CtrlR']:
                                    if 'CtrlL' not in self.modifier_keys and 'CtrlR' not in self.modifier_keys:
                                        self.modifier_keys.discard('Ctrl')
                                self.needs_render = True
                        
                        with self.lock:
                            self.pressed_keys.pop(normalized, None)
                            self.needs_render = True
        
        finally:
            if self.keyboard_device:
                self.keyboard_device.ungrab()
                print("\nReleased keyboard device")
    
    def render_loop(self):
        """Continuous rendering loop"""
        # Initial render
        self.render_keyboard()
        
        while self.running:
            # Only render if something changed
            with self.lock:
                if self.needs_render:
                    self.needs_render = False
                    should_render = True
                else:
                    should_render = False
            
            if should_render:
                self.render_keyboard()
            
            time.sleep(0.016)  # ~60 FPS check rate, but only renders on change
    
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
