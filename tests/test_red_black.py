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

    def test_case2a_lr_zigzag(self, interpreter, rb_dsl):
        """Case 2a: uncle BLACK, parent is left child, node is right child (LR zig-zag)."""
        bst = BST()
        bst.insert(30)
        bst.insert(10)
        bst.insert(20)
        bst.root.colour = "BLACK"          # 30
        bst.root.left.colour = "RED"       # parent (10)
        bst.root.left.right.colour = "RED" # node (20) — right child of left child

        node_20 = bst.root.left.right
        new_node = interpreter.apply_rules(node_20, rb_dsl)

        # After Case 2a+3a: node 20 becomes new subtree root (BLACK),
        # 10 and 30 become its RED children
        assert new_node.val == 20
        assert new_node.colour == "BLACK"
        assert new_node.left.val == 10
        assert new_node.right.val == 30
        assert new_node.left.colour == "RED"
        assert new_node.right.colour == "RED"

    def test_case3a_ll_straight(self, interpreter, rb_dsl):
        """Case 3a: uncle BLACK, parent is left child, node is left child (LL straight)."""
        bst = BST()
        bst.insert(30)
        bst.insert(20)
        bst.insert(10)
        bst.root.colour = "BLACK"           # 30
        bst.root.left.colour = "RED"        # parent (20)
        bst.root.left.left.colour = "RED"   # node (10)

        node_10 = bst.root.left.left
        new_node = interpreter.apply_rules(node_10, rb_dsl)

        # After Case 3a: 20 becomes new subtree root (BLACK), 10 and 30 are RED
        assert new_node.val == 20
        assert new_node.colour == "BLACK"
        assert new_node.left.val == 10
        assert new_node.right.val == 30
        assert new_node.left.colour == "RED"
        assert new_node.right.colour == "RED"

    def test_case2b_rl_zigzag(self, interpreter, rb_dsl):
        """Case 2b: uncle BLACK, parent is right child, node is left child (RL zig-zag)."""
        bst = BST()
        bst.insert(10)
        bst.insert(30)
        bst.insert(20)
        bst.root.colour = "BLACK"           # 10
        bst.root.right.colour = "RED"       # parent (30)
        bst.root.right.left.colour = "RED"  # node (20) — left child of right child

        node_20 = bst.root.right.left
        new_node = interpreter.apply_rules(node_20, rb_dsl)

        # After Case 2b+3b: 20 becomes new subtree root (BLACK),
        # 10 and 30 become its RED children
        assert new_node.val == 20
        assert new_node.colour == "BLACK"
        assert new_node.left.val == 10
        assert new_node.right.val == 30
        assert new_node.left.colour == "RED"
        assert new_node.right.colour == "RED"

    def test_case3b_rr_straight(self, interpreter, rb_dsl):
        """Case 3b: uncle BLACK, parent is right child, node is right child (RR straight)."""
        bst = BST()
        bst.insert(10)
        bst.insert(20)
        bst.insert(30)
        bst.root.colour = "BLACK"            # 10
        bst.root.right.colour = "RED"        # parent (20)
        bst.root.right.right.colour = "RED"  # node (30)

        node_30 = bst.root.right.right
        new_node = interpreter.apply_rules(node_30, rb_dsl)

        # After Case 3b: 20 becomes new subtree root (BLACK), 10 and 30 are RED
        assert new_node.val == 20
        assert new_node.colour == "BLACK"
        assert new_node.left.val == 10
        assert new_node.right.val == 30
        assert new_node.left.colour == "RED"
        assert new_node.right.colour == "RED"

    def test_is_left_child_sensor(self, interpreter):
        """is_left_child returns 1 for left child, 0 for right child."""
        bst = BST()
        bst.insert(20)
        bst.insert(10)
        bst.insert(30)
        dsl_left = 'IF is_left_child == 1 THEN SET_COLOUR "BLACK"'
        dsl_right = 'IF is_left_child == 0 THEN SET_COLOUR "BLACK"'

        node_10 = bst.root.left
        node_30 = bst.root.right
        node_10.colour = "RED"
        node_30.colour = "RED"

        interpreter.apply_rules(node_10, dsl_left)
        assert node_10.colour == "BLACK"   # rule fired — is left child

        interpreter.apply_rules(node_30, dsl_left)
        assert node_30.colour == "RED"     # rule did NOT fire — is right child

        interpreter.apply_rules(node_30, dsl_right)
        assert node_30.colour == "BLACK"   # rule fired — is right child

    def test_parent_is_left_child_sensor(self, interpreter):
        """parent_is_left_child returns 1 when parent is grandparent's left child."""
        bst = BST()
        bst.insert(30)
        bst.insert(10)
        bst.insert(20)  # right child of 10, which is left child of 30
        dsl = 'IF parent_is_left_child == 1 THEN SET_COLOUR "BLACK"'

        node_20 = bst.root.left.right
        node_20.colour = "RED"
        interpreter.apply_rules(node_20, dsl)
        assert node_20.colour == "BLACK"


# ============================================================
# Native RBTree deletion tests
# ============================================================

class TestNativeRBTreeDeletion:
    """Tests for the pure-Python reference RBTree deletion."""

    @pytest.mark.parametrize("insert_seq, delete_seq", [
        ([10, 20, 30], [20]),
        ([10, 20, 30], [10]),
        ([10, 20, 30], [30]),
        ([10, 20, 30], [10, 20, 30]),
        ([1, 2, 3, 4, 5, 6, 7], [4, 2, 6]),
        ([1, 2, 3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6, 7]),
        ([7, 6, 5, 4, 3, 2, 1], [7, 6, 5, 4, 3, 2, 1]),
        ([4, 2, 6, 1, 3, 5, 7], [4]),
        ([4, 2, 6, 1, 3, 5, 7], [1, 7]),
        ([10, 5, 15, 3, 7, 12, 20, 1], [10, 5, 15]),
        ([20, 10, 30, 5, 15, 25, 35], [20, 10, 30, 5, 15, 25, 35]),
    ])
    def test_invariants_after_deletion(self, insert_seq, delete_seq):
        """RBTree maintains all invariants after each deletion."""
        tree = RBTree()
        for val in insert_seq:
            tree.insert(val)
        for val in delete_seq:
            tree.delete(val)
            if tree.root is not tree.NIL:
                tree.check_invariants()

    @pytest.mark.parametrize("insert_seq, delete_seq", [
        ([10, 20, 30], [20]),
        ([1, 2, 3, 4, 5], [3]),
        ([5, 3, 7, 1, 4, 6, 8], [5, 3]),
    ])
    def test_inorder_after_deletion(self, insert_seq, delete_seq):
        """In-order traversal yields correct sorted values after deletion."""
        tree = RBTree()
        for val in insert_seq:
            tree.insert(val)
        for val in delete_seq:
            tree.delete(val)
        expected = sorted(set(insert_seq) - set(delete_seq))
        assert tree.inorder() == expected

    def test_delete_nonexistent(self):
        """Deleting a value not in the tree is a no-op."""
        tree = RBTree()
        tree.insert(10)
        tree.insert(20)
        tree.delete(99)
        assert tree.inorder() == [10, 20]
        tree.check_invariants()

    def test_delete_all_to_empty(self):
        """Deleting all values results in an empty tree."""
        tree = RBTree()
        for val in [10, 20, 30]:
            tree.insert(val)
        for val in [10, 20, 30]:
            tree.delete(val)
        assert tree.root is tree.NIL


# ============================================================
# DSL deletion fix-up fixtures
# ============================================================

@pytest.fixture
def rb_delete_dsl():
    """Load the red-black-delete.dsl script."""
    dsl_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'red-black-delete.dsl')
    with open(dsl_path) as f:
        return f.read()


@pytest.fixture
def rb_insert_dsl():
    """Load the red-black.dsl insertion script (alias for rb_dsl)."""
    dsl_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'red-black.dsl')
    with open(dsl_path) as f:
        return f.read()


def _rb_to_treenode(rb_tree, rb_node, parent=None):
    """Convert an RBNode subtree to a TreeNode subtree (for DSL interpreter use)."""
    if rb_node is rb_tree.NIL:
        return None
    tn = TreeNode(rb_node.val)
    tn.colour = rb_node.colour
    tn.parent = parent
    tn.left = _rb_to_treenode(rb_tree, rb_node.left, tn)
    tn.right = _rb_to_treenode(rb_tree, rb_node.right, tn)
    tn.height = 1 + max(
        tn.left.height if tn.left else 0,
        tn.right.height if tn.right else 0,
    )
    return tn


def _build_rb_tree(interpreter, insert_dsl, values):
    """Build a correct RB tree using the reference implementation, then convert to TreeNodes."""
    ref = RBTree()
    for val in values:
        ref.insert(val)
    return _rb_to_treenode(ref, ref.root)


# ============================================================
# DSL-based Red-Black deletion tests
# ============================================================

class TestDSLRedBlackDeletion:
    """Tests that the DSL red-black-delete.dsl script handles deletion fix-up."""

    def test_delete_dsl_parses(self, interpreter, rb_delete_dsl):
        """The red-black-delete.dsl file parses without errors."""
        tree = interpreter.parser.parse(rb_delete_dsl)
        assert tree is not None

    def test_delete_red_leaf_no_fixup(self, interpreter, rb_insert_dsl, rb_delete_dsl):
        """Deleting a RED leaf needs no fix-up — invariants hold."""
        #     20(B)
        #    /    \
        #  10(R)  30(R)
        root = _build_rb_tree(interpreter, rb_insert_dsl, [20, 10, 30])
        assert root.val == 20
        assert root.left.colour == "RED"  # 10 is RED leaf

        root = interpreter.rb_delete(root, 10, rb_delete_dsl)
        assert_rb_invariants(root)
        assert _inorder(root) == [20, 30]

    def test_delete_black_node_with_red_child(self, interpreter, rb_insert_dsl, rb_delete_dsl):
        """Deleting a BLACK node whose replacement is RED — recolour to BLACK."""
        root = _build_rb_tree(interpreter, rb_insert_dsl, [10, 20, 30, 25])
        # After insertion of 10,20,30,25 the tree is valid RB
        assert_rb_invariants(root)
        values_before = set(_inorder(root))
        assert 25 in values_before

        root = interpreter.rb_delete(root, 30, rb_delete_dsl)
        assert_rb_invariants(root)
        assert 30 not in _inorder(root)

    def test_delete_root(self, interpreter, rb_insert_dsl, rb_delete_dsl):
        """Deleting the root maintains invariants."""
        root = _build_rb_tree(interpreter, rb_insert_dsl, [20, 10, 30])
        root = interpreter.rb_delete(root, 20, rb_delete_dsl)
        assert_rb_invariants(root)
        assert 20 not in _inorder(root)

    def test_delete_nonexistent(self, interpreter, rb_insert_dsl, rb_delete_dsl):
        """Deleting a value not in the tree is a no-op."""
        root = _build_rb_tree(interpreter, rb_insert_dsl, [10, 20, 30])
        root_before = root
        root = interpreter.rb_delete(root, 99, rb_delete_dsl)
        assert _inorder(root) == [10, 20, 30]

    @pytest.mark.parametrize("insert_seq, delete_seq", [
        ([10, 20, 30], [10, 20, 30]),
        ([1, 2, 3, 4, 5, 6, 7], [4, 2, 6, 1, 3, 5, 7]),
        ([7, 6, 5, 4, 3, 2, 1], [1, 3, 5, 7, 2, 6, 4]),
        ([4, 2, 6, 1, 3, 5, 7], [7, 6, 5, 4, 3, 2, 1]),
        ([10, 5, 15, 3, 7, 12, 20], [12, 5, 20, 3, 15, 7, 10]),
        ([20, 10, 30, 5, 15, 25, 35], [20, 10, 30, 5, 15, 25, 35]),
    ])
    def test_invariants_through_deletions(self, interpreter, rb_insert_dsl, rb_delete_dsl,
                                           insert_seq, delete_seq):
        """RB invariants hold after each DSL-driven deletion."""
        root = _build_rb_tree(interpreter, rb_insert_dsl, insert_seq)
        assert_rb_invariants(root)

        remaining = set(insert_seq)
        for val in delete_seq:
            root = interpreter.rb_delete(root, val, rb_delete_dsl)
            remaining.discard(val)
            if root:
                assert_rb_invariants(root)
            assert _inorder(root) if root else [] == sorted(remaining)

    @pytest.mark.parametrize("insert_seq, delete_seq", [
        ([10, 20, 30], [10, 20, 30]),
        ([1, 2, 3, 4, 5, 6, 7], [4, 2, 6, 1, 3, 5, 7]),
        ([4, 2, 6, 1, 3, 5, 7], [7, 6, 5, 4, 3, 2, 1]),
        ([20, 10, 30, 5, 15, 25, 35], [20, 10, 30, 5, 15, 25, 35]),
    ])
    def test_cross_validate_with_reference(self, interpreter, rb_insert_dsl, rb_delete_dsl,
                                            insert_seq, delete_seq):
        """DSL-driven deletion produces the same values as the reference RBTree."""
        # Reference
        ref_tree = RBTree()
        for val in insert_seq:
            ref_tree.insert(val)

        # DSL
        dsl_root = _build_rb_tree(interpreter, rb_insert_dsl, insert_seq)

        for val in delete_seq:
            ref_tree.delete(val)
            dsl_root = interpreter.rb_delete(dsl_root, val, rb_delete_dsl)

            ref_inorder = ref_tree.inorder()
            dsl_inorder = _inorder(dsl_root) if dsl_root else []
            assert dsl_inorder == ref_inorder, (
                f"After deleting {val}: DSL={dsl_inorder}, ref={ref_inorder}"
            )

    def test_delete_all_to_empty(self, interpreter, rb_insert_dsl, rb_delete_dsl):
        """Deleting all values results in an empty tree."""
        root = _build_rb_tree(interpreter, rb_insert_dsl, [10, 20, 30])
        for val in [10, 20, 30]:
            root = interpreter.rb_delete(root, val, rb_delete_dsl)
        assert root is None or _inorder(root) == []
