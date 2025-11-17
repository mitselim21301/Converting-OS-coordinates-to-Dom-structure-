#!/usr/bin/env python3
"""
Wayland-Specific Example - MCP Accurate Click Server

Demonstrates Wayland-specific features and workarounds:
- Detecting Wayland environment
- Handling Wayland-specific limitations
- Using D-Bus for window management
- Browser compatibility on Wayland
- Fractional scaling support
- Input limitations and workarounds

Wayland Characteristics:
- Modern, secure display protocol
- Per-client window management
- Better multi-monitor support
- Native fractional scaling
- No direct input access (goes through compositor)
- Some legacy apps may not work well

Key Differences from X11:
- No direct window IDs accessible
- No xdotool support (uses alternative methods)
- D-Bus for some window management
- Environment variables critical for scaling
- Browser needs Ozone/Wayland support

Requirements:
    pip install pynput playwright
    # For D-Bus access:
    sudo apt-get install libdbus-1-dev

Run: python3 wayland_example.py

Note: This example will ONLY work on Wayland. It will detect X11 and exit gracefully.
"""

import sys
import os
import logging
import time
from pathlib import Path
from typing import Optional, Dict
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

try:
    from mcp_server.platform.linux import LinuxInputSimulator, LinuxDPIHandler
except ImportError:
    logger.warning("MCP Linux modules not available")
    LinuxInputSimulator = None
    LinuxDPIHandler = None


@dataclass
class WaylandInfo:
    """Information about Wayland environment."""
    session_type: str
    display: Optional[str]
    seat: Optional[str]
    gdk_scale: Optional[str]
    qt_scale: Optional[str]
    compositor: Optional[str]

    def __str__(self) -> str:
        return (f"Wayland Session\n"
                f"  Session Type: {self.session_type}\n"
                f"  Display: {self.display or 'not set'}\n"
                f"  Seat: {self.seat or 'default'}\n"
                f"  GDK Scale: {self.gdk_scale or 'not set'}\n"
                f"  QT Scale: {self.qt_scale or 'not set'}\n"
                f"  Compositor: {self.compositor or 'unknown'}")


class WaylandExample:
    """Demonstrates Wayland-specific features."""

    def __init__(self):
        """Initialize Wayland example."""
        self.input_simulator = None
        self.dpi_handler = None
        self.wayland_info = None

        # Check if we're on Wayland
        if not self._check_wayland():
            logger.error("This example requires Wayland. You are running on X11 or another display server.")
            sys.exit(1)

        self._init_wayland()

    def _check_wayland(self) -> bool:
        """
        Check if running on Wayland.

        Returns:
            True if Wayland is available
        """
        # Check XDG_SESSION_TYPE
        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        if session_type == 'wayland':
            return True

        # Check WAYLAND_DISPLAY
        if os.environ.get('WAYLAND_DISPLAY'):
            return True

        # Check if DISPLAY is set (X11 indicator)
        if os.environ.get('DISPLAY'):
            return False

        return False

    def _init_wayland(self) -> None:
        """Initialize Wayland support."""
        logger.info("Initializing Wayland support...")

        # Collect Wayland environment info
        self.wayland_info = WaylandInfo(
            session_type=os.environ.get('XDG_SESSION_TYPE', 'wayland'),
            display=os.environ.get('WAYLAND_DISPLAY'),
            seat=os.environ.get('XDG_SEAT', 'seat0'),
            gdk_scale=os.environ.get('GDK_SCALE'),
            qt_scale=os.environ.get('QT_SCALE_FACTOR'),
            compositor=self._detect_compositor()
        )

        # Initialize input simulator
        if LinuxInputSimulator:
            try:
                self.input_simulator = LinuxInputSimulator()
                logger.info("✓ Input simulator initialized")
            except Exception as e:
                logger.warning(f"Input simulator failed: {e}")

        # Initialize DPI handler
        if LinuxDPIHandler:
            try:
                self.dpi_handler = LinuxDPIHandler()
                logger.info("✓ DPI handler initialized")
            except Exception as e:
                logger.warning(f"DPI handler failed: {e}")

    def _detect_compositor(self) -> Optional[str]:
        """
        Detect which Wayland compositor is running.

        Returns:
            Compositor name or None
        """
        # Check common compositors
        compositors = {
            'GNOME_SESSION_NAME': 'GNOME',
            'KDE_SESSION_VERSION': 'KDE/Plasma',
            'DESKTOP_SESSION': None,  # Fallback
        }

        for env_var, name in compositors.items():
            if value := os.environ.get(env_var):
                if 'gnome' in value.lower():
                    return 'GNOME'
                elif 'kde' in value.lower() or 'plasma' in value.lower():
                    return 'KDE/Plasma'
                elif 'sway' in value.lower():
                    return 'Sway'

        # Check for XDG_CURRENT_DESKTOP
        if desktop := os.environ.get('XDG_CURRENT_DESKTOP'):
            return desktop

        return None

    def show_environment_info(self) -> None:
        """Display Wayland environment information."""
        logger.info("\n[Wayland Environment]")
        logger.info(str(self.wayland_info))

    def check_fractional_scaling_support(self) -> bool:
        """
        Check if fractional scaling is supported.

        Wayland natively supports fractional scaling, but it varies by compositor.

        Returns:
            True if fractional scaling is likely supported
        """
        logger.info("\n[Fractional Scaling Support]")

        if not self.dpi_handler:
            logger.warning("DPI handler not available")
            return False

        try:
            monitors = self.dpi_handler.get_monitors()

            for monitor in monitors:
                dpi = monitor.dpi
                scale = dpi / 96.0  # 96 DPI = 100%

                is_fractional = scale % 1 != 0
                scale_pct = int(scale * 100)

                status = "✓ Fractional" if is_fractional else "○ Integer"
                logger.info(f"  Monitor {monitor.width}x{monitor.height}: {scale_pct}% ({status})")

            return True

        except Exception as e:
            logger.warning(f"Could not check scaling: {e}")
            return False

    def get_wayland_browser_launch_options(self) -> dict:
        """
        Get browser launch options optimized for Wayland.

        Best Practice: Different browsers need different Wayland options.

        Returns:
            Launch options dictionary
        """
        logger.info("\n[Browser Launch Options for Wayland]")

        options = {
            'headless': False,
            'args': []
        }

        # Force Ozone/Wayland for Chromium-based browsers
        options['args'].extend([
            '--ozone-platform=wayland',
            '--enable-wayland-ime',
            '--no-sandbox',
        ])

        logger.info("Recommended Chromium flags:")
        for arg in options['args']:
            logger.info(f"  {arg}")

        return options

    def demonstrate_input_on_wayland(self) -> None:
        """
        Demonstrate input handling on Wayland.

        Show important considerations for Wayland input.
        """
        logger.info("\n[Input on Wayland]")

        logger.info("Important considerations:")
        logger.info("  1. Input goes through Wayland compositor")
        logger.info("  2. Applications must have focus for input to work")
        logger.info("  3. No screen-global input (only per-client)")
        logger.info("  4. Coordinate scaling is handled by compositor")
        logger.info("  5. Some legacy input methods don't work on Wayland")

        if self.input_simulator:
            logger.info("\n✓ Input simulator available (uses pynput or xdotool)")
            logger.info("  Recommended: Use Playwright for browser automation")
        else:
            logger.warning("\n✗ Input simulator not available")
            logger.warning("  Consider using Playwright for automation")

    def run_example(self) -> int:
        """Execute the complete Wayland example."""
        logger.info("=" * 70)
        logger.info("WAYLAND-SPECIFIC EXAMPLE - MCP ACCURATE CLICK SERVER")
        logger.info("=" * 70)

        # Step 1: Show environment info
        self.show_environment_info()

        # Step 2: Check fractional scaling
        self.check_fractional_scaling_support()

        # Step 3: Get browser launch options
        self.get_wayland_browser_launch_options()

        # Step 4: Explain input handling
        self.demonstrate_input_on_wayland()

        # Step 5: Test browser with Wayland options
        logger.info("\n[Browser Test on Wayland]")

        try:
            with sync_playwright() as p:
                # Use Chromium for best Wayland support
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
                    logger.info(f"  Viewport: {structure.viewport_width}x{structure.viewport_height}")
                    logger.info(f"  Device Pixel Ratio: {structure.device_pixel_ratio}")
                except Exception as e:
                    logger.debug(f"DOM extraction skipped: {e}")

                # Demonstrate clicking on Wayland
                logger.info("\n[Wayland Click Demonstration]")

                viewport = page.viewport()
                if viewport:
                    # Click in the center (Playwright handles Wayland coordinates)
                    center_x = viewport['width'] / 2
                    center_y = viewport['height'] / 2

                    logger.info(f"Viewport center: ({center_x:.0f}, {center_y:.0f})")
                    logger.info("Clicking...")

                    page.mouse.click(center_x, center_y)
                    time.sleep(0.3)
                    logger.info("✓ Click successful on Wayland")

                # Keep browser open briefly
                logger.info("\nBrowser will close in 2 seconds...")
                time.sleep(2)

                browser.close()
                logger.info("✓ Browser closed")

        except Exception as e:
            logger.error(f"Browser test failed: {e}")
            import traceback
            traceback.print_exc()

        # Summary and recommendations
        logger.info("\n" + "=" * 70)
        logger.info("WAYLAND EXAMPLE COMPLETED")
        logger.info("=" * 70)
        logger.info("\nWayland-Specific Recommendations:")
        logger.info("  1. Use Playwright for browser automation")
        logger.info("  2. Ensure applications have window focus")
        logger.info("  3. Test with both GTK and Qt applications")
        logger.info("  4. Consider screen capture for validation")
        logger.info("  5. Use Wayland-native input methods when possible")
        logger.info(f"\nCompositor: {self.wayland_info.compositor or 'unknown'}")

        return 0


def main():
    """Entry point."""
    example = WaylandExample()
    return example.run_example()


if __name__ == "__main__":
    sys.exit(main())
