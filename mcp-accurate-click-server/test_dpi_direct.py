#!/usr/bin/env python3
"""
Direct test for Linux DPI Handler - bypasses package structure.
"""

import sys
import os
import importlib.util

# Load the base module directly
base_path = '/home/user/Converting-OS-coordinates-to-Dom-structure-/mcp-accurate-click-server/src/mcp_server/platform/base/__init__.py'
spec = importlib.util.spec_from_file_location("base", base_path)
base = importlib.util.module_from_spec(spec)
sys.modules['mcp_server.platform.base'] = base
spec.loader.exec_module(base)

# Load the DPI handler module directly
dpi_path = '/home/user/Converting-OS-coordinates-to-Dom-structure-/mcp-accurate-click-server/src/mcp_server/platform/linux/dpi_handler.py'
spec = importlib.util.spec_from_file_location("dpi_handler", dpi_path)
dpi_handler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dpi_handler)

LinuxDPIHandler = dpi_handler.LinuxDPIHandler
DisplayServer = dpi_handler.DisplayServer
MonitorInfo = base.MonitorInfo


def test_dpi_handler():
    """Test all DPI handler functionality."""
    print("=" * 70)
    print("Linux DPI Handler - Direct Test")
    print("=" * 70)
    print()

    # Create handler
    print("Creating DPI Handler...")
    handler = LinuxDPIHandler()
    print("✓ Handler created successfully")
    print()

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
        print(f"     Position: ({monitor.left}, {monitor.top}) to ({monitor.right}, {monitor.bottom})")
        print(f"     DPI: {monitor.dpi_x} x {monitor.dpi_y}")
        print(f"     Scale Factor: {monitor.scale_factor:.2f}")
        print(f"     Scale Percentage: {monitor.scale_percentage}%")
        print(f"     Is Primary: {monitor.is_primary}")
        print()

    # Primary monitor
    print(f"4. Primary Monitor:")
    primary = handler.get_primary_monitor()
    if primary:
        print(f"   ✓ Name: {primary.name}")
        print(f"   ✓ Resolution: {primary.width} x {primary.height}")
        print(f"   ✓ DPI: {primary.dpi_x} x {primary.dpi_y}")
    else:
        print(f"   ✗ ERROR: No primary monitor found!")
        return False
    print()

    # Test DPI at point
    print(f"5. DPI at Specific Points:")
    test_points = [
        (0, 0),
        (100, 100),
        (500, 500),
    ]
    for x, y in test_points:
        dpi = handler.get_dpi_at_point(x, y)
        monitor = handler.get_monitor_at_point(x, y)
        monitor_name = monitor.name if monitor else "Unknown"
        print(f"   Point ({x:4d}, {y:4d}): DPI {dpi[0]:3d}x{dpi[1]:3d} (Monitor: {monitor_name})")
    print()

    # Mixed DPI environment
    print(f"6. Mixed DPI Environment Check:")
    is_mixed = handler.is_mixed_dpi_environment()
    print(f"   Mixed DPI: {is_mixed}")
    if is_mixed:
        print(f"   ⚠ System has monitors with different DPI values")
    else:
        print(f"   ✓ All monitors have consistent DPI")
    print()

    # Cache test
    print(f"7. Cache Performance Test:")
    import time

    # Test cached calls
    start = time.time()
    for _ in range(100):
        handler.enumerate_monitors(refresh=False)
    cached_time = time.time() - start

    # Test refresh calls
    handler._invalidate_cache()
    start = time.time()
    handler.enumerate_monitors(refresh=True)  # First call to populate
    for _ in range(10):  # Fewer iterations for refresh test
        handler._invalidate_cache()
        handler.enumerate_monitors(refresh=True)
    refresh_time = (time.time() - start) / 10  # Average per call

    print(f"   100 cached calls: {cached_time*1000:.2f} ms ({cached_time*10:.4f} ms/call)")
    print(f"   Avg refresh call: {refresh_time*1000:.2f} ms/call")
    if cached_time > 0 and refresh_time > 0:
        speedup = refresh_time / (cached_time/100)
        print(f"   Cache speedup: {speedup:.1f}x faster")
    print()

    # Scale factor tests
    print(f"8. Scale Factor Calculations:")
    test_dpis = [96, 120, 144, 168, 192, 240, 288]
    print(f"   {'DPI':<6} {'Scale':<8} {'Percentage':<12}")
    print(f"   {'-'*6} {'-'*8} {'-'*12}")
    for dpi in test_dpis:
        scale = handler.get_scale_factor(dpi)
        percentage = int(scale * 100)
        print(f"   {dpi:<6} {scale:<8.2f} {percentage}%")
    print()

    # Window DPI test (with None handle as we don't have real windows)
    print(f"9. Window DPI Test:")
    window_dpi = handler.get_dpi_for_window(None)
    print(f"   Window DPI (fallback): {window_dpi[0]} x {window_dpi[1]}")
    print()

    # Test interface compliance
    print(f"10. Interface Compliance Check:")
    required_methods = [
        'get_dpi_for_window',
        'get_dpi_at_point',
        'get_system_dpi',
        'get_scale_factor',
        'enumerate_monitors',
        'get_monitor_at_point',
        'get_primary_monitor',
        'is_mixed_dpi_environment'
    ]

    all_implemented = True
    for method in required_methods:
        has_method = hasattr(handler, method) and callable(getattr(handler, method))
        status = "✓" if has_method else "✗"
        print(f"   {status} {method}")
        if not has_method:
            all_implemented = False

    if not all_implemented:
        print(f"\n   ✗ Some required methods are missing!")
        return False

    print()

    print("=" * 70)
    print("✓ All tests completed successfully!")
    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        success = test_dpi_handler()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
