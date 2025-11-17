"""
Linux Tool Availability Detector

Detects availability of required and optional tools for mcp-accurate-click-server.
Provides alternative tool paths and fallback methods.
"""

import subprocess
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """Tool availability status."""
    AVAILABLE = "available"
    MISSING = "missing"
    INSTALLED_WRONG_LOCATION = "wrong_location"
    VERSION_MISMATCH = "version_mismatch"


class Tool:
    """Represents a Linux tool/command."""

    def __init__(
        self,
        name: str,
        package_name: str = "",
        alternative_names: Optional[List[str]] = None,
        alternative_paths: Optional[List[str]] = None,
        required: bool = False,
        min_version: Optional[str] = None,
        version_flag: str = "--version",
        fallback_tool: Optional[str] = None,
    ):
        """
        Initialize Tool.

        Args:
            name: Primary command name
            package_name: Package name to install
            alternative_names: Alternative command names (e.g., "chromium-browser" for chromium)
            alternative_paths: Alternative paths to search
            required: Whether this tool is required
            min_version: Minimum version required
            version_flag: Flag to get version (--version, -v, etc.)
            fallback_tool: Name of fallback tool if this one is missing
        """
        self.name = name
        self.package_name = package_name or name
        self.alternative_names = alternative_names or []
        self.alternative_paths = alternative_paths or []
        self.required = required
        self.min_version = min_version
        self.version_flag = version_flag
        self.fallback_tool = fallback_tool
        self.status = ToolStatus.MISSING
        self.found_path: Optional[str] = None
        self.version: Optional[str] = None

    def __repr__(self) -> str:
        return f"Tool({self.name}, status={self.status.value})"


class ToolDetector:
    """
    Detects availability of tools required for mcp-accurate-click-server.

    Supports detection for:
    - X11 tools (xdotool, wmctrl, xwininfo, xprop)
    - Display tools (xrandr, arandr)
    - Python libraries
    - Optional tools
    """

    # Essential tools for X11
    X11_TOOLS = {
        'xdotool': Tool(
            'xdotool',
            'xdotool',
            required=True,
            min_version="1.20160805",
            version_flag='--version'
        ),
        'wmctrl': Tool(
            'wmctrl',
            'wmctrl',
            required=True,
            min_version="1.07",
            version_flag='-v'
        ),
        'xwininfo': Tool(
            'xwininfo',
            'x11-utils',
            required=False,
            version_flag='-version'
        ),
        'xprop': Tool(
            'xprop',
            'x11-utils',
            required=False,
            version_flag='-version'
        ),
    }

    # Display tools
    DISPLAY_TOOLS = {
        'xrandr': Tool(
            'xrandr',
            'x11-utils',
            required=False,
            version_flag='--version'
        ),
        'arandr': Tool(
            'arandr',
            'arandr',
            required=False,
            version_flag='--version'
        ),
    }

    # Python library tools
    PYTHON_TOOLS = {
        'pynput': Tool(
            'pynput',
            'python3-pynput',
            alternative_names=['pynput-1.7.6'],
            required=True,
        ),
        'python-xlib': Tool(
            'python-xlib',
            'python3-xlib',
            alternative_names=['Xlib', 'xlib'],
            required=False,
        ),
        'psutil': Tool(
            'psutil',
            'python3-psutil',
            required=False,
        ),
    }

    # All tools registry
    ALL_TOOLS = {**X11_TOOLS, **DISPLAY_TOOLS}

    def __init__(self):
        """Initialize tool detector."""
        self._tools_cache: Dict[str, Tool] = {}
        self._python_modules: Dict[str, bool] = {}

    def detect_all(self) -> Dict[str, Tool]:
        """
        Detect all tools.

        Returns:
            Dictionary of tools with their status
        """
        tools = {}

        # Detect system tools
        for name, tool in self.ALL_TOOLS.items():
            tools[name] = self.detect_tool(name)

        # Detect Python modules
        for name in self.PYTHON_TOOLS.keys():
            self.detect_python_module(name)

        return tools

    def detect_tool(self, tool_name: str) -> Tool:
        """
        Detect availability of a specific tool.

        Args:
            tool_name: Name of tool to detect

        Returns:
            Tool object with updated status
        """
        if tool_name in self._tools_cache:
            return self._tools_cache[tool_name]

        tool = self.ALL_TOOLS.get(tool_name)
        if not tool:
            logger.warning(f"Unknown tool: {tool_name}")
            return Tool(tool_name)

        # Make a copy to avoid modifying the template
        tool = Tool(
            tool.name,
            tool.package_name,
            tool.alternative_names,
            tool.alternative_paths,
            tool.required,
            tool.min_version,
            tool.version_flag,
            tool.fallback_tool,
        )

        # Try to find the tool
        path = self._find_tool(tool)
        if path:
            tool.found_path = path
            tool.status = ToolStatus.AVAILABLE
            tool.version = self._get_version(path, tool.version_flag)
            logger.info(f"Found {tool_name} at {path} (version: {tool.version})")
        else:
            tool.status = ToolStatus.MISSING
            logger.warning(f"Tool not found: {tool_name}")

        self._tools_cache[tool_name] = tool
        return tool

    def detect_python_module(self, module_name: str) -> bool:
        """
        Detect if Python module is available.

        Args:
            module_name: Name of Python module

        Returns:
            True if module is available
        """
        if module_name in self._python_modules:
            return self._python_modules[module_name]

        try:
            __import__(module_name)
            self._python_modules[module_name] = True
            logger.info(f"Python module available: {module_name}")
            return True
        except ImportError:
            self._python_modules[module_name] = False
            logger.warning(f"Python module not available: {module_name}")
            return False

    def _find_tool(self, tool: Tool) -> Optional[str]:
        """
        Find tool in system PATH or alternative paths.

        Args:
            tool: Tool to find

        Returns:
            Path to tool or None if not found
        """
        # Primary tool name
        path = self._check_command(tool.name)
        if path:
            return path

        # Alternative names
        for alt_name in tool.alternative_names:
            path = self._check_command(alt_name)
            if path:
                return path

        # Alternative paths
        for alt_path in tool.alternative_paths:
            if Path(alt_path).exists():
                return alt_path

        return None

    def _check_command(self, command: str) -> Optional[str]:
        """
        Check if command exists in PATH.

        Args:
            command: Command to check

        Returns:
            Full path to command or None
        """
        path = shutil.which(command)
        if path:
            return path

        return None

    def _get_version(self, command: str, version_flag: str = "--version") -> Optional[str]:
        """
        Get version of installed tool.

        Args:
            command: Command to check
            version_flag: Flag to get version

        Returns:
            Version string or None
        """
        try:
            result = subprocess.run(
                [command, version_flag],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                # Extract version (usually first line)
                output = result.stdout.strip().split('\n')[0]
                # Try to extract version number
                import re
                match = re.search(r'(\d+\.\d+(?:\.\d+)?)', output)
                if match:
                    return match.group(1)
                return output

        except Exception as e:
            logger.debug(f"Failed to get version for {command}: {e}")

        return None

    def get_missing_tools(self) -> List[str]:
        """
        Get list of missing required tools.

        Returns:
            List of missing tool names
        """
        missing = []
        for name, tool in self.ALL_TOOLS.items():
            if tool.required:
                detected = self.detect_tool(name)
                if detected.status == ToolStatus.MISSING:
                    missing.append(name)

        return missing

    def get_available_tools(self) -> Dict[str, str]:
        """
        Get all available tools with their paths.

        Returns:
            Dictionary of tool name to path
        """
        available = {}
        for name in self.ALL_TOOLS.keys():
            tool = self.detect_tool(name)
            if tool.status == ToolStatus.AVAILABLE and tool.found_path:
                available[name] = tool.found_path

        return available

    def get_python_modules_status(self) -> Dict[str, bool]:
        """
        Get status of Python modules.

        Returns:
            Dictionary of module name to availability
        """
        status = {}
        for name in self.PYTHON_TOOLS.keys():
            status[name] = self.detect_python_module(name)

        return status

    def has_x11_tools(self) -> bool:
        """Check if minimal X11 tools are available."""
        required_x11 = ['xdotool', 'wmctrl']
        for tool_name in required_x11:
            tool = self.detect_tool(tool_name)
            if tool.status == ToolStatus.MISSING:
                return False

        return True

    def has_python_base(self) -> bool:
        """Check if basic Python dependencies are met."""
        # At least one input method should be available
        has_pynput = self.detect_python_module('pynput')
        has_xlib = self.detect_python_module('python-xlib')

        return has_pynput or has_xlib

    def get_summary(self) -> str:
        """
        Get summary of tool availability.

        Returns:
            Formatted summary string
        """
        lines = ["Tool Availability Summary:", ""]

        # System tools
        lines.append("System Tools:")
        for name, tool in self.ALL_TOOLS.items():
            detected = self.detect_tool(name)
            status = detected.status.value
            version = f"({detected.version})" if detected.version else ""
            req = "[REQUIRED]" if tool.required else "[OPTIONAL]"
            lines.append(f"  {name:15} {status:20} {version:15} {req}")

        # Python modules
        lines.append("")
        lines.append("Python Modules:")
        for name, tool in self.PYTHON_TOOLS.items():
            available = self.detect_python_module(name)
            status = "available" if available else "missing"
            req = "[REQUIRED]" if tool.required else "[OPTIONAL]"
            lines.append(f"  {name:15} {status:20} {req}")

        return "\n".join(lines)


# Global detector instance
_detector: Optional[ToolDetector] = None


def get_tool_detector() -> ToolDetector:
    """Get or create global tool detector."""
    global _detector
    if _detector is None:
        _detector = ToolDetector()
    return _detector


__all__ = [
    'ToolDetector',
    'Tool',
    'ToolStatus',
    'get_tool_detector',
]
