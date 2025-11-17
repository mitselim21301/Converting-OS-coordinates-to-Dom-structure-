# MCP Accurate Click Server - Linux Examples

Comprehensive examples demonstrating accurate clicking and DOM interaction on Linux systems.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation](#installation)
3. [Examples Overview](#examples-overview)
4. [Display Server Detection](#display-server-detection)
5. [DPI and Scaling](#dpi-and-scaling)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## Getting Started

### Quick Start

```bash
# Install dependencies
pip install playwright pynput

# Run a basic example
python3 basic_linux_click.py
```

### System Requirements

- **OS**: Linux (any distribution)
- **Python**: 3.8+
- **Display Server**: X11 or Wayland
- **Browsers**: Chrome, Firefox, Edge, or Brave (for browser examples)

## Installation

### 1. Core Dependencies

```bash
pip install pynput playwright python-xlib
```

### 2. System Packages (Recommended)

#### Debian/Ubuntu:
```bash
sudo apt-get update
sudo apt-get install -y \
    x11-utils \
    xdotool \
    wmctrl \
    xrandr \
    libdbus-1-dev
```

#### Fedora/RHEL:
```bash
sudo dnf install -y \
    xorg-x11-utils \
    xdotool \
    wmctrl \
    xrandr \
    dbus-devel
```

#### Arch:
```bash
sudo pacman -S \
    xorg-utils \
    xdotool \
    wmctrl \
    libdbus
```

### 3. Browser Installation (Optional)

The examples work with multiple browsers. Install at least one:

```bash
# Chromium (Debian/Ubuntu)
sudo apt-get install chromium-browser

# Firefox (all distributions)
sudo apt-get install firefox

# Google Chrome (Ubuntu)
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb

# Brave (Ubuntu)
sudo apt-get install brave-browser
```

## Examples Overview

### 1. **basic_linux_click.py**
Simple example demonstrating:
- Display server detection (X11 vs Wayland)
- DOM structure extraction
- Simple clicking
- Basic error handling

**Run**: `python3 basic_linux_click.py`

**When to use**: Start here to understand the basics.

### 2. **multi_monitor_linux.py**
Demonstrates:
- Detecting all connected monitors
- Per-monitor DPI detection
- Handling fractional scaling (125%, 150%, 175%)
- Clicking across monitor boundaries
- HiDPI/Retina display support

**Run**: `python3 multi_monitor_linux.py`

**When to use**: You have multiple monitors or need scaling awareness.

### 3. **browser_automation_linux.py**
Demonstrates:
- Detecting installed browsers (Chrome, Firefox, Edge, Brave)
- Launching browsers with optimal settings
- Handling browser-specific scaling
- DOM extraction and clicking
- Cross-browser compatibility

**Run**: `python3 browser_automation_linux.py`

**When to use**: Automating browser tasks across different browsers.

### 4. **dpi_detection_linux.py**
Demonstrates:
- System DPI querying
- Per-monitor DPI detection
- Fractional scaling detection
- HiDPI/Retina display identification
- Coordinate conversion based on DPI

**Run**: `python3 dpi_detection_linux.py`

**When to use**: You need to understand DPI/scaling in your environment.

### 5. **x11_example.py**
X11-specific example showing:
- X11 window detection and listing
- python-xlib integration
- Low-level X11 input
- Window focus management
- Clipboard operations

**Run**: `python3 x11_example.py` (X11 only)

**When to use**: You're on X11 and need direct window access.

**Note**: This example only works on X11. It detects Wayland and exits gracefully.

### 6. **wayland_example.py**
Wayland-specific example showing:
- Wayland environment detection
- D-Bus integration
- Fractional scaling support
- Compositor detection (GNOME, KDE, Sway)
- Wayland-specific browser options

**Run**: `python3 wayland_example.py` (Wayland only)

**When to use**: You're on Wayland and need modern display server support.

**Note**: This example only works on Wayland. It detects X11 and exits gracefully.

## Display Server Detection

### How to Check Your Display Server

```bash
# Method 1: Check XDG_SESSION_TYPE
echo $XDG_SESSION_TYPE  # Output: x11 or wayland

# Method 2: Check DISPLAY (X11) or WAYLAND_DISPLAY (Wayland)
echo $DISPLAY           # X11: :0, :1, etc.
echo $WAYLAND_DISPLAY   # Wayland: wayland-0, wayland-1, etc.

# Method 3: Query systemd session
loginctl show-session -p Type

# Method 4: Check if Xvfb is running (headless X11)
ps aux | grep X
```

### Switching Between X11 and Wayland

Most modern Linux distributions allow switching at login:

1. **Click your username** at the login screen (GNOME/KDE)
2. **Select the session type** (usually shown as "GNOME" vs "GNOME (Wayland)")
3. **Log in**

Or use your desktop environment's display server settings:
- **GNOME**: Settings → About → Switch to Wayland/X11
- **KDE**: System Settings → Display and Monitor → Compositor

## DPI and Scaling

### Understanding DPI on Linux

**X11 DPI Calculation**:
```
DPI = (pixel_width / physical_width_in_inches) * 96
Scale = DPI / 96
```

**Wayland DPI**:
- Environment variable based: `GDK_SCALE`, `QT_SCALE_FACTOR`
- Typically: 1.0 (100%), 1.25 (125%), 1.5 (150%), 2.0 (200%)

### Checking Your DPI

```bash
# Check system DPI
xdpyinfo | grep resolution

# Check monitor information (X11)
xrandr

# Check Wayland scaling
echo $GDK_SCALE
echo $QT_SCALE_FACTOR

# Check physical DPI (requires xdpyinfo)
xdpyinfo | grep -A5 "screen #0"
```

### Common DPI Values

| DPI | Scale | Usage |
|-----|-------|-------|
| 96  | 100%  | Standard (default baseline) |
| 120 | 125%  | Tablets, 2-in-1 devices |
| 144 | 150%  | High-resolution laptops |
| 168 | 175%  | Very high DPI displays |
| 192 | 200%  | Retina/HiDPI displays |

### Fractional Scaling Support

**X11**: Limited, depends on compositor
**Wayland**: Full support, native 125%, 150%, 175%

To enable fractional scaling on GNOME Wayland:
```bash
# Enable experimental fractional scaling
gsettings set org.gnome.mutter experimental-features "['scale-monitor-framebuffer']"
```

## Best Practices

### 1. Always Detect Display Server First

```python
import os

def get_display_server():
    session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
    if session_type == 'wayland':
        return 'wayland'
    elif session_type == 'x11' or os.environ.get('DISPLAY'):
        return 'x11'
    return 'unknown'
```

### 2. Handle DPI Scaling

```python
# Get DPI for accurate coordinates
from mcp_server.platform.linux import LinuxDPIHandler

dpi_handler = LinuxDPIHandler()
monitors = dpi_handler.get_monitors()

for monitor in monitors:
    scale = monitor.dpi / 96.0  # 96 is baseline
    print(f"Monitor: {monitor.width}x{monitor.height} @ {scale:.2f}x scaling")
```

### 3. Use Platform-Specific Input When Possible

```python
# Prefer platform-specific input simulators
from mcp_server.platform.linux import LinuxInputSimulator

simulator = LinuxInputSimulator()
simulator.click(x, y)  # More reliable than pynput
```

### 4. Account for Coordinate Systems

Linux has multiple coordinate systems:

1. **Logical Coordinates**: What applications see (DPI-adjusted)
2. **Physical Coordinates**: Actual screen pixels
3. **Viewport Coordinates**: Browser-specific

```python
# Example: Converting logical to physical
logical_x, logical_y = 100, 100
scale_factor = 1.5  # 150% scaling

physical_x = logical_x * scale_factor
physical_y = logical_y * scale_factor
```

### 5. Always Add Error Handling

```python
try:
    simulator.click(x, y)
except Exception as e:
    logger.error(f"Click failed: {e}")
    # Fall back to alternative method
    try:
        page.mouse.click(x, y)  # Playwright fallback
    except:
        logger.error("All click methods failed")
```

### 6. Test on Both X11 and Wayland

```python
# Check which system you're on
if get_display_server() == 'x11':
    # Use X11-specific features
    window = get_x11_window()
else:
    # Use Wayland-compatible methods
    use_wayland_methods()
```

### 7. Handle Multi-Monitor Setups

```python
# Always check which monitor the browser is on
monitors = dpi_handler.get_monitors()

for monitor in monitors:
    if monitor.contains_point(window_x, window_y):
        # Apply this monitor's scaling
        scale = monitor.dpi / 96.0
        break
```

## Troubleshooting

### Common Issues

#### 1. "Permission denied" errors
**Problem**: Cannot access input devices

**Solution**:
```bash
# Add user to input group
sudo usermod -a -G input $USER
newgrp input

# Or run with sudo
sudo python3 example.py
```

#### 2. Clicks not registering
**Problem**: Clicks work in some applications but not others

**Possible causes**:
- Window not in focus (especially on Wayland)
- Incorrect coordinate system
- DPI scaling not accounted for

**Solution**:
```python
# 1. Ensure window has focus
page.focus()

# 2. Check DPI/scaling
dpi_handler = LinuxDPIHandler()
monitors = dpi_handler.get_monitors()

# 3. Use Playwright's coordinate system
page.mouse.click(x, y)  # Handles DPI internally
```

#### 3. DPI detection returns 96 DPI on HiDPI display
**Problem**: System not reporting correct DPI

**Possible causes**:
- xrandr not available
- Wayland without proper scale detection
- Fractional scaling not detected

**Solution**:
```bash
# Install xrandr
sudo apt-get install xrandr

# Check physical monitor info
xrandr --query

# On Wayland, set manually
export GDK_SCALE=2  # For 200% scaling
```

#### 4. "Display not found" error on Wayland
**Problem**: WAYLAND_DISPLAY not set

**Solution**:
```bash
# Check available displays
ls /run/user/$(id -u)/wayland-*

# Set manually if needed
export WAYLAND_DISPLAY=wayland-0
```

#### 5. Browser not launching
**Problem**: Playwright cannot find browser

**Solution**:
```bash
# Install browsers
sudo apt-get install chromium-browser firefox

# Or let Playwright download them
python3 -m pytest --install
```

#### 6. Multi-monitor coordinates wrong
**Problem**: Clicking on secondary monitor doesn't work

**Possible causes**:
- Monitor offsets not accounted for
- Different DPI on each monitor
- Coordinate system confusion

**Solution**:
```python
# Get monitor layout
monitors = dpi_handler.get_monitors()

# Find which monitor contains point
for monitor in monitors:
    if monitor.contains_point(x, y):
        # Convert to monitor-relative coordinates
        rel_x = x - monitor.offset_x
        rel_y = y - monitor.offset_y
        break
```

### Debug Logging

Enable detailed logging for troubleshooting:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# This will show detailed information about:
# - Display server detection
# - DPI queries
# - Monitor information
# - Click attempts
# - Coordinate conversions
```

### Checking System Capabilities

```bash
# List all monitors and DPI
xrandr --query --verbose

# Check window manager
echo $DESKTOP_SESSION
loginctl show-session -p Type

# Check input devices
ls -la /dev/input/

# Check Xlib availability
python3 -c "from Xlib import display; print('Xlib OK')"

# Check xdotool
which xdotool
xdotool --version
```

## Environment Variables Reference

### Display Server Detection
- `XDG_SESSION_TYPE`: Session type (x11, wayland, tty)
- `DISPLAY`: X11 display (e.g., :0)
- `WAYLAND_DISPLAY`: Wayland display (e.g., wayland-0)

### DPI and Scaling
- `GDK_SCALE`: Integer scaling for GTK apps (1, 2, 3)
- `GDK_DPI_SCALE`: Decimal scaling for GTK apps
- `QT_SCALE_FACTOR`: Scaling for Qt apps
- `QT_DPI`: Explicit DPI for Qt apps
- `XCURSOR_SIZE`: Cursor size

### Desktop Environment
- `DESKTOP_SESSION`: Current desktop session
- `GNOME_SESSION_NAME`: GNOME-specific
- `KDE_SESSION_VERSION`: KDE-specific

## Additional Resources

### Linux Display Server Documentation
- [X11 Documentation](https://www.x.org/releases/X11R7.7/doc/index.html)
- [Wayland Documentation](https://wayland.freedesktop.org/)
- [xrandr Manual](https://man.archlinux.org/man/xrandr.1)
- [X11 Window Properties](https://tronche.com/gui/x/xlib/window-information/properties-and-atoms.html)

### Python Libraries
- [Playwright](https://playwright.dev/python/)
- [pynput](https://pynput.readthedocs.io/)
- [python-xlib](https://python-xlib.github.io/)

### MCP Accurate Click Server
- [Project Repository](../)
- [Core Documentation](../../README.md)

## Examples Summary Table

| Example | Platform | Purpose | Complexity |
|---------|----------|---------|------------|
| basic_linux_click.py | Both | Getting started | Beginner |
| multi_monitor_linux.py | Both | Multi-monitor setup | Intermediate |
| browser_automation_linux.py | Both | Browser automation | Intermediate |
| dpi_detection_linux.py | Both | DPI/scaling analysis | Intermediate |
| x11_example.py | X11 only | Native X11 features | Advanced |
| wayland_example.py | Wayland only | Modern Wayland features | Advanced |

## Contributing

Found an issue? Have a suggestion? Please open an issue or PR in the main repository.

## License

These examples are part of the MCP Accurate Click Server project. See LICENSE file for details.
