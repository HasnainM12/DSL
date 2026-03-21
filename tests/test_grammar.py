"""Tests for grammar.lark — parsing valid and invalid DSL scripts."""
import pytest
from lark.exceptions import UnexpectedInput


# ============================================================
# Valid Parsing
# ============================================================
class TestValidParsing:
    def test_valid_avl_script_parses(self, interpreter):
        script = "IF balance_factor > 1 THEN ROTATE_RIGHT"
        tree = interpreter.parser.parse(script)
        assert tree is not None

    def test_arithmetic_in_condition(self, interpreter):
        script = "IF balance_factor + 1 > 2 THEN ROTATE_RIGHT"
        tree = interpreter.parser.parse(script)
        assert tree is not None

    def test_subtraction_in_condition(self, interpreter):
        script = "IF balance_factor - 1 > 0 THEN ROTATE_LEFT"
        tree = interpreter.parser.parse(script)
        assert tree is not None

    def test_not_condition(self, interpreter):
        script = 'IF NOT node_colour == "RED" THEN ROTATE_LEFT'
        tree = interpreter.parser.parse(script)
        assert tree is not None

    def test_parent_colour_keyword(self, interpreter):
        script = 'IF parent_colour == "RED" THEN ROTATE_RIGHT'
        tree = interpreter.parser.parse(script)
        assert tree is not None

    def test_uncle_colour_keyword(self, interpreter):
        script = 'IF uncle_colour == "RED" THEN SET_COLOUR "BLACK"'
        tree = interpreter.parser.parse(script)
        assert tree is not None

    def test_complex_red_black_rule(self, interpreter):
        script = 'IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "RED" THEN { SET_COLOUR "BLACK" }'
        tree = interpreter.parser.parse(script)
        assert tree is not None

    def test_action_block_multiple_actions(self, interpreter):
        script = 'IF balance_factor > 1 THEN { ROTATE_RIGHT SET_COLOUR "BLACK" }'
        tree = interpreter.parser.parse(script)
        assert tree is not None

    def test_or_condition(self, interpreter):
        script = "IF balance_factor > 1 OR balance_factor < -1 THEN ROTATE_RIGHT"
        tree = interpreter.parser.parse(script)
        assert tree is not None

    def test_parenthesized_condition(self, interpreter):
        script = "IF (balance_factor > 1 AND left_child_balance < 0) THEN ROTATE_LEFT_RIGHT"
        tree = interpreter.parser.parse(script)
        assert tree is not None

    def test_avl_dsl_file_parses(self, interpreter):
        import os
        dsl_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'avl.dsl')
        with open(dsl_path) as f:
            tree = interpreter.parser.parse(f.read())
        assert tree is not None

    def test_red_black_dsl_file_parses(self, interpreter):
        import os
        dsl_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'red-black.dsl')
        with open(dsl_path) as f:
            tree = interpreter.parser.parse(f.read())
        assert tree is not None

    def test_set_parent_colour_parses(self, interpreter):
        script = 'SET_PARENT_COLOUR "BLACK"'
        tree = interpreter.parser.parse(script)
        assert tree is not None

    def test_set_uncle_colour_parses(self, interpreter):
        script = 'SET_UNCLE_COLOUR "BLACK"'
        tree = interpreter.parser.parse(script)
        assert tree is not None

    def test_set_grandparent_colour_parses(self, interpreter):
        script = 'SET_GRANDPARENT_COLOUR "RED"'
        tree = interpreter.parser.parse(script)
        assert tree is not None

    def test_rb_case1_action_block_parses(self, interpreter):
        script = ('IF node_colour == "RED" AND parent_colour == "RED" '
                  'AND uncle_colour == "RED" THEN { '
                  'SET_PARENT_COLOUR "BLACK" '
                  'SET_UNCLE_COLOUR "BLACK" '
                  'SET_GRANDPARENT_COLOUR "RED" }')
        tree = interpreter.parser.parse(script)
        assert tree is not None


# ============================================================
# Invalid Parsing
# ============================================================
class TestInvalidParsing:
    def test_invalid_script_raises(self, interpreter):
        with pytest.raises(UnexpectedInput):
            interpreter.parser.parse("GIBBERISH nonsense >>>")

    def test_missing_then_keyword(self, interpreter):
        with pytest.raises(UnexpectedInput):
            interpreter.parser.parse("IF balance_factor > 1 ROTATE_RIGHT")

    def test_missing_condition(self, interpreter):
        with pytest.raises(UnexpectedInput):
            interpreter.parser.parse("IF THEN ROTATE_RIGHT")

    def test_empty_string_raises(self, interpreter):
        with pytest.raises(UnexpectedInput):
            interpreter.parser.parse("")
