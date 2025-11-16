"""
Windows Window Manager - Browser Window Tracking

Handles:
- Browser window detection and tracking
- Window positioning and bounds
- Client area vs non-client area
- Window-to-screen coordinate conversion
- Multi-monitor window tracking
"""

import ctypes
from ctypes import wintypes
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class WindowInfo:
    """Information about a window."""
    hwnd: int
    title: str
    class_name: str
    process_id: int
    thread_id: int
    is_visible: bool
    is_minimized: bool
    is_maximized: bool
    window_rect: Tuple[int, int, int, int]  # left, top, right, bottom
    client_rect: Tuple[int, int, int, int]  # left, top, right, bottom
    monitor_handle: int

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


class WindowManager:
    """
    Manages browser window detection and tracking on Windows.

    Handles window enumeration, browser detection, and coordinate conversions.
    """

    # Browser process names (lowercase)
    BROWSER_PROCESSES = {
        'chrome.exe': 'Chrome',
        'firefox.exe': 'Firefox',
        'msedge.exe': 'Edge',
        'brave.exe': 'Brave',
        'opera.exe': 'Opera',
        'vivaldi.exe': 'Vivaldi',
        'iexplore.exe': 'Internet Explorer',
        'applicationframehost.exe': 'Edge (UWP)',  # Legacy Edge
    }

    # Browser class names
    BROWSER_CLASS_NAMES = [
        'Chrome_WidgetWin_1',  # Chrome, Edge, Brave
        'MozillaWindowClass',  # Firefox
        'OperaWindowClass',    # Opera
        'IEFrame',             # Internet Explorer
    ]

    # Window styles
    WS_VISIBLE = 0x10000000
    WS_MINIMIZE = 0x20000000
    WS_MAXIMIZE = 0x01000000

    # Windows structures
    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    class POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

    def __init__(self):
        """Initialize window manager."""
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32

        # Increase buffer sizes for better compatibility
        self._title_buffer_size = 512
        self._class_buffer_size = 256

    def get_window_info(self, hwnd: int) -> Optional[WindowInfo]:
        """
        Get detailed information about a window.

        Args:
            hwnd: Window handle

        Returns:
            WindowInfo object or None if failed
        """
        try:
            # Check if window is valid
            if not self.user32.IsWindow(hwnd):
                return None

            # Get window title
            title_buffer = ctypes.create_unicode_buffer(self._title_buffer_size)
            self.user32.GetWindowTextW(hwnd, title_buffer, self._title_buffer_size)
            title = title_buffer.value

            # Get class name
            class_buffer = ctypes.create_unicode_buffer(self._class_buffer_size)
            self.user32.GetClassNameW(hwnd, class_buffer, self._class_buffer_size)
            class_name = class_buffer.value

            # Get process and thread IDs
            process_id = wintypes.DWORD()
            thread_id = self.user32.GetWindowThreadProcessId(
                hwnd,
                ctypes.byref(process_id)
            )

            # Check visibility
            is_visible = bool(self.user32.IsWindowVisible(hwnd))

            # Get window style
            style = self.user32.GetWindowLongW(hwnd, -16)  # GWL_STYLE
            is_minimized = bool(style & self.WS_MINIMIZE)
            is_maximized = bool(style & self.WS_MAXIMIZE)

            # Get window rectangle (screen coordinates)
            window_rect = self.RECT()
            self.user32.GetWindowRect(hwnd, ctypes.byref(window_rect))

            # Get client rectangle
            client_rect = self.RECT()
            self.user32.GetClientRect(hwnd, ctypes.byref(client_rect))

            # Convert client rect to screen coordinates
            top_left = self.POINT(0, 0)
            self.user32.ClientToScreen(hwnd, ctypes.byref(top_left))
            bottom_right = self.POINT(client_rect.right, client_rect.bottom)
            self.user32.ClientToScreen(hwnd, ctypes.byref(bottom_right))

            client_rect_screen = (
                top_left.x,
                top_left.y,
                bottom_right.x,
                bottom_right.y
            )

            # Get monitor
            monitor_handle = self.user32.MonitorFromWindow(hwnd, 0x00000002)  # MONITOR_DEFAULTTONEAREST

            return WindowInfo(
                hwnd=hwnd,
                title=title,
                class_name=class_name,
                process_id=process_id.value,
                thread_id=thread_id,
                is_visible=is_visible,
                is_minimized=is_minimized,
                is_maximized=is_maximized,
                window_rect=(
                    window_rect.left,
                    window_rect.top,
                    window_rect.right,
                    window_rect.bottom
                ),
                client_rect=client_rect_screen,
                monitor_handle=monitor_handle
            )

        except Exception as e:
            logger.error(f"Failed to get window info for hwnd {hwnd}: {e}")
            return None

    def get_process_name(self, process_id: int) -> Optional[str]:
        """
        Get the process name from process ID.

        Args:
            process_id: Process ID

        Returns:
            Process name (e.g., 'chrome.exe') or None
        """
        try:
            # Open process
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            hprocess = self.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION,
                False,
                process_id
            )

            if not hprocess:
                return None

            try:
                # Get executable path
                size = wintypes.DWORD(1024)
                buffer = ctypes.create_unicode_buffer(size.value)

                # Try QueryFullProcessImageNameW (Vista+)
                if self.kernel32.QueryFullProcessImageNameW(
                    hprocess,
                    0,
                    buffer,
                    ctypes.byref(size)
                ):
                    full_path = buffer.value
                    # Extract filename
                    return full_path.split('\\')[-1].lower()

            finally:
                self.kernel32.CloseHandle(hprocess)

        except Exception as e:
            logger.debug(f"Failed to get process name for PID {process_id}: {e}")

        return None

    def is_browser_window(self, hwnd: int) -> bool:
        """
        Check if window is a browser window.

        Args:
            hwnd: Window handle

        Returns:
            True if window is a browser
        """
        info = self.get_window_info(hwnd)
        if not info or not info.is_visible:
            return False

        # Check class name
        if info.class_name in self.BROWSER_CLASS_NAMES:
            return True

        # Check process name
        process_name = self.get_process_name(info.process_id)
        if process_name and process_name in self.BROWSER_PROCESSES:
            return True

        # Check title for common browser patterns
        title_lower = info.title.lower()
        browser_indicators = [
            'chrome', 'firefox', 'edge', 'brave', 'opera', 'vivaldi',
            'mozilla', 'internet explorer', 'safari'
        ]
        return any(indicator in title_lower for indicator in browser_indicators)

    def enumerate_windows(
        self,
        visible_only: bool = True,
        browsers_only: bool = False
    ) -> List[WindowInfo]:
        """
        Enumerate all windows.

        Args:
            visible_only: Only include visible windows
            browsers_only: Only include browser windows

        Returns:
            List of WindowInfo objects
        """
        windows = []

        def enum_windows_callback(hwnd, lparam):
            try:
                info = self.get_window_info(hwnd)
                if not info:
                    return True

                # Filter by visibility
                if visible_only and not info.is_visible:
                    return True

                # Filter by browser
                if browsers_only and not self.is_browser_window(hwnd):
                    return True

                # Skip minimized windows
                if info.is_minimized:
                    return True

                # Skip windows with no title
                if not info.title:
                    return True

                windows.append(info)

            except Exception as e:
                logger.debug(f"Error enumerating window {hwnd}: {e}")

            return True

        # Create callback
        WNDENUMPROC = ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HWND,
            wintypes.LPARAM
        )
        callback = WNDENUMPROC(enum_windows_callback)

        try:
            self.user32.EnumWindows(callback, 0)
        except Exception as e:
            logger.error(f"Failed to enumerate windows: {e}")

        return windows

    def find_browser_windows(self) -> List[WindowInfo]:
        """
        Find all browser windows.

        Returns:
            List of browser WindowInfo objects
        """
        return self.enumerate_windows(visible_only=True, browsers_only=True)

    def get_window_at_point(self, x: int, y: int) -> Optional[WindowInfo]:
        """
        Get window at a specific screen point.

        Args:
            x: X coordinate in screen pixels
            y: Y coordinate in screen pixels

        Returns:
            WindowInfo for window at point or None
        """
        try:
            pt = self.POINT(x, y)
            hwnd = self.user32.WindowFromPoint(pt)

            if hwnd:
                # Get the top-level window
                hwnd = self.user32.GetAncestor(hwnd, 2)  # GA_ROOT
                return self.get_window_info(hwnd)

        except Exception as e:
            logger.error(f"Failed to get window at point ({x}, {y}): {e}")

        return None

    def get_foreground_window(self) -> Optional[WindowInfo]:
        """
        Get the foreground (active) window.

        Returns:
            WindowInfo for foreground window or None
        """
        try:
            hwnd = self.user32.GetForegroundWindow()
            if hwnd:
                return self.get_window_info(hwnd)
        except Exception as e:
            logger.error(f"Failed to get foreground window: {e}")

        return None

    def screen_to_client(
        self,
        hwnd: int,
        screen_x: int,
        screen_y: int
    ) -> Tuple[int, int]:
        """
        Convert screen coordinates to client coordinates.

        Args:
            hwnd: Window handle
            screen_x: X coordinate in screen pixels
            screen_y: Y coordinate in screen pixels

        Returns:
            Tuple of (client_x, client_y)
        """
        try:
            pt = self.POINT(screen_x, screen_y)
            result = self.user32.ScreenToClient(hwnd, ctypes.byref(pt))
            if result:
                return (pt.x, pt.y)
        except Exception as e:
            logger.error(f"ScreenToClient failed: {e}")

        return (screen_x, screen_y)

    def client_to_screen(
        self,
        hwnd: int,
        client_x: int,
        client_y: int
    ) -> Tuple[int, int]:
        """
        Convert client coordinates to screen coordinates.

        Args:
            hwnd: Window handle
            client_x: X coordinate in client pixels
            client_y: Y coordinate in client pixels

        Returns:
            Tuple of (screen_x, screen_y)
        """
        try:
            pt = self.POINT(client_x, client_y)
            result = self.user32.ClientToScreen(hwnd, ctypes.byref(pt))
            if result:
                return (pt.x, pt.y)
        except Exception as e:
            logger.error(f"ClientToScreen failed: {e}")

        return (client_x, client_y)

    def get_window_by_title(
        self,
        title_pattern: str,
        exact_match: bool = False
    ) -> Optional[WindowInfo]:
        """
        Find window by title.

        Args:
            title_pattern: Title to search for (regex if not exact_match)
            exact_match: Use exact string matching instead of regex

        Returns:
            WindowInfo for first matching window or None
        """
        windows = self.enumerate_windows(visible_only=True)

        for window in windows:
            if exact_match:
                if window.title == title_pattern:
                    return window
            else:
                if re.search(title_pattern, window.title, re.IGNORECASE):
                    return window

        return None

    def get_browser_type(self, hwnd: int) -> Optional[str]:
        """
        Detect browser type from window.

        Args:
            hwnd: Window handle

        Returns:
            Browser name (e.g., 'Chrome', 'Firefox') or None
        """
        info = self.get_window_info(hwnd)
        if not info:
            return None

        # Check process name
        process_name = self.get_process_name(info.process_id)
        if process_name:
            browser = self.BROWSER_PROCESSES.get(process_name)
            if browser:
                return browser

        # Check class name
        if 'Chrome' in info.class_name:
            return 'Chrome'
        elif 'Mozilla' in info.class_name:
            return 'Firefox'
        elif 'Opera' in info.class_name:
            return 'Opera'
        elif 'IEFrame' in info.class_name:
            return 'Internet Explorer'

        # Check title
        title_lower = info.title.lower()
        if 'chrome' in title_lower:
            return 'Chrome'
        elif 'firefox' in title_lower:
            return 'Firefox'
        elif 'edge' in title_lower:
            return 'Edge'
        elif 'brave' in title_lower:
            return 'Brave'
        elif 'opera' in title_lower:
            return 'Opera'

        return None

    def get_window_summary(self, hwnd: int) -> Dict[str, any]:
        """
        Get comprehensive window information for debugging.

        Args:
            hwnd: Window handle

        Returns:
            Dictionary with window details
        """
        info = self.get_window_info(hwnd)
        if not info:
            return {"error": "Invalid window handle"}

        browser_type = self.get_browser_type(hwnd)

        return {
            "hwnd": hwnd,
            "title": info.title,
            "class_name": info.class_name,
            "browser_type": browser_type,
            "process_id": info.process_id,
            "is_visible": info.is_visible,
            "is_minimized": info.is_minimized,
            "is_maximized": info.is_maximized,
            "window_bounds": {
                "left": info.window_rect[0],
                "top": info.window_rect[1],
                "right": info.window_rect[2],
                "bottom": info.window_rect[3],
                "width": info.window_width,
                "height": info.window_height
            },
            "client_bounds": {
                "left": info.client_rect[0],
                "top": info.client_rect[1],
                "right": info.client_rect[2],
                "bottom": info.client_rect[3],
                "width": info.client_width,
                "height": info.client_height
            },
            "chrome_offsets": {
                "x": info.chrome_offset_x,
                "y": info.chrome_offset_y
            },
            "monitor_handle": info.monitor_handle
        }


# Singleton instance
_window_manager: Optional[WindowManager] = None


def get_window_manager() -> WindowManager:
    """Get or create singleton WindowManager instance."""
    global _window_manager
    if _window_manager is None:
        _window_manager = WindowManager()
    return _window_manager
