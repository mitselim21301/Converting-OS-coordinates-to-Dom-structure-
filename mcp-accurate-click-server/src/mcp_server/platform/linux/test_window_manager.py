#!/usr/bin/env python3
"""
Test script for Linux Window Manager

Demonstrates and validates the functionality of the LinuxWindowManager class.
Tests window detection, browser identification, and coordinate conversion.

Usage:
    python3 test_window_manager.py
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def print_window_info(info, index: int = None) -> None:
    """Print detailed window information."""
    prefix = f"[{index}] " if index is not None else ""
    print(f"\n{prefix}Window Details:")
    print(f"  Handle: {info.handle}")
    print(f"  Title: {info.title}")
    print(f"  Class: {info.class_name}")
    print(f"  PID: {info.process_id}")
    print(f"  Visible: {info.is_visible}")
    print(f"  Minimized: {info.is_minimized}")
    print(f"  Maximized: {info.is_maximized}")
    print(f"  Window Rect: {info.window_rect} ({info.window_width}x{info.window_height})")
    print(f"  Client Rect: {info.client_rect} ({info.client_width}x{info.client_height})")
    print(f"  Chrome Offset: X={info.chrome_offset_x}, Y={info.chrome_offset_y}")


def test_initialization() -> bool:
    """Test window manager initialization."""
    print_section("Test 1: Window Manager Initialization")

    try:
        from mcp_server.platform.linux.window_manager import get_window_manager

        wm = get_window_manager()
        print(f"✓ Window manager created successfully")
        print(f"  Display type: {wm.display_type}")
        print(f"  X11 display: {'Available' if wm.x_display else 'Not available'}")
        print(f"  wmctrl: {'Available' if wm.has_wmctrl else 'Not available'}")
        print(f"  xdotool: {'Available' if wm.has_xdotool else 'Not available'}")
        print(f"  xwininfo: {'Available' if wm.has_xwininfo else 'Not available'}")
        print(f"  xprop: {'Available' if wm.has_xprop else 'Not available'}")

        return True

    except Exception as e:
        print(f"✗ Failed to initialize window manager: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_find_browser_windows() -> bool:
    """Test finding browser windows."""
    print_section("Test 2: Find Browser Windows")

    try:
        from mcp_server.platform.linux.window_manager import get_window_manager

        wm = get_window_manager()
        browsers = wm.find_browser_windows()

        print(f"✓ Found {len(browsers)} browser window(s)")

        for i, browser in enumerate(browsers, 1):
            print_window_info(browser, i)

        if not browsers:
            print("  Note: No browser windows found. Open a browser to test this feature.")

        return True

    except Exception as e:
        print(f"✗ Failed to find browser windows: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_active_window() -> bool:
    """Test getting the active window."""
    print_section("Test 3: Get Active/Foreground Window")

    try:
        from mcp_server.platform.linux.window_manager import get_window_manager

        wm = get_window_manager()
        active = wm.get_foreground_window()

        if active:
            print(f"✓ Active window found")
            print_window_info(active)
        else:
            print("  Note: Could not determine active window")

        return True

    except Exception as e:
        print(f"✗ Failed to get active window: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_is_browser_window() -> bool:
    """Test browser detection."""
    print_section("Test 4: Browser Window Detection")

    try:
        from mcp_server.platform.linux.window_manager import get_window_manager

        wm = get_window_manager()
        active = wm.get_foreground_window()

        if active:
            is_browser = wm.is_browser_window(active.handle)
            print(f"✓ Browser detection test completed")
            print(f"  Window: {active.title[:50]}...")
            print(f"  Is browser: {is_browser}")
        else:
            print("  Note: No active window to test")

        return True

    except Exception as e:
        print(f"✗ Failed browser detection test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_coordinate_conversion() -> bool:
    """Test coordinate conversion."""
    print_section("Test 5: Coordinate Conversion")

    try:
        from mcp_server.platform.linux.window_manager import get_window_manager

        wm = get_window_manager()
        active = wm.get_foreground_window()

        if active:
            print(f"✓ Testing coordinate conversion on: {active.title[:50]}...")

            # Test screen to client
            screen_x, screen_y = 100, 100
            client_x, client_y = wm.screen_to_client(active.handle, screen_x, screen_y)
            print(f"  Screen ({screen_x}, {screen_y}) -> Client ({client_x}, {client_y})")

            # Test client to screen
            back_x, back_y = wm.client_to_screen(active.handle, client_x, client_y)
            print(f"  Client ({client_x}, {client_y}) -> Screen ({back_x}, {back_y})")

            # Verify round-trip
            if back_x == screen_x and back_y == screen_y:
                print(f"  ✓ Round-trip conversion successful!")
            else:
                print(f"  ! Round-trip mismatch: ({screen_x}, {screen_y}) != ({back_x}, {back_y})")

        else:
            print("  Note: No active window to test")

        return True

    except Exception as e:
        print(f"✗ Failed coordinate conversion test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_window_at_point() -> bool:
    """Test getting window at specific point."""
    print_section("Test 6: Get Window at Point")

    try:
        from mcp_server.platform.linux.window_manager import get_window_manager

        wm = get_window_manager()

        # Test center of screen (likely to have a window)
        test_x, test_y = 500, 500

        window = wm.get_window_at_point(test_x, test_y)

        if window:
            print(f"✓ Window found at ({test_x}, {test_y})")
            print_window_info(window)
        else:
            print(f"  Note: No window found at ({test_x}, {test_y})")

        return True

    except Exception as e:
        print(f"✗ Failed window at point test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chrome_offsets() -> bool:
    """Test window chrome (decoration) offset calculation."""
    print_section("Test 7: Window Chrome Offsets")

    try:
        from mcp_server.platform.linux.window_manager import get_window_manager

        wm = get_window_manager()
        browsers = wm.find_browser_windows()

        if browsers:
            print(f"✓ Testing chrome offsets on {len(browsers)} browser(s)")

            for i, browser in enumerate(browsers, 1):
                print(f"\n[{i}] {browser.title[:50]}...")
                print(f"  Window size: {browser.window_width}x{browser.window_height}")
                print(f"  Client size: {browser.client_width}x{browser.client_height}")
                print(f"  Left border: {browser.chrome_offset_x}px")
                print(f"  Top border/titlebar: {browser.chrome_offset_y}px")

                # Typical browser chrome is 0-10px sides, 30-80px top
                if 0 <= browser.chrome_offset_x <= 15:
                    print(f"  ✓ Left offset looks reasonable")
                else:
                    print(f"  ! Unusual left offset: {browser.chrome_offset_x}px")

                if 20 <= browser.chrome_offset_y <= 100:
                    print(f"  ✓ Top offset looks reasonable")
                else:
                    print(f"  ! Unusual top offset: {browser.chrome_offset_y}px")

        else:
            print("  Note: No browser windows found. Open a browser to test this feature.")

        return True

    except Exception as e:
        print(f"✗ Failed chrome offset test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main() -> int:
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  Linux Window Manager Test Suite")
    print("=" * 70)

    tests = [
        test_initialization,
        test_find_browser_windows,
        test_active_window,
        test_is_browser_window,
        test_coordinate_conversion,
        test_window_at_point,
        test_chrome_offsets,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print_section("Test Summary")
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
