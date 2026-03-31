"""
test_dsl_keywords.py — Comprehensive tests for DSL keywords, sensors, and actions.

Covers areas not tested by the existing suite:
  - All sibling sensor keywords (sibling_colour, sibling_left_colour,
    sibling_right_colour) — parsing AND runtime behaviour
  - PROPAGATE and DONE signal actions — appear correctly in the actions list
  - Sibling colour mutations (SET_SIBLING_COLOUR, SET_SIBLING_LEFT_COLOUR,
    SET_SIBLING_RIGHT_COLOUR, SET_SIBLING_COLOUR_FROM_PARENT)
  - Sibling rotation actions (ROTATE_LEFT_AT_SIBLING, ROTATE_RIGHT_AT_SIBLING)
  - ROTATE_LEFT_AT_GRANDPARENT / ROTATE_RIGHT_AT_GRANDPARENT execution
  - All six comparison operators, including >= / <= / !=
  - First-match-wins rule semantics
  - Grammar error cases: unclosed braces, internal token names used as keywords
"""

import os

import pytest
from lark.exceptions import UnexpectedInput

from interpreter import DSLInterpreter
from tree import BST

# ── helpers ───────────────────────────────────────────────────────────────────


def _inorder(node):
    """Return in-order values from a BST subtree."""
    if node is None:
        return []
    return _inorder(node.left) + [node.val] + _inorder(node.right)


# ── Grammar / Parsing ─────────────────────────────────────────────────────────


class TestNewKeywordsParsing:
    """Every keyword added for RB deletion round-trips through the parser."""

    def test_sibling_colour_sensor_parses(self, interpreter):
        t = interpreter.parser.parse('IF sibling_colour == "RED" THEN ROTATE_LEFT')
        assert t is not None

    def test_sibling_left_colour_sensor_parses(self, interpreter):
        t = interpreter.parser.parse(
            'IF sibling_left_colour == "BLACK" THEN ROTATE_RIGHT'
        )
        assert t is not None

    def test_sibling_right_colour_sensor_parses(self, interpreter):
        t = interpreter.parser.parse(
            'IF sibling_right_colour == "BLACK" THEN ROTATE_RIGHT'
        )
        assert t is not None

    def test_propagate_standalone_parses(self, interpreter):
        t = interpreter.parser.parse("PROPAGATE")
        assert t is not None

    def test_done_standalone_parses(self, interpreter):
        t = interpreter.parser.parse("DONE")
        assert t is not None

    def test_rotate_left_at_sibling_parses(self, interpreter):
        t = interpreter.parser.parse("ROTATE_LEFT_AT_SIBLING")
        assert t is not None

    def test_rotate_right_at_sibling_parses(self, interpreter):
        t = interpreter.parser.parse("ROTATE_RIGHT_AT_SIBLING")
        assert t is not None

    def test_set_sibling_colour_parses(self, interpreter):
        t = interpreter.parser.parse('SET_SIBLING_COLOUR "BLACK"')
        assert t is not None

    def test_set_sibling_left_colour_parses(self, interpreter):
        t = interpreter.parser.parse('SET_SIBLING_LEFT_COLOUR "BLACK"')
        assert t is not None

    def test_set_sibling_right_colour_parses(self, interpreter):
        t = interpreter.parser.parse('SET_SIBLING_RIGHT_COLOUR "RED"')
        assert t is not None

    def test_set_sibling_colour_from_parent_parses(self, interpreter):
        t = interpreter.parser.parse("SET_SIBLING_COLOUR_FROM_PARENT")
        assert t is not None

    def test_all_sibling_sensors_in_condition_parses(self, interpreter):
        script = (
            'IF sibling_colour == "BLACK" '
            'AND sibling_left_colour == "BLACK" '
            'AND sibling_right_colour == "BLACK" '
            "THEN PROPAGATE"
        )
        assert interpreter.parser.parse(script) is not None

    def test_propagate_inside_action_block_parses(self, interpreter):
        script = (
            'IF sibling_colour == "BLACK" THEN { SET_SIBLING_COLOUR "RED" PROPAGATE }'
        )
        assert interpreter.parser.parse(script) is not None

    def test_done_inside_action_block_parses(self, interpreter):
        script = (
            'IF sibling_right_colour == "RED" '
            "THEN { SET_SIBLING_COLOUR_FROM_PARENT "
            'SET_PARENT_COLOUR "BLACK" '
            'SET_SIBLING_RIGHT_COLOUR "BLACK" '
            "ROTATE_LEFT_AT_PARENT DONE }"
        )
        assert interpreter.parser.parse(script) is not None

    def test_rotate_left_at_grandparent_standalone_parses(self, interpreter):
        """The keyword the user originally asked about — must parse without error."""
        t = interpreter.parser.parse("ROTATE_LEFT_AT_GRANDPARENT")
        assert t is not None

    def test_rotate_left_at_grandparent_in_rule_parses(self, interpreter):
        t = interpreter.parser.parse(
            'IF node_colour == "RED" AND parent_colour == "RED" '
            "THEN ROTATE_LEFT_AT_GRANDPARENT"
        )
        assert t is not None

    def test_rotate_right_at_grandparent_in_rule_parses(self, interpreter):
        t = interpreter.parser.parse(
            'IF node_colour == "RED" AND parent_colour == "RED" '
            "THEN ROTATE_RIGHT_AT_GRANDPARENT"
        )
        assert t is not None

    def test_red_black_delete_file_parses(self, interpreter):
        """The red-black-delete.dsl example file must parse cleanly."""
        path = os.path.join(
            os.path.dirname(__file__), "..", "examples", "red-black-delete.dsl"
        )
        with open(path) as f:
            t = interpreter.parser.parse(f.read())
        assert t is not None


# ── Comparators ───────────────────────────────────────────────────────────────


class TestComparators:
    """All six comparison operators fire at the correct boundary."""

    # ------------------------------------------------------------------
    # >= (greater-than-or-equal)
    # ------------------------------------------------------------------

    def test_gte_triggers_at_boundary(self, interpreter):
        """balance_factor >= 2 fires when bf == 2 exactly."""
        bst = BST()
        for v in [30, 20, 10]:  # root bf = 2
            bst.insert(v)
        new_root = interpreter.apply_rules(
            bst.root, "IF balance_factor >= 2 THEN ROTATE_RIGHT"
        )
        assert new_root.val == 20

    def test_gte_triggers_above_boundary(self, interpreter):
        """balance_factor >= 1 fires when bf == 2."""
        bst = BST()
        for v in [30, 20, 10]:
            bst.insert(v)
        new_root = interpreter.apply_rules(
            bst.root, "IF balance_factor >= 1 THEN ROTATE_RIGHT"
        )
        assert new_root.val == 20

    def test_gte_does_not_trigger_below_boundary(self, interpreter):
        """balance_factor >= 2 does NOT fire when bf == 0."""
        bst = BST()
        for v in [20, 10, 30]:  # root bf = 0
            bst.insert(v)
        new_root = interpreter.apply_rules(
            bst.root, "IF balance_factor >= 2 THEN ROTATE_RIGHT"
        )
        assert new_root is bst.root  # unchanged

    # ------------------------------------------------------------------
    # <= (less-than-or-equal)
    # ------------------------------------------------------------------

    def test_lte_triggers_at_boundary(self, interpreter):
        """balance_factor <= -2 fires when bf == -2 exactly."""
        bst = BST()
        for v in [10, 20, 30]:  # root bf = -2
            bst.insert(v)
        new_root = interpreter.apply_rules(
            bst.root, "IF balance_factor <= -2 THEN ROTATE_LEFT"
        )
        assert new_root.val == 20

    def test_lte_does_not_trigger_above_boundary(self, interpreter):
        """balance_factor <= -2 does NOT fire when bf == 0."""
        bst = BST()
        for v in [20, 10, 30]:
            bst.insert(v)
        new_root = interpreter.apply_rules(
            bst.root, "IF balance_factor <= -2 THEN ROTATE_LEFT"
        )
        assert new_root is bst.root  # unchanged

    # ------------------------------------------------------------------
    # != (not-equal)
    # ------------------------------------------------------------------

    def test_neq_triggers_when_values_differ(self, interpreter):
        """node_colour != "BLACK" fires when the node is RED."""
        bst = BST()
        bst.insert(50)
        bst.root.colour = "RED"
        new_root = interpreter.apply_rules(
            bst.root, 'IF node_colour != "BLACK" THEN SET_COLOUR "BLACK"'
        )
        assert new_root.colour == "BLACK"

    def test_neq_does_not_trigger_when_values_equal(self, interpreter):
        """node_colour != "BLACK" does NOT fire when the node is already BLACK."""
        bst = BST()
        bst.insert(50)
        bst.root.colour = "BLACK"
        new_root = interpreter.apply_rules(
            bst.root, 'IF node_colour != "BLACK" THEN SET_COLOUR "RED"'
        )
        assert new_root.colour == "BLACK"  # unchanged

    # ------------------------------------------------------------------
    # > strict boundary
    # ------------------------------------------------------------------

    def test_gt_does_not_trigger_at_exact_boundary(self, interpreter):
        """balance_factor > 2 does NOT fire when bf == 2 (strict greater-than)."""
        bst = BST()
        for v in [30, 20, 10]:  # root bf = 2
            bst.insert(v)
        new_root = interpreter.apply_rules(
            bst.root, "IF balance_factor > 2 THEN ROTATE_RIGHT"
        )
        assert new_root is bst.root  # no rotation performed

    # ------------------------------------------------------------------
    # < strict boundary
    # ------------------------------------------------------------------

    def test_lt_does_not_trigger_at_exact_boundary(self, interpreter):
        """balance_factor < -2 does NOT fire when bf == -2."""
        bst = BST()
        for v in [10, 20, 30]:  # root bf = -2
            bst.insert(v)
        new_root = interpreter.apply_rules(
            bst.root, "IF balance_factor < -2 THEN ROTATE_LEFT"
        )
        assert new_root is bst.root  # no rotation performed


# ── Sibling sensors ───────────────────────────────────────────────────────────


class TestSiblingSensors:
    """sibling_colour / sibling_left_colour / sibling_right_colour return
    the correct value in all structural configurations."""

    def _three_node_tree(self):
        """Return a 3-node tree: 20(B) -> 10(R) left, 30(R) right."""
        bst = BST()
        for v in [20, 10, 30]:
            bst.insert(v)
        bst.root.colour = "BLACK"
        bst.root.left.colour = "RED"
        bst.root.right.colour = "RED"
        return bst

    # ------------------------------------------------------------------
    # sibling_colour
    # ------------------------------------------------------------------

    def test_sibling_colour_for_left_child(self, interpreter):
        """Node 10 (left child) — sibling is 30 (RED): condition fires."""
        bst = self._three_node_tree()
        interpreter.apply_rules(
            bst.root.left, 'IF sibling_colour == "RED" THEN SET_COLOUR "BLACK"'
        )
        assert bst.root.left.colour == "BLACK"

    def test_sibling_colour_for_right_child(self, interpreter):
        """Node 30 (right child) — sibling is 10 (RED): condition fires."""
        bst = self._three_node_tree()
        interpreter.apply_rules(
            bst.root.right, 'IF sibling_colour == "RED" THEN SET_COLOUR "BLACK"'
        )
        assert bst.root.right.colour == "BLACK"

    def test_sibling_colour_defaults_to_black_when_no_sibling(self, interpreter):
        """A node with no sibling reports sibling_colour as BLACK."""
        bst = BST()
        bst.insert(10)
        bst.insert(20)  # right child; has no sibling
        # sibling_colour == "BLACK" should be True → colour changes to BLACK
        interpreter.apply_rules(
            bst.root.right, 'IF sibling_colour == "BLACK" THEN SET_COLOUR "BLACK"'
        )
        assert bst.root.right.colour == "BLACK"

    def test_sibling_colour_defaults_to_black_for_root(self, interpreter):
        """The root node (no parent) reports sibling_colour as BLACK."""
        bst = BST()
        bst.insert(50)
        bst.root.colour = "RED"
        interpreter.apply_rules(
            bst.root, 'IF sibling_colour == "BLACK" THEN SET_COLOUR "BLACK"'
        )
        assert bst.root.colour == "BLACK"

    def test_sibling_colour_black_sibling_does_not_trigger_red_check(self, interpreter):
        """sibling_colour == "RED" does NOT fire when sibling is BLACK."""
        bst = self._three_node_tree()
        bst.root.right.colour = "BLACK"  # sibling of left child is now BLACK
        interpreter.apply_rules(
            bst.root.left, 'IF sibling_colour == "RED" THEN SET_COLOUR "BLACK"'
        )
        assert bst.root.left.colour == "RED"  # unchanged

    # ------------------------------------------------------------------
    # sibling_left_colour
    # ------------------------------------------------------------------

    def test_sibling_left_colour_when_sibling_child_is_red(self, interpreter):
        """sibling_left_colour returns RED when sibling's left child is RED."""
        #   20(B)
        #  /     \
        # 10(B)  30(B)
        #        /
        #       25(R)   ← sibling's left child from node 10's perspective
        bst = BST()
        for v in [20, 10, 30, 25]:
            bst.insert(v)
        bst.root.colour = "BLACK"
        bst.root.left.colour = "BLACK"
        bst.root.right.colour = "BLACK"
        bst.root.right.left.colour = "RED"

        interpreter.apply_rules(
            bst.root.left, 'IF sibling_left_colour == "RED" THEN SET_COLOUR "RED"'
        )
        assert bst.root.left.colour == "RED"  # rule fired

    def test_sibling_left_colour_defaults_to_black_when_absent(self, interpreter):
        """sibling_left_colour returns BLACK when sibling has no left child."""
        bst = self._three_node_tree()  # sibling (30) has no children
        interpreter.apply_rules(
            bst.root.left, 'IF sibling_left_colour == "BLACK" THEN SET_COLOUR "BLACK"'
        )
        assert bst.root.left.colour == "BLACK"

    # ------------------------------------------------------------------
    # sibling_right_colour
    # ------------------------------------------------------------------

    def test_sibling_right_colour_when_sibling_child_is_red(self, interpreter):
        """sibling_right_colour returns RED when sibling's right child is RED."""
        #   20(B)
        #  /     \
        # 10(B)  30(B)
        #            \
        #            35(R)   ← sibling's right child from node 10's perspective
        bst = BST()
        for v in [20, 10, 30, 35]:
            bst.insert(v)
        bst.root.colour = "BLACK"
        bst.root.left.colour = "BLACK"
        bst.root.right.colour = "BLACK"
        bst.root.right.right.colour = "RED"

        interpreter.apply_rules(
            bst.root.left, 'IF sibling_right_colour == "RED" THEN SET_COLOUR "RED"'
        )
        assert bst.root.left.colour == "RED"  # rule fired

    def test_sibling_right_colour_defaults_to_black_when_absent(self, interpreter):
        """sibling_right_colour returns BLACK when sibling has no right child."""
        bst = self._three_node_tree()
        interpreter.apply_rules(
            bst.root.left, 'IF sibling_right_colour == "BLACK" THEN SET_COLOUR "BLACK"'
        )
        assert bst.root.left.colour == "BLACK"


# ── DONE / PROPAGATE signals ─────────────────────────────────────────────────


class TestSignals:
    """PROPAGATE → 'SIGNAL_PROPAGATE' and DONE → 'SIGNAL_DONE' appear in the
    actions list returned by apply_rules(..., return_flag=True)."""

    def test_standalone_propagate_is_in_actions(self, interpreter):
        bst = BST()
        bst.insert(20)
        bst.insert(10)
        _, actions = interpreter.apply_rules(
            bst.root.left, "PROPAGATE", return_flag=True
        )
        assert "SIGNAL_PROPAGATE" in actions

    def test_standalone_done_is_in_actions(self, interpreter):
        bst = BST()
        bst.insert(20)
        bst.insert(10)
        _, actions = interpreter.apply_rules(bst.root.left, "DONE", return_flag=True)
        assert "SIGNAL_DONE" in actions

    def test_conditional_propagate_fires_when_condition_true(self, interpreter):
        """PROPAGATE inside a rule appears in actions when its condition is met."""
        bst = BST()
        for v in [20, 10, 30]:
            bst.insert(v)
        bst.root.colour = "BLACK"
        bst.root.left.colour = "BLACK"
        bst.root.right.colour = "BLACK"  # sibling of left child is BLACK

        _, actions = interpreter.apply_rules(
            bst.root.left,
            'IF sibling_colour == "BLACK" THEN { SET_SIBLING_COLOUR "RED" PROPAGATE }',
            return_flag=True,
        )
        assert "SIGNAL_PROPAGATE" in actions

    def test_conditional_done_fires_when_condition_true(self, interpreter):
        """DONE inside a rule appears in actions when its condition is met."""
        bst = BST()
        for v in [20, 10, 30]:
            bst.insert(v)
        bst.root.colour = "BLACK"
        bst.root.left.colour = "BLACK"
        bst.root.right.colour = "BLACK"

        _, actions = interpreter.apply_rules(
            bst.root.left,
            'IF sibling_colour == "BLACK" THEN { SET_SIBLING_COLOUR_FROM_PARENT DONE }',
            return_flag=True,
        )
        assert "SIGNAL_DONE" in actions

    def test_propagate_not_in_actions_when_condition_false(self, interpreter):
        """PROPAGATE does NOT appear in actions when its rule condition is false."""
        bst = BST()
        for v in [20, 10, 30]:
            bst.insert(v)
        bst.root.right.colour = "RED"  # sibling is RED, not BLACK
        bst.root.left.colour = "BLACK"

        _, actions = interpreter.apply_rules(
            bst.root.left,
            'IF sibling_colour == "BLACK" THEN PROPAGATE',
            return_flag=True,
        )
        assert "SIGNAL_PROPAGATE" not in actions

    def test_done_not_in_actions_when_condition_false(self, interpreter):
        """DONE does NOT appear in actions when its rule condition is false."""
        bst = BST()
        for v in [20, 10, 30]:
            bst.insert(v)
        bst.root.right.colour = "RED"
        bst.root.left.colour = "BLACK"

        _, actions = interpreter.apply_rules(
            bst.root.left,
            'IF sibling_colour == "BLACK" THEN DONE',
            return_flag=True,
        )
        assert "SIGNAL_DONE" not in actions


# ── Sibling colour mutations ──────────────────────────────────────────────────


class TestSiblingColourActions:
    """SET_SIBLING_COLOUR, SET_SIBLING_LEFT_COLOUR, SET_SIBLING_RIGHT_COLOUR,
    and SET_SIBLING_COLOUR_FROM_PARENT mutate exactly the right node."""

    def _rb_tree(self):
        """3-node tree: 20(B) -> 10(R) left, 30(R) right."""
        bst = BST()
        for v in [20, 10, 30]:
            bst.insert(v)
        bst.root.colour = "BLACK"
        bst.root.left.colour = "RED"
        bst.root.right.colour = "RED"
        return bst

    def test_set_sibling_colour_changes_right_sibling(self, interpreter):
        """Applied to left child: changes the right sibling's colour."""
        bst = self._rb_tree()
        interpreter.apply_rules(bst.root.left, 'SET_SIBLING_COLOUR "BLACK"')
        assert bst.root.right.colour == "BLACK"
        assert bst.root.left.colour == "RED"  # own colour unchanged

    def test_set_sibling_colour_changes_left_sibling(self, interpreter):
        """Applied to right child: changes the left sibling's colour."""
        bst = self._rb_tree()
        interpreter.apply_rules(bst.root.right, 'SET_SIBLING_COLOUR "BLACK"')
        assert bst.root.left.colour == "BLACK"
        assert bst.root.right.colour == "RED"  # own colour unchanged

    def test_set_sibling_colour_is_noop_when_no_sibling(self, interpreter):
        """No exception when the target node has no sibling."""
        bst = BST()
        bst.insert(10)
        bst.insert(20)  # only child; no sibling
        interpreter.apply_rules(bst.root.right, 'SET_SIBLING_COLOUR "BLACK"')
        # Just checking no exception is raised; tree structure intact
        assert _inorder(bst.root) == [10, 20]

    def test_set_sibling_left_colour(self, interpreter):
        """SET_SIBLING_LEFT_COLOUR recolours the sibling's left child."""
        bst = BST()
        for v in [20, 10, 30, 25]:
            bst.insert(v)
        bst.root.colour = "BLACK"
        bst.root.left.colour = "BLACK"
        bst.root.right.colour = "BLACK"
        bst.root.right.left.colour = "RED"  # sibling's left child

        interpreter.apply_rules(bst.root.left, 'SET_SIBLING_LEFT_COLOUR "BLACK"')
        assert bst.root.right.left.colour == "BLACK"

    def test_set_sibling_right_colour(self, interpreter):
        """SET_SIBLING_RIGHT_COLOUR recolours the sibling's right child."""
        bst = BST()
        for v in [20, 10, 30, 35]:
            bst.insert(v)
        bst.root.colour = "BLACK"
        bst.root.left.colour = "BLACK"
        bst.root.right.colour = "BLACK"
        bst.root.right.right.colour = "RED"  # sibling's right child

        interpreter.apply_rules(bst.root.left, 'SET_SIBLING_RIGHT_COLOUR "BLACK"')
        assert bst.root.right.right.colour == "BLACK"

    def test_set_sibling_colour_from_parent_copies_black_parent(self, interpreter):
        """Parent BLACK → sibling gets BLACK."""
        bst = self._rb_tree()  # parent=20(B), sibling of left child=30(R)
        interpreter.apply_rules(bst.root.left, "SET_SIBLING_COLOUR_FROM_PARENT")
        assert bst.root.right.colour == "BLACK"

    def test_set_sibling_colour_from_parent_copies_red_parent(self, interpreter):
        """Parent RED → sibling gets RED."""
        bst = BST()
        for v in [20, 10, 30]:
            bst.insert(v)
        bst.root.colour = "RED"
        bst.root.left.colour = "BLACK"
        bst.root.right.colour = "BLACK"

        interpreter.apply_rules(bst.root.left, "SET_SIBLING_COLOUR_FROM_PARENT")
        assert bst.root.right.colour == "RED"


# ── Sibling rotations ─────────────────────────────────────────────────────────


class TestSiblingRotations:
    """ROTATE_LEFT_AT_SIBLING and ROTATE_RIGHT_AT_SIBLING restructure the
    correct subtree without raising exceptions."""

    def test_rotate_left_at_sibling_promotes_sibling_right_child(self, interpreter):
        """Left-rotating the right sibling makes its right child the new sibling.

        Before:        After rotating sibling (30) left:
            20(B)            20(B)
           /    \\           /    \\
         10(B) 30(B)       10(B) 40(R)
                  \\              /
                  40(R)         30(B)
        """
        bst = BST()
        for v in [20, 10, 30, 40]:
            bst.insert(v)
        bst.root.colour = "BLACK"
        bst.root.left.colour = "BLACK"
        bst.root.right.colour = "BLACK"
        bst.root.right.right.colour = "RED"

        interpreter.apply_rules(bst.root.left, "ROTATE_LEFT_AT_SIBLING")

        # The old sibling's right child (40) is now root's right child
        assert bst.root.right.val == 40
        assert _inorder(bst.root) == [10, 20, 30, 40]

    def test_rotate_right_at_sibling_promotes_sibling_left_child(self, interpreter):
        """Right-rotating the left sibling makes its left child the new sibling.

        Before:        After rotating sibling (10) right:
            20(B)            20(B)
           /    \\           /    \\
         10(B) 30(B)        5(R) 30(B)
         /                     \\
        5(R)                   10(B)
        """
        bst = BST()
        for v in [20, 10, 30, 5]:
            bst.insert(v)
        bst.root.colour = "BLACK"
        bst.root.left.colour = "BLACK"
        bst.root.right.colour = "BLACK"
        bst.root.left.left.colour = "RED"

        interpreter.apply_rules(bst.root.right, "ROTATE_RIGHT_AT_SIBLING")

        # The old sibling's left child (5) is now root's left child
        assert bst.root.left.val == 5
        assert _inorder(bst.root) == [5, 10, 20, 30]

    def test_rotate_left_at_sibling_is_noop_when_no_sibling(self, interpreter):
        """No exception when the node has no sibling."""
        bst = BST()
        bst.insert(10)
        bst.insert(20)  # only right child; has no sibling
        interpreter.apply_rules(bst.root.right, "ROTATE_LEFT_AT_SIBLING")
        assert _inorder(bst.root) == [10, 20]

    def test_rotate_right_at_sibling_is_noop_when_no_sibling(self, interpreter):
        """No exception when the node has no sibling."""
        bst = BST()
        bst.insert(30)
        bst.insert(20)  # only left child; has no sibling
        interpreter.apply_rules(bst.root.left, "ROTATE_RIGHT_AT_SIBLING")
        assert _inorder(bst.root) == [20, 30]


# ── ROTATE_*_AT_GRANDPARENT execution ────────────────────────────────────────


class TestRotateAtGrandparent:
    """Verify ROTATE_LEFT_AT_GRANDPARENT and ROTATE_RIGHT_AT_GRANDPARENT
    produce the correct new subtree root."""

    def test_rotate_left_at_grandparent_returns_grandparent_right_child(
        self, interpreter
    ):
        """Rotating left at grandparent (10) makes its right child (20) the new root.

        Before:        After:
          10(B)          20(R)
             \\          /    \\
             20(R)     10(B)  30(R)
                \\
                30(R)
        """
        bst = BST()
        for v in [10, 20, 30]:
            bst.insert(v)
        bst.root.colour = "BLACK"
        bst.root.right.colour = "RED"
        bst.root.right.right.colour = "RED"

        new_node = interpreter.apply_rules(
            bst.root.right.right, "ROTATE_LEFT_AT_GRANDPARENT"
        )
        assert new_node.val == 20

    def test_rotate_right_at_grandparent_returns_grandparent_left_child(
        self, interpreter
    ):
        """Rotating right at grandparent (30) makes its left child (20) the new root.

        Before:        After:
            30(B)         20(R)
            /            /    \\
          20(R)         10(R)  30(B)
          /
        10(R)
        """
        bst = BST()
        for v in [30, 20, 10]:
            bst.insert(v)
        bst.root.colour = "BLACK"
        bst.root.left.colour = "RED"
        bst.root.left.left.colour = "RED"

        new_node = interpreter.apply_rules(
            bst.root.left.left, "ROTATE_RIGHT_AT_GRANDPARENT"
        )
        assert new_node.val == 20

    def test_rotate_left_at_grandparent_in_rb_case3b(self, interpreter):
        """Full RB Case 3b uses ROTATE_LEFT_AT_GRANDPARENT correctly."""
        bst = BST()
        for v in [10, 20, 30]:
            bst.insert(v)
        bst.root.colour = "BLACK"
        bst.root.right.colour = "RED"
        bst.root.right.right.colour = "RED"

        script = (
            'IF node_colour == "RED" AND parent_colour == "RED" '
            'AND uncle_colour == "BLACK" '
            "AND parent_is_left_child == 0 AND is_left_child == 0 THEN { "
            'SET_PARENT_COLOUR "BLACK" '
            'SET_GRANDPARENT_COLOUR "RED" '
            "ROTATE_LEFT_AT_GRANDPARENT }"
        )
        new_root = interpreter.apply_rules(bst.root.right.right, script)
        assert new_root.val == 20
        assert new_root.colour == "BLACK"
        assert new_root.left.val == 10
        assert new_root.right.val == 30


# ── Grammar error cases ───────────────────────────────────────────────────────


class TestGrammarErrors:
    """Common mistakes produce the expected parse errors."""

    def test_unclosed_brace_raises_unexpected_input(self, interpreter):
        """A { without a closing } is always a syntax error."""
        with pytest.raises(UnexpectedInput):
            interpreter.parser.parse("IF balance_factor > 1 THEN {\n    ROTATE_RIGHT\n")

    def test_unclosed_brace_error_is_on_last_action_line(self, interpreter):
        """Lark reports the error on the line of the last action in the block."""
        with pytest.raises(UnexpectedInput) as exc_info:
            interpreter.parser.parse(
                "IF balance_factor > 1 THEN {\n"
                "    ROTATE_RIGHT\n"
                "    ROTATE_LEFT_AT_GRANDPARENT\n"  # line 3
            )
        assert exc_info.value.line == 3

    def test_signal_propagate_internal_name_raises(self, interpreter):
        """SIGNAL_PROPAGATE is the grammar's internal token name, not a keyword."""
        with pytest.raises(Exception):
            interpreter.parser.parse("SIGNAL_PROPAGATE")

    def test_signal_done_internal_name_raises(self, interpreter):
        """SIGNAL_DONE is the grammar's internal token name, not a keyword."""
        with pytest.raises(Exception):
            interpreter.parser.parse("SIGNAL_DONE")

    def test_sensor_used_as_action_raises(self, interpreter):
        """A sensor keyword cannot appear where an action is expected."""
        with pytest.raises(UnexpectedInput):
            interpreter.parser.parse("IF balance_factor > 1 THEN balance_factor")

    def test_missing_if_keyword_raises(self, interpreter):
        """A bare condition without IF is not valid DSL."""
        with pytest.raises(UnexpectedInput):
            interpreter.parser.parse("balance_factor > 1 THEN ROTATE_RIGHT")

    def test_missing_then_keyword_raises(self, interpreter):
        with pytest.raises(UnexpectedInput):
            interpreter.parser.parse("IF balance_factor > 1 ROTATE_RIGHT")

    def test_unknown_identifier_raises(self, interpreter):
        """An unrecognised word in keyword position raises a parse error."""
        with pytest.raises(Exception):
            interpreter.parser.parse("IF fake_sensor > 1 THEN ROTATE_RIGHT")


# ── Misc / integration ────────────────────────────────────────────────────────


class TestMiscFeatures:
    """height sensor, first-match-wins semantics, multi-rule scripts."""

    def test_height_sensor_triggers_correct_rule(self, interpreter):
        """The height sensor reflects actual node height."""
        bst = BST()
        for v in [30, 20, 10]:  # root height = 3
            bst.insert(v)
        new_root = interpreter.apply_rules(bst.root, "IF height > 2 THEN ROTATE_RIGHT")
        assert new_root.val == 20

    def test_height_sensor_does_not_trigger_when_too_small(self, interpreter):
        bst = BST()
        bst.insert(20)  # single-node tree, height = 1
        new_root = interpreter.apply_rules(
            bst.root, 'IF height > 1 THEN SET_COLOUR "BLACK"'
        )
        assert new_root is bst.root  # no change

    def test_first_match_wins_only_first_rule_fires(self, interpreter):
        """When two rules both match, only the first one executes."""
        bst = BST()
        bst.insert(50)
        bst.root.colour = "RED"

        # Both rules would match; only the first should execute.
        script = (
            'IF node_colour == "RED" THEN SET_COLOUR "BLACK"\n'
            'IF node_colour == "RED" THEN SET_COLOUR "RED"\n'  # would undo the first
        )
        new_root = interpreter.apply_rules(bst.root, script)
        # If first-match-wins is correct the node stays BLACK (second rule not evaluated)
        assert new_root.colour == "BLACK"

    def test_second_rule_fires_when_first_does_not_match(self, interpreter):
        """The second rule executes when the first condition is false."""
        bst = BST()
        for v in [10, 20, 30]:  # root bf = -2
            bst.insert(v)

        script = (
            "IF balance_factor > 1 THEN ROTATE_RIGHT\n"  # False for bf=-2
            "IF balance_factor < -1 THEN ROTATE_LEFT\n"  # True  for bf=-2
        )
        new_root = interpreter.apply_rules(bst.root, script)
        assert new_root.val == 20

    def test_is_left_child_returns_zero_for_root(self, interpreter):
        """The root node has no parent, so is_left_child == 0."""
        bst = BST()
        bst.insert(50)
        bst.root.colour = "RED"
        # is_left_child == 0 should be True for root → colour changes
        interpreter.apply_rules(
            bst.root, 'IF is_left_child == 0 THEN SET_COLOUR "BLACK"'
        )
        assert bst.root.colour == "BLACK"

    def test_multi_action_block_all_actions_execute(self, interpreter):
        """Every action in a { } block executes, not just the first."""
        bst = BST()
        for v in [20, 10, 30]:
            bst.insert(v)
        bst.root.colour = "BLACK"
        bst.root.left.colour = "RED"
        bst.root.right.colour = "RED"
        bst.root.left.parent = bst.root

        script = (
            'IF node_colour == "RED" AND parent_colour == "BLACK" THEN { '
            'SET_COLOUR "BLACK" '
            'SET_PARENT_COLOUR "RED" }'
        )
        interpreter.apply_rules(bst.root.left, script)
        assert bst.root.left.colour == "BLACK"  # SET_COLOUR fired
        assert bst.root.colour == "RED"  # SET_PARENT_COLOUR fired

    def test_comment_only_lines_are_ignored(self, interpreter):
        """Comments interspersed with rules do not affect execution."""
        bst = BST()
        for v in [30, 20, 10]:
            bst.insert(v)
        script = (
            "# left-heavy: rotate right\n"
            "IF balance_factor > 1 THEN ROTATE_RIGHT\n"
            "# done\n"
        )
        new_root = interpreter.apply_rules(bst.root, script)
        assert new_root.val == 20
