#!/usr/bin/env bash
# Build script for mcp-accurate-click-server
# This script handles building, testing, and packaging the project

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Ensure Python is available
check_python() {
    if ! command_exists python3; then
        log_error "Python 3 is not installed"
        exit 1
    fi

    local python_version
    python_version=$(python3 --version | cut -d' ' -f2)
    log_info "Using Python $python_version"
}

# Clean build artifacts
clean() {
    log_info "Cleaning build artifacts..."

    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete

    log_success "Clean complete"
}

# Install dependencies
install_deps() {
    log_info "Installing dependencies..."

    python3 -m pip install --upgrade pip setuptools wheel build

    if [ "${1:-}" == "dev" ]; then
        log_info "Installing development dependencies..."
        python3 -m pip install -r requirements-dev.txt
    elif [ "${1:-}" == "all" ]; then
        log_info "Installing all dependencies..."
        python3 -m pip install -r requirements-dev.txt
        python3 -m pip install -r requirements-vision.txt
    else
        log_info "Installing core dependencies..."
        python3 -m pip install -r requirements.txt
    fi

    log_success "Dependencies installed"
}

# Run tests
run_tests() {
    log_info "Running tests..."

    if ! command_exists pytest; then
        log_warning "pytest not found, installing..."
        python3 -m pip install pytest pytest-cov pytest-asyncio
    fi

    python3 -m pytest tests/ -v

    log_success "Tests passed"
}

# Run tests with coverage
run_tests_coverage() {
    log_info "Running tests with coverage..."

    python3 -m pytest tests/ --cov=src/mcp_server --cov-report=html --cov-report=term

    log_success "Coverage report generated in htmlcov/"
}

# Run code formatting
format_code() {
    log_info "Formatting code..."

    if command_exists black; then
        python3 -m black src/ tests/
    else
        log_warning "black not installed, skipping formatting"
    fi

    if command_exists isort; then
        python3 -m isort src/ tests/
    else
        log_warning "isort not installed, skipping import sorting"
    fi

    log_success "Code formatted"
}

# Run linting
run_lint() {
    log_info "Running linters..."

    local has_errors=0

    if command_exists ruff; then
        python3 -m ruff check src/ tests/ || has_errors=1
    else
        log_warning "ruff not installed, skipping"
    fi

    if command_exists pylint; then
        python3 -m pylint src/ || has_errors=1
    else
        log_warning "pylint not installed, skipping"
    fi

    if [ $has_errors -eq 0 ]; then
        log_success "Linting passed"
    else
        log_error "Linting found issues"
        return 1
    fi
}

# Run type checking
run_type_check() {
    log_info "Running type checking..."

    if command_exists mypy; then
        python3 -m mypy src/
        log_success "Type checking passed"
    else
        log_warning "mypy not installed, skipping type checking"
    fi
}

# Build package
build_package() {
    log_info "Building package..."

    clean

    python3 -m build

    log_success "Package built successfully"
    log_info "Distribution packages in dist/"
    ls -lh dist/
}

# Full CI/CD pipeline
run_ci() {
    log_info "Running full CI/CD pipeline..."

    format_code
    run_lint
    run_type_check
    run_tests_coverage
    build_package

    log_success "CI/CD pipeline complete!"
}

# Install Playwright browsers
install_playwright() {
    log_info "Installing Playwright browsers..."

    python3 -m playwright install chromium

    log_success "Playwright browsers installed"
}

# Development setup
dev_setup() {
    log_info "Setting up development environment..."

    check_python
    install_deps dev
    install_playwright

    if command_exists pre-commit; then
        pre-commit install
        log_success "Pre-commit hooks installed"
    fi

    log_success "Development environment ready!"
}

# Show usage
usage() {
    cat << EOF
Build script for mcp-accurate-click-server

Usage: $0 [command]

Commands:
    clean           Clean build artifacts
    install         Install core dependencies
    install-dev     Install development dependencies
    install-all     Install all dependencies
    test            Run tests
    test-cov        Run tests with coverage
    format          Format code
    lint            Run linters
    type-check      Run type checking
    build           Build distribution packages
    ci              Run full CI/CD pipeline
    playwright      Install Playwright browsers
    dev-setup       Complete development setup
    help            Show this help message

Examples:
    $0 dev-setup    # Set up development environment
    $0 ci           # Run full CI/CD pipeline
    $0 build        # Build distribution packages
EOF
}

# Main script logic
main() {
    check_python

    case "${1:-help}" in
        clean)
            clean
            ;;
        install)
            install_deps
            ;;
        install-dev)
            install_deps dev
            ;;
        install-all)
            install_deps all
            ;;
        test)
            run_tests
            ;;
        test-cov)
            run_tests_coverage
            ;;
        format)
            format_code
            ;;
        lint)
            run_lint
            ;;
        type-check)
            run_type_check
            ;;
        build)
            build_package
            ;;
        ci)
            run_ci
            ;;
        playwright)
            install_playwright
            ;;
        dev-setup)
            dev_setup
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            log_error "Unknown command: $1"
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
