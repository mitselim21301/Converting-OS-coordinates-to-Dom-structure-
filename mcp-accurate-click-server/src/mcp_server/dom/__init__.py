#!/usr/bin/env python3
"""
DOM Extraction Module

Production-ready DOM extraction system with coordinate mapping,
caching, and comprehensive element finding strategies.

This module provides:
- DOMStructureExtractor: Extract complete DOM structures with caching
- CoordinateMapper: Map coordinates to elements using multiple strategies
- Data Models: Comprehensive representations of DOM elements and structures
- Performance: Caching, incremental updates, large DOM optimization

Usage:
    from mcp_server.dom import DOMStructureExtractor, CoordinateMapper, ExtractionOptions
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('https://example.com')

        # Extract DOM structure
        options = ExtractionOptions(use_cache=True, cache_ttl=60)
        extractor = DOMStructureExtractor(page, options)
        structure = extractor.extract()

        # Map coordinates to elements
        mapper = CoordinateMapper(structure)
        element = mapper.find_element_at_point(100, 200)

        # Find elements by text
        results = mapper.find_elements_by_text("Submit")

        browser.close()
"""

# Core classes
from .extractor import DOMStructureExtractor, DOMCache
from .mapper import CoordinateMapper, SearchStrategy, SearchResult

# Data models
from .models import (
    # Core models
    DOMElement,
    BoundingBox,
    DOMStructure,
    ViewportInfo,
    DOMStatistics,

    # Configuration
    ExtractionOptions,
    CoordinateType,
)

__version__ = "1.0.0"

__all__ = [
    # Extractors
    "DOMStructureExtractor",
    "DOMCache",

    # Mappers
    "CoordinateMapper",
    "SearchStrategy",
    "SearchResult",

    # Models
    "DOMElement",
    "BoundingBox",
    "DOMStructure",
    "ViewportInfo",
    "DOMStatistics",

    # Configuration
    "ExtractionOptions",
    "CoordinateType",
]


def create_extractor(page, **options):
    """
    Convenience function to create a DOMStructureExtractor.

    Args:
        page: Playwright page object
        **options: Extraction options (passed to ExtractionOptions)

    Returns:
        DOMStructureExtractor instance

    Example:
        extractor = create_extractor(page, use_cache=True, cache_ttl=120)
        structure = extractor.extract()
    """
    extraction_options = ExtractionOptions(**options)
    return DOMStructureExtractor(page, extraction_options)


def create_mapper(page_or_structure):
    """
    Convenience function to create a CoordinateMapper.

    Args:
        page_or_structure: Either a Playwright page or DOMStructure

    Returns:
        CoordinateMapper instance

    Example:
        # From page
        mapper = create_mapper(page)

        # From structure
        structure = extractor.extract()
        mapper = create_mapper(structure)
    """
    # Check if it's a DOMStructure or a Playwright page
    if isinstance(page_or_structure, DOMStructure):
        return CoordinateMapper(page_or_structure)
    else:
        # Assume it's a page, extract structure first
        extractor = DOMStructureExtractor(page_or_structure)
        structure = extractor.extract()
        return CoordinateMapper(structure)


# Module-level configuration
DEFAULT_CACHE_TTL = 60  # seconds
DEFAULT_MAX_CACHE_SIZE = 100
DEFAULT_MAX_TEXT_LENGTH = 500

# Export module info
__author__ = "MCP Accurate Click Server Team"
__license__ = "MIT"
