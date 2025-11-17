"""
Pytest Configuration for Platform Tests

Provides shared fixtures, mocks, and utilities for platform testing.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List

# Import base classes at module level for fixtures
from mcp_server.platform.base import MouseButton


# ==================== Platform Detection Fixtures ====================

@pytest.fixture
def platform_name():
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


@pytest.fixture
def is_macos():
    """Check if running on macOS."""
    return sys.platform == 'darwin'


# ==================== Environment Variable Fixtures ====================

@pytest.fixture
def clean_environment():
    """Provide a clean environment without display server variables."""
    env_vars = ['DISPLAY', 'WAYLAND_DISPLAY', 'XDG_SESSION_TYPE',
                'GDK_SCALE', 'GDK_DPI_SCALE', 'QT_SCALE_FACTOR']

    original_values = {}
    for var in env_vars:
        if var in os.environ:
            original_values[var] = os.environ[var]
            del os.environ[var]

    yield

    # Restore original values
    for var, value in original_values.items():
        os.environ[var] = value


@pytest.fixture
def x11_environment():
    """Mock X11 environment."""
    with patch.dict('os.environ', {
        'DISPLAY': ':0',
        'XDG_SESSION_TYPE': 'x11'
    }, clear=False):
        yield


@pytest.fixture
def wayland_environment():
    """Mock Wayland environment."""
    with patch.dict('os.environ', {
        'WAYLAND_DISPLAY': 'wayland-0',
        'XDG_SESSION_TYPE': 'wayland'
    }, clear=False):
        yield


# ==================== Mock Command Output Fixtures ====================

@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for testing."""
    with patch('subprocess.run') as mock_run:
        yield mock_run


@pytest.fixture
def mock_xrandr_single_monitor():
    """Mock xrandr output for single 1080p monitor."""
    return """Screen 0: minimum 8 x 8, current 1920 x 1080, maximum 32767 x 32767
DP-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 527mm x 296mm
   1920x1080     60.00*+  59.94
   1680x1050     59.95
   1280x1024     75.02    60.02
   1280x720      60.00    59.94
"""


@pytest.fixture
def mock_xrandr_dual_monitors_same_dpi():
    """Mock xrandr output for dual monitors, same DPI."""
    return """Screen 0: minimum 8 x 8, current 3840 x 1080, maximum 32767 x 32767
DP-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 527mm x 296mm
   1920x1080     60.00*+
HDMI-1 connected 1920x1080+1920+0 (normal left inverted right x axis y axis) 527mm x 296mm
   1920x1080     60.00*+
"""


@pytest.fixture
def mock_xrandr_dual_monitors_mixed_dpi():
    """Mock xrandr output for dual monitors with different DPI."""
    return """Screen 0: minimum 8 x 8, current 4480 x 1440, maximum 32767 x 32767
DP-1 connected primary 2560x1440+0+0 (normal left inverted right x axis y axis) 597mm x 336mm
   2560x1440     59.95*+
HDMI-1 connected 1920x1080+2560+0 (normal left inverted right x axis y axis) 527mm x 296mm
   1920x1080     60.00*+
"""


@pytest.fixture
def mock_xrandr_triple_monitors():
    """Mock xrandr output for triple monitor setup."""
    return """Screen 0: minimum 8 x 8, current 5760 x 1080, maximum 32767 x 32767
HDMI-1 connected 1920x1080+-1920+0 (normal left inverted right x axis y axis) 527mm x 296mm
   1920x1080     60.00*+
DP-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 527mm x 296mm
   1920x1080     60.00*+
DP-2 connected 1920x1080+1920+0 (normal left inverted right x axis y axis) 527mm x 296mm
   1920x1080     60.00*+
"""


@pytest.fixture
def mock_wmctrl_window_list():
    """Mock wmctrl -lGpx output."""
    return """0x01400005 0 12345 0    0    1920 1080 hostname Google Chrome
0x01600007 0 12346 1920 0    1920 1080 hostname Mozilla Firefox
0x01800009 0 12347 100  100  800  600  hostname gnome-terminal
0x01a0000b 0 12348 0    0    1920 1080 hostname Brave Browser
"""


@pytest.fixture
def mock_wlr_randr_output():
    """Mock wlr-randr output (Wayland)."""
    return """DP-1 "Samsung Electric Company S24D330 0x00000001"
  Physical size: 531x299 mm
  Enabled: yes
  Modes:
    1920x1080 px, 60.000000 Hz (preferred, current)
  Position: 0,0
  Transform: normal
  Scale: 1.000000
"""


# ==================== Mock Python Library Fixtures ====================

@pytest.fixture
def mock_pynput():
    """Mock pynput library."""
    mock_controller = MagicMock()
    mock_controller.position = (0, 0)

    mock_button = MagicMock()
    mock_button.left = 'left'
    mock_button.right = 'right'
    mock_button.middle = 'middle'

    with patch.dict('sys.modules', {
        'pynput': MagicMock(),
        'pynput.mouse': MagicMock(Controller=lambda: mock_controller, Button=mock_button)
    }):
        yield mock_controller


@pytest.fixture
def mock_xlib():
    """Mock python-xlib."""
    mock_display = MagicMock()
    mock_screen = MagicMock()
    mock_root = MagicMock()

    mock_screen.root = mock_root
    mock_display.screen.return_value = mock_screen

    with patch.dict('sys.modules', {
        'Xlib': MagicMock(),
        'Xlib.display': MagicMock(Display=lambda: mock_display),
        'Xlib.X': MagicMock(),
        'Xlib.Xatom': MagicMock(),
    }):
        yield mock_display


@pytest.fixture
def mock_psutil():
    """Mock psutil library."""
    mock_process = MagicMock()
    mock_process.name.return_value = 'test-process'
    mock_process.cmdline.return_value = ['test-process', '--arg']
    mock_process.exe.return_value = '/usr/bin/test-process'

    with patch.dict('sys.modules', {
        'psutil': MagicMock(Process=lambda pid: mock_process)
    }):
        yield mock_process


# ==================== Performance Testing Fixtures ====================

@pytest.fixture
def performance_threshold():
    """Define performance thresholds for tests."""
    return {
        'mouse_move_max_time': 0.1,  # 100ms max for mouse move
        'click_max_time': 0.15,       # 150ms max for click
        'monitor_enum_max_time': 0.5, # 500ms max for monitor enumeration
        'cache_speedup_factor': 10,   # Cache should be 10x faster
    }


# ==================== Mock Data Fixtures ====================

@pytest.fixture
def sample_monitor_single():
    """Sample single monitor configuration."""
    from mcp_server.platform.base import MonitorInfo
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
def sample_monitors_dual():
    """Sample dual monitor configuration."""
    from mcp_server.platform.base import MonitorInfo
    return [
        MonitorInfo(
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
        ),
        MonitorInfo(
            handle="HDMI-1",
            left=1920,
            top=0,
            right=3840,
            bottom=1080,
            dpi_x=96,
            dpi_y=96,
            is_primary=False,
            scale_factor=1.0,
            name="HDMI-1"
        )
    ]


@pytest.fixture
def sample_window_browser():
    """Sample browser window."""
    from mcp_server.platform.base import WindowInfo
    return WindowInfo(
        handle=0x01400005,
        title="Google Chrome - Test Page",
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


# ==================== Parametrize Fixtures ====================

@pytest.fixture(params=[96, 120, 144, 192])
def dpi_values(request):
    """Parametrized DPI values for testing."""
    return request.param


@pytest.fixture(params=[1.0, 1.25, 1.5, 2.0])
def scale_factors(request):
    """Parametrized scale factors for testing."""
    return request.param


@pytest.fixture(params=[
    ('left', MouseButton.LEFT),
    ('right', MouseButton.RIGHT),
    ('middle', MouseButton.MIDDLE),
])
def mouse_buttons(request):
    """Parametrized mouse buttons."""
    return request.param


# ==================== Cleanup Fixtures ====================

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    yield

    # Reset Linux singletons if they exist
    try:
        from mcp_server.platform.linux.input_simulator import LinuxInputSimulator
        LinuxInputSimulator._instance = None
    except ImportError:
        pass

    try:
        from mcp_server.platform.linux.window_manager import _window_manager
        # Reset would go here if needed
    except ImportError:
        pass


# ==================== Helper Functions ====================

def create_mock_monitor(name: str, left: int, top: int, width: int, height: int,
                       dpi: int = 96, is_primary: bool = False):
    """Helper to create MonitorInfo for testing."""
    from mcp_server.platform.base import MonitorInfo
    return MonitorInfo(
        handle=name,
        left=left,
        top=top,
        right=left + width,
        bottom=top + height,
        dpi_x=dpi,
        dpi_y=dpi,
        is_primary=is_primary,
        scale_factor=dpi / 96.0,
        name=name
    )


def create_mock_window(handle: int, title: str, class_name: str,
                      x: int = 0, y: int = 0, width: int = 1920, height: int = 1080):
    """Helper to create WindowInfo for testing."""
    from mcp_server.platform.base import WindowInfo
    return WindowInfo(
        handle=handle,
        title=title,
        class_name=class_name,
        process_id=12345,
        thread_id=0,
        is_visible=True,
        is_minimized=False,
        is_maximized=False,
        window_rect=(x, y, x + width, y + height),
        client_rect=(x + 2, y + 30, x + width - 2, y + height - 2),
        monitor_handle=0
    )
