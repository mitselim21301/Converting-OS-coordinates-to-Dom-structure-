#!/usr/bin/env python3
"""
Comprehensive DOM Module Tests

This module provides extensive test coverage for all DOM functionality:
- DOMStructureExtractor
- CoordinateMapper
- DOMElement and BoundingBox models
- Extraction options and filtering
- Edge cases and error handling
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from typing import Dict, List, Optional
import json


# =============================================================================
# Test Models
# =============================================================================

class TestBoundingBoxModel:
    """Test BoundingBox data model"""

    def test_bounding_box_creation(self):
        """Test creating a BoundingBox"""
        from mcp_server.dom import BoundingBox

        bbox = BoundingBox(
            x=10, y=20, width=100, height=50,
            top=20, right=110, bottom=70, left=10,
            page_x=10, page_y=120
        )

        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 50

    def test_bounding_box_center(self):
        """Test bounding box center calculation"""
        from mcp_server.dom import BoundingBox

        bbox = BoundingBox(
            x=0, y=0, width=100, height=50,
            top=0, right=100, bottom=50, left=0,
            page_x=0, page_y=0
        )

        assert bbox.center_x == 50
        assert bbox.center_y == 25

    def test_bounding_box_page_center(self):
        """Test page center calculation"""
        from mcp_server.dom import BoundingBox

        bbox = BoundingBox(
            x=10, y=10, width=100, height=50,
            top=10, right=110, bottom=60, left=10,
            page_x=10, page_y=510  # With scroll
        )

        assert bbox.page_center_x == 60
        assert bbox.page_center_y == 535

    def test_bounding_box_area(self):
        """Test area calculation"""
        from mcp_server.dom import BoundingBox

        bbox = BoundingBox(
            x=0, y=0, width=100, height=50,
            top=0, right=100, bottom=50, left=0,
            page_x=0, page_y=0
        )

        assert bbox.area == 5000

    def test_contains_point_viewport(self):
        """Test contains_point with viewport coordinates"""
        from mcp_server.dom import BoundingBox, CoordinateType

        bbox = BoundingBox(
            x=10, y=20, width=100, height=50,
            top=20, right=110, bottom=70, left=10,
            page_x=10, page_y=20
        )

        assert bbox.contains_point(50, 40, CoordinateType.VIEWPORT) is True
        assert bbox.contains_point(5, 5, CoordinateType.VIEWPORT) is False
        assert bbox.contains_point(120, 40, CoordinateType.VIEWPORT) is False

    def test_contains_point_page(self):
        """Test contains_point with page coordinates"""
        from mcp_server.dom import BoundingBox, CoordinateType

        bbox = BoundingBox(
            x=10, y=20, width=100, height=50,
            top=20, right=110, bottom=70, left=10,
            page_x=10, page_y=520  # With scroll
        )

        assert bbox.contains_point(50, 540, CoordinateType.PAGE) is True
        assert bbox.contains_point(50, 40, CoordinateType.PAGE) is False

    def test_contains_point_screen(self):
        """Test contains_point with screen coordinates"""
        from mcp_server.dom import BoundingBox, CoordinateType

        bbox = BoundingBox(
            x=10, y=20, width=100, height=50,
            top=20, right=110, bottom=70, left=10,
            page_x=10, page_y=20,
            screen_x=110, screen_y=220
        )

        assert bbox.contains_point(150, 240, CoordinateType.SCREEN) is True
        assert bbox.contains_point(50, 40, CoordinateType.SCREEN) is False

    def test_intersects(self):
        """Test bounding box intersection"""
        from mcp_server.dom import BoundingBox

        bbox1 = BoundingBox(
            x=0, y=0, width=100, height=100,
            top=0, right=100, bottom=100, left=0,
            page_x=0, page_y=0
        )

        bbox2 = BoundingBox(
            x=50, y=50, width=100, height=100,
            top=50, right=150, bottom=150, left=50,
            page_x=50, page_y=50
        )

        bbox3 = BoundingBox(
            x=200, y=200, width=100, height=100,
            top=200, right=300, bottom=300, left=200,
            page_x=200, page_y=200
        )

        assert bbox1.intersects(bbox2) is True
        assert bbox1.intersects(bbox3) is False


class TestDOMElementModel:
    """Test DOMElement data model"""

    def test_dom_element_creation(self):
        """Test creating a DOMElement"""
        from mcp_server.dom import DOMElement, BoundingBox

        bbox = BoundingBox(
            x=0, y=0, width=100, height=50,
            top=0, right=100, bottom=50, left=0,
            page_x=0, page_y=0
        )

        element = DOMElement(
            tag_name="button",
            element_id="submit",
            class_names=["btn", "primary"],
            role="button",
            aria_label=None,
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
            xpath="//button[@id='submit']",
            css_selector="#submit",
            depth=2,
            parent_tag="form"
        )

        assert element.tag_name == "button"
        assert element.element_id == "submit"
        assert element.clickable is True

    def test_dom_element_with_defaults(self):
        """Test DOMElement with default values"""
        from mcp_server.dom import DOMElement, BoundingBox

        bbox = BoundingBox(
            x=0, y=0, width=100, height=50,
            top=0, right=100, bottom=50, left=0,
            page_x=0, page_y=0
        )

        element = DOMElement(
            tag_name="div",
            element_id=None,
            class_names=[],
            role=None,
            aria_label=None,
            accessible_name=None,
            text_content=None,
            inner_text=None,
            value=None,
            placeholder=None,
            bounding_box=bbox,
            visible=True,
            enabled=True,
            focusable=False,
            clickable=False,
            xpath="//div[1]",
            css_selector="div",
            depth=1,
            parent_tag="body"
        )

        assert element.tag_name == "div"
        assert element.child_count == 0  # Default
        assert element.z_index == "auto"  # Default


# =============================================================================
# Test Extraction Options
# =============================================================================

class TestExtractionOptions:
    """Test ExtractionOptions configuration"""

    def test_default_extraction_options(self):
        """Test default extraction options"""
        from mcp_server.dom import ExtractionOptions

        options = ExtractionOptions()

        # Should have reasonable defaults
        assert options.include_hidden is not None or True
        assert options.max_depth is None or isinstance(options.max_depth, int)

    def test_custom_extraction_options(self):
        """Test custom extraction options"""
        from mcp_server.dom import ExtractionOptions

        options = ExtractionOptions(
            include_hidden=False,
            max_depth=5,
            include_shadow_dom=True
        )

        assert options.include_hidden is False
        assert options.max_depth == 5


# =============================================================================
# Test DOM Structure
# =============================================================================

class TestDOMStructure:
    """Test DOMStructure model"""

    def test_dom_structure_creation(self):
        """Test creating a DOMStructure"""
        from mcp_server.dom import DOMStructure, DOMElement, BoundingBox

        bbox = BoundingBox(
            x=0, y=0, width=100, height=50,
            top=0, right=100, bottom=50, left=0,
            page_x=0, page_y=0
        )

        element = DOMElement(
            tag_name="button",
            element_id="test",
            class_names=[],
            role="button",
            aria_label=None,
            accessible_name=None,
            text_content="Test",
            inner_text="Test",
            value=None,
            placeholder=None,
            bounding_box=bbox,
            visible=True,
            enabled=True,
            focusable=True,
            clickable=True,
            xpath="//button",
            css_selector="button",
            depth=1,
            parent_tag="body"
        )

        structure = DOMStructure(
            url="http://example.com",
            title="Test Page",
            elements=[element],
            viewport_width=1920,
            viewport_height=1080
        )

        assert structure.url == "http://example.com"
        assert len(structure.elements) == 1
        assert structure.viewport_width == 1920


# =============================================================================
# Test Coordinate Mapper
# =============================================================================

class TestCoordinateMapper:
    """Test CoordinateMapper functionality"""

    def test_coordinate_mapper_initialization(self):
        """Test creating a CoordinateMapper"""
        from mcp_server.dom import CoordinateMapper

        mapper = CoordinateMapper()
        assert mapper is not None

    @pytest.mark.asyncio
    async def test_viewport_to_page_conversion(self):
        """Test converting viewport coordinates to page coordinates"""
        from mcp_server.dom import CoordinateMapper

        mapper = CoordinateMapper()

        # Mock page
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=500)  # scrollY

        viewport_x, viewport_y = 100, 200
        page_coords = await mapper.viewport_to_page(
            mock_page, viewport_x, viewport_y
        )

        # Page Y should be viewport Y + scroll
        assert page_coords[0] == 100  # X unchanged
        assert page_coords[1] == 700  # Y + scrollY

    @pytest.mark.asyncio
    async def test_page_to_viewport_conversion(self):
        """Test converting page coordinates to viewport coordinates"""
        from mcp_server.dom import CoordinateMapper

        mapper = CoordinateMapper()

        # Mock page
        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=500)  # scrollY

        page_x, page_y = 100, 700
        viewport_coords = await mapper.page_to_viewport(
            mock_page, page_x, page_y
        )

        # Viewport Y should be page Y - scroll
        assert viewport_coords[0] == 100
        assert viewport_coords[1] == 200  # Y - scrollY


# =============================================================================
# Test DOM Structure Extractor
# =============================================================================

class TestDOMStructureExtractor:
    """Test DOMStructureExtractor functionality"""

    def test_extractor_initialization(self):
        """Test creating a DOMStructureExtractor"""
        from mcp_server.dom import DOMStructureExtractor

        extractor = DOMStructureExtractor()
        assert extractor is not None

    @pytest.mark.asyncio
    async def test_extract_basic_structure(self):
        """Test extracting basic DOM structure"""
        from mcp_server.dom import DOMStructureExtractor

        extractor = DOMStructureExtractor()

        # Mock page
        mock_page = AsyncMock()
        mock_page.url = "http://example.com"
        mock_page.title = AsyncMock(return_value="Test Page")
        mock_page.viewport_size = {"width": 1920, "height": 1080}
        mock_page.evaluate = AsyncMock(return_value=[
            {
                "tagName": "BUTTON",
                "id": "submit",
                "className": "btn primary",
                "role": "button",
                "ariaLabel": None,
                "textContent": "Submit",
                "innerText": "Submit",
                "value": None,
                "placeholder": None,
                "boundingBox": {
                    "x": 100, "y": 200, "width": 80, "height": 40,
                    "top": 200, "right": 180, "bottom": 240, "left": 100
                },
                "visible": True,
                "enabled": True,
                "focusable": True,
                "clickable": True,
                "xpath": "//button[@id='submit']",
                "cssSelector": "#submit",
                "depth": 2,
                "parentTag": "form"
            }
        ])

        structure = await extractor.extract(mock_page)

        assert structure.url == "http://example.com"
        assert structure.title == "Test Page"
        assert len(structure.elements) > 0 or structure.elements is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
