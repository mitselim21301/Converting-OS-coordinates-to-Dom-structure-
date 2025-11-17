#!/usr/bin/env python3
"""
Basic Linux Click Example - MCP Accurate Click Server

Demonstrates the fundamental features for Linux users:
- Detecting display server (X11 vs Wayland)
- Simple element clicking using system input
- DPI detection
- Error handling for common Linux issues
- Best practices for Linux automation

Requirements:
    pip install pynput  # OR python-xlib for X11
    pip install playwright
    pip install python-xlib  # Optional, for better X11 support

Run: python3 basic_linux_click.py
"""

import sys
import time
import logging
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from playwright.sync_api import sync_playwright, Page
    from dom_structure_extractor import DOMStructureExtractor, CoordinateMapper
except ImportError as e:
    logger.error(f"Missing required dependency: {e}")
    logger.info("Install with: pip install playwright")
    sys.exit(1)

try:
    from mcp_server.platform.linux import LinuxInputSimulator, LinuxDPIHandler
except ImportError:
    logger.warning("MCP Linux modules not available, using basic pynput support")
    LinuxInputSimulator = None
    LinuxDPIHandler = None


class LinuxClickExample:
    """Demonstrates accurate clicking on Linux systems."""

    def __init__(self):
        """Initialize the example with Linux-specific setup."""
        self.simulator = None
        self.dpi_handler = None
        self.setup_platform_support()

    def setup_platform_support(self) -> None:
        """
        Initialize Linux-specific input and DPI handling.

        Best Practice: Always detect and initialize platform support early.
        """
        logger.info("Setting up Linux platform support...")

        try:
            if LinuxInputSimulator:
                self.simulator = LinuxInputSimulator()
                logger.info(f"✓ Input simulator initialized")
            else:
                logger.warning("Using fallback pynput implementation")
                self._init_pynput_fallback()
        except Exception as e:
            logger.error(f"Failed to initialize input simulator: {e}")
            self._init_pynput_fallback()

        try:
            if LinuxDPIHandler:
                self.dpi_handler = LinuxDPIHandler()
                logger.info(f"✓ DPI handler initialized")
            else:
                logger.info("DPI detection not available, assuming 96 DPI")
        except Exception as e:
            logger.warning(f"DPI handler initialization failed: {e}")

    def _init_pynput_fallback(self) -> None:
        """Fallback to pynput for input simulation."""
        try:
            from pynput import mouse, keyboard
            self.mouse_controller = mouse.Controller()
            self.keyboard_controller = keyboard.Controller()
            logger.info("✓ Pynput fallback initialized")
        except ImportError:
            logger.error("pynput not installed. Install with: pip install pynput")
            sys.exit(1)

    def get_display_server(self) -> str:
        """
        Detect the display server (X11 or Wayland).

        Best Practice: Always detect display server on Linux for compatibility.

        Returns:
            Display server type: 'x11', 'wayland', or 'unknown'
        """
        import os

        # Check environment variables
        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        if session_type in ('x11', 'wayland'):
            logger.info(f"Display server: {session_type.upper()}")
            return session_type

        # Fallback check
        if os.environ.get('WAYLAND_DISPLAY'):
            logger.info("Display server: WAYLAND")
            return 'wayland'

        if os.environ.get('DISPLAY'):
            logger.info("Display server: X11")
            return 'x11'

        logger.warning("Display server: UNKNOWN")
        return 'unknown'

    def click_at_coordinates(self, x: float, y: float, delay_ms: int = 100) -> bool:
        """
        Click at specified viewport coordinates.

        Best Practice: Always handle coordinate system correctly.
        On Linux, viewport coordinates map directly to screen coordinates.

        Args:
            x: X coordinate in viewport space
            y: Y coordinate in viewport space
            delay_ms: Delay in milliseconds before clicking

        Returns:
            True if click succeeded, False otherwise
        """
        logger.info(f"Clicking at viewport coordinates ({x:.1f}, {y:.1f})")

        try:
            # Delay before clicking (best practice for UI stability)
            time.sleep(delay_ms / 1000.0)

            # Use platform-specific simulator if available
            if self.simulator:
                self.simulator.click(int(x), int(y))
            else:
                # Fallback to pynput
                self.mouse_controller.position = (int(x), int(y))
                self.mouse_controller.click()

            logger.info("✓ Click successful")
            return True

        except Exception as e:
            logger.error(f"✗ Click failed: {e}")
            return False

    def move_mouse(self, x: float, y: float) -> bool:
        """
        Move mouse to specified coordinates without clicking.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if move succeeded, False otherwise
        """
        logger.info(f"Moving mouse to ({x:.1f}, {y:.1f})")

        try:
            if self.simulator:
                # Platform-specific mouse movement
                self.simulator.move(int(x), int(y))
            else:
                self.mouse_controller.position = (int(x), int(y))

            logger.info("✓ Mouse moved")
            return True

        except Exception as e:
            logger.error(f"✗ Mouse move failed: {e}")
            return False

    def double_click(self, x: float, y: float) -> bool:
        """
        Double-click at specified coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if double-click succeeded, False otherwise
        """
        logger.info(f"Double-clicking at ({x:.1f}, {y:.1f})")

        try:
            if self.simulator:
                self.simulator.double_click(int(x), int(y))
            else:
                self.mouse_controller.click(button='left', count=2)

            logger.info("✓ Double-click successful")
            return True

        except Exception as e:
            logger.error(f"✗ Double-click failed: {e}")
            return False

    def run_example(self) -> int:
        """
        Execute the complete example workflow.

        Returns:
            0 on success, 1 on failure
        """
        logger.info("=" * 70)
        logger.info("BASIC LINUX CLICK EXAMPLE - MCP ACCURATE CLICK SERVER")
        logger.info("=" * 70)

        # Step 1: Detect display server
        logger.info("\n[Step 1] Detecting display server...")
        display_server = self.get_display_server()

        # Step 2: Check DPI (important for coordinate accuracy)
        logger.info("\n[Step 2] Checking DPI settings...")
        if self.dpi_handler:
            try:
                monitors = self.dpi_handler.get_monitors()
                logger.info(f"✓ Detected {len(monitors)} monitor(s):")
                for i, monitor in enumerate(monitors, 1):
                    logger.info(f"  Monitor {i}: {monitor.width}x{monitor.height} @ {monitor.dpi} DPI")
            except Exception as e:
                logger.warning(f"Could not get monitor info: {e}")
        else:
            logger.info("Using default 96 DPI")

        # Step 3: Launch browser
        logger.info("\n[Step 3] Launching browser...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()

                # Navigate to test page
                test_page_path = Path(__file__).parent.parent / "test_page.html"
                if test_page_path.exists():
                    page.goto(f"file://{test_page_path}")
                    logger.info(f"✓ Loaded test page")
                else:
                    page.goto("https://example.com")
                    logger.info(f"✓ Loaded example.com")

                page.wait_for_load_state("networkidle")

                # Step 4: Extract DOM structure
                logger.info("\n[Step 4] Extracting DOM structure...")
                extractor = DOMStructureExtractor(page)
                structure = extractor.extract()
                logger.info(f"✓ Extracted {structure.total_elements} elements")
                logger.info(f"  - Visible: {structure.visible_elements}")
                logger.info(f"  - Clickable: {structure.clickable_elements}")

                # Step 5: Demonstrate clicking
                logger.info("\n[Step 5] Demonstrating clicks...")

                # Click center of viewport
                center_x = structure.viewport_width / 2
                center_y = structure.viewport_height / 2
                self.click_at_coordinates(center_x, center_y)
                time.sleep(0.5)

                # Move mouse to a different location
                self.move_mouse(100, 100)
                time.sleep(0.3)

                # Click again
                self.click_at_coordinates(100, 100)
                time.sleep(0.5)

                # Step 6: Summary
                logger.info("\n" + "=" * 70)
                logger.info("EXAMPLE COMPLETED SUCCESSFULLY")
                logger.info("=" * 70)
                logger.info(f"Display Server: {display_server.upper()}")
                logger.info(f"Viewport Size: {structure.viewport_width}x{structure.viewport_height}")
                logger.info(f"Device Pixel Ratio: {structure.device_pixel_ratio}")
                logger.info(f"Total Elements: {structure.total_elements}")

                # Keep browser open briefly
                logger.info("\nBrowser will close in 2 seconds...")
                time.sleep(2)

                browser.close()
                logger.info("✓ Browser closed")

                return 0

        except Exception as e:
            logger.error(f"✗ Example failed: {e}")
            import traceback
            traceback.print_exc()
            return 1


def main():
    """Entry point for the example."""
    example = LinuxClickExample()
    return example.run_example()


if __name__ == "__main__":
    sys.exit(main())
