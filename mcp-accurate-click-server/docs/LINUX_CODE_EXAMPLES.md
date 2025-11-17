# Linux Code Examples
## MCP Accurate Click Server on Linux

**Version**: 1.0.0
**Last Updated**: 2025-11-17
**Target**: X11 and Wayland desktop environments

---

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [DPI Detection](#dpi-detection)
3. [Coordinate Transformation](#coordinate-transformation)
4. [Click Operations](#click-operations)
5. [Input Simulation](#input-simulation)
6. [Multi-Monitor Setup](#multi-monitor-setup)
7. [Display Server Detection](#display-server-detection)
8. [Advanced Examples](#advanced-examples)

---

## Basic Usage

### Initialize the Linux Platform Module

```python
# Example 1.1: Basic initialization on Linux
from mcp_server.platform import PlatformFactory

# Automatically detects Linux and returns Linux converter
converter = PlatformFactory.get_coordinate_converter()
print(f"Platform: {type(converter).__name__}")  # LinuxCoordinateConverter

# Get DPI information
dpi_info = converter.get_dpi_info()
print(f"Primary Monitor DPI: {dpi_info['dpi']}")
```

### Check Platform Capabilities

```python
# Example 1.2: Check if running on supported display server
import sys
from mcp_server.platform import PlatformFactory

if sys.platform.startswith('linux'):
    converter = PlatformFactory.get_coordinate_converter()
    dpi_info = converter.get_dpi_info()

    if dpi_info['display_server'] == 'x11':
        print("Running on X11 (Xorg)")
        # Use X11-specific optimizations
    elif dpi_info['display_server'] == 'wayland':
        print("Running on Wayland")
        # Use Wayland-specific features
    else:
        print("Unknown display server")
```

---

## DPI Detection

### Basic DPI Detection

```python
# Example 2.1: Get DPI for primary monitor
from mcp_server.platform.linux import LinuxDPIHandler

handler = LinuxDPIHandler()
dpi = handler.get_primary_monitor_dpi()
print(f"Primary Monitor DPI: {dpi}")

# Example output:
# Primary Monitor DPI: 96  (standard, 100%)
# or
# Primary Monitor DPI: 109 (high DPI, ~113%)
```

### Get All Monitor Information

```python
# Example 2.2: Get all monitors with DPI info
from mcp_server.platform.linux import LinuxDPIHandler

handler = LinuxDPIHandler()
monitors = handler.get_monitors()

for monitor in monitors:
    print(f"\nMonitor: {monitor['name']}")
    print(f"  Connected: {monitor['connected']}")
    print(f"  Primary: {monitor['primary']}")
    print(f"  Resolution: {monitor['resolution']}")
    print(f"  Physical Size: {monitor['physical_size']} mm")
    print(f"  DPI: {monitor['dpi']}")
    print(f"  Position: {monitor['position']}")
    print(f"  Rotation: {monitor['rotation']}")

# Example output:
# Monitor: HDMI-1
#   Connected: True
#   Primary: True
#   Resolution: (1920, 1080)
#   Physical Size: (509, 286) mm
#   DPI: 96
#   Position: (0, 0)
#   Rotation: Normal
#
# Monitor: DP-1
#   Connected: True
#   Primary: False
#   Resolution: (2560, 1440)
#   Physical Size: (597, 336) mm
#   DPI: 109
#   Position: (1920, 0)
#   Rotation: Normal
```

### Get Complete DPI Info

```python
# Example 2.3: Get complete DPI information structure
from mcp_server.platform.linux import LinuxDPIHandler

handler = LinuxDPIHandler()
dpi_info = handler.get_dpi_info()

print(f"Display Server: {dpi_info['display_server']}")
print(f"Primary Monitor: {dpi_info['primary_monitor']}")
print(f"Primary Monitor DPI: {dpi_info['dpi']}")
print(f"Scale Factor: {dpi_info['scale_factor']}")

# Per-monitor information
for monitor_name, info in dpi_info['monitors'].items():
    print(f"\n{monitor_name}:")
    print(f"  DPI: {info['dpi']}")
    print(f"  Scale Factor: {info['scale_factor']}")
    print(f"  Resolution: {info['resolution']}")
    print(f"  Position: {info['position']}")
```

### Handle DPI Override

```python
# Example 2.4: Override detected DPI (useful for testing)
import os
from mcp_server.platform.linux import LinuxDPIHandler

# Set environment variable
os.environ['MCP_DPI_OVERRIDE'] = '120'

handler = LinuxDPIHandler()
dpi_info = handler.get_dpi_info()
print(f"DPI: {dpi_info['dpi']}")  # Will be 120 instead of detected

# Or set in code
from mcp_server.platform.linux.dpi_handler import LinuxDPIHandler
handler = LinuxDPIHandler()
handler.dpi_override = 144
dpi = handler.get_primary_monitor_dpi()
print(f"Overridden DPI: {dpi}")  # 144
```

---

## Coordinate Transformation

### Convert OS Screen to Viewport

```python
# Example 3.1: Transform OS screen coordinates to viewport
from mcp_server.platform import PlatformFactory

converter = PlatformFactory.get_coordinate_converter()

# OS screen coordinates (where mouse is)
os_x, os_y = 1920, 1080

# Convert to viewport coordinates (where click happens in browser)
viewport_x, viewport_y = converter.os_to_viewport(os_x, os_y)

print(f"OS Screen: ({os_x}, {os_y})")
print(f"Viewport: ({viewport_x}, {viewport_y})")

# Example output:
# Without scaling:
#   OS Screen: (1920, 1080) → Viewport: (1920, 1080)
#
# With 125% scaling:
#   OS Screen: (1920, 1080) → Viewport: (1536, 864)
```

### Convert Viewport to OS Screen

```python
# Example 3.2: Transform viewport coordinates back to OS screen
from mcp_server.platform import PlatformFactory

converter = PlatformFactory.get_coordinate_converter()

# Viewport coordinates (where element is in browser)
viewport_x, viewport_y = 400, 300

# Convert to OS coordinates (for mouse simulation)
os_x, os_y = converter.viewport_to_os(viewport_x, viewport_y)

print(f"Viewport: ({viewport_x}, {viewport_y})")
print(f"OS Screen: ({os_x}, {os_y})")
```

### Round-Trip Transformation

```python
# Example 3.3: Verify round-trip accuracy
from mcp_server.platform import PlatformFactory

converter = PlatformFactory.get_coordinate_converter()

# Start with OS coordinates
original_x, original_y = 1920.5, 1080.5

# Convert to viewport and back
viewport_x, viewport_y = converter.os_to_viewport(original_x, original_y)
back_x, back_y = converter.viewport_to_os(viewport_x, viewport_y)

# Should be nearly identical (sub-pixel precision)
print(f"Original: ({original_x}, {original_y})")
print(f"Viewport: ({viewport_x}, {viewport_y})")
print(f"Back to OS: ({back_x}, {back_y})")
print(f"Error: ({abs(original_x - back_x)}, {abs(original_y - back_y)}) pixels")

# Example output:
# Original: (1920.5, 1080.5)
# Viewport: (1920.5, 1080.5)
# Back to OS: (1920.5, 1080.5)
# Error: (0.0, 0.0) pixels  (perfect accuracy)
```

### Batch Coordinate Transformation

```python
# Example 3.4: Transform multiple coordinates efficiently
from mcp_server.platform import PlatformFactory

converter = PlatformFactory.get_coordinate_converter()

# Multiple viewport coordinates
viewport_coords = [
    (100, 100),
    (200, 200),
    (400, 300),
    (500, 400),
]

# Transform all at once (more efficient than individual calls)
os_coords = converter.transform_batch(
    viewport_coords,
    from_system='viewport',
    to_system='os_screen'
)

for vp, os in zip(viewport_coords, os_coords):
    print(f"Viewport {vp} → OS {os}")
```

---

## Click Operations

### Simple Click on Viewport Coordinates

```python
# Example 4.1: Click at viewport coordinates
from mcp_server.platform import PlatformFactory

converter = PlatformFactory.get_coordinate_converter()
simulator = PlatformFactory.get_input_simulator()

# Browser viewport coordinate of button
viewport_x, viewport_y = 400, 300

# Convert to OS screen coordinates
os_x, os_y = converter.viewport_to_os(viewport_x, viewport_y)

# Simulate click
success = simulator.click(os_x, os_y, button='left')
print(f"Click {'succeeded' if success else 'failed'}")
```

### Validate Click Before Clicking

```python
# Example 4.2: Validate element before clicking
from mcp_server.platform import PlatformFactory

converter = PlatformFactory.get_coordinate_converter()
validator = PlatformFactory.get_click_validator()
simulator = PlatformFactory.get_input_simulator()

# Element from DOM extraction
element = {
    'tag_name': 'button',
    'bounding_box': {'x': 100, 'y': 100, 'width': 100, 'height': 40},
    'is_visible': True,
    'is_enabled': True,
    'z_index': 1,
    'pointer_events': 'auto',
    'text_content': 'Submit'
}

# Click at center of element (viewport coordinates)
click_x = element['bounding_box']['x'] + element['bounding_box']['width'] / 2
click_y = element['bounding_box']['y'] + element['bounding_box']['height'] / 2

# Validate click
validation = validator.validate_click_target(element, click_x, click_y)

if validation['valid']:
    print(f"✓ Element is clickable (confidence: {validation['confidence']:.1%})")

    # Convert and click
    os_x, os_y = converter.viewport_to_os(click_x, click_y)
    success = simulator.click(os_x, os_y)
    print(f"Click {'succeeded' if success else 'failed'}")
else:
    print(f"✗ Cannot click element:")
    for error in validation['errors']:
        print(f"  - {error}")
```

### Click with Double-Click

```python
# Example 4.3: Double-click operation
from mcp_server.platform import PlatformFactory

simulator = PlatformFactory.get_input_simulator()

# OS screen coordinates
os_x, os_y = 500, 400

# Double-click at position
success = simulator.double_click(os_x, os_y, delay=0.1)
print(f"Double-click {'succeeded' if success else 'failed'}")
```

---

## Input Simulation

### Type Text

```python
# Example 5.1: Type text using keyboard
from mcp_server.platform import PlatformFactory

simulator = PlatformFactory.get_input_simulator()

# Type simple text
text = "Hello, World!"
success = simulator.type_text(text)
print(f"Typed '{text}': {'success' if success else 'failed'}")

# Type special characters and Unicode
text_unicode = "こんにちは世界"  # Hello World in Japanese
success = simulator.type_text(text_unicode)
print(f"Typed Unicode: {'success' if success else 'failed'}")
```

### Press Individual Keys

```python
# Example 5.2: Press specific keys
from mcp_server.platform import PlatformFactory

simulator = PlatformFactory.get_input_simulator()

# Press Enter
simulator.press_key('Return')

# Press Tab
simulator.press_key('Tab')

# Press Delete
simulator.press_key('Delete')

# Press Escape
simulator.press_key('Escape')

# Available keys on Linux:
# Return, Tab, BackSpace, Delete, Escape
# Home, End, PageUp, PageDown
# Left, Right, Up, Down
# F1-F12, Insert, Pause, etc.
```

### Keyboard Shortcuts

```python
# Example 5.3: Press key combinations
from mcp_server.platform import PlatformFactory

simulator = PlatformFactory.get_input_simulator()

# Ctrl+A (select all)
simulator.key_combination('Control', 'a')

# Ctrl+C (copy)
simulator.key_combination('Control', 'c')

# Ctrl+V (paste)
simulator.key_combination('Control', 'v')

# Ctrl+Z (undo)
simulator.key_combination('Control', 'z')

# Shift+Tab (reverse tab)
simulator.key_combination('Shift', 'Tab')

# Alt+F4 (close window)
simulator.key_combination('Alt', 'F4')
```

### Type and Press Combination

```python
# Example 5.4: Type and press keys in sequence
from mcp_server.platform import PlatformFactory

simulator = PlatformFactory.get_input_simulator()

# Type search query and press Enter
simulator.type_text("python mcp")
simulator.press_key('Return')

# Or with delay for slower systems
import time

simulator.type_text("python")
time.sleep(0.2)
simulator.type_text(" ")
time.sleep(0.2)
simulator.type_text("mcp")
time.sleep(0.2)
simulator.press_key('Return')
```

---

## Multi-Monitor Setup

### Detect Monitor Count

```python
# Example 6.1: Detect number of connected monitors
from mcp_server.platform.linux import LinuxDPIHandler

handler = LinuxDPIHandler()
monitors = handler.get_monitors()

connected_monitors = [m for m in monitors if m['connected']]
print(f"Connected monitors: {len(connected_monitors)}")

for monitor in connected_monitors:
    print(f"  - {monitor['name']}: {monitor['resolution']} @ {monitor['dpi']} DPI")
```

### Handle Different DPI per Monitor

```python
# Example 6.2: Transform coordinates for specific monitor
from mcp_server.platform import PlatformFactory
from mcp_server.platform.linux import LinuxDPIHandler

converter = PlatformFactory.get_coordinate_converter()
dpi_handler = LinuxDPIHandler()

# Get monitor info
monitors = dpi_handler.get_monitors()
print("Monitor DPI Information:")

dpi_info = converter.get_dpi_info()

for monitor_name, monitor_info in dpi_info['monitors'].items():
    dpi = monitor_info['dpi']
    scale = monitor_info['scale_factor']
    res = monitor_info['resolution']
    pos = monitor_info['position']

    print(f"\n{monitor_name}:")
    print(f"  Position: {pos}")
    print(f"  Resolution: {res}")
    print(f"  DPI: {dpi} (scale: {scale:.2f}x)")

    # Calculate viewport for element at (100, 100) on this monitor
    # Adjust for monitor position
    abs_x = pos[0] + 100
    abs_y = pos[1] + 100

    # Transform using main converter (handles per-monitor DPI)
    viewport_x, viewport_y = converter.os_to_viewport(abs_x, abs_y)
    print(f"  Example: OS ({abs_x}, {abs_y}) → Viewport ({viewport_x}, {viewport_y})")
```

### Click on Secondary Monitor

```python
# Example 6.3: Click on element on secondary monitor
from mcp_server.platform import PlatformFactory
from mcp_server.platform.linux import LinuxDPIHandler

converter = PlatformFactory.get_coordinate_converter()
simulator = PlatformFactory.get_input_simulator()
dpi_handler = LinuxDPIHandler()

# Get primary monitor position
monitors = dpi_handler.get_monitors()
primary = next(m for m in monitors if m['primary'])
secondary = next((m for m in monitors if not m['primary']), None)

if secondary:
    # Element is on secondary monitor
    element_x_local = 100  # Local to secondary monitor
    element_y_local = 100

    # Get secondary monitor position in screen space
    secondary_x, secondary_y = secondary['position']

    # Calculate absolute screen coordinates
    abs_x = secondary_x + element_x_local
    abs_y = secondary_y + element_y_local

    # The converter handles per-monitor DPI automatically
    # Just provide absolute screen coordinates
    viewport_x, viewport_y = converter.os_to_viewport(abs_x, abs_y)

    # Convert back to OS for clicking
    os_x, os_y = converter.viewport_to_os(viewport_x, viewport_y)
    simulator.click(os_x, os_y)

    print(f"Clicked on secondary monitor at ({os_x}, {os_y})")
```

---

## Display Server Detection

### Detect X11 vs Wayland

```python
# Example 7.1: Check display server type
from mcp_server.platform.linux import LinuxDPIHandler

handler = LinuxDPIHandler()
display_server = handler._detect_display_server()

print(f"Display Server: {display_server}")

if display_server == 'x11':
    print("✓ Running on X11 (Xorg)")
    print("  - Use xdotool for input simulation")
    print("  - Use xrandr for monitor detection")
    print("  - Older but more stable")

elif display_server == 'wayland':
    print("✓ Running on Wayland")
    print("  - Modern display server")
    print("  - Better performance on some systems")
    print("  - Use wlr-randr for monitor detection")

else:
    print("⚠ Unknown display server")
```

### Check X11 Environment

```python
# Example 7.2: Verify X11 environment variables
import os

print("X11 Environment Variables:")
print(f"  DISPLAY: {os.environ.get('DISPLAY', 'not set')}")
print(f"  XAUTHORITY: {os.environ.get('XAUTHORITY', 'not set')}")
print(f"  XKBVARIANT: {os.environ.get('XKBVARIANT', 'not set')}")

# For X11 to work, DISPLAY must be set
if not os.environ.get('DISPLAY'):
    print("⚠ X11 not available (DISPLAY not set)")
    print("  Running in headless mode or on Wayland")
```

### Check Wayland Environment

```python
# Example 7.3: Verify Wayland environment variables
import os

print("Wayland Environment Variables:")
print(f"  XDG_SESSION_TYPE: {os.environ.get('XDG_SESSION_TYPE', 'not set')}")
print(f"  WAYLAND_DISPLAY: {os.environ.get('WAYLAND_DISPLAY', 'not set')}")
print(f"  WAYLAND_SOCKET: {os.environ.get('WAYLAND_SOCKET', 'not set')}")

# For Wayland
if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
    print("✓ Wayland detected")
```

---

## Advanced Examples

### Complete Click Workflow

```python
# Example 8.1: Complete workflow from element to click
from mcp_server.platform import PlatformFactory
from mcp_server.platform.linux import LinuxDPIHandler

# Setup
converter = PlatformFactory.get_coordinate_converter()
validator = PlatformFactory.get_click_validator()
simulator = PlatformFactory.get_input_simulator()
dpi_handler = LinuxDPIHandler()

# Show system info
dpi_info = converter.get_dpi_info()
print(f"System: {dpi_info['display_server'].upper()} Display Server")
print(f"DPI: {dpi_info['dpi']}")
print(f"Scale: {dpi_info['scale_factor']:.2f}x")

# Target element from DOM
button = {
    'tag_name': 'button',
    'id': 'submit-btn',
    'bounding_box': {'x': 150, 'y': 200, 'width': 120, 'height': 40},
    'is_visible': True,
    'is_enabled': True,
    'z_index': 10,
    'pointer_events': 'auto',
    'text_content': 'Submit Form'
}

# Calculate click point (center of button)
click_x = button['bounding_box']['x'] + button['bounding_box']['width'] / 2
click_y = button['bounding_box']['y'] + button['bounding_box']['height'] / 2

# Step 1: Validate
print(f"\n1. Validating element '{button['text_content']}'...")
validation = validator.validate_click_target(button, click_x, click_y)

if not validation['valid']:
    print("✗ Validation failed:")
    for error in validation['errors']:
        print(f"    - {error}")
    exit(1)

print(f"✓ Validation passed (confidence: {validation['confidence']:.1%})")

# Step 2: Transform coordinates
print(f"\n2. Transforming coordinates...")
print(f"    Viewport: ({click_x}, {click_y})")

os_x, os_y = converter.viewport_to_os(click_x, click_y)
print(f"    OS Screen: ({os_x:.1f}, {os_y:.1f})")

# Step 3: Click
print(f"\n3. Executing click...")
import time
time.sleep(0.1)  # Small delay before clicking

success = simulator.click(os_x, os_y, button='left')

if success:
    print(f"✓ Click executed successfully")
    print(f"    Clicked element: {button['tag_name']}#{button['id']}")
    print(f"    Text: '{button['text_content']}'")
else:
    print(f"✗ Click failed")
```

### Element Hunting with Multiple Strategies

```python
# Example 8.2: Find and click element using multiple strategies
from mcp_server.platform import PlatformFactory

converter = PlatformFactory.get_coordinate_converter()
simulator = PlatformFactory.get_input_simulator()

# Try multiple ways to find and click element
def click_element(viewport_coords_list, button_name):
    """Try to click button using multiple coordinate options"""

    print(f"\nTrying to click '{button_name}'...")

    for i, (vp_x, vp_y) in enumerate(viewport_coords_list, 1):
        try:
            # Convert coordinates
            os_x, os_y = converter.viewport_to_os(vp_x, vp_y)

            # Try click
            success = simulator.click(os_x, os_y, button='left')

            if success:
                print(f"✓ Clicked using strategy {i} at ({vp_x}, {vp_y})")
                return True

        except Exception as e:
            print(f"  Strategy {i} failed: {e}")
            continue

    print(f"✗ Failed to click '{button_name}' with all strategies")
    return False

# Try different possible coordinates for a button
button_coords = [
    (500, 300),   # Expected center
    (510, 305),   # Slightly different
    (490, 295),   # Another variation
]

click_element(button_coords, "Login Button")
```

### System Performance Monitoring

```python
# Example 8.3: Monitor performance of coordinate operations
from mcp_server.platform import PlatformFactory
import time

converter = PlatformFactory.get_coordinate_converter()

# Test coordinate transformation performance
print("Coordinate Transformation Performance:")

# Single transform
start = time.time()
for _ in range(1000):
    converter.os_to_viewport(1920, 1080)
elapsed = time.time() - start
avg_us = (elapsed * 1000000) / 1000
print(f"  Single transform: {avg_us:.2f} μs")

# Batch transform
coords = [(i*100, i*100) for i in range(100)]
start = time.time()
for _ in range(10):
    converter.transform_batch(coords, 'os_screen', 'viewport')
elapsed = time.time() - start
avg_us = (elapsed * 1000000) / 1000
print(f"  Batch transform (100 points): {avg_us:.2f} μs total")

# DPI detection
print("\nDPI Detection Performance:")
start = time.time()
dpi_info = converter.get_dpi_info()
elapsed = time.time() - start
print(f"  First call: {elapsed*1000:.2f} ms")

start = time.time()
dpi_info = converter.get_dpi_info()
elapsed = time.time() - start
print(f"  Cached call: {elapsed*1000:.3f} ms")
```

---

## Common Linux Patterns

### Detect and Adapt to Display Server

```python
# Example 8.4: Adapt behavior based on display server
from mcp_server.platform import PlatformFactory
from mcp_server.platform.linux import LinuxDPIHandler

converter = PlatformFactory.get_coordinate_converter()
dpi_info = converter.get_dpi_info()

display_server = dpi_info['display_server']

if display_server == 'x11':
    # X11-specific optimizations
    print("Using X11 optimizations")
    # - DPI is fixed, no fractional scaling by default
    # - xdotool is reliable
    # - Can use xclip for clipboard

elif display_server == 'wayland':
    # Wayland-specific optimizations
    print("Using Wayland optimizations")
    # - Compositors handle scaling
    # - May need wl-paste for clipboard
    # - Better performance on some systems

else:
    print("Adapting to unknown display server")
```

### Safe Input Simulation

```python
# Example 8.5: Safe input simulation with error handling
from mcp_server.platform import PlatformFactory
from mcp_server.platform.errors import InputSimulationError

simulator = PlatformFactory.get_input_simulator()

def safe_type_text(text):
    """Type text with error handling"""
    try:
        success = simulator.type_text(text)
        if success:
            print(f"✓ Typed: {text}")
            return True
        else:
            print(f"⚠ Type returned False for: {text}")
            return False
    except InputSimulationError as e:
        print(f"✗ Input simulation error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

# Try to type
if not safe_type_text("username"):
    print("Fallback: Could not simulate keyboard input")
```

---

## Integration with MCP Server

### Use from MCP Tool

```python
# Example 8.6: How Linux platform is used within MCP server
from mcp_server.platform import PlatformFactory
from mcp_server.core.dom_extractor import DOMExtractor

# MCP tool implementation (internal)
async def click_element_impl(method, value):
    """MCP tool: click_element"""

    converter = PlatformFactory.get_coordinate_converter()
    simulator = PlatformFactory.get_input_simulator()
    validator = PlatformFactory.get_click_validator()

    # Find element (using DOM extraction)
    extractor = DOMExtractor()
    elements = await extractor.extract_dom_structure()

    # Find matching element
    target = None
    if method == 'text':
        target = next((e for e in elements if e.get('text_content') == value), None)
    elif method == 'selector':
        target = next((e for e in elements if e.get('selector') == value), None)

    if not target:
        return {'success': False, 'error': f'Element not found: {value}'}

    # Validate
    click_x = target['bounding_box']['x'] + target['bounding_box']['width'] / 2
    click_y = target['bounding_box']['y'] + target['bounding_box']['height'] / 2

    validation = validator.validate_click_target(target, click_x, click_y)
    if not validation['valid']:
        return {'success': False, 'error': 'Element not clickable', 'reasons': validation['errors']}

    # Execute click
    os_x, os_y = converter.viewport_to_os(click_x, click_y)
    success = simulator.click(os_x, os_y)

    return {
        'success': success,
        'element': target.get('selector'),
        'coordinates': {'viewport': [click_x, click_y], 'os': [os_x, os_y]},
        'validation': validation
    }
```

---

## Testing Examples

### Unit Test for Linux Converter

```python
# Example 8.7: Test Linux coordinate converter
import pytest
from mcp_server.platform.linux import LinuxCoordinateConverter

def test_linux_coordinate_conversion():
    """Test coordinate transformation on Linux"""
    converter = LinuxCoordinateConverter()

    # Test basic transformation
    os_x, os_y = converter.os_to_viewport(1920, 1080)
    assert isinstance(os_x, float)
    assert isinstance(os_y, float)

    # Test round-trip
    back_x, back_y = converter.viewport_to_os(os_x, os_y)
    assert abs(back_x - 1920) < 0.01
    assert abs(back_y - 1080) < 0.01

def test_dpi_detection():
    """Test DPI detection"""
    converter = LinuxCoordinateConverter()
    dpi_info = converter.get_dpi_info()

    assert 'dpi' in dpi_info
    assert 'scale_factor' in dpi_info
    assert 'display_server' in dpi_info
    assert dpi_info['dpi'] > 50  # Sanity check
    assert dpi_info['dpi'] < 500  # Sanity check
```

---

**Version**: 1.0.0
**Last Updated**: 2025-11-17
**Platform**: Linux (X11 and Wayland)
