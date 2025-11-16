# MCP Accurate Click Server - Test Suite

Comprehensive test suite for the MCP Accurate Click Server with 80%+ coverage.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and utilities
├── test_core.py            # MCP server core functionality tests
├── test_dom.py             # DOM extraction and mapping tests
├── test_windows.py         # Windows coordinate conversion tests
├── test_validation.py      # Click validation tests
├── test_integration.py     # End-to-end integration tests
└── README.md               # This file
```

## Test Categories

### 1. Core Tests (`test_core.py`)
- Server initialization and configuration
- Tool registration and discovery
- Request handling and routing
- Response formatting
- Error handling
- Resource management
- Server lifecycle

**Test Count:** 40+ tests

### 2. DOM Tests (`test_dom.py`)
- DOM structure extraction
- Element detection (buttons, links, inputs, etc.)
- Coordinate mapping (viewport, page, screen)
- Text finding and matching
- Z-index and overlap handling
- Scroll position handling
- Accessibility tree extraction
- Performance tests

**Test Count:** 50+ tests

### 3. Windows Tests (`test_windows.py`)
- DPI awareness and scaling
- Multi-monitor support
- Client/Screen coordinate conversion
- Affine transformations
- Calibration (least squares, RANSAC)
- Sub-pixel precision
- Error analysis
- Windows API integration

**Test Count:** 60+ tests

### 4. Validation Tests (`test_validation.py`)
- Pre-click validation
- Post-click verification
- Element visibility checks
- Clickability validation
- Coordinate accuracy validation
- Vision-based validation
- Hybrid validation strategies
- Error detection

**Test Count:** 50+ tests

### 5. Integration Tests (`test_integration.py`)
- Full click workflows
- Multi-component integration
- Real-world scenarios
- Performance under load
- Error recovery
- Cross-platform compatibility
- Data flow

**Test Count:** 30+ tests

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_core.py -v
pytest tests/test_dom.py -v
pytest tests/test_windows.py -v
pytest tests/test_validation.py -v
pytest tests/test_integration.py -v
```

### Run by Category
```bash
# Unit tests only
pytest tests/ -v -m unit

# Integration tests only
pytest tests/ -v -m integration

# Skip slow tests
pytest tests/ -v -m "not slow"

# Browser-dependent tests
pytest tests/ -v -m requires_browser

# Windows-only tests
pytest tests/ -v -m requires_windows
```

### Run with Coverage
```bash
# Generate coverage report
pytest tests/ --cov=src/mcp_server --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html # Windows
```

### Run Specific Tests
```bash
# Run tests matching pattern
pytest tests/ -v -k "test_button"

# Run specific test class
pytest tests/test_dom.py::TestDOMExtraction -v

# Run specific test
pytest tests/test_core.py::TestMCPServerInitialization::test_server_creates_with_default_config -v
```

## Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (slower, multi-component)
- `@pytest.mark.slow` - Slow-running tests (performance, large data)
- `@pytest.mark.requires_browser` - Tests requiring browser automation
- `@pytest.mark.requires_windows` - Tests requiring Windows OS

## Fixtures

### Common Fixtures (from `conftest.py`)

#### Test Data
- `sample_calibration_points` - Sample OS/DOM point pairs for calibration
- `sample_dom_element` - Sample DOM element
- `sample_dom_structure` - Sample DOM structure with multiple elements

#### Mock Objects
- `mock_browser` - Mock Playwright browser
- `mock_page` - Mock Playwright page
- `mock_page_with_elements` - Mock page with element extraction
- `mock_windows_api` - Mock Windows API functions
- `mock_mcp_server` - Mock MCP server instance
- `mock_mcp_request` - Mock MCP request

#### Utilities
- `create_test_html(elements)` - Create test HTML
- `assert_coordinates_close(coord1, coord2, tolerance)` - Assert coordinate proximity
- `assert_transformation_accurate(transform, source, target, max_error)` - Assert transformation accuracy

## Test Patterns

### Example Test Structure
```python
def test_feature_name(fixture1, fixture2):
    """Test description"""
    # 1. Setup
    input_data = {...}

    # 2. Execute
    result = function_under_test(input_data)

    # 3. Verify
    assert result.success is True
    assert result.value == expected_value
```

### Using Fixtures
```python
def test_with_fixture(sample_dom_element):
    """Test using fixture"""
    assert sample_dom_element.element_id == "submit-btn"
    assert sample_dom_element.clickable is True
```

### Parameterized Tests
```python
@pytest.mark.parametrize("input,expected", [
    (100, 150),
    (200, 300),
    (300, 450),
])
def test_scaling(input, expected):
    """Test with multiple inputs"""
    result = scale(input, factor=1.5)
    assert result == expected
```

## Coverage Goals

Target: **> 80% coverage** across all modules

Current coverage by module:
- Core: TBD
- DOM: TBD
- Windows: TBD
- Validation: TBD
- Integration: TBD

## Best Practices

### Test Naming
- Use descriptive names: `test_<feature>_<scenario>_<expected_result>`
- Example: `test_button_click_with_scroll_workflow`

### Test Organization
- Group related tests in classes
- One assertion per test (when possible)
- Test both success and failure cases

### Mocking
- Mock external dependencies (Windows API, browser)
- Don't mock code under test
- Use descriptive mock names

### Assertions
- Use specific assertions: `assert x == y` not `assert x`
- Include failure messages: `assert x == y, f"Expected {y}, got {x}"`
- Use pytest helpers: `pytest.approx()` for floats

### Performance
- Mark slow tests with `@pytest.mark.slow`
- Keep unit tests fast (< 100ms)
- Use fixtures for expensive setup

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest tests/ --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure package is installed in development mode
pip install -e .
```

**Browser Tests Failing**
```bash
# Install Playwright browsers
playwright install chromium
```

**Windows API Tests Failing on Non-Windows**
```bash
# Skip Windows-specific tests
pytest tests/ -m "not requires_windows"
```

**Slow Test Runs**
```bash
# Run in parallel
pip install pytest-xdist
pytest tests/ -n auto
```

## Contributing

When adding new tests:

1. Follow existing test patterns
2. Add appropriate markers (`@pytest.mark.*`)
3. Use fixtures from `conftest.py`
4. Update this README if adding new test categories
5. Ensure coverage doesn't decrease
6. Run full test suite before committing

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Playwright Testing](https://playwright.dev/python/docs/test-runners)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

## License

Same as parent project.
