"""
CanvasRenderer — tree drawing and animation engine for PyQt6.

Replaces the tkinter Canvas with a custom QWidget that overrides paintEvent.
Animation uses QTimer.singleShot instead of root.after().
"""

from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont

from gui.constants import (
    COLOURS, NODE_RADIUS, Y_START, Y_SPACING,
    HIGHLIGHT_DURATION_MS, ANIM_FRAMES, ANIM_DELAY_MS,
)

_GRID_SPACING = 28
_GRID_DOT_R   = 1


class CanvasRenderer(QWidget):
    """Handles BST visualisation: layout calculation, drawing, and animation."""

    def __init__(self, on_resize=None, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(300)

        self._on_resize_callback = on_resize

        # State used by paintEvent
        self._draw_positions: dict = {}   # {TreeNode: (x, y)}
        self._highlight_val = None
        self._stats_text = ""

    # ------------------------------------------------------------------ #
    # Qt overrides                                                         #
    # ------------------------------------------------------------------ #

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._on_resize_callback:
            self._on_resize_callback()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(COLOURS["bg_medium"]))

        # Dot grid
        self._paint_dot_grid(painter)

        # Tree
        self._paint_tree(painter, self._draw_positions, self._highlight_val)

        # Stats overlay (top-right)
        if self._stats_text:
            painter.setPen(QColor(COLOURS["fg_text"]))
            painter.setFont(QFont("Inter", 11))
            painter.drawText(
                self.rect().adjusted(0, 10, -10, 0),
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
                self._stats_text,
            )

    # ------------------------------------------------------------------ #
    # Drawing helpers                                                       #
    # ------------------------------------------------------------------ #

    def _paint_dot_grid(self, painter: QPainter):
        color = QColor(COLOURS["grid_dot"])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        w, h = self.width(), self.height()
        s, r = _GRID_SPACING, _GRID_DOT_R
        for x in range(0, w, s):
            for y in range(0, h, s):
                painter.drawEllipse(QPointF(x, y), r, r)

    def _paint_tree(self, painter: QPainter, positions: dict, highlight_val=None):
        if not positions:
            return

        r = NODE_RADIUS

        # Pass 1 — edges
        pen = QPen(QColor(COLOURS["edge_colour"]), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for node, (px, py) in positions.items():
            if node.left and node.left in positions:
                cx, cy = positions[node.left]
                painter.drawLine(int(px), int(py), int(cx), int(cy))
            if node.right and node.right in positions:
                cx, cy = positions[node.right]
                painter.drawLine(int(px), int(py), int(cx), int(cy))

        # Pass 2 — node circles
        for node, (nx, ny) in positions.items():
            highlighted = highlight_val is not None and node.val == highlight_val
            if highlighted:
                fill    = QColor(COLOURS["node_delete_highlight"])
                outline = fill
            elif getattr(node, "colour", None) == "RED":
                fill    = QColor(COLOURS["node_red_fill"])
                outline = QColor(COLOURS["node_red_outline"])
            else:
                fill    = QColor(COLOURS["node_fill"])
                outline = QColor(COLOURS["node_outline"])

            painter.setPen(QPen(outline, 3))
            painter.setBrush(QBrush(fill))
            painter.drawEllipse(QPointF(nx, ny), r, r)

        # Pass 3 — labels
        font = QFont("Inter", 12, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(COLOURS["node_text"]))
        fm = painter.fontMetrics()
        for node, (nx, ny) in positions.items():
            label = str(node.val)
            tw = fm.horizontalAdvance(label)
            th = fm.height()
            painter.drawText(int(nx - tw / 2), int(ny + th / 4), label)

    # ------------------------------------------------------------------ #
    # Layout                                                               #
    # ------------------------------------------------------------------ #

    def calculate_positions(self, node, depth, left, right, positions):
        if node is None:
            return
        x = (left + right) / 2
        y = Y_START + depth * Y_SPACING
        positions[node] = (x, y)
        self.calculate_positions(node.left,  depth + 1, left, x, positions)
        self.calculate_positions(node.right, depth + 1, x, right, positions)

    def capture_target_positions(self, bst_root) -> dict:
        targets = {}
        self.calculate_positions(bst_root, 0, 0, self.width(), targets)
        return targets

    # ------------------------------------------------------------------ #
    # Public drawing API                                                   #
    # ------------------------------------------------------------------ #

    def draw_tree(self, bst_root, current_positions, _event=None):
        """Recompute positions from scratch and repaint."""
        if bst_root is None:
            self._draw_positions = {}
            self._highlight_val  = None
            current_positions.clear()
            self.update()
            return

        positions = self.capture_target_positions(bst_root)
        self._draw_positions = positions
        self._highlight_val  = None
        current_positions.clear()
        current_positions.update(positions)
        self.update()

    def draw_stats(self, bst_root):
        if not bst_root:
            self._stats_text = ""
        else:
            lh = bst_root.left.height  if bst_root.left  else 0
            rh = bst_root.right.height if bst_root.right else 0
            bf    = lh - rh
            count = self._tree_count(bst_root)
            self._stats_text = (
                f"Nodes: {count}   Height: {bst_root.height}   Root BF: {bf}"
            )
        self.update()

    def highlight_node(self, node_val, positions, callback):
        """Flash a node, then invoke *callback* after the highlight fades."""
        self._draw_positions = dict(positions)
        self._highlight_val  = node_val
        self.update()
        QTimer.singleShot(HIGHLIGHT_DURATION_MS, callback)

    # ------------------------------------------------------------------ #
    # Animation                                                            #
    # ------------------------------------------------------------------ #

    def animate_frame(
        self, start, targets, frame, total_frames,
        anim_delay, current_positions, animation_queue,
        on_step_forward, animating_setter,
    ):
        """Interpolate one frame and schedule the next via QTimer."""
        # Smoothstep ease
        t = frame / total_frames
        t = t * t * (3.0 - 2.0 * t)

        interpolated = {}
        for node, (tx, ty) in targets.items():
            if node in start:
                sx, sy = start[node]
            else:
                sx, sy = self._find_parent_start(node, start, targets)
            interpolated[node] = (sx + (tx - sx) * t, sy + (ty - sy) * t)

        self._draw_positions = interpolated
        self._highlight_val  = None
        self.update()

        if frame < total_frames:
            QTimer.singleShot(
                anim_delay,
                lambda: self.animate_frame(
                    start, targets, frame + 1, total_frames,
                    anim_delay, current_positions, animation_queue,
                    on_step_forward, animating_setter,
                ),
            )
        else:
            current_positions.clear()
            current_positions.update(targets)
            animating_setter(False)
            if animation_queue:
                QTimer.singleShot(10, on_step_forward)

    def _find_parent_start(self, child, start, targets):
        for node in targets:
            if node.left is child or node.right is child:
                return start.get(node, targets[node])
        return (self.width() / 2, Y_START)

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _tree_count(self, node):
        if not node:
            return 0
        return 1 + self._tree_count(node.left) + self._tree_count(node.right)
