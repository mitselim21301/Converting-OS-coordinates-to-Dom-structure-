#!/usr/bin/env python3
"""
Accessibility Module for MCP Accurate Click Server

This module provides comprehensive accessibility tree integration for
accurate element targeting and interaction in browser automation.

Features:
- Extract accessibility tree via Chrome DevTools Protocol
- Find elements by ARIA role and accessible name
- Compute accessible names according to ARIA specification
- Navigate accessibility tree relationships
- Map accessibility nodes to DOM elements via backendNodeId
- Support semantic element finding for robust automation

Usage:
    from mcp_server.accessibility import (
        AccessibilityTreeExtractor,
        RoleFinder,
        LabelResolver,
        AccessibilityNavigator,
        AXNode
    )

    # Extract accessibility tree
    extractor = AccessibilityTreeExtractor(page)
    await extractor.enable()

    # Find elements by role and name
    finder = RoleFinder(extractor)
    submit_button = await finder.find_one('button', 'Submit')

    # Navigate tree
    navigator = AccessibilityNavigator(extractor)
    parent = await navigator.get_parent(submit_button)

    # Resolve accessible names
    resolver = LabelResolver(page)
    name_info = await resolver.get_accessible_name(element)

References:
- ACCESSIBILITY_TREE_RESEARCH.md
- ACCESSIBILITY_TREE_FOR_CLICKING.md
- Chrome DevTools Protocol: https://chromedevtools.github.io/devtools-protocol/tot/Accessibility/
"""

from .tree_extractor import (
    AccessibilityTreeExtractor,
    AXNode
)

from .role_finder import (
    RoleFinder,
    RoleType,
    SearchCriteria
)

from .label_resolver import (
    LabelResolver,
    AccessibleNameInfo
)

from .navigator import (
    AccessibilityNavigator,
    TraversalOrder,
    TreePath
)

__all__ = [
    # Tree extraction
    'AccessibilityTreeExtractor',
    'AXNode',

    # Role finding
    'RoleFinder',
    'RoleType',
    'SearchCriteria',

    # Label resolution
    'LabelResolver',
    'AccessibleNameInfo',

    # Tree navigation
    'AccessibilityNavigator',
    'TraversalOrder',
    'TreePath',
]

__version__ = '1.0.0'
__author__ = 'MCP Accurate Click Server Team'
__description__ = 'Accessibility tree integration for browser automation'
