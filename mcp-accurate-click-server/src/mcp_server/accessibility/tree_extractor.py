#!/usr/bin/env python3
"""
Accessibility Tree Extractor

Extracts the accessibility tree from a browser using Chrome DevTools Protocol (CDP).
Provides methods to get the full tree, partial trees, and query specific nodes.

References:
- Chrome DevTools Protocol Accessibility Domain: https://chromedevtools.github.io/devtools-protocol/tot/Accessibility/
- ACCESSIBILITY_TREE_RESEARCH.md
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from playwright.sync_api import CDPSession, Page


@dataclass
class AXNode:
    """
    Represents an accessibility node from the Chrome accessibility tree.

    Maps to the AXNode type from Chrome DevTools Protocol with additional
    convenience properties and methods.
    """
    # Core identifiers
    node_id: str
    backend_node_id: Optional[int] = None
    parent_id: Optional[str] = None
    child_ids: List[str] = field(default_factory=list)

    # Semantic properties
    role: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    value: Optional[str] = None

    # State properties
    disabled: bool = False
    hidden: bool = False
    focused: bool = False
    focusable: bool = False
    editable: bool = False
    busy: bool = False

    # Interactive state
    checked: Optional[str] = None  # "true", "false", "mixed"
    pressed: Optional[str] = None  # "true", "false", "mixed"
    selected: Optional[bool] = None
    expanded: Optional[bool] = None
    modal: Optional[bool] = None

    # Validation
    invalid: Optional[str] = None
    required: Optional[bool] = None
    readonly: Optional[bool] = None

    # Additional metadata
    level: Optional[int] = None  # Heading level or tree item depth
    orientation: Optional[str] = None  # "horizontal", "vertical"
    has_popup: Optional[str] = None
    autocomplete: Optional[str] = None
    key_shortcuts: Optional[str] = None
    role_description: Optional[str] = None

    # Live region properties
    live: Optional[str] = None
    atomic: Optional[bool] = None
    relevant: Optional[str] = None

    # Raw data from CDP
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_cdp(cls, node_data: Dict[str, Any]) -> 'AXNode':
        """
        Create an AXNode from Chrome DevTools Protocol node data.

        Args:
            node_data: Raw node data from CDP Accessibility domain

        Returns:
            AXNode instance
        """
        # Helper to extract value from CDP property format
        def get_value(data: Dict[str, Any], key: str, default: Any = None) -> Any:
            if key not in data:
                return default
            prop = data[key]
            if isinstance(prop, dict) and 'value' in prop:
                return prop['value']
            return prop

        # Extract role
        role = None
        if 'role' in node_data:
            role_data = node_data['role']
            if isinstance(role_data, dict):
                role = role_data.get('value')
            else:
                role = role_data

        # Extract name
        name = None
        if 'name' in node_data:
            name_data = node_data['name']
            if isinstance(name_data, dict):
                name = name_data.get('value')
            else:
                name = name_data

        return cls(
            node_id=node_data.get('nodeId', ''),
            backend_node_id=node_data.get('backendDOMNodeId'),
            parent_id=node_data.get('parentId'),
            child_ids=node_data.get('childIds', []),
            role=role,
            name=name,
            description=get_value(node_data, 'description'),
            value=get_value(node_data, 'value'),
            disabled=get_value(node_data, 'disabled', False),
            hidden=get_value(node_data, 'hidden', False),
            focused=get_value(node_data, 'focused', False),
            focusable=get_value(node_data, 'focusable', False),
            editable=get_value(node_data, 'editable', False),
            busy=get_value(node_data, 'busy', False),
            checked=get_value(node_data, 'checked'),
            pressed=get_value(node_data, 'pressed'),
            selected=get_value(node_data, 'selected'),
            expanded=get_value(node_data, 'expanded'),
            modal=get_value(node_data, 'modal'),
            invalid=get_value(node_data, 'invalid'),
            required=get_value(node_data, 'required'),
            readonly=get_value(node_data, 'readonly'),
            level=get_value(node_data, 'level'),
            orientation=get_value(node_data, 'orientation'),
            has_popup=get_value(node_data, 'haspopup'),
            autocomplete=get_value(node_data, 'autocomplete'),
            key_shortcuts=get_value(node_data, 'keyshortcuts'),
            role_description=get_value(node_data, 'roledescription'),
            live=get_value(node_data, 'live'),
            atomic=get_value(node_data, 'atomic'),
            relevant=get_value(node_data, 'relevant'),
            raw_data=node_data
        )

    def is_interactable(self) -> bool:
        """Check if this node is interactable (clickable, focusable, etc.)"""
        if self.disabled or self.hidden:
            return False

        # Common interactable roles
        interactable_roles = {
            'button', 'link', 'checkbox', 'radio', 'textbox', 'searchbox',
            'combobox', 'listbox', 'menuitem', 'menuitemcheckbox', 'menuitemradio',
            'option', 'slider', 'spinbutton', 'switch', 'tab', 'treeitem'
        }

        return (self.focusable or
                (self.role and self.role.lower() in interactable_roles))

    def __repr__(self) -> str:
        return f"AXNode(role={self.role}, name={self.name}, id={self.node_id})"


class AccessibilityTreeExtractor:
    """
    Extracts accessibility tree information from a browser using Chrome DevTools Protocol.

    This class provides methods to:
    - Enable/disable the accessibility domain
    - Extract full or partial accessibility trees
    - Query for specific nodes by role and name
    - Map between accessibility nodes and DOM elements

    Usage:
        extractor = AccessibilityTreeExtractor(page)
        await extractor.enable()
        root = await extractor.get_root_node()
        nodes = await extractor.query_tree(role='button', name='Submit')
        await extractor.disable()
    """

    def __init__(self, page: Page):
        """
        Initialize the extractor.

        Args:
            page: Playwright Page instance
        """
        self.page = page
        self._cdp_session: Optional[CDPSession] = None
        self._enabled = False

    async def _get_cdp_session(self) -> CDPSession:
        """Get or create CDP session"""
        if self._cdp_session is None:
            self._cdp_session = await self.page.context.new_cdp_session(self.page)
        return self._cdp_session

    async def enable(self) -> None:
        """
        Enable the accessibility domain.

        This must be called before using other methods. It makes AXNodeIds
        consistent between method calls.

        Note: Enabling accessibility can impact page performance.
        """
        if self._enabled:
            return

        cdp = await self._get_cdp_session()
        await cdp.send('Accessibility.enable')
        self._enabled = True

    async def disable(self) -> None:
        """
        Disable the accessibility domain and release resources.
        """
        if not self._enabled:
            return

        cdp = await self._get_cdp_session()
        await cdp.send('Accessibility.disable')
        self._enabled = False

    async def get_root_node(self, frame_id: Optional[str] = None) -> AXNode:
        """
        Get the root accessibility node for a frame.

        Args:
            frame_id: Optional frame ID (uses main frame if not specified)

        Returns:
            Root AXNode

        Raises:
            RuntimeError: If accessibility domain is not enabled
        """
        if not self._enabled:
            raise RuntimeError("Accessibility domain not enabled. Call enable() first.")

        cdp = await self._get_cdp_session()

        params = {}
        if frame_id:
            params['frameId'] = frame_id

        result = await cdp.send('Accessibility.getRootAXNode', params)
        return AXNode.from_cdp(result['node'])

    async def get_full_tree(
        self,
        depth: Optional[int] = None,
        frame_id: Optional[str] = None
    ) -> List[AXNode]:
        """
        Get the full accessibility tree.

        Warning: This can be expensive on large pages.

        Args:
            depth: Maximum depth to traverse (optional)
            frame_id: Frame ID (optional, uses main frame if not specified)

        Returns:
            List of all AXNodes in the tree
        """
        if not self._enabled:
            raise RuntimeError("Accessibility domain not enabled. Call enable() first.")

        cdp = await self._get_cdp_session()

        params = {}
        if depth is not None:
            params['depth'] = depth
        if frame_id:
            params['frameId'] = frame_id

        result = await cdp.send('Accessibility.getFullAXTree', params)
        return [AXNode.from_cdp(node) for node in result.get('nodes', [])]

    async def get_partial_tree(
        self,
        backend_node_id: Optional[int] = None,
        node_id: Optional[str] = None,
        object_id: Optional[str] = None,
        fetch_relatives: bool = True
    ) -> List[AXNode]:
        """
        Get a partial accessibility tree for a specific DOM node.

        Provide exactly one of: backend_node_id, node_id, or object_id.

        Args:
            backend_node_id: Backend DOM node ID
            node_id: DOM node ID
            object_id: JavaScript object ID
            fetch_relatives: Whether to fetch ancestors (default True)

        Returns:
            List of AXNodes (target node and optionally its ancestors)
        """
        if not self._enabled:
            raise RuntimeError("Accessibility domain not enabled. Call enable() first.")

        cdp = await self._get_cdp_session()

        params = {'fetchRelatives': fetch_relatives}

        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        elif node_id is not None:
            params['nodeId'] = node_id
        elif object_id is not None:
            params['objectId'] = object_id
        else:
            raise ValueError("Must provide backend_node_id, node_id, or object_id")

        result = await cdp.send('Accessibility.getPartialAXTree', params)
        return [AXNode.from_cdp(node) for node in result.get('nodes', [])]

    async def get_child_nodes(self, node_id: str, frame_id: Optional[str] = None) -> List[AXNode]:
        """
        Get child nodes of an accessibility node.

        Args:
            node_id: Parent node ID
            frame_id: Optional frame ID

        Returns:
            List of child AXNodes
        """
        if not self._enabled:
            raise RuntimeError("Accessibility domain not enabled. Call enable() first.")

        cdp = await self._get_cdp_session()

        params = {'id': node_id}
        if frame_id:
            params['frameId'] = frame_id

        result = await cdp.send('Accessibility.getChildAXNodes', params)
        return [AXNode.from_cdp(node) for node in result.get('nodes', [])]

    async def query_tree(
        self,
        role: Optional[str] = None,
        name: Optional[str] = None,
        backend_node_id: Optional[int] = None,
        node_id: Optional[str] = None,
        object_id: Optional[str] = None
    ) -> List[AXNode]:
        """
        Query the accessibility tree for nodes matching criteria.

        Can search the entire tree or a subtree starting from a specific node.

        Args:
            role: ARIA role to match (e.g., 'button', 'link')
            name: Accessible name to match
            backend_node_id: Start search from this backend node ID (optional)
            node_id: Start search from this DOM node ID (optional)
            object_id: Start search from this object ID (optional)

        Returns:
            List of matching AXNodes
        """
        if not self._enabled:
            raise RuntimeError("Accessibility domain not enabled. Call enable() first.")

        cdp = await self._get_cdp_session()

        params = {}

        # Add search criteria
        if role:
            params['role'] = role
        if name:
            params['accessibleName'] = name

        # Add starting node if specified
        if backend_node_id is not None:
            params['backendNodeId'] = backend_node_id
        elif node_id is not None:
            params['nodeId'] = node_id
        elif object_id is not None:
            params['objectId'] = object_id

        result = await cdp.send('Accessibility.queryAXTree', params)
        return [AXNode.from_cdp(node) for node in result.get('nodes', [])]

    async def get_node_for_backend_id(self, backend_node_id: int) -> Optional[AXNode]:
        """
        Get the accessibility node for a specific backend DOM node ID.

        Args:
            backend_node_id: Backend DOM node ID

        Returns:
            AXNode if found, None otherwise
        """
        nodes = await self.get_partial_tree(
            backend_node_id=backend_node_id,
            fetch_relatives=False
        )
        return nodes[0] if nodes else None

    async def get_node_at_coordinates(self, x: float, y: float) -> Optional[AXNode]:
        """
        Get the accessibility node at specific viewport coordinates.

        This first finds the DOM element at the coordinates, then gets its
        accessibility representation.

        Args:
            x: Viewport X coordinate
            y: Viewport Y coordinate

        Returns:
            AXNode at coordinates, or None if not found
        """
        if not self._enabled:
            raise RuntimeError("Accessibility domain not enabled. Call enable() first.")

        cdp = await self._get_cdp_session()

        # Enable DOM domain if not already enabled
        await cdp.send('DOM.enable')

        try:
            # Find DOM node at coordinates
            result = await cdp.send('DOM.getNodeForLocation', {
                'x': int(x),
                'y': int(y),
                'includeUserAgentShadowDOM': False,
                'ignorePointerEventsNone': False
            })

            backend_node_id = result.get('backendNodeId')
            if not backend_node_id:
                return None

            # Get accessibility node for that DOM node
            return await self.get_node_for_backend_id(backend_node_id)

        except Exception as e:
            # Node might not exist or be hidden
            return None

    def __enter__(self):
        """Context manager support (sync version not recommended)"""
        raise NotImplementedError("Use async context manager: async with extractor")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.enable()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disable()
        return False
