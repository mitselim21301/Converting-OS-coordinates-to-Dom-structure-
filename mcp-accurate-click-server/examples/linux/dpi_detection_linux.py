#!/usr/bin/env python3
"""
DPI Detection Linux Example - MCP Accurate Click Server

Demonstrates DPI detection and handling on Linux:
- Querying system DPI settings
- Per-monitor DPI detection
- Fractional scaling (125%, 150%, 175%)
- HiDPI/Retina display support
- Converting coordinates based on DPI
- Handling dynamic DPI changes

Key Linux DPI Concepts:
- X11: Uses xrandr for monitor DPI
  * Physical DPI = 96 DPI * scale factor
  * Scale factor from xrandr output

- Wayland: Uses environment variables
  * GDK_SCALE (GNOME) - 1, 2, or 3
  * QT_SCALE_FACTOR (KDE) - 0.5 to 3.0
  * FRACTIONAL scaling for modern compositors

- Coordinate Accuracy:
  * Logical coordinates: What apps see (DPI-adjusted)
  * Physical coordinates: Actual screen pixels
  * Proper mapping is CRITICAL for accurate clicking

Requirements:
    pip install pynput playwright
    # For best DPI detection:
    sudo apt-get install x11-utils xrandr  # X11 systems

Run: python3 dpi_detection_linux.py
"""

import sys
import os
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from playwright.sync_api import sync_playwright, Page
except ImportError as e:
    logger.error(f"Missing dependency: {e}")
    sys.exit(1)

try:
    from mcp_server.platform.linux import LinuxDPIHandler
except ImportError:
    logger.warning("MCP Linux DPI handler not available")
    LinuxDPIHandler = None


@dataclass
class DPIInfo:
    """Container for DPI information."""
    name: str
    dpi: float
    scale_factor: float
    display_type: str
    physical_dpi: Optional[float] = None

    def __str__(self) -> str:
        scale_pct = int(self.scale_factor * 100)
        result = f"{self.name}: {self.dpi:.1f} DPI ({scale_pct}% scale)"

        if self.physical_dpi and self.physical_dpi != self.dpi:
            result += f" [Physical: {self.physical_dpi:.1f}]"

        result += f" [{self.display_type}]"
        return result

    @property
    def is_hidpi(self) -> bool:
        """Check if this is HiDPI/Retina display."""
        return self.dpi > 96 or self.scale_factor > 1.0


class DPIDetectionExample:
    """Demonstrates DPI detection and handling on Linux."""

    # Standard baseline DPI
    BASELINE_DPI = 96

    # Common DPI values and what they mean
    COMMON_DPI_MAP = {
        72: "Low DPI (older displays)",
        96: "Standard DPI (baseline, 100%)",
        120: "125% scaling",
        144: "150% scaling",
        168: "175% scaling",
        192: "200% scaling (HiDPI)",
    }

    def __init__(self):
        """Initialize DPI detection example."""
        self.dpi_handler = None
        self.environment_info: Dict[str, str] = {}
        self.monitors_dpi: List[DPIInfo] = []

        self._init_dpi_handler()
        self._collect_environment_info()

    def _init_dpi_handler(self) -> None:
        """Initialize DPI handler."""
        logger.info("Initializing DPI handler...")

        try:
            if LinuxDPIHandler:
                self.dpi_handler = LinuxDPIHandler()
                logger.info("✓ DPI handler initialized")
            else:
                logger.warning("DPI handler not available, using environment-based detection")
        except Exception as e:
            logger.warning(f"DPI handler initialization failed: {e}")

    def _collect_environment_info(self) -> None:
        """
        Collect relevant environment variables for DPI detection.

        Best Practice: Always check environment variables first on Linux.
        """
        logger.info("\n[Environment Variables for DPI]")

        relevant_vars = [
            'XDG_SESSION_TYPE',
            'DISPLAY',
            'WAYLAND_DISPLAY',
            'GDK_SCALE',
            'GDK_DPI_SCALE',
            'QT_SCALE_FACTOR',
            'QT_DPI',
            'QT_FONT_DPI',
            'XCURSOR_SIZE',
        ]

        logger.info("Relevant environment variables:")
        for var in relevant_vars:
            value = os.environ.get(var)
            if value:
                self.environment_info[var] = value
                logger.info(f"  {var}={value}")

        if not self.environment_info:
            logger.info("  (no relevant variables set)")

    def detect_display_server(self) -> str:
        """
        Detect display server and log specifics.

        Returns:
            Display server type: 'x11', 'wayland', or 'unknown'
        """
        logger.info("\n[Display Server Detection]")

        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        if session_type in ('x11', 'wayland'):
            logger.info(f"✓ Display Server: {session_type.upper()}")
            return session_type

        if os.environ.get('WAYLAND_DISPLAY'):
            logger.info("✓ Display Server: WAYLAND (from WAYLAND_DISPLAY)")
            return 'wayland'

        if os.environ.get('DISPLAY'):
            logger.info("✓ Display Server: X11 (from DISPLAY)")
            return 'x11'

        logger.warning("✗ Display Server: UNKNOWN")
        return 'unknown'

    def detect_monitors_dpi(self) -> bool:
        """
        Detect DPI for all monitors.

        Returns:
            True if detection succeeded
        """
        logger.info("\n[Monitor DPI Detection]")

        if not self.dpi_handler:
            logger.warning("DPI handler not available, using fallback detection")
            return self._detect_dpi_fallback()

        try:
            monitor_list = self.dpi_handler.get_monitors()

            if not monitor_list:
                logger.error("No monitors detected")
                return False

            logger.info(f"✓ Detected {len(monitor_list)} monitor(s):")

            for i, monitor_info in enumerate(monitor_list, 1):
                dpi_info = DPIInfo(
                    name=f"Monitor {i}",
                    dpi=monitor_info.dpi,
                    scale_factor=monitor_info.dpi / self.BASELINE_DPI,
                    display_type=self._get_display_type(monitor_info.dpi)
                )
                self.monitors_dpi.append(dpi_info)

                logger.info(f"\n  {dpi_info}")
                logger.info(f"    Resolution: {monitor_info.width}x{monitor_info.height}")

                if dpi_info.is_hidpi:
                    logger.info(f"    → HiDPI/Retina display detected")

            return True

        except Exception as e:
            logger.error(f"DPI detection failed: {e}")
            return self._detect_dpi_fallback()

    def _detect_dpi_fallback(self) -> bool:
        """
        Fallback DPI detection using xrandr and environment variables.

        Returns:
            True if at least one DPI was detected
        """
        try:
            # Try xrandr first
            if os.environ.get('DISPLAY'):
                return self._detect_dpi_xrandr()

            # Try environment variables
            dpi = self._detect_dpi_environment()
            if dpi:
                dpi_info = DPIInfo(
                    name="System DPI",
                    dpi=dpi,
                    scale_factor=dpi / self.BASELINE_DPI,
                    display_type=self._get_display_type(dpi)
                )
                self.monitors_dpi.append(dpi_info)
                logger.info(f"✓ {dpi_info}")
                return True

            # Default
            logger.warning("Using default 96 DPI")
            return False

        except Exception as e:
            logger.error(f"Fallback detection failed: {e}")
            return False

    def _detect_dpi_xrandr(self) -> bool:
        """
        Detect DPI using xrandr command (X11).

        Returns:
            True if successful
        """
        try:
            result = subprocess.run(['xrandr', '--query'],
                                  capture_output=True, text=True, timeout=5)

            if result.returncode != 0:
                return False

            # Parse xrandr output for DPI information
            # xrandr outputs physical dimensions, we need to calculate DPI
            import re

            # Look for lines like: "HDMI-1 connected (normal left inverted right x axis y axis)"
            dpi_detected = False

            for line in result.stdout.split('\n'):
                if 'connected' in line and 'mm' in line:
                    # Extract physical dimensions
                    match = re.search(r'(\d+)mm x (\d+)mm', line)
                    if match:
                        width_mm, height_mm = int(match.group(1)), int(match.group(2))
                        # This would need resolution to calculate DPI
                        # Approximate: if physical dimensions < 200mm, likely HiDPI
                        estimated_dpi = 192 if width_mm < 200 else 96
                        dpi_info = DPIInfo(
                            name="Estimated (from physical)",
                            dpi=float(estimated_dpi),
                            scale_factor=estimated_dpi / self.BASELINE_DPI,
                            display_type=self._get_display_type(estimated_dpi)
                        )
                        self.monitors_dpi.append(dpi_info)
                        logger.info(f"✓ {dpi_info}")
                        dpi_detected = True

            return dpi_detected

        except Exception as e:
            logger.debug(f"xrandr detection failed: {e}")
            return False

    def _detect_dpi_environment(self) -> Optional[float]:
        """
        Detect DPI from environment variables.

        Returns:
            DPI value or None
        """
        # Check GDK_SCALE (GNOME)
        if gdk_scale := os.environ.get('GDK_SCALE'):
            try:
                scale = float(gdk_scale)
                return self.BASELINE_DPI * scale
            except ValueError:
                pass

        # Check GDK_DPI_SCALE
        if gdk_dpi := os.environ.get('GDK_DPI_SCALE'):
            try:
                scale = float(gdk_dpi)
                return self.BASELINE_DPI * scale
            except ValueError:
                pass

        # Check QT_SCALE_FACTOR (KDE)
        if qt_scale := os.environ.get('QT_SCALE_FACTOR'):
            try:
                scale = float(qt_scale)
                return self.BASELINE_DPI * scale
            except ValueError:
                pass

        return None

    @staticmethod
    def _get_display_type(dpi: float) -> str:
        """
        Get display type description based on DPI.

        Args:
            dpi: DPI value

        Returns:
            Display type string
        """
        if dpi <= 96:
            return "Standard"
        elif dpi <= 120:
            return "125% Scaling"
        elif dpi <= 144:
            return "150% Scaling"
        elif dpi <= 168:
            return "175% Scaling"
        else:
            return "HiDPI/Retina"

    def demonstrate_coordinate_conversion(self) -> None:
        """
        Demonstrate how DPI affects coordinate conversion.

        Best Practice: Show the importance of DPI-aware coordinates.
        """
        logger.info("\n[Coordinate Conversion Examples]")

        if not self.monitors_dpi:
            logger.warning("No monitors detected, cannot demonstrate")
            return

        # Example coordinates to convert
        logical_x, logical_y = 100, 100

        for dpi_info in self.monitors_dpi:
            logger.info(f"\n{dpi_info.name}:")
            logger.info(f"  Logical coordinate (app sees): ({logical_x}, {logical_y})")

            # Convert logical to physical
            physical_x = logical_x * dpi_info.scale_factor
            physical_y = logical_y * dpi_info.scale_factor

            logger.info(f"  Physical coordinate (screen): ({physical_x:.1f}, {physical_y:.1f})")

            if dpi_info.scale_factor != 1.0:
                logger.info(f"  Conversion factor: {dpi_info.scale_factor:.2f}x")

    def test_browser_dpi_awareness(self) -> None:
        """
        Test DPI awareness in browser.

        Shows how browsers handle DPI scaling.
        """
        logger.info("\n[Browser DPI Awareness Test]")

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()

                # Create a simple test page
                test_html = """
                <html>
                <body style="margin: 20px; font-family: monospace;">
                    <h1>DPI Awareness Test</h1>
                    <p>Device Pixel Ratio: <span id="dpr"></span></p>
                    <p>Viewport Size: <span id="viewport"></span></p>
                    <p>Screen Size: <span id="screen"></span></p>
                    <div id="box" style="width: 100px; height: 100px; background: blue; margin: 20px;"></div>
                    <script>
                        document.getElementById('dpr').textContent = window.devicePixelRatio;
                        document.getElementById('viewport').textContent =
                            window.innerWidth + ' x ' + window.innerHeight;
                        document.getElementById('screen').textContent =
                            screen.width + ' x ' + screen.height;
                    </script>
                </body>
                </html>
                """

                page.set_content(test_html)

                # Extract browser info
                dpr = page.evaluate("() => window.devicePixelRatio")
                viewport = page.viewport()

                logger.info(f"✓ Browser DPI (Device Pixel Ratio): {dpr}")
                if viewport:
                    logger.info(f"✓ Viewport: {viewport['width']}x{viewport['height']}")

                logger.info("\nBrowser will close in 2 seconds...")
                import time
                time.sleep(2)

                browser.close()

        except Exception as e:
            logger.warning(f"Browser test skipped: {e}")

    def run_example(self) -> int:
        """Execute the complete DPI detection example."""
        logger.info("=" * 70)
        logger.info("DPI DETECTION LINUX EXAMPLE - MCP ACCURATE CLICK SERVER")
        logger.info("=" * 70)

        # Step 1: Detect display server
        display_server = self.detect_display_server()

        # Step 2: Detect monitor DPI
        if not self.detect_monitors_dpi():
            logger.warning("DPI detection partially failed")

        # Step 3: Demonstrate coordinate conversion
        self.demonstrate_coordinate_conversion()

        # Step 4: Test browser DPI awareness
        self.test_browser_dpi_awareness()

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("DPI DETECTION EXAMPLE COMPLETED")
        logger.info("=" * 70)
        logger.info(f"Display Server: {display_server.upper()}")
        logger.info(f"Monitors Detected: {len(self.monitors_dpi)}")

        if self.monitors_dpi:
            hidpi_count = sum(1 for m in self.monitors_dpi if m.is_hidpi)
            logger.info(f"HiDPI Monitors: {hidpi_count}")

        return 0


def main():
    """Entry point."""
    example = DPIDetectionExample()
    return example.run_example()


if __name__ == "__main__":
    sys.exit(main())
