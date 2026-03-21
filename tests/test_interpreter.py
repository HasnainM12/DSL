"""Tests for interpreter.py — balancing rules, script execution, error handling."""
import pytest
from tree import BST
from tests.helpers import AVL_RULES


# ============================================================
# Balancing (apply_rules / balance_tree)
# ============================================================
class TestBalancing:
    def test_left_heavy_rotation(self, interpreter, avl_rules):
        """DSL correctly rotates a left-heavy tree (3-2-1)."""
        bst = BST()
        for v in [3, 2, 1]:
            bst.insert(v)
        assert bst.root.val == 3

        bst.root = interpreter.balance_tree(bst.root, avl_rules)
        assert bst.root.val == 2
        assert bst.root.left.val == 1
        assert bst.root.right.val == 3

    def test_right_heavy_rotation(self, interpreter, avl_rules):
        """DSL correctly rotates a right-heavy tree (1-2-3)."""
        bst = BST()
        for v in [1, 2, 3]:
            bst.insert(v)
        assert bst.root.val == 1

        bst.root = interpreter.balance_tree(bst.root, avl_rules)
        assert bst.root.val == 2
        assert bst.root.left.val == 1
        assert bst.root.right.val == 3

    def test_balanced_tree_no_action(self, interpreter, avl_rules):
        """DSL does nothing to an already balanced tree."""
        bst = BST()
        for v in [2, 1, 3]:
            bst.insert(v)
        bst.root = interpreter.balance_tree(bst.root, avl_rules)
        assert bst.root.val == 2

    def test_double_rotation_left_right(self, interpreter):
        """Left-right double rotation (3-1-2 case)."""
        bst = BST()
        for v in [3, 1, 2]:
            bst.insert(v)
        new_root = interpreter.apply_rules(bst.root, "ROTATE_LEFT_RIGHT")
        assert new_root.val == 2
        assert new_root.left.val == 1
        assert new_root.right.val == 3

    def test_double_rotation_right_left(self, interpreter):
        """Right-left double rotation (1-3-2 case)."""
        bst = BST()
        for v in [1, 3, 2]:
            bst.insert(v)
        new_root = interpreter.apply_rules(bst.root, "ROTATE_RIGHT_LEFT")
        assert new_root.val == 2
        assert new_root.left.val == 1
        assert new_root.right.val == 3

    def test_balance_none_returns_none(self, interpreter, avl_rules):
        """Balancing a None root returns None."""
        assert interpreter.balance_tree(None, avl_rules) is None

    def test_single_node_unchanged(self, interpreter, avl_rules):
        """A single-node tree stays unchanged after balancing."""
        bst = BST()
        bst.insert(42)
        bst.root = interpreter.balance_tree(bst.root, avl_rules)
        assert bst.root.val == 42
        assert bst.root.left is None
        assert bst.root.right is None


# ============================================================
# execute_script — INSERT / DELETE / comments
# ============================================================
class TestExecuteScript:
    def test_parse_insert_command(self, interpreter):
        tree = interpreter.parser.parse("INSERT 10")
        assert tree is not None

    def test_parse_delete_command(self, interpreter):
        tree = interpreter.parser.parse("DELETE 20")
        assert tree is not None

    def test_parse_comment(self, interpreter):
        tree = interpreter.parser.parse("# this is a comment\nINSERT 10")
        assert tree is not None

    def test_insert_action_returns_tuple(self, interpreter):
        actions = interpreter.execute_script("INSERT 10")
        assert ("INSERT", 10) in actions

    def test_delete_action_returns_tuple(self, interpreter):
        actions = interpreter.execute_script("DELETE 20")
        assert ("DELETE", 20) in actions

    def test_multiple_inserts_ordered(self, interpreter):
        actions = interpreter.execute_script("INSERT 5\nINSERT 10\nINSERT 15")
        assert actions == [("INSERT", 5), ("INSERT", 10), ("INSERT", 15)]

    def test_insert_delete_sequence(self, interpreter):
        actions = interpreter.execute_script("INSERT 42\nDELETE 42")
        assert actions == [("INSERT", 42), ("DELETE", 42)]

    def test_negative_number_insert(self, interpreter):
        actions = interpreter.execute_script("INSERT -5")
        assert ("INSERT", -5) in actions

    def test_mixed_script_with_rules_and_inserts(self, interpreter):
        script = """
# Insert some nodes first
INSERT 30
INSERT 10
INSERT 20
# Then apply balancing
IF balance_factor > 1 THEN ROTATE_RIGHT
IF balance_factor < -1 THEN ROTATE_LEFT
"""
        actions = interpreter.execute_script(script)
        inserts = [a for a in actions if isinstance(a, tuple) and a[0] == "INSERT"]
        assert len(inserts) == 3
        assert inserts == [("INSERT", 30), ("INSERT", 10), ("INSERT", 20)]

    def test_comment_only_script_fails(self, interpreter):
        """A script containing only comments should fail to parse."""
        with pytest.raises(Exception):
            interpreter.parser.parse("# just a comment")


# ============================================================
# Error Handling
# ============================================================
class TestErrorHandling:
    def test_invalid_syntax_apply_rules_raises(self, interpreter):
        """apply_rules with garbage DSL raises RuntimeError."""
        bst = BST()
        bst.insert(50)
        original = bst.root
        with pytest.raises(RuntimeError):
            interpreter.apply_rules(original, "GIBBERISH NONSENSE")

    def test_invalid_syntax_balance_tree_raises(self, interpreter):
        """balance_tree with garbage DSL raises RuntimeError."""
        bst = BST()
        bst.insert(50)
        original = bst.root
        with pytest.raises(RuntimeError):
            interpreter.balance_tree(original, "NOT VALID DSL")

    def test_execute_script_raises_on_bad_syntax(self, interpreter):
        """execute_script propagates the parse error for invalid DSL."""
        with pytest.raises(Exception):
            interpreter.execute_script("THIS IS NOT VALID")


# ============================================================
# balance_step — single-rotation-per-call
# ============================================================
class TestBalanceStep:
    def test_step_returns_changed_true(self, interpreter):
        """An unbalanced tree triggers at least one rotation step."""
        bst = BST()
        for v in [3, 2, 1]:
            bst.insert(v)
        parsed = interpreter.parser.parse(AVL_RULES)
        new_root, changed = interpreter.balance_step(bst.root, parsed)
        assert changed is True
        assert new_root.val == 2

    def test_step_returns_changed_false_when_balanced(self, interpreter):
        """A balanced tree produces changed=False."""
        bst = BST()
        for v in [2, 1, 3]:
            bst.insert(v)
        parsed = interpreter.parser.parse(AVL_RULES)
        _, changed = interpreter.balance_step(bst.root, parsed)
        assert changed is False

    def test_step_on_none(self, interpreter):
        """balance_step on None returns (None, False)."""
        parsed = interpreter.parser.parse(AVL_RULES)
        node, changed = interpreter.balance_step(None, parsed)
        assert node is None
        assert changed is False


# ============================================================
# New DSL features — Stage 2
# ============================================================
class TestNewFeatures:
    def test_avl_rule_triggers_rotate_right(self, interpreter):
        bst = BST()
        for v in [30, 20, 10]:
            bst.insert(v)
        script = "IF balance_factor > 1 THEN ROTATE_RIGHT"
        new_root = interpreter.balance_tree(bst.root, script)
        assert new_root.val == 20

    def test_no_rule_triggers_when_balanced(self, interpreter):
        bst = BST()
        for v in [20, 10, 30]:
            bst.insert(v)
        script = "IF balance_factor > 1 THEN ROTATE_RIGHT"
        new_root = interpreter.balance_tree(bst.root, script)
        assert new_root.val == 20  # unchanged

    def test_set_colour_action(self, interpreter):
        """SET_COLOUR changes node colour."""
        bst = BST()
        bst.insert(50)
        new_root = interpreter.apply_rules(bst.root, 'SET_COLOUR "BLACK"')
        assert new_root.colour == "BLACK"

    def test_colour_comparison(self, interpreter):
        """String comparison (node_colour == 'RED') works correctly."""
        bst = BST()
        bst.insert(50)
        # node_colour defaults to RED, so the condition should be True
        script = 'IF node_colour == "RED" THEN SET_COLOUR "BLACK"'
        new_root = interpreter.balance_tree(bst.root, script)
        assert new_root.colour == "BLACK"

    def test_not_condition(self, interpreter):
        """NOT negates a condition."""
        bst = BST()
        bst.insert(50)
        # node_colour is RED, NOT RED → False, so nothing should happen
        script = 'IF NOT node_colour == "RED" THEN SET_COLOUR "BLACK"'
        new_root = interpreter.balance_tree(bst.root, script)
        assert new_root.colour == "RED"  # unchanged

    def test_arithmetic_in_condition(self, interpreter):
        """Arithmetic expressions work in conditions."""
        bst = BST()
        for v in [30, 20, 10]:
            bst.insert(v)
        # balance_factor is 2, so 2 - 1 > 0 is True
        script = "IF balance_factor - 1 > 0 THEN ROTATE_RIGHT"
        new_root = interpreter.balance_tree(bst.root, script)
        assert new_root.val == 20

    def test_full_avl_dsl_file(self, interpreter):
        """The examples/avl.dsl script correctly balances a skewed tree."""
        import os
        dsl_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'avl.dsl')
        with open(dsl_path) as f:
            avl_script = f.read()
        bst = BST()
        for v in range(1, 11):
            bst.insert(v)
            bst.root = interpreter.balance_tree(bst.root, avl_script)
        # AVL tree with 10 nodes should have height ~4
        assert bst.root.height <= 5

    def test_set_parent_colour(self, interpreter):
        """SET_PARENT_COLOUR changes the parent node's colour."""
        bst = BST()
        bst.insert(10)
        bst.insert(20)
        bst.root.colour = "BLACK"
        bst.root.right.colour = "RED"
        # Apply at child node (20) — should colour parent (10)
        new_root = interpreter.apply_rules(bst.root.right, 'SET_PARENT_COLOUR "RED"')
        assert bst.root.colour == "RED"

    def test_set_uncle_colour(self, interpreter):
        """SET_UNCLE_COLOUR changes the uncle node's colour."""
        bst = BST()
        bst.insert(10)
        bst.insert(5)   # uncle
        bst.insert(20)
        bst.insert(25)  # node — uncle is 5
        bst.root.colour = "BLACK"
        bst.root.left.colour = "RED"
        bst.root.right.colour = "RED"
        bst.root.right.right.colour = "RED"
        # Apply at node 25 — uncle is 5
        interpreter.apply_rules(bst.root.right.right, 'SET_UNCLE_COLOUR "BLACK"')
        assert bst.root.left.colour == "BLACK"

    def test_set_grandparent_colour(self, interpreter):
        """SET_GRANDPARENT_COLOUR changes the grandparent node's colour."""
        bst = BST()
        bst.insert(10)
        bst.insert(20)
        bst.insert(30)
        bst.root.colour = "BLACK"
        bst.root.right.colour = "RED"
        bst.root.right.right.colour = "RED"
        # Apply at node 30 — grandparent is 10
        interpreter.apply_rules(bst.root.right.right, 'SET_GRANDPARENT_COLOUR "RED"')
        assert bst.root.colour == "RED"