#!/usr/bin/env python3
"""
ARIA Role Finder

Finds elements by their ARIA role and accessible name using the accessibility tree.
This provides the most robust way to locate elements for automation.

References:
- W3C ARIA Specification: https://w3c.github.io/aria/
- ACCESSIBILITY_TREE_FOR_CLICKING.md
"""

from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum

from .tree_extractor import AccessibilityTreeExtractor, AXNode


class RoleType(Enum):
    """
    Common ARIA roles for element targeting.

    See: https://www.w3.org/TR/wai-aria-1.2/#role_definitions
    """
    # Widget roles
    BUTTON = "button"
    CHECKBOX = "checkbox"
    LINK = "link"
    MENUITEM = "menuitem"
    MENUITEMCHECKBOX = "menuitemcheckbox"
    MENUITEMRADIO = "menuitemradio"
    OPTION = "option"
    RADIO = "radio"
    SEARCHBOX = "searchbox"
    SLIDER = "slider"
    SPINBUTTON = "spinbutton"
    SWITCH = "switch"
    TAB = "tab"
    TABPANEL = "tabpanel"
    TEXTBOX = "textbox"
    COMBOBOX = "combobox"

    # Composite roles
    GRID = "grid"
    LISTBOX = "listbox"
    MENU = "menu"
    MENUBAR = "menubar"
    RADIOGROUP = "radiogroup"
    TABLIST = "tablist"
    TREE = "tree"
    TREEGRID = "treegrid"

    # Document structure
    ARTICLE = "article"
    DEFINITION = "definition"
    DIRECTORY = "directory"
    DOCUMENT = "document"
    FEED = "feed"
    FIGURE = "figure"
    GROUP = "group"
    HEADING = "heading"
    IMG = "img"
    LIST = "list"
    LISTITEM = "listitem"
    MATH = "math"
    NOTE = "note"
    PRESENTATION = "presentation"
    REGION = "region"
    SEPARATOR = "separator"
    TABLE = "table"
    TERM = "term"
    TOOLBAR = "toolbar"
    TOOLTIP = "tooltip"

    # Landmark roles
    BANNER = "banner"
    COMPLEMENTARY = "complementary"
    CONTENTINFO = "contentinfo"
    FORM = "form"
    MAIN = "main"
    NAVIGATION = "navigation"
    SEARCH = "search"

    # Live region roles
    ALERT = "alert"
    LOG = "log"
    MARQUEE = "marquee"
    STATUS = "status"
    TIMER = "timer"

    # Window roles
    ALERTDIALOG = "alertdialog"
    DIALOG = "dialog"


@dataclass
class SearchCriteria:
    """Criteria for finding elements by accessibility properties"""
    role: Optional[str] = None
    name: Optional[str] = None
    name_contains: Optional[str] = None
    name_matches: Optional[Callable[[str], bool]] = None
    description: Optional[str] = None
    description_contains: Optional[str] = None

    # State filters
    disabled: Optional[bool] = None
    hidden: Optional[bool] = None
    focusable: Optional[bool] = None
    checked: Optional[str] = None  # "true", "false", "mixed"
    pressed: Optional[str] = None
    expanded: Optional[bool] = None
    selected: Optional[bool] = None

    # Additional filters
    level: Optional[int] = None  # For headings
    has_backend_node: bool = True  # Exclude virtual nodes by default

    def matches(self, node: AXNode) -> bool:
        """
        Check if a node matches these search criteria.

        Args:
            node: AXNode to check

        Returns:
            True if node matches all specified criteria
        """
        # Role check
        if self.role is not None:
            if node.role is None or node.role.lower() != self.role.lower():
                return False

        # Name checks
        if self.name is not None:
            if node.name != self.name:
                return False

        if self.name_contains is not None:
            if not node.name or self.name_contains.lower() not in node.name.lower():
                return False

        if self.name_matches is not None:
            if not node.name or not self.name_matches(node.name):
                return False

        # Description checks
        if self.description is not None:
            if node.description != self.description:
                return False

        if self.description_contains is not None:
            if not node.description or self.description_contains.lower() not in node.description.lower():
                return False

        # State checks
        if self.disabled is not None and node.disabled != self.disabled:
            return False

        if self.hidden is not None and node.hidden != self.hidden:
            return False

        if self.focusable is not None and node.focusable != self.focusable:
            return False

        if self.checked is not None and node.checked != self.checked:
            return False

        if self.pressed is not None and node.pressed != self.pressed:
            return False

        if self.expanded is not None and node.expanded != self.expanded:
            return False

        if self.selected is not None and node.selected != self.selected:
            return False

        # Additional checks
        if self.level is not None and node.level != self.level:
            return False

        if self.has_backend_node and node.backend_node_id is None:
            return False

        return True


class RoleFinder:
    """
    Find elements by ARIA role and accessible name.

    This is the most robust strategy for element targeting, as ARIA attributes
    are semantic and less likely to change than CSS classes or DOM structure.

    Usage:
        finder = RoleFinder(extractor)
        buttons = await finder.find_by_role('button')
        submit = await finder.find_by_role_and_name('button', 'Submit')
        checkboxes = await finder.find_interactable('checkbox')
    """

    def __init__(self, extractor: AccessibilityTreeExtractor):
        """
        Initialize the finder.

        Args:
            extractor: AccessibilityTreeExtractor instance
        """
        self.extractor = extractor

    async def find_by_role(
        self,
        role: str,
        include_hidden: bool = False,
        include_disabled: bool = False
    ) -> List[AXNode]:
        """
        Find all elements with a specific ARIA role.

        Args:
            role: ARIA role (e.g., 'button', 'link', 'checkbox')
            include_hidden: Include hidden elements
            include_disabled: Include disabled elements

        Returns:
            List of matching AXNodes
        """
        nodes = await self.extractor.query_tree(role=role)

        if not include_hidden:
            nodes = [n for n in nodes if not n.hidden]

        if not include_disabled:
            nodes = [n for n in nodes if not n.disabled]

        return nodes

    async def find_by_role_and_name(
        self,
        role: str,
        name: str,
        exact_match: bool = True,
        include_hidden: bool = False,
        include_disabled: bool = False
    ) -> List[AXNode]:
        """
        Find elements by ARIA role and accessible name.

        This is the recommended approach for robust element targeting.

        Args:
            role: ARIA role
            name: Accessible name
            exact_match: Whether to match name exactly (vs. contains)
            include_hidden: Include hidden elements
            include_disabled: Include disabled elements

        Returns:
            List of matching AXNodes
        """
        if exact_match:
            # Use CDP query for exact match (more efficient)
            nodes = await self.extractor.query_tree(role=role, name=name)

            if not include_hidden:
                nodes = [n for n in nodes if not n.hidden]

            if not include_disabled:
                nodes = [n for n in nodes if not n.disabled]

            return nodes
        else:
            # Get all with role, then filter by name contains
            nodes = await self.find_by_role(
                role=role,
                include_hidden=include_hidden,
                include_disabled=include_disabled
            )

            return [
                n for n in nodes
                if n.name and name.lower() in n.name.lower()
            ]

    async def find_one(
        self,
        role: str,
        name: Optional[str] = None,
        exact_match: bool = True
    ) -> Optional[AXNode]:
        """
        Find a single element by role and optionally name.

        Returns the first matching element, or None if not found.

        Args:
            role: ARIA role
            name: Accessible name (optional)
            exact_match: Whether to match name exactly

        Returns:
            First matching AXNode, or None
        """
        if name:
            nodes = await self.find_by_role_and_name(
                role=role,
                name=name,
                exact_match=exact_match,
                include_hidden=False,
                include_disabled=False
            )
        else:
            nodes = await self.find_by_role(
                role=role,
                include_hidden=False,
                include_disabled=False
            )

        return nodes[0] if nodes else None

    async def find_interactable(
        self,
        role: Optional[str] = None
    ) -> List[AXNode]:
        """
        Find all interactable elements (clickable, focusable, etc.).

        Args:
            role: Optional role filter

        Returns:
            List of interactable AXNodes
        """
        if role:
            nodes = await self.find_by_role(role, include_hidden=False, include_disabled=False)
        else:
            # Get full tree and filter
            all_nodes = await self.extractor.get_full_tree()
            nodes = [n for n in all_nodes if not n.hidden and not n.disabled]

        return [n for n in nodes if n.is_interactable()]

    async def find_by_criteria(self, criteria: SearchCriteria) -> List[AXNode]:
        """
        Find elements matching complex search criteria.

        This allows for flexible, multi-attribute searches.

        Args:
            criteria: SearchCriteria instance

        Returns:
            List of matching AXNodes

        Example:
            criteria = SearchCriteria(
                role='button',
                name_contains='submit',
                disabled=False,
                focusable=True
            )
            buttons = await finder.find_by_criteria(criteria)
        """
        # Start with role-based query if specified
        if criteria.role:
            nodes = await self.extractor.query_tree(role=criteria.role)
        else:
            # Get all nodes
            nodes = await self.extractor.get_full_tree()

        # Filter by criteria
        return [n for n in nodes if criteria.matches(n)]

    async def find_buttons_by_text(self, text: str, exact: bool = False) -> List[AXNode]:
        """
        Convenience method to find buttons by their text.

        Args:
            text: Button text to search for
            exact: Whether to match exactly

        Returns:
            List of button AXNodes
        """
        return await self.find_by_role_and_name(
            role='button',
            name=text,
            exact_match=exact
        )

    async def find_links_by_text(self, text: str, exact: bool = False) -> List[AXNode]:
        """
        Convenience method to find links by their text.

        Args:
            text: Link text to search for
            exact: Whether to match exactly

        Returns:
            List of link AXNodes
        """
        return await self.find_by_role_and_name(
            role='link',
            name=text,
            exact_match=exact
        )

    async def find_headings(self, level: Optional[int] = None, text: Optional[str] = None) -> List[AXNode]:
        """
        Find heading elements, optionally filtered by level and text.

        Args:
            level: Heading level (1-6)
            text: Heading text to search for

        Returns:
            List of heading AXNodes
        """
        criteria = SearchCriteria(
            role='heading',
            level=level
        )

        if text:
            criteria.name_contains = text

        return await self.find_by_criteria(criteria)

    async def find_textboxes(self, placeholder: Optional[str] = None) -> List[AXNode]:
        """
        Find text input fields.

        Args:
            placeholder: Filter by placeholder text (searches in name/description)

        Returns:
            List of textbox AXNodes
        """
        nodes = await self.find_by_role('textbox')

        if placeholder:
            nodes = [
                n for n in nodes
                if (n.name and placeholder.lower() in n.name.lower()) or
                   (n.description and placeholder.lower() in n.description.lower())
            ]

        return nodes

    async def find_checked_items(self, role: Optional[str] = None) -> List[AXNode]:
        """
        Find checked checkboxes, radio buttons, or menu items.

        Args:
            role: Optional role filter (checkbox, radio, menuitemcheckbox, etc.)

        Returns:
            List of checked AXNodes
        """
        criteria = SearchCriteria(
            role=role,
            checked="true"
        )
        return await self.find_by_criteria(criteria)

    async def find_expanded_items(self, role: Optional[str] = None) -> List[AXNode]:
        """
        Find expanded elements (menus, accordions, etc.).

        Args:
            role: Optional role filter

        Returns:
            List of expanded AXNodes
        """
        criteria = SearchCriteria(
            role=role,
            expanded=True
        )
        return await self.find_by_criteria(criteria)

    async def verify_element_exists(
        self,
        role: str,
        name: str,
        timeout_ms: int = 5000
    ) -> bool:
        """
        Verify that an element with the given role and name exists.

        Useful for assertions and validation.

        Args:
            role: ARIA role
            name: Accessible name
            timeout_ms: Maximum time to wait (default 5000ms)

        Returns:
            True if element found, False otherwise
        """
        import asyncio

        start_time = asyncio.get_event_loop().time()
        end_time = start_time + (timeout_ms / 1000)

        while asyncio.get_event_loop().time() < end_time:
            node = await self.find_one(role=role, name=name)
            if node:
                return True

            # Wait a bit before retrying
            await asyncio.sleep(0.1)

        return False

    async def get_element_state(self, role: str, name: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of an element.

        Args:
            role: ARIA role
            name: Accessible name

        Returns:
            Dictionary with element state, or None if not found
        """
        node = await self.find_one(role=role, name=name)
        if not node:
            return None

        return {
            'role': node.role,
            'name': node.name,
            'disabled': node.disabled,
            'hidden': node.hidden,
            'focused': node.focused,
            'focusable': node.focusable,
            'checked': node.checked,
            'pressed': node.pressed,
            'selected': node.selected,
            'expanded': node.expanded,
            'value': node.value,
            'backend_node_id': node.backend_node_id
        }
