#!/usr/bin/env python3
"""
Comprehensive DOM Structure Extractor with Coordinate Mapping

This module provides a sophisticated approach to extracting DOM structure,
combining multiple strategies for maximum accuracy:
1. Accessibility tree extraction
2. DOM element enumeration with coordinates
3. Visual viewport analysis
4. Text content extraction with positioning
5. Interactive element detection
"""

import json
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple, Any
from playwright.sync_api import sync_playwright, Page, ElementHandle, Locator
import hashlib


@dataclass
class BoundingBox:
    """Represents element bounding box in multiple coordinate systems"""
    x: float  # Viewport X
    y: float  # Viewport Y
    width: float
    height: float
    top: float
    right: float
    bottom: float
    left: float

    # Page coordinates (accounting for scroll)
    page_x: float
    page_y: float

    # Screen coordinates (if available)
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
class DOMElement:
    """Comprehensive representation of a DOM element"""
    # Identity
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

    # Attributes
    attributes: Dict[str, str]

    # Computed style (selected properties)
    z_index: str
    opacity: str
    display: str
    visibility: str
    pointer_events: str

    # Unique identifier
    uid: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        return result


@dataclass
class DOMStructure:
    """Complete DOM structure with metadata"""
    url: str
    title: str
    timestamp: float

    # Viewport info
    viewport_width: int
    viewport_height: int
    device_pixel_ratio: float

    # Scroll info
    scroll_x: float
    scroll_y: float

    # Page dimensions
    page_width: float
    page_height: float

    # Elements
    elements: List[DOMElement]
    interactive_elements: List[DOMElement]
    text_elements: List[DOMElement]

    # Statistics
    total_elements: int
    visible_elements: int
    clickable_elements: int

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'url': self.url,
            'title': self.title,
            'timestamp': self.timestamp,
            'viewport': {
                'width': self.viewport_width,
                'height': self.viewport_height,
                'device_pixel_ratio': self.device_pixel_ratio
            },
            'scroll': {
                'x': self.scroll_x,
                'y': self.scroll_y
            },
            'page': {
                'width': self.page_width,
                'height': self.page_height
            },
            'elements': [elem.to_dict() for elem in self.elements],
            'interactive_elements': [elem.to_dict() for elem in self.interactive_elements],
            'text_elements': [elem.to_dict() for elem in self.text_elements],
            'statistics': {
                'total_elements': self.total_elements,
                'visible_elements': self.visible_elements,
                'clickable_elements': self.clickable_elements
            }
        }


class DOMStructureExtractor:
    """Extract comprehensive DOM structure with multiple strategies"""

    def __init__(self, page: Page):
        self.page = page

    def extract(self) -> DOMStructure:
        """Extract complete DOM structure"""
        start_time = time.time()

        # Get viewport and page info
        viewport_info = self._get_viewport_info()

        # Extract all elements
        all_elements = self._extract_all_elements()

        # Categorize elements
        interactive = [e for e in all_elements if e.clickable or e.focusable]
        text_elements = [e for e in all_elements if e.text_content and len(e.text_content.strip()) > 0]
        visible = [e for e in all_elements if e.visible]
        clickable = [e for e in all_elements if e.clickable]

        structure = DOMStructure(
            url=self.page.url,
            title=self.page.title(),
            timestamp=time.time(),
            viewport_width=viewport_info['viewport_width'],
            viewport_height=viewport_info['viewport_height'],
            device_pixel_ratio=viewport_info['device_pixel_ratio'],
            scroll_x=viewport_info['scroll_x'],
            scroll_y=viewport_info['scroll_y'],
            page_width=viewport_info['page_width'],
            page_height=viewport_info['page_height'],
            elements=all_elements,
            interactive_elements=interactive,
            text_elements=text_elements,
            total_elements=len(all_elements),
            visible_elements=len(visible),
            clickable_elements=len(clickable)
        )

        print(f"✓ Extracted DOM structure in {time.time() - start_time:.2f}s")
        print(f"  Total elements: {len(all_elements)}")
        print(f"  Visible elements: {len(visible)}")
        print(f"  Interactive elements: {len(interactive)}")
        print(f"  Text elements: {len(text_elements)}")

        return structure

    def _get_viewport_info(self) -> Dict:
        """Get viewport and page dimensions"""
        return self.page.evaluate("""() => {
            return {
                viewport_width: window.innerWidth,
                viewport_height: window.innerHeight,
                device_pixel_ratio: window.devicePixelRatio,
                scroll_x: window.scrollX,
                scroll_y: window.scrollY,
                page_width: document.documentElement.scrollWidth,
                page_height: document.documentElement.scrollHeight
            };
        }""")

    def _extract_all_elements(self) -> List[DOMElement]:
        """Extract all DOM elements with comprehensive information"""

        # JavaScript to extract all element information
        elements_data = self.page.evaluate("""() => {
            const elements = [];
            const allElements = document.querySelectorAll('*');

            function getXPath(element) {
                if (element.id) {
                    return `//*[@id="${element.id}"]`;
                }
                if (element === document.body) {
                    return '/html/body';
                }

                let ix = 0;
                const siblings = element.parentNode?.childNodes || [];
                for (let i = 0; i < siblings.length; i++) {
                    const sibling = siblings[i];
                    if (sibling === element) {
                        const parentPath = element.parentNode ? getXPath(element.parentNode) : '';
                        return `${parentPath}/${element.tagName.toLowerCase()}[${ix + 1}]`;
                    }
                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                        ix++;
                    }
                }
                return '';
            }

            function getCSSSelector(element) {
                if (element.id) {
                    return `#${element.id}`;
                }

                const path = [];
                let current = element;

                while (current && current !== document.body) {
                    let selector = current.tagName.toLowerCase();

                    if (current.className && typeof current.className === 'string') {
                        const classes = current.className.trim().split(/\\s+/).filter(c => c);
                        if (classes.length > 0) {
                            selector += '.' + classes.join('.');
                        }
                    }

                    path.unshift(selector);
                    current = current.parentElement;
                }

                return path.join(' > ');
            }

            function getDepth(element) {
                let depth = 0;
                let current = element;
                while (current.parentElement) {
                    depth++;
                    current = current.parentElement;
                }
                return depth;
            }

            function isVisible(element) {
                const style = window.getComputedStyle(element);
                const rect = element.getBoundingClientRect();

                return (
                    style.display !== 'none' &&
                    style.visibility !== 'hidden' &&
                    style.opacity !== '0' &&
                    rect.width > 0 &&
                    rect.height > 0
                );
            }

            function isClickable(element) {
                const tagName = element.tagName.toLowerCase();
                const clickableTags = ['a', 'button', 'input', 'select', 'textarea', 'label'];

                if (clickableTags.includes(tagName)) {
                    return true;
                }

                const role = element.getAttribute('role');
                const clickableRoles = ['button', 'link', 'checkbox', 'radio', 'tab', 'menuitem'];
                if (role && clickableRoles.includes(role)) {
                    return true;
                }

                if (element.onclick || element.hasAttribute('onclick')) {
                    return true;
                }

                const style = window.getComputedStyle(element);
                if (style.cursor === 'pointer') {
                    return true;
                }

                return false;
            }

            function getAccessibleName(element) {
                // Try aria-label first
                if (element.hasAttribute('aria-label')) {
                    return element.getAttribute('aria-label');
                }

                // Try aria-labelledby
                if (element.hasAttribute('aria-labelledby')) {
                    const id = element.getAttribute('aria-labelledby');
                    const labelElement = document.getElementById(id);
                    if (labelElement) {
                        return labelElement.textContent.trim();
                    }
                }

                // For inputs, try associated label
                if (element.tagName.toLowerCase() === 'input') {
                    const label = document.querySelector(`label[for="${element.id}"]`);
                    if (label) {
                        return label.textContent.trim();
                    }
                }

                // Try title attribute
                if (element.hasAttribute('title')) {
                    return element.getAttribute('title');
                }

                // Fallback to text content for certain elements
                const textTags = ['button', 'a', 'label'];
                if (textTags.includes(element.tagName.toLowerCase())) {
                    return element.textContent.trim();
                }

                return null;
            }

            allElements.forEach((element, index) => {
                const rect = element.getBoundingClientRect();
                const style = window.getComputedStyle(element);
                const attributes = {};

                for (let attr of element.attributes) {
                    attributes[attr.name] = attr.value;
                }

                const visible = isVisible(element);

                elements.push({
                    index: index,
                    tag_name: element.tagName.toLowerCase(),
                    element_id: element.id || null,
                    class_names: element.className && typeof element.className === 'string'
                        ? element.className.trim().split(/\\s+/).filter(c => c)
                        : [],
                    role: element.getAttribute('role') || null,
                    aria_label: element.getAttribute('aria-label') || null,
                    accessible_name: getAccessibleName(element),
                    text_content: element.textContent ? element.textContent.trim().substring(0, 500) : null,
                    inner_text: element.innerText ? element.innerText.trim().substring(0, 500) : null,
                    value: element.value || null,
                    placeholder: element.placeholder || null,
                    bounding_box: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                        top: rect.top,
                        right: rect.right,
                        bottom: rect.bottom,
                        left: rect.left,
                        page_x: rect.left + window.scrollX,
                        page_y: rect.top + window.scrollY
                    },
                    visible: visible,
                    enabled: !element.disabled,
                    focusable: element.tabIndex >= 0 || ['input', 'button', 'select', 'textarea', 'a'].includes(element.tagName.toLowerCase()),
                    clickable: isClickable(element),
                    xpath: getXPath(element),
                    css_selector: getCSSSelector(element),
                    depth: getDepth(element),
                    parent_tag: element.parentElement ? element.parentElement.tagName.toLowerCase() : null,
                    attributes: attributes,
                    z_index: style.zIndex,
                    opacity: style.opacity,
                    display: style.display,
                    visibility: style.visibility,
                    pointer_events: style.pointerEvents
                });
            });

            return elements;
        }""")

        # Convert to DOMElement objects
        dom_elements = []
        for elem_data in elements_data:
            # Create UID from element properties
            uid_string = f"{elem_data['tag_name']}-{elem_data.get('element_id', '')}-{elem_data['xpath']}"
            uid = hashlib.md5(uid_string.encode()).hexdigest()[:16]

            bbox = BoundingBox(**elem_data['bounding_box'])

            dom_element = DOMElement(
                tag_name=elem_data['tag_name'],
                element_id=elem_data['element_id'],
                class_names=elem_data['class_names'],
                role=elem_data['role'],
                aria_label=elem_data['aria_label'],
                accessible_name=elem_data['accessible_name'],
                text_content=elem_data['text_content'],
                inner_text=elem_data['inner_text'],
                value=elem_data['value'],
                placeholder=elem_data['placeholder'],
                bounding_box=bbox,
                visible=elem_data['visible'],
                enabled=elem_data['enabled'],
                focusable=elem_data['focusable'],
                clickable=elem_data['clickable'],
                xpath=elem_data['xpath'],
                css_selector=elem_data['css_selector'],
                depth=elem_data['depth'],
                parent_tag=elem_data['parent_tag'],
                attributes=elem_data['attributes'],
                z_index=elem_data['z_index'],
                opacity=elem_data['opacity'],
                display=elem_data['display'],
                visibility=elem_data['visibility'],
                pointer_events=elem_data['pointer_events'],
                uid=uid
            )

            dom_elements.append(dom_element)

        return dom_elements


class CoordinateMapper:
    """Map between coordinates and DOM elements"""

    def __init__(self, dom_structure: DOMStructure):
        self.structure = dom_structure

    def find_element_at_point(self, x: float, y: float,
                             coordinate_type: str = 'viewport') -> Optional[DOMElement]:
        """
        Find DOM element at specified coordinates

        Args:
            x: X coordinate
            y: Y coordinate
            coordinate_type: 'viewport', 'page', or 'screen'

        Returns:
            DOMElement if found, None otherwise
        """
        # Convert to viewport coordinates if needed
        if coordinate_type == 'page':
            x = x - self.structure.scroll_x
            y = y - self.structure.scroll_y
        elif coordinate_type == 'screen':
            # Screen coordinates would need browser window position
            # For now, treat as viewport
            pass

        # Find all elements that contain this point
        candidates = []
        for element in self.structure.elements:
            if not element.visible:
                continue

            bbox = element.bounding_box
            if (bbox.left <= x <= bbox.right and
                bbox.top <= y <= bbox.bottom):
                candidates.append(element)

        if not candidates:
            return None

        # Return the element with highest z-index and depth (most specific)
        candidates.sort(key=lambda e: (
            int(e.z_index) if e.z_index.isdigit() else 0,
            e.depth
        ), reverse=True)

        return candidates[0]

    def find_elements_by_text(self, text: str, exact: bool = False) -> List[DOMElement]:
        """Find elements containing specified text"""
        results = []
        text_lower = text.lower()

        for element in self.structure.text_elements:
            if element.text_content:
                if exact:
                    if element.text_content.strip() == text:
                        results.append(element)
                else:
                    if text_lower in element.text_content.lower():
                        results.append(element)

        return results

    def find_clickable_near_text(self, text: str, max_distance: float = 100) -> List[DOMElement]:
        """Find clickable elements near text"""
        text_elements = self.find_elements_by_text(text, exact=False)
        if not text_elements:
            return []

        results = []
        for text_elem in text_elements:
            text_center = (text_elem.bounding_box.center_x, text_elem.bounding_box.center_y)

            for clickable in self.structure.interactive_elements:
                if not clickable.visible or not clickable.clickable:
                    continue

                click_center = (clickable.bounding_box.center_x, clickable.bounding_box.center_y)
                distance = ((text_center[0] - click_center[0])**2 +
                           (text_center[1] - click_center[1])**2)**0.5

                if distance <= max_distance:
                    results.append(clickable)

        return results


if __name__ == '__main__':
    # Quick test
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto('https://example.com')
        page.wait_for_load_state('networkidle')

        extractor = DOMStructureExtractor(page)
        structure = extractor.extract()

        # Save to file
        with open('/tmp/dom_structure.json', 'w') as f:
            json.dump(structure.to_dict(), f, indent=2)

        print(f"\n✓ Saved structure to /tmp/dom_structure.json")

        browser.close()
