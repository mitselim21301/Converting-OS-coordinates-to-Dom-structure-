#!/usr/bin/env python3
"""
Accessibility Tree Navigator

Provides methods to navigate and traverse the accessibility tree,
including parent-child relationships, siblings, and tree walking.

References:
- ACCESSIBILITY_TREE_RESEARCH.md
- Chrome DevTools Protocol Accessibility Domain
"""

from typing import List, Optional, Dict, Callable, Any
from dataclasses import dataclass
from enum import Enum

from .tree_extractor import AccessibilityTreeExtractor, AXNode


class TraversalOrder(Enum):
    """Order for tree traversal"""
    PRE_ORDER = "pre_order"      # Parent before children
    POST_ORDER = "post_order"    # Children before parent
    LEVEL_ORDER = "level_order"  # Breadth-first


@dataclass
class TreePath:
    """Represents a path through the accessibility tree"""
    nodes: List[AXNode]

    @property
    def depth(self) -> int:
        """Get the depth of this path"""
        return len(self.nodes)

    @property
    def leaf(self) -> AXNode:
        """Get the leaf node of this path"""
        return self.nodes[-1] if self.nodes else None

    @property
    def root(self) -> AXNode:
        """Get the root node of this path"""
        return self.nodes[0] if self.nodes else None

    def to_string(self) -> str:
        """Get a string representation of the path"""
        return ' > '.join([
            f"{n.role or 'unknown'}:{n.name or 'unnamed'}"
            for n in self.nodes
        ])


class AccessibilityNavigator:
    """
    Navigate and traverse the accessibility tree.

    Provides methods to:
    - Walk parent-child relationships
    - Find siblings
    - Traverse tree in different orders
    - Get paths from root to specific nodes
    - Find common ancestors

    Usage:
        navigator = AccessibilityNavigator(extractor)
        parent = await navigator.get_parent(node)
        siblings = await navigator.get_siblings(node)
        path = await navigator.get_path_to_node(node)
    """

    def __init__(self, extractor: AccessibilityTreeExtractor):
        """
        Initialize the navigator.

        Args:
            extractor: AccessibilityTreeExtractor instance
        """
        self.extractor = extractor
        self._node_cache: Dict[str, AXNode] = {}

    async def _build_node_cache(self) -> None:
        """Build a cache of all nodes in the tree"""
        nodes = await self.extractor.get_full_tree()
        self._node_cache = {node.node_id: node for node in nodes}

    async def _ensure_cache(self) -> None:
        """Ensure node cache is populated"""
        if not self._node_cache:
            await self._build_node_cache()

    def clear_cache(self) -> None:
        """Clear the node cache (call after tree changes)"""
        self._node_cache.clear()

    async def get_node_by_id(self, node_id: str) -> Optional[AXNode]:
        """
        Get a node by its ID.

        Args:
            node_id: Node ID

        Returns:
            AXNode if found, None otherwise
        """
        await self._ensure_cache()
        return self._node_cache.get(node_id)

    async def get_parent(self, node: AXNode) -> Optional[AXNode]:
        """
        Get the parent of a node.

        Args:
            node: AXNode

        Returns:
            Parent AXNode, or None if at root
        """
        if not node.parent_id:
            return None

        return await self.get_node_by_id(node.parent_id)

    async def get_children(self, node: AXNode) -> List[AXNode]:
        """
        Get the children of a node.

        Args:
            node: AXNode

        Returns:
            List of child AXNodes
        """
        if not node.child_ids:
            return []

        # Try to get from cache first
        await self._ensure_cache()
        children = []

        for child_id in node.child_ids:
            child = self._node_cache.get(child_id)
            if child:
                children.append(child)

        # If cache didn't have all children, fetch them directly
        if len(children) != len(node.child_ids):
            children = await self.extractor.get_child_nodes(node.node_id)

        return children

    async def get_siblings(self, node: AXNode, include_self: bool = False) -> List[AXNode]:
        """
        Get the siblings of a node.

        Args:
            node: AXNode
            include_self: Whether to include the node itself

        Returns:
            List of sibling AXNodes
        """
        parent = await self.get_parent(node)
        if not parent:
            return [node] if include_self else []

        siblings = await self.get_children(parent)

        if not include_self:
            siblings = [s for s in siblings if s.node_id != node.node_id]

        return siblings

    async def get_previous_sibling(self, node: AXNode) -> Optional[AXNode]:
        """
        Get the previous sibling of a node.

        Args:
            node: AXNode

        Returns:
            Previous sibling, or None
        """
        siblings = await self.get_siblings(node, include_self=True)

        for i, sibling in enumerate(siblings):
            if sibling.node_id == node.node_id and i > 0:
                return siblings[i - 1]

        return None

    async def get_next_sibling(self, node: AXNode) -> Optional[AXNode]:
        """
        Get the next sibling of a node.

        Args:
            node: AXNode

        Returns:
            Next sibling, or None
        """
        siblings = await self.get_siblings(node, include_self=True)

        for i, sibling in enumerate(siblings):
            if sibling.node_id == node.node_id and i < len(siblings) - 1:
                return siblings[i + 1]

        return None

    async def get_ancestors(self, node: AXNode) -> List[AXNode]:
        """
        Get all ancestors of a node, from parent to root.

        Args:
            node: AXNode

        Returns:
            List of ancestor AXNodes (parent first, root last)
        """
        ancestors = []
        current = node

        while True:
            parent = await self.get_parent(current)
            if not parent:
                break
            ancestors.append(parent)
            current = parent

        return ancestors

    async def get_path_to_node(self, node: AXNode) -> TreePath:
        """
        Get the path from root to a specific node.

        Args:
            node: Target AXNode

        Returns:
            TreePath from root to node
        """
        ancestors = await self.get_ancestors(node)
        ancestors.reverse()  # Root first
        ancestors.append(node)  # Add target node at end

        return TreePath(nodes=ancestors)

    async def get_common_ancestor(self, node1: AXNode, node2: AXNode) -> Optional[AXNode]:
        """
        Find the lowest common ancestor of two nodes.

        Args:
            node1: First AXNode
            node2: Second AXNode

        Returns:
            Common ancestor AXNode, or None
        """
        path1 = await self.get_path_to_node(node1)
        path2 = await self.get_path_to_node(node2)

        # Find last common node in paths
        common = None
        for n1, n2 in zip(path1.nodes, path2.nodes):
            if n1.node_id == n2.node_id:
                common = n1
            else:
                break

        return common

    async def get_descendants(
        self,
        node: AXNode,
        max_depth: Optional[int] = None,
        filter_fn: Optional[Callable[[AXNode], bool]] = None
    ) -> List[AXNode]:
        """
        Get all descendants of a node.

        Args:
            node: Root AXNode
            max_depth: Maximum depth to traverse (None = unlimited)
            filter_fn: Optional filter function

        Returns:
            List of descendant AXNodes
        """
        descendants = []

        async def traverse(current: AXNode, depth: int):
            if max_depth is not None and depth > max_depth:
                return

            children = await self.get_children(current)
            for child in children:
                if filter_fn is None or filter_fn(child):
                    descendants.append(child)
                await traverse(child, depth + 1)

        await traverse(node, 0)
        return descendants

    async def traverse(
        self,
        node: AXNode,
        order: TraversalOrder = TraversalOrder.PRE_ORDER,
        filter_fn: Optional[Callable[[AXNode], bool]] = None
    ) -> List[AXNode]:
        """
        Traverse the tree starting from a node.

        Args:
            node: Starting AXNode
            order: Traversal order (pre-order, post-order, level-order)
            filter_fn: Optional filter function

        Returns:
            List of AXNodes in traversal order
        """
        if order == TraversalOrder.PRE_ORDER:
            return await self._traverse_pre_order(node, filter_fn)
        elif order == TraversalOrder.POST_ORDER:
            return await self._traverse_post_order(node, filter_fn)
        elif order == TraversalOrder.LEVEL_ORDER:
            return await self._traverse_level_order(node, filter_fn)
        else:
            raise ValueError(f"Unknown traversal order: {order}")

    async def _traverse_pre_order(
        self,
        node: AXNode,
        filter_fn: Optional[Callable[[AXNode], bool]]
    ) -> List[AXNode]:
        """Pre-order traversal (parent before children)"""
        result = []

        if filter_fn is None or filter_fn(node):
            result.append(node)

        children = await self.get_children(node)
        for child in children:
            result.extend(await self._traverse_pre_order(child, filter_fn))

        return result

    async def _traverse_post_order(
        self,
        node: AXNode,
        filter_fn: Optional[Callable[[AXNode], bool]]
    ) -> List[AXNode]:
        """Post-order traversal (children before parent)"""
        result = []

        children = await self.get_children(node)
        for child in children:
            result.extend(await self._traverse_post_order(child, filter_fn))

        if filter_fn is None or filter_fn(node):
            result.append(node)

        return result

    async def _traverse_level_order(
        self,
        node: AXNode,
        filter_fn: Optional[Callable[[AXNode], bool]]
    ) -> List[AXNode]:
        """Level-order traversal (breadth-first)"""
        result = []
        queue = [node]

        while queue:
            current = queue.pop(0)

            if filter_fn is None or filter_fn(current):
                result.append(current)

            children = await self.get_children(current)
            queue.extend(children)

        return result

    async def find_in_subtree(
        self,
        root: AXNode,
        role: Optional[str] = None,
        name: Optional[str] = None,
        filter_fn: Optional[Callable[[AXNode], bool]] = None
    ) -> List[AXNode]:
        """
        Find nodes in a subtree matching criteria.

        Args:
            root: Root of subtree to search
            role: ARIA role to match
            name: Accessible name to match
            filter_fn: Additional filter function

        Returns:
            List of matching AXNodes
        """
        def combined_filter(node: AXNode) -> bool:
            # Check role
            if role and (not node.role or node.role.lower() != role.lower()):
                return False

            # Check name
            if name and node.name != name:
                return False

            # Check custom filter
            if filter_fn and not filter_fn(node):
                return False

            return True

        return await self._traverse_pre_order(root, combined_filter)

    async def get_interactable_descendants(self, node: AXNode) -> List[AXNode]:
        """
        Get all interactable descendants of a node.

        Args:
            node: Root AXNode

        Returns:
            List of interactable descendant AXNodes
        """
        return await self.get_descendants(
            node,
            filter_fn=lambda n: n.is_interactable()
        )

    async def get_visible_descendants(self, node: AXNode) -> List[AXNode]:
        """
        Get all visible (non-hidden) descendants of a node.

        Args:
            node: Root AXNode

        Returns:
            List of visible descendant AXNodes
        """
        return await self.get_descendants(
            node,
            filter_fn=lambda n: not n.hidden
        )

    async def get_depth(self, node: AXNode) -> int:
        """
        Get the depth of a node in the tree (root = 0).

        Args:
            node: AXNode

        Returns:
            Depth as integer
        """
        path = await self.get_path_to_node(node)
        return path.depth - 1  # Subtract 1 because path includes the node itself

    async def is_ancestor_of(self, potential_ancestor: AXNode, node: AXNode) -> bool:
        """
        Check if one node is an ancestor of another.

        Args:
            potential_ancestor: Potential ancestor AXNode
            node: Target AXNode

        Returns:
            True if potential_ancestor is an ancestor of node
        """
        ancestors = await self.get_ancestors(node)
        return any(a.node_id == potential_ancestor.node_id for a in ancestors)

    async def is_descendant_of(self, potential_descendant: AXNode, node: AXNode) -> bool:
        """
        Check if one node is a descendant of another.

        Args:
            potential_descendant: Potential descendant AXNode
            node: Target AXNode

        Returns:
            True if potential_descendant is a descendant of node
        """
        return await self.is_ancestor_of(node, potential_descendant)

    async def get_tree_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the accessibility tree.

        Returns:
            Dictionary with tree statistics
        """
        await self._ensure_cache()

        total_nodes = len(self._node_cache)
        roles = {}
        interactable = 0
        hidden = 0
        disabled = 0
        with_backend_node = 0

        for node in self._node_cache.values():
            # Count by role
            role = node.role or 'unknown'
            roles[role] = roles.get(role, 0) + 1

            # Count states
            if node.is_interactable():
                interactable += 1
            if node.hidden:
                hidden += 1
            if node.disabled:
                disabled += 1
            if node.backend_node_id is not None:
                with_backend_node += 1

        return {
            'total_nodes': total_nodes,
            'roles': roles,
            'interactable_count': interactable,
            'hidden_count': hidden,
            'disabled_count': disabled,
            'with_backend_node': with_backend_node,
            'virtual_nodes': total_nodes - with_backend_node
        }

    async def print_tree(
        self,
        node: Optional[AXNode] = None,
        max_depth: int = 5,
        show_ids: bool = False
    ) -> str:
        """
        Print a visual representation of the tree.

        Args:
            node: Starting node (uses root if None)
            max_depth: Maximum depth to print
            show_ids: Whether to show node IDs

        Returns:
            String representation of tree
        """
        if node is None:
            node = await self.extractor.get_root_node()

        lines = []

        async def print_node(n: AXNode, depth: int, prefix: str):
            if depth > max_depth:
                return

            # Build node description
            role = n.role or 'unknown'
            name = n.name or ''
            desc = f"{role}"

            if name:
                desc += f' "{name}"'

            if show_ids:
                desc += f" (id: {n.node_id})"

            if n.hidden:
                desc += " [hidden]"
            if n.disabled:
                desc += " [disabled]"

            lines.append(f"{prefix}{desc}")

            # Print children
            children = await self.get_children(n)
            for i, child in enumerate(children):
                is_last = i == len(children) - 1
                child_prefix = prefix + ("└── " if is_last else "├── ")
                continuation = prefix + ("    " if is_last else "│   ")

                await print_node(child, depth + 1, child_prefix)

        await print_node(node, 0, "")
        return '\n'.join(lines)
