"""
Main MCP Server Implementation for Accurate Click Server

Implements the Model Context Protocol (MCP) server for browser automation
with accurate click capabilities.
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .config import ServerConfig, get_config_manager, init_config
from .tools import get_tool_registry, init_tool_registry
from .handlers import ToolHandlers, HandlerResult


logger = logging.getLogger(__name__)


class MCPAccurateClickServer:
    """
    MCP Server for Accurate Click automation

    Provides browser automation capabilities via MCP protocol with:
    - Accurate element clicking
    - Multiple identification methods
    - Coordinate transformation
    - Comprehensive validation
    """

    def __init__(self, config: Optional[ServerConfig] = None):
        """
        Initialize MCP server

        Args:
            config: Server configuration (uses defaults if None)
        """
        # Initialize configuration
        self.config_manager = init_config(config)
        self.config = self.config_manager.config
        self.logger = self.config_manager.logger

        # Initialize tool registry
        self.tool_registry = init_tool_registry()

        # Browser instances
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        # Tool handlers
        self._handlers: Optional[ToolHandlers] = None

        # Server state
        self._running = False
        self._request_count = 0
        self._active_requests = 0

        self.logger.info(f"Initialized {self.config.name} v{self.config.version}")

    # ========================================================================
    # LIFECYCLE MANAGEMENT
    # ========================================================================

    async def start(self):
        """Start the MCP server and browser"""
        if self._running:
            self.logger.warning("Server already running")
            return

        self.logger.info("Starting MCP Accurate Click Server...")

        try:
            # Start Playwright
            self._playwright = await async_playwright().start()

            # Launch browser
            browser_type = getattr(self._playwright, self.config.browser_type)
            self._browser = await browser_type.launch(
                headless=self.config.headless,
                timeout=self.config.browser_timeout
            )

            # Create context
            self._context = await self._browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="MCP-Accurate-Click-Server/1.0"
            )

            # Create page
            self._page = await self._context.new_page()

            # Set default timeout
            self._page.set_default_timeout(self.config.browser_timeout)

            # Initialize handlers
            self._handlers = ToolHandlers(self._page)

            self._running = True

            self.logger.info(f"Server started successfully ({self.config.browser_type} browser)")

        except Exception as e:
            self.logger.error(f"Failed to start server: {e}", exc_info=True)
            await self.stop()
            raise

    async def stop(self):
        """Stop the MCP server and cleanup"""
        if not self._running:
            return

        self.logger.info("Stopping MCP Accurate Click Server...")

        try:
            # Close page
            if self._page:
                await self._page.close()
                self._page = None

            # Close context
            if self._context:
                await self._context.close()
                self._context = None

            # Close browser
            if self._browser:
                await self._browser.close()
                self._browser = None

            # Stop playwright
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

            self._handlers = None
            self._running = False

            self.logger.info("Server stopped successfully")

        except Exception as e:
            self.logger.error(f"Error stopping server: {e}", exc_info=True)

    async def restart(self):
        """Restart the server"""
        self.logger.info("Restarting server...")
        await self.stop()
        await self.start()

    @asynccontextmanager
    async def running(self):
        """Context manager for server lifecycle"""
        await self.start()
        try:
            yield self
        finally:
            await self.stop()

    # ========================================================================
    # MCP PROTOCOL METHODS
    # ========================================================================

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools (MCP protocol)

        Returns:
            List of tool schemas
        """
        self.logger.debug("Listing tools")

        tools = self.tool_registry.get_schemas()

        # Filter by enabled status if configured
        enabled_tools = [
            tool for tool in tools
            if self.config_manager.is_tool_enabled(tool["name"])
        ]

        return enabled_tools

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool (MCP protocol)

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if not self._running:
            return {
                "success": False,
                "error": "Server not running"
            }

        # Rate limiting check
        if self._active_requests >= self.config.max_concurrent_requests:
            return {
                "success": False,
                "error": f"Too many concurrent requests (max: {self.config.max_concurrent_requests})"
            }

        # Validate tool exists
        tool = self.tool_registry.get(name)
        if not tool:
            return {
                "success": False,
                "error": f"Unknown tool: {name}"
            }

        # Validate tool enabled
        if not self.config_manager.is_tool_enabled(name):
            return {
                "success": False,
                "error": f"Tool disabled: {name}"
            }

        # Validate parameters
        is_valid, error_msg = self.tool_registry.validate_parameters(name, arguments)
        if not is_valid:
            return {
                "success": False,
                "error": f"Invalid parameters: {error_msg}"
            }

        # Execute tool with timeout
        self._active_requests += 1
        self._request_count += 1

        try:
            self.logger.info(f"Executing tool: {name} (request #{self._request_count})")

            result = await asyncio.wait_for(
                self._execute_tool(name, arguments),
                timeout=self.config.request_timeout_seconds
            )

            return result.to_dict()

        except asyncio.TimeoutError:
            self.logger.error(f"Tool execution timeout: {name}")
            return {
                "success": False,
                "error": f"Tool execution timeout after {self.config.request_timeout_seconds}s"
            }

        except Exception as e:
            self.logger.error(f"Tool execution error: {name}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Tool execution error: {str(e)}"
            }

        finally:
            self._active_requests -= 1

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> HandlerResult:
        """Internal tool execution dispatcher"""

        if not self._handlers:
            raise RuntimeError("Handlers not initialized")

        # Route to appropriate handler
        if name == "click_element":
            return await self._handlers.handle_click_element(arguments)

        elif name == "find_element":
            return await self._handlers.handle_find_element(arguments)

        elif name == "get_dom_structure":
            return await self._handlers.handle_get_dom_structure(arguments)

        elif name == "validate_click":
            return await self._handlers.handle_validate_click(arguments)

        else:
            return HandlerResult(
                success=False,
                data={},
                error=f"Handler not implemented for tool: {name}"
            )

    # ========================================================================
    # BROWSER CONTROL
    # ========================================================================

    async def navigate(self, url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
        """
        Navigate to URL

        Args:
            url: URL to navigate to
            wait_until: Wait condition (load, domcontentloaded, networkidle)

        Returns:
            Navigation result
        """
        if not self._page:
            return {
                "success": False,
                "error": "Page not initialized"
            }

        try:
            self.logger.info(f"Navigating to: {url}")

            response = await self._page.goto(url, wait_until=wait_until)

            return {
                "success": True,
                "url": self._page.url,
                "title": await self._page.title(),
                "status": response.status if response else None
            }

        except Exception as e:
            self.logger.error(f"Navigation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_page_info(self) -> Dict[str, Any]:
        """Get current page information"""
        if not self._page:
            return {"error": "Page not initialized"}

        return {
            "url": self._page.url,
            "title": await self._page.title(),
            "viewport": self._page.viewport_size
        }

    async def screenshot(self, path: Optional[str] = None, full_page: bool = False) -> Dict[str, Any]:
        """
        Take page screenshot

        Args:
            path: Save path (auto-generated if None)
            full_page: Capture full scrollable page

        Returns:
            Screenshot info
        """
        if not self._page:
            return {
                "success": False,
                "error": "Page not initialized"
            }

        try:
            if not path:
                path = str(self.config.screenshot_dir / f"screenshot_{int(asyncio.get_event_loop().time() * 1000)}.png")

            await self._page.screenshot(path=path, full_page=full_page)

            return {
                "success": True,
                "path": path,
                "full_page": full_page
            }

        except Exception as e:
            self.logger.error(f"Screenshot error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ========================================================================
    # SERVER INFO & STATS
    # ========================================================================

    def get_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            "name": self.config.name,
            "version": self.config.version,
            "running": self._running,
            "browser": {
                "type": self.config.browser_type,
                "headless": self.config.headless,
                "connected": self._browser is not None
            },
            "statistics": {
                "total_requests": self._request_count,
                "active_requests": self._active_requests
            },
            "tools": {
                "available": len(self.tool_registry.list_tools()),
                "enabled": len([
                    t for t in self.tool_registry.list_tools()
                    if self.config_manager.is_tool_enabled(t)
                ])
            }
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        return {
            "total_requests": self._request_count,
            "active_requests": self._active_requests,
            "max_concurrent": self.config.max_concurrent_requests,
            "uptime": "N/A"  # Would need start time tracking
        }

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def is_running(self) -> bool:
        """Check if server is running"""
        return self._running

    def get_page(self) -> Optional[Page]:
        """Get current page instance (for advanced usage)"""
        return self._page

    async def execute_script(self, script: str) -> Any:
        """
        Execute JavaScript in page context

        Args:
            script: JavaScript code to execute

        Returns:
            Script result
        """
        if not self._page:
            raise RuntimeError("Page not initialized")

        return await self._page.evaluate(script)


# ============================================================================
# STDIO MCP SERVER (for MCP protocol over stdio)
# ============================================================================

class StdioMCPServer:
    """
    MCP Server with stdio transport

    Implements MCP protocol over stdin/stdout for integration
    with MCP clients.
    """

    def __init__(self, server: MCPAccurateClickServer):
        """
        Initialize stdio MCP server

        Args:
            server: Underlying server instance
        """
        self.server = server
        self.logger = logging.getLogger(f"{__name__}.StdioMCPServer")

    async def run(self):
        """Run stdio MCP server loop"""
        self.logger.info("Starting stdio MCP server...")

        await self.server.start()

        try:
            # Read from stdin, write to stdout
            while True:
                try:
                    # Read JSON-RPC message from stdin
                    line = await asyncio.get_event_loop().run_in_executor(
                        None, input
                    )

                    if not line:
                        break

                    # Parse request
                    try:
                        request = json.loads(line)
                    except json.JSONDecodeError as e:
                        self._write_error(-32700, "Parse error", str(e))
                        continue

                    # Handle request
                    response = await self._handle_request(request)

                    # Write response
                    self._write_response(response)

                except EOFError:
                    break

                except Exception as e:
                    self.logger.error(f"Error in stdio loop: {e}", exc_info=True)

        finally:
            await self.server.stop()

    async def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON-RPC request"""

        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        # Handle different MCP methods
        if method == "tools/list":
            result = await self.server.list_tools()

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result = await self.server.call_tool(tool_name, arguments)

        elif method == "server/info":
            result = self.server.get_info()

        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": "Method not found",
                    "data": {"method": method}
                }
            }

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    def _write_response(self, response: Dict[str, Any]):
        """Write JSON-RPC response to stdout"""
        print(json.dumps(response), flush=True)

    def _write_error(self, code: int, message: str, data: Any = None):
        """Write JSON-RPC error to stdout"""
        error = {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message
            }
        }

        if data:
            error["error"]["data"] = data

        print(json.dumps(error), flush=True)


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_server(config: Optional[ServerConfig] = None) -> MCPAccurateClickServer:
    """
    Create MCP server instance

    Args:
        config: Server configuration

    Returns:
        Configured server instance
    """
    return MCPAccurateClickServer(config)


async def create_and_start_server(config: Optional[ServerConfig] = None) -> MCPAccurateClickServer:
    """
    Create and start MCP server

    Args:
        config: Server configuration

    Returns:
        Running server instance
    """
    server = create_server(config)
    await server.start()
    return server
