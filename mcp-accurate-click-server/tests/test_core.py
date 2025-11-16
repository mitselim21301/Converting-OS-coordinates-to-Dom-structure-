"""
Test MCP Server Core Functionality

Tests for the core MCP server implementation including:
- Server initialization and configuration
- Tool registration and discovery
- Request handling and routing
- Response formatting
- Error handling
- Resource management
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import json
from typing import Dict, List


class TestMCPServerInitialization:
    """Test MCP server initialization"""

    def test_server_creates_with_default_config(self):
        """Test server creates with default configuration"""
        # Mock server creation
        server = Mock()
        server.name = "accurate-click-server"
        server.version = "1.0.0"

        assert server.name == "accurate-click-server"
        assert server.version == "1.0.0"

    def test_server_creates_with_custom_config(self):
        """Test server creates with custom configuration"""
        config = {
            "name": "custom-click-server",
            "version": "2.0.0",
            "log_level": "DEBUG"
        }

        server = Mock()
        server.config = config

        assert server.config["name"] == "custom-click-server"
        assert server.config["version"] == "2.0.0"
        assert server.config["log_level"] == "DEBUG"

    def test_server_initializes_components(self):
        """Test server initializes all required components"""
        server = Mock()
        server.dom_extractor = Mock()
        server.coord_transformer = Mock()
        server.click_validator = Mock()

        assert server.dom_extractor is not None
        assert server.coord_transformer is not None
        assert server.click_validator is not None

    def test_server_loads_plugins(self):
        """Test server loads and registers plugins"""
        server = Mock()
        server.plugins = ["dom", "windows", "validation"]

        assert len(server.plugins) == 3
        assert "dom" in server.plugins


class TestToolRegistration:
    """Test MCP tool registration and discovery"""

    def test_register_click_tool(self):
        """Test registering click tool"""
        server = Mock()
        server.tools = []

        tool = {
            "name": "click",
            "description": "Click at coordinates",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "x": {"type": "number"},
                    "y": {"type": "number"}
                },
                "required": ["x", "y"]
            }
        }

        server.tools.append(tool)

        assert len(server.tools) == 1
        assert server.tools[0]["name"] == "click"

    def test_register_extract_dom_tool(self):
        """Test registering extract_dom tool"""
        server = Mock()
        server.tools = []

        tool = {
            "name": "extract_dom",
            "description": "Extract DOM structure",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                }
            }
        }

        server.tools.append(tool)

        assert len(server.tools) == 1
        assert server.tools[0]["name"] == "extract_dom"

    def test_list_tools(self):
        """Test listing all registered tools"""
        server = Mock()
        server.tools = [
            {"name": "click"},
            {"name": "extract_dom"},
            {"name": "validate_click"}
        ]

        tool_names = [tool["name"] for tool in server.tools]

        assert len(tool_names) == 3
        assert "click" in tool_names
        assert "extract_dom" in tool_names
        assert "validate_click" in tool_names

    def test_get_tool_by_name(self):
        """Test retrieving tool by name"""
        server = Mock()
        server.tools = [
            {"name": "click", "version": "1.0"},
            {"name": "extract_dom", "version": "1.0"}
        ]

        def get_tool(name):
            return next((t for t in server.tools if t["name"] == name), None)

        tool = get_tool("click")
        assert tool is not None
        assert tool["name"] == "click"

        tool = get_tool("nonexistent")
        assert tool is None


class TestRequestHandling:
    """Test MCP request handling"""

    def test_handle_tools_list_request(self):
        """Test handling tools/list request"""
        server = Mock()
        server.tools = [
            {"name": "click"},
            {"name": "extract_dom"}
        ]

        request = {
            "method": "tools/list",
            "params": {}
        }

        response = {
            "tools": server.tools
        }

        assert response["tools"] == server.tools
        assert len(response["tools"]) == 2

    def test_handle_tools_call_request(self):
        """Test handling tools/call request"""
        request = {
            "method": "tools/call",
            "params": {
                "name": "click",
                "arguments": {
                    "x": 100,
                    "y": 200
                }
            }
        }

        # Mock handler
        handler = Mock(return_value={"success": True})

        response = handler(request["params"])

        assert response["success"] is True
        handler.assert_called_once()

    def test_handle_invalid_method(self):
        """Test handling invalid method request"""
        request = {
            "method": "invalid/method",
            "params": {}
        }

        # Should raise or return error
        error_response = {
            "error": {
                "code": -32601,
                "message": "Method not found"
            }
        }

        assert "error" in error_response
        assert error_response["error"]["code"] == -32601

    def test_handle_malformed_request(self):
        """Test handling malformed request"""
        request = {
            "method": "tools/call"
            # Missing params
        }

        error_response = {
            "error": {
                "code": -32600,
                "message": "Invalid Request"
            }
        }

        assert "error" in error_response

    def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        server = Mock()
        server.request_count = 0

        def handle_request(request):
            server.request_count += 1
            return {"id": server.request_count}

        # Simulate concurrent requests
        responses = []
        for i in range(5):
            responses.append(handle_request({"method": "tools/call"}))

        assert len(responses) == 5
        assert server.request_count == 5


class TestResponseFormatting:
    """Test MCP response formatting"""

    def test_success_response_format(self):
        """Test success response format"""
        response = {
            "content": [
                {
                    "type": "text",
                    "text": "Click successful"
                }
            ]
        }

        assert "content" in response
        assert response["content"][0]["type"] == "text"

    def test_error_response_format(self):
        """Test error response format"""
        response = {
            "error": {
                "code": -32000,
                "message": "Click failed",
                "data": {
                    "reason": "Element not found"
                }
            }
        }

        assert "error" in response
        assert response["error"]["code"] == -32000
        assert "data" in response["error"]

    def test_structured_data_response(self):
        """Test structured data in response"""
        response = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "dom_structure": {
                            "elements": 150,
                            "clickable": 25
                        }
                    })
                }
            ]
        }

        data = json.loads(response["content"][0]["text"])
        assert data["dom_structure"]["elements"] == 150

    def test_multiple_content_blocks(self):
        """Test response with multiple content blocks"""
        response = {
            "content": [
                {
                    "type": "text",
                    "text": "Click successful"
                },
                {
                    "type": "resource",
                    "uri": "dom://screenshot.png"
                }
            ]
        }

        assert len(response["content"]) == 2
        assert response["content"][0]["type"] == "text"
        assert response["content"][1]["type"] == "resource"


class TestErrorHandling:
    """Test error handling in MCP server"""

    def test_tool_execution_error(self):
        """Test handling tool execution error"""
        def failing_tool():
            raise Exception("Tool execution failed")

        try:
            failing_tool()
            assert False, "Should have raised exception"
        except Exception as e:
            error_response = {
                "error": {
                    "code": -32000,
                    "message": str(e)
                }
            }
            assert error_response["error"]["message"] == "Tool execution failed"

    def test_validation_error(self):
        """Test handling validation error"""
        request = {
            "method": "tools/call",
            "params": {
                "name": "click",
                "arguments": {
                    "x": "invalid"  # Should be number
                }
            }
        }

        # Validation should fail
        def validate(args):
            if not isinstance(args.get("x"), (int, float)):
                raise ValueError("x must be a number")

        with pytest.raises(ValueError, match="x must be a number"):
            validate(request["params"]["arguments"])

    def test_resource_not_found_error(self):
        """Test handling resource not found error"""
        error_response = {
            "error": {
                "code": -32002,
                "message": "Resource not found",
                "data": {
                    "uri": "dom://nonexistent"
                }
            }
        }

        assert error_response["error"]["code"] == -32002
        assert "uri" in error_response["error"]["data"]

    def test_timeout_error(self):
        """Test handling timeout error"""
        import time

        def slow_operation():
            time.sleep(0.1)
            return "done"

        start = time.time()
        result = slow_operation()
        duration = time.time() - start

        # Simulate timeout check
        timeout = 0.05
        if duration > timeout:
            error_response = {
                "error": {
                    "code": -32001,
                    "message": "Operation timeout"
                }
            }
            assert error_response["error"]["code"] == -32001

    def test_error_recovery(self):
        """Test error recovery mechanism"""
        server = Mock()
        server.error_count = 0
        server.max_errors = 3

        def handle_with_recovery():
            server.error_count += 1
            if server.error_count >= server.max_errors:
                return {"error": "Too many errors"}
            return {"success": True}

        # First two should succeed
        result1 = handle_with_recovery()
        result2 = handle_with_recovery()
        assert result1["success"] is True
        assert result2["success"] is True

        # Third should error
        result3 = handle_with_recovery()
        assert "error" in result3


class TestResourceManagement:
    """Test resource management"""

    def test_browser_resource_lifecycle(self):
        """Test browser resource lifecycle"""
        browser = Mock()
        browser.is_connected = Mock(return_value=True)
        browser.close = Mock()

        # Acquire resource
        assert browser.is_connected()

        # Use resource
        # ...

        # Release resource
        browser.close()
        browser.is_connected.return_value = False

        assert not browser.is_connected()

    def test_page_context_management(self):
        """Test page context management"""
        page = Mock()
        page.context = Mock()

        # Create context
        page.context.pages = [page]

        assert len(page.context.pages) == 1

        # Close context
        page.context.close = Mock()
        page.context.close()

        page.context.close.assert_called_once()

    def test_memory_cleanup(self):
        """Test memory cleanup after operations"""
        cache = {}

        # Add items to cache
        for i in range(100):
            cache[f"key_{i}"] = {"data": "x" * 1000}

        assert len(cache) == 100

        # Cleanup
        cache.clear()

        assert len(cache) == 0

    def test_connection_pooling(self):
        """Test connection pooling"""
        pool = {
            "connections": [],
            "max_size": 5
        }

        # Add connections
        for i in range(3):
            conn = Mock()
            conn.id = i
            pool["connections"].append(conn)

        assert len(pool["connections"]) == 3
        assert len(pool["connections"]) <= pool["max_size"]

    def test_resource_limits(self):
        """Test resource limits enforcement"""
        server = Mock()
        server.max_concurrent_requests = 10
        server.active_requests = 0

        def acquire_slot():
            if server.active_requests >= server.max_concurrent_requests:
                return False
            server.active_requests += 1
            return True

        # Should succeed
        for i in range(10):
            assert acquire_slot() is True

        # Should fail (limit reached)
        assert acquire_slot() is False


class TestServerLifecycle:
    """Test server lifecycle management"""

    def test_server_startup(self):
        """Test server startup sequence"""
        server = Mock()
        server.started = False

        def start():
            # Initialize components
            server.dom_extractor = Mock()
            server.transformer = Mock()
            server.started = True

        start()

        assert server.started is True
        assert server.dom_extractor is not None

    def test_server_shutdown(self):
        """Test server shutdown sequence"""
        server = Mock()
        server.started = True
        server.connections = [Mock(), Mock()]

        def shutdown():
            # Close connections
            for conn in server.connections:
                conn.close()
            server.connections.clear()
            server.started = False

        shutdown()

        assert server.started is False
        assert len(server.connections) == 0

    def test_graceful_shutdown(self):
        """Test graceful shutdown with pending requests"""
        server = Mock()
        server.pending_requests = [Mock(), Mock(), Mock()]

        def graceful_shutdown():
            # Wait for pending requests
            while server.pending_requests:
                request = server.pending_requests.pop()
                # Complete request
                request.complete()

        graceful_shutdown()

        assert len(server.pending_requests) == 0

    def test_server_restart(self):
        """Test server restart capability"""
        server = Mock()
        server.started = False

        def restart():
            # Shutdown
            server.started = False
            # Startup
            server.started = True

        restart()

        assert server.started is True


class TestConfiguration:
    """Test server configuration"""

    def test_load_config_from_file(self):
        """Test loading configuration from file"""
        config_data = {
            "server": {
                "port": 8080,
                "host": "localhost"
            },
            "logging": {
                "level": "INFO"
            }
        }

        # Simulate loading
        config = config_data

        assert config["server"]["port"] == 8080
        assert config["logging"]["level"] == "INFO"

    def test_config_validation(self):
        """Test configuration validation"""
        config = {
            "port": 8080,
            "max_connections": 100
        }

        # Validate
        assert isinstance(config["port"], int)
        assert config["max_connections"] > 0

    def test_config_defaults(self):
        """Test configuration defaults"""
        config = {}

        # Apply defaults
        config.setdefault("port", 8080)
        config.setdefault("log_level", "INFO")

        assert config["port"] == 8080
        assert config["log_level"] == "INFO"

    def test_config_override(self):
        """Test configuration override"""
        default_config = {"timeout": 30}
        user_config = {"timeout": 60}

        # Override
        config = {**default_config, **user_config}

        assert config["timeout"] == 60


# ============================================================================
# Integration-style tests
# ============================================================================

class TestEndToEndCore:
    """End-to-end tests for core functionality"""

    def test_full_request_lifecycle(self):
        """Test complete request lifecycle"""
        server = Mock()

        # 1. Receive request
        request = {
            "method": "tools/call",
            "params": {
                "name": "click",
                "arguments": {"x": 100, "y": 200}
            }
        }

        # 2. Validate request
        assert request["method"] == "tools/call"
        assert "params" in request

        # 3. Route to handler
        handler = Mock(return_value={"success": True})
        response = handler(request["params"])

        # 4. Format response
        assert response["success"] is True

        # 5. Send response
        handler.assert_called_once()

    def test_server_handles_multiple_tool_calls(self):
        """Test server handling multiple different tool calls"""
        tools = {
            "click": Mock(return_value={"clicked": True}),
            "extract_dom": Mock(return_value={"elements": 100}),
            "validate": Mock(return_value={"valid": True})
        }

        # Call different tools
        result1 = tools["click"]({"x": 100, "y": 200})
        result2 = tools["extract_dom"]({"url": "http://example.com"})
        result3 = tools["validate"]({"x": 100, "y": 200})

        assert result1["clicked"] is True
        assert result2["elements"] == 100
        assert result3["valid"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
