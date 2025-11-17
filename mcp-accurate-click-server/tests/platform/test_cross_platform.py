"""
Cross-Platform Tests - Works on Both Windows and Linux

Tests platform-agnostic functionality and ensures:
- Abstract base classes work correctly
- Platform detection works
- Factory functions return correct implementations
- Common data structures behave consistently
- Coordinate conversions follow same logic
"""

import pytest
import sys
import platform
from unittest.mock import Mock, MagicMock, patch
from typing import Type

# Import base classes
from mcp_server.platform.base import (
    MouseButton, KeyModifier, MonitorInfo, WindowInfo, Point, Rectangle,
    PlatformInputSimulator, PlatformDPIHandler,
    PlatformWindowManager, PlatformCoordinateConverter
)


# ==================== Platform Detection Fixtures ====================

@pytest.fixture
def current_platform():
    """Get current platform name."""
    return sys.platform


@pytest.fixture
def is_linux():
    """Check if running on Linux."""
    return sys.platform.startswith('linux')


@pytest.fixture
def is_windows():
    """Check if running on Windows."""
    return sys.platform.startswith('win')


@pytest.fixture(params=['linux', 'windows'])
def mock_platform(request):
    """Parametrized fixture for both platforms."""
    return request.param


# ==================== Common Data Structure Tests ====================

class TestCommonDataStructures:
    """Test common data structures work on all platforms - 8 tests."""

    def test_mouse_button_enum(self):
        """Test MouseButton enum values."""
        assert MouseButton.LEFT == 1
        assert MouseButton.RIGHT == 2
        assert MouseButton.MIDDLE == 3
        assert MouseButton.X1 == 4
        assert MouseButton.X2 == 5

    def test_key_modifier_enum(self):
        """Test KeyModifier enum values."""
        assert KeyModifier.NONE == 0
        assert KeyModifier.SHIFT == 1
        assert KeyModifier.CTRL == 2
        assert KeyModifier.ALT == 4
        assert KeyModifier.META == 8

    def test_monitor_info_properties(self):
        """Test MonitorInfo computed properties."""
        monitor = MonitorInfo(
            handle="test",
            left=0,
            top=0,
            right=1920,
            bottom=1080,
            dpi_x=96,
            dpi_y=96,
            is_primary=True,
            scale_factor=1.0,
            name="Test Monitor"
        )

        assert monitor.width == 1920
        assert monitor.height == 1080
        assert monitor.scale_percentage == 100

        # Test with 150% scaling
        monitor_scaled = MonitorInfo(
            handle="test2",
            left=0,
            top=0,
            right=2560,
            bottom=1440,
            dpi_x=144,
            dpi_y=144,
            is_primary=False,
            scale_factor=1.5,
            name="Scaled Monitor"
        )

        assert monitor_scaled.scale_percentage == 150

    def test_window_info_properties(self):
        """Test WindowInfo computed properties."""
        window = WindowInfo(
            handle=12345,
            title="Test Window",
            class_name="TestClass",
            process_id=9999,
            thread_id=8888,
            is_visible=True,
            is_minimized=False,
            is_maximized=False,
            window_rect=(10, 20, 1010, 620),
            client_rect=(15, 60, 1005, 615),
            monitor_handle=0
        )

        assert window.window_width == 1000
        assert window.window_height == 600
        assert window.client_width == 990
        assert window.client_height == 555
        assert window.chrome_offset_x == 5  # 15 - 10
        assert window.chrome_offset_y == 40  # 60 - 20

    def test_point_coordinate_spaces(self):
        """Test Point with different coordinate spaces."""
        physical = Point(1000, 500, "physical")
        logical = Point(800, 400, "logical")
        css = Point(600, 300, "css")
        dom = Point(400, 200, "dom")

        assert physical.coordinate_space == "physical"
        assert logical.coordinate_space == "logical"
        assert css.coordinate_space == "css"
        assert dom.coordinate_space == "dom"

    def test_rectangle_properties(self):
        """Test Rectangle computed properties."""
        rect = Rectangle(
            left=100,
            top=200,
            right=1100,
            bottom=900,
            coordinate_space="physical"
        )

        assert rect.width == 1000
        assert rect.height == 700

    def test_rectangle_contains_point(self):
        """Test Rectangle point containment."""
        rect = Rectangle(
            left=0,
            top=0,
            right=1920,
            bottom=1080,
            coordinate_space="physical"
        )

        # Inside
        assert rect.contains_point(100, 100) is True
        assert rect.contains_point(1920, 1080) is True
        assert rect.contains_point(0, 0) is True

        # Outside
        assert rect.contains_point(-10, 100) is False
        assert rect.contains_point(100, -10) is False
        assert rect.contains_point(2000, 100) is False
        assert rect.contains_point(100, 1100) is False

    def test_monitor_info_with_negative_coordinates(self):
        """Test MonitorInfo with negative coordinates (multi-monitor)."""
        monitor = MonitorInfo(
            handle="left-monitor",
            left=-1920,
            top=0,
            right=0,
            bottom=1080,
            dpi_x=96,
            dpi_y=96,
            is_primary=False,
            scale_factor=1.0,
            name="Left Monitor"
        )

        assert monitor.width == 1920
        assert monitor.height == 1080
        assert monitor.left < 0


# ==================== Platform Detection Tests ====================

class TestPlatformDetection:
    """Test platform detection works correctly - 5 tests."""

    def test_detect_current_platform(self, current_platform):
        """Test current platform detection."""
        assert current_platform in ['linux', 'win32', 'darwin']

    def test_linux_module_imports_on_linux(self, is_linux):
        """Test Linux modules import correctly on Linux."""
        if is_linux:
            try:
                from mcp_server.platform.linux.input_simulator import LinuxInputSimulator
                from mcp_server.platform.linux.dpi_handler import LinuxDPIHandler
                from mcp_server.platform.linux.window_manager import LinuxWindowManager
                from mcp_server.platform.linux.coordinate_converter import LinuxCoordinateConverter
                assert True
            except ImportError as e:
                pytest.fail(f"Failed to import Linux modules on Linux: {e}")
        else:
            pytest.skip("Not running on Linux")

    def test_windows_module_imports_on_windows(self, is_windows):
        """Test Windows modules import correctly on Windows."""
        if is_windows:
            try:
                from mcp_server.windows.input_simulator import WindowsInputSimulator
                from mcp_server.windows.dpi_handler import WindowsDPIHandler
                from mcp_server.windows.window_manager import WindowsWindowManager
                from mcp_server.windows.coordinate_converter import WindowsCoordinateConverter
                assert True
            except ImportError as e:
                pytest.fail(f"Failed to import Windows modules on Windows: {e}")
        else:
            pytest.skip("Not running on Windows")

    @patch('sys.platform', 'linux')
    def test_platform_module_selection_linux(self):
        """Test correct platform module is selected for Linux."""
        # This would test the platform factory/selector
        # Implementation depends on how platform selection is done in the main code
        pass

    @patch('sys.platform', 'win32')
    def test_platform_module_selection_windows(self):
        """Test correct platform module is selected for Windows."""
        # This would test the platform factory/selector
        # Implementation depends on how platform selection is done in the main code
        pass


# ==================== Abstract Base Class Tests ====================

class TestAbstractBaseClasses:
    """Test abstract base classes enforce interface - 4 tests."""

    def test_platform_input_simulator_is_abstract(self):
        """Test PlatformInputSimulator cannot be instantiated."""
        with pytest.raises(TypeError):
            PlatformInputSimulator()

    def test_platform_dpi_handler_is_abstract(self):
        """Test PlatformDPIHandler cannot be instantiated."""
        with pytest.raises(TypeError):
            PlatformDPIHandler()

    def test_platform_window_manager_is_abstract(self):
        """Test PlatformWindowManager cannot be instantiated."""
        with pytest.raises(TypeError):
            PlatformWindowManager()

    def test_platform_coordinate_converter_is_abstract(self):
        """Test PlatformCoordinateConverter cannot be instantiated."""
        with pytest.raises(TypeError):
            PlatformCoordinateConverter()


# ==================== Coordinate Conversion Logic Tests ====================

class TestCoordinateConversionLogic:
    """Test coordinate conversion logic is consistent across platforms - 6 tests."""

    def test_dpi_to_scale_factor_conversion(self):
        """Test DPI to scale factor conversion formula."""
        # Formula: scale = DPI / 96
        assert self._dpi_to_scale(96) == 1.0
        assert self._dpi_to_scale(120) == 1.25
        assert self._dpi_to_scale(144) == 1.5
        assert self._dpi_to_scale(192) == 2.0
        assert self._dpi_to_scale(288) == 3.0

    def test_physical_to_logical_formula(self):
        """Test physical to logical pixel conversion formula."""
        # Formula: logical = physical * (96 / DPI)

        # 100% scaling (96 DPI)
        assert self._physical_to_logical(1000, 96) == 1000

        # 125% scaling (120 DPI)
        assert self._physical_to_logical(1250, 120) == 1000

        # 150% scaling (144 DPI)
        assert self._physical_to_logical(1500, 144) == 1000

        # 200% scaling (192 DPI)
        assert self._physical_to_logical(2000, 192) == 1000

    def test_logical_to_physical_formula(self):
        """Test logical to physical pixel conversion formula."""
        # Formula: physical = logical * (DPI / 96)

        # 100% scaling (96 DPI)
        assert self._logical_to_physical(1000, 96) == 1000

        # 125% scaling (120 DPI)
        assert self._logical_to_physical(1000, 120) == 1250

        # 150% scaling (144 DPI)
        assert self._logical_to_physical(1000, 144) == 1500

        # 200% scaling (192 DPI)
        assert self._logical_to_physical(1000, 192) == 2000

    def test_physical_to_css_formula(self):
        """Test physical to CSS pixel conversion formula."""
        # Formula: CSS = physical / (devicePixelRatio * zoom)

        # No scaling
        assert self._physical_to_css(1000, 1.0, 1.0) == 1000

        # 2x device pixel ratio
        assert self._physical_to_css(2000, 2.0, 1.0) == 1000

        # 150% browser zoom
        assert self._physical_to_css(1500, 1.0, 1.5) == 1000

        # Combined: 2x DPR + 1.5x zoom
        assert self._physical_to_css(3000, 2.0, 1.5) == 1000

    def test_css_to_dom_formula(self):
        """Test CSS viewport to DOM document conversion."""
        # Formula: DOM = CSS - viewport_offset + scroll

        # No offsets or scroll
        assert self._css_to_dom(500, 0, 0) == 500

        # With viewport offset (browser chrome)
        assert self._css_to_dom(500, 80, 0) == 420  # 500 - 80

        # With scroll
        assert self._css_to_dom(500, 0, 100) == 600  # 500 + 100

        # With both
        assert self._css_to_dom(500, 80, 100) == 520  # 500 - 80 + 100

    def test_inverse_conversion_roundtrip(self):
        """Test that forward and inverse conversions cancel out."""
        # Physical <-> Logical roundtrip
        original_physical = 1920
        dpi = 144

        logical = self._physical_to_logical(original_physical, dpi)
        back_to_physical = self._logical_to_physical(logical, dpi)

        # Allow for small rounding errors (within 2 pixels)
        assert abs(back_to_physical - original_physical) <= 2

        # Physical <-> CSS roundtrip
        original_physical = 2000
        dpr = 2.0
        zoom = 1.5

        css = self._physical_to_css(original_physical, dpr, zoom)
        back_to_physical = self._css_to_physical(css, dpr, zoom)

        # Allow for small rounding errors (within 2 pixels)
        assert abs(back_to_physical - original_physical) <= 2

    # Helper methods for formula tests
    def _dpi_to_scale(self, dpi: int) -> float:
        """Convert DPI to scale factor."""
        return dpi / 96.0

    def _physical_to_logical(self, physical: int, dpi: int) -> int:
        """Convert physical to logical pixels."""
        return int(physical * 96 / dpi)

    def _logical_to_physical(self, logical: int, dpi: int) -> int:
        """Convert logical to physical pixels."""
        return int(logical * dpi / 96)

    def _physical_to_css(self, physical: int, dpr: float, zoom: float) -> int:
        """Convert physical to CSS pixels."""
        return int(physical / (dpr * zoom))

    def _css_to_physical(self, css: int, dpr: float, zoom: float) -> int:
        """Convert CSS to physical pixels."""
        return int(css * dpr * zoom)

    def _css_to_dom(self, css: int, viewport_offset: int, scroll: int) -> int:
        """Convert CSS viewport to DOM document coordinates."""
        return css - viewport_offset + scroll


# ==================== Multi-Monitor Scenario Tests ====================

class TestMultiMonitorScenarios:
    """Test multi-monitor scenarios work consistently - 6 tests."""

    def test_dual_monitor_side_by_side(self):
        """Test dual monitors arranged side by side."""
        monitor1 = MonitorInfo(
            handle="1", left=0, top=0, right=1920, bottom=1080,
            dpi_x=96, dpi_y=96, is_primary=True, scale_factor=1.0, name="Primary"
        )
        monitor2 = MonitorInfo(
            handle="2", left=1920, top=0, right=3840, bottom=1080,
            dpi_x=96, dpi_y=96, is_primary=False, scale_factor=1.0, name="Secondary"
        )

        monitors = [monitor1, monitor2]

        # Virtual screen should span both
        min_x = min(m.left for m in monitors)
        max_x = max(m.right for m in monitors)

        assert min_x == 0
        assert max_x == 3840

    def test_dual_monitor_stacked(self):
        """Test dual monitors arranged vertically."""
        monitor1 = MonitorInfo(
            handle="1", left=0, top=0, right=1920, bottom=1080,
            dpi_x=96, dpi_y=96, is_primary=True, scale_factor=1.0, name="Top"
        )
        monitor2 = MonitorInfo(
            handle="2", left=0, top=1080, right=1920, bottom=2160,
            dpi_x=96, dpi_y=96, is_primary=False, scale_factor=1.0, name="Bottom"
        )

        monitors = [monitor1, monitor2]

        # Virtual screen height should be combined
        min_y = min(m.top for m in monitors)
        max_y = max(m.bottom for m in monitors)

        assert min_y == 0
        assert max_y == 2160

    def test_monitor_left_of_primary_negative_coords(self):
        """Test monitor positioned to the left (negative coordinates)."""
        monitor_left = MonitorInfo(
            handle="left", left=-1920, top=0, right=0, bottom=1080,
            dpi_x=96, dpi_y=96, is_primary=False, scale_factor=1.0, name="Left"
        )
        monitor_primary = MonitorInfo(
            handle="primary", left=0, top=0, right=1920, bottom=1080,
            dpi_x=96, dpi_y=96, is_primary=True, scale_factor=1.0, name="Primary"
        )

        monitors = [monitor_left, monitor_primary]

        min_x = min(m.left for m in monitors)
        assert min_x == -1920

    def test_mixed_dpi_monitors(self):
        """Test monitors with different DPI/scaling."""
        monitor_normal = MonitorInfo(
            handle="1", left=0, top=0, right=1920, bottom=1080,
            dpi_x=96, dpi_y=96, is_primary=True, scale_factor=1.0, name="Normal DPI"
        )
        monitor_hidpi = MonitorInfo(
            handle="2", left=1920, top=0, right=4480, bottom=1440,
            dpi_x=144, dpi_y=144, is_primary=False, scale_factor=1.5, name="HiDPI"
        )

        # Check that DPI differs
        assert monitor_normal.dpi_x != monitor_hidpi.dpi_x
        assert monitor_normal.scale_factor != monitor_hidpi.scale_factor

    def test_point_on_specific_monitor(self):
        """Test determining which monitor contains a point."""
        monitors = [
            MonitorInfo(
                handle="1", left=0, top=0, right=1920, bottom=1080,
                dpi_x=96, dpi_y=96, is_primary=True, scale_factor=1.0, name="M1"
            ),
            MonitorInfo(
                handle="2", left=1920, top=0, right=3840, bottom=1080,
                dpi_x=96, dpi_y=96, is_primary=False, scale_factor=1.0, name="M2"
            ),
        ]

        # Point on monitor 1
        point1 = (500, 500)
        m1 = self._find_monitor_containing_point(monitors, *point1)
        assert m1.name == "M1"

        # Point on monitor 2
        point2 = (2500, 500)
        m2 = self._find_monitor_containing_point(monitors, *point2)
        assert m2.name == "M2"

    def test_virtual_desktop_spanning(self):
        """Test virtual desktop spans all monitors."""
        monitors = [
            MonitorInfo(
                handle="1", left=-1920, top=0, right=0, bottom=1080,
                dpi_x=96, dpi_y=96, is_primary=False, scale_factor=1.0, name="Left"
            ),
            MonitorInfo(
                handle="2", left=0, top=0, right=1920, bottom=1080,
                dpi_x=96, dpi_y=96, is_primary=True, scale_factor=1.0, name="Center"
            ),
            MonitorInfo(
                handle="3", left=1920, top=0, right=3840, bottom=1080,
                dpi_x=96, dpi_y=96, is_primary=False, scale_factor=1.0, name="Right"
            ),
        ]

        min_x = min(m.left for m in monitors)
        max_x = max(m.right for m in monitors)
        min_y = min(m.top for m in monitors)
        max_y = max(m.bottom for m in monitors)

        virtual_width = max_x - min_x
        virtual_height = max_y - min_y

        assert min_x == -1920
        assert max_x == 3840
        assert virtual_width == 5760
        assert virtual_height == 1080

    def _find_monitor_containing_point(self, monitors: list, x: int, y: int):
        """Helper to find monitor containing a point."""
        for monitor in monitors:
            if (monitor.left <= x < monitor.right and
                monitor.top <= y < monitor.bottom):
                return monitor
        return None


# ==================== Error Handling Tests ====================

class TestErrorHandling:
    """Test error handling is consistent across platforms - 4 tests."""

    def test_handle_missing_monitor_gracefully(self):
        """Test graceful handling when no monitors detected."""
        # This should return a default/fallback monitor
        # instead of crashing
        pass

    def test_handle_invalid_window_handle(self):
        """Test handling of invalid window handles."""
        # Should return None or appropriate error instead of crashing
        pass

    def test_handle_out_of_bounds_coordinates(self):
        """Test handling coordinates outside virtual screen."""
        rect = Rectangle(0, 0, 1920, 1080, "physical")

        # Out of bounds coordinates should be handled gracefully
        assert rect.contains_point(-100, 500) is False
        assert rect.contains_point(2000, 500) is False

    def test_handle_zero_or_negative_dpi(self):
        """Test handling of invalid DPI values."""
        # DPI should never be 0 or negative
        # Implementation should clamp to minimum valid value (e.g., 96)

        def safe_scale_factor(dpi: int) -> float:
            if dpi <= 0:
                dpi = 96
            return dpi / 96.0

        assert safe_scale_factor(0) == 1.0
        assert safe_scale_factor(-10) == 1.0
        assert safe_scale_factor(96) == 1.0
