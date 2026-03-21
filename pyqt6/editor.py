"""
EditorPanel — code editor with line-number gutter for PyQt6.

Uses the canonical Qt line-number-area pattern:
  CodeEditor (QPlainTextEdit subclass)
  └── LineNumberArea (QWidget painted by CodeEditor)
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPlainTextEdit, QFrame
from PyQt6.QtCore import Qt, QRect, QSize, QTimer
from PyQt6.QtGui import (
    QColor, QPainter, QFont, QTextFormat,
    QTextCharFormat, QTextCursor,
)

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
        font = QFont("Cascadia Code", 11)
        self.setFont(font)
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {COLOURS["bg_dark"]};
                color: {COLOURS["fg_text"]};
                border: none;
                selection-background-color: {COLOURS["focus_ring"]};
                selection-color: #ffffff;
            }}
        """)
        self.setTabStopDistance(
            self.fontMetrics().horizontalAdvance(" ") * 4
        )

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

        block        = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top    = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        font   = QFont("Cascadia Code", 11)
        painter.setFont(font)

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor(COLOURS["fg_gutter"]))
                painter.drawText(
                    0, top,
                    self._line_number_area.width() - 4,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(block_number + 1),
                )
            block        = block.next()
            top          = bottom
            bottom       = top + round(self.blockBoundingRect(block).height())
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
        selection = QPlainTextEdit.ExtraSelection()
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
        selection = QPlainTextEdit.ExtraSelection()
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#8B0000"))
        fmt.setForeground(QColor("#ffffff"))
        selection.format = fmt
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        cursor = QTextCursor(block)
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        selection.cursor = cursor
        # Keep current-line highlight + error
        cl = QPlainTextEdit.ExtraSelection()
        cl.format.setBackground(QColor(COLOURS["bg_card"]))
        cl.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        cl.cursor = self.textCursor()
        cl.cursor.clearSelection()
        self.setExtraSelections([cl, selection])

    def clear_error(self):
        self._highlight_current_line()  # restores current-line only

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
            font-size: 15px;
            font-weight: bold;
            font-family: Inter;
            padding: 10px 12px 4px 12px;
            background: {COLOURS["bg_dark"]};
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

    def set_validate_callback(self, cb):
        self.editor.set_validate_callback(cb)
