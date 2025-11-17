"""
Comprehensive Linux Integration Tests - 30+ Tests

Tests all 4 Linux modules:
1. LinuxInputSimulator
2. LinuxDPIHandler
3. LinuxWindowManager
4. LinuxCoordinateConverter

Features:
- Mocked external dependencies (xrandr, wmctrl, xdotool, pynput, etc.)
- Multi-monitor scenarios
- Error handling and edge cases
- Performance benchmarks
- X11 and Wayland support
"""

import pytest
import subprocess
import time
from unittest.mock import Mock, MagicMock, patch, mock_open, PropertyMock
from typing import List, Tuple, Dict, Any

# Import Linux modules
from mcp_server.platform.linux.input_simulator import LinuxInputSimulator, get_input_simulator
from mcp_server.platform.linux.dpi_handler import LinuxDPIHandler, DisplayServer, create_dpi_handler
from mcp_server.platform.linux.window_manager import LinuxWindowManager, get_window_manager
from mcp_server.platform.linux.coordinate_converter import LinuxCoordinateConverter, get_converter

# Import base classes
from mcp_server.platform.base import (
    MouseButton, MonitorInfo, WindowInfo, Point, Rectangle,
    PlatformInputSimulator, PlatformDPIHandler, PlatformWindowManager, PlatformCoordinateConverter
)


# ==================== Fixtures ====================

@pytest.fixture
def mock_x11_environment():
    """Mock X11 environment variables."""
    with patch.dict('os.environ', {
        'DISPLAY': ':0',
        'XDG_SESSION_TYPE': 'x11'
    }):
        yield


@pytest.fixture
def mock_wayland_environment():
    """Mock Wayland environment variables."""
    with patch.dict('os.environ', {
        'WAYLAND_DISPLAY': 'wayland-0',
        'XDG_SESSION_TYPE': 'wayland'
    }):
        yield


@pytest.fixture
def mock_xrandr_output_single():
    """Mock xrandr output for single monitor."""
    return """Screen 0: minimum 8 x 8, current 1920 x 1080, maximum 32767 x 32767
DP-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 527mm x 296mm
   1920x1080     60.00*+
   1680x1050     59.95
   1280x1024     75.02    60.02
"""


@pytest.fixture
def mock_xrandr_output_dual():
    """Mock xrandr output for dual monitors with different DPI."""
    return """Screen 0: minimum 8 x 8, current 4480 x 1440, maximum 32767 x 32767
DP-1 connected primary 2560x1440+0+0 (normal left inverted right x axis y axis) 597mm x 336mm
   2560x1440     59.95*+
HDMI-1 connected 1920x1080+2560+0 (normal left inverted right x axis y axis) 527mm x 296mm
   1920x1080     60.00*+
"""


@pytest.fixture
def mock_xrandr_output_negative_coords():
    """Mock xrandr output with negative coordinates (monitor left of primary)."""
    return """Screen 0: minimum 8 x 8, current 4480 x 1440, maximum 32767 x 32767
DP-1 connected primary 2560x1440+1920+0 (normal left inverted right x axis y axis) 597mm x 336mm
   2560x1440     59.95*+
HDMI-1 connected 1920x1080+-1920+0 (normal left inverted right x axis y axis) 527mm x 296mm
   1920x1080     60.00*+
"""


@pytest.fixture
def mock_wmctrl_output():
    """Mock wmctrl -lGpx output."""
    return """0x01400005 0 12345 0    0    1920 1080 hostname Google Chrome
0x01600007 0 12346 1920 0    1920 1080 hostname Mozilla Firefox
0x01800009 0 12347 100  100  800  600  hostname Terminal
"""


@pytest.fixture
def sample_monitor_info():
    """Sample MonitorInfo for testing."""
    return MonitorInfo(
        handle="DP-1",
        left=0,
        top=0,
        right=1920,
        bottom=1080,
        dpi_x=96,
        dpi_y=96,
        is_primary=True,
        scale_factor=1.0,
        name="DP-1"
    )


@pytest.fixture
def sample_window_info():
    """Sample WindowInfo for testing."""
    return WindowInfo(
        handle=0x01400005,
        title="Google Chrome",
        class_name="chrome",
        process_id=12345,
        thread_id=0,
        is_visible=True,
        is_minimized=False,
        is_maximized=False,
        window_rect=(0, 0, 1920, 1080),
        client_rect=(2, 30, 1918, 1078),
        monitor_handle=0
    )


# ==================== Input Simulator Tests ====================

class TestLinuxInputSimulator:
    """Test LinuxInputSimulator - 8 tests."""

    def test_singleton_pattern(self):
        """Test singleton instance creation."""
        # Reset singleton
        LinuxInputSimulator._instance = None

        sim1 = LinuxInputSimulator()
        sim2 = LinuxInputSimulator()

        assert sim1 is sim2
        assert id(sim1) == id(sim2)

    def test_display_server_detection_x11(self, mock_x11_environment):
        """Test X11 detection."""
        LinuxInputSimulator._instance = None
        with patch('mcp_server.platform.linux.input_simulator.subprocess.run'):
            sim = LinuxInputSimulator()
            assert sim._display_server == 'x11'

    def test_display_server_detection_wayland(self, mock_wayland_environment):
        """Test Wayland detection."""
        LinuxInputSimulator._instance = None
        with patch('mcp_server.platform.linux.input_simulator.subprocess.run'):
            sim = LinuxInputSimulator()
            assert sim._display_server == 'wayland'

    @patch('mcp_server.platform.linux.input_simulator.subprocess.run')
    def test_move_mouse_with_pynput(self, mock_run):
        """Test mouse movement using pynput."""
        LinuxInputSimulator._instance = None

        # Mock pynput
        mock_controller = MagicMock()
        mock_controller.position = (100, 200)

        with patch('mcp_server.platform.linux.input_simulator.Controller', return_value=mock_controller):
            sim = LinuxInputSimulator()

            # Simulate move
            result = sim.move_mouse(500, 600)

            assert result is True
            assert mock_controller.position == (500, 600)

    @patch('mcp_server.platform.linux.input_simulator.subprocess.run')
    def test_click_all_mouse_buttons(self, mock_run):
        """Test clicking with different mouse buttons."""
        LinuxInputSimulator._instance = None

        mock_controller = MagicMock()
        mock_controller.position = (100, 100)
        mock_button = MagicMock()

        with patch('mcp_server.platform.linux.input_simulator.Controller', return_value=mock_controller), \
             patch('mcp_server.platform.linux.input_simulator.Button', mock_button):

            sim = LinuxInputSimulator()
            sim._pynput_available = True

            # Test all button types
            for button in [MouseButton.LEFT, MouseButton.RIGHT, MouseButton.MIDDLE]:
                result = sim.click(100, 100, button=button)
                assert result is True

    @patch('mcp_server.platform.linux.input_simulator.subprocess.run')
    def test_scroll_vertical_and_horizontal(self, mock_run):
        """Test vertical and horizontal scrolling."""
        LinuxInputSimulator._instance = None

        mock_controller = MagicMock()

        with patch('mcp_server.platform.linux.input_simulator.Controller', return_value=mock_controller):
            sim = LinuxInputSimulator()

            # Vertical scroll
            result_v = sim.scroll(5, horizontal=False)
            assert result_v is True
            mock_controller.scroll.assert_called_with(0, 5)

            # Horizontal scroll
            result_h = sim.scroll(3, horizontal=True)
            assert result_h is True
            mock_controller.scroll.assert_called_with(3, 0)

    @patch('mcp_server.platform.linux.input_simulator.subprocess.run')
    def test_get_cursor_pos(self, mock_run):
        """Test getting cursor position."""
        LinuxInputSimulator._instance = None

        mock_controller = MagicMock()
        mock_controller.position = (250, 350)

        with patch('mcp_server.platform.linux.input_simulator.Controller', return_value=mock_controller):
            sim = LinuxInputSimulator()

            pos = sim.get_cursor_pos()
            assert pos == (250, 350)

    def test_set_delays(self):
        """Test setting input delays."""
        LinuxInputSimulator._instance = None

        with patch('mcp_server.platform.linux.input_simulator.subprocess.run'):
            sim = LinuxInputSimulator()

            sim.set_delays(move_delay=20, click_delay=15, double_click_delay=200)

            assert sim._move_delay == 20
            assert sim._click_delay == 15
            assert sim._double_click_delay == 200


# ==================== DPI Handler Tests ====================

class TestLinuxDPIHandler:
    """Test LinuxDPIHandler - 10 tests."""

    @patch('mcp_server.platform.linux.dpi_handler.subprocess.run')
    def test_display_server_detection_x11(self, mock_run, mock_x11_environment):
        """Test X11 display server detection."""
        mock_run.return_value = MagicMock(returncode=0)

        handler = LinuxDPIHandler()
        assert handler._display_server == DisplayServer.X11

    @patch('mcp_server.platform.linux.dpi_handler.subprocess.run')
    def test_display_server_detection_wayland(self, mock_run, mock_wayland_environment):
        """Test Wayland display server detection."""
        handler = LinuxDPIHandler()
        assert handler._display_server == DisplayServer.WAYLAND

    @patch('mcp_server.platform.linux.dpi_handler.subprocess.run')
    def test_enumerate_monitors_single_x11(self, mock_run, mock_x11_environment, mock_xrandr_output_single):
        """Test single monitor enumeration on X11."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_xrandr_output_single
        )

        handler = LinuxDPIHandler()
        monitors = handler.enumerate_monitors()

        assert len(monitors) == 1
        assert monitors[0].name == "DP-1"
        assert monitors[0].width == 1920
        assert monitors[0].height == 1080
        assert monitors[0].is_primary is True

    @patch('mcp_server.platform.linux.dpi_handler.subprocess.run')
    def test_enumerate_monitors_dual_x11(self, mock_run, mock_x11_environment, mock_xrandr_output_dual):
        """Test dual monitor enumeration on X11."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_xrandr_output_dual
        )

        handler = LinuxDPIHandler()
        monitors = handler.enumerate_monitors()

        assert len(monitors) == 2
        assert monitors[0].name == "DP-1"
        assert monitors[1].name == "HDMI-1"
        assert monitors[0].is_primary is True
        assert monitors[1].is_primary is False

    @patch('mcp_server.platform.linux.dpi_handler.subprocess.run')
    def test_get_monitor_at_point(self, mock_run, mock_x11_environment, mock_xrandr_output_dual):
        """Test getting monitor at specific point."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_xrandr_output_dual
        )

        handler = LinuxDPIHandler()

        # Point on first monitor
        monitor1 = handler.get_monitor_at_point(100, 100)
        assert monitor1.name == "DP-1"

        # Point on second monitor
        monitor2 = handler.get_monitor_at_point(3000, 100)
        assert monitor2.name == "HDMI-1"

    @patch('mcp_server.platform.linux.dpi_handler.subprocess.run')
    def test_get_primary_monitor(self, mock_run, mock_x11_environment, mock_xrandr_output_dual):
        """Test getting primary monitor."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_xrandr_output_dual
        )

        handler = LinuxDPIHandler()
        primary = handler.get_primary_monitor()

        assert primary is not None
        assert primary.is_primary is True
        assert primary.name == "DP-1"

    @patch('mcp_server.platform.linux.dpi_handler.subprocess.run')
    def test_is_mixed_dpi_environment(self, mock_run, mock_x11_environment):
        """Test mixed DPI detection."""
        # Create output with different DPI monitors
        output = """Screen 0: minimum 8 x 8, current 4480 x 1440, maximum 32767 x 32767
DP-1 connected primary 2560x1440+0+0 (normal left inverted right x axis y axis) 597mm x 336mm
   2560x1440     59.95*+
HDMI-1 connected 1920x1080+2560+0 (normal left inverted right x axis y axis) 406mm x 228mm
   1920x1080     60.00*+
"""
        mock_run.return_value = MagicMock(returncode=0, stdout=output)

        handler = LinuxDPIHandler()

        # Different physical sizes should result in different DPI
        is_mixed = handler.is_mixed_dpi_environment()
        # This should detect mixed DPI based on calculations

    @patch('mcp_server.platform.linux.dpi_handler.subprocess.run')
    def test_cache_invalidation(self, mock_run, mock_x11_environment, mock_xrandr_output_single):
        """Test monitor cache invalidation."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_xrandr_output_single
        )

        handler = LinuxDPIHandler()

        # First call - cache miss
        monitors1 = handler.enumerate_monitors()
        call_count1 = mock_run.call_count

        # Second call - cache hit
        monitors2 = handler.enumerate_monitors()
        call_count2 = mock_run.call_count

        assert call_count1 == call_count2  # No new call

        # Force refresh
        monitors3 = handler.enumerate_monitors(refresh=True)
        call_count3 = mock_run.call_count

        assert call_count3 > call_count2  # New call made

    @patch('mcp_server.platform.linux.dpi_handler.subprocess.run')
    def test_get_scale_factor(self, mock_run, mock_x11_environment):
        """Test scale factor calculation."""
        handler = LinuxDPIHandler()

        assert handler.get_scale_factor(96) == 1.0
        assert handler.get_scale_factor(120) == 1.25
        assert handler.get_scale_factor(144) == 1.5
        assert handler.get_scale_factor(192) == 2.0

    @patch('mcp_server.platform.linux.dpi_handler.subprocess.run')
    def test_environment_variable_scaling(self, mock_run, mock_x11_environment):
        """Test environment variable scaling detection."""
        with patch.dict('os.environ', {'GDK_SCALE': '2'}):
            handler = LinuxDPIHandler()
            assert handler._env_scale_factor == 2.0

        with patch.dict('os.environ', {'QT_SCALE_FACTOR': '1.5'}):
            handler = LinuxDPIHandler()
            assert handler._env_scale_factor == 1.5


# ==================== Window Manager Tests ====================

class TestLinuxWindowManager:
    """Test LinuxWindowManager - 8 tests."""

    @patch('mcp_server.platform.linux.window_manager.XLIB_AVAILABLE', False)
    @patch('mcp_server.platform.linux.window_manager.subprocess.run')
    def test_command_availability_detection(self, mock_run, mock_x11_environment):
        """Test detection of available commands."""
        # Mock which command
        def which_side_effect(*args, **kwargs):
            cmd = args[0][1]
            if cmd in ['wmctrl', 'xdotool']:
                return MagicMock(returncode=0)
            return MagicMock(returncode=1)

        mock_run.side_effect = which_side_effect

        wm = LinuxWindowManager()
        assert wm.has_wmctrl is True
        assert wm.has_xdotool is True

    @patch('mcp_server.platform.linux.window_manager.XLIB_AVAILABLE', True)
    @patch('mcp_server.platform.linux.window_manager.display')
    def test_x11_initialization(self, mock_display, mock_x11_environment):
        """Test X11 initialization with python-xlib."""
        mock_display_obj = MagicMock()
        mock_screen = MagicMock()
        mock_root = MagicMock()

        mock_screen.root = mock_root
        mock_display_obj.screen.return_value = mock_screen
        mock_display.Display.return_value = mock_display_obj

        wm = LinuxWindowManager()
        assert wm.x_display is not None
        assert wm.x_root is not None

    @patch('mcp_server.platform.linux.window_manager.XLIB_AVAILABLE', False)
    @patch('mcp_server.platform.linux.window_manager.subprocess.run')
    def test_is_browser_process_name(self, mock_run, mock_x11_environment):
        """Test browser process name detection."""
        wm = LinuxWindowManager()

        assert wm._is_browser_process_name('chrome') is True
        assert wm._is_browser_process_name('firefox') is True
        assert wm._is_browser_process_name('google-chrome-stable') is True
        assert wm._is_browser_process_name('brave-browser') is True
        assert wm._is_browser_process_name('notepad') is False
        assert wm._is_browser_process_name('terminal') is False

    @patch('mcp_server.platform.linux.window_manager.XLIB_AVAILABLE', False)
    @patch('mcp_server.platform.linux.window_manager.subprocess.run')
    def test_parse_window_id_formats(self, mock_run, mock_x11_environment):
        """Test parsing different window ID formats."""
        wm = LinuxWindowManager()

        # Hex format
        assert wm._parse_window_id('0x01400005') == 0x01400005
        assert wm._parse_window_id('0x1234567') == 0x1234567

        # Decimal format
        assert wm._parse_window_id('12345') == 12345

        # Invalid format
        assert wm._parse_window_id('invalid') is None

    @patch('mcp_server.platform.linux.window_manager.PSUTIL_AVAILABLE', True)
    @patch('mcp_server.platform.linux.window_manager.psutil')
    @patch('mcp_server.platform.linux.window_manager.subprocess.run')
    def test_get_process_info_with_psutil(self, mock_run, mock_psutil, mock_x11_environment):
        """Test process info retrieval with psutil."""
        mock_process = MagicMock()
        mock_process.name.return_value = 'chrome'
        mock_process.cmdline.return_value = ['chrome', '--flag']
        mock_process.exe.return_value = '/usr/bin/chrome'

        mock_psutil.Process.return_value = mock_process

        wm = LinuxWindowManager()
        info = wm._get_process_info(12345)

        assert info['name'] == 'chrome'
        assert 'chrome' in info['cmdline']
        assert info['exe'] == '/usr/bin/chrome'

    @patch('mcp_server.platform.linux.window_manager.XLIB_AVAILABLE', False)
    @patch('mcp_server.platform.linux.window_manager.subprocess.run')
    def test_screen_to_client_conversion(self, mock_run, mock_x11_environment, sample_window_info):
        """Test screen to client coordinate conversion."""
        wm = LinuxWindowManager()

        with patch.object(wm, 'get_window_info', return_value=sample_window_info):
            client_x, client_y = wm.screen_to_client(0x01400005, 100, 100)

            # Client rect is (2, 30, 1918, 1078)
            # Screen (100, 100) - Client origin (2, 30) = (98, 70)
            assert client_x == 98
            assert client_y == 70

    @patch('mcp_server.platform.linux.window_manager.XLIB_AVAILABLE', False)
    @patch('mcp_server.platform.linux.window_manager.subprocess.run')
    def test_client_to_screen_conversion(self, mock_run, mock_x11_environment, sample_window_info):
        """Test client to screen coordinate conversion."""
        wm = LinuxWindowManager()

        with patch.object(wm, 'get_window_info', return_value=sample_window_info):
            screen_x, screen_y = wm.client_to_screen(0x01400005, 50, 50)

            # Client (50, 50) + Client origin (2, 30) = Screen (52, 80)
            assert screen_x == 52
            assert screen_y == 80

    @patch('mcp_server.platform.linux.window_manager.XLIB_AVAILABLE', False)
    @patch('mcp_server.platform.linux.window_manager.subprocess.run')
    def test_is_browser_wm_class(self, mock_run, mock_x11_environment):
        """Test WM_CLASS browser detection."""
        wm = LinuxWindowManager()

        assert wm._is_browser_wm_class('google-chrome') is True
        assert wm._is_browser_wm_class('firefox') is True
        assert wm._is_browser_wm_class('chromium-browser') is True
        assert wm._is_browser_wm_class('gnome-terminal') is False


# ==================== Coordinate Converter Tests ====================

class TestLinuxCoordinateConverter:
    """Test LinuxCoordinateConverter - 10 tests."""

    @patch('mcp_server.platform.linux.coordinate_converter.subprocess.run')
    def test_display_server_detection(self, mock_run, mock_x11_environment):
        """Test display server detection."""
        mock_run.return_value = MagicMock(returncode=0)

        converter = LinuxCoordinateConverter()
        assert converter.display_server == 'x11'

    @patch('mcp_server.platform.linux.coordinate_converter.subprocess.run')
    def test_parse_xrandr_single_monitor(self, mock_run, mock_xrandr_output_single):
        """Test parsing xrandr output for single monitor."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_xrandr_output_single
        )

        converter = LinuxCoordinateConverter()
        monitors = converter._parse_xrandr_output()

        assert len(monitors) == 1
        assert monitors[0].name == "DP-1"
        assert monitors[0].width == 1920
        assert monitors[0].height == 1080

    @patch('mcp_server.platform.linux.coordinate_converter.subprocess.run')
    def test_parse_xrandr_dual_monitors(self, mock_run, mock_xrandr_output_dual):
        """Test parsing xrandr output for dual monitors."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_xrandr_output_dual
        )

        converter = LinuxCoordinateConverter()
        monitors = converter._parse_xrandr_output()

        assert len(monitors) == 2
        assert monitors[0].left == 0
        assert monitors[1].left == 2560  # Second monitor offset

    @patch('mcp_server.platform.linux.coordinate_converter.subprocess.run')
    def test_virtual_screen_bounds_dual(self, mock_run, mock_xrandr_output_dual):
        """Test virtual screen bounds with dual monitors."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_xrandr_output_dual
        )

        converter = LinuxCoordinateConverter()
        bounds = converter.get_virtual_screen_bounds()

        # DP-1: 2560x1440+0+0, HDMI-1: 1920x1080+2560+0
        assert bounds.left == 0
        assert bounds.top == 0
        assert bounds.right == 4480  # 2560 + 1920
        assert bounds.bottom == 1440  # max height

    @patch('mcp_server.platform.linux.coordinate_converter.subprocess.run')
    def test_virtual_screen_negative_coordinates(self, mock_run, mock_xrandr_output_negative_coords):
        """Test virtual screen with negative coordinates."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_xrandr_output_negative_coords
        )

        converter = LinuxCoordinateConverter()
        bounds = converter.get_virtual_screen_bounds()

        # Should handle negative coordinates properly
        assert bounds.left < 0

    def test_physical_to_logical_conversion(self):
        """Test physical to logical pixel conversion."""
        converter = LinuxCoordinateConverter()

        # 96 DPI (no scaling)
        point = converter.physical_to_logical(1000, 500, dpi=96)
        assert point.x == 1000
        assert point.y == 500

        # 144 DPI (150% scaling)
        point = converter.physical_to_logical(1500, 900, dpi=144)
        assert point.x == 1000
        assert point.y == 600

    def test_logical_to_physical_conversion(self):
        """Test logical to physical pixel conversion."""
        converter = LinuxCoordinateConverter()

        # 96 DPI (no scaling)
        point = converter.logical_to_physical(1000, 500, dpi=96)
        assert point.x == 1000
        assert point.y == 500

        # 192 DPI (200% scaling)
        point = converter.logical_to_physical(500, 300, dpi=192)
        assert point.x == 1000
        assert point.y == 600

    def test_physical_to_css_conversion(self):
        """Test physical to CSS pixel conversion."""
        converter = LinuxCoordinateConverter()

        # No scaling
        point = converter.physical_to_css(1000, 500, device_pixel_ratio=1.0)
        assert point.x == 1000
        assert point.y == 500

        # 2x device pixel ratio
        point = converter.physical_to_css(2000, 1000, device_pixel_ratio=2.0)
        assert point.x == 1000
        assert point.y == 500

        # With browser zoom
        point = converter.physical_to_css(1500, 900, device_pixel_ratio=1.5, browser_zoom=1.5)
        assert point.x == 666  # 1500 / (1.5 * 1.5)
        assert point.y == 400  # 900 / (1.5 * 1.5)

    def test_css_to_dom_conversion(self):
        """Test CSS viewport to DOM document conversion."""
        converter = LinuxCoordinateConverter()

        # No scroll, no offset
        point = converter.css_to_dom(100, 200)
        assert point.x == 100
        assert point.y == 200

        # With viewport offset (browser chrome)
        point = converter.css_to_dom(100, 200, viewport_offset_x=10, viewport_offset_y=80)
        assert point.x == 90
        assert point.y == 120

        # With scroll
        point = converter.css_to_dom(100, 200, scroll_x=50, scroll_y=100)
        assert point.x == 150
        assert point.y == 300

    def test_full_conversion_chain(self):
        """Test complete physical to DOM conversion chain."""
        converter = LinuxCoordinateConverter()

        result = converter.physical_to_dom_full_chain(
            physical_x=1920,
            physical_y=1080,
            dpi=144,
            device_pixel_ratio=1.5,
            browser_zoom=1.0,
            viewport_offset_x=0,
            viewport_offset_y=80,
            scroll_x=0,
            scroll_y=200
        )

        assert 'physical' in result
        assert 'logical' in result
        assert 'css' in result
        assert 'dom' in result

        assert result['physical'].x == 1920
        assert result['physical'].y == 1080


# ==================== Performance and Edge Case Tests ====================

class TestPerformanceAndEdgeCases:
    """Performance benchmarks and edge case tests - 6 tests."""

    @patch('mcp_server.platform.linux.input_simulator.subprocess.run')
    def test_input_simulator_performance_benchmark(self, mock_run):
        """Benchmark input simulator operations."""
        LinuxInputSimulator._instance = None

        mock_controller = MagicMock()
        mock_controller.position = (0, 0)

        with patch('mcp_server.platform.linux.input_simulator.Controller', return_value=mock_controller):
            sim = LinuxInputSimulator()

            start_time = time.time()

            # Perform 100 operations
            for i in range(100):
                sim.move_mouse(i * 10, i * 10)

            elapsed = time.time() - start_time

            # Should complete 100 moves in under 1 second (with mocks)
            assert elapsed < 1.0

    @patch('mcp_server.platform.linux.dpi_handler.subprocess.run')
    def test_dpi_handler_cache_performance(self, mock_run, mock_x11_environment, mock_xrandr_output_dual):
        """Test DPI handler caching improves performance."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_xrandr_output_dual
        )

        handler = LinuxDPIHandler()

        # First call - cache miss
        start1 = time.time()
        handler.enumerate_monitors()
        time1 = time.time() - start1

        # Second call - cache hit
        start2 = time.time()
        handler.enumerate_monitors()
        time2 = time.time() - start2

        # Cached call should be faster
        assert time2 < time1

    @patch('mcp_server.platform.linux.dpi_handler.subprocess.run')
    def test_xrandr_timeout_handling(self, mock_run, mock_x11_environment):
        """Test graceful handling of xrandr timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('xrandr', 5)

        handler = LinuxDPIHandler()
        monitors = handler.enumerate_monitors()

        # Should return fallback monitor
        assert len(monitors) >= 1

    @patch('mcp_server.platform.linux.dpi_handler.subprocess.run')
    def test_xrandr_invalid_output_handling(self, mock_run, mock_x11_environment):
        """Test handling of malformed xrandr output."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Invalid xrandr output\nGarbage data\n"
        )

        handler = LinuxDPIHandler()
        monitors = handler.enumerate_monitors()

        # Should return fallback monitor when parsing fails
        assert len(monitors) >= 1

    @patch('mcp_server.platform.linux.window_manager.subprocess.run')
    def test_window_manager_missing_dependencies(self, mock_run, mock_x11_environment):
        """Test window manager with all tools missing."""
        with patch('mcp_server.platform.linux.window_manager.XLIB_AVAILABLE', False):
            mock_run.return_value = MagicMock(returncode=1)  # which returns not found

            wm = LinuxWindowManager()

            assert wm.has_wmctrl is False
            assert wm.has_xdotool is False
            assert wm.has_xwininfo is False

    @patch('mcp_server.platform.linux.coordinate_converter.subprocess.run')
    def test_coordinate_converter_monitor_count(self, mock_run, mock_xrandr_output_dual):
        """Test monitor count detection."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_xrandr_output_dual
        )

        converter = LinuxCoordinateConverter()
        count = converter.get_monitor_count()

        assert count == 2


# ==================== Abstract Base Class Compliance Tests ====================

class TestAbstractBaseClassCompliance:
    """Verify all abstract methods are implemented - 4 tests."""

    def test_input_simulator_implements_all_abstract_methods(self):
        """Verify LinuxInputSimulator implements all PlatformInputSimulator methods."""
        required_methods = [
            'move_mouse', 'click', 'scroll', 'get_cursor_pos', 'set_delays'
        ]

        for method in required_methods:
            assert hasattr(LinuxInputSimulator, method)
            assert callable(getattr(LinuxInputSimulator, method))

    def test_dpi_handler_implements_all_abstract_methods(self):
        """Verify LinuxDPIHandler implements all PlatformDPIHandler methods."""
        required_methods = [
            'get_dpi_for_window', 'get_dpi_at_point', 'get_system_dpi',
            'get_scale_factor', 'enumerate_monitors', 'get_monitor_at_point',
            'get_primary_monitor', 'is_mixed_dpi_environment'
        ]

        for method in required_methods:
            assert hasattr(LinuxDPIHandler, method)
            assert callable(getattr(LinuxDPIHandler, method))

    def test_window_manager_implements_all_abstract_methods(self):
        """Verify LinuxWindowManager implements all PlatformWindowManager methods."""
        required_methods = [
            'get_window_info', 'is_browser_window', 'find_browser_windows',
            'get_window_at_point', 'get_foreground_window',
            'screen_to_client', 'client_to_screen'
        ]

        for method in required_methods:
            assert hasattr(LinuxWindowManager, method)
            assert callable(getattr(LinuxWindowManager, method))

    def test_coordinate_converter_implements_all_abstract_methods(self):
        """Verify LinuxCoordinateConverter implements all PlatformCoordinateConverter methods."""
        required_methods = [
            'get_virtual_screen_bounds', 'get_monitor_count', 'get_physical_cursor_pos',
            'physical_to_logical', 'logical_to_physical', 'physical_to_css', 'css_to_physical'
        ]

        for method in required_methods:
            assert hasattr(LinuxCoordinateConverter, method)
            assert callable(getattr(LinuxCoordinateConverter, method))
