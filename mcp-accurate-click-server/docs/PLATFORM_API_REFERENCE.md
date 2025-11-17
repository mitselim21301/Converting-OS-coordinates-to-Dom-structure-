# Platform Abstraction Layer - API Reference
## MCP Accurate Click Server

**Version**: 1.0.0
**Last Updated**: 2025-11-17

---

## Table of Contents

1. [Platform Factory](#platform-factory)
2. [Base Classes](#base-classes)
3. [Platform Implementations](#platform-implementations)
4. [Code Examples](#code-examples)
5. [Error Handling](#error-handling)
6. [Thread Safety](#thread-safety)

---

## Platform Factory

### PlatformFactory Class

**Purpose**: Single entry point for platform-specific implementations

**Location**: `src/mcp_server/platform/__init__.py`

```python
from mcp_server.platform import PlatformFactory

# Get platform-specific converter (auto-detected)
converter = PlatformFactory.get_coordinate_converter()

# Get platform-specific click validator
validator = PlatformFactory.get_click_validator()

# Get platform-specific input simulator
simulator = PlatformFactory.get_input_simulator()
```

### Factory Methods

```python
class PlatformFactory:
    """Factory for creating platform-specific implementations"""

    @staticmethod
    def get_coordinate_converter() -> PlatformCoordinateConverter:
        """
        Get platform-specific coordinate converter.

        Returns:
            PlatformCoordinateConverter: Windows, Linux, or macOS converter

        Raises:
            NotImplementedError: If platform is not supported

        Example:
            >>> converter = PlatformFactory.get_coordinate_converter()
            >>> viewport_x, viewport_y = converter.os_to_viewport(1920, 1080)
        """
        pass

    @staticmethod
    def get_click_validator() -> PlatformClickValidator:
        """
        Get platform-specific click validator.

        Returns:
            PlatformClickValidator: Platform-specific validator

        Raises:
            NotImplementedError: If platform is not supported

        Example:
            >>> validator = PlatformFactory.get_click_validator()
            >>> result = validator.validate_click_target(element, 500, 300)
        """
        pass

    @staticmethod
    def get_input_simulator() -> PlatformInputSimulator:
        """
        Get platform-specific input simulator.

        Returns:
            PlatformInputSimulator: Platform-specific simulator

        Raises:
            NotImplementedError: If platform is not supported

        Example:
            >>> simulator = PlatformFactory.get_input_simulator()
            >>> simulator.click(1920, 1080)
        """
        pass

    @staticmethod
    def get_window_manager() -> PlatformWindowManager:
        """
        Get platform-specific window manager.

        Returns:
            PlatformWindowManager: Platform-specific window manager

        Raises:
            NotImplementedError: If platform is not supported

        Example:
            >>> wm = PlatformFactory.get_window_manager()
            >>> viewport = wm.get_viewport_metrics()
        """
        pass
```

---

## Base Classes

### PlatformCoordinateConverter (Abstract)

**Purpose**: Convert between different coordinate systems

**Location**: `src/mcp_server/platform/base/__init__.py`

```python
class PlatformCoordinateConverter(ABC):
    """
    Base class for platform-specific coordinate conversion.

    All coordinate systems are in physical screen pixels.
    DPI scaling is handled internally.
    """

    @abstractmethod
    def os_to_viewport(self, x: float, y: float) -> Tuple[float, float]:
        """
        Convert OS screen coordinates to browser viewport coordinates.

        Args:
            x: X coordinate in OS screen space (physical pixels)
            y: Y coordinate in OS screen space (physical pixels)

        Returns:
            Tuple[float, float]: (viewport_x, viewport_y) in CSS pixels

        Raises:
            CoordinateTransformError: If transformation fails

        Example:
            >>> converter = PlatformFactory.get_coordinate_converter()
            >>> # OS screen (1920, 1080) at 150% DPI
            >>> vp_x, vp_y = converter.os_to_viewport(1920, 1080)
            >>> print(vp_x, vp_y)  # Output: (1280.0, 720.0)
        """

    @abstractmethod
    def viewport_to_os(self, x: float, y: float) -> Tuple[float, float]:
        """
        Convert browser viewport coordinates to OS screen coordinates.

        Args:
            x: X coordinate in viewport (CSS pixels)
            y: Y coordinate in viewport (CSS pixels)

        Returns:
            Tuple[float, float]: (os_x, os_y) in physical pixels

        Raises:
            CoordinateTransformError: If transformation fails

        Example:
            >>> converter = PlatformFactory.get_coordinate_converter()
            >>> # Viewport (400, 300) at 150% DPI
            >>> os_x, os_y = converter.viewport_to_os(400, 300)
            >>> print(os_x, os_y)  # Output: (600.0, 450.0)
        """

    @abstractmethod
    def viewport_to_page(self, x: float, y: float) -> Tuple[float, float]:
        """
        Convert viewport coordinates to page coordinates (includes scroll).

        Args:
            x: X coordinate in viewport (CSS pixels)
            y: Y coordinate in viewport (CSS pixels)

        Returns:
            Tuple[float, float]: (page_x, page_y) in CSS pixels

        Example:
            >>> converter = PlatformFactory.get_coordinate_converter()
            >>> # Page is scrolled 100px down
            >>> page_x, page_y = converter.viewport_to_page(400, 300)
            >>> print(page_x, page_y)  # Output: (400.0, 400.0)
        """

    @abstractmethod
    def page_to_viewport(self, x: float, y: float) -> Tuple[float, float]:
        """
        Convert page coordinates to viewport coordinates.

        Args:
            x: X coordinate on page (CSS pixels)
            y: Y coordinate on page (CSS pixels)

        Returns:
            Tuple[float, float]: (viewport_x, viewport_y) in CSS pixels

        Example:
            >>> converter = PlatformFactory.get_coordinate_converter()
            >>> # Page element at (400, 400), page scrolled 100px down
            >>> vp_x, vp_y = converter.page_to_viewport(400, 400)
            >>> print(vp_x, vp_y)  # Output: (400.0, 300.0)
        """

    @abstractmethod
    def get_dpi_info(self) -> Dict[str, Any]:
        """
        Get DPI and scaling information for current display.

        Returns:
            Dict with keys:
            - 'dpi' (int): Dots per inch for primary monitor
            - 'scale_factor' (float): 1.0 at 96 DPI, 2.0 at 192 DPI
            - 'primary_monitor' (str): Name of primary monitor
            - 'monitors' (Dict): Per-monitor information
                {
                    'monitor_name': {
                        'dpi': int,
                        'scale_factor': float,
                        'resolution': (width, height),
                        'position': (x, y)
                    }
                }
            - 'display_server' (str): 'windows', 'x11', 'wayland', 'macos'

        Raises:
            DPIDetectionError: If DPI detection fails

        Example:
            >>> converter = PlatformFactory.get_coordinate_converter()
            >>> dpi_info = converter.get_dpi_info()
            >>> print(dpi_info['dpi'])  # 96, 120, 144, etc.
            >>> print(dpi_info['scale_factor'])  # 1.0, 1.25, 1.5, etc.
        """

    def enable_cache(self, enabled: bool) -> None:
        """
        Enable/disable DPI caching for performance.

        Args:
            enabled: True to cache, False to always query

        Example:
            >>> converter = PlatformFactory.get_coordinate_converter()
            >>> converter.enable_cache(True)  # Cache DPI info
            >>> dpi1 = converter.get_dpi_info()  # Queries OS
            >>> dpi2 = converter.get_dpi_info()  # Returns cached
        """

    def transform_batch(
        self,
        coords_list: List[Tuple[float, float]],
        from_system: str,
        to_system: str
    ) -> List[Tuple[float, float]]:
        """
        Transform multiple coordinates efficiently.

        Args:
            coords_list: List of (x, y) tuples
            from_system: 'os_screen', 'viewport', 'page', 'dom_element'
            to_system: 'os_screen', 'viewport', 'page', 'dom_element'

        Returns:
            List[Tuple[float, float]]: Transformed coordinates

        Example:
            >>> converter = PlatformFactory.get_coordinate_converter()
            >>> points = [(100, 100), (200, 200), (300, 300)]
            >>> converted = converter.transform_batch(
            ...     points,
            ...     from_system='os_screen',
            ...     to_system='viewport'
            ... )
        """
```

### PlatformClickValidator (Abstract)

```python
class PlatformClickValidator(ABC):
    """
    Base class for platform-specific click validation.

    Validates that an element can be clicked at given coordinates.
    """

    @abstractmethod
    def validate_click_target(
        self,
        element: Dict[str, Any],
        x: float,
        y: float
    ) -> Dict[str, Any]:
        """
        Validate that element is clickable at given coordinates.

        Args:
            element: Element information dict with:
                - 'tag_name': str (button, a, input, etc.)
                - 'bounding_box': {x, y, width, height}
                - 'is_visible': bool
                - 'is_enabled': bool
                - 'z_index': int
                - 'pointer_events': str ('auto', 'none', etc.)
            x: X coordinate for click (viewport pixels)
            y: Y coordinate for click (viewport pixels)

        Returns:
            Dict with keys:
            - 'valid' (bool): True if element is clickable
            - 'confidence' (float): 0.0-1.0 confidence level
            - 'reasons' (List[str]): Validation checks passed
            - 'warnings' (List[str]): Non-blocking issues
            - 'errors' (List[str]): Blocking issues

        Example:
            >>> validator = PlatformFactory.get_click_validator()
            >>> element = {
            ...     'tag_name': 'button',
            ...     'bounding_box': {'x': 100, 'y': 100, 'width': 100, 'height': 40},
            ...     'is_visible': True,
            ...     'is_enabled': True,
            ...     'z_index': 1,
            ...     'pointer_events': 'auto'
            ... }
            >>> result = validator.validate_click_target(element, 150, 120)
            >>> print(result['valid'])  # True
            >>> print(result['confidence'])  # 0.95
        """

    def validate_batch(
        self,
        elements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate multiple elements efficiently.

        Args:
            elements: List of element dicts

        Returns:
            List[Dict]: Validation results for each element
        """
```

### PlatformInputSimulator (Abstract)

```python
class PlatformInputSimulator(ABC):
    """
    Base class for platform-specific input simulation.

    Simulates mouse and keyboard input at OS level.
    """

    @abstractmethod
    def click(
        self,
        x: float,
        y: float,
        button: str = 'left',
        delay: float = 0.0
    ) -> bool:
        """
        Simulate mouse click at OS coordinates.

        Args:
            x: X coordinate in OS screen space (physical pixels)
            y: Y coordinate in OS screen space (physical pixels)
            button: 'left', 'right', 'middle'
            delay: Delay before click in seconds

        Returns:
            bool: True if click succeeded, False otherwise

        Raises:
            InputSimulationError: If simulation fails

        Example:
            >>> simulator = PlatformFactory.get_input_simulator()
            >>> simulator.click(1920, 1080, button='left')
            True
        """

    @abstractmethod
    def double_click(self, x: float, y: float, delay: float = 0.1) -> bool:
        """
        Simulate double-click at OS coordinates.

        Args:
            x: X coordinate in OS screen space
            y: Y coordinate in OS screen space
            delay: Delay between clicks in seconds

        Returns:
            bool: True if successful
        """

    @abstractmethod
    def type_text(self, text: str) -> bool:
        """
        Type text using keyboard simulation.

        Args:
            text: Text to type (supports Unicode)

        Returns:
            bool: True if successful

        Example:
            >>> simulator = PlatformFactory.get_input_simulator()
            >>> simulator.type_text("Hello, World!")
            True
        """

    @abstractmethod
    def press_key(self, key: str) -> bool:
        """
        Press a single key.

        Args:
            key: Key name ('Return', 'Tab', 'Escape', 'Delete', etc.)

        Returns:
            bool: True if successful
        """

    @abstractmethod
    def key_combination(self, *keys: str) -> bool:
        """
        Press multiple keys simultaneously.

        Args:
            keys: Key names to press together

        Returns:
            bool: True if successful

        Example:
            >>> simulator = PlatformFactory.get_input_simulator()
            >>> simulator.key_combination('Control', 'c')  # Ctrl+C
            True
        """

    @abstractmethod
    def move_mouse(self, x: float, y: float, duration: float = 0.5) -> bool:
        """
        Move mouse to position with optional animation.

        Args:
            x: Target X coordinate
            y: Target Y coordinate
            duration: Animation duration in seconds

        Returns:
            bool: True if successful
        """
```

---

## Platform Implementations

### Windows Implementation

**Location**: `src/mcp_server/windows/`

```python
# Import Windows-specific implementation
from mcp_server.windows import (
    WindowsCoordinateConverter,
    WindowsClickValidator,
    WindowsInputSimulator,
    WindowsWindowManager
)

# Or use factory
from mcp_server.platform import PlatformFactory

converter = PlatformFactory.get_coordinate_converter()
# Returns WindowsCoordinateConverter on Windows

# Windows-specific features
dpi_info = converter.get_dpi_info()
print(dpi_info['monitors'])  # Per-monitor DPI info
```

**Windows DPI Scaling Reference**:
```python
# Common Windows DPI values and scale factors
WINDOWS_DPI_SCALES = {
    96: 1.0,      # 100% (standard)
    120: 1.25,    # 125%
    144: 1.5,     # 150%
    168: 1.75,    # 175%
    192: 2.0,     # 200%
    240: 2.5,     # 250%
}

# DPI-aware API calls
GetDpiForMonitor(hmonitor, MDT_EFFECTIVE_DPI, &dpi)
SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
```

### Linux Implementation

**Location**: `src/mcp_server/platform/linux/`

```python
# Import Linux-specific implementation
from mcp_server.platform.linux import (
    LinuxCoordinateConverter,
    LinuxClickValidator,
    LinuxInputSimulator,
    LinuxWindowManager,
    LinuxDPIHandler
)

# Or use factory
from mcp_server.platform import PlatformFactory

converter = PlatformFactory.get_coordinate_converter()
# Returns LinuxCoordinateConverter on Linux

# Linux-specific DPI detection
dpi_info = converter.get_dpi_info()
print(dpi_info['display_server'])  # 'x11' or 'wayland'
print(dpi_info['monitors'])         # Per-monitor xrandr info
```

**Linux Display Server Detection**:
```python
# Automatic detection
from mcp_server.platform.linux import LinuxDPIHandler

handler = LinuxDPIHandler()
display_server = handler._detect_display_server()  # 'x11' or 'wayland'

# Manual override
import os
os.environ['XDG_SESSION_TYPE'] = 'x11'  # or 'wayland'
```

### macOS Implementation (Planned)

```python
# Future: macOS support via Quartz Display Services
from mcp_server.platform.macos import (
    MacOSCoordinateConverter,
    MacOSClickValidator,
    MacOSInputSimulator
)

# Planned features:
# - Retina display support (2x, 3x scaling)
# - Multi-monitor with different scales
# - Native macOS keyboard/mouse events
# - Accessibility API integration
```

---

## Code Examples

### Example 1: Basic Coordinate Transformation

```python
from mcp_server.platform import PlatformFactory

# Get platform-specific converter
converter = PlatformFactory.get_coordinate_converter()

# Transform OS screen coordinates to viewport
os_x, os_y = 1920, 1080
viewport_x, viewport_y = converter.os_to_viewport(os_x, os_y)

print(f"OS Screen: ({os_x}, {os_y})")
print(f"Viewport: ({viewport_x}, {viewport_y})")

# Platform-specific behavior:
# Windows @ 150% DPI:  (1920, 1080) → (1280, 720)
# Linux @ 96 DPI:      (1920, 1080) → (1920, 1080)
# macOS @ 2x scale:    (1920, 1080) → (960, 540)
```

### Example 2: DPI-Aware Scaling

```python
from mcp_server.platform import PlatformFactory

converter = PlatformFactory.get_coordinate_converter()

# Get DPI information
dpi_info = converter.get_dpi_info()

print(f"DPI: {dpi_info['dpi']}")
print(f"Scale Factor: {dpi_info['scale_factor']}")

# Get all monitors
for monitor_name, monitor_info in dpi_info['monitors'].items():
    print(f"\n{monitor_name}:")
    print(f"  DPI: {monitor_info['dpi']}")
    print(f"  Scale: {monitor_info['scale_factor']}")
    print(f"  Resolution: {monitor_info['resolution']}")
    print(f"  Position: {monitor_info['position']}")
```

### Example 3: Click Validation

```python
from mcp_server.platform import PlatformFactory

validator = PlatformFactory.get_click_validator()
converter = PlatformFactory.get_coordinate_converter()

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

# Validate at center of element
center_x = element['bounding_box']['x'] + element['bounding_box']['width'] / 2
center_y = element['bounding_box']['y'] + element['bounding_box']['height'] / 2

result = validator.validate_click_target(element, center_x, center_y)

if result['valid']:
    print(f"✓ Element is clickable (confidence: {result['confidence']:.1%})")
else:
    print(f"✗ Element cannot be clicked")
    for error in result['errors']:
        print(f"  - {error}")
```

### Example 4: Multi-Platform Input Simulation

```python
from mcp_server.platform import PlatformFactory

simulator = PlatformFactory.get_input_simulator()
converter = PlatformFactory.get_coordinate_converter()

# Convert viewport coordinates to OS coordinates
viewport_x, viewport_y = 400, 300
os_x, os_y = converter.viewport_to_os(viewport_x, viewport_y)

# Simulate click (platform-specific implementation)
simulator.click(os_x, os_y, button='left')

# Simulate keyboard input
simulator.type_text("Hello, World!")
simulator.press_key('Return')

# Simulate keyboard shortcut
simulator.key_combination('Control', 'a')  # Ctrl+A
simulator.key_combination('Control', 'c')  # Ctrl+C
```

### Example 5: Batch Transformation

```python
from mcp_server.platform import PlatformFactory

converter = PlatformFactory.get_coordinate_converter()

# Transform multiple coordinates at once
viewport_coords = [
    (100, 100),
    (200, 200),
    (300, 300),
    (400, 400),
    (500, 500)
]

# More efficient than individual transforms
os_coords = converter.transform_batch(
    viewport_coords,
    from_system='viewport',
    to_system='os_screen'
)

for vp, os in zip(viewport_coords, os_coords):
    print(f"Viewport {vp} → OS {os}")
```

### Example 6: Caching for Performance

```python
from mcp_server.platform import PlatformFactory

converter = PlatformFactory.get_coordinate_converter()

# Enable DPI caching (useful for repeated operations)
converter.enable_cache(True)

# First call queries OS
dpi_info_1 = converter.get_dpi_info()

# Subsequent calls use cached value (faster)
dpi_info_2 = converter.get_dpi_info()

# Disable cache when DPI might change (e.g., moving window)
converter.enable_cache(False)
```

---

## Error Handling

### Exception Hierarchy

```python
# Base exception
class PlatformError(Exception):
    """Base exception for platform-specific errors"""

# Coordinate transformation errors
class CoordinateTransformError(PlatformError):
    """Error during coordinate transformation"""

# DPI detection errors
class DPIDetectionError(PlatformError):
    """Error detecting DPI information"""

# Input simulation errors
class InputSimulationError(PlatformError):
    """Error simulating input"""

# Platform not supported
class PlatformNotSupportedError(PlatformError):
    """Platform is not supported"""
```

### Error Handling Examples

```python
from mcp_server.platform import PlatformFactory
from mcp_server.platform.errors import (
    CoordinateTransformError,
    DPIDetectionError,
    InputSimulationError
)

converter = PlatformFactory.get_coordinate_converter()

try:
    dpi_info = converter.get_dpi_info()
except DPIDetectionError as e:
    print(f"Failed to detect DPI: {e}")
    # Fallback to default DPI
    dpi_info = {'dpi': 96, 'scale_factor': 1.0}

try:
    vp_x, vp_y = converter.os_to_viewport(x, y)
except CoordinateTransformError as e:
    print(f"Coordinate transformation failed: {e}")

simulator = PlatformFactory.get_input_simulator()

try:
    simulator.click(x, y)
except InputSimulationError as e:
    print(f"Click simulation failed: {e}")
```

---

## Thread Safety

All platform components are **thread-safe singletons** that can be safely accessed from multiple threads concurrently.

### Thread-Safe Singleton Usage

```python
from mcp_server.platform import get_coordinate_converter, get_window_manager
import threading

# All threads share the same thread-safe singleton instance
def worker_thread(thread_id):
    # Safe to call from multiple threads - returns shared singleton
    converter = get_coordinate_converter()

    # All coordinate conversions are thread-safe
    vp_x, vp_y = converter.os_to_viewport(1920, 1080)
    print(f"Thread {thread_id}: viewport coords = ({vp_x}, {vp_y})")

    # Window manager is also a thread-safe singleton
    wm = get_window_manager()
    windows = wm.find_browser_windows()

# Start multiple threads - all share the same singleton instances
threads = [threading.Thread(target=worker_thread, args=(i,)) for i in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### Thread-Safety Guarantees

1. **Singleton Pattern**: Each component uses double-check locking for thread-safe initialization
2. **Cache Operations**: Monitor and display caches are protected by internal locks
3. **Concurrent Access**: All public methods are safe to call from multiple threads
4. **Resource Cleanup**: Automatic cleanup via destructors - no manual resource management needed
5. **Input Simulation**: Click/keyboard operations are atomic and thread-safe

### Implementation Details

- **CoordinateConverter**: Cache-aside pattern with `threading.Lock()` protecting cache reads/writes
- **WindowManager**: Thread-safe singleton with automatic X11/Wayland connection cleanup
- **DPIHandler**: Thread-safe DPI queries with per-monitor caching
- **InputSimulator**: Thread-safe input operations with retry logic

---

## Platform Detection

```python
import sys
from mcp_server.platform import PlatformFactory

# Detect current platform
if sys.platform == 'win32':
    print("Windows")
elif sys.platform.startswith('linux'):
    print("Linux")
elif sys.platform == 'darwin':
    print("macOS")

# Use factory for automatic detection
converter = PlatformFactory.get_coordinate_converter()
dpi_info = converter.get_dpi_info()
print(f"Display Server: {dpi_info.get('display_server', 'unknown')}")
```

---

**Version**: 1.0.0
**Last Updated**: 2025-11-17
