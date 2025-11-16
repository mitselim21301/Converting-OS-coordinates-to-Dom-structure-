"""
Windows DPI Handler - DPI Scaling and Per-Monitor V2 Support

Handles:
- Per-Monitor DPI Awareness V2
- Mixed DPI environments
- DPI change detection
- Monitor-specific DPI queries
- DPI scaling calculations
"""

import ctypes
from ctypes import wintypes
from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass
from enum import IntEnum
import logging

logger = logging.getLogger(__name__)


class MonitorDpiType(IntEnum):
    """DPI types for GetDpiForMonitor."""
    MDT_EFFECTIVE_DPI = 0  # Recommended for rendering
    MDT_ANGULAR_DPI = 1    # Based on angular width
    MDT_RAW_DPI = 2        # Based on raw resolution


class DpiAwarenessContext(IntEnum):
    """DPI awareness context values."""
    UNAWARE = -1
    SYSTEM_AWARE = -2
    PER_MONITOR_AWARE = -3
    PER_MONITOR_AWARE_V2 = -4
    UNAWARE_GDISCALED = -5


@dataclass
class MonitorInfo:
    """Information about a display monitor."""
    handle: int
    left: int
    top: int
    right: int
    bottom: int
    dpi_x: int
    dpi_y: int
    is_primary: bool
    scale_factor: float

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def scale_percentage(self) -> int:
        """Get scaling percentage (100, 125, 150, 200, etc.)"""
        return int((self.dpi_x / 96) * 100)


class DpiHandler:
    """
    Handles DPI awareness and scaling on Windows.

    Supports Per-Monitor DPI V2 with automatic fallback to older methods.
    """

    # Monitor info flags
    MONITORINFOF_PRIMARY = 0x00000001

    # Monitor default flags
    MONITOR_DEFAULTTONULL = 0x00000000
    MONITOR_DEFAULTTOPRIMARY = 0x00000001
    MONITOR_DEFAULTTONEAREST = 0x00000002

    # Windows structures
    class POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    class MONITORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", wintypes.DWORD),
        ]

    def __init__(self):
        """Initialize DPI handler with Windows API access."""
        self.user32 = ctypes.windll.user32
        self.shcore = None

        # Try to load shcore.dll for DPI functions (Windows 8.1+)
        try:
            self.shcore = ctypes.windll.shcore
        except (OSError, AttributeError):
            logger.warning("shcore.dll not available - limited DPI support")

        # Cache monitors (refreshed when needed)
        self._monitors_cache: List[MonitorInfo] = []
        self._cache_valid = False

    def get_dpi_for_window(self, hwnd: int) -> Tuple[int, int]:
        """
        Get DPI for a specific window (recommended method).

        Args:
            hwnd: Window handle

        Returns:
            Tuple of (dpi_x, dpi_y)
        """
        try:
            # Try GetDpiForWindow (Windows 10 1607+)
            dpi = self.user32.GetDpiForWindow(hwnd)
            if dpi:
                return (dpi, dpi)
        except (AttributeError, OSError) as e:
            logger.debug(f"GetDpiForWindow not available: {e}")

        # Fallback: Get DPI for monitor containing window
        try:
            hmonitor = self.user32.MonitorFromWindow(
                hwnd,
                self.MONITOR_DEFAULTTONEAREST
            )
            return self.get_dpi_for_monitor(hmonitor)
        except Exception as e:
            logger.error(f"Failed to get window DPI: {e}")
            return (96, 96)

    def get_dpi_for_monitor(self, hmonitor: int) -> Tuple[int, int]:
        """
        Get DPI for a specific monitor.

        Args:
            hmonitor: Monitor handle

        Returns:
            Tuple of (dpi_x, dpi_y)
        """
        if not self.shcore:
            return self.get_system_dpi()

        try:
            dpi_x = wintypes.UINT()
            dpi_y = wintypes.UINT()

            result = self.shcore.GetDpiForMonitor(
                hmonitor,
                MonitorDpiType.MDT_EFFECTIVE_DPI,
                ctypes.byref(dpi_x),
                ctypes.byref(dpi_y)
            )

            if result == 0:  # S_OK
                return (dpi_x.value, dpi_y.value)

        except Exception as e:
            logger.error(f"GetDpiForMonitor failed: {e}")

        return self.get_system_dpi()

    def get_system_dpi(self) -> Tuple[int, int]:
        """
        Get system DPI (primary monitor at login).

        Returns:
            Tuple of (dpi_x, dpi_y)
        """
        try:
            # Try GetDpiForSystem (Windows 10 1607+)
            dpi = self.user32.GetDpiForSystem()
            return (dpi, dpi)
        except (AttributeError, OSError):
            pass

        # Fallback to GetDeviceCaps
        try:
            hdc = self.user32.GetDC(0)
            if hdc:
                LOGPIXELSX = 88
                LOGPIXELSY = 90
                dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, LOGPIXELSX)
                dpi_y = ctypes.windll.gdi32.GetDeviceCaps(hdc, LOGPIXELSY)
                self.user32.ReleaseDC(0, hdc)
                return (dpi_x, dpi_y)
        except Exception as e:
            logger.error(f"Failed to get system DPI: {e}")

        # Ultimate fallback
        return (96, 96)

    def get_dpi_at_point(self, x: int, y: int) -> Tuple[int, int]:
        """
        Get DPI for the monitor containing a specific point.

        Args:
            x: X coordinate in screen pixels
            y: Y coordinate in screen pixels

        Returns:
            Tuple of (dpi_x, dpi_y)
        """
        try:
            pt = self.POINT(x, y)
            hmonitor = self.user32.MonitorFromPoint(
                pt,
                self.MONITOR_DEFAULTTONEAREST
            )
            return self.get_dpi_for_monitor(hmonitor)
        except Exception as e:
            logger.error(f"Failed to get DPI at point ({x}, {y}): {e}")
            return self.get_system_dpi()

    def get_scale_factor(self, dpi: int) -> float:
        """
        Get scale factor from DPI value.

        Args:
            dpi: DPI value

        Returns:
            Scale factor (1.0 = 100%, 1.25 = 125%, etc.)
        """
        return dpi / 96.0

    def dpi_to_percentage(self, dpi: int) -> int:
        """
        Convert DPI to percentage (100, 125, 150, 200, etc.).

        Args:
            dpi: DPI value

        Returns:
            Scale percentage
        """
        return int((dpi / 96) * 100)

    def percentage_to_dpi(self, percentage: int) -> int:
        """
        Convert percentage to DPI value.

        Args:
            percentage: Scale percentage (100, 125, 150, etc.)

        Returns:
            DPI value
        """
        return int((percentage / 100) * 96)

    def scale_value(self, value: int, from_dpi: int, to_dpi: int) -> int:
        """
        Scale a value from one DPI to another.

        Uses MulDiv pattern for accurate integer scaling.

        Args:
            value: Value to scale
            from_dpi: Source DPI
            to_dpi: Target DPI

        Returns:
            Scaled value
        """
        if from_dpi == to_dpi:
            return value

        # MulDiv pattern: value * to_dpi / from_dpi
        # Add half divisor for rounding
        return (value * to_dpi + from_dpi // 2) // from_dpi

    def enumerate_monitors(self, refresh: bool = False) -> List[MonitorInfo]:
        """
        Enumerate all display monitors.

        Args:
            refresh: Force refresh of cached monitor data

        Returns:
            List of MonitorInfo objects
        """
        if not refresh and self._cache_valid and self._monitors_cache:
            return self._monitors_cache

        monitors = []

        # Callback for EnumDisplayMonitors
        def monitor_enum_proc(hmonitor, hdc, lprect, lparam):
            try:
                # Get monitor info
                mi = self.MONITORINFO()
                mi.cbSize = ctypes.sizeof(self.MONITORINFO)

                if not self.user32.GetMonitorInfoW(hmonitor, ctypes.byref(mi)):
                    return True  # Continue enumeration

                # Get DPI
                dpi_x, dpi_y = self.get_dpi_for_monitor(hmonitor)

                # Create MonitorInfo
                info = MonitorInfo(
                    handle=hmonitor,
                    left=mi.rcMonitor.left,
                    top=mi.rcMonitor.top,
                    right=mi.rcMonitor.right,
                    bottom=mi.rcMonitor.bottom,
                    dpi_x=dpi_x,
                    dpi_y=dpi_y,
                    is_primary=bool(mi.dwFlags & self.MONITORINFOF_PRIMARY),
                    scale_factor=dpi_x / 96.0
                )

                monitors.append(info)

                logger.debug(
                    f"Monitor: {info.width}x{info.height} @ "
                    f"({info.left}, {info.top}), "
                    f"DPI: {info.dpi_x}x{info.dpi_y} ({info.scale_percentage}%), "
                    f"Primary: {info.is_primary}"
                )

            except Exception as e:
                logger.error(f"Error processing monitor: {e}")

            return True  # Continue enumeration

        # Create callback
        MONITORENUMPROC = ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HMONITOR,
            wintypes.HDC,
            ctypes.POINTER(self.RECT),
            wintypes.LPARAM
        )
        callback = MONITORENUMPROC(monitor_enum_proc)

        try:
            # Enumerate monitors
            self.user32.EnumDisplayMonitors(
                None,  # All monitors
                None,  # No clipping
                callback,
                0
            )

            self._monitors_cache = monitors
            self._cache_valid = True

        except Exception as e:
            logger.error(f"Failed to enumerate monitors: {e}")

        return monitors

    def get_monitor_at_point(self, x: int, y: int) -> Optional[MonitorInfo]:
        """
        Get monitor information for the monitor containing a point.

        Args:
            x: X coordinate in screen pixels
            y: Y coordinate in screen pixels

        Returns:
            MonitorInfo object or None if not found
        """
        try:
            pt = self.POINT(x, y)
            hmonitor = self.user32.MonitorFromPoint(
                pt,
                self.MONITOR_DEFAULTTONEAREST
            )

            # Find in cache or enumerate
            monitors = self.enumerate_monitors()
            for monitor in monitors:
                if monitor.handle == hmonitor:
                    return monitor

            # If not in cache, refresh and try again
            monitors = self.enumerate_monitors(refresh=True)
            for monitor in monitors:
                if monitor.handle == hmonitor:
                    return monitor

        except Exception as e:
            logger.error(f"Failed to get monitor at point ({x}, {y}): {e}")

        return None

    def get_primary_monitor(self) -> Optional[MonitorInfo]:
        """
        Get the primary monitor.

        Returns:
            MonitorInfo for primary monitor or None
        """
        monitors = self.enumerate_monitors()
        for monitor in monitors:
            if monitor.is_primary:
                return monitor
        return None

    def is_mixed_dpi_environment(self) -> bool:
        """
        Check if system has mixed DPI (different DPI on different monitors).

        Returns:
            True if monitors have different DPI values
        """
        monitors = self.enumerate_monitors()
        if len(monitors) <= 1:
            return False

        first_dpi = monitors[0].dpi_x
        for monitor in monitors[1:]:
            if monitor.dpi_x != first_dpi:
                return True

        return False

    def get_dpi_awareness_context(self) -> Optional[int]:
        """
        Get current DPI awareness context.

        Returns:
            DPI awareness context value or None if not available
        """
        try:
            return self.user32.GetThreadDpiAwarenessContext()
        except (AttributeError, OSError) as e:
            logger.debug(f"GetThreadDpiAwarenessContext not available: {e}")
            return None

    def physical_to_logical_point(
        self,
        hwnd: int,
        x: int,
        y: int
    ) -> Tuple[int, int]:
        """
        Convert physical point to logical coordinates for per-monitor DPI.

        Args:
            hwnd: Window handle
            x: Physical X coordinate
            y: Physical Y coordinate

        Returns:
            Tuple of (logical_x, logical_y)
        """
        try:
            pt = self.POINT(x, y)
            result = self.user32.PhysicalToLogicalPointForPerMonitorDPI(
                hwnd,
                ctypes.byref(pt)
            )
            if result:
                return (pt.x, pt.y)
        except (AttributeError, OSError) as e:
            logger.debug(f"PhysicalToLogicalPointForPerMonitorDPI failed: {e}")

        # Fallback: Calculate based on DPI
        dpi_x, dpi_y = self.get_dpi_for_window(hwnd)
        logical_x = int(x * 96 / dpi_x)
        logical_y = int(y * 96 / dpi_y)
        return (logical_x, logical_y)

    def logical_to_physical_point(
        self,
        hwnd: int,
        x: int,
        y: int
    ) -> Tuple[int, int]:
        """
        Convert logical point to physical coordinates for per-monitor DPI.

        Args:
            hwnd: Window handle
            x: Logical X coordinate
            y: Logical Y coordinate

        Returns:
            Tuple of (physical_x, physical_y)
        """
        try:
            pt = self.POINT(x, y)
            result = self.user32.LogicalToPhysicalPointForPerMonitorDPI(
                hwnd,
                ctypes.byref(pt)
            )
            if result:
                return (pt.x, pt.y)
        except (AttributeError, OSError) as e:
            logger.debug(f"LogicalToPhysicalPointForPerMonitorDPI failed: {e}")

        # Fallback: Calculate based on DPI
        dpi_x, dpi_y = self.get_dpi_for_window(hwnd)
        physical_x = int(x * dpi_x / 96)
        physical_y = int(y * dpi_y / 96)
        return (physical_x, physical_y)

    def get_dpi_summary(self) -> Dict[str, any]:
        """
        Get comprehensive DPI information for debugging.

        Returns:
            Dictionary with DPI information
        """
        system_dpi = self.get_system_dpi()
        monitors = self.enumerate_monitors()
        primary = self.get_primary_monitor()

        return {
            "system_dpi": {
                "x": system_dpi[0],
                "y": system_dpi[1],
                "percentage": self.dpi_to_percentage(system_dpi[0])
            },
            "primary_monitor": {
                "dpi_x": primary.dpi_x if primary else None,
                "dpi_y": primary.dpi_y if primary else None,
                "scale_percentage": primary.scale_percentage if primary else None,
                "bounds": f"{primary.width}x{primary.height}" if primary else None
            } if primary else None,
            "monitor_count": len(monitors),
            "mixed_dpi": self.is_mixed_dpi_environment(),
            "monitors": [
                {
                    "index": i,
                    "bounds": f"{m.width}x{m.height} @ ({m.left}, {m.top})",
                    "dpi": f"{m.dpi_x}x{m.dpi_y}",
                    "scale": f"{m.scale_percentage}%",
                    "primary": m.is_primary
                }
                for i, m in enumerate(monitors)
            ]
        }


# Singleton instance
_dpi_handler: Optional[DpiHandler] = None


def get_dpi_handler() -> DpiHandler:
    """Get or create singleton DpiHandler instance."""
    global _dpi_handler
    if _dpi_handler is None:
        _dpi_handler = DpiHandler()
    return _dpi_handler
