#!/usr/bin/env python3
"""
Coordinate Mapper

Maps between coordinates and DOM elements using multiple strategies
for robust element location and interaction.
"""

import logging
from typing import List, Optional, Tuple, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

from .models import DOMElement, DOMStructure, BoundingBox, CoordinateType

logger = logging.getLogger(__name__)


class SearchStrategy(Enum):
    """Element search strategies"""
    POINT_INTERSECTION = "point_intersection"  # Elements containing point
    NEAREST_CLICKABLE = "nearest_clickable"    # Nearest clickable element
    TEXT_MATCH = "text_match"                  # Text content matching
    ACCESSIBILITY = "accessibility"            # Accessibility tree search
    VISUAL_PROXIMITY = "visual_proximity"      # Visual distance-based
    Z_INDEX_PRIORITY = "z_index_priority"      # Highest z-index first


@dataclass
class SearchResult:
    """Result from element search"""
    element: DOMElement
    confidence: float  # 0.0 to 1.0
    strategy: SearchStrategy
    distance: Optional[float] = None  # Distance from target point
    match_score: Optional[float] = None  # Text/attribute match score

    def __lt__(self, other):
        """Compare by confidence for sorting"""
        return self.confidence < other.confidence


class CoordinateMapper:
    """
    Map between coordinates and DOM elements using multiple strategies.

    Provides comprehensive element finding capabilities including:
    - Point-based intersection
    - Text-based searching
    - Accessibility tree navigation
    - Proximity-based finding
    - Fuzzy matching with confidence scores
    """

    def __init__(self, dom_structure: DOMStructure):
        """
        Initialize mapper with DOM structure.

        Args:
            dom_structure: Extracted DOM structure
        """
        self.structure = dom_structure
        self._build_spatial_index()

    def _build_spatial_index(self):
        """Build spatial index for faster coordinate lookups"""
        # Simple grid-based spatial index
        self._spatial_grid: Dict[Tuple[int, int], List[DOMElement]] = {}
        grid_size = 100  # pixels

        for element in self.structure.elements:
            if not element.visible:
                continue

            bbox = element.bounding_box
            # Calculate grid cells this element overlaps
            min_grid_x = int(bbox.left // grid_size)
            max_grid_x = int(bbox.right // grid_size)
            min_grid_y = int(bbox.top // grid_size)
            max_grid_y = int(bbox.bottom // grid_size)

            for gx in range(min_grid_x, max_grid_x + 1):
                for gy in range(min_grid_y, max_grid_y + 1):
                    grid_key = (gx, gy)
                    if grid_key not in self._spatial_grid:
                        self._spatial_grid[grid_key] = []
                    self._spatial_grid[grid_key].append(element)

        logger.debug(f"Built spatial index with {len(self._spatial_grid)} cells")

    def find_element_at_point(
        self,
        x: float,
        y: float,
        coordinate_type: CoordinateType = CoordinateType.VIEWPORT,
        strategies: Optional[List[SearchStrategy]] = None
    ) -> Optional[DOMElement]:
        """
        Find DOM element at specified coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            coordinate_type: Coordinate system type
            strategies: Search strategies to use (default: all)

        Returns:
            DOMElement if found, None otherwise
        """
        strategies = strategies or [SearchStrategy.POINT_INTERSECTION,
                                   SearchStrategy.Z_INDEX_PRIORITY]

        results = []

        for strategy in strategies:
            if strategy == SearchStrategy.POINT_INTERSECTION:
                result = self._find_by_point_intersection(x, y, coordinate_type)
                if result:
                    results.append(result)

            elif strategy == SearchStrategy.NEAREST_CLICKABLE:
                result = self._find_nearest_clickable(x, y, coordinate_type)
                if result:
                    results.append(result)

            elif strategy == SearchStrategy.Z_INDEX_PRIORITY:
                result = self._find_by_z_index(x, y, coordinate_type)
                if result:
                    results.append(result)

        if not results:
            return None

        # Return highest confidence result
        results.sort(reverse=True)
        best_result = results[0]

        logger.debug(
            f"Found element at ({x}, {y}): {best_result.element.tag_name} "
            f"(confidence: {best_result.confidence:.2f}, strategy: {best_result.strategy.value})"
        )

        return best_result.element

    def _find_by_point_intersection(
        self,
        x: float,
        y: float,
        coordinate_type: CoordinateType
    ) -> Optional[SearchResult]:
        """Find elements that contain the point"""
        # Convert to viewport coordinates if needed
        viewport_x, viewport_y = self._convert_to_viewport(x, y, coordinate_type)

        # Use spatial index for faster lookup
        grid_size = 100
        grid_x = int(viewport_x // grid_size)
        grid_y = int(viewport_y // grid_size)

        candidates = []

        # Check nearby grid cells
        for gx in range(grid_x - 1, grid_x + 2):
            for gy in range(grid_y - 1, grid_y + 2):
                grid_key = (gx, gy)
                if grid_key in self._spatial_grid:
                    candidates.extend(self._spatial_grid[grid_key])

        # Remove duplicates using UID
        seen = {}
        for elem in candidates:
            if elem.uid not in seen:
                seen[elem.uid] = elem
        candidates = list(seen.values())

        # Find elements containing point
        matching = []
        for element in candidates:
            if element.bounding_box.contains_point(viewport_x, viewport_y, CoordinateType.VIEWPORT):
                matching.append(element)

        if not matching:
            return None

        # Return element with highest z-index and depth
        best = max(matching, key=lambda e: (
            int(e.z_index) if e.z_index.isdigit() else 0,
            e.depth
        ))

        confidence = 0.9 if best.clickable else 0.7
        return SearchResult(best, confidence, SearchStrategy.POINT_INTERSECTION)

    def _find_by_z_index(
        self,
        x: float,
        y: float,
        coordinate_type: CoordinateType
    ) -> Optional[SearchResult]:
        """Find element prioritizing z-index"""
        viewport_x, viewport_y = self._convert_to_viewport(x, y, coordinate_type)

        candidates = []
        for element in self.structure.elements:
            if not element.visible:
                continue

            if element.bounding_box.contains_point(viewport_x, viewport_y, CoordinateType.VIEWPORT):
                z_index = int(element.z_index) if element.z_index.isdigit() else 0
                candidates.append((z_index, element.depth, element))

        if not candidates:
            return None

        # Sort by z-index (desc), then depth (desc)
        candidates.sort(reverse=True)
        best = candidates[0][2]

        return SearchResult(best, 0.95, SearchStrategy.Z_INDEX_PRIORITY)

    def _find_nearest_clickable(
        self,
        x: float,
        y: float,
        coordinate_type: CoordinateType,
        max_distance: float = 50
    ) -> Optional[SearchResult]:
        """Find nearest clickable element to point"""
        viewport_x, viewport_y = self._convert_to_viewport(x, y, coordinate_type)

        nearest = None
        min_distance = float('inf')

        for element in self.structure.clickable_elements:
            if not element.visible:
                continue

            # Calculate distance to element center
            distance = self._calculate_distance(
                viewport_x, viewport_y,
                element.bounding_box.center_x,
                element.bounding_box.center_y
            )

            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                nearest = element

        if nearest is None:
            return None

        # Confidence decreases with distance
        confidence = max(0.3, 1.0 - (min_distance / max_distance))

        return SearchResult(
            nearest,
            confidence,
            SearchStrategy.NEAREST_CLICKABLE,
            distance=min_distance
        )

    def find_elements_by_text(
        self,
        text: str,
        exact: bool = False,
        case_sensitive: bool = False,
        include_invisible: bool = False
    ) -> List[SearchResult]:
        """
        Find elements containing specified text.

        Args:
            text: Text to search for
            exact: Exact match required
            case_sensitive: Case-sensitive matching
            include_invisible: Include invisible elements

        Returns:
            List of search results sorted by relevance
        """
        results = []

        search_text = text if case_sensitive else text.lower()

        for element in self.structure.elements:
            if not include_invisible and not element.visible:
                continue

            # Check various text properties
            text_sources = [
                element.text_content,
                element.inner_text,
                element.accessible_name,
                element.aria_label,
                element.value,
                element.placeholder
            ]

            for source in text_sources:
                if source is None:
                    continue

                element_text = source if case_sensitive else source.lower()

                if exact:
                    if element_text.strip() == search_text:
                        match_score = 1.0
                    else:
                        continue
                else:
                    if search_text in element_text:
                        # Calculate match score based on text length ratio
                        match_score = min(1.0, len(search_text) / len(element_text))
                    else:
                        continue

                confidence = 0.9 if exact else match_score
                results.append(SearchResult(
                    element,
                    confidence,
                    SearchStrategy.TEXT_MATCH,
                    match_score=match_score
                ))
                break  # Found match, move to next element

        # Sort by confidence
        results.sort(reverse=True)

        logger.debug(f"Found {len(results)} elements matching text: '{text}'")
        return results

    def find_elements_by_role(
        self,
        role: str,
        name: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Find elements by ARIA role and optional accessible name.

        Args:
            role: ARIA role to search for
            name: Optional accessible name filter

        Returns:
            List of search results
        """
        results = []

        for element in self.structure.elements:
            if element.role != role:
                continue

            if name:
                # Check if accessible name matches
                if not element.accessible_name:
                    continue

                # Fuzzy match
                name_lower = name.lower()
                accessible_lower = element.accessible_name.lower()

                if name_lower in accessible_lower:
                    match_score = len(name_lower) / len(accessible_lower)
                    confidence = 0.9 * match_score
                else:
                    continue
            else:
                confidence = 0.95

            results.append(SearchResult(
                element,
                confidence,
                SearchStrategy.ACCESSIBILITY
            ))

        results.sort(reverse=True)
        logger.debug(f"Found {len(results)} elements with role: {role}")
        return results

    def find_clickable_near_text(
        self,
        text: str,
        max_distance: float = 100,
        exact_text: bool = False
    ) -> List[SearchResult]:
        """
        Find clickable elements near text.

        Args:
            text: Text to search for
            max_distance: Maximum distance in pixels
            exact_text: Require exact text match

        Returns:
            List of clickable elements near text
        """
        # Find text elements
        text_results = self.find_elements_by_text(text, exact=exact_text)
        if not text_results:
            logger.debug(f"No text elements found for: '{text}'")
            return []

        results = []

        for text_result in text_results:
            text_elem = text_result.element
            text_center = (text_elem.bounding_box.center_x, text_elem.bounding_box.center_y)

            for clickable in self.structure.clickable_elements:
                if not clickable.visible:
                    continue

                click_center = (clickable.bounding_box.center_x, clickable.bounding_box.center_y)
                distance = self._calculate_distance(
                    text_center[0], text_center[1],
                    click_center[0], click_center[1]
                )

                if distance <= max_distance:
                    # Confidence based on distance and text match quality
                    distance_score = 1.0 - (distance / max_distance)
                    confidence = (text_result.confidence + distance_score) / 2

                    results.append(SearchResult(
                        clickable,
                        confidence,
                        SearchStrategy.VISUAL_PROXIMITY,
                        distance=distance
                    ))

        # Remove duplicates and sort
        seen = set()
        unique_results = []
        for result in sorted(results, reverse=True):
            if result.element.uid not in seen:
                seen.add(result.element.uid)
                unique_results.append(result)

        logger.debug(f"Found {len(unique_results)} clickable elements near text: '{text}'")
        return unique_results

    def find_elements_in_region(
        self,
        left: float,
        top: float,
        right: float,
        bottom: float,
        element_filter: Optional[Callable[[DOMElement], bool]] = None
    ) -> List[DOMElement]:
        """
        Find all elements within a rectangular region.

        Args:
            left: Left boundary
            top: Top boundary
            right: Right boundary
            bottom: Bottom boundary
            element_filter: Optional filter function

        Returns:
            List of elements in region
        """
        region_box = BoundingBox(
            x=left, y=top,
            width=right - left,
            height=bottom - top,
            top=top, right=right,
            bottom=bottom, left=left,
            page_x=left, page_y=top
        )

        results = []

        for element in self.structure.elements:
            if not element.visible:
                continue

            # Check if element intersects region
            if element.bounding_box.intersects(region_box):
                if element_filter is None or element_filter(element):
                    results.append(element)

        logger.debug(f"Found {len(results)} elements in region")
        return results

    def find_elements_by_attribute(
        self,
        attribute: str,
        value: Optional[str] = None,
        partial_match: bool = False
    ) -> List[DOMElement]:
        """
        Find elements by attribute.

        Args:
            attribute: Attribute name
            value: Optional attribute value
            partial_match: Allow partial value matching

        Returns:
            List of matching elements
        """
        results = []

        for element in self.structure.elements:
            if attribute not in element.attributes:
                continue

            if value is None:
                # Just check attribute exists
                results.append(element)
            else:
                attr_value = element.attributes[attribute]
                if partial_match:
                    if value.lower() in attr_value.lower():
                        results.append(element)
                else:
                    if attr_value == value:
                        results.append(element)

        logger.debug(f"Found {len(results)} elements with attribute: {attribute}")
        return results

    def get_element_path(self, element: DOMElement) -> List[DOMElement]:
        """
        Get element hierarchy path from root to element.

        Args:
            element: Target element

        Returns:
            List of elements from root to target
        """
        path = [element]
        current = element

        while current.parent_tag:
            # Find parent element
            parent = None
            for elem in self.structure.elements:
                if (elem.tag_name == current.parent_tag and
                    elem.depth == current.depth - 1):
                    # Simple heuristic - may need improvement
                    if current.bounding_box.intersects(elem.bounding_box):
                        parent = elem
                        break

            if parent:
                path.insert(0, parent)
                current = parent
            else:
                break

        return path

    def _convert_to_viewport(
        self,
        x: float,
        y: float,
        coordinate_type: CoordinateType
    ) -> Tuple[float, float]:
        """Convert coordinates to viewport space"""
        if coordinate_type == CoordinateType.PAGE:
            return (
                x - self.structure.viewport.scroll_x,
                y - self.structure.viewport.scroll_y
            )
        elif coordinate_type == CoordinateType.SCREEN:
            # Would need window position for accurate conversion
            # For now, assume screen = viewport
            logger.warning("Screen coordinate conversion not fully implemented")
            return (x, y)
        else:  # VIEWPORT
            return (x, y)

    def _calculate_distance(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float
    ) -> float:
        """Calculate Euclidean distance between two points"""
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def get_clickable_center(self, element: DOMElement) -> Tuple[float, float]:
        """
        Get optimal click point for element.

        Args:
            element: Target element

        Returns:
            (x, y) coordinates for clicking
        """
        # For most elements, center is best
        bbox = element.bounding_box

        # Special handling for specific element types
        if element.tag_name == 'input' and element.attributes.get('type') == 'checkbox':
            # Click slightly offset for checkbox
            return (bbox.left + 10, bbox.center_y)

        elif element.tag_name == 'select':
            # Click on right side for dropdown
            return (bbox.right - 20, bbox.center_y)

        else:
            # Default to center
            return (bbox.center_x, bbox.center_y)

    def validate_clickable(
        self,
        element: DOMElement,
        x: Optional[float] = None,
        y: Optional[float] = None
    ) -> bool:
        """
        Validate that element is actually clickable at given coordinates.

        Args:
            element: Element to validate
            x: Optional X coordinate (defaults to element center)
            y: Optional Y coordinate (defaults to element center)

        Returns:
            True if element is clickable at coordinates
        """
        if not element.visible or not element.clickable:
            return False

        # Use center if coordinates not provided
        if x is None or y is None:
            x, y = self.get_clickable_center(element)

        # Check if point is within element bounds
        if not element.bounding_box.contains_point(x, y):
            return False

        # Check if element is being obscured by another element
        element_at_point = self.find_element_at_point(
            x, y,
            CoordinateType.VIEWPORT,
            [SearchStrategy.Z_INDEX_PRIORITY]
        )

        if element_at_point and element_at_point.uid != element.uid:
            logger.warning(
                f"Element {element.tag_name}#{element.element_id} is obscured by "
                f"{element_at_point.tag_name}#{element_at_point.element_id}"
            )
            return False

        return True
