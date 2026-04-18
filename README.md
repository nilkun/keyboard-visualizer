# Keyboard Visualizer

A CLI tool that displays all keyboard presses visualized as a real keyboard in your terminal.

## Features

- Real-time visualization of keyboard presses
- Shows actual output characters (e.g., 'a' vs 'A' with Shift)
- Customizable keyboard layout via JSON configuration
- Color-coded pressed keys (default: orange)
- Blocks all keyboard input except 'q' to quit
- Support for special keys (Shift, Ctrl, Alt, etc.)
- Configurable appearance (colors, width, characters)

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Make the script executable (optional):
```bash
chmod +x keyboard_visualizer.py
```

## Usage

Run with default configuration:
```bash
python3 keyboard_visualizer.py
```

Run with custom configuration:
```bash
python3 keyboard_visualizer.py my_custom_config.json
```

**True Input Blocking (Linux only):**

For complete keyboard input blocking (prevents keys from reaching other applications), run with sudo and the `--evdev` flag:

```bash
sudo python3 keyboard_visualizer.py --evdev
```

This requires the `evdev` library and root permissions to grab the keyboard device.

Press **q** to quit the visualizer.

## Configuration

Edit `keyboard_config.json` to customize your keyboard layout. Here's what you can configure:

### Layout
The `layout` array defines the keyboard structure. Each sub-array represents a row of keys:
```json
"layout": [
  ["Esc", "F1", "F2", "F3", ...],
  ["`", "1", "2", "3", ...],
  ...
]
```

### Appearance Options

- **key_width**: Base width of each key (default: 5)
- **highlight_char**: Character used to fill pressed keys (default: "█")
- **normal_char**: Character used to fill unpressed keys (default: "░")
- **border_char**: Character used for borders (default: "─")
- **highlight_color**: Color for pressed keys (default: "orange")
  - Available colors: orange, red, green, yellow, blue, magenta, cyan, white, bright_red, bright_green, bright_yellow, bright_blue, bright_magenta, bright_cyan

### Example Custom Configuration

Create a minimal layout with custom colors:
```json
{
  "layout": [
    ["Q", "W", "E", "R", "T", "Y"],
    ["A", "S", "D", "F", "G", "H"],
    ["Z", "X", "C", "V", "B", "N"]
  ],
  "key_width": 4,
  "highlight_char": "▓",
  "normal_char": "░",
  "border_char": "═",
  "highlight_color": "bright_cyan"
}
```

## Keyboard Layouts

You can create different layouts for different keyboard types:

- **QWERTY** (default)
- **DVORAK** - Rearrange keys in the layout array
- **Gaming** - Create a focused layout with WASD, number keys, etc.
- **60% keyboard** - Remove function keys and numpad
- **Custom** - Any layout you want!

## Requirements

- Python 3.6+
- pynput library
- Terminal with Unicode support
- evdev library (Linux only, optional - for true input blocking)

## Troubleshooting

**Permissions Error**: On Linux with `--evdev` flag, you need to run with sudo to grab keyboard devices.

**Keys not displaying**: Make sure the key names in your config match the normalized key names used by the program (check the key mapping in the code).

**Input not being blocked**: By default (without `--evdev`), the visualizer uses pynput which doesn't block input on all systems. Use `sudo python3 keyboard_visualizer.py --evdev` on Linux for true input blocking.

**Multiple keyboards**: If you have multiple keyboard devices, the tool will auto-select the first one it finds with standard keyboard keys.

## License

MIT License - Feel free to modify and distribute!
