#!/usr/bin/env python3
"""
MCP Accurate Click Server - Main Entry Point

Run as:
    python -m mcp_server [OPTIONS]

Examples:
    # Run as MCP stdio server
    python -m mcp_server --stdio

    # Run demo
    python -m mcp_server --demo

    # Run with custom config
    python -m mcp_server --config config.yaml --stdio

    # Show version and features
    python -m mcp_server --version
    python -m mcp_server --features
"""

import sys
import argparse
import asyncio
import logging
from pathlib import Path

from mcp_server import (
    MCPAccurateClickServer,
    ServerConfig,
    ConfigManager,
    __version__,
    get_features,
    print_info
)


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def run_stdio_server(config: ServerConfig):
    """Run server in stdio mode for MCP clients."""
    server = MCPAccurateClickServer(config)

    print("Starting MCP Accurate Click Server in stdio mode...", file=sys.stderr)
    print(f"Version: {__version__}", file=sys.stderr)
    print("Ready for MCP requests on stdin/stdout", file=sys.stderr)

    async with server.running():
        # Run stdio server loop
        await server.run_stdio()


async def run_demo(config: ServerConfig):
    """Run interactive demo."""
    server = MCPAccurateClickServer(config)

    print("=" * 80)
    print("MCP Accurate Click Server - Interactive Demo")
    print("=" * 80)
    print()

    async with server.running():
        # Navigate to example page
        examples_dir = Path(__file__).parent.parent.parent / "examples"
        test_page = examples_dir / "test_page.html"

        if test_page.exists():
            await server.navigate(f"file://{test_page.absolute()}")
            print(f"✓ Loaded test page: {test_page}")
        else:
            await server.navigate("https://example.com")
            print("✓ Loaded example.com")

        print()
        print("Available tools:")
        for tool_name in server.get_available_tools():
            print(f"  - {tool_name}")

        print()
        print("Demo: Clicking a button by text...")

        # Demo click
        result = await server.call_tool("click_element", {
            "method": "by_text",
            "text": "More information",
            "validate": True
        })

        print(f"✓ Click result: {result.get('success', False)}")
        if result.get('element'):
            print(f"  Element: {result['element']}")

        print()
        print("Demo: Extracting DOM structure...")

        # Demo DOM extraction
        dom_result = await server.call_tool("get_dom_structure", {
            "include_text": True,
            "include_interactive": True
        })

        stats = dom_result.get('statistics', {})
        print(f"✓ DOM extracted:")
        print(f"  Total elements: {stats.get('total_elements', 0)}")
        print(f"  Interactive: {stats.get('interactive_elements', 0)}")
        print(f"  Text elements: {stats.get('text_elements', 0)}")

        print()
        print("=" * 80)
        print("Demo complete! Press Ctrl+C to exit.")
        print("=" * 80)

        # Keep server running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\nShutting down...")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MCP Accurate Click Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --stdio                Run as MCP stdio server
  %(prog)s --demo                 Run interactive demo
  %(prog)s --config cfg.yaml      Use custom configuration
  %(prog)s --version              Show version information
  %(prog)s --features             Show available features
        """
    )

    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Run as MCP stdio server (for Claude, etc.)"
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run interactive demo"
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (YAML or JSON)"
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit"
    )

    parser.add_argument(
        "--features",
        action="store_true",
        help="Show available features and exit"
    )

    args = parser.parse_args()

    # Show version
    if args.version:
        print(f"MCP Accurate Click Server v{__version__}")
        return 0

    # Show features
    if args.features:
        print_info()
        return 0

    # Setup logging
    setup_logging(args.log_level)

    # Load configuration
    if args.config:
        config_manager = ConfigManager()
        config = config_manager.load_from_file(args.config)
    else:
        config = ServerConfig()

    # Override with CLI args
    if args.headless:
        config.headless = True
    config.log_level = args.log_level

    # Run appropriate mode
    try:
        if args.stdio:
            asyncio.run(run_stdio_server(config))
        elif args.demo:
            asyncio.run(run_demo(config))
        else:
            # Default: show help
            parser.print_help()
            print("\nTip: Use --stdio to run as MCP server, or --demo for interactive demo")
            return 1
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.log_level == "DEBUG":
            import traceback
            traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
