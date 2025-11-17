"""
Linux Setup Module for mcp-accurate-click-server

Provides:
- Distribution detection
- Tool availability checking
- Compatibility matrix
- Setup orchestration
"""

from .detection import (
    DistributionDetector,
    DistributionInfo,
    PackageManager,
    DesktopEnvironment,
    DisplayServer,
    ToolDetector,
    Tool,
    ToolStatus,
)
from .matrix import (
    CompatibilityMatrix,
    DistroFamily,
    PackageInfo,
)

__all__ = [
    # Detection
    'DistributionDetector',
    'DistributionInfo',
    'PackageManager',
    'DesktopEnvironment',
    'DisplayServer',
    'ToolDetector',
    'Tool',
    'ToolStatus',
    # Compatibility
    'CompatibilityMatrix',
    'DistroFamily',
    'PackageInfo',
]
