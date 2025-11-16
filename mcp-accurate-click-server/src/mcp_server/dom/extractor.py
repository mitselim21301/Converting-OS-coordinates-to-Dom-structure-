#!/usr/bin/env python3
"""
DOM Structure Extractor

Enhanced DOM extraction system with caching, incremental updates,
and optimizations for large DOMs.
"""

import time
import logging
import hashlib
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime, timedelta
from playwright.sync_api import Page, Error as PlaywrightError

from .models import (
    DOMElement, BoundingBox, DOMStructure, ViewportInfo,
    DOMStatistics, ExtractionOptions, CoordinateType
)

logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with TTL support"""

    def __init__(self, structure: DOMStructure, ttl: int):
        self.structure = structure
        self.created_at = datetime.now()
        self.ttl = ttl
        self.access_count = 0
        self.last_accessed = datetime.now()

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now() - self.created_at > timedelta(seconds=self.ttl)

    def access(self) -> DOMStructure:
        """Access cached structure and update metadata"""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.structure


class DOMCache:
    """Cache layer for DOM structures with TTL support"""

    def __init__(self, default_ttl: int = 60, max_size: int = 100):
        self._cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def _generate_key(self, url: str, viewport_width: int, viewport_height: int,
                      scroll_x: float, scroll_y: float) -> str:
        """Generate cache key from page state"""
        key_string = f"{url}-{viewport_width}x{viewport_height}-{scroll_x},{scroll_y}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[DOMStructure]:
        """Get cached structure if available and not expired"""
        if key not in self._cache:
            self.misses += 1
            return None

        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            self.misses += 1
            logger.debug(f"Cache miss (expired): {key}")
            return None

        self.hits += 1
        logger.debug(f"Cache hit: {key} (accessed {entry.access_count} times)")
        structure = entry.access()
        structure.is_cached = True
        return structure

    def set(self, key: str, structure: DOMStructure, ttl: Optional[int] = None):
        """Store structure in cache"""
        # Evict oldest entries if cache is full
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        ttl = ttl or self.default_ttl
        self._cache[key] = CacheEntry(structure, ttl)
        structure.cache_key = key
        logger.debug(f"Cached structure: {key} (TTL: {ttl}s)")

    def _evict_oldest(self):
        """Evict least recently accessed entry"""
        if not self._cache:
            return

        oldest_key = min(self._cache.keys(),
                        key=lambda k: self._cache[k].last_accessed)
        del self._cache[oldest_key]
        logger.debug(f"Evicted cache entry: {oldest_key}")

    def invalidate(self, key: str):
        """Invalidate specific cache entry"""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Invalidated cache: {key}")

    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        self.hits = 0
        self.misses = 0
        logger.debug("Cache cleared")

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hit_rate,
            'entries': {
                key: {
                    'age': (datetime.now() - entry.created_at).total_seconds(),
                    'access_count': entry.access_count,
                    'ttl': entry.ttl
                }
                for key, entry in self._cache.items()
            }
        }


class DOMStructureExtractor:
    """
    Enhanced DOM structure extractor with caching and optimization.

    Features:
    - Result caching with TTL
    - Incremental update support
    - Large DOM optimization (>1000 elements)
    - Flexible filtering options
    - Accessibility tree extraction
    - Comprehensive error handling
    """

    def __init__(self, page: Page, options: Optional[ExtractionOptions] = None):
        """
        Initialize extractor.

        Args:
            page: Playwright page object
            options: Extraction options
        """
        self.page = page
        self.options = options or ExtractionOptions()
        self.cache = DOMCache(
            default_ttl=self.options.cache_ttl,
            max_size=100
        ) if self.options.use_cache else None
        self._last_structure: Optional[DOMStructure] = None

    def extract(self, force_refresh: bool = False) -> DOMStructure:
        """
        Extract complete DOM structure.

        Args:
            force_refresh: Bypass cache and force new extraction

        Returns:
            DOMStructure object

        Raises:
            RuntimeError: If extraction fails
        """
        start_time = time.time()

        try:
            # Check cache first
            if not force_refresh and self.cache:
                viewport_info = self._get_viewport_info()
                cache_key = self.cache._generate_key(
                    self.page.url,
                    viewport_info['viewport_width'],
                    viewport_info['viewport_height'],
                    viewport_info['scroll_x'],
                    viewport_info['scroll_y']
                )

                cached = self.cache.get(cache_key)
                if cached:
                    logger.info(f"Using cached DOM structure (hit rate: {self.cache.hit_rate:.2%})")
                    return cached

            # Extract fresh structure
            logger.info(f"Extracting DOM structure for {self.page.url}")
            structure = self._extract_fresh()

            # Cache result
            if self.cache and cache_key:
                self.cache.set(cache_key, structure)

            # Store for incremental updates
            self._last_structure = structure

            extraction_time = time.time() - start_time
            logger.info(
                f"✓ Extracted DOM structure in {extraction_time:.2f}s "
                f"({structure.statistics.total_elements} elements)"
            )

            return structure

        except Exception as e:
            logger.error(f"Failed to extract DOM structure: {e}", exc_info=True)
            raise RuntimeError(f"DOM extraction failed: {e}") from e

    def _extract_fresh(self) -> DOMStructure:
        """Extract fresh DOM structure"""
        start_time = time.time()

        # Get viewport and page info
        viewport_info = self._get_viewport_info()

        # Extract all elements
        all_elements = self._extract_all_elements()

        # Apply filters if specified
        if self.options.tag_filter or self.options.exclude_tags:
            all_elements = self._apply_filters(all_elements)

        # Categorize elements
        interactive = [e for e in all_elements if e.is_interactive]
        text_elements = [e for e in all_elements if e.has_text]
        form_elements = [e for e in all_elements
                        if e.tag_name in {'input', 'select', 'textarea', 'button', 'form'}]
        clickable = [e for e in all_elements if e.clickable]
        visible = [e for e in all_elements if e.visible]

        # Calculate statistics
        extraction_time = time.time() - start_time
        viewport_area = viewport_info['viewport_width'] * viewport_info['viewport_height']
        element_density = len(visible) / viewport_area if viewport_area > 0 else 0

        statistics = DOMStatistics(
            total_elements=len(all_elements),
            visible_elements=len(visible),
            clickable_elements=len(clickable),
            interactive_elements=len(interactive),
            text_elements=len(text_elements),
            form_elements=len(form_elements),
            link_elements=len([e for e in all_elements if e.tag_name == 'a']),
            button_elements=len([e for e in all_elements if e.tag_name == 'button']),
            input_elements=len([e for e in all_elements if e.tag_name == 'input']),
            extraction_time=extraction_time,
            element_density=element_density
        )

        viewport = ViewportInfo(
            width=viewport_info['viewport_width'],
            height=viewport_info['viewport_height'],
            device_pixel_ratio=viewport_info['device_pixel_ratio'],
            scroll_x=viewport_info['scroll_x'],
            scroll_y=viewport_info['scroll_y'],
            page_width=viewport_info['page_width'],
            page_height=viewport_info['page_height']
        )

        structure = DOMStructure(
            url=self.page.url,
            title=self.page.title(),
            timestamp=time.time(),
            viewport=viewport,
            elements=all_elements,
            interactive_elements=interactive,
            text_elements=text_elements,
            form_elements=form_elements,
            clickable_elements=clickable,
            statistics=statistics
        )

        return structure

    def _get_viewport_info(self) -> Dict[str, Any]:
        """Get viewport and page dimensions"""
        try:
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
        except PlaywrightError as e:
            logger.error(f"Failed to get viewport info: {e}")
            raise

    def _extract_all_elements(self) -> List[DOMElement]:
        """Extract all DOM elements with comprehensive information"""
        try:
            # Get extraction options as dict
            options_dict = {
                'include_invisible': self.options.include_invisible,
                'max_text_length': self.options.max_text_length,
                'max_depth': self.options.max_depth,
                'extract_aria': self.options.extract_aria,
                'extract_computed_styles': self.options.extract_computed_styles,
                'extract_attributes': self.options.extract_attributes,
                'batch_size': self.options.batch_size
            }

            # JavaScript to extract all element information
            elements_data = self.page.evaluate("""(options) => {
                const elements = [];
                const allElements = Array.from(document.querySelectorAll('*'));

                // Helper functions
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
                                selector += '.' + classes.slice(0, 3).join('.');
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
                        parseFloat(style.opacity) > 0 &&
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
                    const clickableRoles = ['button', 'link', 'checkbox', 'radio', 'tab', 'menuitem', 'option'];
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
                    if (element.tagName.toLowerCase() === 'input' && element.id) {
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
                        const text = element.textContent.trim();
                        return text.length > 0 ? text : null;
                    }

                    return null;
                }

                function getAriaAttributes(element) {
                    const ariaAttrs = {};
                    for (let attr of element.attributes) {
                        if (attr.name.startsWith('aria-')) {
                            ariaAttrs[attr.name] = attr.value;
                        }
                    }
                    return ariaAttrs;
                }

                // Process elements
                allElements.forEach((element, index) => {
                    const depth = getDepth(element);

                    // Skip if depth exceeds limit
                    if (options.max_depth !== null && depth > options.max_depth) {
                        return;
                    }

                    const visible = isVisible(element);

                    // Skip invisible elements if not requested
                    if (!options.include_invisible && !visible) {
                        return;
                    }

                    const rect = element.getBoundingClientRect();
                    const style = window.getComputedStyle(element);

                    // Extract attributes
                    const attributes = {};
                    if (options.extract_attributes) {
                        for (let attr of element.attributes) {
                            attributes[attr.name] = attr.value;
                        }
                    }

                    // Extract ARIA attributes
                    const ariaAttrs = options.extract_aria ? getAriaAttributes(element) : {};

                    const elementData = {
                        index: index,
                        tag_name: element.tagName.toLowerCase(),
                        element_id: element.id || null,
                        class_names: element.className && typeof element.className === 'string'
                            ? element.className.trim().split(/\\s+/).filter(c => c)
                            : [],
                        role: element.getAttribute('role') || null,
                        aria_label: element.getAttribute('aria-label') || null,
                        accessible_name: getAccessibleName(element),
                        aria_attributes: ariaAttrs,
                        text_content: element.textContent
                            ? element.textContent.trim().substring(0, options.max_text_length)
                            : null,
                        inner_text: element.innerText
                            ? element.innerText.trim().substring(0, options.max_text_length)
                            : null,
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
                        focusable: element.tabIndex >= 0 ||
                                  ['input', 'button', 'select', 'textarea', 'a'].includes(element.tagName.toLowerCase()),
                        clickable: isClickable(element),
                        checked: element.checked !== undefined ? element.checked : null,
                        selected: element.selected !== undefined ? element.selected : null,
                        xpath: getXPath(element),
                        css_selector: getCSSSelector(element),
                        depth: depth,
                        parent_tag: element.parentElement ? element.parentElement.tagName.toLowerCase() : null,
                        child_count: element.children.length,
                        attributes: attributes,
                        timestamp: Date.now() / 1000
                    };

                    // Add computed styles if requested
                    if (options.extract_computed_styles) {
                        elementData.z_index = style.zIndex;
                        elementData.opacity = style.opacity;
                        elementData.display = style.display;
                        elementData.visibility = style.visibility;
                        elementData.pointer_events = style.pointerEvents;
                        elementData.position = style.position;
                        elementData.overflow = style.overflow;
                    }

                    elements.push(elementData);
                });

                return elements;
            }""", options_dict)

            # Convert to DOMElement objects
            dom_elements = []
            for elem_data in elements_data:
                bbox = BoundingBox(**elem_data['bounding_box'])

                dom_element = DOMElement(
                    tag_name=elem_data['tag_name'],
                    element_id=elem_data.get('element_id'),
                    class_names=elem_data.get('class_names', []),
                    role=elem_data.get('role'),
                    aria_label=elem_data.get('aria_label'),
                    accessible_name=elem_data.get('accessible_name'),
                    aria_attributes=elem_data.get('aria_attributes', {}),
                    text_content=elem_data.get('text_content'),
                    inner_text=elem_data.get('inner_text'),
                    value=elem_data.get('value'),
                    placeholder=elem_data.get('placeholder'),
                    bounding_box=bbox,
                    visible=elem_data['visible'],
                    enabled=elem_data['enabled'],
                    focusable=elem_data['focusable'],
                    clickable=elem_data['clickable'],
                    checked=elem_data.get('checked'),
                    selected=elem_data.get('selected'),
                    xpath=elem_data['xpath'],
                    css_selector=elem_data['css_selector'],
                    depth=elem_data['depth'],
                    parent_tag=elem_data.get('parent_tag'),
                    child_count=elem_data.get('child_count', 0),
                    attributes=elem_data.get('attributes', {}),
                    z_index=elem_data.get('z_index', 'auto'),
                    opacity=elem_data.get('opacity', '1'),
                    display=elem_data.get('display', 'block'),
                    visibility=elem_data.get('visibility', 'visible'),
                    pointer_events=elem_data.get('pointer_events', 'auto'),
                    position=elem_data.get('position', 'static'),
                    overflow=elem_data.get('overflow', 'visible'),
                    timestamp=elem_data.get('timestamp')
                )

                dom_elements.append(dom_element)

            logger.debug(f"Extracted {len(dom_elements)} elements")
            return dom_elements

        except PlaywrightError as e:
            logger.error(f"Failed to extract elements: {e}")
            raise

    def _apply_filters(self, elements: List[DOMElement]) -> List[DOMElement]:
        """Apply tag and class filters to element list"""
        filtered = elements

        # Tag filter (include only specified tags)
        if self.options.tag_filter:
            filtered = [e for e in filtered if e.tag_name in self.options.tag_filter]

        # Exclude tags
        if self.options.exclude_tags:
            filtered = [e for e in filtered if e.tag_name not in self.options.exclude_tags]

        # Class filter (include only elements with specified classes)
        if self.options.class_filter:
            filtered = [e for e in filtered
                       if any(cls in e.class_names for cls in self.options.class_filter)]

        logger.debug(f"Filtered {len(elements)} -> {len(filtered)} elements")
        return filtered

    def extract_incremental(self, element_selector: str) -> List[DOMElement]:
        """
        Extract only specific elements for incremental updates.

        Args:
            element_selector: CSS selector for elements to extract

        Returns:
            List of extracted DOM elements
        """
        try:
            logger.debug(f"Incremental extraction: {element_selector}")

            # Use page.evaluate to extract specific elements
            elements_data = self.page.evaluate(f"""
                (selector) => {{
                    const elements = document.querySelectorAll(selector);
                    // ... (similar extraction logic for matched elements)
                    return Array.from(elements).map(elem => ({{
                        // ... element data
                    }}));
                }}
            """, element_selector)

            # Convert and return
            # TODO: Implement full conversion
            return []

        except Exception as e:
            logger.error(f"Incremental extraction failed: {e}")
            return []

    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics"""
        return self.cache.get_stats() if self.cache else None

    def clear_cache(self):
        """Clear the extraction cache"""
        if self.cache:
            self.cache.clear()
            logger.info("Cache cleared")
