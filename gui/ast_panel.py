"""
ASTPanel — displays the parsed Lark AST as an interactive tree (PyQt6 version).
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from lark import Tree, Token

from gui.constants import COLOURS


class ASTPanel(QWidget):
    """Read-only panel that renders a Lark parse tree as an interactive tree."""

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
            font-size: 14px;
            font-weight: bold;
            font-family: "Inter", sans-serif;
            padding: 8px 12px 4px 12px;
            background: transparent;
        """)
        layout.addWidget(header)

        # Tree area
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setFont(QFont("Cascadia Code", 11))
        # Keep styling consistent
        self._tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {COLOURS["bg_dark"]};
                color: {COLOURS["fg_text"]};
                border: none;
            }}
            QTreeWidget::item:hover {{
                background-color: {COLOURS["bg_card"]};
            }}
            QTreeWidget::item:selected {{
                background-color: {COLOURS["bg_card"]};
            }}
        """)
        layout.addWidget(self._tree)
        
        # Placeholder
        self._placeholder = QLabel("Tree structure will appear here...")
        self._placeholder.setStyleSheet(f"""
            color: #A39E95;
            font-family: "Inter", sans-serif;
            font-size: 13px;
            font-style: italic;
            padding: 12px;
        """)
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self._placeholder)
        
        self._tree.hide()

    def update(self, lark_tree):   # noqa: A003
        """Render a Lark parse tree into the QTreeWidget."""
        self.clear()
        if lark_tree:
            self._placeholder.hide()
            self._tree.show()
            self._build_tree(lark_tree, self._tree)
            
            # Optionally expand just the top-level root node so the user sees more than just "start"
            top_item = self._tree.topLevelItem(0)
            if top_item:
                top_item.setExpanded(True)
        else:
            self._tree.hide()
            self._placeholder.show()

    def clear(self):
        self._tree.clear()
        self._tree.hide()
        self._placeholder.show()

    def _build_tree(self, node, parent):
        if isinstance(node, Tree):
            # Rule name
            item = QTreeWidgetItem(parent)
            item.setText(0, str(node.data))
            item.setForeground(0, QColor(COLOURS.get("header_accent", "#58a6ff")))
            
            for child in node.children:
                self._build_tree(child, item)
            
            # Explicitly keep nodes collapsed by default (QTreeWidget default is collapsed anyway)
            item.setExpanded(False)

        elif isinstance(node, Token):
            # Token value
            item = QTreeWidgetItem(parent)
            item.setText(0, f"{node.type}: {node.value}")
            item.setForeground(0, QColor(COLOURS.get("fg_text", "#e6edf3")))
