#!/usr/bin/env bash
# Quick development helper script
# Shortcuts for common development tasks

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

case "${1:-help}" in
    run)
        # Run the MCP server
        python3 -m mcp_server.cli "$@"
        ;;
    shell)
        # Start Python shell with package imported
        python3 -i -c "from mcp_server import *; print('MCP Server package imported')"
        ;;
    watch-test)
        # Watch tests and re-run on change
        if command -v pytest-watch >/dev/null 2>&1; then
            ptw tests/
        else
            echo "Installing pytest-watch..."
            pip install pytest-watch
            ptw tests/
        fi
        ;;
    debug)
        # Run with debugger
        python3 -m pdb -m mcp_server.cli "$@"
        ;;
    profile)
        # Profile the application
        python3 -m cProfile -o profile.stats -m mcp_server.cli "$@"
        echo "Profile saved to profile.stats"
        ;;
    repl)
        # Start IPython REPL if available
        if command -v ipython >/dev/null 2>&1; then
            ipython -i -c "from mcp_server import *"
        else
            python3 -i -c "from mcp_server import *"
        fi
        ;;
    *)
        cat << EOF
Development helper script

Usage: $0 [command]

Commands:
    run          Run the MCP server
    shell        Start Python shell with package imported
    repl         Start IPython REPL with package imported
    watch-test   Watch tests and re-run on change
    debug        Run with debugger
    profile      Profile the application
    help         Show this help message
EOF
        ;;
esac
