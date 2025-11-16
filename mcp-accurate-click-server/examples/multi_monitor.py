#!/usr/bin/env python3
"""
Multi-Monitor Example - MCP Accurate Click Server

This example demonstrates handling multi-monitor setups:
- Detecting monitor configurations
- Per-monitor coordinate transformations
- DPI scaling awareness
- Cross-monitor window tracking
- Monitor-specific calibration
- Coordinate system conversions

Run this example to understand multi-monitor automation patterns.
"""

import sys
import time
import platform
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.sync_api import sync_playwright, Page, Browser
from dom_structure_extractor import DOMStructureExtractor, CoordinateMapper
from os_to_dom_transformer import OSToDOM_Transformer
import numpy as np


@dataclass
class Monitor:
    """Represents a physical monitor."""
    id: int
    name: str
    x: int  # Screen X coordinate of top-left corner
    y: int  # Screen Y coordinate of top-left corner
    width: int
    height: int
    dpi_scale: float
    is_primary: bool

    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """Get monitor bounds (x, y, width, height)."""
        return (self.x, self.y, self.width, self.height)

    @property
    def center(self) -> Tuple[int, int]:
        """Get monitor center coordinates."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is within this monitor."""
        return (self.x <= x < self.x + self.width and
                self.y <= y < self.y + self.height)


class MonitorManager:
    """
    Manages multiple monitors and coordinate transformations.

    Features:
    - Monitor detection and configuration
    - Per-monitor coordinate transformations
    - DPI scaling handling
    - Automatic monitor selection based on coordinates
    """

    def __init__(self):
        """Initialize monitor manager."""
        self.monitors: List[Monitor] = []
        self.transformers: Dict[int, OSToDOM_Transformer] = {}
        self.current_monitor: Optional[Monitor] = None

    def detect_monitors(self) -> List[Monitor]:
        """
        Detect all connected monitors.

        Note: This is a simplified simulation. In production, you would use
        platform-specific APIs:
        - Windows: EnumDisplayMonitors, GetMonitorInfo
        - macOS: NSScreen APIs
        - Linux: xrandr or similar

        Returns:
            List of detected monitors
        """
        print("Detecting monitors...")

        # Simulate monitor detection
        # In a real implementation, use platform-specific APIs
        if platform.system() == "Windows":
            # Would use: ctypes.windll.user32.EnumDisplayMonitors
            pass
        elif platform.system() == "Darwin":  # macOS
            # Would use: PyObjC NSScreen.screens()
            pass
        elif platform.system() == "Linux":
            # Would use: subprocess + xrandr parsing
            pass

        # For this example, simulate a dual-monitor setup
        self.monitors = [
            Monitor(
                id=1,
                name="Primary Monitor",
                x=0,
                y=0,
                width=1920,
                height=1080,
                dpi_scale=1.0,
                is_primary=True
            ),
            Monitor(
                id=2,
                name="Secondary Monitor",
                x=1920,  # To the right of primary
                y=0,
                width=2560,
                height=1440,
                dpi_scale=1.25,  # Higher DPI
                is_primary=False
            )
        ]

        print(f"✓ Detected {len(self.monitors)} monitor(s):")
        for mon in self.monitors:
            print(f"  {mon.id}. {mon.name}")
            print(f"     Position: ({mon.x}, {mon.y})")
            print(f"     Size: {mon.width}x{mon.height}")
            print(f"     DPI Scale: {mon.dpi_scale}")
            print(f"     Primary: {mon.is_primary}")

        return self.monitors

    def get_monitor_at_position(self, x: int, y: int) -> Optional[Monitor]:
        """
        Determine which monitor contains the given screen coordinates.

        Args:
            x: Screen X coordinate
            y: Screen Y coordinate

        Returns:
            Monitor containing the point, or None
        """
        for monitor in self.monitors:
            if monitor.contains_point(x, y):
                return monitor
        return None

    def get_primary_monitor(self) -> Optional[Monitor]:
        """Get the primary monitor."""
        for monitor in self.monitors:
            if monitor.is_primary:
                return monitor
        return self.monitors[0] if self.monitors else None

    def screen_to_monitor_coordinates(
        self,
        screen_x: int,
        screen_y: int,
        monitor: Monitor
    ) -> Tuple[int, int]:
        """
        Convert screen coordinates to monitor-local coordinates.

        Args:
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate
            monitor: Target monitor

        Returns:
            (x, y) in monitor-local coordinates
        """
        return (
            screen_x - monitor.x,
            screen_y - monitor.y
        )

    def monitor_to_screen_coordinates(
        self,
        monitor_x: int,
        monitor_y: int,
        monitor: Monitor
    ) -> Tuple[int, int]:
        """
        Convert monitor-local coordinates to screen coordinates.

        Args:
            monitor_x: Monitor-local X coordinate
            monitor_y: Monitor-local Y coordinate
            monitor: Source monitor

        Returns:
            (x, y) in screen coordinates
        """
        return (
            monitor_x + monitor.x,
            monitor_y + monitor.y
        )

    def calibrate_monitor(
        self,
        monitor: Monitor,
        page: Page,
        num_points: int = 9
    ) -> bool:
        """
        Calibrate coordinate transformation for a specific monitor.

        Args:
            monitor: Monitor to calibrate
            page: Playwright page on this monitor
            num_points: Number of calibration points

        Returns:
            True if calibration succeeded, False otherwise
        """
        print(f"\nCalibrating monitor: {monitor.name}")
        print(f"  Position: ({monitor.x}, {monitor.y})")
        print(f"  Size: {monitor.width}x{monitor.height}")
        print(f"  DPI Scale: {monitor.dpi_scale}")

        try:
            # Extract DOM structure
            extractor = DOMStructureExtractor(page)
            structure = extractor.extract()

            # Generate calibration points (grid pattern)
            grid_size = int(np.ceil(np.sqrt(num_points)))

            # DOM coordinates (viewport-local)
            dom_points = []
            for i in range(grid_size):
                for j in range(grid_size):
                    if len(dom_points) >= num_points:
                        break
                    x = (i + 1) * structure.viewport_width / (grid_size + 1)
                    y = (j + 1) * structure.viewport_height / (grid_size + 1)
                    dom_points.append([x, y])

            dom_points = np.array(dom_points[:num_points])

            # Simulate OS screen coordinates
            # In production, these would come from actual OS mouse positions
            # Apply monitor offset, DPI scaling, and browser chrome offset

            # Convert DOM viewport coords to window coords (add browser chrome)
            chrome_offset_x = 8
            chrome_offset_y = 85  # Browser title bar + address bar

            # Convert to monitor-local coords
            monitor_coords = dom_points + np.array([chrome_offset_x, chrome_offset_y])

            # Apply DPI scaling
            monitor_coords = monitor_coords * monitor.dpi_scale

            # Convert to screen coordinates
            screen_coords = monitor_coords + np.array([monitor.x, monitor.y])

            # Add realistic measurement noise
            screen_coords += np.random.randn(*screen_coords.shape) * 2.0

            print(f"\n  Generated {len(dom_points)} calibration points")
            print(f"  DOM range: ({dom_points[:, 0].min():.0f}, {dom_points[:, 1].min():.0f}) to "
                  f"({dom_points[:, 0].max():.0f}, {dom_points[:, 1].max():.0f})")
            print(f"  Screen range: ({screen_coords[:, 0].min():.0f}, {screen_coords[:, 1].min():.0f}) to "
                  f"({screen_coords[:, 0].max():.0f}, {screen_coords[:, 1].max():.0f})")

            # Create and calibrate transformer
            transformer = OSToDOM_Transformer(enable_adaptive=True)
            report = transformer.calibrate(
                screen_coords,  # OS screen coordinates
                dom_points,     # DOM viewport coordinates
                use_ransac=True,
                refine=True
            )

            # Store transformer for this monitor
            self.transformers[monitor.id] = transformer

            print(f"\n  ✓ Calibration successful")
            print(f"    - Accuracy: {report['validation']['achieved_accuracy']:.4f} pixels")
            print(f"    - Sub-pixel: {report['validation']['is_subpixel_accurate']}")
            print(f"    - Scale detected: ({report['decomposition']['scale'][0]:.4f}, "
                  f"{report['decomposition']['scale'][1]:.4f})")
            print(f"    - Translation: ({report['decomposition']['translation'][0]:.1f}, "
                  f"{report['decomposition']['translation'][1]:.1f})")

            return True

        except Exception as e:
            print(f"\n  ✗ Calibration failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def transform_screen_to_dom(
        self,
        screen_x: int,
        screen_y: int
    ) -> Optional[Tuple[float, float, Monitor]]:
        """
        Transform screen coordinates to DOM coordinates.

        Automatically determines which monitor contains the coordinates
        and uses the appropriate transformation.

        Args:
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate

        Returns:
            (dom_x, dom_y, monitor) tuple, or None if no monitor found
        """
        # Find which monitor contains this point
        monitor = self.get_monitor_at_position(screen_x, screen_y)

        if not monitor:
            print(f"✗ No monitor found for screen position ({screen_x}, {screen_y})")
            return None

        # Get transformer for this monitor
        transformer = self.transformers.get(monitor.id)

        if not transformer:
            print(f"✗ No calibration for monitor {monitor.name}")
            return None

        # Transform coordinates
        dom_x, dom_y = transformer.transform_os_to_dom(screen_x, screen_y)

        return (dom_x, dom_y, monitor)

    def show_configuration(self):
        """Display current monitor configuration."""
        print(f"\n{'=' * 70}")
        print("Multi-Monitor Configuration")
        print(f"{'=' * 70}\n")

        total_width = max(m.x + m.width for m in self.monitors)
        total_height = max(m.y + m.height for m in self.monitors)

        print(f"Total screen space: {total_width}x{total_height}")
        print(f"Number of monitors: {len(self.monitors)}\n")

        for monitor in self.monitors:
            print(f"Monitor {monitor.id}: {monitor.name}")
            print(f"  Bounds: ({monitor.x}, {monitor.y}) to "
                  f"({monitor.x + monitor.width}, {monitor.y + monitor.height})")
            print(f"  Size: {monitor.width}x{monitor.height}")
            print(f"  DPI Scale: {monitor.dpi_scale}x")
            print(f"  Primary: {'Yes' if monitor.is_primary else 'No'}")
            print(f"  Calibrated: {'Yes' if monitor.id in self.transformers else 'No'}")
            print()


def demo_multi_monitor(browser: Browser):
    """
    Demonstrate multi-monitor coordination.

    Args:
        browser: Playwright browser instance
    """
    print("\n" + "=" * 70)
    print("DEMO: Multi-Monitor Coordination")
    print("=" * 70)

    # Initialize monitor manager
    manager = MonitorManager()

    # Detect monitors
    monitors = manager.detect_monitors()

    if not monitors:
        print("\n✗ No monitors detected")
        return

    # Show configuration
    manager.show_configuration()

    # Simulate opening browsers on different monitors
    print(f"\n{'=' * 70}")
    print("Calibrating Monitors")
    print(f"{'=' * 70}\n")

    for monitor in monitors:
        print(f"\nOpening browser window on {monitor.name}...")

        # Create new page
        page = browser.new_page()

        # Navigate to test page
        test_page_path = Path(__file__).parent / "test_page.html"
        if test_page_path.exists():
            page.goto(f"file://{test_page_path}")
        else:
            page.goto("https://example.com")

        page.wait_for_load_state("networkidle")

        # Calibrate this monitor
        manager.calibrate_monitor(monitor, page, num_points=9)

        # Close the page (in production, you'd keep it open)
        time.sleep(1)
        page.close()

    # Demo coordinate transformation
    print(f"\n{'=' * 70}")
    print("Testing Coordinate Transformations")
    print(f"{'=' * 70}\n")

    test_points = [
        (100, 100),      # Primary monitor, top-left area
        (960, 540),      # Primary monitor, center
        (2000, 100),     # Secondary monitor, top-left area
        (3200, 720),     # Secondary monitor, center
    ]

    for screen_x, screen_y in test_points:
        print(f"\nScreen position: ({screen_x}, {screen_y})")

        result = manager.transform_screen_to_dom(screen_x, screen_y)

        if result:
            dom_x, dom_y, monitor = result
            print(f"  ✓ Monitor: {monitor.name}")
            print(f"  ✓ DOM coordinates: ({dom_x:.2f}, {dom_y:.2f})")

            # Convert back
            monitor_x, monitor_y = manager.screen_to_monitor_coordinates(
                screen_x, screen_y, monitor
            )
            print(f"  ✓ Monitor-local: ({monitor_x}, {monitor_y})")
        else:
            print(f"  ✗ Transformation failed")


def demo_window_tracking():
    """Demonstrate tracking windows across monitors."""
    print(f"\n{'=' * 70}")
    print("DEMO: Window Tracking Across Monitors")
    print(f"{'=' * 70}\n")

    manager = MonitorManager()
    manager.detect_monitors()

    # Simulate window positions
    window_positions = [
        ("Browser Window 1", 100, 100, 1200, 800),
        ("Browser Window 2", 2100, 200, 1400, 900),
        ("Browser Window 3", 800, 100, 1600, 1000),  # Spans monitors
    ]

    for name, x, y, width, height in window_positions:
        print(f"\n{name}:")
        print(f"  Position: ({x}, {y})")
        print(f"  Size: {width}x{height}")

        # Check which monitor(s) the window is on
        # Check top-left corner
        monitor = manager.get_monitor_at_position(x, y)
        if monitor:
            print(f"  Top-left on: {monitor.name}")

        # Check center
        center_x = x + width // 2
        center_y = y + height // 2
        monitor = manager.get_monitor_at_position(center_x, center_y)
        if monitor:
            print(f"  Center on: {monitor.name}")

        # Check if spanning
        top_right_mon = manager.get_monitor_at_position(x + width, y)
        if top_right_mon and top_right_mon.id != monitor.id:
            print(f"  ⚠ Window spans multiple monitors!")


def main():
    """
    Main example workflow.
    """
    print("=" * 70)
    print("MCP ACCURATE CLICK SERVER - MULTI-MONITOR EXAMPLE")
    print("=" * 70)

    print("\n⚠ Note: This example simulates a multi-monitor setup.")
    print("In production, it would detect actual monitor configurations")
    print("using platform-specific APIs.\n")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)

            # Demo 1: Multi-monitor coordination
            demo_multi_monitor(browser)

            # Demo 2: Window tracking
            demo_window_tracking()

            print("\n" + "=" * 70)
            print("SUMMARY")
            print("=" * 70)
            print("✓ Demonstrated multi-monitor features:")
            print("  - Monitor detection and configuration")
            print("  - Per-monitor coordinate calibration")
            print("  - DPI scaling awareness")
            print("  - Screen to monitor-local coordinate conversion")
            print("  - Automatic monitor selection")
            print("  - Window position tracking")
            print("\n✓ Key Takeaways:")
            print("  - Each monitor needs separate calibration")
            print("  - DPI scaling varies per monitor")
            print("  - Coordinate transformations are monitor-specific")
            print("  - Windows can span multiple monitors")

            browser.close()
            print("\n✓ Multi-monitor example completed successfully!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
