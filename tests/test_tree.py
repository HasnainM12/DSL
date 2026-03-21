"""Tests for tree.py — BST insert, delete, contains, rotations, heights, layout."""
import pytest
from tree import BST, TreeNode
from tests.helpers import count_nodes


# ============================================================
# Insert
# ============================================================
class TestInsert:
    def test_insert_into_empty_tree(self):
        bst = BST()
        assert bst.insert(50) is True
        assert bst.root.val == 50

    def test_insert_duplicate_returns_false(self):
        bst = BST()
        bst.insert(50)
        assert bst.insert(50) is False

    @pytest.mark.parametrize("values,expected_count", [
        ([50], 1),
        ([50, 25, 75], 3),
        ([50, 25, 75, 10, 30, 60, 80], 7),
    ])
    def test_insert_multiple(self, values, expected_count):
        bst = BST()
        for v in values:
            bst.insert(v)
        assert count_nodes(bst.root) == expected_count

    def test_insert_duplicates_ignored(self):
        """After inserting [50, 25, 75, 50, 25] only 3 nodes should exist."""
        bst = BST()
        for v in [50, 25, 75, 50, 25]:
            bst.insert(v)
        assert count_nodes(bst.root) == 3

    @pytest.mark.parametrize("val", [-10, -1, 0])
    def test_insert_negative_and_zero(self, val):
        bst = BST()
        assert bst.insert(val) is True
        assert bst.root.val == val


# ============================================================
# Contains
# ============================================================
class TestContains:
    def test_contains_existing(self):
        bst = BST()
        for v in [50, 25, 75]:
            bst.insert(v)
        assert bst.contains(25) is True

    def test_contains_missing(self):
        bst = BST()
        for v in [50, 25, 75]:
            bst.insert(v)
        assert bst.contains(99) is False

    def test_contains_empty_tree(self):
        bst = BST()
        assert bst.contains(1) is False


# ============================================================
# Delete
# ============================================================
class TestDelete:
    def test_delete_leaf(self):
        bst = BST()
        for v in [50, 25, 75]:
            bst.insert(v)
        assert bst.delete(25) is True
        assert bst.contains(25) is False
        assert count_nodes(bst.root) == 2

    def test_delete_node_with_one_child(self):
        bst = BST()
        for v in [50, 25, 10]:
            bst.insert(v)
        assert bst.delete(25) is True
        assert bst.contains(10) is True
        assert count_nodes(bst.root) == 2

    def test_delete_node_with_two_children(self):
        bst = BST()
        for v in [50, 25, 75, 10, 30]:
            bst.insert(v)
        assert bst.delete(25) is True
        assert bst.contains(10) is True
        assert bst.contains(30) is True
        assert count_nodes(bst.root) == 4

    def test_delete_root(self):
        bst = BST()
        for v in [50, 25, 75]:
            bst.insert(v)
        assert bst.delete(50) is True
        assert bst.contains(50) is False
        assert count_nodes(bst.root) == 2

    def test_delete_missing_returns_false(self):
        bst = BST()
        bst.insert(50)
        assert bst.delete(99) is False

    def test_delete_from_empty_tree(self):
        bst = BST()
        assert bst.delete(1) is False


# ============================================================
# Rotations
# ============================================================
class TestRotations:
    def test_rotate_right(self, sample_bst):
        new_root = sample_bst.rotate_right(sample_bst.root)
        assert new_root.val == 25
        assert new_root.right.val == 50
        assert new_root.left.val == 10

    def test_rotate_left(self, sample_bst):
        new_root = sample_bst.rotate_left(sample_bst.root)
        assert new_root.val == 75
        assert new_root.left.val == 50
        assert new_root.right.val == 80

    def test_rotate_right_on_none(self):
        bst = BST()
        assert bst.rotate_right(None) is None

    def test_rotate_left_on_none(self):
        bst = BST()
        assert bst.rotate_left(None) is None

    def test_rotate_right_no_left_child(self):
        node = TreeNode(10)
        node.right = TreeNode(20)
        bst = BST()
        result = bst.rotate_right(node)
        assert result.val == 10  # unchanged

    def test_rotate_left_no_right_child(self):
        node = TreeNode(10)
        node.left = TreeNode(5)
        bst = BST()
        result = bst.rotate_left(node)
        assert result.val == 10  # unchanged

    def test_rotate_left_right(self):
        bst = BST()
        for v in [30, 10, 20]:
            bst.insert(v)
        new_root = bst.rotate_left_right(bst.root)
        assert new_root.val == 20
        assert new_root.left.val == 10
        assert new_root.right.val == 30

    def test_rotate_right_left(self):
        bst = BST()
        for v in [10, 30, 20]:
            bst.insert(v)
        new_root = bst.rotate_right_left(bst.root)
        assert new_root.val == 20
        assert new_root.left.val == 10
        assert new_root.right.val == 30

    def test_rotate_left_ascending_sequence(self):
        """Ascending insert 10, 20, 30 → rotate_left on root gives root=20."""
        bst = BST()
        for v in [10, 20, 30]:
            bst.insert(v)
        new_root = bst.rotate_left(bst.root)
        assert new_root.val == 20
        assert new_root.left.val == 10
        assert new_root.right.val == 30

    def test_parent_references_after_insert(self):
        """Parent pointers are set correctly after insert."""
        bst = BST()
        for v in [50, 25, 75]:
            bst.insert(v)
        assert bst.root.parent is None
        assert bst.root.left.parent is bst.root
        assert bst.root.right.parent is bst.root

    def test_parent_references_after_rotate_left(self):
        """Parent pointers are updated correctly after rotate_left."""
        bst = BST()
        for v in [10, 20, 30]:
            bst.insert(v)
        # Before: root=10, 10.right=20, 20.right=30
        new_root = bst.rotate_left(bst.root)
        # After:  root=20, 20.left=10, 20.right=30
        assert new_root.val == 20
        assert new_root.parent is None       # was root, stays root
        assert new_root.left.val == 10
        assert new_root.left.parent is new_root   # 10's parent is now 20
        assert new_root.right.val == 30
        assert new_root.right.parent is new_root   # 30's parent is still 20

    def test_parent_references_after_rotate_right(self):
        """Parent pointers are updated correctly after rotate_right."""
        bst = BST()
        for v in [30, 20, 10]:
            bst.insert(v)
        new_root = bst.rotate_right(bst.root)
        assert new_root.val == 20
        assert new_root.parent is None
        assert new_root.left.val == 10
        assert new_root.left.parent is new_root
        assert new_root.right.val == 30
        assert new_root.right.parent is new_root


# ============================================================
# Height Updates
# ============================================================
class TestHeightUpdates:
    def test_leaf_height_is_one(self):
        bst = BST()
        bst.insert(50)
        assert bst.root.height == 1

    def test_height_updates_on_insert(self):
        bst = BST()
        bst.insert(50)
        bst.insert(25)
        assert bst.root.height == 2
        bst.insert(10)
        assert bst.root.height == 3

    def test_height_unchanged_on_duplicate(self):
        bst = BST()
        for v in [50, 25, 75]:
            bst.insert(v)
        h_before = bst.root.height
        bst.insert(50)
        assert bst.root.height == h_before


# ============================================================
# Position Layout  (migrated from test_phase2.py)
# ============================================================
class TestPositionLayout:
    def test_positions(self, sample_bst):
        """Verify mid-point coordinate layout for a 7-node tree."""
        positions = {}
        Y_START = 50
        Y_SPACING = 80

        def calc(node, depth, left, right):
            if node is None:
                return
            x = (left + right) / 2
            y = Y_START + depth * Y_SPACING
            positions[node.val] = (x, y)
            calc(node.left, depth + 1, left, x)
            calc(node.right, depth + 1, x, right)

        canvas_w = 800
        calc(sample_bst.root, 0, 0, canvas_w)

        assert positions[50] == (400.0, 50)
        assert positions[25] == (200.0, 130)
        assert positions[75] == (600.0, 130)
        assert positions[10] == (100.0, 210)
        assert positions[30] == (300.0, 210)
        assert positions[60] == (500.0, 210)
        assert positions[80] == (700.0, 210)
        assert len(positions) == 7


# ============================================================
# Animation-Queue Mutations  (migrated from test_phase3.py)
# ============================================================
class TestAnimationQueue:
    def test_rotation_then_insert(self, sample_bst):
        """Right rotation on root, then insert 40."""
        sample_bst.root = sample_bst.rotate_right(sample_bst.root)
        assert sample_bst.root.val == 25
        assert sample_bst.root.right.val == 50

        sample_bst.insert(40)
        node30 = sample_bst.root.right.left
        assert node30.val == 30
        assert node30.right.val == 40

    def test_node_count_after_mutations(self, sample_bst):
        """After rotate + insert, tree should have 8 nodes."""
        sample_bst.root = sample_bst.rotate_right(sample_bst.root)
        sample_bst.insert(40)
        assert count_nodes(sample_bst.root) == 8
