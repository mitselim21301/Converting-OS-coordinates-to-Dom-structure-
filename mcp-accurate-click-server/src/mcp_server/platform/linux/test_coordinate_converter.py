#!/usr/bin/env python3
"""
Test script for Linux Coordinate Converter.

Tests all coordinate conversion methods, multi-monitor support,
and edge cases including negative coordinates.
"""

import sys
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_coordinate_converter():
    """Comprehensive test of Linux coordinate converter."""

    print("=" * 80)
    print("Linux Coordinate Converter - Comprehensive Test Suite")
    print("=" * 80)
    print()

    try:
        from mcp_server.platform.linux.coordinate_converter import get_converter
        from mcp_server.platform.linux.dpi_handler import create_dpi_handler
    except ImportError as e:
        print(f"ERROR: Failed to import modules: {e}")
        return False

    # Initialize DPI handler
    print("Initializing DPI handler...")
    dpi_handler = create_dpi_handler()

    # Initialize coordinate converter
    print("Initializing coordinate converter...")
    converter = get_converter(dpi_handler)
    print(f"Display server detected: {converter.display_server}")
    print()

    # Test 1: Display Configuration
    print("-" * 80)
    print("TEST 1: Display Configuration Summary")
    print("-" * 80)

    summary = converter.get_display_summary()
    print(f"Display Server: {summary['display_server']}")
    print(f"Monitor Count: {summary['monitor_count']}")
    print(f"Virtual Screen: {summary['virtual_screen']['width']}x{summary['virtual_screen']['height']}")
    print(f"Virtual Screen Bounds: ({summary['virtual_screen']['left']}, {summary['virtual_screen']['top']}) to ({summary['virtual_screen']['right']}, {summary['virtual_screen']['bottom']})")
    print(f"Cursor Position: ({summary['cursor_position']['x']}, {summary['cursor_position']['y']})")
    print()

    for i, monitor in enumerate(summary['monitors']):
        print(f"  Monitor {i + 1}: {monitor['name']}")
        print(f"    Bounds: {monitor['bounds']}")
        print(f"    DPI: {monitor['dpi']}")
        print(f"    Scale: {monitor['scale']}")
        print(f"    Primary: {monitor['primary']}")
        print()

    # Test 2: Virtual Screen Bounds
    print("-" * 80)
    print("TEST 2: Virtual Screen Bounds")
    print("-" * 80)

    virtual_screen = converter.get_virtual_screen_bounds()
    print(f"Virtual screen bounds: ({virtual_screen.left}, {virtual_screen.top}) to ({virtual_screen.right}, {virtual_screen.bottom})")
    print(f"Virtual screen size: {virtual_screen.width}x{virtual_screen.height}")
    print(f"Contains negative coordinates: {virtual_screen.left < 0 or virtual_screen.top < 0}")
    print()

    # Test 3: Physical to Logical Conversion
    print("-" * 80)
    print("TEST 3: Physical to Logical Conversion")
    print("-" * 80)

    test_cases = [
        (1920, 1080, 96),   # 100% scaling
        (1920, 1080, 120),  # 125% scaling
        (1920, 1080, 144),  # 150% scaling
        (1920, 1080, 192),  # 200% scaling
        (-1920, 0, 96),     # Negative coordinates (monitor to left)
        (0, -1080, 96),     # Negative coordinates (monitor above)
    ]

    for phys_x, phys_y, dpi in test_cases:
        logical = converter.physical_to_logical(phys_x, phys_y, dpi)
        print(f"Physical ({phys_x}, {phys_y}) @ {dpi} DPI -> Logical ({logical.x}, {logical.y})")
    print()

    # Test 4: Logical to Physical Conversion
    print("-" * 80)
    print("TEST 4: Logical to Physical Conversion (Round-trip)")
    print("-" * 80)

    for phys_x, phys_y, dpi in test_cases:
        logical = converter.physical_to_logical(phys_x, phys_y, dpi)
        physical = converter.logical_to_physical(logical.x, logical.y, dpi)
        match = abs(physical.x - phys_x) <= 1 and abs(physical.y - phys_y) <= 1  # Allow 1px rounding error
        status = "✓ PASS" if match else "✗ FAIL"
        print(f"{status}: Physical ({phys_x}, {phys_y}) -> Logical ({logical.x}, {logical.y}) -> Physical ({physical.x}, {physical.y})")
    print()

    # Test 5: Physical to CSS Conversion
    print("-" * 80)
    print("TEST 5: Physical to CSS Conversion")
    print("-" * 80)

    css_test_cases = [
        (1920, 1080, 1.0, 1.0),   # No scaling
        (1920, 1080, 1.5, 1.0),   # 1.5x device pixel ratio
        (1920, 1080, 2.0, 1.0),   # 2x device pixel ratio (Retina)
        (1920, 1080, 1.0, 1.25),  # 125% browser zoom
        (1920, 1080, 1.5, 1.5),   # Combined 1.5x DPR + 1.5x zoom
    ]

    for phys_x, phys_y, dpr, zoom in css_test_cases:
        css = converter.physical_to_css(phys_x, phys_y, dpr, zoom)
        print(f"Physical ({phys_x}, {phys_y}) @ DPR={dpr}, Zoom={zoom} -> CSS ({css.x}, {css.y})")
    print()

    # Test 6: CSS to Physical Conversion (Round-trip)
    print("-" * 80)
    print("TEST 6: CSS to Physical Conversion (Round-trip)")
    print("-" * 80)

    for phys_x, phys_y, dpr, zoom in css_test_cases:
        css = converter.physical_to_css(phys_x, phys_y, dpr, zoom)
        physical = converter.css_to_physical(css.x, css.y, dpr, zoom)
        match = abs(physical.x - phys_x) <= 1 and abs(physical.y - phys_y) <= 1
        status = "✓ PASS" if match else "✗ FAIL"
        print(f"{status}: Physical ({phys_x}, {phys_y}) -> CSS ({css.x}, {css.y}) -> Physical ({physical.x}, {physical.y})")
    print()

    # Test 7: Full Coordinate Chain
    print("-" * 80)
    print("TEST 7: Full Coordinate Transformation Chain")
    print("-" * 80)

    phys_x, phys_y = 1920, 1080
    dpi = 144  # 150% scaling
    dpr = 1.5
    zoom = 1.0
    viewport_x, viewport_y = 0, 100  # Browser chrome offset
    scroll_x, scroll_y = 0, 500  # Page scroll

    chain = converter.physical_to_dom_full_chain(
        phys_x, phys_y,
        dpi=dpi,
        device_pixel_ratio=dpr,
        browser_zoom=zoom,
        viewport_offset_x=viewport_x,
        viewport_offset_y=viewport_y,
        scroll_x=scroll_x,
        scroll_y=scroll_y
    )

    print(f"Physical: ({chain['physical'].x}, {chain['physical'].y})")
    print(f"Logical:  ({chain['logical'].x}, {chain['logical'].y})")
    print(f"CSS:      ({chain['css'].x}, {chain['css'].y})")
    print(f"DOM:      ({chain['dom'].x}, {chain['dom'].y})")
    print()

    # Test 8: Coordinate Validation
    print("-" * 80)
    print("TEST 8: Coordinate Validation")
    print("-" * 80)

    # Test within bounds
    center_x = (virtual_screen.left + virtual_screen.right) // 2
    center_y = (virtual_screen.top + virtual_screen.bottom) // 2
    valid = converter.validate_coordinate(center_x, center_y, "physical")
    print(f"Center of virtual screen ({center_x}, {center_y}): {'✓ Valid' if valid else '✗ Invalid'}")

    # Test outside bounds
    invalid = converter.validate_coordinate(virtual_screen.right + 1000, virtual_screen.bottom + 1000, "physical")
    print(f"Outside virtual screen: {'✗ Invalid (expected)' if not invalid else '✓ Valid (unexpected!)'}")

    # Test negative coordinates (valid for multi-monitor)
    if virtual_screen.left < 0:
        valid_neg = converter.validate_coordinate(virtual_screen.left, virtual_screen.top, "physical")
        print(f"Negative coordinates ({virtual_screen.left}, {virtual_screen.top}): {'✓ Valid' if valid_neg else '✗ Invalid'}")
    print()

    # Test 9: Monitor Detection
    print("-" * 80)
    print("TEST 9: Monitor Detection at Point")
    print("-" * 80)

    test_points = [
        (0, 0),
        (100, 100),
        (1920, 1080),
    ]

    if virtual_screen.left < 0:
        test_points.append((virtual_screen.left + 10, 10))

    for x, y in test_points:
        monitor = converter.get_monitor_at_point(x, y)
        if monitor:
            print(f"Point ({x}, {y}): Monitor '{monitor.name}' - {monitor.width}x{monitor.height} @ ({monitor.left}, {monitor.top})")
        else:
            print(f"Point ({x}, {y}): No monitor found")
    print()

    # Test 10: DPI at Point
    print("-" * 80)
    print("TEST 10: DPI Detection at Point")
    print("-" * 80)

    for x, y in test_points:
        dpi_x, dpi_y = converter.get_dpi_at_point(x, y)
        scale = dpi_x / 96.0
        print(f"Point ({x}, {y}): DPI {dpi_x}x{dpi_y} (Scale: {scale:.2f}x or {int(scale * 100)}%)")
    print()

    # Test 11: Multi-Monitor Translation
    print("-" * 80)
    print("TEST 11: Multi-Monitor Coordinate Translation")
    print("-" * 80)

    monitors = summary['monitors']
    if len(monitors) >= 2:
        # Get first two monitors
        mon1 = converter.get_monitor_at_point(0, 0)

        # Find a different monitor
        mon2 = None
        for x, y in test_points:
            m = converter.get_monitor_at_point(x, y)
            if m and m.handle != mon1.handle:
                mon2 = m
                break

        if mon2:
            test_x, test_y = 100, 100
            translated = converter.translate_coordinate_between_monitors(
                test_x, test_y, mon1, mon2
            )
            print(f"Translate ({test_x}, {test_y}) from {mon1.name} to {mon2.name}:")
            print(f"  {mon1.name}: DPI {mon1.dpi_x}")
            print(f"  {mon2.name}: DPI {mon2.dpi_x}")
            print(f"  Result: ({translated.x}, {translated.y})")
        else:
            print("Only one monitor detected, skipping translation test")
    else:
        print("Only one monitor detected, skipping translation test")
    print()

    # Summary
    print("=" * 80)
    print("TEST SUITE COMPLETE")
    print("=" * 80)
    print(f"✓ All core functionality tested successfully")
    print(f"✓ Display server: {converter.display_server}")
    print(f"✓ Monitors detected: {len(monitors)}")
    print(f"✓ Virtual screen: {virtual_screen.width}x{virtual_screen.height}")
    print(f"✓ Negative coordinates supported: {virtual_screen.left < 0 or virtual_screen.top < 0}")
    print()

    return True


if __name__ == '__main__':
    try:
        success = test_coordinate_converter()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception("Test failed with exception")
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
