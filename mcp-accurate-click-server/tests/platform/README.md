# Platform Tests for MCP Accurate Click Server

Comprehensive cross-platform test suite covering Linux X11, Linux Wayland, and cross-platform functionality.

## Test Structure

### test_linux_integration.py
**40+ tests** covering all 4 Linux modules:

1. **LinuxInputSimulator Tests (8 tests)**
   - Singleton pattern
   - Display server detection (X11/Wayland)
   - Mouse movement with pynput
   - Clicking with all mouse buttons
   - Vertical and horizontal scrolling
   - Cursor position retrieval
   - Input delay configuration

2. **LinuxDPIHandler Tests (10 tests)**
   - X11 and Wayland display server detection
   - Single and dual monitor enumeration
   - Monitor selection by point
   - Primary monitor identification
   - Mixed DPI environment detection
   - Cache invalidation and performance
   - Scale factor calculations
   - Environment variable scaling (GDK_SCALE, QT_SCALE_FACTOR)

3. **LinuxWindowManager Tests (8 tests)**
   - Command availability detection (wmctrl, xdotool, xwininfo)
   - X11 initialization with python-xlib
   - Browser process name detection
   - Window ID parsing (hex/decimal formats)
   - Process info retrieval with psutil
   - Screen ↔ Client coordinate conversions
   - WM_CLASS browser detection

4. **LinuxCoordinateConverter Tests (10 tests)**
   - Display server detection
   - Xrandr output parsing (single/dual/negative coords)
   - Virtual screen bounds calculation
   - Physical ↔ Logical pixel conversions
   - Physical ↔ CSS pixel conversions
   - CSS ↔ DOM coordinate conversions
   - Full conversion chain testing

5. **Performance and Edge Cases (6 tests)**
   - Input simulator performance benchmarks
   - DPI handler cache performance
   - Xrandr timeout handling
   - Invalid xrandr output handling
   - Missing dependencies handling
   - Monitor count detection

6. **Abstract Base Class Compliance (4 tests)**
   - Verification that all abstract methods are implemented
   - Tests for InputSimulator, DPIHandler, WindowManager, CoordinateConverter

### test_cross_platform.py
**33+ tests** for platform-agnostic functionality:

1. **Common Data Structures (8 tests)**
   - MouseButton and KeyModifier enums
   - MonitorInfo properties and calculations
   - WindowInfo properties (chrome offsets, dimensions)
   - Point coordinate spaces
   - Rectangle containment and properties
   - Negative coordinates handling

2. **Platform Detection (5 tests)**
   - Current platform detection
   - Linux module imports on Linux
   - Windows module imports on Windows
   - Platform module selection logic

3. **Abstract Base Classes (4 tests)**
   - Verification that ABCs cannot be instantiated
   - Interface enforcement

4. **Coordinate Conversion Logic (6 tests)**
   - DPI to scale factor conversions
   - Physical ↔ Logical formulas
   - Physical ↔ CSS formulas
   - CSS ↔ DOM formulas
   - Inverse conversion roundtrips

5. **Multi-Monitor Scenarios (6 tests)**
   - Dual monitors side-by-side
   - Dual monitors stacked vertically
   - Negative coordinates (monitor left of primary)
   - Mixed DPI monitors
   - Point-to-monitor mapping
   - Virtual desktop spanning

6. **Error Handling (4 tests)**
   - Missing monitor handling
   - Invalid window handle handling
   - Out-of-bounds coordinates
   - Zero/negative DPI handling

## Running Tests

### Run all platform tests
```bash
pytest tests/platform/ -v
```

### Run only Linux integration tests
```bash
pytest tests/platform/test_linux_integration.py -v
```

### Run only cross-platform tests
```bash
pytest tests/platform/test_cross_platform.py -v
```

### Run with coverage
```bash
pytest tests/platform/ --cov=mcp_server.platform --cov-report=html
```

### Run specific test class
```bash
pytest tests/platform/test_linux_integration.py::TestLinuxInputSimulator -v
```

### Run tests matching pattern
```bash
pytest tests/platform/ -k "dpi" -v
```

## Test Features

### Mocking Strategy
All external dependencies are mocked for CI/CD compatibility:
- **subprocess.run**: Mocked for xrandr, wmctrl, xdotool, etc.
- **pynput**: Mocked Controller and Button classes
- **python-xlib**: Mocked Display and X11 operations
- **psutil**: Mocked Process class

### Fixtures
Comprehensive fixtures in `conftest.py`:
- Environment mocking (X11, Wayland)
- Command output mocking (xrandr, wmctrl, wlr-randr)
- Sample data (monitors, windows)
- Performance thresholds
- Platform detection

### Parametrization
Tests use `@pytest.fixture(params=...)` for:
- Different DPI values (96, 120, 144, 192)
- Different scale factors (1.0, 1.25, 1.5, 2.0)
- Different mouse buttons (LEFT, RIGHT, MIDDLE)
- Different monitor configurations

### Performance Benchmarks
- Input simulator operations: < 1 second for 100 operations
- Cache speedup: 10x faster on subsequent calls
- Monitor enumeration: < 500ms

## Coverage Goals

Target: **90%+ code coverage** for all Linux modules

Covered areas:
- ✅ All public methods
- ✅ Error handling paths
- ✅ Edge cases (negative coords, missing deps, timeouts)
- ✅ Multi-monitor scenarios
- ✅ Different display servers (X11/Wayland)
- ✅ Different DPI configurations
- ✅ Singleton patterns
- ✅ Cache mechanisms

## Test Design Principles

1. **Isolation**: Each test is independent, mocks external dependencies
2. **Determinism**: No flaky tests, consistent results
3. **Fast**: All tests complete in < 5 seconds total
4. **Readable**: Clear test names describing what is being tested
5. **Maintainable**: Fixtures reduce duplication
6. **CI-Friendly**: No actual system calls, works in containers

## Adding New Tests

When adding new platform functionality:

1. Add tests to appropriate test class
2. Mock all external dependencies
3. Test happy path and error cases
4. Add performance benchmark if applicable
5. Update this README with test count

Example:
```python
@patch('mcp_server.platform.linux.module.subprocess.run')
def test_new_feature(self, mock_run, sample_fixture):
    """Test description."""
    # Arrange
    mock_run.return_value = MagicMock(returncode=0, stdout="...")

    # Act
    result = module.new_feature()

    # Assert
    assert result == expected
```

## Dependencies

Required for running tests:
```bash
pip install pytest pytest-cov pytest-mock
```

Optional (for actual platform code, but mocked in tests):
```bash
pip install pynput python-xlib psutil
```

## Notes

- Tests work on any platform due to comprehensive mocking
- X11 and Wayland specific tests are clearly marked
- All abstract base class methods are verified as implemented
- Performance tests ensure code efficiency
- Multi-monitor tests cover complex scenarios
