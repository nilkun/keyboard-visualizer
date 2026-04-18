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

- **default_key_width**: Default width for all keys (default: 5)
- **key_widths**: Override width for specific keys (see below)
- **highlight_char**: Character used to fill pressed keys (default: "█")
- **normal_char**: Character used to fill unpressed keys (default: "░")
- **border_char**: Character used for borders (default: "─")
- **highlight_color**: Default color for pressed keys (default: "orange")
  - Available colors: orange, red, green, yellow, blue, magenta, cyan, white, bright_red, bright_green, bright_yellow, bright_blue, bright_magenta, bright_cyan, purple, pink, lime, teal, gold, gray, light_gray

### Custom Key Widths

You can set a custom width for specific keys with the `key_widths` object:

```json
"default_key_width": 5,
"key_widths": {
  "Space": 20,
  "Enter": 8,
  "Backspace": 9,
  "Shift": 8,
  "Tab": 6,
  "Caps": 6
}
```

All keys will use `default_key_width` unless specified in `key_widths`.

### Custom Key Labels

You can customize how keys are displayed with the `key_labels` object:

```json
"key_labels": {
  "W": "UP",
  "A": "←",
  "S": "↓",
  "D": "→",
  "Space": "JUMP",
  "Enter": "⏎"
}
```

### Multi-Color Key Labels

Add colors to individual characters within a key label using color tags:

```json
"key_labels": {
  "W": "W{red}A{blue}S{green}D",
  "Space": "J{cyan}U{magenta}M{yellow}P"
}
```

Each character can have its own color by adding `{colorname}` after it.

### Per-Key Colors

Override the default highlight color for specific keys:

```json
"key_colors": {
  "W": "bright_green",
  "A": "bright_green",
  "S": "bright_green",
  "D": "bright_green",
  "Space": "bright_cyan",
  "Q": "bright_red"
}
```

### Example Custom Configuration

See `keyboard_config_example.json` for a gaming keyboard setup with:
- WASD keys with custom symbols and green color
- Space bar with multi-colored "JUMP" text and custom width (20)
- Special Unicode symbols for modifier keys
- Custom widths for larger keys (Enter, Backspace, Shift)
- Custom colors per key

You can also create minimal layouts:
```json
{
  "layout": [
    ["Q", "W", "E", "R", "T", "Y"],
    ["A", "S", "D", "F", "G", "H"],
    ["Z", "X", "C", "V", "B", "N"]
  ],
  "default_key_width": 4,
  "key_widths": {},
  "highlight_char": "▓",
  "normal_char": "░",
  "border_char": "═",
  "highlight_color": "bright_cyan",
  "key_labels": {
    "W": "↑",
    "A": "←",
    "S": "↓",
    "D": "→"
  },
  "key_colors": {
    "W": "bright_green",
    "A": "bright_green",
    "S": "bright_green",
    "D": "bright_green"
  }
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
