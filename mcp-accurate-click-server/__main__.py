"""
Main entry point for MCP Accurate Click Server

Run as:
    python -m mcp_server [options]
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

from src.mcp_server.core import (
    MCPAccurateClickServer,
    StdioMCPServer,
    ServerConfig,
    create_server
)


def setup_logging(level: str = "INFO", log_file: str = None):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),
            *([logging.FileHandler(log_file)] if log_file else [])
        ]
    )


async def run_stdio_server(config: ServerConfig):
    """Run MCP server with stdio transport"""
    server = create_server(config)
    stdio_server = StdioMCPServer(server)

    try:
        await stdio_server.run()
    except KeyboardInterrupt:
        logging.info("Server interrupted by user")
    except Exception as e:
        logging.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


async def run_interactive_demo(config: ServerConfig):
    """Run interactive demo server"""
    server = create_server(config)

    async with server.running():
        print("\n" + "=" * 70)
        print("MCP Accurate Click Server - Interactive Demo")
        print("=" * 70)
        print(f"\nServer running with {config.browser_type} browser")
        print(f"Headless mode: {config.headless}")
        print("\nAvailable tools:")

        tools = await server.list_tools()
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description'][:60]}...")

        print("\n" + "=" * 70)
        print("\nNavigating to example.com...")

        result = await server.navigate("https://example.com")
        print(f"Navigation: {result}")

        print("\nGetting DOM structure...")
        dom_result = await server.call_tool("get_dom_structure", {
            "include_interactive_only": True
        })

        if dom_result["success"]:
            stats = dom_result["data"]["statistics"]
            print(f"DOM Statistics:")
            print(f"  Total elements: {stats['total']}")
            print(f"  Interactive: {stats['interactive']}")

        print("\nTaking screenshot...")
        screenshot = await server.screenshot()
        print(f"Screenshot: {screenshot}")

        print("\n" + "=" * 70)
        print("Demo completed successfully!")
        print("=" * 70)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="MCP Accurate Click Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run as MCP stdio server
  python -m mcp_server --stdio

  # Run interactive demo
  python -m mcp_server --demo

  # Run with custom configuration
  python -m mcp_server --config config.json --stdio

  # Run with debug logging
  python -m mcp_server --log-level DEBUG --demo
        """
    )

    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Run as MCP stdio server (for MCP clients)"
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run interactive demo"
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (JSON)"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )

    parser.add_argument(
        "--log-file",
        type=str,
        help="Log file path"
    )

    parser.add_argument(
        "--browser",
        type=str,
        choices=["chromium", "firefox", "webkit"],
        help="Browser type"
    )

    parser.add_argument(
        "--headless",
        type=lambda x: x.lower() in ("true", "1", "yes"),
        help="Run browser in headless mode (true/false)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level, args.log_file)

    # Load configuration
    if args.config:
        config = ServerConfig.from_file(args.config)
    else:
        config = ServerConfig.from_env()

    # Override with command-line arguments
    if args.browser:
        config.browser_type = args.browser
    if args.headless is not None:
        config.headless = args.headless
    if args.log_level:
        config.log_level = args.log_level
    if args.log_file:
        config.log_file = args.log_file

    # Run appropriate mode
    if args.stdio:
        asyncio.run(run_stdio_server(config))
    elif args.demo:
        asyncio.run(run_interactive_demo(config))
    else:
        # Default to stdio server
        print("No mode specified. Use --stdio or --demo", file=sys.stderr)
        print("Run with --help for usage information", file=sys.stderr)
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
