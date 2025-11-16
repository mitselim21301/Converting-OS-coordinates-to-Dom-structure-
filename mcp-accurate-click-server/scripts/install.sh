#!/usr/bin/env bash
# Installation script for mcp-accurate-click-server
# Handles different installation scenarios

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo -e "${BLUE}MCP Accurate Click Server - Installation${NC}"
echo ""

# Check Python version
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 is required but not found"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

# Check minimum Python version (3.9)
if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 9) else 1)'; then
    echo -e "${GREEN}Python version OK${NC}"
else
    echo "Error: Python 3.9 or higher is required"
    exit 1
fi

# Upgrade pip
echo ""
echo "Upgrading pip..."
python3 -m pip install --upgrade pip setuptools wheel

# Determine installation type
INSTALL_TYPE="${1:-basic}"

case "$INSTALL_TYPE" in
    basic)
        echo ""
        echo "Installing basic package..."
        python3 -m pip install -e .
        ;;
    dev)
        echo ""
        echo "Installing with development dependencies..."
        python3 -m pip install -e ".[dev]"
        python3 -m pip install -r requirements-dev.txt
        ;;
    full)
        echo ""
        echo "Installing with all dependencies..."
        python3 -m pip install -e ".[all]"
        python3 -m pip install -r requirements-dev.txt
        python3 -m pip install -r requirements-vision.txt
        ;;
    vision)
        echo ""
        echo "Installing with vision dependencies..."
        python3 -m pip install -e ".[vision]"
        python3 -m pip install -r requirements-vision.txt
        ;;
    *)
        echo "Unknown installation type: $INSTALL_TYPE"
        echo ""
        echo "Usage: $0 [basic|dev|full|vision]"
        echo ""
        echo "  basic   - Install core dependencies only (default)"
        echo "  dev     - Install with development tools"
        echo "  full    - Install everything"
        echo "  vision  - Install with vision/OCR support"
        exit 1
        ;;
esac

# Install Playwright browsers
if [[ "$INSTALL_TYPE" != "basic" ]]; then
    echo ""
    echo "Installing Playwright browsers..."
    python3 -m playwright install chromium
fi

# Setup pre-commit hooks for dev installation
if [[ "$INSTALL_TYPE" == "dev" ]] || [[ "$INSTALL_TYPE" == "full" ]]; then
    if command -v pre-commit >/dev/null 2>&1; then
        echo ""
        echo "Setting up pre-commit hooks..."
        pre-commit install
    fi
fi

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "Next steps:"
echo "  - Run tests: pytest tests/"
echo "  - Start server: python -m mcp_server.cli"
echo "  - See Makefile for more commands"
