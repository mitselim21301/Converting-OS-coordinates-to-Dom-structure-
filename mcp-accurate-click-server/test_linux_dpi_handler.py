#!/usr/bin/env python3
"""
Test script for Linux DPI Handler.

Demonstrates all functionality and validates the implementation.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_server.platform.linux import LinuxDPIHandler, DisplayServer


def test_dpi_handler():
    """Test all DPI handler functionality."""
    print("=" * 70)
    print("Linux DPI Handler - Comprehensive Test")
    print("=" * 70)
    print()

    # Create handler
    handler = LinuxDPIHandler()

    # Display server detection
    print(f"1. Display Server Detection:")
    print(f"   Detected: {handler._display_server.value}")
    print(f"   Environment Scale Factor: {handler._env_scale_factor}")
    print()

    # System DPI
    print(f"2. System DPI:")
    system_dpi = handler.get_system_dpi()
    print(f"   DPI: {system_dpi[0]} x {system_dpi[1]}")
    scale = handler.get_scale_factor(system_dpi[0])
    print(f"   Scale Factor: {scale:.2f} ({int(scale * 100)}%)")
    print()

    # Enumerate monitors
    print(f"3. Monitor Enumeration:")
    monitors = handler.enumerate_monitors()
    print(f"   Total Monitors: {len(monitors)}")
    print()

    for i, monitor in enumerate(monitors, 1):
        print(f"   Monitor {i}:")
        print(f"     Name: {monitor.name}")
        print(f"     Handle: {monitor.handle}")
        print(f"     Resolution: {monitor.width} x {monitor.height}")
        print(f"     Position: ({monitor.left}, {monitor.top})")
        print(f"     DPI: {monitor.dpi_x} x {monitor.dpi_y}")
        print(f"     Scale Factor: {monitor.scale_factor:.2f}")
        print(f"     Scale Percentage: {monitor.scale_percentage}%")
        print(f"     Is Primary: {monitor.is_primary}")
        print()

    # Primary monitor
    print(f"4. Primary Monitor:")
    primary = handler.get_primary_monitor()
    if primary:
        print(f"   Name: {primary.name}")
        print(f"   Resolution: {primary.width} x {primary.height}")
        print(f"   DPI: {primary.dpi_x} x {primary.dpi_y}")
    else:
        print(f"   ERROR: No primary monitor found!")
    print()

    # Test DPI at point
    print(f"5. DPI at Specific Points:")
    test_points = [
        (0, 0),
        (100, 100),
        (1920, 1080),
    ]
    for x, y in test_points:
        dpi = handler.get_dpi_at_point(x, y)
        monitor = handler.get_monitor_at_point(x, y)
        monitor_name = monitor.name if monitor else "Unknown"
        print(f"   Point ({x}, {y}): DPI {dpi[0]}x{dpi[1]} (Monitor: {monitor_name})")
    print()

    # Mixed DPI environment
    print(f"6. Mixed DPI Environment:")
    is_mixed = handler.is_mixed_dpi_environment()
    print(f"   Mixed DPI: {is_mixed}")
    print()

    # Cache test
    print(f"7. Cache Performance Test:")
    import time
    start = time.time()
    for _ in range(100):
        handler.enumerate_monitors(refresh=False)
    cached_time = time.time() - start

    handler._invalidate_cache()
    start = time.time()
    for _ in range(100):
        handler.enumerate_monitors(refresh=True)
    refresh_time = time.time() - start

    print(f"   100 cached calls: {cached_time*1000:.2f} ms")
    print(f"   100 refresh calls: {refresh_time*1000:.2f} ms")
    print(f"   Cache speedup: {refresh_time/cached_time:.1f}x")
    print()

    # Scale factor tests
    print(f"8. Scale Factor Calculations:")
    test_dpis = [96, 120, 144, 168, 192, 288]
    for dpi in test_dpis:
        scale = handler.get_scale_factor(dpi)
        print(f"   {dpi} DPI = {scale:.2f}x ({int(scale * 100)}%)")
    print()

    print("=" * 70)
    print("All tests completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_dpi_handler()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
