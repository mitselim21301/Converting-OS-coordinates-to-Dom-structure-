# Integration Testing Guide

## Quick Start

### Prerequisites
```bash
cd mcp-accurate-click-server
pip install -r requirements-dev.txt
```

### Run All Integration Tests
```bash
pytest tests/test_integration_final.py -v -s
```

---

## Test Categories

### 1. Import Verification (8 tests)
Verifies all modules can be imported correctly.

```bash
pytest tests/test_integration_final.py::TestImportVerification -v
```

**Tests:**
- `test_import_mcp_server_root` - Root module import
- `test_import_core_module` - Core submodule imports
- `test_import_platform_module` - Platform factory imports
- `test_import_dom_module` - DOM extraction imports
- `test_import_validation_module` - Validation module imports
- `test_import_accessibility_module` - Accessibility module imports
- `test_import_vision_module` - Vision module imports (optional)
- `test_import_windows_module_availability` - Windows module imports
- `test_import_linux_module_availability` - Linux module imports

**Expected Output:**
```
✓ All modules import successfully
✓ Classes and functions available
✓ Optional modules detected correctly
```

---

### 2. Platform Factory Functions (7 tests)
Tests cross-platform factory pattern.

```bash
pytest tests/test_integration_final.py::TestPlatformFactories -v
```

**Tests:**
- `test_get_platform_function` - Platform detection
- `test_platform_detection_functions` - is_windows/is_linux/is_macos
- `test_get_input_simulator_factory` - Input simulator factory
- `test_get_dpi_handler_factory` - DPI handler factory
- `test_get_window_manager_factory` - Window manager factory
- `test_get_coordinate_converter_factory` - Coordinate converter factory
- `test_platform_factory_consistency` - All factories consistent

**Expected Output:**
```
✓ Platform correctly detected
✓ Platform-specific implementations returned
✓ Factories throw appropriate errors for unsupported platforms
```

---

### 3. End-to-End Workflow (4 tests)
Tests complete server lifecycle.

```bash
pytest tests/test_integration_final.py::TestE2EWorkflow -v
```

**Tests:**
- `test_server_creation_and_config` - Server instantiation
- `test_server_lifecycle` - Server start/stop
- `test_tool_registry_integration` - Tool registry
- `test_configuration_manager_integration` - Config manager

**Expected Output:**
```
✓ Server creates successfully
✓ Config loads correctly
✓ Tool registry has tools
✓ Configuration manager works
```

---

### 4. Coordinate Pipeline (6 tests)
Tests complete coordinate transformation pipeline.

```bash
pytest tests/test_integration_final.py::TestCoordinatePipeline -v
```

**Tests:**
- `test_dom_element_bounding_box` - BoundingBox calculations
- `test_dom_element_coordinate_systems` - Coordinate system handling
- `test_coordinate_transformation_chain` - Full transformation
- `test_dom_to_physical_coordinate_mapping` - DOM to OS coords
- `test_pipeline_with_viewport_scroll` - Scroll handling
- `test_pipeline_with_dpi_scaling` - DPI scaling

**Expected Output:**
```
✓ Bounding box calculations correct
✓ Coordinate systems convert properly
✓ Transformation chain works
✓ DPI scaling applied correctly
```

---

### 5. Windows Compatibility (7 tests)
Tests Windows-specific functionality.

```bash
pytest tests/test_integration_final.py::TestWindowsCompatibility -v
```

**Tests:**
- `test_windows_platform_detection` - Windows detection
- `test_windows_module_imports` - Windows module imports (Windows only)
- `test_windows_dpi_handler` - DPI handler (Windows only)
- `test_windows_window_manager` - Window manager (Windows only)
- `test_windows_coordinate_converter` - Converter (Windows only)
- `test_windows_input_simulator` - Input simulator (Windows only)
- `test_windows_compatibility_not_broken` - Compatibility check

**Expected Output:**
```
On Windows:
✓ All Windows modules import
✓ All Windows factories work

On Linux/macOS:
✓ Windows compatibility verified (not broken)
```

---

### 6. Integration Smoke Tests (6 tests)
Quick tests of basic functionality.

```bash
pytest tests/test_integration_final.py::TestIntegrationSmoke -v
```

**Tests:**
- `test_server_import_and_instantiate` - Server creation
- `test_config_creation` - Configuration
- `test_tool_registry_basic` - Tool registry
- `test_platform_factory_basic` - Platform detection
- `test_dom_module_basic` - DOM module
- `test_feature_detection` - Feature detection

**Expected Output:**
```
✓ Basic functionality works
✓ All modules accessible
✓ No import errors
```

---

### 7. Integration Documentation (3 tests)
Tests that documentation is complete.

```bash
pytest tests/test_integration_final.py::TestIntegrationDocumentation -v
```

**Tests:**
- `test_integration_points_documented` - Integration points
- `test_version_consistency` - Version numbers
- `test_api_completeness` - API completeness

**Expected Output:**
```
✓ Integration points documented
✓ Versions consistent
✓ API complete
```

---

## Running Tests by Platform

### On Windows
```bash
# All tests run, including Windows-specific tests
pytest tests/test_integration_final.py -v

# Windows-specific tests
pytest tests/test_integration_final.py::TestWindowsCompatibility -v -k "windows"
```

### On Linux
```bash
# All tests run, Windows tests skipped appropriately
pytest tests/test_integration_final.py -v

# Check platform factory consistency
pytest tests/test_integration_final.py::TestPlatformFactories::test_get_coordinate_converter_factory -v
```

### On macOS
```bash
# All tests run, macOS support tests skipped (not yet implemented)
pytest tests/test_integration_final.py -v

# Tests will show macOS as detected but some factories raise NotImplemented
```

---

## Test Output Interpretation

### Successful Test Run
```
tests/test_integration_final.py::TestImportVerification::test_import_mcp_server_root PASSED
tests/test_integration_final.py::TestImportVerification::test_import_core_module PASSED
...
======================== 41 passed in 2.34s ========================
```

### Expected Warnings (not failures)
```
# In headless environment (expected)
⊘ Windows module (not on Windows)
⊘ Linux display (headless environment)
⊘ macOS support (not yet implemented)
```

### Actual Failures (should not occur)
```
# These indicate real problems:
✗ ImportError: Cannot import module
✗ AttributeError: Missing class/function
✗ AssertionError: Test assertion failed
```

---

## Troubleshooting

### Module Not Found Error
**Problem:** `ModuleNotFoundError: No module named 'X'`

**Solution:**
```bash
pip install -r requirements-dev.txt
export PYTHONPATH=/path/to/mcp-accurate-click-server/src:$PYTHONPATH
```

### Test Collection Error
**Problem:** `ERROR collecting tests/test_integration_final.py`

**Solution:**
```bash
# Install missing dependencies
pip install pytest pytest-asyncio pytest-mock numpy pydantic

# Check imports
python -c "import tests.test_integration_final"
```

### Platform-Specific Import Error
**Problem:** On Linux: `NameError: name 'Xatom' is not defined`

**Solution:** This is expected in headless environments. Tests handle this gracefully.
```bash
# Run tests with appropriate logging
pytest tests/test_integration_final.py -v --log-level=DEBUG
```

### Async Test Error
**Problem:** `RuntimeError: no running event loop`

**Solution:** Ensure pytest-asyncio is installed:
```bash
pip install pytest-asyncio
```

---

## Continuous Integration

### GitHub Actions Example
```yaml
name: Integration Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.9, '3.10', '3.11']

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt

      - name: Run integration tests
        run: |
          pytest tests/test_integration_final.py -v --tb=short
```

---

## Performance Testing

### Run with Timing
```bash
pytest tests/test_integration_final.py -v --durations=10
```

### Expected Timing
```
test_import_mcp_server_root: 0.01s ✓
test_platform_factory_consistency: 0.05s ✓
test_coordinate_transformation_chain: 0.02s ✓
...
Total: ~2-3 seconds ✓
```

---

## Coverage Analysis

### Generate Coverage Report
```bash
pytest tests/test_integration_final.py \
  --cov=mcp_server \
  --cov-report=html \
  --cov-report=term
```

### View Coverage
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Expected Coverage
```
mcp_server/core/: 95%+ ✓
mcp_server/platform/: 85%+ ✓
mcp_server/dom/: 90%+ ✓
Overall: 89%+ ✓
```

---

## Test Maintenance

### Adding New Tests

1. Add test method to appropriate test class
2. Use clear naming: `test_[feature]_[scenario]`
3. Include docstring explaining what's tested
4. Use fixtures for common setup
5. Log important assertions

Example:
```python
class TestNewFeature:
    def test_new_feature_works(self):
        """Test that new feature works correctly"""
        from mcp_server.new_module import NewClass

        obj = NewClass()
        assert obj is not None
        logger.info("✓ New feature working")
```

### Updating Existing Tests

1. Maintain backward compatibility
2. Update docstrings
3. Run full test suite
4. Check coverage impact
5. Update this guide if needed

---

## Debugging Tests

### Run Single Test with Verbose Output
```bash
pytest tests/test_integration_final.py::TestImportVerification::test_import_mcp_server_root -vv -s
```

### Run with Debug Output
```bash
pytest tests/test_integration_final.py -v -s --log-level=DEBUG
```

### Run with Print Statements
```bash
pytest tests/test_integration_final.py -v -s --capture=no
```

### Check Python Path
```bash
python -c "
import sys
print('Python Path:')
for p in sys.path:
    print(f'  {p}')
"
```

---

## Integration Test Summary

| Test Suite | Tests | Time | Status |
|-----------|-------|------|--------|
| TestImportVerification | 8 | ~0.5s | ✓ |
| TestPlatformFactories | 7 | ~0.3s | ✓ |
| TestE2EWorkflow | 4 | ~0.2s | ✓ |
| TestCoordinatePipeline | 6 | ~0.3s | ✓ |
| TestWindowsCompatibility | 7 | ~0.3s | ✓ |
| TestIntegrationSmoke | 6 | ~0.3s | ✓ |
| TestIntegrationDocumentation | 3 | ~0.1s | ✓ |
| **TOTAL** | **41** | **~2.0s** | **✓** |

---

## References

- Main Documentation: `/INTEGRATION_COMPLETE.md`
- Verification Report: `/INTEGRATION_VERIFICATION_REPORT.md`
- Test File: `tests/test_integration_final.py`
- Examples: `examples/`
- API Reference: `src/mcp_server/`

---

**Last Updated:** 2025-11-17
**Version:** 1.0.0
