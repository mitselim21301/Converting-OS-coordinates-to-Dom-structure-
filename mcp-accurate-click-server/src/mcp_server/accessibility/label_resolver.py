#!/usr/bin/env python3
"""
Accessible Name and Label Resolver

Computes accessible names for elements according to the Accessible Name and
Description Computation specification.

This handles:
- aria-label
- aria-labelledby
- aria-describedby
- Native HTML labels
- Element text content
- Placeholder and title attributes

References:
- Accessible Name Computation: https://www.w3.org/TR/accname-1.2/
- ACCESSIBILITY_TREE_RESEARCH.md
"""

from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass
from playwright.sync_api import Page, CDPSession, ElementHandle

from .tree_extractor import AXNode


@dataclass
class AccessibleNameInfo:
    """
    Information about how an element's accessible name was computed.
    """
    name: str
    source: str  # "aria-label", "aria-labelledby", "label", "content", "placeholder", "title", etc.
    referenced_elements: List[str] = None  # IDs of elements used in computation

    def __post_init__(self):
        if self.referenced_elements is None:
            self.referenced_elements = []


class LabelResolver:
    """
    Resolves accessible names and descriptions for DOM elements.

    The accessible name computation follows this precedence:
    1. aria-labelledby (highest priority)
    2. aria-label
    3. Native HTML label element
    4. Element's text content
    5. placeholder attribute
    6. title attribute (lowest priority)

    Usage:
        resolver = LabelResolver(page)
        name_info = await resolver.get_accessible_name(element)
        print(f"Name: {name_info.name}, Source: {name_info.source}")
    """

    def __init__(self, page: Page):
        """
        Initialize the resolver.

        Args:
            page: Playwright Page instance
        """
        self.page = page
        self._cdp_session: Optional[CDPSession] = None

    async def _get_cdp_session(self) -> CDPSession:
        """Get or create CDP session"""
        if self._cdp_session is None:
            self._cdp_session = await self.page.context.new_cdp_session(self.page)
        return self._cdp_session

    async def get_accessible_name(
        self,
        element: ElementHandle,
        visited: Optional[Set[str]] = None
    ) -> AccessibleNameInfo:
        """
        Compute the accessible name for an element.

        Follows the ARIA accessible name computation algorithm.

        Args:
            element: Playwright ElementHandle
            visited: Set of element IDs already visited (prevents infinite recursion)

        Returns:
            AccessibleNameInfo with computed name and source
        """
        if visited is None:
            visited = set()

        # Get element attributes
        attrs = await self._get_element_attributes(element)
        element_id = attrs.get('id', '')

        if element_id and element_id in visited:
            # Prevent infinite recursion in aria-labelledby chains
            return AccessibleNameInfo(name='', source='circular-reference')

        if element_id:
            visited.add(element_id)

        # 1. Check aria-labelledby (highest priority)
        if 'aria-labelledby' in attrs:
            name = await self._resolve_aria_labelledby(attrs['aria-labelledby'], visited)
            if name:
                return AccessibleNameInfo(
                    name=name,
                    source='aria-labelledby',
                    referenced_elements=attrs['aria-labelledby'].split()
                )

        # 2. Check aria-label
        if 'aria-label' in attrs:
            label = attrs['aria-label'].strip()
            if label:
                return AccessibleNameInfo(name=label, source='aria-label')

        # 3. Check for native label element
        label_name = await self._find_native_label(element, attrs)
        if label_name:
            return AccessibleNameInfo(name=label_name, source='label')

        # 4. Get element's text content
        tag_name = await element.evaluate('el => el.tagName.toLowerCase()')

        # For certain elements, use their text content
        if tag_name in ['button', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            text = await self._get_text_content(element)
            if text:
                return AccessibleNameInfo(name=text, source='content')

        # For inputs, check value
        if tag_name == 'input':
            input_type = attrs.get('type', 'text')
            if input_type in ['button', 'submit', 'reset']:
                value = attrs.get('value', '')
                if value:
                    return AccessibleNameInfo(name=value, source='value')

        # 5. Check placeholder
        if 'placeholder' in attrs:
            placeholder = attrs['placeholder'].strip()
            if placeholder:
                return AccessibleNameInfo(name=placeholder, source='placeholder')

        # 6. Check title (lowest priority)
        if 'title' in attrs:
            title = attrs['title'].strip()
            if title:
                return AccessibleNameInfo(name=title, source='title')

        # No accessible name found
        return AccessibleNameInfo(name='', source='none')

    async def get_accessible_description(self, element: ElementHandle) -> Optional[str]:
        """
        Get the accessible description for an element.

        Checks aria-describedby and title attribute.

        Args:
            element: Playwright ElementHandle

        Returns:
            Description string, or None
        """
        attrs = await self._get_element_attributes(element)

        # Check aria-describedby
        if 'aria-describedby' in attrs:
            desc = await self._resolve_aria_describedby(attrs['aria-describedby'])
            if desc:
                return desc

        # Check title (if not already used as name)
        if 'title' in attrs:
            # Only use title as description if it's not the accessible name
            name_info = await self.get_accessible_name(element)
            if name_info.source != 'title':
                return attrs['title'].strip()

        return None

    async def _get_element_attributes(self, element: ElementHandle) -> Dict[str, str]:
        """
        Get all attributes of an element.

        Args:
            element: ElementHandle

        Returns:
            Dictionary of attribute name -> value
        """
        return await element.evaluate('''
            el => {
                const attrs = {};
                for (const attr of el.attributes) {
                    attrs[attr.name] = attr.value;
                }
                return attrs;
            }
        ''')

    async def _get_text_content(self, element: ElementHandle) -> str:
        """
        Get the visible text content of an element.

        Args:
            element: ElementHandle

        Returns:
            Text content, trimmed and normalized
        """
        text = await element.evaluate('''
            el => {
                // Get innerText if available (respects visibility)
                if (el.innerText !== undefined) {
                    return el.innerText;
                }
                // Fallback to textContent
                return el.textContent || '';
            }
        ''')

        # Normalize whitespace
        return ' '.join(text.split())

    async def _resolve_aria_labelledby(
        self,
        labelledby: str,
        visited: Set[str]
    ) -> Optional[str]:
        """
        Resolve aria-labelledby reference(s).

        Args:
            labelledby: Space-separated list of element IDs
            visited: Set of visited IDs (for cycle detection)

        Returns:
            Combined text from referenced elements, or None
        """
        element_ids = labelledby.strip().split()
        if not element_ids:
            return None

        texts = []
        for element_id in element_ids:
            if element_id in visited:
                continue  # Skip circular references

            # Find element by ID
            referenced = await self.page.query_selector(f'#{element_id}')
            if referenced:
                # Recursively get accessible name
                name_info = await self.get_accessible_name(referenced, visited.copy())
                if name_info.name:
                    texts.append(name_info.name)

        return ' '.join(texts) if texts else None

    async def _resolve_aria_describedby(self, describedby: str) -> Optional[str]:
        """
        Resolve aria-describedby reference(s).

        Args:
            describedby: Space-separated list of element IDs

        Returns:
            Combined text from referenced elements, or None
        """
        element_ids = describedby.strip().split()
        if not element_ids:
            return None

        texts = []
        for element_id in element_ids:
            # Find element by ID
            referenced = await self.page.query_selector(f'#{element_id}')
            if referenced:
                text = await self._get_text_content(referenced)
                if text:
                    texts.append(text)

        return ' '.join(texts) if texts else None

    async def _find_native_label(
        self,
        element: ElementHandle,
        attrs: Dict[str, str]
    ) -> Optional[str]:
        """
        Find the native HTML label for an input element.

        Args:
            element: ElementHandle
            attrs: Element attributes

        Returns:
            Label text, or None
        """
        # Check if this is a labelable element
        tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
        labelable_elements = ['input', 'textarea', 'select', 'button', 'meter', 'output', 'progress']

        if tag_name not in labelable_elements:
            return None

        element_id = attrs.get('id')

        # Method 1: Label with for attribute
        if element_id:
            label = await self.page.query_selector(f'label[for="{element_id}"]')
            if label:
                text = await self._get_text_content(label)
                if text:
                    return text

        # Method 2: Element wrapped in label
        label = await element.evaluate('''
            el => {
                let parent = el.parentElement;
                while (parent) {
                    if (parent.tagName.toLowerCase() === 'label') {
                        return parent;
                    }
                    parent = parent.parentElement;
                }
                return null;
            }
        ''')

        if label:
            # Get label's handle and extract text
            label_element = await element.evaluate_handle('''
                el => {
                    let parent = el.parentElement;
                    while (parent) {
                        if (parent.tagName.toLowerCase() === 'label') {
                            return parent;
                        }
                        parent = parent.parentElement;
                    }
                    return null;
                }
            ''')

            if label_element:
                text = await label_element.evaluate('el => el.innerText || el.textContent || ""')
                text = ' '.join(text.split())  # Normalize whitespace
                if text:
                    return text

        return None

    async def validate_accessible_names(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Validate accessible names for all interactive elements on the page.

        Returns a report of elements with missing or problematic accessible names.

        Returns:
            Dictionary with 'missing', 'empty', and 'good' lists
        """
        result = {
            'missing': [],
            'empty': [],
            'good': []
        }

        # Find all interactive elements
        interactive_selectors = [
            'button',
            'a[href]',
            'input:not([type="hidden"])',
            'textarea',
            'select',
            '[role="button"]',
            '[role="link"]',
            '[role="checkbox"]',
            '[role="radio"]',
            '[role="menuitem"]',
            '[tabindex]:not([tabindex="-1"])'
        ]

        for selector in interactive_selectors:
            elements = await self.page.query_selector_all(selector)

            for element in elements:
                # Get accessible name
                name_info = await self.get_accessible_name(element)

                # Get element info for report
                tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                attrs = await self._get_element_attributes(element)

                element_info = {
                    'tag': tag_name,
                    'id': attrs.get('id'),
                    'class': attrs.get('class'),
                    'name': name_info.name,
                    'source': name_info.source
                }

                if name_info.source == 'none':
                    result['missing'].append(element_info)
                elif not name_info.name.strip():
                    result['empty'].append(element_info)
                else:
                    result['good'].append(element_info)

        return result

    async def get_accessible_name_from_ax_node(self, ax_node: AXNode) -> str:
        """
        Get accessible name directly from an AXNode.

        This is simpler than computing from DOM, as the browser has already
        computed the accessible name.

        Args:
            ax_node: AXNode from accessibility tree

        Returns:
            Accessible name
        """
        return ax_node.name or ''

    async def get_description_from_ax_node(self, ax_node: AXNode) -> str:
        """
        Get accessible description directly from an AXNode.

        Args:
            ax_node: AXNode from accessibility tree

        Returns:
            Accessible description
        """
        return ax_node.description or ''

    async def compare_computed_vs_browser(
        self,
        element: ElementHandle,
        ax_node: AXNode
    ) -> Dict[str, Any]:
        """
        Compare our computed accessible name with the browser's.

        Useful for debugging and validation.

        Args:
            element: ElementHandle
            ax_node: Corresponding AXNode

        Returns:
            Comparison dict with both names and whether they match
        """
        computed = await self.get_accessible_name(element)
        browser_name = ax_node.name or ''

        return {
            'computed_name': computed.name,
            'computed_source': computed.source,
            'browser_name': browser_name,
            'match': computed.name == browser_name,
            'difference': abs(len(computed.name) - len(browser_name))
        }
