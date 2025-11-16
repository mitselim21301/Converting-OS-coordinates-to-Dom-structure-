#!/usr/bin/env bash
# Test runner script with various testing options

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

MODE="${1:-all}"

case "$MODE" in
    all)
        echo -e "${BLUE}Running all tests...${NC}"
        python3 -m pytest tests/ -v
        ;;
    fast)
        echo -e "${BLUE}Running fast tests (fail fast)...${NC}"
        python3 -m pytest tests/ -x -v
        ;;
    cov)
        echo -e "${BLUE}Running tests with coverage...${NC}"
        python3 -m pytest tests/ --cov=src/mcp_server --cov-report=html --cov-report=term -v
        echo ""
        echo -e "${GREEN}Coverage report: htmlcov/index.html${NC}"
        ;;
    unit)
        echo -e "${BLUE}Running unit tests only...${NC}"
        python3 -m pytest tests/unit/ -v
        ;;
    integration)
        echo -e "${BLUE}Running integration tests...${NC}"
        python3 -m pytest tests/integration/ -v
        ;;
    watch)
        echo -e "${BLUE}Running tests in watch mode...${NC}"
        if command -v ptw >/dev/null 2>&1; then
            ptw tests/
        else
            echo -e "${YELLOW}pytest-watch not installed. Installing...${NC}"
            python3 -m pip install pytest-watch
            ptw tests/
        fi
        ;;
    parallel)
        echo -e "${BLUE}Running tests in parallel...${NC}"
        python3 -m pytest tests/ -n auto -v
        ;;
    markers)
        echo -e "${BLUE}Available test markers:${NC}"
        python3 -m pytest --markers
        ;;
    slow)
        echo -e "${BLUE}Running slow tests only...${NC}"
        python3 -m pytest tests/ -v -m slow
        ;;
    not-slow)
        echo -e "${BLUE}Running tests excluding slow tests...${NC}"
        python3 -m pytest tests/ -v -m "not slow"
        ;;
    failed)
        echo -e "${BLUE}Re-running failed tests...${NC}"
        python3 -m pytest tests/ --lf -v
        ;;
    verbose)
        echo -e "${BLUE}Running tests with verbose output...${NC}"
        python3 -m pytest tests/ -vv --tb=long
        ;;
    help)
        cat << EOF
Test runner script

Usage: $0 [mode]

Modes:
    all         Run all tests (default)
    fast        Run tests with fail-fast mode
    cov         Run tests with coverage report
    unit        Run unit tests only
    integration Run integration tests only
    watch       Run tests in watch mode
    parallel    Run tests in parallel
    markers     Show available test markers
    slow        Run slow tests only
    not-slow    Run tests excluding slow tests
    failed      Re-run only failed tests
    verbose     Run tests with verbose output
    help        Show this help message

Examples:
    $0          # Run all tests
    $0 cov      # Run with coverage
    $0 watch    # Watch mode for development
EOF
        ;;
    *)
        echo "Unknown mode: $MODE"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac
