"""
Pytest Configuration and Shared Fixtures
Provides common test utilities, fixtures, and mocks for the test suite.
"""

import pytest
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from unittest.mock import Mock, MagicMock, patch
import json


# ============================================================================
# Test Data Classes
# ============================================================================

@dataclass
class MockBoundingBox:
    """Mock bounding box for testing"""
    x: float
    y: float
    width: float
    height: float
    top: float
    right: float
    bottom: float
    left: float
    page_x: float
    page_y: float
    screen_x: Optional[float] = None
    screen_y: Optional[float] = None

    @property
    def center_x(self) -> float:
        return self.x + (self.width / 2)

    @property
    def center_y(self) -> float:
        return self.y + (self.height / 2)

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass
class MockDOMElement:
    """Mock DOM element for testing"""
    tag_name: str
    element_id: Optional[str]
    class_names: List[str]
    role: Optional[str]
    aria_label: Optional[str]
    accessible_name: Optional[str]
    text_content: Optional[str]
    inner_text: Optional[str]
    value: Optional[str]
    placeholder: Optional[str]
    bounding_box: MockBoundingBox
    visible: bool
    enabled: bool
    focusable: bool
    clickable: bool
    xpath: str
    css_selector: str
    depth: int
    parent_tag: Optional[str]
    attributes: Dict[str, str]
    z_index: str
    opacity: str
    display: str
    visibility: str
    pointer_events: str
    uid: str


@dataclass
class MockDOMStructure:
    """Mock DOM structure for testing"""
    url: str
    title: str
    timestamp: float
    viewport_width: int
    viewport_height: int
    device_pixel_ratio: float
    scroll_x: float
    scroll_y: float
    page_width: float
    page_height: float
    elements: List[MockDOMElement]
    interactive_elements: List[MockDOMElement]
    text_elements: List[MockDOMElement]
    total_elements: int
    visible_elements: int
    clickable_elements: int


# ============================================================================
# Fixtures - Test Data
# ============================================================================

@pytest.fixture
def sample_calibration_points():
    """Sample calibration points for transformation testing"""
    os_points = np.array([
        [100, 100],
        [800, 100],
        [100, 500],
        [800, 500],
        [450, 300],
        [200, 200],
        [600, 200],
        [200, 400],
        [600, 400],
        [450, 150],
    ], dtype=np.float64)

    # DOM points with typical transformation (scale, rotate, translate)
    dom_points = np.array([
        [270, 220],
        [1110, 320],
        [150, 700],
        [990, 800],
        [600, 460],
        [350, 340],
        [850, 400],
        [230, 600],
        [770, 660],
        [600, 280],
    ], dtype=np.float64)

    return os_points, dom_points


@pytest.fixture
def sample_dom_element():
    """Create a sample DOM element for testing"""
    bbox = MockBoundingBox(
        x=100, y=100, width=200, height=50,
        top=100, right=300, bottom=150, left=100,
        page_x=100, page_y=200
    )

    return MockDOMElement(
        tag_name="button",
        element_id="submit-btn",
        class_names=["btn", "btn-primary"],
        role="button",
        aria_label="Submit form",
        accessible_name="Submit",
        text_content="Submit",
        inner_text="Submit",
        value=None,
        placeholder=None,
        bounding_box=bbox,
        visible=True,
        enabled=True,
        focusable=True,
        clickable=True,
        xpath='//*[@id="submit-btn"]',
        css_selector="#submit-btn",
        depth=3,
        parent_tag="form",
        attributes={"id": "submit-btn", "type": "submit"},
        z_index="auto",
        opacity="1",
        display="block",
        visibility="visible",
        pointer_events="auto",
        uid="abc123def456"
    )


@pytest.fixture
def sample_dom_structure(sample_dom_element):
    """Create a sample DOM structure for testing"""
    # Create multiple elements
    elements = [sample_dom_element]

    # Add a link element
    link_bbox = MockBoundingBox(
        x=50, y=50, width=100, height=30,
        top=50, right=150, bottom=80, left=50,
        page_x=50, page_y=150
    )
    link = MockDOMElement(
        tag_name="a",
        element_id="home-link",
        class_names=["nav-link"],
        role="link",
        aria_label=None,
        accessible_name="Home",
        text_content="Home",
        inner_text="Home",
        value=None,
        placeholder=None,
        bounding_box=link_bbox,
        visible=True,
        enabled=True,
        focusable=True,
        clickable=True,
        xpath='//*[@id="home-link"]',
        css_selector="#home-link",
        depth=2,
        parent_tag="nav",
        attributes={"id": "home-link", "href": "/"},
        z_index="auto",
        opacity="1",
        display="inline",
        visibility="visible",
        pointer_events="auto",
        uid="xyz789uvw012"
    )
    elements.append(link)

    return MockDOMStructure(
        url="http://example.com",
        title="Test Page",
        timestamp=1234567890.0,
        viewport_width=1920,
        viewport_height=1080,
        device_pixel_ratio=1.0,
        scroll_x=0,
        scroll_y=100,
        page_width=1920,
        page_height=2000,
        elements=elements,
        interactive_elements=[sample_dom_element, link],
        text_elements=[sample_dom_element, link],
        total_elements=2,
        visible_elements=2,
        clickable_elements=2
    )


# ============================================================================
# Fixtures - Mock Browser/Page
# ============================================================================

@pytest.fixture
def mock_browser():
    """Mock Playwright browser"""
    browser = MagicMock()
    browser.contexts = []
    return browser


@pytest.fixture
def mock_page():
    """Mock Playwright page with common methods"""
    page = MagicMock()

    # Basic properties
    page.url = "http://example.com"
    page.title.return_value = "Test Page"

    # Viewport
    page.viewport_size = {"width": 1920, "height": 1080}

    # Evaluate
    page.evaluate.return_value = {
        "viewport_width": 1920,
        "viewport_height": 1080,
        "device_pixel_ratio": 1.0,
        "scroll_x": 0,
        "scroll_y": 0,
        "page_width": 1920,
        "page_height": 2000
    }

    # Wait methods
    page.wait_for_load_state = MagicMock()
    page.wait_for_selector = MagicMock()

    return page


@pytest.fixture
def mock_page_with_elements(mock_page):
    """Mock page with element extraction"""

    def mock_evaluate(script):
        """Return mock element data based on script"""
        if "document.querySelectorAll" in script or "allElements" in script:
            return [
                {
                    "index": 0,
                    "tag_name": "button",
                    "element_id": "submit-btn",
                    "class_names": ["btn", "btn-primary"],
                    "role": "button",
                    "aria_label": "Submit form",
                    "accessible_name": "Submit",
                    "text_content": "Submit",
                    "inner_text": "Submit",
                    "value": None,
                    "placeholder": None,
                    "bounding_box": {
                        "x": 100, "y": 100, "width": 200, "height": 50,
                        "top": 100, "right": 300, "bottom": 150, "left": 100,
                        "page_x": 100, "page_y": 200
                    },
                    "visible": True,
                    "enabled": True,
                    "focusable": True,
                    "clickable": True,
                    "xpath": '//*[@id="submit-btn"]',
                    "css_selector": "#submit-btn",
                    "depth": 3,
                    "parent_tag": "form",
                    "attributes": {"id": "submit-btn", "type": "submit"},
                    "z_index": "auto",
                    "opacity": "1",
                    "display": "block",
                    "visibility": "visible",
                    "pointer_events": "auto"
                }
            ]
        else:
            return {
                "viewport_width": 1920,
                "viewport_height": 1080,
                "device_pixel_ratio": 1.0,
                "scroll_x": 0,
                "scroll_y": 0,
                "page_width": 1920,
                "page_height": 2000
            }

    mock_page.evaluate.side_effect = mock_evaluate
    return mock_page


# ============================================================================
# Fixtures - Windows API Mocks
# ============================================================================

@pytest.fixture
def mock_windows_api():
    """Mock Windows API functions"""
    with patch('ctypes.windll') as mock_windll:
        # Mock user32
        mock_user32 = MagicMock()
        mock_user32.GetDC.return_value = 1
        mock_user32.GetSystemMetrics.return_value = 96  # Standard DPI
        mock_user32.GetCursorPos.return_value = True
        mock_user32.GetWindowRect.return_value = True
        mock_user32.ClientToScreen.return_value = True
        mock_user32.ScreenToClient.return_value = True

        # Mock gdi32
        mock_gdi32 = MagicMock()
        mock_gdi32.GetDeviceCaps.return_value = 96  # Standard DPI

        mock_windll.user32 = mock_user32
        mock_windll.gdi32 = mock_gdi32

        yield {
            'user32': mock_user32,
            'gdi32': mock_gdi32
        }


# ============================================================================
# Fixtures - MCP Server Mocks
# ============================================================================

@pytest.fixture
def mock_mcp_server():
    """Mock MCP server instance"""
    server = MagicMock()
    server.name = "accurate-click-server"
    server.version = "1.0.0"
    server.tools = []
    server.resources = []
    return server


@pytest.fixture
def mock_mcp_request():
    """Mock MCP request"""
    request = MagicMock()
    request.method = "tools/call"
    request.params = {
        "name": "click",
        "arguments": {
            "x": 100,
            "y": 200,
            "button": "left"
        }
    }
    return request


# ============================================================================
# Utility Functions
# ============================================================================

def create_test_html(elements: List[Dict]) -> str:
    """
    Create test HTML with specified elements

    Args:
        elements: List of element specifications

    Returns:
        HTML string
    """
    html_parts = ['<!DOCTYPE html>', '<html>', '<body>']

    for elem in elements:
        tag = elem.get('tag', 'div')
        elem_id = elem.get('id', '')
        classes = elem.get('classes', [])
        text = elem.get('text', '')
        style = elem.get('style', '')

        attrs = []
        if elem_id:
            attrs.append(f'id="{elem_id}"')
        if classes:
            attrs.append(f'class="{" ".join(classes)}"')
        if style:
            attrs.append(f'style="{style}"')

        attrs_str = ' '.join(attrs)
        html_parts.append(f'<{tag} {attrs_str}>{text}</{tag}>')

    html_parts.extend(['</body>', '</html>'])
    return '\n'.join(html_parts)


def assert_coordinates_close(coord1: Tuple[float, float],
                             coord2: Tuple[float, float],
                             tolerance: float = 1.0) -> bool:
    """
    Assert two coordinates are close within tolerance

    Args:
        coord1: First coordinate (x, y)
        coord2: Second coordinate (x, y)
        tolerance: Maximum allowed distance

    Returns:
        True if within tolerance

    Raises:
        AssertionError if coordinates differ by more than tolerance
    """
    x1, y1 = coord1
    x2, y2 = coord2
    distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    assert distance <= tolerance, \
        f"Coordinates {coord1} and {coord2} differ by {distance:.2f} (tolerance: {tolerance})"
    return True


def assert_transformation_accurate(transform,
                                   source_points: np.ndarray,
                                   target_points: np.ndarray,
                                   max_error: float = 2.0) -> bool:
    """
    Assert transformation is accurate for given point pairs

    Args:
        transform: Transformation object with transform_points method
        source_points: Source coordinates (Nx2)
        target_points: Expected target coordinates (Nx2)
        max_error: Maximum allowed error in pixels

    Returns:
        True if accurate

    Raises:
        AssertionError if transformation errors exceed max_error
    """
    transformed = transform.transform_points(source_points)
    errors = np.linalg.norm(transformed - target_points, axis=1)
    max_actual_error = np.max(errors)

    assert max_actual_error <= max_error, \
        f"Transformation error {max_actual_error:.2f} exceeds maximum {max_error}"
    return True


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_browser: mark test as requiring browser"
    )
    config.addinivalue_line(
        "markers", "requires_windows: mark test as requiring Windows OS"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Add markers based on test file name
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)

        # Mark slow tests
        if "performance" in item.nodeid.lower() or "stress" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Create temporary directory for test data"""
    return tmp_path_factory.mktemp("test_data")


@pytest.fixture
def clean_test_env():
    """Ensure clean test environment"""
    # Setup
    yield
    # Teardown - can add cleanup here if needed
    pass
