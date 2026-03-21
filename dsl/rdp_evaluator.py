"""
rdp_evaluator.py — Evaluator for the hand-written RDP AST.

This module provides an RDPEvaluator class that traverses the dataclass-based
AST produced by RDPParser. It perfectly mirrors the behaviour of Lark's
BalancingLogic transformer, allowing the backend to be swapped seamlessly.
"""

from dsl.rdp_parser import (
    ProgramNode, RuleNode, ActionNode, ComparisonNode,
    AndNode, OrNode, NotNode, BinOpNode, NumberNode, KeywordNode, StringNode
)


class RDPEvaluator:
    """Evaluates an RDP AST against a concrete tree node context."""

    def __init__(self, current_node):
        self.node = current_node

    def evaluate(self, ast_node):
        """Recursively evaluate an AST node, returning values or actions."""
        if isinstance(ast_node, ProgramNode):
            return self._eval_program(ast_node)
        elif isinstance(ast_node, RuleNode):
            return self._eval_rule(ast_node)
        elif isinstance(ast_node, ActionNode):
            return self._eval_action(ast_node)
        elif isinstance(ast_node, ComparisonNode):
            return self._eval_comparison(ast_node)
        elif isinstance(ast_node, AndNode):
            return self._eval_and(ast_node)
        elif isinstance(ast_node, OrNode):
            return self._eval_or(ast_node)
        elif isinstance(ast_node, NotNode):
            return self._eval_not(ast_node)
        elif isinstance(ast_node, BinOpNode):
            return self._eval_binop(ast_node)
        elif isinstance(ast_node, NumberNode):
            return ast_node.value
        elif isinstance(ast_node, StringNode):
            return ast_node.value
        elif isinstance(ast_node, KeywordNode):
            return self._eval_keyword(ast_node)
        else:
            raise ValueError(f"Unknown AST node type: {type(ast_node)}")

    # --- Node Evaluation Methods ---

    def _eval_program(self, node: ProgramNode):
        triggered_actions = []
        for item in node.items:
            result = self.evaluate(item)
            if result is not None:
                if isinstance(result, list):
                    triggered_actions.extend(result)
                else:
                    triggered_actions.append(result)
        return triggered_actions

    def _eval_rule(self, node: RuleNode):
        condition_met = self.evaluate(node.condition)
        if condition_met:
            return [self.evaluate(a) for a in node.actions]
        return None

    def _eval_action(self, node: ActionNode):
        # String match on the action_type to replicate the DSL rule names
        if node.action_type in ("ROTATE_LEFT", "ROTATE_RIGHT", 
                                "ROTATE_LEFT_RIGHT", "ROTATE_RIGHT_LEFT"):
            return node.action_type
        
        if node.action_type == "SET_COLOUR":
            return ("SET_COLOUR", str(node.argument).strip('"').upper())
        
        if node.action_type == "SET_PARENT_COLOUR":
            return ("SET_PARENT_COLOUR", str(node.argument).strip('"').upper())

        if node.action_type == "SET_UNCLE_COLOUR":
            return ("SET_UNCLE_COLOUR", str(node.argument).strip('"').upper())

        if node.action_type == "SET_GRANDPARENT_COLOUR":
            return ("SET_GRANDPARENT_COLOUR", str(node.argument).strip('"').upper())

        if node.action_type == "INSERT":
            return ("INSERT", int(float(node.argument)))
            
        if node.action_type == "DELETE":
            return ("DELETE", int(float(node.argument)))
            
        raise ValueError(f"Unknown action: {node.action_type}")

    def _eval_comparison(self, node: ComparisonNode):
        val1 = self.evaluate(node.left)
        val2 = self.evaluate(node.right)

        # Try numeric comparison first, fall back to string comparison
        try:
            v1 = float(val1)
            v2 = float(val2)
        except (ValueError, TypeError):
            # String comparison fallback (e.g. node_colour == "RED")
            v1 = str(val1).strip('"').upper()
            v2 = str(val2).strip('"').upper()

        op = node.op
        if op == ">": return v1 > v2
        if op == "<": return v1 < v2
        if op == "==": return v1 == v2
        if op == "!=": return v1 != v2
        if op == ">=": return v1 >= v2
        if op == "<=": return v1 <= v2
        return False

    def _eval_and(self, node: AndNode):
        return self.evaluate(node.left) and self.evaluate(node.right)

    def _eval_or(self, node: OrNode):
        return self.evaluate(node.left) or self.evaluate(node.right)

    def _eval_not(self, node: NotNode):
        return not self.evaluate(node.operand)

    def _eval_binop(self, node: BinOpNode):
        left = float(self.evaluate(node.left))
        right = float(self.evaluate(node.right))
        if node.op == '+':
            return left + right
        elif node.op == '-':
            return left - right
        raise ValueError(f"Unknown binary operator: {node.op}")

    def _eval_keyword(self, node: KeywordNode):
        kw = node.name
        
        if kw == "height":
            return self.node.height if self.node else 0
            
        if kw == "balance_factor":
            if not self.node: return 0
            left_h = self.node.left.height if self.node.left else 0
            right_h = self.node.right.height if self.node.right else 0
            return left_h - right_h
            
        if kw == "left_child_balance":
            if not self.node or not self.node.left: return 0
            left_h = self.node.left.left.height if self.node.left.left else 0
            right_h = self.node.left.right.height if self.node.left.right else 0
            return left_h - right_h
            
        if kw == "right_child_balance":
            if not self.node or not self.node.right: return 0
            left_h = self.node.right.left.height if self.node.right.left else 0
            right_h = self.node.right.right.height if self.node.right.right else 0
            return left_h - right_h
            
        if kw == "node_colour":
            return getattr(self.node, 'colour', 'BLACK')
            
        if kw == "parent_colour":
            if self.node and getattr(self.node, 'parent', None):
                return getattr(self.node.parent, 'colour', 'BLACK')
            return 'BLACK'
            
        if kw == "uncle_colour":
            if not self.node or not getattr(self.node, 'parent', None):
                return 'BLACK'
            parent = self.node.parent
            if not getattr(parent, 'parent', None):
                return 'BLACK'
            grandparent = parent.parent
            
            if grandparent.left is parent:
                uncle = grandparent.right
            else:
                uncle = grandparent.left
            return getattr(uncle, 'colour', 'BLACK') if uncle else 'BLACK'
            
        raise ValueError(f"Unknown sensor keyword: {kw}")
