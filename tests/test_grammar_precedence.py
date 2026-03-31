"""Tests for grammar-level operator precedence — NOT > AND > OR.

These tests inspect the Lark parse-tree *structure* to verify that
the grammar correctly implements standard boolean operator precedence
without relying on the runtime evaluator.
"""
import pytest
from interpreter import DSLInterpreter


@pytest.fixture
def parser():
    return DSLInterpreter().parser


class TestNotPrecedence:
    """NOT must bind tighter than AND and OR."""

    def test_not_binds_tighter_than_and(self, parser):
        """``NOT X AND Y`` must parse as ``(NOT X) AND Y``."""
        tree = parser.parse(
            "IF NOT balance_factor > 1 AND height > 5 THEN ROTATE_RIGHT"
        )
        rule = tree.children[0]  # the rule node
        condition = rule.children[0]  # top-level condition

        # Top-level should be and_expr with NOT on the left
        assert condition.data == "and_expr"
        left, right = condition.children
        assert left.data == "not_expr"
        assert right.data == "comparison"

    def test_not_binds_tighter_than_or(self, parser):
        """``NOT X OR Y`` must parse as ``(NOT X) OR Y``."""
        tree = parser.parse(
            "IF NOT balance_factor > 1 OR height > 5 THEN ROTATE_RIGHT"
        )
        rule = tree.children[0]
        condition = rule.children[0]

        assert condition.data == "or_expr"
        left, right = condition.children
        assert left.data == "not_expr"
        assert right.data == "comparison"

    def test_explicit_parens_match_implicit(self, parser):
        """``(NOT X) AND Y`` must produce same structure as ``NOT X AND Y``."""
        implicit = parser.parse(
            "IF NOT balance_factor > 1 AND height > 5 THEN ROTATE_RIGHT"
        )
        explicit = parser.parse(
            "IF (NOT balance_factor > 1) AND height > 5 THEN ROTATE_RIGHT"
        )
        # Both should produce and_expr at the top with not_expr on the left
        assert implicit.children[0].children[0].data == "and_expr"
        assert explicit.children[0].children[0].data == "and_expr"
        assert implicit.children[0].children[0].children[0].data == "not_expr"
        assert explicit.children[0].children[0].children[0].data == "not_expr"

    def test_not_entire_or_with_parens(self, parser):
        """``NOT (X OR Y)`` wraps the whole OR — NOT takes the paren group."""
        tree = parser.parse(
            "IF NOT (balance_factor > 1 OR height > 5) THEN ROTATE_RIGHT"
        )
        rule = tree.children[0]
        condition = rule.children[0]

        assert condition.data == "not_expr"
        inner = condition.children[0]
        assert inner.data == "or_expr"


class TestAndOrPrecedence:
    """AND must bind tighter than OR."""

    def test_and_binds_tighter_than_or(self, parser):
        """``A AND B OR C`` must parse as ``(A AND B) OR C``."""
        tree = parser.parse(
            "IF balance_factor > 1 AND height > 2 OR height > 5 THEN ROTATE_RIGHT"
        )
        rule = tree.children[0]
        condition = rule.children[0]

        assert condition.data == "or_expr"
        left, right = condition.children
        assert left.data == "and_expr"
        assert right.data == "comparison"

    def test_or_then_and(self, parser):
        """``A OR B AND C`` must parse as ``A OR (B AND C)``."""
        tree = parser.parse(
            "IF balance_factor > 1 OR height > 2 AND height > 5 THEN ROTATE_RIGHT"
        )
        rule = tree.children[0]
        condition = rule.children[0]

        assert condition.data == "or_expr"
        left, right = condition.children
        assert left.data == "comparison"
        assert right.data == "and_expr"


class TestAdvancedLogicParsing:
    """Verify parse trees for the real rules in advanced_logic.dsl."""

    def test_rule3_compound_condition(self, parser):
        """Rule 3: NOT (height > 5) AND (bf > 1 OR lb < 0)
        must parse as (NOT(height>5)) AND (bf>1 OR lb<0)."""
        tree = parser.parse(
            "IF NOT (height > 5) AND (balance_factor > 1 OR left_child_balance < 0)"
            " THEN ROTATE_LEFT_RIGHT"
        )
        rule = tree.children[0]
        condition = rule.children[0]

        # Top level: and_expr
        assert condition.data == "and_expr", (
            f"Expected and_expr at top level, got {condition.data}"
        )
        left, right = condition.children
        # Left: NOT(height > 5)
        assert left.data == "not_expr"
        # Right: or_expr(bf > 1, lb < 0)
        assert right.data == "or_expr"

    def test_rule1_not_in_and(self, parser):
        """Rule 1: ... AND NOT (is_left_child == 1 OR ...) still works."""
        tree = parser.parse(
            'IF (balance_factor + right_child_balance > 2) AND '
            'NOT (is_left_child == 1 OR parent_is_left_child == 1) THEN ROTATE_LEFT'
        )
        rule = tree.children[0]
        condition = rule.children[0]

        # Top level: and_expr
        assert condition.data == "and_expr"
        left, right = condition.children
        assert left.data == "comparison"
        assert right.data == "not_expr"
        # Inside NOT: or_expr
        assert right.children[0].data == "or_expr"
