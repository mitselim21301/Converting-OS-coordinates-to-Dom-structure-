#!/usr/bin/env python3
"""
DOM Data Models

Comprehensive data models for DOM structure representation with
support for multiple coordinate systems and accessibility features.
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Any
from enum import Enum
import hashlib


class CoordinateType(Enum):
    """Coordinate system types"""
    VIEWPORT = "viewport"  # Relative to visible viewport
    PAGE = "page"          # Relative to full page (including scroll)
    SCREEN = "screen"      # Relative to screen (OS coordinates)


@dataclass
class BoundingBox:
    """
    Represents element bounding box in multiple coordinate systems.

    Provides comprehensive position information including viewport,
    page, and optional screen coordinates.
    """
    # Viewport coordinates (relative to visible area)
    x: float
    y: float
    width: float
    height: float
    top: float
    right: float
    bottom: float
    left: float

    # Page coordinates (accounting for scroll)
    page_x: float
    page_y: float

    # Screen coordinates (OS level, if available)
    screen_x: Optional[float] = None
    screen_y: Optional[float] = None

    @property
    def center_x(self) -> float:
        """Get center X coordinate in viewport space"""
        return self.x + (self.width / 2)

    @property
    def center_y(self) -> float:
        """Get center Y coordinate in viewport space"""
        return self.y + (self.height / 2)

    @property
    def page_center_x(self) -> float:
        """Get center X coordinate in page space"""
        return self.page_x + (self.width / 2)

    @property
    def page_center_y(self) -> float:
        """Get center Y coordinate in page space"""
        return self.page_y + (self.height / 2)

    @property
    def area(self) -> float:
        """Calculate bounding box area"""
        return self.width * self.height

    def contains_point(self, x: float, y: float, coordinate_type: CoordinateType = CoordinateType.VIEWPORT) -> bool:
        """
        Check if point is within bounding box.

        Args:
            x: X coordinate
            y: Y coordinate
            coordinate_type: Coordinate system type

        Returns:
            True if point is within bounds
        """
        if coordinate_type == CoordinateType.PAGE:
            return (self.page_x <= x <= self.page_x + self.width and
                    self.page_y <= y <= self.page_y + self.height)
        elif coordinate_type == CoordinateType.SCREEN and self.screen_x and self.screen_y:
            return (self.screen_x <= x <= self.screen_x + self.width and
                    self.screen_y <= y <= self.screen_y + self.height)
        else:  # VIEWPORT
            return (self.left <= x <= self.right and
                    self.top <= y <= self.bottom)

    def intersects(self, other: 'BoundingBox') -> bool:
        """Check if this bounding box intersects with another"""
        return not (self.right < other.left or
                    self.left > other.right or
                    self.bottom < other.top or
                    self.top > other.bottom)

    def intersection_area(self, other: 'BoundingBox') -> float:
        """Calculate intersection area with another bounding box"""
        if not self.intersects(other):
            return 0.0

        x_overlap = min(self.right, other.right) - max(self.left, other.left)
        y_overlap = min(self.bottom, other.bottom) - max(self.top, other.top)
        return x_overlap * y_overlap


@dataclass
class DOMElement:
    """
    Comprehensive representation of a DOM element.

    Includes identity, accessibility, content, position, state,
    hierarchy, attributes, and computed styles.
    """
    # Identity (required fields first)
    tag_name: str
    element_id: Optional[str]
    class_names: List[str]

    # Accessibility
    role: Optional[str]
    aria_label: Optional[str]
    accessible_name: Optional[str]

    # Content
    text_content: Optional[str]
    inner_text: Optional[str]
    value: Optional[str]
    placeholder: Optional[str]

    # Position
    bounding_box: BoundingBox

    # State
    visible: bool
    enabled: bool
    focusable: bool
    clickable: bool

    # Hierarchy
    xpath: str
    css_selector: str
    depth: int
    parent_tag: Optional[str]

    # Fields with defaults must come after fields without defaults
    # Accessibility (with defaults)
    aria_attributes: Dict[str, str] = field(default_factory=dict)

    # State (with defaults)
    checked: Optional[bool] = None
    selected: Optional[bool] = None

    # Hierarchy (with defaults)
    child_count: int = 0

    # Attributes
    attributes: Dict[str, str] = field(default_factory=dict)

    # Computed style (selected properties)
    z_index: str = "auto"
    opacity: str = "1"
    display: str = "block"
    visibility: str = "visible"
    pointer_events: str = "auto"
    position: str = "static"
    overflow: str = "visible"

    # Unique identifier
    uid: str = ""

    # Metadata
    timestamp: Optional[float] = None

    def __post_init__(self):
        """Generate UID if not provided"""
        if not self.uid:
            uid_string = f"{self.tag_name}-{self.element_id or ''}-{self.xpath}"
            self.uid = hashlib.md5(uid_string.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert bounding_box to dict if needed
        if isinstance(result.get('bounding_box'), BoundingBox):
            result['bounding_box'] = asdict(result['bounding_box'])
        return result

    def matches_selector(self, selector: str) -> bool:
        """
        Check if element matches a simple selector.
        Supports: tag, #id, .class
        """
        selector = selector.strip()

        # ID selector
        if selector.startswith('#'):
            return self.element_id == selector[1:]

        # Class selector
        if selector.startswith('.'):
            return selector[1:] in self.class_names

        # Tag selector
        return self.tag_name.lower() == selector.lower()

    @property
    def is_interactive(self) -> bool:
        """Check if element is interactive"""
        return self.clickable or self.focusable

    @property
    def has_text(self) -> bool:
        """Check if element has visible text content"""
        return bool(self.text_content and self.text_content.strip())

    @property
    def center_point(self) -> tuple[float, float]:
        """Get center point in viewport coordinates"""
        return (self.bounding_box.center_x, self.bounding_box.center_y)


@dataclass
class ViewportInfo:
    """Viewport and page dimension information"""
    width: int
    height: int
    device_pixel_ratio: float
    scroll_x: float
    scroll_y: float
    page_width: float
    page_height: float

    # Screen information (if available)
    screen_x: Optional[float] = None
    screen_y: Optional[float] = None
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None


@dataclass
class DOMStatistics:
    """Statistics about extracted DOM structure"""
    total_elements: int
    visible_elements: int
    clickable_elements: int
    interactive_elements: int
    text_elements: int
    form_elements: int
    link_elements: int
    button_elements: int
    input_elements: int

    # Performance metrics
    extraction_time: float
    element_density: float  # elements per viewport area

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class DOMStructure:
    """
    Complete DOM structure with metadata.

    Represents a snapshot of the entire DOM at a specific point in time,
    including all elements, categorizations, and statistics.
    """
    # Page metadata
    url: str
    title: str
    timestamp: float

    # Viewport info
    viewport: ViewportInfo

    # Elements (main storage)
    elements: List[DOMElement]

    # Categorized elements (references to main elements)
    interactive_elements: List[DOMElement] = field(default_factory=list)
    text_elements: List[DOMElement] = field(default_factory=list)
    form_elements: List[DOMElement] = field(default_factory=list)
    clickable_elements: List[DOMElement] = field(default_factory=list)

    # Statistics
    statistics: Optional[DOMStatistics] = None

    # Cache metadata
    cache_key: Optional[str] = None
    is_cached: bool = False

    def __post_init__(self):
        """Categorize elements if not already done"""
        if not self.interactive_elements:
            self.interactive_elements = [e for e in self.elements if e.is_interactive]

        if not self.text_elements:
            self.text_elements = [e for e in self.elements if e.has_text]

        if not self.form_elements:
            form_tags = {'input', 'select', 'textarea', 'button', 'form'}
            self.form_elements = [e for e in self.elements if e.tag_name in form_tags]

        if not self.clickable_elements:
            self.clickable_elements = [e for e in self.elements if e.clickable]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'url': self.url,
            'title': self.title,
            'timestamp': self.timestamp,
            'viewport': asdict(self.viewport),
            'elements': [elem.to_dict() for elem in self.elements],
            'interactive_elements': [elem.to_dict() for elem in self.interactive_elements],
            'text_elements': [elem.to_dict() for elem in self.text_elements],
            'form_elements': [elem.to_dict() for elem in self.form_elements],
            'clickable_elements': [elem.to_dict() for elem in self.clickable_elements],
            'statistics': self.statistics.to_dict() if self.statistics else None,
            'cache_metadata': {
                'cache_key': self.cache_key,
                'is_cached': self.is_cached
            }
        }

    def get_element_by_uid(self, uid: str) -> Optional[DOMElement]:
        """Find element by unique identifier"""
        for elem in self.elements:
            if elem.uid == uid:
                return elem
        return None

    def get_elements_by_tag(self, tag_name: str) -> List[DOMElement]:
        """Get all elements with specified tag name"""
        return [e for e in self.elements if e.tag_name.lower() == tag_name.lower()]

    def get_elements_by_role(self, role: str) -> List[DOMElement]:
        """Get all elements with specified ARIA role"""
        return [e for e in self.elements if e.role == role]

    def get_visible_elements(self) -> List[DOMElement]:
        """Get all visible elements"""
        return [e for e in self.elements if e.visible]


@dataclass
class ExtractionOptions:
    """Options for DOM extraction"""
    # Performance options
    include_invisible: bool = False
    max_text_length: int = 500
    max_depth: Optional[int] = None

    # Filtering options
    tag_filter: Optional[List[str]] = None
    class_filter: Optional[List[str]] = None
    exclude_tags: Optional[List[str]] = None

    # Feature flags
    extract_aria: bool = True
    extract_computed_styles: bool = True
    extract_attributes: bool = True

    # Optimization
    use_cache: bool = True
    cache_ttl: int = 60  # seconds
    batch_size: int = 100  # for large DOM processing

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
