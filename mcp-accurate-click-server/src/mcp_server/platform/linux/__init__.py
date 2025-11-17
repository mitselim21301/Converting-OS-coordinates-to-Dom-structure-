"""
Linux platform implementation for MCP Accurate Click Server.

Provides Linux-specific implementations for:
- Input simulation (mouse/keyboard)
- DPI/scaling handling
- Window management
- Coordinate conversion

Supports both X11 and Wayland display servers.
"""

from mcp_server.platform.linux.input_simulator import (
    LinuxInputSimulator,
    get_input_simulator,
)
from mcp_server.platform.linux.dpi_handler import (
    LinuxDPIHandler,
    create_dpi_handler,
    DisplayServer,
)
from mcp_server.platform.linux.coordinate_converter import (
    LinuxCoordinateConverter,
    get_converter,
)
from mcp_server.platform.linux.window_manager import (
    LinuxWindowManager,
    get_window_manager,
)

__all__ = [
    'LinuxInputSimulator',
    'get_input_simulator',
    'LinuxDPIHandler',
    'create_dpi_handler',
    'DisplayServer',
    'LinuxCoordinateConverter',
    'get_converter',
    'LinuxWindowManager',
    'get_window_manager',
]
