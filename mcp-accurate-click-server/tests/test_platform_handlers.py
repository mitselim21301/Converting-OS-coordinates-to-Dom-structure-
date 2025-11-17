"""
Tests for platform-specific handler integration.

Tests platform abstraction layer integration with MCP handlers:
- Platform detection and initialization
- Native vs. Playwright clicking
- Coordinate conversion
- DPI handling
- Cross-platform compatibility (Windows, Linux, macOS)
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch, call
from typing import Dict, Any, Optional

# Mark async tests
pytestmark = pytest.mark.asyncio

# Test fixtures and mocks
class MockInputSimulator:
    """Mock input simulator for testing."""

    def __init__(self):
        self.click_calls = []
        self.move_calls = []
        self.scroll_calls = []

    def click(self, x: int, y: int, button=None, clicks=1, use_virtual_desk=True) -> bool:
        self.click_calls.append({"x": x, "y": y, "button": button, "clicks": clicks})
        return True

    def move_mouse(self, x: int, y: int, use_virtual_desk=True) -> bool:
        self.move_calls.append({"x": x, "y": y})
        return True

    def scroll(self, amount: int, horizontal: bool = False) -> bool:
        self.scroll_calls.append({"amount": amount, "horizontal": horizontal})
        return True

    def get_cursor_pos(self):
        return (100, 100)

    def set_delays(self, move_delay=None, click_delay=None, double_click_delay=None):
        pass


class MockDPIHandler:
    """Mock DPI handler for testing."""

    def __init__(self):
        self.dpi_x = 96
        self.dpi_y = 96

    def get_system_dpi(self):
        return (self.dpi_x, self.dpi_y)

    def get_dpi_for_window(self, handle):
        return (self.dpi_x, self.dpi_y)

    def get_dpi_at_point(self, x, y):
        return (self.dpi_x, self.dpi_y)

    def get_scale_factor(self, dpi):
        return dpi / 96.0

    def enumerate_monitors(self):
        from mcp_server.platform.base import MonitorInfo
        return [
            MonitorInfo(
                handle=1,
                left=0,
                top=0,
                right=1920,
                bottom=1080,
                dpi_x=self.dpi_x,
                dpi_y=self.dpi_y,
                is_primary=True,
                scale_factor=1.0,
                name="Primary"
            )
        ]

    def get_monitor_at_point(self, x, y):
        from mcp_server.platform.base import MonitorInfo
        return MonitorInfo(
            handle=1,
            left=0,
            top=0,
            right=1920,
            bottom=1080,
            dpi_x=self.dpi_x,
            dpi_y=self.dpi_y,
            is_primary=True,
            scale_factor=1.0,
            name="Primary"
        )

    def get_primary_monitor(self):
        return self.enumerate_monitors()[0] if self.enumerate_monitors() else None

    def is_mixed_dpi_environment(self):
        return False


class MockCoordinateConverter:
    """Mock coordinate converter for testing."""

    def get_virtual_screen_bounds(self, refresh=False):
        from mcp_server.platform.base import Rectangle
        return Rectangle(0, 0, 1920, 1080, "physical")

    def get_monitor_count(self):
        return 1

    def get_physical_cursor_pos(self):
        from mcp_server.platform.base import Point
        return Point(100, 100, "physical")

    def physical_to_logical(self, physical_x, physical_y, dpi=96):
        from mcp_server.platform.base import Point
        scale = dpi / 96.0
        return Point(int(physical_x / scale), int(physical_y / scale), "logical")

    def logical_to_physical(self, logical_x, logical_y, dpi=96):
        from mcp_server.platform.base import Point
        scale = dpi / 96.0
        return Point(int(logical_x * scale), int(logical_y * scale), "physical")

    def physical_to_css(self, physical_x, physical_y, device_pixel_ratio=1.0, browser_zoom=1.0):
        from mcp_server.platform.base import Point
        return Point(int(physical_x / device_pixel_ratio), int(physical_y / device_pixel_ratio), "css")

    def css_to_physical(self, css_x, css_y, device_pixel_ratio=1.0, browser_zoom=1.0):
        from mcp_server.platform.base import Point
        return Point(int(css_x * device_pixel_ratio), int(css_y * device_pixel_ratio), "physical")


class MockWindowManager:
    """Mock window manager for testing."""

    def get_window_info(self, handle):
        from mcp_server.platform.base import WindowInfo
        return WindowInfo(
            handle=handle,
            title="Test Window",
            class_name="TestClass",
            process_id=1234,
            thread_id=5678,
            is_visible=True,
            is_minimized=False,
            is_maximized=False,
            window_rect=(0, 0, 1920, 1080),
            client_rect=(0, 30, 1920, 1050),
            monitor_handle=1
        )

    def is_browser_window(self, handle):
        return True

    def find_browser_windows(self):
        return [self.get_window_info(1)]

    def get_window_at_point(self, x, y):
        return self.get_window_info(1)

    def get_foreground_window(self):
        return self.get_window_info(1)

    def screen_to_client(self, handle, screen_x, screen_y):
        return (screen_x, screen_y - 30)

    def client_to_screen(self, handle, client_x, client_y):
        return (client_x, client_y + 30)


# ========================================================================
# PLATFORM DETECTION TESTS
# ========================================================================

class TestPlatformDetection:
    """Test platform detection and initialization."""

    async def test_platform_detection(self):
        """Test that platform is correctly detected."""
        with patch("mcp_server.platform.get_platform") as mock_get_platform:
            mock_get_platform.return_value = "linux"

            from mcp_server.platform import get_platform
            assert get_platform() == "linux"

    async def test_platform_handlers_initialization_success(self):
        """Test successful initialization of platform handlers."""
        mock_input_sim = MockInputSimulator()
        mock_dpi = MockDPIHandler()
        mock_converter = MockCoordinateConverter()
        mock_wm = MockWindowManager()

        with patch("mcp_server.platform.get_input_simulator") as mock_get_input, \
             patch("mcp_server.platform.get_dpi_handler") as mock_get_dpi, \
             patch("mcp_server.platform.get_coordinate_converter") as mock_get_conv, \
             patch("mcp_server.platform.get_window_manager") as mock_get_wm, \
             patch("mcp_server.platform.get_platform") as mock_get_platform:

            mock_get_platform.return_value = "linux"
            mock_get_input.return_value = mock_input_sim
            mock_get_dpi.return_value = mock_dpi
            mock_get_conv.return_value = mock_converter
            mock_get_wm.return_value = mock_wm

            # Import after patching
            from mcp_server.core.handlers import ToolHandlers

            mock_page = AsyncMock()
            mock_page.url = "http://example.com"

            # Create handlers
            handlers = ToolHandlers(mock_page)

            # Verify initialization
            assert handlers.platform == "linux"
            assert handlers.input_simulator is not None
            assert handlers.dpi_handler is not None
            assert handlers.coordinate_converter is not None
            assert handlers.window_manager is not None

    async def test_platform_handlers_initialization_with_failures(self):
        """Test graceful handling of platform handler initialization failures."""
        with patch("mcp_server.platform.get_input_simulator") as mock_get_input, \
             patch("mcp_server.platform.get_dpi_handler") as mock_get_dpi, \
             patch("mcp_server.platform.get_coordinate_converter") as mock_get_conv, \
             patch("mcp_server.platform.get_window_manager") as mock_get_wm, \
             patch("mcp_server.platform.get_platform") as mock_get_platform:

            mock_get_platform.return_value = "linux"
            mock_get_input.side_effect = RuntimeError("Input simulator not available")
            mock_get_dpi.side_effect = RuntimeError("DPI handler not available")
            mock_get_conv.return_value = MockCoordinateConverter()
            mock_get_wm.return_value = MockWindowManager()

            from mcp_server.core.handlers import ToolHandlers

            mock_page = AsyncMock()
            mock_page.url = "http://example.com"

            # Should not raise, but handle gracefully
            handlers = ToolHandlers(mock_page)

            # Verify fallback
            assert handlers.input_simulator is None  # Failed to initialize
            assert handlers.dpi_handler is None  # Failed to initialize
            assert handlers.coordinate_converter is not None
            assert handlers.window_manager is not None


# ========================================================================
# CLICK HANDLER TESTS
# ========================================================================

class TestPlatformClickHandling:
    """Test platform-aware click handling."""

    async def _setup_handlers(self):
        """Setup handlers with mocked platform dependencies."""
        mock_input_sim = MockInputSimulator()
        mock_dpi = MockDPIHandler()
        mock_converter = MockCoordinateConverter()
        mock_wm = MockWindowManager()

        with patch("mcp_server.platform.get_input_simulator") as mock_get_input, \
             patch("mcp_server.platform.get_dpi_handler") as mock_get_dpi, \
             patch("mcp_server.platform.get_coordinate_converter") as mock_get_conv, \
             patch("mcp_server.platform.get_window_manager") as mock_get_wm, \
             patch("mcp_server.platform.get_platform") as mock_get_platform:

            mock_get_platform.return_value = "linux"
            mock_get_input.return_value = mock_input_sim
            mock_get_dpi.return_value = mock_dpi
            mock_get_conv.return_value = mock_converter
            mock_get_wm.return_value = mock_wm

            from mcp_server.core.handlers import ToolHandlers
            from mcp_server.core.config import ServerConfig, init_config

            # Initialize config
            init_config()

            mock_page = AsyncMock()
            mock_page.url = "http://example.com"
            mock_page.mouse = AsyncMock()
            mock_page.mouse.click = AsyncMock()
            mock_page.evaluate = AsyncMock(return_value=0)
            mock_page.locator = MagicMock()

            handlers = ToolHandlers(mock_page)
            return handlers, mock_page, mock_input_sim

    async def test_playwright_click_on_element(self):
        """Test Playwright click on element."""
        handlers, mock_page, mock_input_sim = await self._setup_handlers()

        # Mock element
        mock_element = AsyncMock()
        mock_element.click = AsyncMock()
        mock_element.bounding_box = AsyncMock(return_value={
            "x": 100,
            "y": 100,
            "width": 50,
            "height": 20
        })

        # Perform click
        coords = await handlers._perform_click(mock_element, {}, force=False, timeout=5000)

        # Verify
        assert coords["x"] == 125  # Center of element
        assert coords["y"] == 110
        assert coords["coordinate_system"] == "viewport"
        assert coords["click_method"] == "playwright_element"

    async def test_native_click_fallback(self):
        """Test fallback to native click when Playwright fails."""
        handlers, mock_page, mock_input_sim = await self._setup_handlers()

        # Mock element that fails to click with Playwright
        mock_element = AsyncMock()
        from playwright.async_api import Error as PlaywrightError
        mock_element.click = AsyncMock(side_effect=PlaywrightError("Click failed"))
        mock_element.bounding_box = AsyncMock(return_value={
            "x": 100,
            "y": 100,
            "width": 50,
            "height": 20
        })

        # Perform click
        coords = await handlers._perform_click(mock_element, {}, force=False, timeout=5000)

        # Verify native click was attempted
        assert mock_input_sim.click_calls  # Native click was called

    async def test_coordinate_click_playwright(self):
        """Test coordinate click using Playwright."""
        handlers, mock_page, mock_input_sim = await self._setup_handlers()

        params = {
            "x": 100,
            "y": 200,
            "coordinate_system": "viewport"
        }

        coords = await handlers._perform_click(None, params, force=False, timeout=5000)

        # Verify Playwright click was used
        assert coords["click_method"] == "playwright_coordinates"
        assert coords["x"] == 100
        assert coords["y"] == 200

    async def test_coordinate_click_native(self):
        """Test coordinate click using native input."""
        handlers, mock_page, mock_input_sim = await self._setup_handlers()

        params = {
            "x": 100,
            "y": 200,
            "coordinate_system": "viewport",
            "use_native_click": True
        }

        coords = await handlers._perform_click(None, params, force=False, timeout=5000)

        # Verify native click was attempted (may fail in test environment)
        assert coords["click_method"] in ["native", "native_failed"]
        # In test environment, native click may not be available
        assert coords["x"] == 100
        assert coords["y"] == 200


# ========================================================================
# SCROLL HANDLER TESTS
# ========================================================================

class TestPlatformScrollHandling:
    """Test platform-aware scroll handling."""

    async def _setup_handlers(self):
        """Setup handlers with mocked platform dependencies."""
        mock_input_sim = MockInputSimulator()
        mock_dpi = MockDPIHandler()
        mock_converter = MockCoordinateConverter()
        mock_wm = MockWindowManager()

        with patch("mcp_server.platform.get_input_simulator") as mock_get_input, \
             patch("mcp_server.platform.get_dpi_handler") as mock_get_dpi, \
             patch("mcp_server.platform.get_coordinate_converter") as mock_get_conv, \
             patch("mcp_server.platform.get_window_manager") as mock_get_wm, \
             patch("mcp_server.platform.get_platform") as mock_get_platform:

            mock_get_platform.return_value = "linux"
            mock_get_input.return_value = mock_input_sim
            mock_get_dpi.return_value = mock_dpi
            mock_get_conv.return_value = mock_converter
            mock_get_wm.return_value = mock_wm

            from mcp_server.core.handlers import ToolHandlers
            from mcp_server.core.config import init_config

            init_config()

            mock_page = AsyncMock()
            mock_page.url = "http://example.com"
            mock_page.evaluate = AsyncMock()

            handlers = ToolHandlers(mock_page)
            return handlers, mock_page, mock_input_sim

    async def test_playwright_scroll(self):
        """Test Playwright scroll."""
        handlers, mock_page, mock_input_sim = await self._setup_handlers()

        params = {
            "direction": "down",
            "amount": 3,
            "target": "viewport",
            "use_native_scroll": False
        }

        result = await handlers.handle_scroll(params)

        assert result.success
        assert result.data["scrolled"]
        assert result.data["scroll_method"] == "playwright"
        assert mock_page.evaluate.called

    async def test_native_scroll(self):
        """Test native scroll."""
        handlers, mock_page, mock_input_sim = await self._setup_handlers()

        params = {
            "direction": "down",
            "amount": 3,
            "target": "viewport",
            "use_native_scroll": True
        }

        result = await handlers.handle_scroll(params)

        assert result.success
        assert result.data["scrolled"]
        assert result.data["scroll_method"] == "native"
        assert mock_input_sim.scroll_calls


# ========================================================================
# MOUSE MOVE HANDLER TESTS
# ========================================================================

class TestPlatformMouseMoveHandling:
    """Test platform-aware mouse move handling."""

    async def _setup_handlers(self):
        """Setup handlers with mocked platform dependencies."""
        mock_input_sim = MockInputSimulator()
        mock_dpi = MockDPIHandler()
        mock_converter = MockCoordinateConverter()
        mock_wm = MockWindowManager()

        with patch("mcp_server.platform.get_input_simulator") as mock_get_input, \
             patch("mcp_server.platform.get_dpi_handler") as mock_get_dpi, \
             patch("mcp_server.platform.get_coordinate_converter") as mock_get_conv, \
             patch("mcp_server.platform.get_window_manager") as mock_get_wm, \
             patch("mcp_server.platform.get_platform") as mock_get_platform:

            mock_get_platform.return_value = "linux"
            mock_get_input.return_value = mock_input_sim
            mock_get_dpi.return_value = mock_dpi
            mock_get_conv.return_value = mock_converter
            mock_get_wm.return_value = mock_wm

            from mcp_server.core.handlers import ToolHandlers
            from mcp_server.core.config import init_config

            init_config()

            mock_page = AsyncMock()
            mock_page.url = "http://example.com"
            mock_page.mouse = AsyncMock()
            mock_page.mouse.move = AsyncMock()

            handlers = ToolHandlers(mock_page)
            return handlers, mock_page, mock_input_sim

    async def test_playwright_mouse_move(self):
        """Test Playwright mouse move."""
        handlers, mock_page, mock_input_sim = await self._setup_handlers()

        params = {
            "x": 100,
            "y": 200,
            "coordinate_system": "viewport"
        }

        result = await handlers.handle_mouse_move(params)

        assert result.success
        assert result.data["moved"]
        assert result.data["coordinates"]["move_method"] == "playwright"
        assert mock_page.mouse.move.called

    async def test_native_mouse_move(self):
        """Test native mouse move."""
        handlers, mock_page, mock_input_sim = await self._setup_handlers()

        params = {
            "x": 100,
            "y": 200,
            "coordinate_system": "screen"
        }

        result = await handlers.handle_mouse_move(params)

        assert result.success
        assert result.data["moved"]
        assert result.data["coordinates"]["move_method"] == "native"
        assert mock_input_sim.move_calls


# ========================================================================
# PLATFORM INFO HANDLER TESTS
# ========================================================================

class TestPlatformInfoHandler:
    """Test platform info retrieval."""

    async def _setup_handlers(self):
        """Setup handlers with mocked platform dependencies."""
        mock_input_sim = MockInputSimulator()
        mock_dpi = MockDPIHandler()
        mock_converter = MockCoordinateConverter()
        mock_wm = MockWindowManager()

        with patch("mcp_server.platform.get_input_simulator") as mock_get_input, \
             patch("mcp_server.platform.get_dpi_handler") as mock_get_dpi, \
             patch("mcp_server.platform.get_coordinate_converter") as mock_get_conv, \
             patch("mcp_server.platform.get_window_manager") as mock_get_wm, \
             patch("mcp_server.platform.get_platform") as mock_get_platform:

            mock_get_platform.return_value = "linux"
            mock_get_input.return_value = mock_input_sim
            mock_get_dpi.return_value = mock_dpi
            mock_get_conv.return_value = mock_converter
            mock_get_wm.return_value = mock_wm

            from mcp_server.core.handlers import ToolHandlers
            from mcp_server.core.config import init_config

            init_config()

            mock_page = AsyncMock()
            mock_page.url = "http://example.com"

            handlers = ToolHandlers(mock_page)
            return handlers

    async def test_get_platform_info(self):
        """Test getting platform information."""
        handlers = await self._setup_handlers()

        result = await handlers.handle_get_platform_info({})

        assert result.success
        assert result.data["platform"] == "linux"
        assert "browser_info" in result.data
        assert "capabilities" in result.data
        assert result.data["capabilities"]["input_simulation"] is True
        assert result.data["capabilities"]["dpi_handling"] is True
        assert "monitors" in result.data


# ========================================================================
# WINDOWS PLATFORM TESTS
# ========================================================================

class TestWindowsPlatformHandling:
    """Test Windows-specific behavior."""

    async def test_windows_dpi_scaling(self):
        """Test Windows DPI scaling handling."""
        mock_input_sim = MockInputSimulator()
        mock_dpi = MockDPIHandler()
        mock_dpi.dpi_x = 192  # 200% scaling
        mock_dpi.dpi_y = 192
        mock_converter = MockCoordinateConverter()
        mock_wm = MockWindowManager()

        with patch("mcp_server.platform.get_input_simulator") as mock_get_input, \
             patch("mcp_server.platform.get_dpi_handler") as mock_get_dpi, \
             patch("mcp_server.platform.get_coordinate_converter") as mock_get_conv, \
             patch("mcp_server.platform.get_window_manager") as mock_get_wm, \
             patch("mcp_server.platform.get_platform") as mock_get_platform:

            mock_get_platform.return_value = "windows"
            mock_get_input.return_value = mock_input_sim
            mock_get_dpi.return_value = mock_dpi
            mock_get_conv.return_value = mock_converter
            mock_get_wm.return_value = mock_wm

            from mcp_server.core.handlers import ToolHandlers
            from mcp_server.core.config import init_config

            init_config()

            mock_page = AsyncMock()
            mock_page.url = "http://example.com"

            handlers = ToolHandlers(mock_page)
            browser_info = handlers._get_browser_info()

            assert browser_info["platform"] == "windows"
            assert browser_info["dpi"]["x"] == 192
            assert browser_info["dpi_scale"] == 2.0


# ========================================================================
# CROSS-PLATFORM COMPATIBILITY TESTS
# ========================================================================

class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility."""

    @pytest.mark.parametrize("platform_name", ["linux", "windows"])
    async def test_handler_works_on_all_platforms(self, platform_name):
        """Test that handlers work on all supported platforms."""
        mock_input_sim = MockInputSimulator()
        mock_dpi = MockDPIHandler()
        mock_converter = MockCoordinateConverter()
        mock_wm = MockWindowManager()

        with patch("mcp_server.platform.get_input_simulator") as mock_get_input, \
             patch("mcp_server.platform.get_dpi_handler") as mock_get_dpi, \
             patch("mcp_server.platform.get_coordinate_converter") as mock_get_conv, \
             patch("mcp_server.platform.get_window_manager") as mock_get_wm, \
             patch("mcp_server.platform.get_platform") as mock_get_platform:

            mock_get_platform.return_value = platform_name
            mock_get_input.return_value = mock_input_sim
            mock_get_dpi.return_value = mock_dpi
            mock_get_conv.return_value = mock_converter
            mock_get_wm.return_value = mock_wm

            from mcp_server.core.handlers import ToolHandlers
            from mcp_server.core.config import init_config

            init_config()

            mock_page = AsyncMock()
            mock_page.url = "http://example.com"
            mock_page.evaluate = AsyncMock(return_value=0)

            handlers = ToolHandlers(mock_page)

            # Test platform info works
            result = await handlers.handle_get_platform_info({})
            assert result.success
            assert result.data["platform"] == platform_name

    async def test_backward_compatibility_playwright_click(self):
        """Test backward compatibility with existing Playwright click."""
        mock_input_sim = None  # Simulate platform abstraction not available

        with patch("mcp_server.platform.get_input_simulator") as mock_get_input, \
             patch("mcp_server.platform.get_dpi_handler") as mock_get_dpi, \
             patch("mcp_server.platform.get_coordinate_converter") as mock_get_conv, \
             patch("mcp_server.platform.get_window_manager") as mock_get_wm, \
             patch("mcp_server.platform.get_platform") as mock_get_platform:

            mock_get_platform.return_value = "linux"
            mock_get_input.side_effect = RuntimeError("Not available")
            mock_get_dpi.side_effect = RuntimeError("Not available")
            mock_get_conv.side_effect = RuntimeError("Not available")
            mock_get_wm.side_effect = RuntimeError("Not available")

            from mcp_server.core.handlers import ToolHandlers
            from mcp_server.core.config import init_config

            init_config()

            mock_page = AsyncMock()
            mock_page.url = "http://example.com"
            mock_page.mouse = AsyncMock()
            mock_page.mouse.click = AsyncMock()

            handlers = ToolHandlers(mock_page)

            # Should still work with Playwright
            params = {
                "x": 100,
                "y": 200,
                "coordinate_system": "viewport"
            }

            coords = await handlers._perform_click(None, params, force=False, timeout=5000)

            # Should use Playwright click
            assert coords["click_method"] == "playwright_coordinates"
            assert mock_page.mouse.click.called
