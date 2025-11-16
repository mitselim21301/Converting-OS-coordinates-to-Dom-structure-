# Build & Development Quick Reference

## Installation

```bash
# Basic installation
pip install -e .

# Development installation
make dev-setup
# or
./scripts/install.sh dev

# With all dependencies
./scripts/install.sh full
```

## Common Commands

### Using Make

```bash
make help              # Show all available commands
make install           # Install package
make install-dev       # Install with dev dependencies
make test              # Run tests
make test-cov          # Run tests with coverage
make format            # Format code
make lint              # Run linters
make type-check        # Run type checking
make check             # Run all checks
make build             # Build distribution
make clean             # Clean build artifacts
```

### Using Scripts

```bash
# Build script
./scripts/build.sh dev-setup    # Setup dev environment
./scripts/build.sh test         # Run tests
./scripts/build.sh build        # Build package
./scripts/build.sh ci           # Full CI pipeline

# Test script
./scripts/test.sh all           # All tests
./scripts/test.sh cov           # With coverage
./scripts/test.sh watch         # Watch mode
./scripts/test.sh fast          # Fail-fast mode

# Install script
./scripts/install.sh basic      # Basic install
./scripts/install.sh dev        # Dev install
./scripts/install.sh full       # Full install

# Dev script
./scripts/dev.sh run            # Run server
./scripts/dev.sh shell          # Python shell
./scripts/dev.sh repl           # IPython REPL
```

## Development Workflow

### Initial Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd mcp-accurate-click-server

# 2. Setup development environment
make dev-setup

# 3. Verify installation
make test
```

### Making Changes

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes
# ... edit files ...

# 3. Format code
make format

# 4. Run checks
make check

# 5. Commit changes
git add .
git commit -m "feat: add my feature"
```

### Before Committing

```bash
# Run all checks
make check

# Or individually:
make format        # Format code
make lint          # Check code quality
make type-check    # Type checking
make test-cov      # Run tests with coverage
```

## Testing

```bash
# All tests
pytest
# or
make test

# With coverage
pytest --cov
# or
make test-cov

# Watch mode
./scripts/test.sh watch

# Specific test
pytest tests/test_specific.py::test_function

# Parallel execution
pytest -n auto

# Only failed tests
pytest --lf
```

## Building

```bash
# Build distribution
make build

# Clean first, then build
make clean build

# Build wheel only
make build-wheel

# Build source dist only
make build-sdist
```

## Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/
# or
make format

# Lint
ruff check src/ tests/
pylint src/
# or
make lint

# Type check
mypy src/
# or
make type-check

# Pre-commit hooks
pre-commit run --all-files
```

## Package Management

```bash
# Install in editable mode
pip install -e .

# Install with extras
pip install -e ".[dev]"
pip install -e ".[vision]"
pip install -e ".[all]"

# Uninstall
pip uninstall mcp-accurate-click-server
```

## Playwright

```bash
# Install browsers
python -m playwright install chromium
# or
make playwright-install

# Codegen (record actions)
python -m playwright codegen
```

## Documentation

```bash
# Build docs
make docs

# Serve docs locally
make docs-serve

# View in browser
open docs/_build/html/index.html
```

## Publishing

```bash
# Publish to Test PyPI
make publish-test

# Publish to PyPI
make publish
```

## Troubleshooting

### Clean everything

```bash
make clean-all
```

### Reinstall dependencies

```bash
pip install --upgrade pip
pip install -r requirements-dev.txt
```

### Reset environment

```bash
# Remove virtual environment
deactivate
rm -rf venv/

# Create new one
python -m venv venv
source venv/bin/activate
make dev-setup
```

## Environment Variables

Create a `.env` file for local configuration:

```bash
# .env
DEBUG=true
LOG_LEVEL=DEBUG
MCP_SERVER_PORT=8080
```

## Git Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

## Performance

```bash
# Profile code
python -m cProfile -o profile.stats script.py

# Benchmark tests
pytest tests/benchmarks/ --benchmark-only
```

## Security

```bash
# Security check
make security-check

# Or manually:
pip install safety bandit
safety check
bandit -r src/
```
