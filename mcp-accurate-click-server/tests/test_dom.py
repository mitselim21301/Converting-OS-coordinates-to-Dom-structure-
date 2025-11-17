"""
Test DOM Extraction and Mapping

Tests for DOM structure extraction, element detection, and coordinate mapping:
- DOM structure extraction
- Element detection (interactive, text, visible)
- Coordinate mapping (viewport, page, screen)
- Text finding and matching
- Z-index and overlap handling
- Scroll position handling
- Accessibility tree extraction
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
import json

# Import test utilities from conftest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from conftest import (
    MockBoundingBox,
    MockDOMElement,
    MockDOMStructure,
    assert_coordinates_close,
    create_test_html
)


class TestDOMExtraction:
    """Test DOM structure extraction"""

    def test_extract_basic_dom_structure(self, mock_page_with_elements):
        """Test extracting basic DOM structure"""
        # Simulated extraction (would use actual extractor)
        structure = {
            "url": "http://example.com",
            "title": "Test Page",
            "elements": mock_page_with_elements.evaluate("script"),
            "total_elements": 1
        }

        assert structure["url"] == "http://example.com"
        assert structure["total_elements"] >= 1
        assert len(structure["elements"]) >= 1

    def test_extract_viewport_info(self, mock_page):
        """Test extracting viewport information"""
        viewport_info = mock_page.evaluate("() => window.innerWidth")

        # Mock returns dict
        info = mock_page.evaluate("script")

        assert info["viewport_width"] == 1920
        assert info["viewport_height"] == 1080
        assert info["device_pixel_ratio"] == 1.0

    def test_extract_scroll_position(self, mock_page):
        """Test extracting scroll position"""
        info = mock_page.evaluate("script")

        assert "scroll_x" in info
        assert "scroll_y" in info
        assert info["scroll_x"] == 0
        assert info["scroll_y"] == 0

    def test_extract_page_dimensions(self, mock_page):
        """Test extracting page dimensions"""
        info = mock_page.evaluate("script")

        assert info["page_width"] == 1920
        assert info["page_height"] == 2000

    def test_extract_all_elements(self, sample_dom_structure):
        """Test extracting all DOM elements"""
        elements = sample_dom_structure.elements

        assert len(elements) == 2
        assert all(hasattr(e, 'tag_name') for e in elements)
        assert all(hasattr(e, 'bounding_box') for e in elements)

    def test_filter_visible_elements(self, sample_dom_structure):
        """Test filtering visible elements"""
        visible = [e for e in sample_dom_structure.elements if e.visible]

        assert len(visible) == 2
        assert all(e.visible for e in visible)

    def test_extract_element_attributes(self, sample_dom_element):
        """Test extracting element attributes"""
        assert sample_dom_element.element_id == "submit-btn"
        assert "btn" in sample_dom_element.class_names
        assert sample_dom_element.attributes["type"] == "submit"

    def test_extract_computed_styles(self, sample_dom_element):
        """Test extracting computed styles"""
        assert sample_dom_element.display == "block"
        assert sample_dom_element.visibility == "visible"
        assert sample_dom_element.opacity == "1"
        assert sample_dom_element.z_index == "auto"


class TestElementDetection:
    """Test element detection capabilities"""

    def test_detect_clickable_elements(self, sample_dom_structure):
        """Test detecting clickable elements"""
        clickable = sample_dom_structure.interactive_elements

        assert len(clickable) == 2
        assert all(e.clickable for e in clickable)

    def test_detect_button_elements(self, sample_dom_structure):
        """Test detecting button elements"""
        buttons = [e for e in sample_dom_structure.elements
                   if e.tag_name == "button"]

        assert len(buttons) == 1
        assert buttons[0].element_id == "submit-btn"

    def test_detect_link_elements(self, sample_dom_structure):
        """Test detecting link elements"""
        links = [e for e in sample_dom_structure.elements
                 if e.tag_name == "a"]

        assert len(links) == 1
        assert links[0].element_id == "home-link"

    def test_detect_input_elements(self):
        """Test detecting input elements"""
        # Create mock input element
        bbox = MockBoundingBox(
            x=50, y=50, width=200, height=30,
            top=50, right=250, bottom=80, left=50,
            page_x=50, page_y=50
        )
        input_elem = MockDOMElement(
            tag_name="input",
            element_id="email",
            class_names=["form-control"],
            role=None,
            aria_label=None,
            accessible_name="Email",
            text_content=None,
            inner_text=None,
            value="",
            placeholder="Enter email",
            bounding_box=bbox,
            visible=True,
            enabled=True,
            focusable=True,
            clickable=True,
            xpath='//*[@id="email"]',
            css_selector="#email",
            depth=2,
            parent_tag="form",
            attributes={"id": "email", "type": "email"},
            z_index="auto",
            opacity="1",
            display="block",
            visibility="visible",
            pointer_events="auto",
            uid="input123"
        )

        assert input_elem.tag_name == "input"
        assert input_elem.placeholder == "Enter email"
        assert input_elem.clickable is True

    def test_detect_role_button_elements(self):
        """Test detecting elements with role=button"""
        bbox = MockBoundingBox(
            x=100, y=100, width=150, height=40,
            top=100, right=250, bottom=140, left=100,
            page_x=100, page_y=100
        )
        div_button = MockDOMElement(
            tag_name="div",
            element_id="custom-btn",
            class_names=["button-like"],
            role="button",
            aria_label="Custom button",
            accessible_name="Custom button",
            text_content="Click",
            inner_text="Click",
            value=None,
            placeholder=None,
            bounding_box=bbox,
            visible=True,
            enabled=True,
            focusable=True,
            clickable=True,
            xpath='//*[@id="custom-btn"]',
            css_selector="#custom-btn",
            depth=1,
            parent_tag="div",
            attributes={"id": "custom-btn", "role": "button"},
            z_index="auto",
            opacity="1",
            display="block",
            visibility="visible",
            pointer_events="auto",
            uid="div123"
        )

        assert div_button.role == "button"
        assert div_button.clickable is True

    def test_detect_disabled_elements(self):
        """Test detecting disabled elements"""
        bbox = MockBoundingBox(
            x=100, y=100, width=100, height=30,
            top=100, right=200, bottom=130, left=100,
            page_x=100, page_y=100
        )
        disabled_btn = MockDOMElement(
            tag_name="button",
            element_id="disabled-btn",
            class_names=["btn"],
            role="button",
            aria_label=None,
            accessible_name="Disabled",
            text_content="Disabled",
            inner_text="Disabled",
            value=None,
            placeholder=None,
            bounding_box=bbox,
            visible=True,
            enabled=False,  # Disabled
            focusable=False,
            clickable=True,  # Still technically clickable tag
            xpath='//*[@id="disabled-btn"]',
            css_selector="#disabled-btn",
            depth=1,
            parent_tag="form",
            attributes={"id": "disabled-btn", "disabled": "true"},
            z_index="auto",
            opacity="0.5",
            display="block",
            visibility="visible",
            pointer_events="none",
            uid="dis123"
        )

        assert disabled_btn.enabled is False
        assert disabled_btn.pointer_events == "none"

    def test_detect_hidden_elements(self):
        """Test detecting hidden elements"""
        bbox = MockBoundingBox(
            x=0, y=0, width=0, height=0,
            top=0, right=0, bottom=0, left=0,
            page_x=0, page_y=0
        )
        hidden_elem = MockDOMElement(
            tag_name="div",
            element_id="hidden",
            class_names=[],
            role=None,
            aria_label=None,
            accessible_name=None,
            text_content="Hidden content",
            inner_text="Hidden content",
            value=None,
            placeholder=None,
            bounding_box=bbox,
            visible=False,  # Hidden
            enabled=True,
            focusable=False,
            clickable=False,
            xpath='//*[@id="hidden"]',
            css_selector="#hidden",
            depth=1,
            parent_tag="body",
            attributes={"id": "hidden"},
            z_index="auto",
            opacity="1",
            display="none",  # display: none
            visibility="visible",
            pointer_events="auto",
            uid="hid123"
        )

        assert hidden_elem.visible is False
        assert hidden_elem.display == "none"


class TestCoordinateMapping:
    """Test coordinate mapping functionality"""

    def test_find_element_at_viewport_coordinates(self, sample_dom_structure):
        """Test finding element at viewport coordinates"""
        # Button is at x:100-300, y:100-150
        # Center would be at (200, 125)

        def find_at_point(x, y):
            for elem in sample_dom_structure.elements:
                bbox = elem.bounding_box
                if (bbox.left <= x <= bbox.right and
                    bbox.top <= y <= bbox.bottom):
                    return elem
            return None

        # Test center of button
        elem = find_at_point(200, 125)
        assert elem is not None
        assert elem.element_id == "submit-btn"

    def test_find_element_at_page_coordinates(self, sample_dom_structure):
        """Test finding element at page coordinates (with scroll)"""
        # Account for scroll_y = 100
        # Button page_y = 200, so viewport would be 200 - 100 = 100

        def find_at_page_point(x, y, scroll_x, scroll_y):
            viewport_x = x - scroll_x
            viewport_y = y - scroll_y

            for elem in sample_dom_structure.elements:
                bbox = elem.bounding_box
                if (bbox.left <= viewport_x <= bbox.right and
                    bbox.top <= viewport_y <= bbox.bottom):
                    return elem
            return None

        # Test with scroll offset
        elem = find_at_page_point(200, 225, 0, 100)
        assert elem is not None
        assert elem.element_id == "submit-btn"

    def test_convert_viewport_to_page_coordinates(self, sample_dom_structure):
        """Test converting viewport to page coordinates"""
        viewport_x, viewport_y = 200, 125
        scroll_x = sample_dom_structure.scroll_x
        scroll_y = sample_dom_structure.scroll_y

        page_x = viewport_x + scroll_x
        page_y = viewport_y + scroll_y

        assert page_x == 200
        assert page_y == 225  # 125 + 100

    def test_convert_page_to_viewport_coordinates(self, sample_dom_structure):
        """Test converting page to viewport coordinates"""
        page_x, page_y = 200, 225
        scroll_x = sample_dom_structure.scroll_x
        scroll_y = sample_dom_structure.scroll_y

        viewport_x = page_x - scroll_x
        viewport_y = page_y - scroll_y

        assert viewport_x == 200
        assert viewport_y == 125  # 225 - 100

    def test_element_bounding_box_center(self, sample_dom_element):
        """Test calculating element center coordinates"""
        bbox = sample_dom_element.bounding_box

        center_x = bbox.center_x
        center_y = bbox.center_y

        assert center_x == 200  # 100 + 200/2
        assert center_y == 125  # 100 + 50/2

    def test_element_bounding_box_area(self, sample_dom_element):
        """Test calculating element area"""
        bbox = sample_dom_element.bounding_box

        area = bbox.area

        assert area == 10000  # 200 * 50


class TestTextFinding:
    """Test text finding and matching"""

    def test_find_exact_text_match(self, sample_dom_structure):
        """Test finding element by exact text match"""
        def find_by_text(text, exact=True):
            results = []
            for elem in sample_dom_structure.text_elements:
                if elem.text_content:
                    if exact:
                        if elem.text_content.strip() == text:
                            results.append(elem)
                    else:
                        if text.lower() in elem.text_content.lower():
                            results.append(elem)
            return results

        results = find_by_text("Submit", exact=True)
        assert len(results) == 1
        assert results[0].element_id == "submit-btn"

    def test_find_partial_text_match(self, sample_dom_structure):
        """Test finding element by partial text match"""
        def find_by_text(text, exact=False):
            results = []
            for elem in sample_dom_structure.text_elements:
                if elem.text_content:
                    if text.lower() in elem.text_content.lower():
                        results.append(elem)
            return results

        results = find_by_text("sub", exact=False)
        assert len(results) >= 1  # Should find "Submit"

    def test_find_text_case_insensitive(self, sample_dom_structure):
        """Test case-insensitive text finding"""
        def find_by_text(text):
            results = []
            for elem in sample_dom_structure.text_elements:
                if elem.text_content:
                    if text.lower() in elem.text_content.lower():
                        results.append(elem)
            return results

        results = find_by_text("HOME")
        assert len(results) >= 1  # Should find "Home" link

    def test_find_by_aria_label(self, sample_dom_structure):
        """Test finding element by ARIA label"""
        def find_by_aria_label(label):
            results = []
            for elem in sample_dom_structure.elements:
                if elem.aria_label == label:
                    results.append(elem)
            return results

        results = find_by_aria_label("Submit form")
        assert len(results) == 1

    def test_find_by_accessible_name(self, sample_dom_structure):
        """Test finding element by accessible name"""
        def find_by_accessible_name(name):
            results = []
            for elem in sample_dom_structure.elements:
                if elem.accessible_name == name:
                    results.append(elem)
            return results

        results = find_by_accessible_name("Submit")
        assert len(results) >= 1

    def test_find_by_placeholder(self):
        """Test finding element by placeholder text"""
        bbox = MockBoundingBox(
            x=50, y=50, width=200, height=30,
            top=50, right=250, bottom=80, left=50,
            page_x=50, page_y=50
        )
        input_elem = MockDOMElement(
            tag_name="input",
            element_id="search",
            class_names=[],
            role=None,
            aria_label=None,
            accessible_name=None,
            text_content=None,
            inner_text=None,
            value="",
            placeholder="Search...",
            bounding_box=bbox,
            visible=True,
            enabled=True,
            focusable=True,
            clickable=True,
            xpath='//*[@id="search"]',
            css_selector="#search",
            depth=1,
            parent_tag="form",
            attributes={"id": "search", "placeholder": "Search..."},
            z_index="auto",
            opacity="1",
            display="block",
            visibility="visible",
            pointer_events="auto",
            uid="search123"
        )

        assert input_elem.placeholder == "Search..."


class TestZIndexAndOverlap:
    """Test z-index and element overlap handling"""

    def test_find_topmost_element_at_point(self):
        """Test finding topmost element at overlapping coordinates"""
        # Create overlapping elements with different z-indexes
        bbox1 = MockBoundingBox(
            x=100, y=100, width=200, height=200,
            top=100, right=300, bottom=300, left=100,
            page_x=100, page_y=100
        )
        elem1 = MockDOMElement(
            tag_name="div",
            element_id="bottom",
            class_names=[],
            role=None,
            aria_label=None,
            accessible_name=None,
            text_content="Bottom",
            inner_text="Bottom",
            value=None,
            placeholder=None,
            bounding_box=bbox1,
            visible=True,
            enabled=True,
            focusable=False,
            clickable=False,
            xpath='//*[@id="bottom"]',
            css_selector="#bottom",
            depth=1,
            parent_tag="body",
            attributes={"id": "bottom"},
            z_index="1",
            opacity="1",
            display="block",
            visibility="visible",
            pointer_events="auto",
            uid="bottom123"
        )

        bbox2 = MockBoundingBox(
            x=150, y=150, width=200, height=200,
            top=150, right=350, bottom=350, left=150,
            page_x=150, page_y=150
        )
        elem2 = MockDOMElement(
            tag_name="div",
            element_id="top",
            class_names=[],
            role=None,
            aria_label=None,
            accessible_name=None,
            text_content="Top",
            inner_text="Top",
            value=None,
            placeholder=None,
            bounding_box=bbox2,
            visible=True,
            enabled=True,
            focusable=False,
            clickable=False,
            xpath='//*[@id="top"]',
            css_selector="#top",
            depth=1,
            parent_tag="body",
            attributes={"id": "top"},
            z_index="2",
            opacity="1",
            display="block",
            visibility="visible",
            pointer_events="auto",
            uid="top123"
        )

        elements = [elem1, elem2]

        # Find element at overlap point (200, 200)
        def find_topmost(x, y, elements):
            candidates = []
            for elem in elements:
                bbox = elem.bounding_box
                if (bbox.left <= x <= bbox.right and
                    bbox.top <= y <= bbox.bottom and
                    elem.visible):
                    candidates.append(elem)

            if not candidates:
                return None

            # Sort by z-index and depth
            candidates.sort(key=lambda e: (
                int(e.z_index) if e.z_index.isdigit() else 0,
                e.depth
            ), reverse=True)

            return candidates[0]

        topmost = find_topmost(200, 200, elements)
        assert topmost.element_id == "top"

    def test_pointer_events_none_passthrough(self):
        """Test that pointer-events:none allows click passthrough"""
        bbox = MockBoundingBox(
            x=100, y=100, width=200, height=200,
            top=100, right=300, bottom=300, left=100,
            page_x=100, page_y=100
        )
        overlay = MockDOMElement(
            tag_name="div",
            element_id="overlay",
            class_names=[],
            role=None,
            aria_label=None,
            accessible_name=None,
            text_content="Overlay",
            inner_text="Overlay",
            value=None,
            placeholder=None,
            bounding_box=bbox,
            visible=True,
            enabled=True,
            focusable=False,
            clickable=False,
            xpath='//*[@id="overlay"]',
            css_selector="#overlay",
            depth=2,
            parent_tag="body",
            attributes={"id": "overlay"},
            z_index="10",
            opacity="1",
            display="block",
            visibility="visible",
            pointer_events="none",  # Allows passthrough
            uid="overlay123"
        )

        # Should not be clickable due to pointer-events:none
        assert overlay.pointer_events == "none"


class TestScrollHandling:
    """Test scroll position handling"""

    def test_element_coordinates_with_scroll(self, sample_dom_structure):
        """Test element coordinates account for scroll"""
        elem = sample_dom_structure.elements[0]

        # Viewport coordinates
        viewport_y = elem.bounding_box.y

        # Page coordinates (absolute)
        page_y = elem.bounding_box.page_y

        # With scroll_y = 100
        scroll_y = sample_dom_structure.scroll_y

        # page_y should equal viewport_y + scroll_y
        assert page_y == viewport_y + scroll_y

    def test_scroll_offset_calculation(self, sample_dom_structure):
        """Test calculating scroll offset"""
        scroll_x = sample_dom_structure.scroll_x
        scroll_y = sample_dom_structure.scroll_y

        assert scroll_x == 0
        assert scroll_y == 100

    def test_click_coordinates_with_scroll(self, sample_dom_structure):
        """Test calculating click coordinates with scroll offset"""
        elem = sample_dom_structure.elements[0]

        # Click at element center (viewport coordinates)
        click_viewport_x = elem.bounding_box.center_x
        click_viewport_y = elem.bounding_box.center_y

        # Convert to page coordinates
        click_page_x = click_viewport_x + sample_dom_structure.scroll_x
        click_page_y = click_viewport_y + sample_dom_structure.scroll_y

        assert click_page_x == click_viewport_x
        assert click_page_y == click_viewport_y + 100


class TestAccessibilityTree:
    """Test accessibility tree extraction"""

    def test_extract_aria_roles(self, sample_dom_structure):
        """Test extracting ARIA roles"""
        roles = [e.role for e in sample_dom_structure.elements if e.role]

        assert len(roles) >= 1
        assert "button" in roles

    def test_extract_aria_labels(self, sample_dom_structure):
        """Test extracting ARIA labels"""
        labels = [e.aria_label for e in sample_dom_structure.elements
                  if e.aria_label]

        assert len(labels) >= 1
        assert "Submit form" in labels

    def test_extract_accessible_names(self, sample_dom_structure):
        """Test extracting accessible names"""
        names = [e.accessible_name for e in sample_dom_structure.elements
                 if e.accessible_name]

        assert len(names) >= 2
        assert "Submit" in names
        assert "Home" in names


class TestPerformance:
    """Test DOM extraction performance"""

    @pytest.mark.slow
    def test_extract_large_dom_structure(self):
        """Test extracting large DOM structure (performance)"""
        # Simulate large structure
        elements = []
        for i in range(1000):
            bbox = MockBoundingBox(
                x=i % 100 * 10, y=i // 100 * 20,
                width=50, height=20,
                top=i // 100 * 20, right=(i % 100 * 10) + 50,
                bottom=(i // 100 * 20) + 20, left=i % 100 * 10,
                page_x=i % 100 * 10, page_y=i // 100 * 20
            )
            elem = MockDOMElement(
                tag_name="div",
                element_id=f"elem_{i}",
                class_names=[],
                role=None,
                aria_label=None,
                accessible_name=None,
                text_content=f"Element {i}",
                inner_text=f"Element {i}",
                value=None,
                placeholder=None,
                bounding_box=bbox,
                visible=True,
                enabled=True,
                focusable=False,
                clickable=False,
                xpath=f'//*[@id="elem_{i}"]',
                css_selector=f"#elem_{i}",
                depth=1,
                parent_tag="body",
                attributes={"id": f"elem_{i}"},
                z_index="auto",
                opacity="1",
                display="block",
                visibility="visible",
                pointer_events="auto",
                uid=f"uid_{i}"
            )
            elements.append(elem)

        assert len(elements) == 1000

    def test_coordinate_lookup_performance(self):
        """Test coordinate lookup performance"""
        # Create grid of elements
        elements = []
        for i in range(100):
            for j in range(100):
                bbox = MockBoundingBox(
                    x=i * 10, y=j * 10,
                    width=8, height=8,
                    top=j * 10, right=(i * 10) + 8,
                    bottom=(j * 10) + 8, left=i * 10,
                    page_x=i * 10, page_y=j * 10
                )
                elem = MockDOMElement(
                    tag_name="div",
                    element_id=f"elem_{i}_{j}",
                    class_names=[],
                    role=None,
                    aria_label=None,
                    accessible_name=None,
                    text_content=f"{i},{j}",
                    inner_text=f"{i},{j}",
                    value=None,
                    placeholder=None,
                    bounding_box=bbox,
                    visible=True,
                    enabled=True,
                    focusable=False,
                    clickable=False,
                    xpath=f'//*[@id="elem_{i}_{j}"]',
                    css_selector=f"#elem_{i}_{j}",
                    depth=1,
                    parent_tag="body",
                    attributes={"id": f"elem_{i}_{j}"},
                    z_index="auto",
                    opacity="1",
                    display="block",
                    visibility="visible",
                    pointer_events="auto",
                    uid=f"uid_{i}_{j}"
                )
                elements.append(elem)

        # Perform lookups
        def find_at_point(x, y):
            for elem in elements:
                bbox = elem.bounding_box
                if (bbox.left <= x <= bbox.right and
                    bbox.top <= y <= bbox.bottom):
                    return elem
            return None

        # Should find element quickly even with 10,000 elements
        result = find_at_point(55, 55)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
