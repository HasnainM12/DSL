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
        bst.insert(25)
        # Apply rule specifically to the child node to avoid root enforcement overrides
        # node_colour is RED, NOT RED → False, so nothing should happen
        script = 'IF NOT node_colour == "RED" THEN SET_COLOUR "BLACK"'
        new_node = interpreter.apply_rules(bst.root.left, script)
        assert new_node.colour == "RED"  # unchanged

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


# ============================================================
# balance_step — INSERT/DELETE commands in script must not
#                cause false-positive changed=True
# ============================================================
class TestBalanceStepWithInserts:
    def test_insert_in_script_does_not_cause_false_positive(self, interpreter):
        """balance_step must return changed=False when no rule condition is met,
        even if the parsed_tree contains INSERT commands."""
        bst = BST()
        for v in [2, 1, 3]:  # already balanced
            bst.insert(v)
        script = "IF balance_factor > 1 THEN ROTATE_RIGHT\nINSERT 50\nINSERT 30"
        parsed = interpreter.parser.parse(script)
        _, changed = interpreter.balance_step(bst.root, parsed)
        assert changed is False  # was True (bug) — INSERT tuples made triggered truthy

    def test_insert_in_script_rule_still_fires_when_needed(self, interpreter):
        """balance_step returns changed=True when a real rule fires, even with INSERT commands in script."""
        bst = BST()
        for v in [3, 2, 1]:  # left-heavy — needs rotation
            bst.insert(v)
        script = "IF balance_factor > 1 THEN ROTATE_RIGHT\nINSERT 50"
        parsed = interpreter.parser.parse(script)
        new_root, changed = interpreter.balance_step(bst.root, parsed)
        assert changed is True
        assert new_root.val == 2

    def test_advanced_logic_rule3_produces_one_step(self, interpreter):
        """Rule 3 of advanced_logic.dsl fires exactly once on a zig-zag 50->30->40 tree."""
        bst = BST()
        for v in [50, 30, 40]:
            bst.insert(v)
        script = (
            "IF NOT (height > 5) AND (balance_factor > 1 OR left_child_balance < 0)"
            " THEN {\n    ROTATE_LEFT_RIGHT\n}\nINSERT 99"
        )
        parsed = interpreter.parser.parse(script)
        steps = 0
        root = bst.root
        while True:
            root, changed = interpreter.balance_step(root, parsed)
            if not changed:
                break
            steps += 1
            assert steps <= 5, "Should not need more than a few steps"
        assert steps == 1
        assert root.val == 40


# ============================================================
# Compound conditions — precedence, evaluation, integration
# ============================================================
class TestCompoundConditions:
    """Tests for NOT/AND/OR precedence and evaluation correctness."""

    def test_not_and_precedence_balanced_tree(self, interpreter):
        """NOT (height > 5) AND (bf > 1) should NOT fire on a balanced tree.

        Previously: grammar parsed as NOT((h>5) AND (bf>1)) = NOT(False AND False) = True.
        Now: grammar parses as (NOT(h>5)) AND (bf>1) = True AND False = False.
        """
        bst = BST()
        for v in [2, 1, 3]:  # balanced, bf=0, h=2
            bst.insert(v)
        script = "IF NOT (height > 5) AND balance_factor > 1 THEN ROTATE_RIGHT"
        new_root = interpreter.apply_rules(bst.root, script)
        assert new_root.val == 2  # unchanged — rule should NOT fire

    def test_not_and_precedence_unbalanced_tree(self, interpreter):
        """NOT (height > 5) AND (bf > 1) SHOULD fire on a left-heavy tree."""
        bst = BST()
        for v in [3, 2, 1]:  # left-heavy, bf=2, h=3
            bst.insert(v)
        script = "IF NOT (height > 5) AND balance_factor > 1 THEN ROTATE_RIGHT"
        new_root = interpreter.apply_rules(bst.root, script)
        assert new_root.val == 2  # rotated

    def test_complex_compound_rule3_node50_fires(self, interpreter):
        """Node 50 in [50,30,40] should fire Rule 3 (bf=2, lb=-1, h=3<5)."""
        bst = BST()
        for v in [50, 30, 40]:
            bst.insert(v)
        script = (
            "IF NOT (height > 5) AND (balance_factor > 1 OR left_child_balance < 0)"
            " THEN ROTATE_LEFT_RIGHT"
        )
        new_root = interpreter.apply_rules(bst.root, script)
        assert new_root.val == 40  # left-right rotation on root 50

    def test_complex_compound_rule3_node30_no_fire(self, interpreter):
        """Node 30 in [50,30,40] should NOT fire Rule 3 (bf=-1, lb=0)."""
        bst = BST()
        for v in [50, 30, 40]:
            bst.insert(v)
        script = (
            "IF NOT (height > 5) AND (balance_factor > 1 OR left_child_balance < 0)"
            " THEN ROTATE_LEFT_RIGHT"
        )
        node30 = bst.root.left
        new_root = interpreter.apply_rules(node30, script)
        # Node 30 has bf=-1 (not >1) and lb=0 (not <0), so rule should NOT fire
        assert new_root.val == 30  # unchanged

    def test_complex_compound_rule3_node40_no_fire(self, interpreter):
        """Node 40 (leaf) in [50,30,40] should NOT fire Rule 3."""
        bst = BST()
        for v in [50, 30, 40]:
            bst.insert(v)
        script = (
            "IF NOT (height > 5) AND (balance_factor > 1 OR left_child_balance < 0)"
            " THEN ROTATE_LEFT_RIGHT"
        )
        node40 = bst.root.left.right
        new_root = interpreter.apply_rules(node40, script)
        assert new_root.val == 40  # unchanged

    def test_insert_before_rules_collected(self, interpreter):
        """INSERT commands before IF rules are collected by execute_script."""
        script = "INSERT 10\nINSERT 20\nIF balance_factor > 1 THEN ROTATE_RIGHT"
        actions = interpreter.execute_script(script)
        inserts = [a for a in actions if isinstance(a, tuple)]
        assert inserts == [("INSERT", 10), ("INSERT", 20)]

    def test_insert_after_rules_collected(self, interpreter):
        """INSERT commands after IF rules are collected by execute_script."""
        script = "IF balance_factor > 1 THEN ROTATE_RIGHT\nINSERT 10\nINSERT 20"
        actions = interpreter.execute_script(script)
        inserts = [a for a in actions if isinstance(a, tuple)]
        assert inserts == [("INSERT", 10), ("INSERT", 20)]

    def test_multiple_rules_first_match_wins(self, interpreter):
        """When multiple rules match, only the first fires (if/elif semantics)."""
        bst = BST()
        for v in [3, 2, 1]:  # bf=2 at root
            bst.insert(v)
        # Both rules would match, but first-match-wins should apply ROTATE_RIGHT
        script = (
            "IF balance_factor > 1 THEN ROTATE_RIGHT\n"
            "IF balance_factor > 0 THEN ROTATE_LEFT"
        )
        new_root = interpreter.apply_rules(bst.root, script)
        assert new_root.val == 2  # ROTATE_RIGHT was applied, not ROTATE_LEFT

    def test_and_or_combined_evaluation(self, interpreter):
        """A AND B OR C evaluates as (A AND B) OR C."""
        bst = BST()
        for v in [3, 2, 1]:  # bf=2, h=3
            bst.insert(v)
        # bf > 1 (True) AND height > 10 (False) OR height > 2 (True)
        # With correct precedence: (True AND False) OR True = False OR True = True
        script = "IF balance_factor > 1 AND height > 10 OR height > 2 THEN ROTATE_RIGHT"
        new_root = interpreter.apply_rules(bst.root, script)
        assert new_root.val == 2  # rule fires because OR is True

    def test_full_advanced_logic_balance_loop(self, interpreter):
        """Full advanced_logic.dsl Rule 3 + INSERTs: exactly 1 balance step."""
        bst = BST()
        for v in [50, 30, 40]:
            bst.insert(v)
        script = (
            "IF NOT (height > 5) AND (balance_factor > 1 OR left_child_balance < 0)"
            " THEN {\n    ROTATE_LEFT_RIGHT\n}\nINSERT 99"
        )
        parsed = interpreter.parser.parse(script)
        steps = 0
        root = bst.root
        while True:
            root, changed = interpreter.balance_step(root, parsed)
            if not changed:
                break
            steps += 1
            if steps > 10:
                pytest.fail("Infinite loop — balance_step never converges")
        assert steps == 1, f"Expected 1 step, got {steps}"
        assert root.val == 40
        assert root.left.val == 30
        assert root.right.val == 50