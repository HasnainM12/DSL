"""
EditorPanel — code editor with line-number gutter for PyQt6.

Uses the canonical Qt line-number-area pattern:
  CodeEditor (QPlainTextEdit subclass)
  └── LineNumberArea (QWidget painted by CodeEditor)
"""

import re

from PyQt6.QtCore import QRect, QSize, Qt, QTimer
from PyQt6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QTextFormat,
)
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QPlainTextEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class DSLHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        # 1. Logic / structural keywords  ->  Terracotta, bold
        #    Includes NOT, which was previously missing.
        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor("#C53030"))
        kw_fmt.setFontWeight(QFont.Weight.Bold)
        for word in ["IF", "THEN", "AND", "OR", "NOT"]:
            self.highlighting_rules.append((re.compile(rf"\b{word}\b"), kw_fmt))

        # 2. Sensor keywords  ->  Steel Blue, italic
        #    All twelve sensors the grammar recognises.
        sensor_fmt = QTextCharFormat()
        sensor_fmt.setForeground(QColor("#2B6CB0"))
        sensor_fmt.setFontItalic(True)
        sensors = [
            # Longer names first (defensive — \b handles conflicts, but good practice)
            "left_child_balance",
            "right_child_balance",
            "parent_is_left_child",
            "sibling_left_colour",
            "sibling_right_colour",
            "node_colour",
            "parent_colour",
            "uncle_colour",
            "sibling_colour",
            "is_left_child",
            "balance_factor",
            "height",
        ]
        for word in sensors:
            self.highlighting_rules.append((re.compile(rf"\b{word}\b"), sensor_fmt))

        # 3. Action keywords  ->  Deep Charcoal, bold
        #    Ordered longest-first within each family so that e.g.
        #    ROTATE_LEFT_AT_GRANDPARENT is compiled before ROTATE_LEFT.
        #    The \b word-boundary guarantees no partial overlap regardless,
        #    but longest-first is clearer and avoids any edge-case surprises.
        action_fmt = QTextCharFormat()
        action_fmt.setForeground(QColor("#2D3748"))
        action_fmt.setFontWeight(QFont.Weight.Bold)
        actions = [
            "ROTATE_LEFT_AT_GRANDPARENT",
            "ROTATE_RIGHT_AT_GRANDPARENT",
            "ROTATE_LEFT_AT_PARENT",
            "ROTATE_RIGHT_AT_PARENT",
            "ROTATE_LEFT_AT_SIBLING",
            "ROTATE_RIGHT_AT_SIBLING",
            "ROTATE_LEFT_RIGHT",
            "ROTATE_RIGHT_LEFT",
            "ROTATE_LEFT",
            "ROTATE_RIGHT",
            "SET_SIBLING_COLOUR_FROM_PARENT",
            "SET_SIBLING_LEFT_COLOUR",
            "SET_SIBLING_RIGHT_COLOUR",
            "SET_SIBLING_COLOUR",
            "SET_GRANDPARENT_COLOUR",
            "SET_PARENT_COLOUR",
            "SET_UNCLE_COLOUR",
            "SET_COLOUR",
            "INSERT",
            "DELETE",
            "PROPAGATE",
            "DONE",
        ]
        for word in actions:
            self.highlighting_rules.append((re.compile(rf"\b{word}\b"), action_fmt))

        # 4. Comparison / arithmetic operators  ->  Warm Gold, bold
        #    Multi-character operators listed first so >=, <=, ==, !=
        #    are matched as a unit rather than as two separate characters.
        #    The old pattern also incorrectly included * which is not in the grammar.
        op_fmt = QTextCharFormat()
        op_fmt.setForeground(QColor("#B7791F"))
        op_fmt.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((re.compile(r">=|<=|==|!=|>|<|\+|-"), op_fmt))

        # 5. Integer literals  ->  Muted Brown
        #    Applied after operators so the digit part of -1 overrides
        #    the operator colour for the digit (the leading - stays gold).
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor("#6B4226"))
        self.highlighting_rules.append((re.compile(r"\b\d+\b"), num_fmt))

        # 6. Quoted strings  ->  Teal
        #    Matches the full "..." literal so colour names like "RED"
        #    are visually distinct from sensor keywords.
        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#2C7A7B"))
        self.highlighting_rules.append((re.compile(r'"[^"\n]*"'), str_fmt))

        # 7. Comments  ->  Muted Taupe  (must be last — overrides everything)
        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#A39E95"))
        self.highlighting_rules.append((re.compile(r"#[^\n]*"), comment_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


from gui.constants import COLOURS

# ──────────────────────────────────────────────────────────────────────────────
# Line-number sidebar
# ──────────────────────────────────────────────────────────────────────────────


class _LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.line_number_area_paint_event(event)


# ──────────────────────────────────────────────────────────────────────────────
# Editor widget
# ──────────────────────────────────────────────────────────────────────────────


class CodeEditor(QPlainTextEdit):
    """QPlainTextEdit with a synced line-number sidebar."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._line_number_area = _LineNumberArea(self)
        self._validate_timer: QTimer | None = None
        self._validate_callback = None

        # Signals
        self.blockCountChanged.connect(self._update_margin)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)

        self._update_margin(0)
        self._highlight_current_line()

        # Styling
        font = QFont("JetBrains Mono", 11)
        self.setFont(font)
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: transparent;
                color: {COLOURS["fg_text"]};
                border: none;
                selection-background-color: {COLOURS["focus_ring"]};
                selection-color: #ffffff;
            }}
        """)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.highlighter = DSLHighlighter(self.document())

    # ── public ──────────────────────────────────────────────────────────

    def line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance("9") * digits

    def set_validate_callback(self, cb):
        self._validate_callback = cb

    # ── line number painting ─────────────────────────────────────────────

    def line_number_area_paint_event(self, event):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor(COLOURS["bg_gutter"]))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + round(self.blockBoundingRect(block).height())
        font = QFont("JetBrains Mono", 11)
        painter.setFont(font)

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor(COLOURS["fg_gutter"]))
                painter.drawText(
                    0,
                    top,
                    self._line_number_area.width() - 4,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(block_number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    # ── Qt overrides ─────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        self._schedule_validation()

    # ── private ──────────────────────────────────────────────────────────

    def _update_margin(self, _=None):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self._update_margin()

    def _highlight_current_line(self):
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor(COLOURS["bg_card"]))
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])

    def _schedule_validation(self):
        if self._validate_timer:
            self._validate_timer.stop()
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(self._run_validation)
        timer.start(500)
        self._validate_timer = timer

    def _run_validation(self):
        self._validate_timer = None
        if self._validate_callback:
            self._validate_callback(self.toPlainText().strip())

    # ── error highlight ───────────────────────────────────────────────────

    def set_error(self, line: int, _col: int, _message: str):
        """Highlight the error line in red."""
        self._clear_error_selections()
        block = self.document().findBlockByLineNumber(line - 1)
        if not block.isValid():
            return
        selection = QTextEdit.ExtraSelection()
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#8B0000"))
        fmt.setForeground(QColor("#ffffff"))
        selection.format = fmt
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        cursor = QTextCursor(block)
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        selection.cursor = cursor
        # Keep current-line highlight + error
        cl = QTextEdit.ExtraSelection()
        cl.format.setBackground(QColor(COLOURS["bg_card"]))
        cl.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        cl.cursor = self.textCursor()
        cl.cursor.clearSelection()
        self.setExtraSelections([cl, selection])

    def clear_error(self):
        self._highlight_current_line()  # restores current-line only

    def set_active_line(self, line: int):
        """Highlight the active line in a pale yellow/tan colour."""
        self._clear_error_selections()
        block = self.document().findBlockByLineNumber(line - 1)
        if not block.isValid():
            return
        selection = QTextEdit.ExtraSelection()
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#EAE3D4"))
        selection.format = fmt
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        cursor = QTextCursor(block)
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        selection.cursor = cursor

        cl = QTextEdit.ExtraSelection()
        cl.format.setBackground(QColor(COLOURS["bg_card"]))
        cl.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        cl.cursor = self.textCursor()
        cl.cursor.clearSelection()
        self.setExtraSelections([cl, selection])

    def clear_active_line(self):
        self._highlight_current_line()

    def _clear_error_selections(self):
        self.setExtraSelections([])


# ──────────────────────────────────────────────────────────────────────────────
# Panel wrapper
# ──────────────────────────────────────────────────────────────────────────────

_PLACEHOLDER = """\
# AVL balancing rules (order matters)
IF balance_factor > 1 AND left_child_balance < 0 THEN ROTATE_LEFT_RIGHT
IF balance_factor < -1 AND right_child_balance > 0 THEN ROTATE_RIGHT_LEFT
IF balance_factor > 1 THEN ROTATE_RIGHT
IF balance_factor < -1 THEN ROTATE_LEFT
"""


class EditorPanel(QWidget):
    """Editor zone: header + CodeEditor with gutter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel("DSL Script Editor")
        header.setStyleSheet(f"""
            color: {COLOURS["header_accent"]};
            font-size: 14px;
            font-weight: bold;
            font-family: "Inter", sans-serif;
            padding: 10px 12px 4px 12px;
            background: transparent;
        """)
        layout.addWidget(header)

        # Accent underline
        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet(f"background: {COLOURS['header_accent']}; margin: 0 10px;")
        layout.addWidget(line)

        # Editor
        self.editor = CodeEditor()
        self.editor.setPlainText(_PLACEHOLDER)
        layout.addWidget(self.editor)

    # ── public API ────────────────────────────────────────────────────────

    def get_script(self) -> str:
        return self.editor.toPlainText().strip()

    def clear(self):
        self.editor.setPlainText("")

    def set_error(self, line: int, col: int, message: str):
        self.editor.set_error(line, col, message)

    def clear_error(self):
        self.editor.clear_error()

    def set_active_line(self, line: int):
        self.editor.set_active_line(line)

    def clear_active_line(self):
        self.editor.clear_active_line()

    def set_validate_callback(self, cb):
        self.editor.set_validate_callback(cb)
