"""
Windows Input Simulator - Mouse Click Simulation

Handles:
- Mouse click simulation using SendInput
- Multi-monitor coordinate normalization
- Physical cursor positioning
- Support for different button types and modifiers
- Accurate clicking with DPI awareness
"""

import ctypes
from ctypes import wintypes
from typing import Optional, Tuple
from enum import IntEnum
import time
import logging

logger = logging.getLogger(__name__)


class MouseButton(IntEnum):
    """Mouse button types."""
    LEFT = 1
    RIGHT = 2
    MIDDLE = 3
    X1 = 4
    X2 = 5


class KeyModifier(IntEnum):
    """Keyboard modifier keys."""
    NONE = 0
    SHIFT = 1
    CTRL = 2
    ALT = 4
    WIN = 8


class InputSimulator:
    """
    Simulates mouse input on Windows using SendInput API.

    Provides accurate clicking with multi-monitor and DPI support.
    """

    # Input types
    INPUT_MOUSE = 0
    INPUT_KEYBOARD = 1

    # Mouse event flags
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP = 0x0040
    MOUSEEVENTF_XDOWN = 0x0080
    MOUSEEVENTF_XUP = 0x0100
    MOUSEEVENTF_WHEEL = 0x0800
    MOUSEEVENTF_HWHEEL = 0x1000
    MOUSEEVENTF_ABSOLUTE = 0x8000
    MOUSEEVENTF_VIRTUALDESK = 0x4000

    # X button data
    XBUTTON1 = 0x0001
    XBUTTON2 = 0x0002

    # Keyboard event flags
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_SCANCODE = 0x0008

    # Virtual key codes for modifiers
    VK_SHIFT = 0x10
    VK_CONTROL = 0x11
    VK_MENU = 0x12  # ALT
    VK_LWIN = 0x5B

    # System metrics
    SM_XVIRTUALSCREEN = 76
    SM_YVIRTUALSCREEN = 77
    SM_CXVIRTUALSCREEN = 78
    SM_CYVIRTUALSCREEN = 79

    # Windows structures
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
        ]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
        ]

    class INPUT_UNION(ctypes.Union):
        _fields_ = [
            ("mi", MOUSEINPUT),
            ("ki", KEYBDINPUT),
        ]

    class INPUT(ctypes.Structure):
        _fields_ = [
            ("type", wintypes.DWORD),
            ("union", INPUT_UNION)
        ]

    class POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

    def __init__(self):
        """Initialize input simulator."""
        self.user32 = ctypes.windll.user32

        # Default delays (milliseconds)
        self.move_delay = 10  # Delay after mouse movement
        self.click_delay = 10  # Delay between down and up
        self.double_click_delay = 100  # Delay between double clicks

    def _normalize_coordinates(
        self,
        x: int,
        y: int,
        use_virtual_desk: bool = True
    ) -> Tuple[int, int]:
        """
        Normalize screen coordinates to 0-65535 range for SendInput.

        Args:
            x: Physical X coordinate
            y: Physical Y coordinate
            use_virtual_desk: Use virtual desktop (multi-monitor)

        Returns:
            Tuple of (normalized_x, normalized_y)
        """
        try:
            if use_virtual_desk:
                # Get virtual screen bounds (handles multi-monitor)
                virtual_left = self.user32.GetSystemMetrics(self.SM_XVIRTUALSCREEN)
                virtual_top = self.user32.GetSystemMetrics(self.SM_YVIRTUALSCREEN)
                virtual_width = self.user32.GetSystemMetrics(self.SM_CXVIRTUALSCREEN)
                virtual_height = self.user32.GetSystemMetrics(self.SM_CYVIRTUALSCREEN)

                # Adjust for virtual screen offset (negative coordinates)
                adjusted_x = x - virtual_left
                adjusted_y = y - virtual_top

                # Normalize to 0-65535
                # Formula from research: (pixel * 65535) / dimension
                normalized_x = int((adjusted_x * 65535) / virtual_width)
                normalized_y = int((adjusted_y * 65535) / virtual_height)

                logger.debug(
                    f"Normalized ({x}, {y}) -> ({normalized_x}, {normalized_y}) "
                    f"[Virtual: ({virtual_left}, {virtual_top}), "
                    f"Size: {virtual_width}x{virtual_height}]"
                )
            else:
                # Single monitor normalization
                screen_width = self.user32.GetSystemMetrics(0)  # SM_CXSCREEN
                screen_height = self.user32.GetSystemMetrics(1)  # SM_CYSCREEN

                normalized_x = int((x * 65535) / screen_width)
                normalized_y = int((y * 65535) / screen_height)

                logger.debug(
                    f"Normalized ({x}, {y}) -> ({normalized_x}, {normalized_y}) "
                    f"[Screen: {screen_width}x{screen_height}]"
                )

            return (normalized_x, normalized_y)

        except Exception as e:
            logger.error(f"Failed to normalize coordinates ({x}, {y}): {e}")
            return (x, y)

    def _send_input(self, inputs: list) -> bool:
        """
        Send input events using SendInput.

        Args:
            inputs: List of INPUT structures

        Returns:
            True if successful
        """
        try:
            input_array = (self.INPUT * len(inputs))(*inputs)
            result = self.user32.SendInput(
                len(inputs),
                ctypes.byref(input_array),
                ctypes.sizeof(self.INPUT)
            )

            if result != len(inputs):
                logger.warning(
                    f"SendInput sent {result}/{len(inputs)} events"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"SendInput failed: {e}")
            return False

    def move_mouse(
        self,
        x: int,
        y: int,
        use_virtual_desk: bool = True
    ) -> bool:
        """
        Move mouse to absolute screen coordinates.

        Args:
            x: Physical X coordinate
            y: Physical Y coordinate
            use_virtual_desk: Use virtual desktop for multi-monitor

        Returns:
            True if successful
        """
        try:
            # Normalize coordinates
            norm_x, norm_y = self._normalize_coordinates(x, y, use_virtual_desk)

            # Create mouse input
            mouse_input = self.MOUSEINPUT()
            mouse_input.dx = norm_x
            mouse_input.dy = norm_y
            mouse_input.mouseData = 0
            mouse_input.dwFlags = self.MOUSEEVENTF_MOVE | self.MOUSEEVENTF_ABSOLUTE
            if use_virtual_desk:
                mouse_input.dwFlags |= self.MOUSEEVENTF_VIRTUALDESK
            mouse_input.time = 0
            mouse_input.dwExtraInfo = None

            # Create INPUT structure
            input_event = self.INPUT()
            input_event.type = self.INPUT_MOUSE
            input_event.union.mi = mouse_input

            # Send input
            result = self._send_input([input_event])

            if result:
                # Small delay to ensure mouse has moved
                time.sleep(self.move_delay / 1000.0)
                logger.debug(f"Moved mouse to ({x}, {y})")

            return result

        except Exception as e:
            logger.error(f"Failed to move mouse to ({x}, {y}): {e}")
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
        try:
            # Move mouse to position
            if not self.move_mouse(x, y, use_virtual_desk):
                return False

            # Perform clicks
            for i in range(clicks):
                if i > 0:
                    # Delay between multiple clicks
                    time.sleep(self.double_click_delay / 1000.0)

                # Send button down and up
                if not self._click_at_current_position(button):
                    return False

            logger.info(
                f"Clicked {clicks}x at ({x}, {y}) with {button.name} button"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to click at ({x}, {y}): {e}")
            return False

    def _click_at_current_position(self, button: MouseButton) -> bool:
        """
        Perform click at current cursor position.

        Args:
            button: Mouse button to click

        Returns:
            True if successful
        """
        try:
            # Determine button flags
            if button == MouseButton.LEFT:
                down_flag = self.MOUSEEVENTF_LEFTDOWN
                up_flag = self.MOUSEEVENTF_LEFTUP
                mouse_data = 0
            elif button == MouseButton.RIGHT:
                down_flag = self.MOUSEEVENTF_RIGHTDOWN
                up_flag = self.MOUSEEVENTF_RIGHTUP
                mouse_data = 0
            elif button == MouseButton.MIDDLE:
                down_flag = self.MOUSEEVENTF_MIDDLEDOWN
                up_flag = self.MOUSEEVENTF_MIDDLEUP
                mouse_data = 0
            elif button == MouseButton.X1:
                down_flag = self.MOUSEEVENTF_XDOWN
                up_flag = self.MOUSEEVENTF_XUP
                mouse_data = self.XBUTTON1
            elif button == MouseButton.X2:
                down_flag = self.MOUSEEVENTF_XDOWN
                up_flag = self.MOUSEEVENTF_XUP
                mouse_data = self.XBUTTON2
            else:
                logger.error(f"Unknown mouse button: {button}")
                return False

            # Create button down input
            down_input = self.MOUSEINPUT()
            down_input.dx = 0
            down_input.dy = 0
            down_input.mouseData = mouse_data
            down_input.dwFlags = down_flag
            down_input.time = 0
            down_input.dwExtraInfo = None

            # Create button up input
            up_input = self.MOUSEINPUT()
            up_input.dx = 0
            up_input.dy = 0
            up_input.mouseData = mouse_data
            up_input.dwFlags = up_flag
            up_input.time = 0
            up_input.dwExtraInfo = None

            # Create INPUT structures
            down_event = self.INPUT()
            down_event.type = self.INPUT_MOUSE
            down_event.union.mi = down_input

            up_event = self.INPUT()
            up_event.type = self.INPUT_MOUSE
            up_event.union.mi = up_input

            # Send both events
            result = self._send_input([down_event, up_event])

            if result:
                # Small delay between down and up
                time.sleep(self.click_delay / 1000.0)

            return result

        except Exception as e:
            logger.error(f"Failed to click at current position: {e}")
            return False

    def scroll(
        self,
        amount: int,
        horizontal: bool = False
    ) -> bool:
        """
        Scroll at current mouse position.

        Args:
            amount: Scroll amount (positive=up/right, negative=down/left)
                   Value is in WHEEL_DELTA units (120 = one notch)
            horizontal: True for horizontal scroll, False for vertical

        Returns:
            True if successful
        """
        try:
            # Create scroll input
            scroll_input = self.MOUSEINPUT()
            scroll_input.dx = 0
            scroll_input.dy = 0
            scroll_input.mouseData = amount
            scroll_input.dwFlags = (
                self.MOUSEEVENTF_HWHEEL if horizontal else self.MOUSEEVENTF_WHEEL
            )
            scroll_input.time = 0
            scroll_input.dwExtraInfo = None

            # Create INPUT structure
            input_event = self.INPUT()
            input_event.type = self.INPUT_MOUSE
            input_event.union.mi = scroll_input

            # Send input
            result = self._send_input([input_event])

            if result:
                direction = "horizontal" if horizontal else "vertical"
                logger.debug(f"Scrolled {direction} by {amount}")

            return result

        except Exception as e:
            logger.error(f"Failed to scroll: {e}")
            return False

    def get_cursor_pos(self) -> Tuple[int, int]:
        """
        Get current physical cursor position.

        Returns:
            Tuple of (x, y) in physical screen coordinates
        """
        try:
            pt = self.POINT()

            # Try GetPhysicalCursorPos first (more accurate)
            try:
                if self.user32.GetPhysicalCursorPos(ctypes.byref(pt)):
                    return (pt.x, pt.y)
            except (AttributeError, OSError):
                pass

            # Fallback to GetCursorPos
            if self.user32.GetCursorPos(ctypes.byref(pt)):
                return (pt.x, pt.y)

        except Exception as e:
            logger.error(f"Failed to get cursor position: {e}")

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
            self.move_delay = max(0, move_delay)
        if click_delay is not None:
            self.click_delay = max(0, click_delay)
        if double_click_delay is not None:
            self.double_click_delay = max(0, double_click_delay)

        logger.debug(
            f"Input delays set: move={self.move_delay}ms, "
            f"click={self.click_delay}ms, "
            f"double_click={self.double_click_delay}ms"
        )

    def click_with_modifiers(
        self,
        x: int,
        y: int,
        button: MouseButton = MouseButton.LEFT,
        modifiers: KeyModifier = KeyModifier.NONE,
        use_virtual_desk: bool = True
    ) -> bool:
        """
        Click with keyboard modifiers held.

        Args:
            x: Physical X coordinate
            y: Physical Y coordinate
            button: Mouse button to click
            modifiers: Keyboard modifiers (can be combined with |)
            use_virtual_desk: Use virtual desktop for multi-monitor

        Returns:
            True if successful
        """
        try:
            # Press modifiers
            modifier_keys = []
            if modifiers & KeyModifier.SHIFT:
                modifier_keys.append(self.VK_SHIFT)
            if modifiers & KeyModifier.CTRL:
                modifier_keys.append(self.VK_CONTROL)
            if modifiers & KeyModifier.ALT:
                modifier_keys.append(self.VK_MENU)
            if modifiers & KeyModifier.WIN:
                modifier_keys.append(self.VK_LWIN)

            # Send key downs
            for vk in modifier_keys:
                if not self._press_key(vk, False):
                    return False

            # Perform click
            result = self.click(x, y, button, 1, use_virtual_desk)

            # Release modifiers
            for vk in reversed(modifier_keys):
                self._press_key(vk, True)

            return result

        except Exception as e:
            logger.error(f"Failed to click with modifiers: {e}")
            return False

    def _press_key(self, vk_code: int, key_up: bool = False) -> bool:
        """
        Press or release a key.

        Args:
            vk_code: Virtual key code
            key_up: True to release, False to press

        Returns:
            True if successful
        """
        try:
            kb_input = self.KEYBDINPUT()
            kb_input.wVk = vk_code
            kb_input.wScan = 0
            kb_input.dwFlags = self.KEYEVENTF_KEYUP if key_up else 0
            kb_input.time = 0
            kb_input.dwExtraInfo = None

            input_event = self.INPUT()
            input_event.type = self.INPUT_KEYBOARD
            input_event.union.ki = kb_input

            return self._send_input([input_event])

        except Exception as e:
            logger.error(f"Failed to press key {vk_code}: {e}")
            return False


# Singleton instance
_input_simulator: Optional[InputSimulator] = None


def get_input_simulator() -> InputSimulator:
    """Get or create singleton InputSimulator instance."""
    global _input_simulator
    if _input_simulator is None:
        _input_simulator = InputSimulator()
    return _input_simulator
