"""
rdp_parser.py — Hand-written Recursive Descent Parser for the DSL grammar.

This module implements the same grammar as grammar.lark using a hand-written
lexer and recursive descent parser.  It is offered as a selectable alternative
backend to the Lark-based parser in interpreter.py.

Grammar (informal BNF):
    start       → (rule | action)+
    rule        → IF condition THEN action_block
    condition   → comparison ((AND | OR) comparison)*
                | NOT condition
                | ( condition )
    comparison  → expression COMPARATOR expression
    expression  → term ((+ | -) term)*
    term        → NUMBER | KEYWORD | STRING | ( expression )
    action_block→ { action+ } | action
    action      → ROTATE_LEFT | ROTATE_RIGHT | ROTATE_LEFT_RIGHT
                | ROTATE_RIGHT_LEFT | SET_COLOUR STRING
                | INSERT NUMBER | DELETE NUMBER

Architecture:
    Lexer     — tokenises the DSL string into a flat list of Token objects
    Parser    — recursive descent producing an AST of dataclass nodes
    AST Nodes — simple Python dataclasses mirroring the Lark tree structure
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Union


# =====================================================================
# AST Node Definitions
# =====================================================================

@dataclass
class NumberNode:
    value: float

@dataclass
class KeywordNode:
    """Sensor keyword like balance_factor, height, node_colour, etc."""
    name: str

@dataclass
class StringNode:
    value: str

@dataclass
class BinOpNode:
    """Arithmetic binary operation: + or -."""
    op: str
    left: object
    right: object

@dataclass
class ComparisonNode:
    op: str
    left: object
    right: object

@dataclass
class AndNode:
    left: object
    right: object

@dataclass
class OrNode:
    left: object
    right: object

@dataclass
class NotNode:
    operand: object

@dataclass
class ActionNode:
    """A single action like ROTATE_LEFT, SET_COLOUR "RED", INSERT 10."""
    action_type: str
    argument: Optional[object] = None

@dataclass
class RuleNode:
    condition: object
    actions: List[ActionNode]

@dataclass
class ProgramNode:
    items: List[Union[RuleNode, ActionNode]]


# =====================================================================
# Lexer
# =====================================================================

# Token types
class TokenType:
    # Literals
    NUMBER   = "NUMBER"
    STRING   = "STRING"
    # Comparators
    COMP     = "COMP"
    # Arithmetic
    PLUS     = "PLUS"
    MINUS    = "MINUS"
    # Punctuation
    LPAREN   = "LPAREN"
    RPAREN   = "RPAREN"
    LBRACE   = "LBRACE"
    RBRACE   = "RBRACE"
    # Keywords
    IF       = "IF"
    THEN     = "THEN"
    AND      = "AND"
    OR       = "OR"
    NOT      = "NOT"
    # Action keywords
    ROTATE_LEFT       = "ROTATE_LEFT"
    ROTATE_RIGHT      = "ROTATE_RIGHT"
    ROTATE_LEFT_RIGHT = "ROTATE_LEFT_RIGHT"
    ROTATE_RIGHT_LEFT = "ROTATE_RIGHT_LEFT"
    SET_COLOUR        = "SET_COLOUR"
    INSERT            = "INSERT"
    DELETE             = "DELETE"
    # Sensor keywords
    KEYWORD  = "KEYWORD"
    # End
    EOF      = "EOF"


@dataclass
class Token:
    type: str
    value: str
    pos: int = 0


# Sensor keywords recognised by the grammar
_SENSOR_KEYWORDS = {
    "balance_factor", "height", "left_child_balance",
    "right_child_balance", "node_colour", "parent_colour", "uncle_colour",
}

# Action keywords (order matters — longer matches first)
_ACTION_KEYWORDS = [
    ("ROTATE_LEFT_RIGHT", TokenType.ROTATE_LEFT_RIGHT),
    ("ROTATE_RIGHT_LEFT", TokenType.ROTATE_RIGHT_LEFT),
    ("ROTATE_LEFT",       TokenType.ROTATE_LEFT),
    ("ROTATE_RIGHT",      TokenType.ROTATE_RIGHT),
    ("SET_COLOUR",        TokenType.SET_COLOUR),
    ("INSERT",            TokenType.INSERT),
    ("DELETE",            TokenType.DELETE),
]

_LOGIC_KEYWORDS = {
    "IF":   TokenType.IF,
    "THEN": TokenType.THEN,
    "AND":  TokenType.AND,
    "OR":   TokenType.OR,
    "NOT":  TokenType.NOT,
}


class LexerError(Exception):
    """Raised when the lexer encounters an unrecognised character."""
    pass


class ParseError(Exception):
    """Raised when the parser encounters unexpected tokens."""
    pass


def tokenize(source: str) -> List[Token]:
    """Convert a DSL source string into a flat list of Tokens."""
    tokens: List[Token] = []
    i = 0
    length = len(source)

    while i < length:
        # Skip whitespace
        if source[i].isspace():
            i += 1
            continue

        # Skip comments (# to end of line)
        if source[i] == '#':
            while i < length and source[i] != '\n':
                i += 1
            continue

        # Strings
        if source[i] == '"':
            j = i + 1
            while j < length and source[j] != '"':
                if source[j] == '\\':
                    j += 1  # skip escaped char
                j += 1
            if j >= length:
                raise LexerError(f"Unterminated string at position {i}")
            tokens.append(Token(TokenType.STRING, source[i+1:j], i))
            i = j + 1
            continue

        # Two-character comparators
        if i + 1 < length and source[i:i+2] in (">=", "<=", "==", "!="):
            tokens.append(Token(TokenType.COMP, source[i:i+2], i))
            i += 2
            continue

        # Single-character comparators
        if source[i] in (">", "<"):
            tokens.append(Token(TokenType.COMP, source[i], i))
            i += 1
            continue

        # Arithmetic / punctuation
        if source[i] == '+':
            tokens.append(Token(TokenType.PLUS, "+", i))
            i += 1
            continue
        if source[i] == '-':
            # Disambiguate: minus sign vs negative number
            # If previous token is a NUMBER, KEYWORD, RPAREN → it's subtraction
            # Otherwise → it's a negative number prefix
            if tokens and tokens[-1].type in (TokenType.NUMBER, TokenType.KEYWORD):
                tokens.append(Token(TokenType.MINUS, "-", i))
                i += 1
                continue
            # Otherwise fall through to number parsing
        if source[i] == '(':
            tokens.append(Token(TokenType.LPAREN, "(", i))
            i += 1
            continue
        if source[i] == ')':
            tokens.append(Token(TokenType.RPAREN, ")", i))
            i += 1
            continue
        if source[i] == '{':
            tokens.append(Token(TokenType.LBRACE, "{", i))
            i += 1
            continue
        if source[i] == '}':
            tokens.append(Token(TokenType.RBRACE, "}", i))
            i += 1
            continue

        # Numbers (including negative)
        if source[i].isdigit() or (source[i] == '-' and i + 1 < length and source[i+1].isdigit()):
            j = i
            if source[j] == '-':
                j += 1
            while j < length and (source[j].isdigit() or source[j] == '.'):
                j += 1
            tokens.append(Token(TokenType.NUMBER, source[i:j], i))
            i = j
            continue

        # Identifiers and keywords
        if source[i].isalpha() or source[i] == '_':
            j = i
            while j < length and (source[j].isalnum() or source[j] == '_'):
                j += 1
            word = source[i:j]

            # Check action keywords (longest match first)
            matched = False
            for action_str, token_type in _ACTION_KEYWORDS:
                if source[i:].startswith(action_str) and (
                    i + len(action_str) >= length or
                    not (source[i + len(action_str)].isalnum() or source[i + len(action_str)] == '_')
                ):
                    tokens.append(Token(token_type, action_str, i))
                    i += len(action_str)
                    matched = True
                    break
            if matched:
                continue

            # Check logic keywords
            if word in _LOGIC_KEYWORDS:
                tokens.append(Token(_LOGIC_KEYWORDS[word], word, i))
                i = j
                continue

            # Check sensor keywords
            if word in _SENSOR_KEYWORDS:
                tokens.append(Token(TokenType.KEYWORD, word, i))
                i = j
                continue

            raise LexerError(f"Unknown identifier '{word}' at position {i}")

        raise LexerError(f"Unexpected character '{source[i]}' at position {i}")

    tokens.append(Token(TokenType.EOF, "", length))
    return tokens


# =====================================================================
# Recursive Descent Parser
# =====================================================================

class RDPParser:
    """
    Hand-written recursive descent parser for the DSL grammar.

    Usage:
        parser = RDPParser()
        ast = parser.parse("IF balance_factor > 1 THEN ROTATE_RIGHT")
        print(ast)
    """

    def __init__(self):
        self._tokens: List[Token] = []
        self._pos = 0

    def parse(self, source: str) -> ProgramNode:
        """Parse a DSL source string and return a ProgramNode AST."""
        self._tokens = tokenize(source)
        self._pos = 0
        result = self._parse_start()
        if self._current().type != TokenType.EOF:
            raise ParseError(
                f"Unexpected token '{self._current().value}' at position {self._current().pos}"
            )
        return result

    # --- helpers ---

    def _current(self) -> Token:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return Token(TokenType.EOF, "", -1)

    def _peek(self) -> Token:
        return self._current()

    def _advance(self) -> Token:
        tok = self._current()
        self._pos += 1
        return tok

    def _expect(self, token_type: str) -> Token:
        tok = self._current()
        if tok.type != token_type:
            raise ParseError(
                f"Expected {token_type}, got {tok.type} ('{tok.value}') at position {tok.pos}"
            )
        return self._advance()

    def _match(self, token_type: str) -> Optional[Token]:
        if self._current().type == token_type:
            return self._advance()
        return None

    # --- grammar rules ---

    def _parse_start(self) -> ProgramNode:
        """start → (rule | action)+"""
        items = []
        while self._current().type != TokenType.EOF:
            if self._current().type == TokenType.IF:
                items.append(self._parse_rule())
            else:
                items.append(self._parse_action())
        if not items:
            raise ParseError("Empty script — expected at least one rule or action")
        return ProgramNode(items=items)

    def _parse_rule(self) -> RuleNode:
        """rule → IF condition THEN action_block"""
        self._expect(TokenType.IF)
        condition = self._parse_condition()
        self._expect(TokenType.THEN)
        actions = self._parse_action_block()
        return RuleNode(condition=condition, actions=actions)

    def _parse_condition(self) -> object:
        """condition → NOT condition | atom ((AND | OR) atom)*"""
        if self._match(TokenType.NOT):
            return NotNode(operand=self._parse_condition())

        left = self._parse_condition_atom()

        while self._current().type in (TokenType.AND, TokenType.OR):
            op = self._advance()
            right = self._parse_condition_atom()
            if op.type == TokenType.AND:
                left = AndNode(left=left, right=right)
            else:
                left = OrNode(left=left, right=right)

        return left

    def _parse_condition_atom(self) -> object:
        """condition_atom → ( condition ) | comparison"""
        if self._match(TokenType.LPAREN):
            cond = self._parse_condition()
            self._expect(TokenType.RPAREN)
            return cond
        if self._current().type == TokenType.NOT:
            return self._parse_condition()
        return self._parse_comparison()

    def _parse_comparison(self) -> ComparisonNode:
        """comparison → expression COMPARATOR expression"""
        left = self._parse_expression()
        op_tok = self._expect(TokenType.COMP)
        right = self._parse_expression()
        return ComparisonNode(op=op_tok.value, left=left, right=right)

    def _parse_expression(self) -> object:
        """expression → term ((+ | -) term)*"""
        node = self._parse_term()
        while self._current().type in (TokenType.PLUS, TokenType.MINUS):
            op_tok = self._advance()
            right = self._parse_term()
            node = BinOpNode(op=op_tok.value, left=node, right=right)
        return node

    def _parse_term(self) -> object:
        """term → NUMBER | KEYWORD | STRING | ( expression )"""
        tok = self._current()

        if tok.type == TokenType.NUMBER:
            self._advance()
            return NumberNode(value=float(tok.value))

        if tok.type == TokenType.KEYWORD:
            self._advance()
            return KeywordNode(name=tok.value)

        if tok.type == TokenType.STRING:
            self._advance()
            return StringNode(value=tok.value)

        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN)
            return expr

        raise ParseError(
            f"Expected number, keyword, string, or '(' but got {tok.type} ('{tok.value}') "
            f"at position {tok.pos}"
        )

    def _parse_action_block(self) -> List[ActionNode]:
        """action_block → { action+ } | action"""
        if self._match(TokenType.LBRACE):
            actions = []
            while self._current().type != TokenType.RBRACE:
                actions.append(self._parse_action())
            self._expect(TokenType.RBRACE)
            return actions
        return [self._parse_action()]

    def _parse_action(self) -> ActionNode:
        """action → rotation | SET_COLOUR STRING | INSERT NUMBER | DELETE NUMBER"""
        tok = self._current()

        if tok.type == TokenType.ROTATE_LEFT:
            self._advance()
            return ActionNode(action_type="ROTATE_LEFT")
        if tok.type == TokenType.ROTATE_RIGHT:
            self._advance()
            return ActionNode(action_type="ROTATE_RIGHT")
        if tok.type == TokenType.ROTATE_LEFT_RIGHT:
            self._advance()
            return ActionNode(action_type="ROTATE_LEFT_RIGHT")
        if tok.type == TokenType.ROTATE_RIGHT_LEFT:
            self._advance()
            return ActionNode(action_type="ROTATE_RIGHT_LEFT")

        if tok.type == TokenType.SET_COLOUR:
            self._advance()
            str_tok = self._expect(TokenType.STRING)
            return ActionNode(action_type="SET_COLOUR", argument=str_tok.value)

        if tok.type == TokenType.INSERT:
            self._advance()
            num_tok = self._expect(TokenType.NUMBER)
            return ActionNode(action_type="INSERT", argument=float(num_tok.value))

        if tok.type == TokenType.DELETE:
            self._advance()
            num_tok = self._expect(TokenType.NUMBER)
            return ActionNode(action_type="DELETE", argument=float(num_tok.value))

        raise ParseError(
            f"Expected action keyword but got {tok.type} ('{tok.value}') "
            f"at position {tok.pos}"
        )


# =====================================================================
# Convenience: pretty-print AST
# =====================================================================

def pretty_print(node, indent=0) -> str:
    """Return a human-readable indented string representation of the AST."""
    pad = "  " * indent
    lines = []

    if isinstance(node, ProgramNode):
        lines.append(f"{pad}Program")
        for item in node.items:
            lines.append(pretty_print(item, indent + 1))

    elif isinstance(node, RuleNode):
        lines.append(f"{pad}Rule")
        lines.append(f"{pad}  condition:")
        lines.append(pretty_print(node.condition, indent + 2))
        lines.append(f"{pad}  actions:")
        for a in node.actions:
            lines.append(pretty_print(a, indent + 2))

    elif isinstance(node, ComparisonNode):
        lines.append(f"{pad}Comparison ({node.op})")
        lines.append(pretty_print(node.left, indent + 1))
        lines.append(pretty_print(node.right, indent + 1))

    elif isinstance(node, AndNode):
        lines.append(f"{pad}AND")
        lines.append(pretty_print(node.left, indent + 1))
        lines.append(pretty_print(node.right, indent + 1))

    elif isinstance(node, OrNode):
        lines.append(f"{pad}OR")
        lines.append(pretty_print(node.left, indent + 1))
        lines.append(pretty_print(node.right, indent + 1))

    elif isinstance(node, NotNode):
        lines.append(f"{pad}NOT")
        lines.append(pretty_print(node.operand, indent + 1))

    elif isinstance(node, BinOpNode):
        lines.append(f"{pad}BinOp ({node.op})")
        lines.append(pretty_print(node.left, indent + 1))
        lines.append(pretty_print(node.right, indent + 1))

    elif isinstance(node, NumberNode):
        lines.append(f"{pad}Number({node.value})")

    elif isinstance(node, KeywordNode):
        lines.append(f"{pad}Keyword({node.name})")

    elif isinstance(node, StringNode):
        lines.append(f"{pad}String(\"{node.value}\")")

    elif isinstance(node, ActionNode):
        arg = f" {node.argument}" if node.argument is not None else ""
        lines.append(f"{pad}Action({node.action_type}{arg})")

    else:
        lines.append(f"{pad}{node!r}")

    return "\n".join(lines)
