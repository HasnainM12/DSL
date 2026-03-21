"""
ASTPanel — displays the parsed Lark AST as indented text (PyQt6 version).
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPlainTextEdit, QFrame
from PyQt6.QtGui import QFont

from gui.constants import COLOURS


class ASTPanel(QWidget):
    """Read-only panel that renders a Lark parse tree as indented text."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel("AST Viewer")
        header.setStyleSheet(f"""
            color: {COLOURS["header_accent"]};
            font-size: 15px;
            font-weight: bold;
            font-family: Inter;
            padding: 8px 12px 4px 12px;
            background: {COLOURS["bg_dark"]};
        """)
        layout.addWidget(header)

        # Text area
        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setFont(QFont("Cascadia Code", 10))
        self._text.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {COLOURS["bg_dark"]};
                color: {COLOURS["fg_text"]};
                border: none;
            }}
        """)
        layout.addWidget(self._text)

    def update(self, lark_tree):   # noqa: A003
        """Render a Lark parse tree as indented text."""
        if lark_tree:
            self._text.setPlainText(lark_tree.pretty())
        else:
            self._text.setPlainText("")

    def clear(self):
        self._text.setPlainText("")
