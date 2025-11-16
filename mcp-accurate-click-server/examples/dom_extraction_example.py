#!/usr/bin/env python3
"""
DOM Extraction System - Comprehensive Example

Demonstrates the complete DOM extraction system with all features:
- DOM structure extraction with caching
- Coordinate mapping with multiple strategies
- Element finding by various criteria
- Accessibility analysis
- Performance optimization
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from playwright.sync_api import sync_playwright
from mcp_server.dom import (
    DOMStructureExtractor,
    CoordinateMapper,
    ExtractionOptions,
    SearchStrategy,
    create_extractor,
    create_mapper
)
from mcp_server.dom.utils import (
    save_structure_to_json,
    get_clickable_regions_summary,
    validate_dom_structure,
    get_accessibility_summary,
    export_clickable_coordinates
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_basic_extraction():
    """Example 1: Basic DOM extraction"""
    print("\n" + "="*80)
    print("Example 1: Basic DOM Extraction")
    print("="*80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')

        # Create extractor with default options
        extractor = DOMStructureExtractor(page)
        structure = extractor.extract()

        # Print summary
        print(f"\nURL: {structure.url}")
        print(f"Title: {structure.title}")
        print(f"Total elements: {structure.statistics.total_elements}")
        print(f"Visible elements: {structure.statistics.visible_elements}")
        print(f"Clickable elements: {structure.statistics.clickable_elements}")
        print(f"Extraction time: {structure.statistics.extraction_time:.2f}s")

        browser.close()


def example_with_caching():
    """Example 2: Extraction with caching"""
    print("\n" + "="*80)
    print("Example 2: DOM Extraction with Caching")
    print("="*80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')

        # Create extractor with caching enabled
        options = ExtractionOptions(
            use_cache=True,
            cache_ttl=120,  # 2 minutes
            include_invisible=False
        )
        extractor = DOMStructureExtractor(page, options)

        # First extraction (cache miss)
        print("\n1st extraction (cache miss):")
        structure1 = extractor.extract()
        print(f"   Time: {structure1.statistics.extraction_time:.3f}s")
        print(f"   Cached: {structure1.is_cached}")

        # Second extraction (cache hit)
        print("\n2nd extraction (cache hit):")
        structure2 = extractor.extract()
        print(f"   Time: {structure2.statistics.extraction_time:.3f}s")
        print(f"   Cached: {structure2.is_cached}")

        # Get cache statistics
        cache_stats = extractor.get_cache_stats()
        if cache_stats:
            print(f"\nCache Statistics:")
            print(f"   Hit rate: {cache_stats['hit_rate']:.1%}")
            print(f"   Hits: {cache_stats['hits']}")
            print(f"   Misses: {cache_stats['misses']}")
            print(f"   Cache size: {cache_stats['size']}/{cache_stats['max_size']}")

        browser.close()


def example_coordinate_mapping():
    """Example 3: Coordinate to element mapping"""
    print("\n" + "="*80)
    print("Example 3: Coordinate to Element Mapping")
    print("="*80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')

        # Extract and create mapper
        extractor = DOMStructureExtractor(page)
        structure = extractor.extract()
        mapper = CoordinateMapper(structure)

        # Find element at specific coordinates
        x, y = 400, 300
        print(f"\nFinding element at ({x}, {y}):")

        element = mapper.find_element_at_point(x, y)
        if element:
            print(f"   Found: <{element.tag_name}>")
            print(f"   ID: {element.element_id or 'none'}")
            print(f"   Classes: {', '.join(element.class_names) or 'none'}")
            print(f"   Text: {(element.text_content or '')[:50]}")
            print(f"   Clickable: {element.clickable}")
            print(f"   Position: ({element.bounding_box.center_x:.0f}, {element.bounding_box.center_y:.0f})")
        else:
            print("   No element found")

        # Find nearest clickable element
        print(f"\nFinding nearest clickable to ({x}, {y}):")
        element = mapper.find_element_at_point(
            x, y,
            strategies=[SearchStrategy.NEAREST_CLICKABLE]
        )
        if element:
            print(f"   Found: <{element.tag_name}>")
            print(f"   Text: {(element.text_content or '')[:50]}")

        browser.close()


def example_text_search():
    """Example 4: Finding elements by text"""
    print("\n" + "="*80)
    print("Example 4: Finding Elements by Text")
    print("="*80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')

        extractor = DOMStructureExtractor(page)
        structure = extractor.extract()
        mapper = CoordinateMapper(structure)

        # Search for text
        search_text = "Example"
        print(f"\nSearching for text: '{search_text}'")

        results = mapper.find_elements_by_text(search_text, exact=False)
        print(f"Found {len(results)} matches:")

        for i, result in enumerate(results[:5], 1):
            elem = result.element
            print(f"\n{i}. <{elem.tag_name}> (confidence: {result.confidence:.2f})")
            print(f"   Text: {(elem.text_content or '')[:60]}")
            print(f"   Position: ({elem.bounding_box.center_x:.0f}, {elem.bounding_box.center_y:.0f})")

        # Find clickable elements near text
        print(f"\n\nFinding clickable elements near '{search_text}':")
        clickable_results = mapper.find_clickable_near_text(search_text, max_distance=100)

        print(f"Found {len(clickable_results)} clickable elements:")
        for i, result in enumerate(clickable_results[:3], 1):
            elem = result.element
            print(f"\n{i}. <{elem.tag_name}> (confidence: {result.confidence:.2f}, distance: {result.distance:.1f}px)")
            print(f"   ID: {elem.element_id or 'none'}")
            print(f"   Text: {(elem.text_content or '')[:50]}")

        browser.close()


def example_accessibility_search():
    """Example 5: Finding elements by accessibility features"""
    print("\n" + "="*80)
    print("Example 5: Accessibility-based Search")
    print("="*80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')

        extractor = DOMStructureExtractor(page)
        structure = extractor.extract()
        mapper = CoordinateMapper(structure)

        # Find elements by role
        print("\nSearching for buttons (by role):")
        button_results = mapper.find_elements_by_role('button')
        print(f"Found {len(button_results)} button elements")

        for i, result in enumerate(button_results[:5], 1):
            elem = result.element
            print(f"\n{i}. <{elem.tag_name}> (confidence: {result.confidence:.2f})")
            print(f"   Accessible name: {elem.accessible_name or 'none'}")
            print(f"   ARIA label: {elem.aria_label or 'none'}")

        # Get accessibility summary
        print("\n\nAccessibility Summary:")
        acc_summary = get_accessibility_summary(structure)
        print(f"   Interactive elements: {acc_summary['total_interactive']}")
        print(f"   With labels: {acc_summary['with_accessible_labels']} ({acc_summary['label_coverage_percent']:.1f}%)")
        print(f"   With roles: {acc_summary['with_roles']} ({acc_summary['role_coverage_percent']:.1f}%)")
        print(f"   Accessibility score: {acc_summary['accessibility_score']:.1f}/100")

        browser.close()


def example_advanced_filtering():
    """Example 6: Advanced filtering options"""
    print("\n" + "="*80)
    print("Example 6: Advanced Filtering")
    print("="*80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')

        # Extract only specific tags
        options = ExtractionOptions(
            tag_filter=['a', 'button', 'input'],
            include_invisible=False,
            extract_aria=True
        )
        extractor = DOMStructureExtractor(page, options)
        structure = extractor.extract()

        print(f"\nFiltered extraction (links, buttons, inputs only):")
        print(f"   Total elements: {structure.statistics.total_elements}")

        # Count by tag
        by_tag = {}
        for elem in structure.elements:
            by_tag[elem.tag_name] = by_tag.get(elem.tag_name, 0) + 1

        print(f"\n   Elements by tag:")
        for tag, count in sorted(by_tag.items()):
            print(f"      {tag}: {count}")

        browser.close()


def example_region_search():
    """Example 7: Finding elements in a specific region"""
    print("\n" + "="*80)
    print("Example 7: Region-based Search")
    print("="*80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')

        extractor = DOMStructureExtractor(page)
        structure = extractor.extract()
        mapper = CoordinateMapper(structure)

        # Define a region (top-left quarter of viewport)
        viewport_width = structure.viewport.width
        viewport_height = structure.viewport.height

        left = 0
        top = 0
        right = viewport_width // 2
        bottom = viewport_height // 2

        print(f"\nSearching in region: ({left}, {top}) to ({right}, {bottom})")

        elements = mapper.find_elements_in_region(
            left, top, right, bottom,
            element_filter=lambda e: e.clickable
        )

        print(f"Found {len(elements)} clickable elements in region:")
        for i, elem in enumerate(elements[:5], 1):
            print(f"\n{i}. <{elem.tag_name}>")
            print(f"   Position: ({elem.bounding_box.center_x:.0f}, {elem.bounding_box.center_y:.0f})")
            print(f"   Size: {elem.bounding_box.width:.0f}x{elem.bounding_box.height:.0f}")

        browser.close()


def example_validation_and_export():
    """Example 8: Validation and export"""
    print("\n" + "="*80)
    print("Example 8: Validation and Export")
    print("="*80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')

        extractor = DOMStructureExtractor(page)
        structure = extractor.extract()

        # Validate structure
        print("\nValidating DOM structure:")
        validation = validate_dom_structure(structure)

        print(f"   Valid: {validation['valid']}")
        print(f"   Element count: {validation['element_count']}")
        print(f"   Visible count: {validation['visible_count']}")
        print(f"   Clickable count: {validation['clickable_count']}")

        if validation['issues']:
            print(f"\n   Issues:")
            for issue in validation['issues']:
                print(f"      - {issue}")

        if validation['warnings']:
            print(f"\n   Warnings:")
            for warning in validation['warnings']:
                print(f"      - {warning}")

        # Get clickable regions summary
        print("\n\nClickable Regions Summary:")
        clickable_summary = get_clickable_regions_summary(structure)
        print(f"   Total clickable: {clickable_summary['total_clickable']}")
        print(f"   Viewport coverage: {clickable_summary['viewport_coverage_percent']:.1f}%")
        print(f"\n   By tag:")
        for tag, count in sorted(clickable_summary['by_tag'].items()):
            print(f"      {tag}: {count}")

        # Export to files
        output_dir = Path('/tmp/dom_extraction_example')
        output_dir.mkdir(exist_ok=True)

        # Export structure as JSON
        json_file = output_dir / 'structure.json'
        if save_structure_to_json(structure, str(json_file)):
            print(f"\n✓ Exported structure to {json_file}")

        # Export clickable coordinates as CSV
        csv_file = output_dir / 'clickable_coords.csv'
        if export_clickable_coordinates(structure, str(csv_file)):
            print(f"✓ Exported clickable coordinates to {csv_file}")

        browser.close()


def example_performance_optimization():
    """Example 9: Performance optimization for large DOMs"""
    print("\n" + "="*80)
    print("Example 9: Performance Optimization")
    print("="*80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to a page with many elements
        page.goto('https://news.ycombinator.com')
        page.wait_for_load_state('networkidle')

        # Optimized options for large DOMs
        options = ExtractionOptions(
            include_invisible=False,          # Skip invisible elements
            max_text_length=200,               # Limit text content length
            max_depth=15,                      # Limit depth to avoid deep nesting
            use_cache=True,                    # Enable caching
            cache_ttl=300,                     # 5 minutes
            batch_size=100                     # Process in batches
        )

        extractor = DOMStructureExtractor(page, options)

        # Measure extraction time
        import time
        start = time.time()
        structure = extractor.extract()
        elapsed = time.time() - start

        print(f"\nPerformance metrics:")
        print(f"   Total elements: {structure.statistics.total_elements}")
        print(f"   Extraction time: {elapsed:.2f}s")
        print(f"   Element density: {structure.statistics.element_density:.4f} elements/px²")
        print(f"   Elements/second: {structure.statistics.total_elements / elapsed:.0f}")

        browser.close()


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print(" DOM EXTRACTION SYSTEM - COMPREHENSIVE EXAMPLES")
    print("="*80)

    try:
        # Run examples
        example_basic_extraction()
        example_with_caching()
        example_coordinate_mapping()
        example_text_search()
        example_accessibility_search()
        example_advanced_filtering()
        example_region_search()
        example_validation_and_export()
        example_performance_optimization()

        print("\n" + "="*80)
        print(" ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")

    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
