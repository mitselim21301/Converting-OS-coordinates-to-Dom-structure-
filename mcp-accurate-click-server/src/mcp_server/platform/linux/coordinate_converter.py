"""
Linux Coordinate Converter - OS to DOM Coordinate Conversion

Handles conversion between:
- Physical screen pixels (OS coordinates)
- Logical pixels (DPI-aware coordinates)
- CSS pixels (browser viewport)
- DOM coordinates (element-relative)

Supports multi-monitor setups with mixed DPI environments on both X11 and Wayland.
Handles negative coordinates for monitors positioned left/above primary display.
"""

import os
import subprocess
import logging
import threading
from typing import Tuple, Optional, Dict, List, Any
from dataclasses import dataclass
import re

from mcp_server.platform.base import (
    PlatformCoordinateConverter,
    Point,
    Rectangle,
    MonitorInfo
)

# Import edge case handler
try:
    from .edge_case_handler import get_edge_case_handler
    EDGE_CASE_HANDLER_AVAILABLE = True
except ImportError:
    EDGE_CASE_HANDLER_AVAILABLE = False

logger = logging.getLogger(__name__)


class LinuxCoordinateConverter(PlatformCoordinateConverter):
    """
    Converts coordinates between different coordinate spaces on Linux.

    Coordinate Spaces:
    - Physical: Raw hardware pixels from the OS
    - Logical: DPI-scaled coordinates (system DPI aware)
    - CSS: Browser viewport pixels (device pixel ratio applied)
    - DOM: Element-relative coordinates

    Supports:
    - X11 (using xrandr/xdotool)
    - Wayland (using wlr-randr or swaymsg where available)
    - Multi-monitor with mixed DPI
    - Negative coordinate spaces
    - Virtual screen boundaries
    """

    def __init__(self, dpi_handler=None):
        """
        Initialize coordinate converter with Linux display system detection.

        Args:
            dpi_handler: Optional PlatformDPIHandler instance for DPI queries
        """
        self.dpi_handler = dpi_handler
        self.display_server = self._detect_display_server()

        # Cache virtual screen dimensions (updated when needed)
        self._virtual_screen_cache: Optional[Rectangle] = None
        self._monitors_cache: List[MonitorInfo] = []
        self._cache_valid = False
        self._edge_case_detection = None

        # Check for edge cases
        if EDGE_CASE_HANDLER_AVAILABLE:
            try:
                edge_handler = get_edge_case_handler()
                self._edge_case_detection = edge_handler.detect_edge_cases()

                if self._edge_case_detection.is_headless:
                    logger.warning("Coordinate Converter: Headless environment - monitor detection may fail")

                if self._edge_case_detection.multiple_x_servers:
                    logger.warning("Coordinate Converter: Multiple X servers detected - ensure correct DISPLAY variable")

                if self._edge_case_detection.remote_access_type.value != 'direct':
                    logger.info(f"Coordinate Converter: Remote access ({self._edge_case_detection.remote_access_type.value})")

            except Exception as e:
                logger.debug(f"Edge case detection failed: {e}")

        logger.info(f"Linux Coordinate Converter initialized for {self.display_server}")

    def _detect_display_server(self) -> str:
        """
        Detect which display server is running (X11 or Wayland).

        Returns:
            'x11' or 'wayland'
        """
        # Check environment variables
        wayland_display = os.environ.get('WAYLAND_DISPLAY')
        xdg_session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()

        if wayland_display or xdg_session_type == 'wayland':
            # Verify wayland tools are available
            if self._command_exists('wlr-randr') or self._command_exists('swaymsg'):
                return 'wayland'

        # Check for X11
        x_display = os.environ.get('DISPLAY')
        if x_display and self._command_exists('xrandr'):
            return 'x11'

        # Default to X11 as it's more common
        logger.warning("Could not definitively detect display server, defaulting to X11")
        return 'x11'

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        try:
            result = subprocess.run(
                ['which', command],
                capture_output=True,
                timeout=1
            )
            return result.returncode == 0
        except Exception:
            return False

    def _parse_xrandr_output(self, refresh: bool = False) -> List[MonitorInfo]:
        """
        Parse xrandr output to get monitor information.

        Args:
            refresh: Force refresh of monitor data

        Returns:
            List of MonitorInfo objects
        """
        if not refresh and self._cache_valid and self._monitors_cache:
            return self._monitors_cache

        monitors = []

        try:
            result = subprocess.run(
                ['xrandr', '--current'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                logger.error(f"xrandr failed: {result.stderr}")
                return monitors

            current_monitor_name = None
            primary_found = False

            for line in result.stdout.split('\n'):
                # Match connected monitor line
                # Example: "DP-1 connected primary 2560x1440+1920+0 (normal left inverted right x axis y axis) 597mm x 336mm"
                monitor_match = re.match(
                    r'^(\S+)\s+connected\s+(primary\s+)?(\d+)x(\d+)\+(\d+)\+(\d+)',
                    line
                )

                if monitor_match:
                    name = monitor_match.group(1)
                    is_primary = monitor_match.group(2) is not None
                    width = int(monitor_match.group(3))
                    height = int(monitor_match.group(4))
                    x_offset = int(monitor_match.group(5))
                    y_offset = int(monitor_match.group(6))

                    current_monitor_name = name

                    # Get DPI from DPI handler if available
                    if self.dpi_handler:
                        try:
                            # Get DPI at center of monitor
                            center_x = x_offset + width // 2
                            center_y = y_offset + height // 2
                            dpi_x, dpi_y = self.dpi_handler.get_dpi_at_point(center_x, center_y)
                        except Exception as e:
                            logger.debug(f"Could not get DPI for {name}: {e}")
                            dpi_x = dpi_y = 96
                    else:
                        dpi_x = dpi_y = 96

                    monitor_info = MonitorInfo(
                        handle=name,
                        left=x_offset,
                        top=y_offset,
                        right=x_offset + width,
                        bottom=y_offset + height,
                        dpi_x=dpi_x,
                        dpi_y=dpi_y,
                        is_primary=is_primary,
                        scale_factor=dpi_x / 96.0,
                        name=name
                    )

                    monitors.append(monitor_info)

                    if is_primary:
                        primary_found = True

                    logger.debug(
                        f"Monitor {name}: {width}x{height} @ ({x_offset}, {y_offset}), "
                        f"DPI: {dpi_x}x{dpi_y}, Primary: {is_primary}"
                    )

            # If no primary found, mark first monitor as primary
            if monitors and not primary_found:
                monitors[0] = MonitorInfo(
                    handle=monitors[0].handle,
                    left=monitors[0].left,
                    top=monitors[0].top,
                    right=monitors[0].right,
                    bottom=monitors[0].bottom,
                    dpi_x=monitors[0].dpi_x,
                    dpi_y=monitors[0].dpi_y,
                    is_primary=True,
                    scale_factor=monitors[0].scale_factor,
                    name=monitors[0].name
                )
                logger.debug(f"No primary found, using {monitors[0].name} as primary")

            self._monitors_cache = monitors
            self._cache_valid = True

        except subprocess.TimeoutExpired:
            logger.error("xrandr command timed out")
        except Exception as e:
            logger.error(f"Failed to parse xrandr output: {e}")

        return monitors

    def _parse_wayland_monitors(self, refresh: bool = False) -> List[MonitorInfo]:
        """
        Parse Wayland compositor output to get monitor information.

        Tries wlr-randr first, then swaymsg as fallback.

        Args:
            refresh: Force refresh of monitor data

        Returns:
            List of MonitorInfo objects
        """
        if not refresh and self._cache_valid and self._monitors_cache:
            return self._monitors_cache

        monitors = []

        # Try wlr-randr first (works with wlroots-based compositors)
        if self._command_exists('wlr-randr'):
            monitors = self._parse_wlr_randr()

        # Fallback to swaymsg for Sway
        if not monitors and self._command_exists('swaymsg'):
            monitors = self._parse_swaymsg()

        # If we still don't have monitors, log error but don't crash
        if not monitors:
            logger.error("Could not detect Wayland monitors, using fallback")
            # Create a default monitor
            monitors = [MonitorInfo(
                handle="default",
                left=0,
                top=0,
                right=1920,
                bottom=1080,
                dpi_x=96,
                dpi_y=96,
                is_primary=True,
                scale_factor=1.0,
                name="default"
            )]

        self._monitors_cache = monitors
        self._cache_valid = True
        return monitors

    def _parse_wlr_randr(self) -> List[MonitorInfo]:
        """Parse wlr-randr output for monitor information."""
        monitors = []

        try:
            result = subprocess.run(
                ['wlr-randr'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return monitors

            current_monitor = {}
            monitor_count = 0

            for line in result.stdout.split('\n'):
                line = line.strip()

                # New monitor section
                if line and not line.startswith(' '):
                    if current_monitor:
                        monitors.append(self._create_monitor_from_dict(
                            current_monitor,
                            len(monitors) == 0
                        ))
                    current_monitor = {'name': line.split()[0]}
                    monitor_count += 1

                # Parse position and resolution
                elif 'current' in line.lower():
                    # Example: "  1920x1080 px, 60.000000 Hz (preferred, current)"
                    match = re.search(r'(\d+)x(\d+)\s+px', line)
                    if match:
                        current_monitor['width'] = int(match.group(1))
                        current_monitor['height'] = int(match.group(2))

                elif 'Position:' in line:
                    # Example: "  Position: 0,0"
                    match = re.search(r'Position:\s*(-?\d+),(-?\d+)', line)
                    if match:
                        current_monitor['x'] = int(match.group(1))
                        current_monitor['y'] = int(match.group(2))

                elif 'Scale:' in line:
                    # Example: "  Scale: 1.500000"
                    match = re.search(r'Scale:\s*([\d.]+)', line)
                    if match:
                        current_monitor['scale'] = float(match.group(1))

            # Add last monitor
            if current_monitor:
                monitors.append(self._create_monitor_from_dict(
                    current_monitor,
                    len(monitors) == 0
                ))

        except Exception as e:
            logger.error(f"Failed to parse wlr-randr: {e}")

        return monitors

    def _parse_swaymsg(self) -> List[MonitorInfo]:
        """Parse swaymsg output for monitor information."""
        monitors = []

        try:
            result = subprocess.run(
                ['swaymsg', '-t', 'get_outputs', '-r'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return monitors

            import json
            outputs = json.loads(result.stdout)

            for output in outputs:
                if not output.get('active', False):
                    continue

                rect = output.get('rect', {})
                scale = output.get('scale', 1.0)

                # Calculate DPI based on scale (approximate)
                dpi = int(96 * scale)

                monitor_info = MonitorInfo(
                    handle=output.get('name', 'unknown'),
                    left=rect.get('x', 0),
                    top=rect.get('y', 0),
                    right=rect.get('x', 0) + rect.get('width', 1920),
                    bottom=rect.get('y', 0) + rect.get('height', 1080),
                    dpi_x=dpi,
                    dpi_y=dpi,
                    is_primary=output.get('focused', False) or len(monitors) == 0,
                    scale_factor=scale,
                    name=output.get('name', 'unknown')
                )

                monitors.append(monitor_info)

                logger.debug(
                    f"Wayland Monitor {monitor_info.name}: "
                    f"{monitor_info.width}x{monitor_info.height} @ "
                    f"({monitor_info.left}, {monitor_info.top}), "
                    f"Scale: {scale}, DPI: {dpi}"
                )

        except Exception as e:
            logger.error(f"Failed to parse swaymsg: {e}")

        return monitors

    def _create_monitor_from_dict(self, data: Dict, is_primary: bool) -> MonitorInfo:
        """Create MonitorInfo from parsed dictionary data."""
        x = data.get('x', 0)
        y = data.get('y', 0)
        width = data.get('width', 1920)
        height = data.get('height', 1080)
        scale = data.get('scale', 1.0)
        dpi = int(96 * scale)

        return MonitorInfo(
            handle=data.get('name', 'unknown'),
            left=x,
            top=y,
            right=x + width,
            bottom=y + height,
            dpi_x=dpi,
            dpi_y=dpi,
            is_primary=is_primary,
            scale_factor=scale,
            name=data.get('name', 'unknown')
        )

    def get_virtual_screen_bounds(self, refresh: bool = False) -> Rectangle:
        """
        Get the virtual screen bounding rectangle.

        The virtual screen encompasses all monitors. It may include negative
        coordinates if monitors are positioned to the left or above the primary.

        Args:
            refresh: Force refresh of cached bounds

        Returns:
            Rectangle containing virtual screen bounds in physical pixels
        """
        if not refresh and self._virtual_screen_cache:
            return self._virtual_screen_cache

        # Get all monitors
        if self.display_server == 'x11':
            monitors = self._parse_xrandr_output(refresh)
        else:
            monitors = self._parse_wayland_monitors(refresh)

        if not monitors:
            # Fallback to reasonable default
            logger.warning("No monitors detected, using fallback bounds")
            self._virtual_screen_cache = Rectangle(0, 0, 1920, 1080, "physical")
            return self._virtual_screen_cache

        # Calculate bounding box of all monitors
        min_x = min(m.left for m in monitors)
        min_y = min(m.top for m in monitors)
        max_x = max(m.right for m in monitors)
        max_y = max(m.bottom for m in monitors)

        self._virtual_screen_cache = Rectangle(
            left=min_x,
            top=min_y,
            right=max_x,
            bottom=max_y,
            coordinate_space="physical"
        )

        logger.debug(
            f"Virtual screen: ({min_x}, {min_y}) to ({max_x}, {max_y}), "
            f"size: {max_x - min_x}x{max_y - min_y}"
        )

        return self._virtual_screen_cache

    def get_monitor_count(self) -> int:
        """Get the number of display monitors."""
        if self.display_server == 'x11':
            monitors = self._parse_xrandr_output()
        else:
            monitors = self._parse_wayland_monitors()

        return len(monitors)

    def get_physical_cursor_pos(self) -> Point:
        """
        Get current cursor position in physical screen coordinates.

        Returns:
            Point with physical screen coordinates
        """
        try:
            if self.display_server == 'x11':
                # Use xdotool to get cursor position
                if self._command_exists('xdotool'):
                    result = subprocess.run(
                        ['xdotool', 'getmouselocation', '--shell'],
                        capture_output=True,
                        text=True,
                        timeout=1
                    )

                    if result.returncode == 0:
                        x, y = 0, 0
                        for line in result.stdout.split('\n'):
                            if line.startswith('X='):
                                x = int(line.split('=')[1])
                            elif line.startswith('Y='):
                                y = int(line.split('=')[1])
                        return Point(x, y, "physical")
            else:
                # Wayland: cursor position is compositor-specific
                # Try swaymsg for Sway
                if self._command_exists('swaymsg'):
                    result = subprocess.run(
                        ['swaymsg', '-t', 'get_seats', '-r'],
                        capture_output=True,
                        text=True,
                        timeout=1
                    )

                    if result.returncode == 0:
                        import json
                        seats = json.loads(result.stdout)
                        for seat in seats:
                            pointer = seat.get('pointer', {})
                            x = pointer.get('x', 0)
                            y = pointer.get('y', 0)
                            if x or y:
                                return Point(int(x), int(y), "physical")

        except Exception as e:
            logger.error(f"Failed to get cursor position: {e}")

        return Point(0, 0, "physical")

    def physical_to_logical(
        self,
        physical_x: int,
        physical_y: int,
        dpi: int = 96
    ) -> Point:
        """
        Convert physical pixels to logical pixels.

        Formula: logical = physical * (96 / DPI)

        Args:
            physical_x: X coordinate in physical pixels
            physical_y: Y coordinate in physical pixels
            dpi: DPI value (default 96 = 100% scaling)

        Returns:
            Point with logical coordinates
        """
        if dpi == 96:
            return Point(physical_x, physical_y, "logical")

        logical_x = int(physical_x * 96 / dpi)
        logical_y = int(physical_y * 96 / dpi)

        return Point(logical_x, logical_y, "logical")

    def logical_to_physical(
        self,
        logical_x: int,
        logical_y: int,
        dpi: int = 96
    ) -> Point:
        """
        Convert logical pixels to physical pixels.

        Formula: physical = logical * (DPI / 96)

        Args:
            logical_x: X coordinate in logical pixels
            logical_y: Y coordinate in logical pixels
            dpi: DPI value (default 96 = 100% scaling)

        Returns:
            Point with physical coordinates
        """
        if dpi == 96:
            return Point(logical_x, logical_y, "physical")

        physical_x = int(logical_x * dpi / 96)
        physical_y = int(logical_y * dpi / 96)

        return Point(physical_x, physical_y, "physical")

    def physical_to_css(
        self,
        physical_x: int,
        physical_y: int,
        device_pixel_ratio: float = 1.0,
        browser_zoom: float = 1.0
    ) -> Point:
        """
        Convert physical screen pixels to CSS pixels.

        CSS pixels = physical pixels / (device_pixel_ratio * browser_zoom)

        Args:
            physical_x: X coordinate in physical pixels
            physical_y: Y coordinate in physical pixels
            device_pixel_ratio: Browser's window.devicePixelRatio
            browser_zoom: Browser zoom level (1.0 = 100%)

        Returns:
            Point with CSS pixel coordinates
        """
        scale_factor = device_pixel_ratio * browser_zoom

        if scale_factor == 1.0:
            return Point(physical_x, physical_y, "css")

        css_x = int(physical_x / scale_factor)
        css_y = int(physical_y / scale_factor)

        return Point(css_x, css_y, "css")

    def css_to_physical(
        self,
        css_x: int,
        css_y: int,
        device_pixel_ratio: float = 1.0,
        browser_zoom: float = 1.0
    ) -> Point:
        """
        Convert CSS pixels to physical screen pixels.

        Physical pixels = CSS pixels * (device_pixel_ratio * browser_zoom)

        Args:
            css_x: X coordinate in CSS pixels
            css_y: Y coordinate in CSS pixels
            device_pixel_ratio: Browser's window.devicePixelRatio
            browser_zoom: Browser zoom level (1.0 = 100%)

        Returns:
            Point with physical pixel coordinates
        """
        scale_factor = device_pixel_ratio * browser_zoom

        if scale_factor == 1.0:
            return Point(css_x, css_y, "physical")

        physical_x = int(css_x * scale_factor)
        physical_y = int(css_y * scale_factor)

        return Point(physical_x, physical_y, "physical")

    def css_to_dom(
        self,
        css_x: int,
        css_y: int,
        viewport_offset_x: int = 0,
        viewport_offset_y: int = 0,
        scroll_x: int = 0,
        scroll_y: int = 0
    ) -> Point:
        """
        Convert CSS viewport coordinates to DOM document coordinates.

        DOM = CSS + scroll - viewport_offset

        Args:
            css_x: X coordinate in CSS viewport pixels
            css_y: Y coordinate in CSS viewport pixels
            viewport_offset_x: Browser chrome left offset
            viewport_offset_y: Browser chrome top offset (address bar, etc.)
            scroll_x: Horizontal scroll position
            scroll_y: Vertical scroll position

        Returns:
            Point with DOM document coordinates
        """
        dom_x = css_x - viewport_offset_x + scroll_x
        dom_y = css_y - viewport_offset_y + scroll_y

        return Point(dom_x, dom_y, "dom")

    def dom_to_css(
        self,
        dom_x: int,
        dom_y: int,
        viewport_offset_x: int = 0,
        viewport_offset_y: int = 0,
        scroll_x: int = 0,
        scroll_y: int = 0
    ) -> Point:
        """
        Convert DOM document coordinates to CSS viewport coordinates.

        CSS = DOM - scroll + viewport_offset

        Args:
            dom_x: X coordinate in DOM document pixels
            dom_y: Y coordinate in DOM document pixels
            viewport_offset_x: Browser chrome left offset
            viewport_offset_y: Browser chrome top offset
            scroll_x: Horizontal scroll position
            scroll_y: Vertical scroll position

        Returns:
            Point with CSS viewport coordinates
        """
        css_x = dom_x + viewport_offset_x - scroll_x
        css_y = dom_y + viewport_offset_y - scroll_y

        return Point(css_x, css_y, "css")

    def physical_to_dom_full_chain(
        self,
        physical_x: int,
        physical_y: int,
        dpi: int = 96,
        device_pixel_ratio: float = 1.0,
        browser_zoom: float = 1.0,
        viewport_offset_x: int = 0,
        viewport_offset_y: int = 0,
        scroll_x: int = 0,
        scroll_y: int = 0
    ) -> Dict[str, Point]:
        """
        Convert physical coordinates through the full transformation chain.

        Returns all intermediate coordinate spaces for debugging.

        Args:
            physical_x: X coordinate in physical pixels
            physical_y: Y coordinate in physical pixels
            dpi: Monitor DPI
            device_pixel_ratio: Browser's window.devicePixelRatio
            browser_zoom: Browser zoom level
            viewport_offset_x: Browser chrome left offset
            viewport_offset_y: Browser chrome top offset
            scroll_x: Horizontal scroll position
            scroll_y: Vertical scroll position

        Returns:
            Dictionary with points in each coordinate space
        """
        # Physical -> Logical
        logical = self.physical_to_logical(physical_x, physical_y, dpi)

        # Physical -> CSS (skip logical for browser)
        css = self.physical_to_css(
            physical_x, physical_y,
            device_pixel_ratio, browser_zoom
        )

        # CSS -> DOM
        dom = self.css_to_dom(
            css.x, css.y,
            viewport_offset_x, viewport_offset_y,
            scroll_x, scroll_y
        )

        return {
            "physical": Point(physical_x, physical_y, "physical"),
            "logical": logical,
            "css": css,
            "dom": dom
        }

    def validate_coordinate(
        self,
        x: int,
        y: int,
        coordinate_space: str = "physical"
    ) -> bool:
        """
        Validate that coordinates are within reasonable bounds.

        Args:
            x: X coordinate
            y: Y coordinate
            coordinate_space: The coordinate space (physical, logical, css, dom)

        Returns:
            True if coordinates are valid
        """
        if coordinate_space == "physical":
            virtual_screen = self.get_virtual_screen_bounds()
            return virtual_screen.contains_point(x, y)

        # For other coordinate spaces, allow wider range
        # (negative values common in DOM, CSS, and multi-monitor setups)
        return -50000 <= x <= 50000 and -50000 <= y <= 50000

    def get_monitor_at_point(self, x: int, y: int) -> Optional[MonitorInfo]:
        """
        Get monitor information for the monitor containing a point.

        Args:
            x: X coordinate in physical screen pixels
            y: Y coordinate in physical screen pixels

        Returns:
            MonitorInfo object or None if not found
        """
        if self.display_server == 'x11':
            monitors = self._parse_xrandr_output()
        else:
            monitors = self._parse_wayland_monitors()

        for monitor in monitors:
            if (monitor.left <= x < monitor.right and
                monitor.top <= y < monitor.bottom):
                return monitor

        # If point is outside all monitors, return closest monitor
        if monitors:
            # Find monitor with minimum distance to point
            def distance_to_monitor(m: MonitorInfo) -> float:
                # Calculate distance from point to monitor rectangle
                # Distance is 0 if point is inside the rectangle bounds
                dx = 0
                if x < m.left:
                    dx = m.left - x
                elif x > m.right:
                    dx = x - m.right

                dy = 0
                if y < m.top:
                    dy = m.top - y
                elif y > m.bottom:
                    dy = y - m.bottom

                return (dx * dx + dy * dy) ** 0.5

            return min(monitors, key=distance_to_monitor)

        return None

    def translate_coordinate_between_monitors(
        self,
        x: int,
        y: int,
        from_monitor: MonitorInfo,
        to_monitor: MonitorInfo
    ) -> Point:
        """
        Translate coordinates from one monitor to another with different DPI.

        This handles the case where monitors have different scaling factors.

        Args:
            x: X coordinate on source monitor
            y: Y coordinate on source monitor
            from_monitor: Source monitor info
            to_monitor: Destination monitor info

        Returns:
            Point with coordinates adjusted for destination monitor
        """
        # If same DPI, no translation needed
        if from_monitor.dpi_x == to_monitor.dpi_x:
            return Point(x, y, "physical")

        # Convert to logical coordinates using source monitor DPI
        logical_x = int((x - from_monitor.left) * 96 / from_monitor.dpi_x)
        logical_y = int((y - from_monitor.top) * 96 / from_monitor.dpi_y)

        # Convert back to physical using destination monitor DPI
        physical_x = int(logical_x * to_monitor.dpi_x / 96) + to_monitor.left
        physical_y = int(logical_y * to_monitor.dpi_y / 96) + to_monitor.top

        return Point(physical_x, physical_y, "physical")

    def get_dpi_at_point(self, x: int, y: int) -> Tuple[int, int]:
        """
        Get DPI for the monitor containing a specific point.

        Args:
            x: X coordinate in screen pixels
            y: Y coordinate in screen pixels

        Returns:
            Tuple of (dpi_x, dpi_y)
        """
        if self.dpi_handler:
            try:
                return self.dpi_handler.get_dpi_at_point(x, y)
            except Exception as e:
                logger.debug(f"DPI handler failed, using monitor detection: {e}")

        # Fallback: get from monitor info
        monitor = self.get_monitor_at_point(x, y)
        if monitor:
            return (monitor.dpi_x, monitor.dpi_y)

        return (96, 96)

    def refresh_display_configuration(self) -> None:
        """
        Refresh display configuration cache.

        Call this when monitors are added/removed or configuration changes.
        """
        self._cache_valid = False
        self._virtual_screen_cache = None
        self._monitors_cache = []

        # Force re-detection
        self.get_virtual_screen_bounds(refresh=True)

        logger.info("Display configuration refreshed")

    def get_display_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive display information for debugging.

        Returns:
            Dictionary with display configuration information
        """
        if self.display_server == 'x11':
            monitors = self._parse_xrandr_output()
        else:
            monitors = self._parse_wayland_monitors()

        virtual_screen = self.get_virtual_screen_bounds()
        cursor_pos = self.get_physical_cursor_pos()

        return {
            "display_server": self.display_server,
            "monitor_count": len(monitors),
            "virtual_screen": {
                "left": virtual_screen.left,
                "top": virtual_screen.top,
                "right": virtual_screen.right,
                "bottom": virtual_screen.bottom,
                "width": virtual_screen.width,
                "height": virtual_screen.height
            },
            "cursor_position": {
                "x": cursor_pos.x,
                "y": cursor_pos.y
            },
            "monitors": [
                {
                    "name": m.name,
                    "bounds": f"{m.width}x{m.height} @ ({m.left}, {m.top})",
                    "dpi": f"{m.dpi_x}x{m.dpi_y}",
                    "scale": f"{m.scale_factor:.2f}x ({m.scale_percentage}%)",
                    "primary": m.is_primary
                }
                for m in monitors
            ]
        }


# Singleton instance
_converter: Optional[LinuxCoordinateConverter] = None
_converter_lock = threading.Lock()


def get_converter(dpi_handler=None) -> LinuxCoordinateConverter:
    """
    Get or create singleton LinuxCoordinateConverter instance (thread-safe).

    Args:
        dpi_handler: Optional PlatformDPIHandler instance

    Returns:
        LinuxCoordinateConverter instance
    """
    global _converter
    if _converter is None:
        with _converter_lock:
            # Double-check pattern inside lock
            if _converter is None:
                _converter = LinuxCoordinateConverter(dpi_handler)
    return _converter
