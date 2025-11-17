# GitHub Actions Workflow - Quick Reference

## What Gets Tested?

### Platforms
- Linux (Ubuntu latest)
- Windows (latest)

### Python Versions
- 3.9
- 3.10
- 3.11
- 3.12

### Total Test Matrix
**8 platform-version combinations** (4 versions × 2 platforms)

## When Does It Run?

### Automatic Triggers
- **Push** to `main`, `develop`, `feature/**` branches
- **Pull Requests** to `main` or `develop`

### Manual Trigger
- GitHub Actions UI: "Run workflow" button

## What Gets Checked?

### 1. Code Quality (Lint and Type Check)
```bash
ruff check src/ tests/           # Ruff linting
black --check src/ tests/        # Black formatting
isort --check-only src/ tests/   # Import sorting
mypy src/                        # Type checking
pylint src/                      # Code analysis (soft fail)
```

### 2. Testing
- Run pytest with coverage on both platforms
- Python 3.9, 3.10, 3.11, 3.12

### 3. System Dependencies (Linux only)
Automatically installed:
- xdotool
- wmctrl
- x11-utils
- xclip, xsel
- libxrandr2

## Coverage Reports

### Where to Find Them
1. **After workflow completes**: GitHub Actions → Run details → Artifacts
2. **Codecov**: https://codecov.io (if configured)

### What's Included
- XML format (for CI tools)
- HTML format (for human review)
- Terminal summary (in logs)

### Coverage Files by Platform
```
coverage-report-linux-py39
coverage-report-linux-py310
coverage-report-linux-py311
coverage-report-linux-py312
coverage-report-windows-py39
coverage-report-windows-py310
coverage-report-windows-py311
coverage-report-windows-py312
```

## Test Results

### Test Result Files
```
test-results-linux-py39
test-results-linux-py310
test-results-linux-py311
test-results-linux-py312
test-results-windows-py39
test-results-windows-py310
test-results-windows-py311
test-results-windows-py312
```

### JUnit XML Format
- Compatible with GitHub Actions, Azure DevOps, Jenkins, etc.
- Can be parsed for detailed test metrics

## Job Dependencies

```
lint-and-type-check ────────────┐
                                ├──> test-status-check (final gate)
test-linux (4 versions) ────────┤
                                │
test-windows (4 versions) ──────┤
                                ├──> coverage-summary
```

## Execution Time Estimate

### Per Job
- **Lint and Type Check**: 2-3 minutes
- **Linux Test Matrix**: 5-7 minutes (runs in parallel)
- **Windows Test Matrix**: 7-10 minutes (runs in parallel)
- **Coverage Summary**: < 1 minute

### Total Pipeline Time
**~10-15 minutes** (jobs run in parallel)

## Failure Scenarios

### Lint Fails
- Fix with: `black . && isort . && ruff check --fix`
- Type errors: `mypy src/`

### Tests Fail
- Check logs in GitHub Actions UI
- Download coverage report to investigate
- Run locally: `pytest tests/ --cov=mcp_server`

### System Dependencies Missing (Linux)
- Workflow handles this automatically
- If testing locally, install: `sudo apt-get install xdotool wmctrl x11-utils`

## Local Development

### Install Same Dependencies
```bash
# Linux
sudo apt-get install xdotool wmctrl x11-utils xclip xsel libxrandr2

# Create env and install
python3 -m venv venv
source venv/bin/activate
cd mcp-accurate-click-server
pip install -e .[dev,linux]  # or [dev,windows]
```

### Run Same Tests Locally
```bash
# Run with same parameters as CI
pytest tests/ \
  --cov=mcp_server \
  --cov-report=html \
  --cov-report=term-missing

# Check code quality
ruff check src/ tests/
black --check src/ tests/
isort --check-only src/ tests/
mypy src/
```

## Common Commands

### Check Workflow Status
```bash
# GitHub CLI
gh run list --workflow=cross-platform-tests.yml

# View specific run
gh run view <run-id> --log
```

### Download Coverage Report
```bash
gh run download <run-id> -n "coverage-report-linux-py311"
```

### Re-run Failed Workflow
```bash
gh run rerun <run-id>
```

### View Workflow File
```bash
cat .github/workflows/cross-platform-tests.yml
```

## Configuration Files Used

- `.github/workflows/cross-platform-tests.yml` - Main workflow
- `pyproject.toml` - Python project config (pytest, coverage, linting)
- `requirements-dev.txt` - Development dependencies
- `setup.py` - Package setup (minimal, uses pyproject.toml)

## Key Features

✓ Cross-platform testing (Linux + Windows)
✓ Multi-version Python support (3.9-3.12)
✓ Comprehensive code quality checks
✓ Coverage reporting with Codecov integration
✓ Artifact storage for all test results
✓ Parallel execution for speed
✓ No configuration required (uses existing project config)
✓ Branch protection compatible
✓ Manual trigger support

## Next Steps

### For Developers
1. Write tests in `tests/` directory
2. Push code to branch
3. Open pull request
4. Wait for workflow to complete
5. Review coverage and test results

### For Repository Maintainers
1. Configure branch protection (recommended)
2. Add Codecov token if using Codecov badges
3. Monitor workflow runs in Actions tab

### For Enhancement
See `.github/CI_CD_SETUP.md` for future improvement suggestions

## Help & Support

### Debugging Failed Workflows
1. Check "Logs" tab in failed job
2. Look for specific error messages
3. Search GitHub Actions documentation
4. Test locally with same Python version

### Contact
Refer to project README or CONTRIBUTING.md for support information
