# CI/CD Pipeline Setup

## Overview

This document describes the GitHub Actions CI/CD pipeline configured for the MCP Accurate Click Server project.

## Workflow Configuration

### File Location
- **Primary Workflow**: `.github/workflows/cross-platform-tests.yml`

### Workflow Trigger Events
The workflow is automatically triggered on:
- **Push events** to `main`, `develop`, and `feature/**` branches
- **Pull requests** against `main` and `develop` branches
- **Manual dispatch** via GitHub Actions UI (`workflow_dispatch`)

### Concurrency Control
- Only one workflow run per branch/ref combination
- In-progress runs are automatically cancelled when new pushes are made
- Prevents duplicate and race condition issues

## Pipeline Jobs

### 1. Lint and Type Check Job
**Runs on**: `ubuntu-latest`
**Python Version**: `3.11`
**Purpose**: Code quality and type safety validation

#### Steps:
1. **Ruff Linting**: Fast Python linter checking for code issues
2. **Black Format Check**: Ensures code follows Black formatting standards
3. **isort Import Check**: Validates import organization
4. **mypy Type Check**: Static type checking for Python code
5. **pylint Analysis**: Additional code quality checks (soft fail)

**Artifacts**: None (status only)

### 2. Linux Testing Job (Matrix)
**Runs on**: `ubuntu-latest`
**Python Versions**: 3.9, 3.10, 3.11, 3.12
**Purpose**: Cross-version testing on Linux platform

#### System Dependencies Installed:
- `xdotool`: X11 command-line tool for simulating mouse/keyboard input
- `wmctrl`: Window manager control tool for manipulating windows
- `x11-utils`: X11 utilities (includes xrandr, xwininfo, etc.)
- `xclip`: X11 clipboard manipulation
- `xsel`: X11 selection manipulation
- `libxrandr2`: X11 Resize and Rotate library

#### Python Dependencies:
- Base requirements from `requirements.txt`
- Development tools from `dev` extra
- Linux-specific packages from `linux` extra
- Playwright browser binaries (Chromium)

#### Test Steps:
1. Checkout code
2. Set up Python (with pip caching)
3. Install system dependencies
4. Install Python dependencies
5. Run pytest with coverage reporting:
   - XML format for CI integration
   - HTML format for artifact storage
   - Terminal format with missing line information
   - JUnit XML for test result tracking
6. Upload coverage to Codecov
7. Store test results and coverage HTML reports as artifacts

### 3. Windows Testing Job (Matrix)
**Runs on**: `windows-latest`
**Python Versions**: 3.9, 3.10, 3.11, 3.12
**Purpose**: Cross-version testing on Windows platform

#### System Dependencies:
None (Windows-specific system libraries are pre-installed on Windows runners)

#### Python Dependencies:
- Base requirements
- Development tools
- Windows-specific packages (pywin32, comtypes)
- Playwright browser binaries

#### Test Steps:
Same as Linux job, adapted for Windows PowerShell syntax

### 4. Coverage Summary Job
**Runs on**: `ubuntu-latest`
**Depends on**: `test-linux`, `test-windows`
**Purpose**: Aggregate and display coverage information

#### Steps:
1. Download all coverage artifacts
2. Display summary of coverage reports

### 5. Test Status Check Job
**Runs on**: `ubuntu-latest`
**Depends on**: All previous jobs
**Purpose**: Final validation that all tests passed

#### Logic:
- Fails the workflow if any job failed
- Passes only if all jobs succeeded
- Ensures branch protection rules can enforce test passage

## Coverage Reporting

### Codecov Integration
- Coverage reports are automatically uploaded to Codecov
- Separate flags for each platform-Python version combination
- Format: `{platform}-py{version}`
- Example flags: `linux-py39`, `windows-py312`

### Coverage Reports Generated
1. **XML Format**: `coverage.xml` - For CI/CD tool integration
2. **HTML Format**: `htmlcov/` - For human review in artifacts
3. **Terminal Output**: Printed to logs with missing line information

### Coverage Configuration (from pyproject.toml)
```toml
[tool.pytest.ini_options]
addopts = [
    "--cov=mcp_server",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
]
```

## Artifact Management

### Stored Artifacts
1. **Test Results**
   - Format: JUnit XML
   - Name: `test-results-{platform}-py{version}`
   - Retention: GitHub default (90 days)

2. **Coverage Reports**
   - Format: HTML with source linking
   - Name: `coverage-report-{platform}-py{version}`
   - Location: `htmlcov/` directory

### Downloading Artifacts
```bash
# Via GitHub CLI
gh run download <run-id> -n "coverage-report-linux-py311"

# Via UI
# Actions tab -> Workflow run -> Artifacts section
```

## Linting and Type Checking Tools

### Ruff
- Fast Python linter written in Rust
- Checks for code style and common errors
- Configuration: `pyproject.toml` [tool.ruff]

### Black
- Code formatter with zero configuration
- Ensures consistent code style across the project
- Configuration: `pyproject.toml` [tool.black]

### isort
- Import statement organizer
- Groups and sorts imports automatically
- Configuration: `pyproject.toml` [tool.isort]

### mypy
- Static type checker for Python
- Validates type annotations
- Configuration: `pyproject.toml` [tool.mypy]
- Ignores missing imports for third-party libraries

### pylint
- Comprehensive code analysis tool
- Checks for bugs and style issues
- Soft fail enabled (doesn't block CI) with `|| true`
- Configuration: `pyproject.toml` [tool.pylint]

## Performance Optimizations

### Pip Caching
- Uses `actions/setup-python@v4` with `cache: "pip"`
- Speeds up dependency installation across jobs
- Cache key includes Python version and requirements hash

### Parallel Execution
- Matrix strategy runs all Python versions in parallel
- Significantly reduces total workflow execution time
- Each platform (Linux/Windows) runs independently

### Fail-Fast Control
- `fail-fast: false` allows all matrix jobs to complete
- Even if one Python version fails, others continue
- Provides comprehensive compatibility information

## Branch Protection Integration

### Recommended GitHub Branch Protection Rules
```yaml
Require status checks to pass before merging:
  - lint-and-type-check
  - test-linux (all matrix combinations)
  - test-windows (all matrix combinations)
  - test-status-check
```

## Local Development Setup

### Prerequisites
- Python 3.9, 3.10, 3.11, or 3.12
- Git

### Ubuntu/Debian Setup
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y xdotool wmctrl x11-utils xclip xsel libxrandr2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
cd mcp-accurate-click-server
pip install -e .[dev,linux]
playwright install chromium
```

### Windows Setup
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install development dependencies
cd mcp-accurate-click-server
pip install -e .[dev,windows]
playwright install chromium
```

### Run Tests Locally
```bash
# Run all tests with coverage
pytest tests/ --cov=mcp_server --cov-report=html

# Run linting
ruff check src/ tests/
black --check src/ tests/
isort --check-only src/ tests/

# Run type checking
mypy src/
```

## Troubleshooting

### Coverage Upload Failures
- `fail_ci_if_error: false` allows workflow to continue
- Check Codecov token if consistently failing
- Verify coverage.xml file is generated correctly

### System Dependency Issues (Linux)
- Some versions of xdotool may require specific X11 setup
- GitHub Actions provides full X11 environment
- For local testing, ensure X11 is running

### Playwright Browser Installation
- First run installs browser binaries
- Subsequent runs use cached binaries
- Takes ~2-3 minutes on first run per Python version

### Windows Line Ending Issues
- Workflow uses backtick (PowerShell) continuation character
- Git should be configured with `core.autocrlf = true` on Windows
- Test files use platform-agnostic line endings

## Future Enhancements

### Potential Improvements
1. Add macOS testing (`runs-on: macos-latest`)
2. Implement parallel test execution with `pytest-xdist`
3. Add performance benchmarking
4. Integrate with cloud code coverage dashboards
5. Add dependency vulnerability scanning
6. Implement container-based testing
7. Add automated release workflow
8. Integrate documentation building

## Support and Resources

### GitHub Actions Documentation
- https://docs.github.com/en/actions
- https://github.com/actions

### Tool Documentation
- Ruff: https://docs.astral.sh/ruff/
- Black: https://black.readthedocs.io/
- mypy: https://mypy.readthedocs.io/
- pytest: https://docs.pytest.org/
- Codecov: https://codecov.io/docs/

## Environment Variables and Secrets

### No Secrets Required
The current workflow does not require GitHub secrets configuration. Codecov upload uses public repository detection.

### Adding Codecov Token (Optional)
If needed, add `CODECOV_TOKEN` secret:
1. Go to Settings > Secrets and variables > Actions
2. Create new secret: `CODECOV_TOKEN`
3. Update Codecov step to use: `token: ${{ secrets.CODECOV_TOKEN }}`
