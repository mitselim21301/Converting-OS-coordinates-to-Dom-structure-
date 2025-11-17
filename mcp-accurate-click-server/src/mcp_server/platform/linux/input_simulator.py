"""
Linux Input Simulator - Production-Ready Implementation

Supports both X11 and Wayland with multiple fallback mechanisms:
1. Primary: pynput (cross-compatible, pure Python)
2. Fallback 1: python-xlib (X11 only, low-level)
3. Fallback 2: xdotool (external tool, X11 only)

Features:
- Multi-monitor support
- Retry logic for transient failures
- Comprehensive error handling
- Support for all mouse buttons (LEFT, RIGHT, MIDDLE, X1, X2)
- Environment detection (X11 vs Wayland)
- Singleton pattern for resource efficiency
"""

import logging
import os
import subprocess
import time
from typing import Optional, Tuple
from threading import Lock

from mcp_server.platform.base import PlatformInputSimulator, MouseButton

# Import edge case handler
try:
    from .edge_case_handler import get_edge_case_handler
    EDGE_CASE_HANDLER_AVAILABLE = True
except ImportError:
    EDGE_CASE_HANDLER_AVAILABLE = False

logger = logging.getLogger(__name__)


class LinuxInputSimulator(PlatformInputSimulator):
    """
    Linux input simulator with multi-method support and automatic fallback.

    Thread-safe singleton implementation for reliable mouse/keyboard control.
    """

    _instance: Optional['LinuxInputSimulator'] = None
    _lock: Lock = Lock()

    def __new__(cls):
        """Singleton pattern - only one instance per process."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Linux input simulator with environment detection."""
        # Prevent re-initialization in singleton
        if hasattr(self, '_initialized'):
            return

        self._initialized = True

        # Delay configuration (milliseconds)
        self._move_delay = 10
        self._click_delay = 10
        self._double_click_delay = 100

        # Retry configuration
        self._max_retries = 3
        self._retry_delay = 0.05  # 50ms between retries

        # Edge case detection
        self._edge_case_detection = None
        if EDGE_CASE_HANDLER_AVAILABLE:
            try:
                edge_handler = get_edge_case_handler()
                self._edge_case_detection = edge_handler.detect_edge_cases()

                if self._edge_case_detection.is_headless:
                    logger.error("Input Simulator: HEADLESS ENVIRONMENT - Input simulation will fail")

                if self._edge_case_detection.permission_issues:
                    logger.warning(f"Input Simulator: Permission issues: {self._edge_case_detection.permission_issues}")

                if self._edge_case_detection.remote_access_type.value != 'direct':
                    logger.info(f"Input Simulator: Remote access ({self._edge_case_detection.remote_access_type.value})")
                    # Increase delays for remote access
                    if 'ssh' in self._edge_case_detection.remote_access_type.value or \
                       'vnc' in self._edge_case_detection.remote_access_type.value:
                        self._move_delay = 50  # Increase to 50ms
                        self._click_delay = 50
                        self._retry_delay = 0.1  # Increase to 100ms
                        logger.info("Input Simulator: Increased delays for remote access")

            except Exception as e:
                logger.debug(f"Edge case detection failed: {e}")

        # Detect display server environment
        self._display_server = self._detect_display_server()
        logger.info(f"Detected display server: {self._display_server}")

        # Initialize input controllers
        self._pynput_available = self._init_pynput()
        self._xlib_available = self._init_xlib()
        self._xdotool_available = self._init_xdotool()

        # Log available methods
        methods = []
        if self._pynput_available:
            methods.append("pynput")
        if self._xlib_available:
            methods.append("python-xlib")
        if self._xdotool_available:
            methods.append("xdotool")

        if not methods:
            # Check if headless - provide helpful error message
            if self._edge_case_detection and self._edge_case_detection.is_headless:
                logger.error(
                    "No input methods available in HEADLESS environment. "
                    "Install Xvfb: apt-get install xvfb"
                )
            else:
                logger.error("No input methods available! Install pynput, python-xlib, or xdotool")
            raise RuntimeError(
                "No Linux input methods available. Install: pip install pynput python-xlib"
            )

        logger.info(f"Available input methods: {', '.join(methods)}")
        logger.info(f"Primary method: {methods[0]}")

    def _detect_display_server(self) -> str:
        """
        Detect whether running under X11 or Wayland.

        Returns:
            'x11', 'wayland', or 'unknown'
        """
        # Check XDG_SESSION_TYPE first (most reliable)
        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        if session_type in ('x11', 'wayland'):
            return session_type

        # Check WAYLAND_DISPLAY
        if os.environ.get('WAYLAND_DISPLAY'):
            return 'wayland'

        # Check DISPLAY (X11)
        if os.environ.get('DISPLAY'):
            return 'x11'

        logger.warning("Could not detect display server type")
        return 'unknown'

    def _init_pynput(self) -> bool:
        """
        Initialize pynput mouse controller (works on both X11 and Wayland).

        Returns:
            True if pynput is available and working
        """
        try:
            from pynput.mouse import Controller, Button
            self._pynput_mouse = Controller()
            self._pynput_button = Button

            # Test that it works
            pos = self._pynput_mouse.position
            logger.debug(f"pynput initialized successfully (cursor at {pos})")
            return True
        except ImportError:
            logger.warning("pynput not available. Install: pip install pynput")
            return False
        except Exception as e:
            logger.warning(f"pynput initialization failed: {e}")
            return False

    def _init_xlib(self) -> bool:
        """
        Initialize python-xlib (X11 only, low-level control).

        Returns:
            True if python-xlib is available and X11 is running
        """
        if self._display_server != 'x11':
            logger.debug("Skipping python-xlib (not running X11)")
            return False

        try:
            from Xlib import X, display
            from Xlib.ext.xtest import fake_input

            self._xlib_display = display.Display()
            self._xlib_screen = self._xlib_display.screen()
            self._xlib_root = self._xlib_screen.root
            self._xlib_X = X
            self._xlib_fake_input = fake_input

            logger.debug("python-xlib initialized successfully")
            return True
        except ImportError:
            logger.debug("python-xlib not available. Install: pip install python-xlib")
            return False
        except Exception as e:
            logger.warning(f"python-xlib initialization failed: {e}")
            return False

    def _init_xdotool(self) -> bool:
        """
        Check if xdotool is available (X11 only, external tool).

        Returns:
            True if xdotool command is available
        """
        if self._display_server != 'x11':
            logger.debug("Skipping xdotool (not running X11)")
            return False

        try:
            result = subprocess.run(
                ['which', 'xdotool'],
                capture_output=True,
                text=True,
                timeout=1
            )
            available = result.returncode == 0

            if available:
                logger.debug("xdotool is available")
            else:
                logger.debug("xdotool not found. Install: sudo apt install xdotool")

            return available
        except Exception as e:
            logger.debug(f"xdotool check failed: {e}")
            return False

    def _pynput_button_map(self, button: MouseButton):
        """Map MouseButton enum to pynput Button."""
        if not self._pynput_available:
            return None

        mapping = {
            MouseButton.LEFT: self._pynput_button.left,
            MouseButton.RIGHT: self._pynput_button.right,
            MouseButton.MIDDLE: self._pynput_button.middle,
            MouseButton.X1: self._pynput_button.x1,
            MouseButton.X2: self._pynput_button.x2,
        }
        return mapping.get(button)

    def _xlib_button_map(self, button: MouseButton) -> int:
        """Map MouseButton enum to X11 button number."""
        mapping = {
            MouseButton.LEFT: 1,
            MouseButton.RIGHT: 3,
            MouseButton.MIDDLE: 2,
            MouseButton.X1: 8,
            MouseButton.X2: 9,
        }
        return mapping.get(button, 1)

    def _xdotool_button_map(self, button: MouseButton) -> int:
        """Map MouseButton enum to xdotool button number."""
        return self._xlib_button_map(button)  # Same mapping as xlib

    def move_mouse(self, x: int, y: int, use_virtual_desk: bool = True) -> bool:
        """
        Move mouse to absolute screen coordinates.

        Args:
            x: Physical X coordinate
            y: Physical Y coordinate
            use_virtual_desk: Use virtual desktop for multi-monitor (always True on Linux)

        Returns:
            True if successful
        """
        for attempt in range(self._max_retries):
            try:
                # Method 1: pynput (preferred - works on X11 and Wayland)
                if self._pynput_available:
                    try:
                        self._pynput_mouse.position = (x, y)

                        # Verify position (with small tolerance for rounding)
                        time.sleep(self._move_delay / 1000.0)
                        actual_x, actual_y = self._pynput_mouse.position

                        if abs(actual_x - x) <= 2 and abs(actual_y - y) <= 2:
                            logger.debug(f"Mouse moved to ({x}, {y}) via pynput")
                            return True
                        else:
                            logger.warning(
                                f"pynput move verification failed: "
                                f"expected ({x}, {y}), got ({actual_x}, {actual_y})"
                            )
                    except Exception as e:
                        logger.debug(f"pynput move_mouse failed: {e}")

                # Method 2: python-xlib (X11 only)
                if self._xlib_available:
                    try:
                        self._xlib_fake_input(
                            self._xlib_display,
                            self._xlib_X.MotionNotify,
                            x=x,
                            y=y
                        )
                        self._xlib_display.sync()

                        time.sleep(self._move_delay / 1000.0)
                        logger.debug(f"Mouse moved to ({x}, {y}) via python-xlib")
                        return True
                    except Exception as e:
                        logger.debug(f"python-xlib move_mouse failed: {e}")

                # Method 3: xdotool (X11 only, external tool)
                if self._xdotool_available:
                    try:
                        subprocess.run(
                            ['xdotool', 'mousemove', '--sync', str(x), str(y)],
                            check=True,
                            capture_output=True,
                            timeout=1
                        )

                        time.sleep(self._move_delay / 1000.0)
                        logger.debug(f"Mouse moved to ({x}, {y}) via xdotool")
                        return True
                    except Exception as e:
                        logger.debug(f"xdotool move_mouse failed: {e}")

                # If we get here, all methods failed
                logger.warning(f"All methods failed for move_mouse({x}, {y}), attempt {attempt + 1}")

            except Exception as e:
                logger.warning(f"move_mouse attempt {attempt + 1} failed: {e}")

            # Wait before retry
            if attempt < self._max_retries - 1:
                time.sleep(self._retry_delay)

        logger.error(f"Failed to move mouse to ({x}, {y}) after {self._max_retries} attempts")
        return False

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
        for attempt in range(self._max_retries):
            try:
                # First, move to position
                if not self.move_mouse(x, y, use_virtual_desk):
                    logger.warning(f"Failed to move mouse before click (attempt {attempt + 1})")
                    if attempt < self._max_retries - 1:
                        time.sleep(self._retry_delay)
                        continue
                    return False

                # Small delay to ensure move completed
                time.sleep(self._click_delay / 1000.0)

                # Perform clicks
                for click_num in range(clicks):
                    success = False

                    # Method 1: pynput (preferred)
                    if self._pynput_available:
                        try:
                            pynput_btn = self._pynput_button_map(button)
                            if pynput_btn:
                                self._pynput_mouse.click(pynput_btn, 1)
                                success = True
                                logger.debug(f"Click {click_num + 1}/{clicks} via pynput")
                        except Exception as e:
                            logger.debug(f"pynput click failed: {e}")

                    # Method 2: python-xlib
                    if not success and self._xlib_available:
                        try:
                            btn_num = self._xlib_button_map(button)

                            # Button press
                            self._xlib_fake_input(
                                self._xlib_display,
                                self._xlib_X.ButtonPress,
                                detail=btn_num
                            )
                            self._xlib_display.sync()

                            time.sleep(self._click_delay / 1000.0)

                            # Button release
                            self._xlib_fake_input(
                                self._xlib_display,
                                self._xlib_X.ButtonRelease,
                                detail=btn_num
                            )
                            self._xlib_display.sync()

                            success = True
                            logger.debug(f"Click {click_num + 1}/{clicks} via python-xlib")
                        except Exception as e:
                            logger.debug(f"python-xlib click failed: {e}")

                    # Method 3: xdotool
                    if not success and self._xdotool_available:
                        try:
                            btn_num = self._xdotool_button_map(button)
                            subprocess.run(
                                ['xdotool', 'click', '--delay', str(self._click_delay), str(btn_num)],
                                check=True,
                                capture_output=True,
                                timeout=1
                            )
                            success = True
                            logger.debug(f"Click {click_num + 1}/{clicks} via xdotool")
                        except Exception as e:
                            logger.debug(f"xdotool click failed: {e}")

                    if not success:
                        logger.warning(f"All methods failed for click {click_num + 1}/{clicks}")
                        raise RuntimeError("All click methods failed")

                    # Delay between double-clicks
                    if click_num < clicks - 1:
                        time.sleep(self._double_click_delay / 1000.0)

                logger.debug(f"Successfully clicked at ({x}, {y}) with {button.name} x{clicks}")
                return True

            except Exception as e:
                logger.warning(f"click attempt {attempt + 1} failed: {e}")

                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay)

        logger.error(
            f"Failed to click at ({x}, {y}) with {button.name} "
            f"after {self._max_retries} attempts"
        )
        return False

    def scroll(self, amount: int, horizontal: bool = False) -> bool:
        """
        Scroll at current mouse position.

        Args:
            amount: Scroll amount (positive=up/right, negative=down/left)
            horizontal: True for horizontal scroll, False for vertical

        Returns:
            True if successful
        """
        for attempt in range(self._max_retries):
            try:
                # Method 1: pynput (preferred)
                if self._pynput_available:
                    try:
                        if horizontal:
                            # Horizontal scroll
                            self._pynput_mouse.scroll(amount, 0)
                        else:
                            # Vertical scroll
                            self._pynput_mouse.scroll(0, amount)

                        logger.debug(
                            f"Scrolled {'horizontally' if horizontal else 'vertically'} "
                            f"by {amount} via pynput"
                        )
                        return True
                    except Exception as e:
                        logger.debug(f"pynput scroll failed: {e}")

                # Method 2: python-xlib (X11 only)
                if self._xlib_available:
                    try:
                        # X11 scroll buttons: 4=up, 5=down, 6=left, 7=right
                        if horizontal:
                            button = 7 if amount > 0 else 6  # right : left
                        else:
                            button = 4 if amount > 0 else 5  # up : down

                        scroll_count = abs(amount)

                        for _ in range(scroll_count):
                            # Button press
                            self._xlib_fake_input(
                                self._xlib_display,
                                self._xlib_X.ButtonPress,
                                detail=button
                            )

                            # Button release
                            self._xlib_fake_input(
                                self._xlib_display,
                                self._xlib_X.ButtonRelease,
                                detail=button
                            )

                        self._xlib_display.sync()

                        logger.debug(
                            f"Scrolled {'horizontally' if horizontal else 'vertically'} "
                            f"by {amount} via python-xlib"
                        )
                        return True
                    except Exception as e:
                        logger.debug(f"python-xlib scroll failed: {e}")

                # Method 3: xdotool (X11 only)
                if self._xdotool_available:
                    try:
                        # xdotool uses 4/5 for vertical, 6/7 for horizontal
                        if horizontal:
                            button = 7 if amount > 0 else 6
                        else:
                            button = 4 if amount > 0 else 5

                        scroll_count = abs(amount)

                        subprocess.run(
                            ['xdotool', 'click', '--repeat', str(scroll_count), str(button)],
                            check=True,
                            capture_output=True,
                            timeout=2
                        )

                        logger.debug(
                            f"Scrolled {'horizontally' if horizontal else 'vertically'} "
                            f"by {amount} via xdotool"
                        )
                        return True
                    except Exception as e:
                        logger.debug(f"xdotool scroll failed: {e}")

                logger.warning(f"All methods failed for scroll (attempt {attempt + 1})")

            except Exception as e:
                logger.warning(f"scroll attempt {attempt + 1} failed: {e}")

            if attempt < self._max_retries - 1:
                time.sleep(self._retry_delay)

        logger.error(f"Failed to scroll after {self._max_retries} attempts")
        return False

    def get_cursor_pos(self) -> Tuple[int, int]:
        """
        Get current physical cursor position.

        Returns:
            Tuple of (x, y) in physical screen coordinates
        """
        # Method 1: pynput (preferred)
        if self._pynput_available:
            try:
                pos = self._pynput_mouse.position
                logger.debug(f"Cursor position: {pos} (via pynput)")
                return pos
            except Exception as e:
                logger.debug(f"pynput get_cursor_pos failed: {e}")

        # Method 2: python-xlib (X11 only)
        if self._xlib_available:
            try:
                pointer = self._xlib_root.query_pointer()
                pos = (pointer.root_x, pointer.root_y)
                logger.debug(f"Cursor position: {pos} (via python-xlib)")
                return pos
            except Exception as e:
                logger.debug(f"python-xlib get_cursor_pos failed: {e}")

        # Method 3: xdotool (X11 only)
        if self._xdotool_available:
            try:
                result = subprocess.run(
                    ['xdotool', 'getmouselocation', '--shell'],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=1
                )

                # Parse output: X=123\nY=456\n...
                lines = result.stdout.strip().split('\n')
                x = int(lines[0].split('=')[1])
                y = int(lines[1].split('=')[1])

                pos = (x, y)
                logger.debug(f"Cursor position: {pos} (via xdotool)")
                return pos
            except Exception as e:
                logger.debug(f"xdotool get_cursor_pos failed: {e}")

        # Fallback: return (0, 0) if all methods fail
        logger.error("All methods failed for get_cursor_pos, returning (0, 0)")
        return (0, 0)

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
        if move_delay is not None:
            self._move_delay = max(0, move_delay)
            logger.debug(f"Move delay set to {self._move_delay}ms")

        if click_delay is not None:
            self._click_delay = max(0, click_delay)
            logger.debug(f"Click delay set to {self._click_delay}ms")

        if double_click_delay is not None:
            self._double_click_delay = max(0, double_click_delay)
            logger.debug(f"Double-click delay set to {self._double_click_delay}ms")


# ==================== Singleton Factory ====================

_simulator_instance: Optional[LinuxInputSimulator] = None
_simulator_lock = Lock()


def get_input_simulator() -> LinuxInputSimulator:
    """
    Get the singleton LinuxInputSimulator instance.

    Returns:
        LinuxInputSimulator singleton instance
    """
    global _simulator_instance

    if _simulator_instance is None:
        with _simulator_lock:
            if _simulator_instance is None:
                _simulator_instance = LinuxInputSimulator()

    return _simulator_instance


__all__ = [
    'LinuxInputSimulator',
    'get_input_simulator',
]
