#!/usr/bin/env python3
"""
DOM Utilities

Helper functions for DOM extraction and analysis.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import DOMStructure, DOMElement, BoundingBox

logger = logging.getLogger(__name__)


def save_structure_to_json(structure: DOMStructure, filepath: str) -> bool:
    """
    Save DOM structure to JSON file.

    Args:
        structure: DOM structure to save
        filepath: Path to output file

    Returns:
        True if successful
    """
    try:
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(structure.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Saved DOM structure to {filepath}")
        return True

    except Exception as e:
        logger.error(f"Failed to save structure: {e}")
        return False


def load_structure_from_json(filepath: str) -> Optional[DOMStructure]:
    """
    Load DOM structure from JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        DOMStructure if successful, None otherwise
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # TODO: Implement full deserialization
        logger.info(f"Loaded DOM structure from {filepath}")
        return None  # Placeholder

    except Exception as e:
        logger.error(f"Failed to load structure: {e}")
        return None


def filter_elements_by_visibility(
    elements: List[DOMElement],
    min_width: float = 1.0,
    min_height: float = 1.0,
    min_opacity: float = 0.1
) -> List[DOMElement]:
    """
    Filter elements by visibility criteria.

    Args:
        elements: List of elements to filter
        min_width: Minimum width in pixels
        min_height: Minimum height in pixels
        min_opacity: Minimum opacity value

    Returns:
        Filtered list of elements
    """
    filtered = []

    for elem in elements:
        if not elem.visible:
            continue

        bbox = elem.bounding_box
        if bbox.width < min_width or bbox.height < min_height:
            continue

        try:
            opacity = float(elem.opacity)
            if opacity < min_opacity:
                continue
        except ValueError:
            pass

        filtered.append(elem)

    return filtered


def get_element_hierarchy_string(element: DOMElement) -> str:
    """
    Get human-readable element hierarchy string.

    Args:
        element: Element to describe

    Returns:
        Hierarchy string (e.g., "html > body > div.container > button#submit")
    """
    # Parse CSS selector for hierarchy
    return element.css_selector


def calculate_element_overlap(elem1: DOMElement, elem2: DOMElement) -> float:
    """
    Calculate overlap ratio between two elements.

    Args:
        elem1: First element
        elem2: Second element

    Returns:
        Overlap ratio (0.0 to 1.0)
    """
    bbox1 = elem1.bounding_box
    bbox2 = elem2.bounding_box

    intersection = bbox1.intersection_area(bbox2)
    union = bbox1.area + bbox2.area - intersection

    return intersection / union if union > 0 else 0.0


def find_element_container(
    element: DOMElement,
    all_elements: List[DOMElement]
) -> Optional[DOMElement]:
    """
    Find the smallest element that contains the target element.

    Args:
        element: Target element
        all_elements: List of all elements

    Returns:
        Container element or None
    """
    candidates = []
    target_bbox = element.bounding_box

    for other in all_elements:
        if other.uid == element.uid:
            continue

        if other.depth >= element.depth:
            continue

        # Check if other contains target
        other_bbox = other.bounding_box
        if (other_bbox.left <= target_bbox.left and
            other_bbox.right >= target_bbox.right and
            other_bbox.top <= target_bbox.top and
            other_bbox.bottom >= target_bbox.bottom):
            candidates.append(other)

    if not candidates:
        return None

    # Return smallest container (highest depth)
    return max(candidates, key=lambda e: e.depth)


def get_clickable_regions_summary(structure: DOMStructure) -> Dict[str, Any]:
    """
    Get summary of clickable regions in the DOM.

    Args:
        structure: DOM structure

    Returns:
        Dictionary with clickable region statistics
    """
    clickable = structure.clickable_elements

    by_tag = {}
    by_role = {}
    total_area = 0

    for elem in clickable:
        # Count by tag
        tag = elem.tag_name
        by_tag[tag] = by_tag.get(tag, 0) + 1

        # Count by role
        role = elem.role or 'none'
        by_role[role] = by_role.get(role, 0) + 1

        # Sum area
        total_area += elem.bounding_box.area

    viewport_area = structure.viewport.width * structure.viewport.height
    coverage = (total_area / viewport_area * 100) if viewport_area > 0 else 0

    return {
        'total_clickable': len(clickable),
        'by_tag': by_tag,
        'by_role': by_role,
        'total_area': total_area,
        'viewport_coverage_percent': coverage
    }


def get_text_density_map(
    structure: DOMStructure,
    grid_size: int = 50
) -> List[List[int]]:
    """
    Create a 2D grid showing text density across the viewport.

    Args:
        structure: DOM structure
        grid_size: Size of grid cells in pixels

    Returns:
        2D list of text element counts per cell
    """
    viewport_width = structure.viewport.width
    viewport_height = structure.viewport.height

    cols = (viewport_width // grid_size) + 1
    rows = (viewport_height // grid_size) + 1

    grid = [[0 for _ in range(cols)] for _ in range(rows)]

    for elem in structure.text_elements:
        if not elem.visible:
            continue

        bbox = elem.bounding_box
        # Find grid cells this element overlaps
        min_col = max(0, int(bbox.left // grid_size))
        max_col = min(cols - 1, int(bbox.right // grid_size))
        min_row = max(0, int(bbox.top // grid_size))
        max_row = min(rows - 1, int(bbox.bottom // grid_size))

        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                grid[row][col] += 1

    return grid


def validate_dom_structure(structure: DOMStructure) -> Dict[str, Any]:
    """
    Validate DOM structure and return diagnostics.

    Args:
        structure: DOM structure to validate

    Returns:
        Dictionary with validation results
    """
    issues = []
    warnings = []

    # Check for reasonable element count
    total = structure.statistics.total_elements
    if total == 0:
        issues.append("No elements extracted")
    elif total > 10000:
        warnings.append(f"Very large DOM: {total} elements")

    # Check viewport dimensions
    if structure.viewport.width == 0 or structure.viewport.height == 0:
        issues.append("Invalid viewport dimensions")

    # Check for duplicate UIDs
    uids = [e.uid for e in structure.elements]
    if len(uids) != len(set(uids)):
        issues.append("Duplicate element UIDs detected")

    # Check bounding boxes
    invalid_bbox_count = 0
    for elem in structure.elements:
        bbox = elem.bounding_box
        if bbox.width < 0 or bbox.height < 0:
            invalid_bbox_count += 1

    if invalid_bbox_count > 0:
        issues.append(f"{invalid_bbox_count} elements with invalid bounding boxes")

    # Check visibility consistency
    visible_count = len([e for e in structure.elements if e.visible])
    if visible_count != structure.statistics.visible_elements:
        warnings.append("Visible element count mismatch")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'element_count': total,
        'visible_count': visible_count,
        'clickable_count': structure.statistics.clickable_elements
    }


def get_accessibility_summary(structure: DOMStructure) -> Dict[str, Any]:
    """
    Get accessibility summary of the DOM.

    Args:
        structure: DOM structure

    Returns:
        Accessibility metrics and findings
    """
    total_interactive = len(structure.interactive_elements)
    with_labels = 0
    with_roles = 0
    missing_alt = []

    for elem in structure.interactive_elements:
        if elem.accessible_name or elem.aria_label:
            with_labels += 1

        if elem.role:
            with_roles += 1

        # Check for images without alt text
        if elem.tag_name == 'img' and 'alt' not in elem.attributes:
            missing_alt.append(elem.uid)

    label_coverage = (with_labels / total_interactive * 100) if total_interactive > 0 else 0
    role_coverage = (with_roles / total_interactive * 100) if total_interactive > 0 else 0

    return {
        'total_interactive': total_interactive,
        'with_accessible_labels': with_labels,
        'with_roles': with_roles,
        'label_coverage_percent': label_coverage,
        'role_coverage_percent': role_coverage,
        'images_missing_alt': len(missing_alt),
        'accessibility_score': (label_coverage + role_coverage) / 2
    }


def export_clickable_coordinates(
    structure: DOMStructure,
    output_file: str
) -> bool:
    """
    Export clickable element coordinates to CSV.

    Args:
        structure: DOM structure
        output_file: Path to output CSV file

    Returns:
        True if successful
    """
    try:
        import csv

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'UID', 'Tag', 'ID', 'Role', 'Text',
                'Center_X', 'Center_Y', 'Width', 'Height',
                'Clickable', 'Visible'
            ])

            for elem in structure.clickable_elements:
                writer.writerow([
                    elem.uid,
                    elem.tag_name,
                    elem.element_id or '',
                    elem.role or '',
                    (elem.text_content or '')[:50],
                    round(elem.bounding_box.center_x, 2),
                    round(elem.bounding_box.center_y, 2),
                    round(elem.bounding_box.width, 2),
                    round(elem.bounding_box.height, 2),
                    elem.clickable,
                    elem.visible
                ])

        logger.info(f"Exported clickable coordinates to {output_file}")
        return True

    except Exception as e:
        logger.error(f"Failed to export coordinates: {e}")
        return False


def create_element_selector_suggestions(element: DOMElement) -> List[str]:
    """
    Generate various selector suggestions for an element.

    Args:
        element: Element to create selectors for

    Returns:
        List of selector strings
    """
    selectors = []

    # ID selector
    if element.element_id:
        selectors.append(f"#{element.element_id}")

    # Class selectors
    if element.class_names:
        selectors.append(f"{element.tag_name}.{'.'.join(element.class_names[:2])}")
        selectors.append(f".{element.class_names[0]}")

    # Role selector
    if element.role:
        selectors.append(f"[role='{element.role}']")

    # Aria label selector
    if element.aria_label:
        selectors.append(f"[aria-label='{element.aria_label}']")

    # XPath
    selectors.append(element.xpath)

    # CSS selector
    selectors.append(element.css_selector)

    return selectors
