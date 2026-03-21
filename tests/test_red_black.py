"""Tests for Red-Black tree — DSL-based and native reference implementation.

Validates Red-Black invariants after insertion:
  1. Root is BLACK
  2. No two consecutive RED nodes (no RED-RED parent-child)
  3. Equal black-height on all root-to-leaf paths
"""
import os
import pytest
from tree import BST, TreeNode
from interpreter import DSLInterpreter
from rb_tree import RBTree


# ============================================================
# Helpers — Red-Black invariant checkers (for DSL-produced trees)
# ============================================================

def _assert_root_is_black(root):
    """Root must be BLACK."""
    assert root is None or root.colour == "BLACK", (
        f"Root {root.val} is {root.colour}, expected BLACK"
    )


def _check_no_red_red(node):
    """No RED node may have a RED child."""
    if node is None:
        return
    if node.colour == "RED":
        if node.left:
            assert node.left.colour != "RED", (
                f"RED-RED: {node.val} (RED) -> left child {node.left.val} (RED)"
            )
        if node.right:
            assert node.right.colour != "RED", (
                f"RED-RED: {node.val} (RED) -> right child {node.right.val} (RED)"
            )
    _check_no_red_red(node.left)
    _check_no_red_red(node.right)


def _black_height(node):
    """Return the black-height of the subtree, asserting consistency."""
    if node is None:
        return 1  # NIL counts as BLACK
    left_bh = _black_height(node.left)
    right_bh = _black_height(node.right)
    assert left_bh == right_bh, (
        f"Black-height mismatch at node {node.val}: left={left_bh}, right={right_bh}"
    )
    return left_bh + (1 if node.colour == "BLACK" else 0)


def assert_rb_invariants(root):
    """Check all three Red-Black invariants on a DSL-produced BST."""
    _assert_root_is_black(root)
    _check_no_red_red(root)
    _black_height(root)


def _inorder(node):
    """Collect in-order values from a BST subtree."""
    if node is None:
        return []
    return _inorder(node.left) + [node.val] + _inorder(node.right)


# ============================================================
# RB DSL Script fixture
# ============================================================

@pytest.fixture
def rb_dsl():
    """Load the red-black.dsl script."""
    dsl_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'red-black.dsl')
    with open(dsl_path) as f:
        return f.read()


@pytest.fixture
def interpreter():
    return DSLInterpreter()


# ============================================================
# Native RBTree reference implementation tests
# ============================================================

class TestNativeRBTree:
    """Tests for the pure-Python reference implementation."""

    @pytest.mark.parametrize("sequence", [
        [10, 20, 30],
        [30, 20, 10],
        [10, 30, 20],
        [1, 2, 3, 4, 5, 6, 7],
        [7, 6, 5, 4, 3, 2, 1],
        [4, 2, 6, 1, 3, 5, 7],
        [10, 5, 15, 3, 7, 12, 20, 1],
    ])
    def test_invariants_hold(self, sequence):
        """RBTree maintains all invariants after each insertion."""
        tree = RBTree()
        for val in sequence:
            tree.insert(val)
            tree.check_invariants()

    @pytest.mark.parametrize("sequence", [
        [10, 20, 30],
        [30, 20, 10],
        [1, 2, 3, 4, 5, 6, 7],
    ])
    def test_inorder_sorted(self, sequence):
        """In-order traversal of RBTree yields sorted values."""
        tree = RBTree()
        for val in sequence:
            tree.insert(val)
        assert tree.inorder() == sorted(sequence)

    def test_duplicate_ignored(self):
        """Inserting a duplicate value has no effect."""
        tree = RBTree()
        tree.insert(10)
        tree.insert(10)
        assert tree.inorder() == [10]


# ============================================================
# DSL-based Red-Black tests  
# ============================================================

class TestDSLRedBlack:
    """Tests that the DSL red-black.dsl script parses and produces correct actions."""

    def test_dsl_parses(self, interpreter, rb_dsl):
        """The red-black.dsl file parses without errors."""
        tree = interpreter.parser.parse(rb_dsl)
        assert tree is not None

    def test_case1_recolour(self, interpreter, rb_dsl):
        """Case 1: Uncle RED triggers recolouring (parent, uncle, grandparent)."""
        # Build: grandparent(10) -> right child (20) -> right child (30)
        # All nodes start RED; set grandparent to BLACK manually
        bst = BST()
        bst.insert(10)
        bst.insert(20)
        bst.insert(5)   # uncle
        bst.insert(30)  # triggers Case 1 at node 30

        # Set up colours: root BLACK, children RED (default), grandchild RED
        bst.root.colour = "BLACK"
        bst.root.right.colour = "RED"   # parent (20)
        bst.root.left.colour = "RED"    # uncle (5)
        bst.root.right.right.colour = "RED"  # node (30)

        # Apply rules at the violating node (30)
        node_30 = bst.root.right.right
        new_node = interpreter.apply_rules(node_30, rb_dsl)

        # After Case 1: parent BLACK, uncle BLACK, grandparent RED
        assert bst.root.right.colour == "BLACK"    # parent recoloured
        assert bst.root.left.colour == "BLACK"      # uncle recoloured
        assert bst.root.colour == "RED"              # grandparent recoloured

    def test_red_black_dsl_file_parses(self, interpreter, rb_dsl):
        """Regression: red-black.dsl remains parseable by the grammar."""
        tree = interpreter.parser.parse(rb_dsl)
        assert tree is not None
