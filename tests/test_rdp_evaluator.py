"""Tests for the RDP Evaluator to ensure it mirrors BalancingLogic perfectly."""
import pytest
from dsl.rdp_parser import RDPParser
from dsl.rdp_evaluator import RDPEvaluator
from tree import BST

@pytest.fixture
def rdp_parser():
    return RDPParser()

def evaluate_script(script, tree_node=None):
    parser = RDPParser()
    ast = parser.parse(script)
    evaluator = RDPEvaluator(tree_node)
    return evaluator.evaluate(ast)

class TestRDPEvaluator:
    def test_eval_simple_action(self):
        script = 'IF balance_factor > 1 THEN ROTATE_RIGHT'
        bst = BST()
        # insert 30, 20, 10 to make a left-heavy tree (root balance_factor = 2)
        for v in [30, 20, 10]:
            bst.insert(v)
            
        actions = evaluate_script(script, bst.root)
        assert actions == ["ROTATE_RIGHT"]

    def test_eval_no_action_when_condition_false(self):
        script = 'IF balance_factor > 1 THEN ROTATE_RIGHT'
        bst = BST()
        # balanced tree
        for v in [20, 10, 30]:
            bst.insert(v)
            
        actions = evaluate_script(script, bst.root)
        assert actions == [] # Rule condition is false, returns empty list from Program level

    def test_eval_set_colour(self):
        script = 'IF node_colour == "RED" THEN SET_COLOUR "BLACK"'
        bst = BST()
        bst.insert(50) # default RED
        actions = evaluate_script(script, bst.root)
        assert actions == [("SET_COLOUR", "BLACK")]
        
    def test_eval_arithmetic_and_logic(self):
        # BF is 2, so 2 - 1 > 0 is True
        script = 'IF balance_factor - 1 > 0 AND NOT node_colour == "BLACK" THEN ROTATE_RIGHT'
        bst = BST()
        for v in [30, 20, 10]:
            bst.insert(v)
        actions = evaluate_script(script, bst.root)
        assert actions == ["ROTATE_RIGHT"]

    def test_eval_uncle_and_parent_colour(self):
        """Build a tree where root=50, L=25, R=75, L.L=10. Verify uncle colour."""
        bst = BST()
        for v in [50, 25, 75, 10]:
            bst.insert(v)
        
        # Colour them
        bst.root.left.colour = "BLACK"    # Parent (25) is BLACK
        bst.root.right.colour = "RED"     # Uncle (75) is RED
        
        # Test from the perspective of 10
        # Its parent is 25 (BLACK), its uncle is 75 (RED)
        script = 'IF parent_colour == "BLACK" AND uncle_colour == "RED" THEN SET_COLOUR "BLACK"'
        actions = evaluate_script(script, bst.root.left.left)
        assert actions == [("SET_COLOUR", "BLACK")]
        
    def test_eval_insert_delete_actions(self):
        script = 'INSERT 10 DELETE 20'
        actions = evaluate_script(script, None)
        assert actions == [("INSERT", 10), ("DELETE", 20)]

    def test_eval_missing_sensor(self):
        script = 'IF fake_sensor > 1 THEN ROTATE_RIGHT'
        # The lexer will fail on fake_sensor as it's not a known keyword
        from dsl.rdp_parser import LexerError
        with pytest.raises(LexerError):
            evaluate_script(script, None)

    def test_eval_set_parent_colour(self):
        """SET_PARENT_COLOUR returns the correct tagged tuple."""
        script = 'SET_PARENT_COLOUR "BLACK"'
        actions = evaluate_script(script, None)
        assert actions == [("SET_PARENT_COLOUR", "BLACK")]

    def test_eval_set_uncle_colour(self):
        """SET_UNCLE_COLOUR returns the correct tagged tuple."""
        script = 'SET_UNCLE_COLOUR "BLACK"'
        actions = evaluate_script(script, None)
        assert actions == [("SET_UNCLE_COLOUR", "BLACK")]

    def test_eval_set_grandparent_colour(self):
        """SET_GRANDPARENT_COLOUR returns the correct tagged tuple."""
        script = 'SET_GRANDPARENT_COLOUR "RED"'
        actions = evaluate_script(script, None)
        assert actions == [("SET_GRANDPARENT_COLOUR", "RED")]

    def test_eval_rb_case1_block(self):
        """A full RB Case 1 action block evaluates to three colour tuples."""
        script = ('IF node_colour == "RED" AND parent_colour == "RED" '
                  'AND uncle_colour == "RED" THEN { '
                  'SET_PARENT_COLOUR "BLACK" '
                  'SET_UNCLE_COLOUR "BLACK" '
                  'SET_GRANDPARENT_COLOUR "RED" }')
        bst = BST()
        bst.insert(10)
        bst.insert(5)
        bst.insert(20)
        bst.insert(25)
        bst.root.colour = "BLACK"
        bst.root.left.colour = "RED"
        bst.root.right.colour = "RED"
        bst.root.right.right.colour = "RED"
        # From perspective of node 25: parent=20(RED), uncle=5(RED)
        actions = evaluate_script(script, bst.root.right.right)
        assert actions == [
            ("SET_PARENT_COLOUR", "BLACK"),
            ("SET_UNCLE_COLOUR", "BLACK"),
            ("SET_GRANDPARENT_COLOUR", "RED"),
        ]

