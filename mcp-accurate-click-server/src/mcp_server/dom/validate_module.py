#!/usr/bin/env python3
"""
Module Validation Script

Quick validation to ensure all imports work and basic structure is sound.
"""

import sys
from pathlib import Path

def validate_imports():
    """Validate that all imports work correctly"""
    print("Validating DOM module imports...")

    try:
        # Core imports
        from mcp_server.dom import (
            DOMStructureExtractor,
            CoordinateMapper,
            ExtractionOptions,
            DOMElement,
            BoundingBox,
            DOMStructure,
            ViewportInfo,
            DOMStatistics,
            CoordinateType,
            SearchStrategy,
            SearchResult,
            create_extractor,
            create_mapper
        )
        print("  ✓ Core imports successful")

        # Model imports
        from mcp_server.dom.models import (
            BoundingBox,
            DOMElement,
            DOMStructure,
            ViewportInfo,
            DOMStatistics,
            ExtractionOptions,
            CoordinateType
        )
        print("  ✓ Model imports successful")

        # Extractor imports
        from mcp_server.dom.extractor import (
            DOMStructureExtractor,
            DOMCache,
            CacheEntry
        )
        print("  ✓ Extractor imports successful")

        # Mapper imports
        from mcp_server.dom.mapper import (
            CoordinateMapper,
            SearchStrategy,
            SearchResult
        )
        print("  ✓ Mapper imports successful")

        # Utils imports
        from mcp_server.dom.utils import (
            save_structure_to_json,
            get_clickable_regions_summary,
            validate_dom_structure,
            get_accessibility_summary
        )
        print("  ✓ Utils imports successful")

        return True

    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_models():
    """Validate that models can be instantiated"""
    print("\nValidating model instantiation...")

    try:
        from mcp_server.dom.models import (
            BoundingBox,
            DOMElement,
            ExtractionOptions,
            CoordinateType
        )

        # Create BoundingBox
        bbox = BoundingBox(
            x=10, y=20, width=100, height=50,
            top=20, right=110, bottom=70, left=10,
            page_x=10, page_y=20
        )
        assert bbox.center_x == 60
        assert bbox.center_y == 45
        assert bbox.area == 5000
        print("  ✓ BoundingBox working")

        # Create DOMElement
        element = DOMElement(
            tag_name="button",
            element_id="submit-btn",
            class_names=["btn", "primary"],
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
            xpath="/html/body/button",
            css_selector="button#submit-btn",
            depth=3,
            parent_tag="div",
            attributes={"id": "submit-btn", "type": "submit"}
        )
        assert element.is_interactive
        assert element.has_text
        assert element.uid  # UID should be auto-generated
        print("  ✓ DOMElement working")

        # Create ExtractionOptions
        options = ExtractionOptions(
            use_cache=True,
            cache_ttl=60,
            include_invisible=False
        )
        assert options.use_cache
        assert options.cache_ttl == 60
        print("  ✓ ExtractionOptions working")

        # Test CoordinateType enum
        assert CoordinateType.VIEWPORT.value == "viewport"
        assert CoordinateType.PAGE.value == "page"
        print("  ✓ CoordinateType enum working")

        return True

    except Exception as e:
        print(f"  ✗ Model validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_cache():
    """Validate cache functionality"""
    print("\nValidating cache system...")

    try:
        from mcp_server.dom.extractor import DOMCache
        from mcp_server.dom.models import DOMStructure, ViewportInfo

        # Create cache
        cache = DOMCache(default_ttl=60, max_size=10)

        # Create mock structure
        viewport = ViewportInfo(
            width=1920, height=1080,
            device_pixel_ratio=1.0,
            scroll_x=0, scroll_y=0,
            page_width=1920, page_height=2000
        )

        structure = DOMStructure(
            url="https://example.com",
            title="Example",
            timestamp=123456.0,
            viewport=viewport,
            elements=[]
        )

        # Test cache operations
        key = cache._generate_key("https://example.com", 1920, 1080, 0, 0)
        assert key
        print("  ✓ Cache key generation working")

        # Set and get
        cache.set(key, structure)
        cached = cache.get(key)
        assert cached is not None
        assert cached.is_cached
        print("  ✓ Cache set/get working")

        # Test hit rate
        cache.get("nonexistent")  # Miss
        hit_rate = cache.hit_rate
        assert 0.0 <= hit_rate <= 1.0
        print("  ✓ Cache statistics working")

        # Test invalidation
        cache.invalidate(key)
        cached = cache.get(key)
        assert cached is None
        print("  ✓ Cache invalidation working")

        return True

    except Exception as e:
        print(f"  ✗ Cache validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_mapper_logic():
    """Validate mapper logic without Playwright"""
    print("\nValidating mapper logic...")

    try:
        from mcp_server.dom.models import (
            DOMStructure, DOMElement, BoundingBox,
            ViewportInfo, CoordinateType
        )
        from mcp_server.dom.mapper import CoordinateMapper, SearchStrategy

        # Create test elements
        bbox1 = BoundingBox(
            x=100, y=100, width=200, height=100,
            top=100, right=300, bottom=200, left=100,
            page_x=100, page_y=100
        )

        elem1 = DOMElement(
            tag_name="button",
            element_id="btn1",
            class_names=["btn"],
            role="button",
            aria_label=None,
            accessible_name="Click me",
            text_content="Click me",
            inner_text="Click me",
            value=None,
            placeholder=None,
            bounding_box=bbox1,
            visible=True,
            enabled=True,
            focusable=True,
            clickable=True,
            xpath="/html/body/button",
            css_selector="button#btn1",
            depth=2,
            parent_tag="div",
            attributes={}
        )

        # Create structure
        viewport = ViewportInfo(
            width=1920, height=1080,
            device_pixel_ratio=1.0,
            scroll_x=0, scroll_y=0,
            page_width=1920, page_height=2000
        )

        structure = DOMStructure(
            url="https://example.com",
            title="Test",
            timestamp=123456.0,
            viewport=viewport,
            elements=[elem1]
        )

        # Create mapper
        mapper = CoordinateMapper(structure)
        print("  ✓ Mapper initialization working")

        # Test point finding
        element = mapper.find_element_at_point(150, 150)
        assert element is not None
        assert element.element_id == "btn1"
        print("  ✓ Point-based finding working")

        # Test text search
        results = mapper.find_elements_by_text("Click")
        assert len(results) > 0
        assert results[0].element.element_id == "btn1"
        print("  ✓ Text search working")

        # Test role search
        results = mapper.find_elements_by_role("button")
        assert len(results) > 0
        print("  ✓ Role search working")

        # Test coordinate conversion
        vx, vy = mapper._convert_to_viewport(100, 100, CoordinateType.VIEWPORT)
        assert vx == 100 and vy == 100
        print("  ✓ Coordinate conversion working")

        # Test distance calculation
        dist = mapper._calculate_distance(0, 0, 3, 4)
        assert dist == 5.0
        print("  ✓ Distance calculation working")

        return True

    except Exception as e:
        print(f"  ✗ Mapper validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validations"""
    print("="*70)
    print("DOM Module Validation")
    print("="*70)

    results = []

    # Run validations
    results.append(("Imports", validate_imports()))
    results.append(("Models", validate_models()))
    results.append(("Cache", validate_cache()))
    results.append(("Mapper", validate_mapper_logic()))

    # Print summary
    print("\n" + "="*70)
    print("Validation Summary")
    print("="*70)

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{name:20s} {status}")

    all_passed = all(success for _, success in results)

    print("="*70)
    if all_passed:
        print("✓ ALL VALIDATIONS PASSED")
        print("="*70)
        return 0
    else:
        print("✗ SOME VALIDATIONS FAILED")
        print("="*70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
