"""
MCP Accurate Click Server

A Model Context Protocol (MCP) server providing accurate browser
clicking and automation capabilities.

Features:
- Multiple click identification methods (text, selector, coordinates, accessibility)
- Sub-pixel coordinate accuracy
- Comprehensive DOM structure extraction
- Click validation and verification
- Adaptive correction based on feedback
- Production-ready error handling and logging

Usage:
    # As a library
    from mcp_server.core import MCPAccurateClickServer, ServerConfig

    config = ServerConfig.from_env()
    server = MCPAccurateClickServer(config)

    async with server.running():
        await server.navigate("https://example.com")
        result = await server.call_tool("click_element", {
            "method": "by_text",
            "text": "Click me"
        })

    # As a command-line tool
    $ python -m mcp_server.core.server

    # As an MCP stdio server
    $ python -m mcp_server --stdio
"""

__version__ = "1.0.0"
__author__ = "MCP Accurate Click Team"

from .core import (
    MCPAccurateClickServer,
    ServerConfig,
    ConfigManager,
    ToolRegistry,
    ClickMethod,
    CoordinateSystem,
    create_server,
    create_and_start_server,
)

__all__ = [
    "__version__",
    "__author__",
    "MCPAccurateClickServer",
    "ServerConfig",
    "ConfigManager",
    "ToolRegistry",
    "ClickMethod",
    "CoordinateSystem",
    "create_server",
    "create_and_start_server",
    "get_features",
    "print_info",
]


def get_features():
    """Get available features and capabilities"""
    features = {
        "version": __version__,
        "click_methods": [
            "by_text - Find elements by visible text",
            "by_selector - CSS selectors",
            "by_xpath - XPath expressions",
            "by_role - ARIA roles",
            "by_accessibility - Accessible names",
            "by_coordinates - Direct coordinates"
        ],
        "coordinate_systems": [
            "viewport - Browser viewport relative",
            "page - Document page relative",
            "screen - CSS screen coordinates",
            "os_physical - Operating system pixels"
        ],
        "mcp_tools": [
            "click_element - Click on elements",
            "find_element - Find without clicking",
            "get_dom_structure - Extract DOM",
            "validate_click - Pre-validation",
            "calibrate_coordinates - Calibration",
            "get_system_info - System info"
        ],
        "validation": [
            "Pre-click visibility checks",
            "Interactability validation",
            "Stability checks (no animation)",
            "Z-index overlap detection",
            "Confidence scoring (0-100%)",
            "Post-click verification",
            "Retry with exponential backoff",
            "Circuit breaker pattern"
        ],
        "optional_features": {
            "windows": _check_windows_support(),
            "vision": _check_vision_support(),
            "accessibility": True
        }
    }
    return features


def print_info():
    """Print server information and features"""
    print(f"MCP Accurate Click Server v{__version__}")
    print(f"Author: {__author__}")
    print()

    features = get_features()

    print("Click Methods:")
    for method in features["click_methods"]:
        print(f"  • {method}")

    print()
    print("Coordinate Systems:")
    for system in features["coordinate_systems"]:
        print(f"  • {system}")

    print()
    print("MCP Tools:")
    for tool in features["mcp_tools"]:
        print(f"  • {tool}")

    print()
    print("Validation Features:")
    for feature in features["validation"]:
        print(f"  • {feature}")

    print()
    print("Optional Features:")
    opt = features["optional_features"]
    print(f"  • Windows Integration: {'✓ Available' if opt['windows'] else '✗ Not available'}")
    print(f"  • Vision Validation: {'✓ Available' if opt['vision'] else '✗ Not available'}")
    print(f"  • Accessibility Tree: {'✓ Available' if opt['accessibility'] else '✗ Not available'}")


def _check_windows_support():
    """Check if Windows integration is available"""
    try:
        import win32api
        return True
    except ImportError:
        return False


def _check_vision_support():
    """Check if vision validation is available"""
    try:
        import cv2
        return True
    except ImportError:
        return False
