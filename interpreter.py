import os
import copy
from lark import Lark, Tree, Transformer, v_args
from tree import BST, TreeNode

# ==========================================
# 1. The Logic Evaluator (Transformer)
# ==========================================
@v_args(inline=True)
class BalancingLogic(Transformer):
    def __init__(self, current_node):
        self.node = current_node

    # --- Primitives ---
    def number(self, n):
        return float(n)

    # --- Tree Properties (Sensors) ---
    def get_height(self, _):
        return self.node.height if self.node else 0

    def get_balance(self, _):
        if not self.node: return 0
        left_h = self.node.left.height if self.node.left else 0
        right_h = self.node.right.height if self.node.right else 0
        return left_h - right_h

    def get_left_balance(self, _):
        if not self.node or not self.node.left: return 0
        left_h = self.node.left.left.height if self.node.left.left else 0
        right_h = self.node.left.right.height if self.node.left.right else 0
        return left_h - right_h
    
    def get_right_balance(self, _):
        if not self.node or not self.node.right: return 0
        left_h = self.node.right.left.height if self.node.right.left else 0
        right_h = self.node.right.right.height if self.node.right.right else 0
        return left_h - right_h
    
    def get_colour(self, _):
        return self.node.colour if self.node else "BLACK"

    def get_parent_colour(self, _):
        """Return the colour of the current node's parent (BLACK if root)."""
        if self.node and self.node.parent:
            return self.node.parent.colour
        return 'BLACK'

    def get_uncle_colour(self, _):
        """Return the colour of the current node's uncle (BLACK if absent)."""
        if not self.node or not self.node.parent or not self.node.parent.parent:
            return 'BLACK'
        grandparent = self.node.parent.parent
        if grandparent.left is self.node.parent:
            uncle = grandparent.right
        else:
            uncle = grandparent.left
        return uncle.colour if uncle else 'BLACK'

    @staticmethod
    def _parse_colour(colour_str):
        """Extract a clean colour string from a Lark tree or plain string."""
        raw = str(colour_str.children[0]) if hasattr(colour_str, 'children') else str(colour_str)
        return raw.strip('"').upper()

    @staticmethod
    def _get_uncle(node):
        """Return the uncle node (or None) for a given node."""
        if not node or not node.parent or not node.parent.parent:
            return None
        grandparent = node.parent.parent
        if grandparent.left is node.parent:
            return grandparent.right
        return grandparent.left

    def set_colour(self, colour_str):
        """Handle SET_COLOUR action — returns a tuple for the action loop."""
        return ("SET_COLOUR", self._parse_colour(colour_str))

    def set_parent_colour(self, colour_str):
        """Handle SET_PARENT_COLOUR — recolour current node's parent."""
        return ("SET_PARENT_COLOUR", self._parse_colour(colour_str))

    def set_uncle_colour(self, colour_str):
        """Handle SET_UNCLE_COLOUR — recolour current node's uncle."""
        return ("SET_UNCLE_COLOUR", self._parse_colour(colour_str))

    def set_grandparent_colour(self, colour_str):
        """Handle SET_GRANDPARENT_COLOUR — recolour current node's grandparent."""
        return ("SET_GRANDPARENT_COLOUR", self._parse_colour(colour_str))

    def string(self, s):
        return str(s)

    def string_literal(self, s):
        """Return a bare string (strip quotes) for use in comparisons."""
        return str(s).strip('"')

    # --- Arithmetic ---
    def add_expr(self, left, right):
        return float(left) + float(right)

    def sub_expr(self, left, right):
        return float(left) - float(right)

    def term(self, val):
        return val

    def expression(self, val):
        """Pass-through for expression: term (no arithmetic)."""
        return val

    # --- Comparisons ---
    def comparison(self, val1, op, val2):
        # Robust Operator Extraction
        operator = getattr(op, 'value', str(op))

        # Try numeric comparison first, fall back to string for colours
        try:
            v1 = float(val1)
            v2 = float(val2)
        except (ValueError, TypeError):
            # String comparison (e.g. node_colour == "RED")
            v1 = str(val1).strip('"').upper()
            v2 = str(val2).strip('"').upper()

        if operator == ">": return v1 > v2
        if operator == "<": return v1 < v2
        if operator == "==": return v1 == v2
        if operator == "!=": return v1 != v2
        if operator == ">=": return v1 >= v2
        if operator == "<=": return v1 <= v2
        return False

    # --- Boolean Logic ---
    def and_expr(self, cond1, cond2):
        return cond1 and cond2

    def or_expr(self, cond1, cond2):
        return cond1 or cond2

    def not_expr(self, cond):
        return not cond

    # --- Actions ---
    def action_block(self, *actions):
        return list(actions)

    def rotate_left(self, _):
        return "ROTATE_LEFT"

    def rotate_right(self, _):
        return "ROTATE_RIGHT"

    def rotate_left_right(self, _):
        return "ROTATE_LEFT_RIGHT"

    def rotate_right_left(self, _):
        return "ROTATE_RIGHT_LEFT"

    def insert_cmd(self, n):
        return ("INSERT", int(float(n)))

    def delete_cmd(self, n):
        return ("DELETE", int(float(n)))

    def rule(self, condition, actions):
        # Extract the actual boolean value from the Tree object
        actual_condition = condition
        if hasattr(condition, 'children') and condition.children:
            actual_condition = condition.children[0]
        
        if actual_condition:
            return actions
        return None

    def start(self, *items):
        triggered_actions = []
        for item in items:
            if item:
                # If it's a list (from rules), extend it
                if isinstance(item, list):
                    triggered_actions.extend(item)
                # If it's a single action (from direct actions), add it
                else:
                    triggered_actions.append(item)
        return triggered_actions


# ==========================================
# 2. The Interpreter Engine
# ==========================================

class DSLInterpreter:
    def __init__(self, grammar_file="grammar.lark"):
        # The Path Fix:
        # Finds grammar.lark in the same directory as this script (DSL/)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        grammar_path = os.path.join(base_dir, grammar_file)

        with open(grammar_path, "r") as f:
            self.parser = Lark(f.read(), start="start", parser="lalr")

    def apply_rules(self, node, dsl_input):
        if not node:
            return None

        # Accept either a raw DSL string or a pre-parsed Lark Tree
        if isinstance(dsl_input, Tree):
            parsed_tree = dsl_input
        else:
            try:
                parsed_tree = self.parser.parse(dsl_input)
            except Exception as e:
                print(f"Syntax Error in DSL: {e}")
                return node

        # Evaluate the AST with this node's context
        # Deep-copy because Lark's transform mutates the tree in place
        evaluator = BalancingLogic(node)
        actions = evaluator.transform(copy.deepcopy(parsed_tree))

        # 3. Execute
        new_root = node
        tree_ops = BST() 

        for action in actions:
            if action == "ROTATE_LEFT":
                new_root = tree_ops.rotate_left(new_root)
            elif action == "ROTATE_RIGHT":
                new_root = tree_ops.rotate_right(new_root)
            elif action == "ROTATE_LEFT_RIGHT":
                new_root = tree_ops.rotate_left_right(new_root)
            elif action == "ROTATE_RIGHT_LEFT":
                new_root = tree_ops.rotate_right_left(new_root)
            elif isinstance(action, tuple) and action[0] == "SET_COLOUR":
                new_root.colour = action[1]
            elif isinstance(action, tuple) and action[0] == "SET_PARENT_COLOUR":
                if new_root.parent:
                    new_root.parent.colour = action[1]
            elif isinstance(action, tuple) and action[0] == "SET_UNCLE_COLOUR":
                uncle = BalancingLogic._get_uncle(new_root)
                if uncle:
                    uncle.colour = action[1]
            elif isinstance(action, tuple) and action[0] == "SET_GRANDPARENT_COLOUR":
                if new_root.parent and new_root.parent.parent:
                    new_root.parent.parent.colour = action[1]
        
        return new_root

    def balance_step(self, node, parsed_tree):
        """Apply EXACTLY ONE rotation (the first found bottom-up) and return.

        Returns (new_node, changed) where *changed* is True when a rotation
        was performed during this call.  The caller can keep calling this
        method until *changed* comes back False to animate one rotation per
        frame.
        """
        if not node:
            return node, False

        # Recurse left first
        node.left, changed = self.balance_step(node.left, parsed_tree)
        if changed:
            node.height = 1 + max(
                node.left.height if node.left else 0,
                node.right.height if node.right else 0,
            )
            return node, True

        # Then right
        node.right, changed = self.balance_step(node.right, parsed_tree)
        if changed:
            node.height = 1 + max(
                node.left.height if node.left else 0,
                node.right.height if node.right else 0,
            )
            return node, True

        # Update height at this node
        node.height = 1 + max(
            node.left.height if node.left else 0,
            node.right.height if node.right else 0,
        )

        # Try to apply rules at this node
        new_root = self.apply_rules(node, parsed_tree)
        if new_root is not node:
            return new_root, True

        return node, False

    def execute_script(self, dsl_script):
        """Parse a full DSL script and return a flat list of actions.

        Each action is either a rotation string (e.g. ``"ROTATE_LEFT"``) or
        a tuple like ``("INSERT", 10)`` / ``("DELETE", 20)``.
        Rules whose conditions are False produce no actions.
        """
        parsed_tree = self.parser.parse(dsl_script)  # caller handles errors
        evaluator = BalancingLogic(current_node=None)
        return evaluator.transform(copy.deepcopy(parsed_tree))

    def balance_tree(self, node, dsl_script):
        if not node:
            return None

        # Parse the DSL script exactly once, then pass the AST down
        try:
            parsed_tree = self.parser.parse(dsl_script)
        except Exception as e:
            print(f"Syntax Error in DSL: {e}")
            return node

        return self._balance_recursive(node, parsed_tree)

    def _balance_recursive(self, node, parsed_tree):
        if not node:
            return None

        # Post-Order Traversal (Bottom-Up)
        node.left = self._balance_recursive(node.left, parsed_tree)
        node.right = self._balance_recursive(node.right, parsed_tree)

        # Update height before applying rules
        node.height = 1 + max(
            node.left.height if node.left else 0,
            node.right.height if node.right else 0
        )

        return self.apply_rules(node, parsed_tree)