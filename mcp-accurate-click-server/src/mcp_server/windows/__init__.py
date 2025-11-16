"""
Windows Integration Module for MCP Accurate Click Server

Provides Windows-specific functionality for accurate mouse clicking:
- Coordinate conversion (OS -> DOM)
- DPI awareness and scaling
- Browser window tracking
- Mouse input simulation

Usage:
    from mcp_server.windows import (
        get_converter,
        get_dpi_handler,
        get_window_manager,
        get_input_simulator
    )

    # Convert coordinates
    converter = get_converter()
    dom_coords = converter.physical_to_dom_full_chain(
        physical_x=1000,
        physical_y=500,
        dpi=144,
        device_pixel_ratio=1.5,
        browser_zoom=1.0,
        viewport_offset_x=8,
        viewport_offset_y=130,
        scroll_x=0,
        scroll_y=100
    )

    # Check DPI
    dpi_handler = get_dpi_handler()
    monitors = dpi_handler.enumerate_monitors()
    for monitor in monitors:
        print(f"Monitor DPI: {monitor.dpi_x} ({monitor.scale_percentage}%)")

    # Find browser windows
    window_manager = get_window_manager()
    browsers = window_manager.find_browser_windows()
    for browser in browsers:
        print(f"Browser: {browser.title}")

    # Click at coordinates
    simulator = get_input_simulator()
    simulator.click(x=1000, y=500)
"""

import platform
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Check if running on Windows
if platform.system() != 'Windows':
    logger.warning(
        "Windows integration module imported on non-Windows platform. "
        "Functionality will be limited."
    )

# Import main classes and factory functions
from .coordinate_converter import (
    CoordinateConverter,
    Point,
    Rectangle,
    get_converter
)

from .dpi_handler import (
    DpiHandler,
    MonitorInfo,
    MonitorDpiType,
    DpiAwarenessContext,
    get_dpi_handler
)

from .window_manager import (
    WindowManager,
    WindowInfo,
    get_window_manager
)

from .input_simulator import (
    InputSimulator,
    MouseButton,
    KeyModifier,
    get_input_simulator
)


__all__ = [
    # Coordinate conversion
    'CoordinateConverter',
    'Point',
    'Rectangle',
    'get_converter',

    # DPI handling
    'DpiHandler',
    'MonitorInfo',
    'MonitorDpiType',
    'DpiAwarenessContext',
    'get_dpi_handler',

    # Window management
    'WindowManager',
    'WindowInfo',
    'get_window_manager',

    # Input simulation
    'InputSimulator',
    'MouseButton',
    'KeyModifier',
    'get_input_simulator',

    # High-level functions
    'click_dom_element',
    'get_system_info',
]


def click_dom_element(
    dom_x: int,
    dom_y: int,
    hwnd: int,
    device_pixel_ratio: float = 1.0,
    browser_zoom: float = 1.0,
    viewport_offset_x: int = 0,
    viewport_offset_y: int = 0,
    scroll_x: int = 0,
    scroll_y: int = 0,
    button: MouseButton = MouseButton.LEFT,
    clicks: int = 1
) -> bool:
    """
    High-level function to click a DOM element.

    Converts DOM coordinates to physical screen coordinates and performs click.

    Args:
        dom_x: X coordinate in DOM document
        dom_y: Y coordinate in DOM document
        hwnd: Browser window handle
        device_pixel_ratio: Browser's window.devicePixelRatio
        browser_zoom: Browser zoom level (1.0 = 100%)
        viewport_offset_x: Browser chrome left offset
        viewport_offset_y: Browser chrome top offset
        scroll_x: Horizontal scroll position
        scroll_y: Vertical scroll position
        button: Mouse button to click
        clicks: Number of clicks

    Returns:
        True if click successful
    """
    try:
        # Get instances
        converter = get_converter()
        dpi_handler = get_dpi_handler()
        window_manager = get_window_manager()
        simulator = get_input_simulator()

        # Get window info
        window_info = window_manager.get_window_info(hwnd)
        if not window_info:
            logger.error(f"Invalid window handle: {hwnd}")
            return False

        # Get DPI for window
        dpi_x, dpi_y = dpi_handler.get_dpi_for_window(hwnd)

        # Convert DOM -> CSS
        css_point = converter.dom_to_css(
            dom_x, dom_y,
            viewport_offset_x, viewport_offset_y,
            scroll_x, scroll_y
        )

        # Convert CSS -> Physical
        physical_point = converter.css_to_physical(
            css_point.x, css_point.y,
            device_pixel_ratio, browser_zoom
        )

        # Add window client offset
        screen_x = window_info.client_rect[0] + physical_point.x
        screen_y = window_info.client_rect[1] + physical_point.y

        logger.info(
            f"Clicking DOM ({dom_x}, {dom_y}) -> "
            f"CSS ({css_point.x}, {css_point.y}) -> "
            f"Physical ({physical_point.x}, {physical_point.y}) -> "
            f"Screen ({screen_x}, {screen_y})"
        )

        # Perform click
        return simulator.click(screen_x, screen_y, button, clicks)

    except Exception as e:
        logger.error(f"Failed to click DOM element: {e}")
        return False


def get_system_info() -> dict:
    """
    Get comprehensive system information for debugging.

    Returns:
        Dictionary with system, DPI, monitor, and window information
    """
    try:
        dpi_handler = get_dpi_handler()
        window_manager = get_window_manager()
        converter = get_converter()

        # Get DPI info
        dpi_info = dpi_handler.get_dpi_summary()

        # Get monitor info
        monitors = dpi_handler.enumerate_monitors()

        # Get browser windows
        browsers = window_manager.find_browser_windows()

        # Get virtual screen
        virtual_screen = converter.get_virtual_screen_bounds()

        # Get cursor position
        cursor = converter.get_physical_cursor_pos()

        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "dpi": dpi_info,
            "virtual_screen": {
                "left": virtual_screen.left,
                "top": virtual_screen.top,
                "right": virtual_screen.right,
                "bottom": virtual_screen.bottom,
                "width": virtual_screen.width,
                "height": virtual_screen.height
            },
            "cursor_position": {
                "x": cursor.x,
                "y": cursor.y
            },
            "browser_windows": [
                {
                    "title": browser.title,
                    "hwnd": browser.hwnd,
                    "browser_type": window_manager.get_browser_type(browser.hwnd),
                    "bounds": {
                        "window": {
                            "left": browser.window_rect[0],
                            "top": browser.window_rect[1],
                            "width": browser.window_width,
                            "height": browser.window_height
                        },
                        "client": {
                            "left": browser.client_rect[0],
                            "top": browser.client_rect[1],
                            "width": browser.client_width,
                            "height": browser.client_height
                        },
                        "chrome_offsets": {
                            "x": browser.chrome_offset_x,
                            "y": browser.chrome_offset_y
                        }
                    }
                }
                for browser in browsers[:5]  # Limit to 5 windows
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        return {
            "error": str(e),
            "platform": platform.system()
        }


# Version info
__version__ = '1.0.0'
__author__ = 'MCP Team'
__description__ = 'Windows integration for accurate mouse clicking with DPI support'
