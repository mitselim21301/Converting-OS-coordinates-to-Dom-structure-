#!/usr/bin/env python3
"""
Multi-Monitor Linux Example - MCP Accurate Click Server

Demonstrates multi-monitor handling on Linux:
- Detecting all connected monitors
- Querying per-monitor DPI scaling
- Handling fractional scaling (125%, 150%, 175%, etc.)
- Converting coordinates between monitors
- Clicking across monitor boundaries
- HiDPI/Retina display support

Key Linux Concepts:
- X11: Uses xrandr for monitor detection
- Wayland: Uses environment variables and D-Bus
- Fractional scaling: Supported on modern Linux (GNOME, KDE)
- Per-monitor DPI: Important for accurate coordinates

Requirements:
    pip install pynput playwright
    # For X11 advanced features:
    sudo apt-get install x11-utils xrandr  # Debian/Ubuntu
    sudo dnf install xrandr xorg-x11-utils # Fedora

Run: python3 multi_monitor_linux.py
"""

import sys
import time
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from playwright.sync_api import sync_playwright, Page
    from dom_structure_extractor import DOMStructureExtractor, CoordinateMapper
except ImportError as e:
    logger.error(f"Missing dependency: {e}")
    sys.exit(1)

try:
    from mcp_server.platform.linux import LinuxDPIHandler, LinuxInputSimulator
except ImportError:
    logger.warning("MCP Linux modules not available")
    LinuxDPIHandler = None
    LinuxInputSimulator = None


@dataclass
class MonitorLayout:
    """Represents the physical layout of monitors."""
    monitor_id: int
    width: int
    height: int
    dpi: float
    scale_factor: float
    offset_x: int
    offset_y: int
    is_primary: bool

    @property
    def display_name(self) -> str:
        """Get display name for logging."""
        primary = " (PRIMARY)" if self.is_primary else ""
        return f"Monitor {self.monitor_id}: {self.width}x{self.height} @ {self.dpi} DPI (scale: {self.scale_factor}){primary}"

    def contains_point(self, x: int, y: int) -> bool:
        """Check if monitor contains a point in screen coordinates."""
        return (self.offset_x <= x < self.offset_x + self.width and
                self.offset_y <= y < self.offset_y + self.height)

    def screen_to_monitor(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """Convert screen coordinates to monitor-relative coordinates."""
        return (screen_x - self.offset_x, screen_y - self.offset_y)

    def monitor_to_screen(self, monitor_x: int, monitor_y: int) -> Tuple[int, int]:
        """Convert monitor-relative coordinates to screen coordinates."""
        return (monitor_x + self.offset_x, monitor_y + self.offset_y)


class MultiMonitorExample:
    """Demonstrates multi-monitor support on Linux."""

    def __init__(self):
        """Initialize multi-monitor example."""
        self.dpi_handler = None
        self.input_simulator = None
        self.monitors: List[MonitorLayout] = []
        self.setup()

    def setup(self) -> None:
        """Initialize platform support."""
        logger.info("Setting up multi-monitor support...")

        try:
            if LinuxDPIHandler:
                self.dpi_handler = LinuxDPIHandler()
                logger.info("✓ DPI handler initialized")
            else:
                logger.warning("DPI handler not available")
        except Exception as e:
            logger.warning(f"DPI handler failed: {e}")

        try:
            if LinuxInputSimulator:
                self.input_simulator = LinuxInputSimulator()
                logger.info("✓ Input simulator initialized")
        except Exception as e:
            logger.warning(f"Input simulator failed: {e}")

    def detect_monitors(self) -> bool:
        """
        Detect all connected monitors.

        Returns:
            True if monitors detected, False otherwise
        """
        logger.info("\n[Monitor Detection]")

        if not self.dpi_handler:
            logger.warning("DPI handler not available, using fallback detection")
            return self._detect_monitors_fallback()

        try:
            monitor_info_list = self.dpi_handler.get_monitors()

            if not monitor_info_list:
                logger.error("No monitors detected")
                return False

            logger.info(f"✓ Detected {len(monitor_info_list)} monitor(s):\n")

            for i, info in enumerate(monitor_info_list, 1):
                monitor = MonitorLayout(
                    monitor_id=i,
                    width=info.width,
                    height=info.height,
                    dpi=info.dpi,
                    scale_factor=info.dpi / 96.0,  # 96 DPI is baseline
                    offset_x=info.x if hasattr(info, 'x') else 0,
                    offset_y=info.y if hasattr(info, 'y') else 0,
                    is_primary=i == 1  # First monitor is usually primary
                )

                self.monitors.append(monitor)
                logger.info(f"  {monitor.display_name}")

                # Show scaling details
                if monitor.scale_factor != 1.0:
                    logger.info(f"    → Scaling active: {monitor.scale_factor:.2f}x "
                              f"({monitor.scale_factor * 100:.0f}%)")

            return True

        except Exception as e:
            logger.error(f"Failed to detect monitors: {e}")
            return self._detect_monitors_fallback()

    def _detect_monitors_fallback(self) -> bool:
        """Fallback monitor detection using xrandr."""
        import subprocess
        import os

        try:
            # Check if we're on X11
            if not os.environ.get('DISPLAY'):
                logger.warning("Not on X11 display")
                # Create a default monitor
                self.monitors = [MonitorLayout(
                    monitor_id=1,
                    width=1920,
                    height=1080,
                    dpi=96,
                    scale_factor=1.0,
                    offset_x=0,
                    offset_y=0,
                    is_primary=True
                )]
                logger.info("Using default monitor: 1920x1080 @ 96 DPI")
                return True

            # Try xrandr
            result = subprocess.run(['xrandr', '--query'], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                logger.warning("xrandr command failed")
                return False

            # Parse xrandr output (basic parsing)
            # Format: HDMI-1 connected 1920x1080+0+0
            import re
            pattern = r'(\S+)\s+connected\s+(\d+)x(\d+)\+(\d+)\+(\d+)'

            for match in re.finditer(pattern, result.stdout):
                name, width, height, offset_x, offset_y = match.groups()
                monitor = MonitorLayout(
                    monitor_id=len(self.monitors) + 1,
                    width=int(width),
                    height=int(height),
                    dpi=96,  # Default, cannot detect without DPI handler
                    scale_factor=1.0,
                    offset_x=int(offset_x),
                    offset_y=int(offset_y),
                    is_primary=len(self.monitors) == 0
                )
                self.monitors.append(monitor)
                logger.info(f"  {monitor.display_name}")

            return len(self.monitors) > 0

        except Exception as e:
            logger.warning(f"Fallback detection failed: {e}")
            # Create default
            self.monitors = [MonitorLayout(
                monitor_id=1,
                width=1920,
                height=1080,
                dpi=96,
                scale_factor=1.0,
                offset_x=0,
                offset_y=0,
                is_primary=True
            )]
            return True

    def find_monitor(self, x: int, y: int) -> Optional[MonitorLayout]:
        """
        Find which monitor contains the given screen coordinates.

        Args:
            x: Screen X coordinate
            y: Screen Y coordinate

        Returns:
            MonitorLayout if found, None otherwise
        """
        for monitor in self.monitors:
            if monitor.contains_point(x, y):
                return monitor
        return None

    def click_on_monitor(self, monitor_id: int, x: int, y: int) -> bool:
        """
        Click at coordinates relative to a specific monitor.

        Args:
            monitor_id: Monitor ID (1-based)
            x: X coordinate relative to monitor
            y: Y coordinate relative to monitor

        Returns:
            True if click succeeded, False otherwise
        """
        if monitor_id < 1 or monitor_id > len(self.monitors):
            logger.error(f"Invalid monitor ID: {monitor_id}")
            return False

        monitor = self.monitors[monitor_id - 1]

        # Convert monitor-relative to screen coordinates
        screen_x, screen_y = monitor.monitor_to_screen(x, y)

        logger.info(f"Clicking on {monitor.display_name}")
        logger.info(f"  Monitor coords: ({x}, {y}) -> Screen coords: ({screen_x}, {screen_y})")

        try:
            if self.input_simulator:
                self.input_simulator.click(int(screen_x), int(screen_y))
            else:
                from pynput import mouse
                controller = mouse.Controller()
                controller.position = (int(screen_x), int(screen_y))
                controller.click()

            logger.info("✓ Click successful")
            return True

        except Exception as e:
            logger.error(f"✗ Click failed: {e}")
            return False

    def demonstrate_fractional_scaling(self) -> None:
        """
        Demonstrate handling of fractional scaling.

        Linux modern desktops support 125%, 150%, 175% scaling.
        This affects coordinate accuracy significantly.
        """
        logger.info("\n[Fractional Scaling Analysis]")

        if not self.monitors:
            logger.warning("No monitors available")
            return

        for monitor in self.monitors:
            if monitor.scale_factor != 1.0:
                logger.info(f"\n{monitor.display_name}")
                logger.info(f"  Scale factor: {monitor.scale_factor:.2f}x")
                logger.info(f"  Scaling type: {'Fractional' if monitor.scale_factor % 1 != 0 else 'Integer'}")

                # Example: How scaling affects coordinates
                example_x, example_y = 100, 100
                logger.info(f"\n  Example - Click at logical (100, 100):")
                logger.info(f"    Logical (DPI-adjusted): (100, 100)")
                logger.info(f"    Physical (screen): ({example_x * monitor.scale_factor:.0f}, "
                          f"{example_y * monitor.scale_factor:.0f})")
            else:
                logger.info(f"\n{monitor.display_name}")
                logger.info(f"  No scaling (100%)")

    def run_example(self) -> int:
        """Execute the complete multi-monitor example."""
        logger.info("=" * 70)
        logger.info("MULTI-MONITOR LINUX EXAMPLE - MCP ACCURATE CLICK SERVER")
        logger.info("=" * 70)

        # Step 1: Detect monitors
        if not self.detect_monitors():
            logger.error("Failed to detect monitors")
            return 1

        # Step 2: Analyze scaling
        self.demonstrate_fractional_scaling()

        # Step 3: Test clicking on different monitors
        if len(self.monitors) > 1:
            logger.info("\n[Cross-Monitor Clicking Test]")
            logger.info("Testing clicks on each monitor...")

            for i, monitor in enumerate(self.monitors, 1):
                # Click center of each monitor
                center_x = monitor.width // 2
                center_y = monitor.height // 2
                self.click_on_monitor(i, center_x, center_y)
                time.sleep(0.3)
        else:
            logger.info("\n[Single Monitor System]")
            if self.monitors:
                monitor = self.monitors[0]
                logger.info(f"Single monitor detected: {monitor.width}x{monitor.height}")
                self.click_on_monitor(1, monitor.width // 2, monitor.height // 2)

        # Step 4: Launch browser on primary monitor
        logger.info("\n[Browser Automation]")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()

                test_page_path = Path(__file__).parent.parent / "test_page.html"
                if test_page_path.exists():
                    page.goto(f"file://{test_page_path}")
                else:
                    page.goto("https://example.com")

                page.wait_for_load_state("networkidle")

                extractor = DOMStructureExtractor(page)
                structure = extractor.extract()

                logger.info(f"✓ Loaded page on primary monitor")
                logger.info(f"  Viewport: {structure.viewport_width}x{structure.viewport_height}")
                logger.info(f"  Device Pixel Ratio: {structure.device_pixel_ratio}")

                logger.info("\nBrowser will close in 2 seconds...")
                time.sleep(2)
                browser.close()

        except Exception as e:
            logger.error(f"Browser automation failed: {e}")
            import traceback
            traceback.print_exc()

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("MULTI-MONITOR EXAMPLE COMPLETED")
        logger.info("=" * 70)
        logger.info(f"Total Monitors: {len(self.monitors)}")

        if self.monitors:
            total_width = max(m.offset_x + m.width for m in self.monitors)
            total_height = max(m.offset_y + m.height for m in self.monitors)
            logger.info(f"Total Screen Area: {total_width}x{total_height}")

        return 0


def main():
    """Entry point."""
    example = MultiMonitorExample()
    return example.run_example()


if __name__ == "__main__":
    sys.exit(main())
