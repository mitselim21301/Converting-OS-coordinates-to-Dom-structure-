"""
Example usage of Windows integration module.

This script demonstrates the key features of the Windows integration.
"""

import logging
import json

# Configure logging to see debug output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_system_info():
    """Example: Get comprehensive system information."""
    print("\n" + "="*70)
    print("EXAMPLE 1: System Information")
    print("="*70)

    try:
        from mcp_server.windows import get_system_info

        info = get_system_info()
        print(json.dumps(info, indent=2))

    except Exception as e:
        logger.error(f"System info example failed: {e}")
        logger.info("Note: This module requires Windows to function properly")


def example_dpi_detection():
    """Example: Detect DPI and monitor configuration."""
    print("\n" + "="*70)
    print("EXAMPLE 2: DPI Detection and Monitor Enumeration")
    print("="*70)

    try:
        from mcp_server.windows import get_dpi_handler

        dpi_handler = get_dpi_handler()

        # Get system DPI
        system_dpi = dpi_handler.get_system_dpi()
        print(f"System DPI: {system_dpi[0]}x{system_dpi[1]} "
              f"({dpi_handler.dpi_to_percentage(system_dpi[0])}%)")

        # Enumerate monitors
        print("\nMonitors:")
        monitors = dpi_handler.enumerate_monitors()
        for i, monitor in enumerate(monitors):
            print(f"\n  Monitor {i + 1}:")
            print(f"    Size: {monitor.width}x{monitor.height}")
            print(f"    Position: ({monitor.left}, {monitor.top})")
            print(f"    DPI: {monitor.dpi_x}x{monitor.dpi_y}")
            print(f"    Scale: {monitor.scale_percentage}%")
            print(f"    Primary: {monitor.is_primary}")

        # Check for mixed DPI
        if dpi_handler.is_mixed_dpi_environment():
            print("\n⚠ Mixed DPI environment detected!")
        else:
            print("\n✓ Uniform DPI across all monitors")

    except Exception as e:
        logger.error(f"DPI detection example failed: {e}")


def example_coordinate_conversion():
    """Example: Convert coordinates between spaces."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Coordinate Conversion")
    print("="*70)

    try:
        from mcp_server.windows import get_converter

        converter = get_converter()

        # Example: Convert physical screen coordinate to DOM
        physical_x, physical_y = 1920, 1080
        dpi = 144  # 150% scaling
        device_pixel_ratio = 1.5
        browser_zoom = 1.0
        viewport_offset_y = 130  # Address bar, etc.
        scroll_y = 250

        print(f"\nInput:")
        print(f"  Physical screen: ({physical_x}, {physical_y})")
        print(f"  Monitor DPI: {dpi} ({int(dpi/96*100)}% scaling)")
        print(f"  Device Pixel Ratio: {device_pixel_ratio}")
        print(f"  Browser Zoom: {browser_zoom}")
        print(f"  Viewport Offset Y: {viewport_offset_y}px")
        print(f"  Scroll Y: {scroll_y}px")

        # Full conversion chain
        result = converter.physical_to_dom_full_chain(
            physical_x=physical_x,
            physical_y=physical_y,
            dpi=dpi,
            device_pixel_ratio=device_pixel_ratio,
            browser_zoom=browser_zoom,
            viewport_offset_y=viewport_offset_y,
            scroll_y=scroll_y
        )

        print(f"\nConversion Chain:")
        print(f"  Physical: ({result['physical'].x}, {result['physical'].y})")
        print(f"  Logical:  ({result['logical'].x}, {result['logical'].y})")
        print(f"  CSS:      ({result['css'].x}, {result['css'].y})")
        print(f"  DOM:      ({result['dom'].x}, {result['dom'].y})")

    except Exception as e:
        logger.error(f"Coordinate conversion example failed: {e}")


def example_browser_detection():
    """Example: Find and analyze browser windows."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Browser Window Detection")
    print("="*70)

    try:
        from mcp_server.windows import get_window_manager

        window_mgr = get_window_manager()

        # Find all browser windows
        browsers = window_mgr.find_browser_windows()

        if not browsers:
            print("No browser windows found!")
            print("(Try opening a browser window and running this again)")
            return

        print(f"\nFound {len(browsers)} browser window(s):")

        for i, browser in enumerate(browsers[:3], 1):  # Show first 3
            browser_type = window_mgr.get_browser_type(browser.hwnd)

            print(f"\n  Browser {i}:")
            print(f"    Type: {browser_type or 'Unknown'}")
            print(f"    Title: {browser.title[:50]}...")
            print(f"    HWND: 0x{browser.hwnd:08X}")
            print(f"    Window Size: {browser.window_width}x{browser.window_height}")
            print(f"    Client Size: {browser.client_width}x{browser.client_height}")
            print(f"    Chrome Offset: ({browser.chrome_offset_x}, {browser.chrome_offset_y})")
            print(f"    Maximized: {browser.is_maximized}")

        # Get foreground window
        foreground = window_mgr.get_foreground_window()
        if foreground and window_mgr.is_browser_window(foreground.hwnd):
            print(f"\n  Active Browser: {foreground.title[:50]}...")

    except Exception as e:
        logger.error(f"Browser detection example failed: {e}")


def example_cursor_tracking():
    """Example: Track cursor position with DPI info."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Cursor Position Tracking")
    print("="*70)

    try:
        from mcp_server.windows import get_converter, get_dpi_handler

        converter = get_converter()
        dpi_handler = get_dpi_handler()

        # Get current cursor position
        cursor = converter.get_physical_cursor_pos()
        print(f"\nCursor Position:")
        print(f"  Physical: ({cursor.x}, {cursor.y})")

        # Get DPI at cursor position
        dpi_x, dpi_y = dpi_handler.get_dpi_at_point(cursor.x, cursor.y)
        print(f"  Monitor DPI: {dpi_x}x{dpi_y} "
              f"({dpi_handler.dpi_to_percentage(dpi_x)}%)")

        # Get monitor info
        monitor = dpi_handler.get_monitor_at_point(cursor.x, cursor.y)
        if monitor:
            print(f"  Monitor: {monitor.width}x{monitor.height} @ "
                  f"({monitor.left}, {monitor.top})")
            print(f"  Primary: {monitor.is_primary}")

        # Virtual screen bounds
        virtual = converter.get_virtual_screen_bounds()
        print(f"\nVirtual Screen:")
        print(f"  Bounds: ({virtual.left}, {virtual.top}) to "
              f"({virtual.right}, {virtual.bottom})")
        print(f"  Size: {virtual.width}x{virtual.height}")

    except Exception as e:
        logger.error(f"Cursor tracking example failed: {e}")


def example_click_simulation():
    """Example: Simulate mouse clicks (demonstration only)."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Click Simulation (Dry Run)")
    print("="*70)

    print("\nThis example demonstrates the click API without actually clicking.")
    print("To perform real clicks, uncomment the code below.\n")

    try:
        from mcp_server.windows import (
            get_input_simulator,
            get_window_manager,
            MouseButton
        )

        simulator = get_input_simulator()
        window_mgr = get_window_manager()

        # Get current cursor position
        cursor_x, cursor_y = simulator.get_cursor_pos()
        print(f"Current cursor position: ({cursor_x}, {cursor_y})")

        # Example clicks (commented out for safety)
        print("\nExample click commands (not executed):")
        print(f"  simulator.click(x={cursor_x}, y={cursor_y})")
        print(f"  simulator.click(x={cursor_x}, y={cursor_y}, button=MouseButton.RIGHT)")
        print(f"  simulator.click(x={cursor_x}, y={cursor_y}, clicks=2)")

        # Uncomment to actually perform clicks:
        # print("\nPerforming test click in 3 seconds...")
        # import time
        # time.sleep(3)
        # simulator.click(cursor_x, cursor_y)

    except Exception as e:
        logger.error(f"Click simulation example failed: {e}")


def example_high_level_api():
    """Example: Use high-level click_dom_element function."""
    print("\n" + "="*70)
    print("EXAMPLE 7: High-Level DOM Element Click API")
    print("="*70)

    print("\nThis example shows how to use the high-level API.")
    print("Actual clicking is disabled for safety.\n")

    try:
        from mcp_server.windows import click_dom_element, MouseButton

        # Example values (from browser)
        dom_x, dom_y = 250, 400
        browser_hwnd = 0x001234AB  # Example HWND
        device_pixel_ratio = 1.5
        browser_zoom = 1.0
        viewport_offset_x = 8
        viewport_offset_y = 130
        scroll_x = 0
        scroll_y = 100

        print("Example DOM click parameters:")
        print(f"  DOM coords: ({dom_x}, {dom_y})")
        print(f"  Browser HWND: 0x{browser_hwnd:08X}")
        print(f"  Device Pixel Ratio: {device_pixel_ratio}")
        print(f"  Browser Zoom: {browser_zoom}")
        print(f"  Viewport Offset: ({viewport_offset_x}, {viewport_offset_y})")
        print(f"  Scroll Position: ({scroll_x}, {scroll_y})")

        print("\nTo perform actual click:")
        print("  success = click_dom_element(")
        print(f"      dom_x={dom_x}, dom_y={dom_y},")
        print(f"      hwnd=browser_hwnd,")
        print(f"      device_pixel_ratio={device_pixel_ratio},")
        print(f"      browser_zoom={browser_zoom},")
        print(f"      viewport_offset_x={viewport_offset_x},")
        print(f"      viewport_offset_y={viewport_offset_y},")
        print(f"      scroll_x={scroll_x}, scroll_y={scroll_y},")
        print(f"      button=MouseButton.LEFT")
        print("  )")

        # Uncomment to perform actual click:
        # success = click_dom_element(
        #     dom_x=dom_x, dom_y=dom_y,
        #     hwnd=browser_hwnd,
        #     device_pixel_ratio=device_pixel_ratio,
        #     browser_zoom=browser_zoom,
        #     viewport_offset_x=viewport_offset_x,
        #     viewport_offset_y=viewport_offset_y,
        #     scroll_x=scroll_x, scroll_y=scroll_y
        # )
        # print(f"\nClick result: {'Success' if success else 'Failed'}")

    except Exception as e:
        logger.error(f"High-level API example failed: {e}")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("Windows Integration Module - Example Usage")
    print("="*70)

    examples = [
        ("System Information", example_system_info),
        ("DPI Detection", example_dpi_detection),
        ("Coordinate Conversion", example_coordinate_conversion),
        ("Browser Detection", example_browser_detection),
        ("Cursor Tracking", example_cursor_tracking),
        ("Click Simulation", example_click_simulation),
        ("High-Level API", example_high_level_api),
    ]

    for name, func in examples:
        try:
            func()
        except Exception as e:
            logger.error(f"Example '{name}' failed: {e}")

    print("\n" + "="*70)
    print("Examples Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
