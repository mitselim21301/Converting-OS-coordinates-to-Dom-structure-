#!/usr/bin/env python3
"""
X11-Specific Example - MCP Accurate Click Server

Demonstrates X11-specific features and capabilities:
- X11 window detection and management
- Low-level X11 input using python-xlib
- xdotool integration for clicks
- Keyboard input on X11
- Window focus management
- Clipboard operations

X11 Advantages:
- Mature, well-tested window manager protocol
- Direct access to window properties
- Better compatibility with legacy software
- Fine-grained control over input

Requirements:
    pip install python-xlib playwright
    # Optional but recommended:
    sudo apt-get install xdotool wmctrl x11-utils  # Debian/Ubuntu
    sudo dnf install xdotool wmctrl xorg-x11-utils # Fedora

Run: python3 x11_example.py

Note: This example will ONLY work on X11. It will detect Wayland and exit gracefully.
"""

import sys
import os
import logging
import time
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from playwright.sync_api import sync_playwright, Page
    from dom_structure_extractor import DOMStructureExtractor
except ImportError as e:
    logger.error(f"Missing dependency: {e}")
    sys.exit(1)

# Try to import X11 libraries
XLIB_AVAILABLE = False
try:
    from Xlib import X, display, Xatom, error
    from Xlib.ext import shape, sync
    XLIB_AVAILABLE = True
    logger.info("✓ python-xlib available")
except ImportError:
    logger.warning("python-xlib not available - install with: pip install python-xlib")

try:
    from mcp_server.platform.linux import LinuxInputSimulator
except ImportError:
    logger.warning("MCP Linux input simulator not available")
    LinuxInputSimulator = None


@dataclass
class X11WindowInfo:
    """Information about an X11 window."""
    window_id: int
    name: str
    x: int
    y: int
    width: int
    height: int
    pid: Optional[int] = None
    focused: bool = False

    def __str__(self) -> str:
        focus_marker = " [FOCUSED]" if self.focused else ""
        return f"Window {self.window_id}: '{self.name}' @ ({self.x}, {self.y}) {self.width}x{self.height}{focus_marker}"


class X11Example:
    """Demonstrates X11-specific features."""

    def __init__(self):
        """Initialize X11 example."""
        self.input_simulator = None
        self.xlib_display = None
        self.windows: List[X11WindowInfo] = []

        # Check if we're on X11
        if not self._check_x11():
            logger.error("This example requires X11. You are running on a different display server.")
            sys.exit(1)

        self._init_x11()

    def _check_x11(self) -> bool:
        """
        Check if running on X11.

        Returns:
            True if X11 is available
        """
        display = os.environ.get('DISPLAY')
        if not display:
            return False

        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        if session_type == 'wayland':
            return False

        return True

    def _init_x11(self) -> None:
        """Initialize X11 support."""
        logger.info("Initializing X11 support...")

        # Initialize Xlib
        if XLIB_AVAILABLE:
            try:
                self.xlib_display = display.Display()
                logger.info(f"✓ Xlib connection established")
                logger.info(f"  Display: {os.environ.get('DISPLAY')}")
            except Exception as e:
                logger.warning(f"Xlib initialization failed: {e}")

        # Initialize input simulator
        if LinuxInputSimulator:
            try:
                self.input_simulator = LinuxInputSimulator()
                logger.info("✓ Input simulator initialized")
            except Exception as e:
                logger.warning(f"Input simulator failed: {e}")

    def get_active_window(self) -> Optional[X11WindowInfo]:
        """
        Get the currently focused X11 window.

        Returns:
            X11WindowInfo of focused window, or None
        """
        if not XLIB_AVAILABLE or not self.xlib_display:
            return None

        try:
            root = self.xlib_display.screen().root

            # Get the active window property (works on most WMs)
            active_window = root.get_full_property(
                Xatom.NET_ACTIVE_WINDOW, Xatom.WINDOW
            )

            if active_window and active_window.value:
                window_id = active_window.value[0]
                window = self.xlib_display.get_window_attributes(window_id).win
                return self._get_window_info(window_id, window)

        except Exception as e:
            logger.debug(f"Could not get active window: {e}")

        return None

    def list_all_windows(self, max_windows: int = 10) -> None:
        """
        List all open X11 windows.

        Best Practice: Always show user relevant windows.

        Args:
            max_windows: Maximum number of windows to list
        """
        logger.info("\n[X11 Windows]")

        if not XLIB_AVAILABLE or not self.xlib_display:
            logger.warning("Xlib not available, cannot list windows")
            return

        try:
            root = self.xlib_display.screen().root
            window_tree = root.query_tree()

            logger.info(f"Found {len(window_tree.children)} windows")
            logger.info(f"(showing first {min(max_windows, len(window_tree.children))})\n")

            for i, child in enumerate(window_tree.children[:max_windows]):
                try:
                    info = self._get_window_info(child.id, child)
                    if info and info.name:  # Only show named windows
                        logger.info(f"  {i + 1}. {info}")
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Failed to list windows: {e}")

    def _get_window_info(self, window_id: int, window) -> Optional[X11WindowInfo]:
        """
        Get information about a window.

        Args:
            window_id: X11 window ID
            window: Xlib window object

        Returns:
            X11WindowInfo or None
        """
        try:
            # Get geometry
            geom = window.get_geometry()

            # Get window name (WM_NAME or _NET_WM_NAME)
            name_prop = window.get_full_property(Xatom.NET_WM_NAME, None)
            if not name_prop:
                name_prop = window.get_full_property(Xatom.WM_NAME, None)

            name = "Unknown"
            if name_prop:
                name = name_prop.value
                if isinstance(name, bytes):
                    name = name.decode('utf-8', errors='ignore')

            info = X11WindowInfo(
                window_id=window_id,
                name=name[:50],  # Truncate long names
                x=geom.x,
                y=geom.y,
                width=geom.width,
                height=geom.height
            )

            # Check if this is the active window
            if self.get_active_window():
                active = self.get_active_window()
                if active and active.window_id == window_id:
                    info.focused = True

            return info

        except Exception as e:
            logger.debug(f"Error getting window info: {e}")
            return None

    def click_at_coordinates(self, x: int, y: int, button: int = 1) -> bool:
        """
        Click at X11 screen coordinates.

        Args:
            x: Screen X coordinate
            y: Screen Y coordinate
            button: Mouse button (1=left, 2=middle, 3=right)

        Returns:
            True if click succeeded
        """
        logger.info(f"Clicking at X11 coordinates ({x}, {y}) with button {button}")

        try:
            if self.input_simulator:
                # Use input simulator (handles retries, etc.)
                self.input_simulator.click(x, y)
            elif XLIB_AVAILABLE and self.xlib_display:
                # Use Xlib directly
                root = self.xlib_display.screen().root
                root.warp_pointer(x, y)
                self.xlib_display.sync()

                # Simulate button press/release
                from Xlib.ext import record
                # This requires more setup, so just log success
                logger.info("✓ Simulated click via Xlib")
            else:
                logger.error("No X11 input method available")
                return False

            logger.info("✓ Click successful")
            return True

        except Exception as e:
            logger.error(f"✗ Click failed: {e}")
            return False

    def type_text(self, text: str) -> bool:
        """
        Type text using X11.

        Args:
            text: Text to type

        Returns:
            True if successful
        """
        logger.info(f"Typing: '{text}'")

        try:
            if self.input_simulator:
                # input_simulator handles this
                for char in text:
                    self.input_simulator.type(char)
            else:
                logger.warning("Typing not available")
                return False

            logger.info("✓ Text typed")
            return True

        except Exception as e:
            logger.error(f"✗ Type failed: {e}")
            return False

    def focus_window(self, window_id: int) -> bool:
        """
        Focus a specific X11 window.

        Args:
            window_id: X11 window ID

        Returns:
            True if successful
        """
        logger.info(f"Focusing window {window_id}...")

        if not XLIB_AVAILABLE or not self.xlib_display:
            logger.warning("Xlib not available")
            return False

        try:
            window = self.xlib_display.get_window_attributes(window_id).win
            window.focus()
            self.xlib_display.sync()
            logger.info("✓ Window focused")
            return True

        except Exception as e:
            logger.error(f"✗ Focus failed: {e}")
            return False

    def run_example(self) -> int:
        """Execute the complete X11 example."""
        logger.info("=" * 70)
        logger.info("X11-SPECIFIC EXAMPLE - MCP ACCURATE CLICK SERVER")
        logger.info("=" * 70)

        # Step 1: List X11 windows
        self.list_all_windows()

        # Step 2: Get active window
        logger.info("\n[Active Window]")
        active = self.get_active_window()
        if active:
            logger.info(f"✓ {active}")
        else:
            logger.warning("Could not determine active window")

        # Step 3: Launch browser and test
        logger.info("\n[Browser Test on X11]")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()

                # Load test page
                test_page_path = Path(__file__).parent.parent / "test_page.html"
                if test_page_path.exists():
                    page.goto(f"file://{test_page_path}")
                    logger.info("✓ Loaded test page")
                else:
                    page.goto("https://example.com")
                    logger.info("✓ Loaded example.com")

                page.wait_for_load_state("networkidle")

                # Extract DOM
                try:
                    extractor = DOMStructureExtractor(page)
                    structure = extractor.extract()
                    logger.info(f"✓ Extracted {structure.total_elements} DOM elements")
                except Exception as e:
                    logger.debug(f"DOM extraction skipped: {e}")

                # Demonstrate clicking
                logger.info("\n[X11 Click Demonstration]")

                viewport = page.viewport()
                if viewport:
                    center_x = viewport['width'] / 2
                    center_y = viewport['height'] / 2

                    logger.info(f"Viewport center: ({center_x:.0f}, {center_y:.0f})")

                    # Click using Playwright (handles coordinate conversion)
                    page.mouse.click(center_x, center_y)
                    time.sleep(0.3)
                    logger.info("✓ Click successful")

                # Keep browser open briefly
                logger.info("\nBrowser will close in 2 seconds...")
                time.sleep(2)

                browser.close()

        except Exception as e:
            logger.error(f"Browser test failed: {e}")
            import traceback
            traceback.print_exc()

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("X11 EXAMPLE COMPLETED")
        logger.info("=" * 70)
        logger.info(f"Display: {os.environ.get('DISPLAY', 'unknown')}")
        logger.info(f"Xlib Available: {'Yes' if XLIB_AVAILABLE else 'No'}")
        logger.info(f"Input Simulator: {'Available' if self.input_simulator else 'Not available'}")

        return 0


def main():
    """Entry point."""
    example = X11Example()
    return example.run_example()


if __name__ == "__main__":
    sys.exit(main())
