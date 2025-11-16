"""
Windows Coordinate Converter - OS to DOM Coordinate Conversion

Handles conversion between:
- Physical screen pixels (OS coordinates)
- Logical pixels (DPI-aware coordinates)
- CSS pixels (browser viewport)
- DOM coordinates (element-relative)

Supports multi-monitor setups with mixed DPI environments.
"""

import ctypes
from ctypes import wintypes
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Point:
    """Represents a 2D point with coordinate space tracking."""
    x: int
    y: int
    coordinate_space: str = "physical"  # physical, logical, css, dom


@dataclass
class Rectangle:
    """Represents a rectangle in any coordinate space."""
    left: int
    top: int
    right: int
    bottom: int
    coordinate_space: str = "physical"

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is within rectangle."""
        return self.left <= x <= self.right and self.top <= y <= self.bottom


class CoordinateConverter:
    """
    Converts coordinates between different coordinate spaces on Windows.

    Coordinate Spaces:
    - Physical: Raw hardware pixels from the OS
    - Logical: DPI-scaled coordinates (system DPI aware)
    - CSS: Browser viewport pixels (device pixel ratio applied)
    - DOM: Element-relative coordinates
    """

    # Windows API structures
    class POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    # System metrics constants
    SM_XVIRTUALSCREEN = 76
    SM_YVIRTUALSCREEN = 77
    SM_CXVIRTUALSCREEN = 78
    SM_CYVIRTUALSCREEN = 79
    SM_CMONITORS = 80

    def __init__(self):
        """Initialize coordinate converter with Windows API access."""
        self.user32 = ctypes.windll.user32
        self.shcore = None

        # Try to load shcore.dll for DPI functions (Windows 8.1+)
        try:
            self.shcore = ctypes.windll.shcore
        except (OSError, AttributeError):
            logger.warning("shcore.dll not available - DPI functions limited")

        # Set process DPI awareness for accurate coordinate reporting
        self._set_dpi_awareness()

        # Cache virtual screen dimensions (updated when needed)
        self._virtual_screen_cache: Optional[Rectangle] = None

    def _set_dpi_awareness(self) -> None:
        """
        Set process to Per-Monitor V2 DPI awareness for accurate coordinates.

        Falls back to older methods if PMv2 not available.
        """
        try:
            # Try Per-Monitor V2 (Windows 10 1703+)
            DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)
            result = self.user32.SetProcessDpiAwarenessContext(
                DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
            )
            if result:
                logger.info("Set DPI awareness to Per-Monitor V2")
                return
        except (AttributeError, OSError) as e:
            logger.debug(f"PMv2 not available: {e}")

        # Try SetProcessDpiAwareness (Windows 8.1+)
        if self.shcore:
            try:
                # PROCESS_PER_MONITOR_DPI_AWARE = 2
                self.shcore.SetProcessDpiAwareness(2)
                logger.info("Set DPI awareness to Per-Monitor V1")
                return
            except (OSError, AttributeError) as e:
                logger.debug(f"Per-Monitor DPI not available: {e}")

        # Fallback to basic DPI awareness (Windows Vista+)
        try:
            self.user32.SetProcessDPIAware()
            logger.info("Set basic DPI awareness")
        except (OSError, AttributeError) as e:
            logger.warning(f"Could not set DPI awareness: {e}")

    def get_virtual_screen_bounds(self, refresh: bool = False) -> Rectangle:
        """
        Get the virtual screen bounding rectangle.

        The virtual screen encompasses all monitors. Primary monitor is at (0,0).
        Monitors to the left/above have negative coordinates.

        Args:
            refresh: Force refresh of cached bounds

        Returns:
            Rectangle containing virtual screen bounds in physical pixels
        """
        if not refresh and self._virtual_screen_cache:
            return self._virtual_screen_cache

        try:
            left = self.user32.GetSystemMetrics(self.SM_XVIRTUALSCREEN)
            top = self.user32.GetSystemMetrics(self.SM_YVIRTUALSCREEN)
            width = self.user32.GetSystemMetrics(self.SM_CXVIRTUALSCREEN)
            height = self.user32.GetSystemMetrics(self.SM_CYVIRTUALSCREEN)

            self._virtual_screen_cache = Rectangle(
                left=left,
                top=top,
                right=left + width,
                bottom=top + height,
                coordinate_space="physical"
            )

            logger.debug(
                f"Virtual screen: ({left}, {top}) to "
                f"({left + width}, {top + height}), "
                f"size: {width}x{height}"
            )

            return self._virtual_screen_cache

        except Exception as e:
            logger.error(f"Failed to get virtual screen bounds: {e}")
            # Return sensible default
            return Rectangle(0, 0, 1920, 1080, "physical")

    def get_monitor_count(self) -> int:
        """Get the number of display monitors."""
        try:
            return self.user32.GetSystemMetrics(self.SM_CMONITORS)
        except Exception as e:
            logger.error(f"Failed to get monitor count: {e}")
            return 1

    def get_physical_cursor_pos(self) -> Point:
        """
        Get current cursor position in physical screen coordinates.

        Uses GetPhysicalCursorPos which always returns actual hardware pixels
        regardless of DPI awareness mode.

        Returns:
            Point with physical screen coordinates
        """
        pt = self.POINT()
        try:
            # Try GetPhysicalCursorPos (Windows Vista+)
            result = self.user32.GetPhysicalCursorPos(ctypes.byref(pt))
            if result:
                return Point(pt.x, pt.y, "physical")
        except (AttributeError, OSError):
            logger.debug("GetPhysicalCursorPos not available, using GetCursorPos")

        # Fallback to GetCursorPos (returns physical coords if DPI-aware)
        try:
            result = self.user32.GetCursorPos(ctypes.byref(pt))
            if result:
                return Point(pt.x, pt.y, "physical")
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
        # (negative values common in DOM, CSS)
        return -10000 <= x <= 50000 and -10000 <= y <= 50000


# Singleton instance
_converter: Optional[CoordinateConverter] = None


def get_converter() -> CoordinateConverter:
    """Get or create singleton CoordinateConverter instance."""
    global _converter
    if _converter is None:
        _converter = CoordinateConverter()
    return _converter
