"""
Platform Abstraction Layer - Cross-platform support for Windows, Linux, and macOS.

Provides factory functions to get platform-specific implementations and comprehensive
error handling with recovery strategies, retry logic, and error reporting.
"""

import platform as _platform
import logging
from typing import Optional

# Import error handling utilities
from .errors import (
    PlatformException,
    InputSimulationError,
    DPIError,
    WindowManagementError,
    CoordinateConversionError,
    PlatformNotSupportedError,
    ResourceError,
    TimeoutError,
    DisplayServerError,
    RetryConfig,
    retry_with_backoff,
    graceful_degradation,
    RecoveryStrategy,
    RetryRecoveryStrategy,
    DegradationRecoveryStrategy,
    SkipRecoveryStrategy,
    ErrorContext,
    error_context,
    ErrorMetrics,
    ErrorReporter,
    get_error_reporter,
    handle_error,
    LogLevel,
    setup_error_logging,
)

logger = logging.getLogger(__name__)


def get_platform() -> str:
    """
    Get the current platform name.

    Returns:
        Platform name: 'windows', 'linux', or 'darwin' (macOS)
    """
    return _platform.system().lower()


def is_windows() -> bool:
    """Check if running on Windows."""
    return get_platform() == 'windows'


def is_linux() -> bool:
    """Check if running on Linux."""
    return get_platform() == 'linux'


def is_macos() -> bool:
    """Check if running on macOS."""
    return get_platform() == 'darwin'


def get_input_simulator():
    """
    Get platform-specific input simulator.

    Returns:
        Platform-specific InputSimulator instance

    Raises:
        RuntimeError: If platform is not supported
    """
    platform_name = get_platform()

    if platform_name == 'windows':
        from mcp_server.windows.input_simulator import get_input_simulator as get_win_simulator
        return get_win_simulator()
    elif platform_name == 'linux':
        from mcp_server.platform.linux.input_simulator import get_input_simulator as get_linux_simulator
        return get_linux_simulator()
    elif platform_name == 'darwin':
        raise RuntimeError("macOS support is coming soon - platform implementation in progress")
    else:
        raise RuntimeError(f"Unsupported platform: {platform_name}")


def get_dpi_handler():
    """
    Get platform-specific DPI handler.

    Returns:
        Platform-specific DpiHandler instance

    Raises:
        RuntimeError: If platform is not supported
    """
    platform_name = get_platform()

    if platform_name == 'windows':
        from mcp_server.windows.dpi_handler import get_dpi_handler as get_win_dpi
        return get_win_dpi()
    elif platform_name == 'linux':
        from mcp_server.platform.linux.dpi_handler import create_dpi_handler as get_linux_dpi
        return get_linux_dpi()
    elif platform_name == 'darwin':
        raise RuntimeError("macOS support is coming soon - platform implementation in progress")
    else:
        raise RuntimeError(f"Unsupported platform: {platform_name}")


def get_window_manager():
    """
    Get platform-specific window manager.

    Returns:
        Platform-specific WindowManager instance

    Raises:
        RuntimeError: If platform is not supported
    """
    platform_name = get_platform()

    if platform_name == 'windows':
        from mcp_server.windows.window_manager import get_window_manager as get_win_wm
        return get_win_wm()
    elif platform_name == 'linux':
        from mcp_server.platform.linux.window_manager import get_window_manager as get_linux_wm
        return get_linux_wm()
    elif platform_name == 'darwin':
        raise RuntimeError("macOS support is coming soon - platform implementation in progress")
    else:
        raise RuntimeError(f"Unsupported platform: {platform_name}")


def get_coordinate_converter():
    """
    Get platform-specific coordinate converter.

    Returns:
        Platform-specific CoordinateConverter instance

    Raises:
        RuntimeError: If platform is not supported
    """
    platform_name = get_platform()

    if platform_name == 'windows':
        from mcp_server.windows.coordinate_converter import get_converter as get_win_converter
        return get_win_converter()
    elif platform_name == 'linux':
        from mcp_server.platform.linux.coordinate_converter import get_converter as get_linux_converter
        return get_linux_converter()
    elif platform_name == 'darwin':
        raise RuntimeError("macOS support is coming soon - platform implementation in progress")
    else:
        raise RuntimeError(f"Unsupported platform: {platform_name}")


__all__ = [
    # Platform detection
    'get_platform',
    'is_windows',
    'is_linux',
    'is_macos',

    # Platform-specific factories
    'get_input_simulator',
    'get_dpi_handler',
    'get_window_manager',
    'get_coordinate_converter',

    # Error handling - Exceptions
    'PlatformException',
    'InputSimulationError',
    'DPIError',
    'WindowManagementError',
    'CoordinateConversionError',
    'PlatformNotSupportedError',
    'ResourceError',
    'TimeoutError',
    'DisplayServerError',

    # Error handling - Retry & Recovery
    'RetryConfig',
    'retry_with_backoff',
    'graceful_degradation',
    'RecoveryStrategy',
    'RetryRecoveryStrategy',
    'DegradationRecoveryStrategy',
    'SkipRecoveryStrategy',

    # Error handling - Context & Reporting
    'ErrorContext',
    'error_context',
    'ErrorMetrics',
    'ErrorReporter',
    'get_error_reporter',
    'handle_error',

    # Error handling - Logging
    'LogLevel',
    'setup_error_logging',
]
