"""
Linux Detection Module

Provides distribution and tool detection for Linux systems.
"""

from .distro_detector import (
    DistributionDetector,
    DistributionInfo,
    PackageManager,
    DesktopEnvironment,
    DisplayServer,
    get_detector,
)
from .tool_detector import (
    ToolDetector,
    Tool,
    ToolStatus,
    get_tool_detector,
)

__all__ = [
    'DistributionDetector',
    'DistributionInfo',
    'PackageManager',
    'DesktopEnvironment',
    'DisplayServer',
    'get_detector',
    'ToolDetector',
    'Tool',
    'ToolStatus',
    'get_tool_detector',
]
