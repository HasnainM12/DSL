"""
rb_tree.py — Canonical Red-Black BST reference implementation.

This module provides a correct, textbook Red-Black tree with insertion
and fix-up, implemented purely in Python (no DSL involvement).  It is
used as a validation reference to verify the DSL-based Red-Black
rebalancing produces correct trees.

Red-Black invariants:
    1. Every node is RED or BLACK.
    2. The root is BLACK.
    3. No RED node has a RED child.
    4. Every root-to-leaf path has the same number of BLACK nodes.
"""

RED = "RED"
BLACK = "BLACK"


class RBNode:
    """A single node in the Red-Black tree."""

    __slots__ = ("val", "colour", "left", "right", "parent")

    def __init__(self, val, colour=RED, left=None, right=None, parent=None):
        self.val = val
        self.colour = colour
        self.left = left
        self.right = right
        self.parent = parent

    def __repr__(self):
        return f"RBNode({self.val}, {self.colour})"


class RBTree:
    """Canonical Red-Black BST with insertion + fix-up."""

    def __init__(self):
        # Sentinel NIL node — shared across the tree
        self.NIL = RBNode(val=None, colour=BLACK)
        self.root = self.NIL

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def insert(self, val):
        """Insert *val* into the tree and fix up Red-Black properties."""
        new_node = RBNode(val, colour=RED, left=self.NIL, right=self.NIL)

        # Standard BST insertion
        parent = None
        current = self.root
        while current is not self.NIL:
            parent = current
            if val < current.val:
                current = current.left
            elif val > current.val:
                current = current.right
            else:
                return  # duplicate — ignore

        new_node.parent = parent
        if parent is None:
            self.root = new_node
        elif val < parent.val:
            parent.left = new_node
        else:
            parent.right = new_node

        self._fix_insert(new_node)

    def inorder(self):
        """Return a sorted list of values via in-order traversal."""
        result = []
        self._inorder(self.root, result)
        return result

    # ------------------------------------------------------------------
    # Red-Black fix-up after insertion
    # ------------------------------------------------------------------

    def _fix_insert(self, node):
        """Restore Red-Black properties after inserting *node*."""
        while node is not self.root and node.parent.colour == RED:
            parent = node.parent
            grandparent = parent.parent

            if parent is grandparent.left:
                uncle = grandparent.right

                # Case 1: Uncle is RED — recolour
                if uncle.colour == RED:
                    parent.colour = BLACK
                    uncle.colour = BLACK
                    grandparent.colour = RED
                    node = grandparent  # propagate up
                else:
                    # Case 2: node is right child — rotate left at parent
                    if node is parent.right:
                        node = parent
                        self._rotate_left(node)
                        parent = node.parent
                        grandparent = parent.parent

                    # Case 3: node is left child — rotate right at grandparent
                    parent.colour = BLACK
                    grandparent.colour = RED
                    self._rotate_right(grandparent)
            else:
                # Mirror: parent is right child of grandparent
                uncle = grandparent.left

                # Case 1: Uncle is RED — recolour
                if uncle.colour == RED:
                    parent.colour = BLACK
                    uncle.colour = BLACK
                    grandparent.colour = RED
                    node = grandparent
                else:
                    # Case 2: node is left child — rotate right at parent
                    if node is parent.left:
                        node = parent
                        self._rotate_right(node)
                        parent = node.parent
                        grandparent = parent.parent

                    # Case 3: node is right child — rotate left at grandparent
                    parent.colour = BLACK
                    grandparent.colour = RED
                    self._rotate_left(grandparent)

        self.root.colour = BLACK

    # ------------------------------------------------------------------
    # Rotations
    # ------------------------------------------------------------------

    def _rotate_left(self, x):
        """Left rotation around node x."""
        y = x.right
        x.right = y.left
        if y.left is not self.NIL:
            y.left.parent = x

        y.parent = x.parent
        if x.parent is None:
            self.root = y
        elif x is x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y

        y.left = x
        x.parent = y

    def _rotate_right(self, x):
        """Right rotation around node x."""
        y = x.left
        x.left = y.right
        if y.right is not self.NIL:
            y.right.parent = x

        y.parent = x.parent
        if x.parent is None:
            self.root = y
        elif x is x.parent.right:
            x.parent.right = y
        else:
            x.parent.left = y

        y.right = x
        x.parent = y

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _inorder(self, node, result):
        if node is not self.NIL:
            self._inorder(node.left, result)
            result.append(node.val)
            self._inorder(node.right, result)

    # ------------------------------------------------------------------
    # Invariant checking (useful for tests)
    # ------------------------------------------------------------------

    def check_invariants(self):
        """Raise AssertionError if any Red-Black invariant is violated."""
        assert self.root.colour == BLACK, "Root must be BLACK"
        self._check_no_red_red(self.root)
        self._check_black_height(self.root)

    def _check_no_red_red(self, node):
        """Assert no RED node has a RED child."""
        if node is self.NIL:
            return
        if node.colour == RED:
            assert node.left.colour == BLACK, (
                f"RED-RED violation: {node.val} -> left child {node.left.val}"
            )
            assert node.right.colour == BLACK, (
                f"RED-RED violation: {node.val} -> right child {node.right.val}"
            )
        self._check_no_red_red(node.left)
        self._check_no_red_red(node.right)

    def _check_black_height(self, node):
        """Assert equal black-height on all root-to-leaf paths. Returns bh."""
        if node is self.NIL:
            return 1  # NIL nodes are BLACK
        left_bh = self._check_black_height(node.left)
        right_bh = self._check_black_height(node.right)
        assert left_bh == right_bh, (
            f"Black-height mismatch at node {node.val}: "
            f"left={left_bh}, right={right_bh}"
        )
        return left_bh + (1 if node.colour == BLACK else 0)
