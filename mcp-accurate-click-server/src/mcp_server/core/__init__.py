"""
MCP Accurate Click Server - Core Module

Core implementation of the Model Context Protocol server for accurate
browser clicking and automation.

Main exports:
- MCPAccurateClickServer: Main server class
- ServerConfig: Server configuration
- ToolRegistry: Tool registration and management
- ToolHandlers: Tool execution handlers

Usage:
    from mcp_server.core import MCPAccurateClickServer, ServerConfig

    # Create and start server
    config = ServerConfig.from_env()
    server = MCPAccurateClickServer(config)

    async with server.running():
        # Server is running
        result = await server.call_tool("click_element", {
            "method": "by_text",
            "text": "Submit"
        })
"""

__version__ = "1.0.0"
__author__ = "MCP Accurate Click Team"

# Configuration
from .config import (
    ServerConfig,
    ToolConfig,
    ConfigManager,
    get_config_manager,
    init_config
)

# Tools
from .tools import (
    ClickMethod,
    CoordinateSystem,
    ToolParameter,
    ToolDefinition,
    ToolRegistry,
    get_tool_registry,
    init_tool_registry,
    # Pre-defined tools
    CLICK_ELEMENT_TOOL,
    FIND_ELEMENT_TOOL,
    GET_DOM_STRUCTURE_TOOL,
    VALIDATE_CLICK_TOOL
)

# Handlers
from .handlers import (
    HandlerResult,
    ToolHandlers,
    create_handlers
)

# Server
from .server import (
    MCPAccurateClickServer,
    StdioMCPServer,
    create_server,
    create_and_start_server
)

# Public API
__all__ = [
    # Version
    "__version__",
    "__author__",

    # Configuration
    "ServerConfig",
    "ToolConfig",
    "ConfigManager",
    "get_config_manager",
    "init_config",

    # Tools
    "ClickMethod",
    "CoordinateSystem",
    "ToolParameter",
    "ToolDefinition",
    "ToolRegistry",
    "get_tool_registry",
    "init_tool_registry",
    "CLICK_ELEMENT_TOOL",
    "FIND_ELEMENT_TOOL",
    "GET_DOM_STRUCTURE_TOOL",
    "VALIDATE_CLICK_TOOL",

    # Handlers
    "HandlerResult",
    "ToolHandlers",
    "create_handlers",

    # Server
    "MCPAccurateClickServer",
    "StdioMCPServer",
    "create_server",
    "create_and_start_server",
]


def get_info():
    """Get module information"""
    return {
        "name": "mcp-accurate-click-server",
        "version": __version__,
        "author": __author__,
        "description": "MCP server for accurate browser clicking and automation",
        "components": {
            "config": "Configuration management",
            "tools": "Tool definitions and registry",
            "handlers": "Tool execution handlers",
            "server": "MCP server implementation"
        }
    }
