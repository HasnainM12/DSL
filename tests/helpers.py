"""Shared constants and helpers for the DSL test-suite."""


AVL_RULES = """\
IF balance_factor > 1 THEN ROTATE_RIGHT
IF balance_factor < -1 THEN ROTATE_LEFT
"""


def count_nodes(node):
    """Return the total number of nodes in the subtree rooted at *node*."""
    if node is None:
        return 0
    return 1 + count_nodes(node.left) + count_nodes(node.right)
