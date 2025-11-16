.PHONY: help install install-dev install-all clean test test-cov lint format type-check build publish dev-setup playwright-install

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
BLACK := $(PYTHON) -m black
ISORT := $(PYTHON) -m isort
MYPY := $(PYTHON) -m mypy
PYLINT := $(PYTHON) -m pylint
RUFF := $(PYTHON) -m ruff

# Directories
SRC_DIR := src
TEST_DIR := tests
DIST_DIR := dist
BUILD_DIR := build

help:
	@echo "MCP Accurate Click Server - Build Commands"
	@echo "=========================================="
	@echo ""
	@echo "Installation:"
	@echo "  make install          Install package with core dependencies"
	@echo "  make install-dev      Install package with development dependencies"
	@echo "  make install-all      Install package with all dependencies"
	@echo "  make playwright-install  Install Playwright browsers"
	@echo ""
	@echo "Development:"
	@echo "  make dev-setup        Complete development environment setup"
	@echo "  make format           Format code with black and isort"
	@echo "  make lint             Run all linters (ruff, pylint)"
	@echo "  make type-check       Run type checking with mypy"
	@echo "  make test             Run tests"
	@echo "  make test-cov         Run tests with coverage report"
	@echo "  make check            Run all checks (format, lint, type-check, test)"
	@echo ""
	@echo "Building:"
	@echo "  make build            Build distribution packages"
	@echo "  make clean            Remove build artifacts"
	@echo "  make clean-all        Remove all generated files"
	@echo ""
	@echo "Publishing:"
	@echo "  make publish-test     Publish to Test PyPI"
	@echo "  make publish          Publish to PyPI (production)"

# Installation targets
install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev]"
	$(PIP) install -r requirements-dev.txt

install-all:
	$(PIP) install -e ".[all]"
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -r requirements-vision.txt

playwright-install:
	$(PYTHON) -m playwright install chromium
	@echo "Playwright Chromium browser installed"

# Development setup
dev-setup: install-dev playwright-install
	pre-commit install
	@echo "Development environment setup complete!"

# Code formatting
format:
	@echo "Running isort..."
	$(ISORT) $(SRC_DIR) $(TEST_DIR)
	@echo "Running black..."
	$(BLACK) $(SRC_DIR) $(TEST_DIR)
	@echo "Code formatting complete!"

format-check:
	@echo "Checking isort..."
	$(ISORT) --check-only $(SRC_DIR) $(TEST_DIR)
	@echo "Checking black..."
	$(BLACK) --check $(SRC_DIR) $(TEST_DIR)

# Linting
lint:
	@echo "Running ruff..."
	$(RUFF) check $(SRC_DIR) $(TEST_DIR)
	@echo "Running pylint..."
	$(PYLINT) $(SRC_DIR)
	@echo "Linting complete!"

lint-fix:
	@echo "Running ruff with auto-fix..."
	$(RUFF) check --fix $(SRC_DIR) $(TEST_DIR)

# Type checking
type-check:
	@echo "Running mypy..."
	$(MYPY) $(SRC_DIR)
	@echo "Type checking complete!"

# Testing
test:
	$(PYTEST) $(TEST_DIR)

test-cov:
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=html --cov-report=term $(TEST_DIR)
	@echo "Coverage report generated in htmlcov/index.html"

test-fast:
	$(PYTEST) -x $(TEST_DIR)

test-verbose:
	$(PYTEST) -vv $(TEST_DIR)

test-parallel:
	$(PYTEST) -n auto $(TEST_DIR)

# Comprehensive checks
check: format-check lint type-check test
	@echo "All checks passed!"

# Building
build: clean
	$(PYTHON) -m build
	@echo "Build complete! Packages in $(DIST_DIR)/"

build-wheel:
	$(PYTHON) -m build --wheel

build-sdist:
	$(PYTHON) -m build --sdist

# Cleaning
clean:
	rm -rf $(BUILD_DIR)
	rm -rf $(DIST_DIR)
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.orig" -delete

clean-all: clean
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf test-results
	rm -rf playwright-report

# Publishing
publish-test: build
	$(PYTHON) -m twine upload --repository testpypi $(DIST_DIR)/*

publish: build
	$(PYTHON) -m twine upload $(DIST_DIR)/*
	@echo "Published to PyPI!"

# Version management
version-patch:
	@echo "Bumping patch version..."
	@# Add version bump logic here

version-minor:
	@echo "Bumping minor version..."
	@# Add version bump logic here

version-major:
	@echo "Bumping major version..."
	@# Add version bump logic here

# Docker support (if needed)
docker-build:
	docker build -t mcp-accurate-click-server:latest .

docker-run:
	docker run -it --rm mcp-accurate-click-server:latest

# Pre-commit
pre-commit:
	pre-commit run --all-files

# Documentation
docs:
	cd docs && make html
	@echo "Documentation built in docs/_build/html/index.html"

docs-serve:
	cd docs/_build/html && $(PYTHON) -m http.server

# Benchmarking
benchmark:
	$(PYTEST) tests/benchmarks/ -v --benchmark-only

# Security checks
security-check:
	$(PIP) install safety bandit
	safety check
	bandit -r $(SRC_DIR)
