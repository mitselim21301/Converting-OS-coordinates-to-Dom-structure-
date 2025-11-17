"""
Base abstract classes for platform-specific implementations.

Defines the common interface that all platforms must implement.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass
from enum import IntEnum


# ==================== Common Data Classes ====================

class MouseButton(IntEnum):
    """Mouse button types - cross-platform."""
    LEFT = 1
    RIGHT = 2
    MIDDLE = 3
    X1 = 4
    X2 = 5


class KeyModifier(IntEnum):
    """Keyboard modifier keys - cross-platform."""
    NONE = 0
    SHIFT = 1
    CTRL = 2
    ALT = 4
    META = 8  # Windows key / Command key


@dataclass
class MonitorInfo:
    """Information about a display monitor - cross-platform."""
    handle: Any  # Platform-specific handle (int on Windows, str on Linux, etc.)
    left: int
    top: int
    right: int
    bottom: int
    dpi_x: int
    dpi_y: int
    is_primary: bool
    scale_factor: float
    name: Optional[str] = None  # Monitor name (e.g., "DP-1", "\\.\DISPLAY1")

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


@dataclass
class WindowInfo:
    """Information about a window - cross-platform."""
    handle: Any  # Platform-specific window handle
    title: str
    class_name: str
    process_id: int
    thread_id: int
    is_visible: bool
    is_minimized: bool
    is_maximized: bool
    window_rect: Tuple[int, int, int, int]  # left, top, right, bottom
    client_rect: Tuple[int, int, int, int]  # left, top, right, bottom (in screen coords)
    monitor_handle: Any

    @property
    def window_width(self) -> int:
        return self.window_rect[2] - self.window_rect[0]

    @property
    def window_height(self) -> int:
        return self.window_rect[3] - self.window_rect[1]

    @property
    def client_width(self) -> int:
        return self.client_rect[2] - self.client_rect[0]

    @property
    def client_height(self) -> int:
        return self.client_rect[3] - self.client_rect[1]

    @property
    def chrome_offset_x(self) -> int:
        """Left border/chrome offset."""
        return self.client_rect[0] - self.window_rect[0]

    @property
    def chrome_offset_y(self) -> int:
        """Top border/chrome offset (title bar, address bar, etc.)"""
        return self.client_rect[1] - self.window_rect[1]


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


# ==================== Abstract Base Classes ====================

class PlatformInputSimulator(ABC):
    """
    Abstract base class for platform-specific input simulation.

    All platforms must implement these methods for mouse and keyboard control.
    """

    @abstractmethod
    def move_mouse(self, x: int, y: int, use_virtual_desk: bool = True) -> bool:
        """
        Move mouse to absolute screen coordinates.

        Args:
            x: Physical X coordinate
            y: Physical Y coordinate
            use_virtual_desk: Use virtual desktop for multi-monitor (platform-specific)

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def click(
        self,
        x: int,
        y: int,
        button: MouseButton = MouseButton.LEFT,
        clicks: int = 1,
        use_virtual_desk: bool = True
    ) -> bool:
        """
        Click at specific screen coordinates.

        Args:
            x: Physical X coordinate
            y: Physical Y coordinate
            button: Mouse button to click
            clicks: Number of clicks (1=single, 2=double)
            use_virtual_desk: Use virtual desktop for multi-monitor

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def scroll(self, amount: int, horizontal: bool = False) -> bool:
        """
        Scroll at current mouse position.

        Args:
            amount: Scroll amount (positive=up/right, negative=down/left)
            horizontal: True for horizontal scroll, False for vertical

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def get_cursor_pos(self) -> Tuple[int, int]:
        """
        Get current physical cursor position.

        Returns:
            Tuple of (x, y) in physical screen coordinates
        """
        pass

    @abstractmethod
    def set_delays(
        self,
        move_delay: Optional[int] = None,
        click_delay: Optional[int] = None,
        double_click_delay: Optional[int] = None
    ) -> None:
        """
        Set delay timings for input simulation.

        Args:
            move_delay: Delay after mouse movement (ms)
            click_delay: Delay between button down/up (ms)
            double_click_delay: Delay between double clicks (ms)
        """
        pass


class PlatformDPIHandler(ABC):
    """
    Abstract base class for platform-specific DPI/scaling handling.

    All platforms must implement these methods for DPI-aware coordinate conversion.
    """

    @abstractmethod
    def get_dpi_for_window(self, window_handle: Any) -> Tuple[int, int]:
        """
        Get DPI for a specific window.

        Args:
            window_handle: Platform-specific window handle

        Returns:
            Tuple of (dpi_x, dpi_y)
        """
        pass

    @abstractmethod
    def get_dpi_at_point(self, x: int, y: int) -> Tuple[int, int]:
        """
        Get DPI for the monitor containing a specific point.

        Args:
            x: X coordinate in screen pixels
            y: Y coordinate in screen pixels

        Returns:
            Tuple of (dpi_x, dpi_y)
        """
        pass

    @abstractmethod
    def get_system_dpi(self) -> Tuple[int, int]:
        """
        Get system DPI (primary monitor default).

        Returns:
            Tuple of (dpi_x, dpi_y)
        """
        pass

    @abstractmethod
    def get_scale_factor(self, dpi: int) -> float:
        """
        Get scale factor from DPI value.

        Args:
            dpi: DPI value

        Returns:
            Scale factor (1.0 = 100%, 1.25 = 125%, etc.)
        """
        pass

    @abstractmethod
    def enumerate_monitors(self, refresh: bool = False) -> List[MonitorInfo]:
        """
        Enumerate all display monitors.

        Args:
            refresh: Force refresh of cached monitor data

        Returns:
            List of MonitorInfo objects
        """
        pass

    @abstractmethod
    def get_monitor_at_point(self, x: int, y: int) -> Optional[MonitorInfo]:
        """
        Get monitor information for the monitor containing a point.

        Args:
            x: X coordinate in screen pixels
            y: Y coordinate in screen pixels

        Returns:
            MonitorInfo object or None if not found
        """
        pass

    @abstractmethod
    def get_primary_monitor(self) -> Optional[MonitorInfo]:
        """
        Get the primary monitor.

        Returns:
            MonitorInfo for primary monitor or None
        """
        pass

    @abstractmethod
    def is_mixed_dpi_environment(self) -> bool:
        """
        Check if system has mixed DPI (different DPI on different monitors).

        Returns:
            True if monitors have different DPI values
        """
        pass


class PlatformWindowManager(ABC):
    """
    Abstract base class for platform-specific window management.

    All platforms must implement these methods for window detection and tracking.
    """

    @abstractmethod
    def get_window_info(self, window_handle: Any) -> Optional[WindowInfo]:
        """
        Get detailed information about a window.

        Args:
            window_handle: Platform-specific window handle

        Returns:
            WindowInfo object or None if failed
        """
        pass

    @abstractmethod
    def is_browser_window(self, window_handle: Any) -> bool:
        """
        Check if window is a browser window.

        Args:
            window_handle: Platform-specific window handle

        Returns:
            True if window is a browser
        """
        pass

    @abstractmethod
    def find_browser_windows(self) -> List[WindowInfo]:
        """
        Find all browser windows.

        Returns:
            List of browser WindowInfo objects
        """
        pass

    @abstractmethod
    def get_window_at_point(self, x: int, y: int) -> Optional[WindowInfo]:
        """
        Get window at a specific screen point.

        Args:
            x: X coordinate in screen pixels
            y: Y coordinate in screen pixels

        Returns:
            WindowInfo for window at point or None
        """
        pass

    @abstractmethod
    def get_foreground_window(self) -> Optional[WindowInfo]:
        """
        Get the foreground (active) window.

        Returns:
            WindowInfo for foreground window or None
        """
        pass

    @abstractmethod
    def screen_to_client(
        self,
        window_handle: Any,
        screen_x: int,
        screen_y: int
    ) -> Tuple[int, int]:
        """
        Convert screen coordinates to client (window-relative) coordinates.

        Args:
            window_handle: Platform-specific window handle
            screen_x: X coordinate in screen pixels
            screen_y: Y coordinate in screen pixels

        Returns:
            Tuple of (client_x, client_y)
        """
        pass

    @abstractmethod
    def client_to_screen(
        self,
        window_handle: Any,
        client_x: int,
        client_y: int
    ) -> Tuple[int, int]:
        """
        Convert client coordinates to screen coordinates.

        Args:
            window_handle: Platform-specific window handle
            client_x: X coordinate in client pixels
            client_y: Y coordinate in client pixels

        Returns:
            Tuple of (screen_x, screen_y)
        """
        pass


class PlatformCoordinateConverter(ABC):
    """
    Abstract base class for platform-specific coordinate conversion.

    All platforms must implement these methods for coordinate space transformations.
    """

    @abstractmethod
    def get_virtual_screen_bounds(self, refresh: bool = False) -> Rectangle:
        """
        Get the virtual screen bounding rectangle.

        Returns:
            Rectangle containing virtual screen bounds in physical pixels
        """
        pass

    @abstractmethod
    def get_monitor_count(self) -> int:
        """Get the number of display monitors."""
        pass

    @abstractmethod
    def get_physical_cursor_pos(self) -> Point:
        """
        Get current cursor position in physical screen coordinates.

        Returns:
            Point with physical screen coordinates
        """
        pass

    @abstractmethod
    def physical_to_logical(
        self,
        physical_x: int,
        physical_y: int,
        dpi: int = 96
    ) -> Point:
        """
        Convert physical pixels to logical pixels.

        Args:
            physical_x: X coordinate in physical pixels
            physical_y: Y coordinate in physical pixels
            dpi: DPI value (default 96 = 100% scaling)

        Returns:
            Point with logical coordinates
        """
        pass

    @abstractmethod
    def logical_to_physical(
        self,
        logical_x: int,
        logical_y: int,
        dpi: int = 96
    ) -> Point:
        """
        Convert logical pixels to physical pixels.

        Args:
            logical_x: X coordinate in logical pixels
            logical_y: Y coordinate in logical pixels
            dpi: DPI value (default 96 = 100% scaling)

        Returns:
            Point with physical coordinates
        """
        pass

    @abstractmethod
    def physical_to_css(
        self,
        physical_x: int,
        physical_y: int,
        device_pixel_ratio: float = 1.0,
        browser_zoom: float = 1.0
    ) -> Point:
        """
        Convert physical screen pixels to CSS pixels.

        Args:
            physical_x: X coordinate in physical pixels
            physical_y: Y coordinate in physical pixels
            device_pixel_ratio: Browser's window.devicePixelRatio
            browser_zoom: Browser zoom level (1.0 = 100%)

        Returns:
            Point with CSS pixel coordinates
        """
        pass

    @abstractmethod
    def css_to_physical(
        self,
        css_x: int,
        css_y: int,
        device_pixel_ratio: float = 1.0,
        browser_zoom: float = 1.0
    ) -> Point:
        """
        Convert CSS pixels to physical screen pixels.

        Args:
            css_x: X coordinate in CSS pixels
            css_y: Y coordinate in CSS pixels
            device_pixel_ratio: Browser's window.devicePixelRatio
            browser_zoom: Browser zoom level (1.0 = 100%)

        Returns:
            Point with physical pixel coordinates
        """
        pass


__all__ = [
    # Enums
    'MouseButton',
    'KeyModifier',
    # Data classes
    'MonitorInfo',
    'WindowInfo',
    'Point',
    'Rectangle',
    # Abstract base classes
    'PlatformInputSimulator',
    'PlatformDPIHandler',
    'PlatformWindowManager',
    'PlatformCoordinateConverter',
]
