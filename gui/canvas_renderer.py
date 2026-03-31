"""
CanvasRenderer — tree drawing and animation engine for PyQt6.

Replaces the tkinter Canvas with a custom QWidget that overrides paintEvent.
Animation uses QTimer.singleShot instead of root.after().
"""

from PyQt6.QtWidgets import QWidget, QSizePolicy, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath, QLinearGradient

from gui.constants import (
    COLOURS, NODE_RADIUS, Y_START, Y_SPACING,
    HIGHLIGHT_DURATION_MS, ANIM_FRAMES, ANIM_DELAY_MS,
    MODE_AVL, MODE_RB
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
        self.mode = MODE_AVL

        
        self.hud_layout = QHBoxLayout(self)
        self.hud_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.hud_layout.setContentsMargins(0, 15, 0, 0)
        self.hud_layout.setSpacing(10)
        
        self.nodes_lbl = self._make_pill()
        self.height_lbl = self._make_pill()
        self.root_bf_lbl = self._make_pill()
        
        self.hud_layout.addWidget(self.nodes_lbl)
        self.hud_layout.addWidget(self.height_lbl)
        self.hud_layout.addWidget(self.root_bf_lbl)
        
        self.nodes_lbl.hide()
        self.height_lbl.hide()
        self.root_bf_lbl.hide()

    def _make_pill(self):
        lbl = QLabel()
        self._update_pill_style(lbl, COLOURS["avl_hud_bg"], COLOURS["avl_hud_fg"])
        return lbl

    def _update_pill_style(self, lbl, bg_color, fg_color):
        lbl.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {fg_color};
                font-family: "Inter", sans-serif;
                font-weight: bold;
                font-size: 10pt;
                padding: 5px 12px;
                border-radius: 14px;
            }}
        """)

    def set_mode(self, mode):
        self.mode = mode
        if mode == MODE_AVL:
            bg = COLOURS["avl_hud_bg"]
            fg = COLOURS["avl_hud_fg"]
        else:
            bg = COLOURS["node_red_fill"]  # Terracotta (now Darker Terracotta)
            fg = "#FFFFFF"

        self._update_pill_style(self.nodes_lbl, bg, fg)
        self._update_pill_style(self.height_lbl, bg, fg)
        self._update_pill_style(self.root_bf_lbl, bg, fg)

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
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for node, (px, py) in positions.items():
            if node.left and node.left in positions:
                cx, cy = positions[node.left]
                path = QPainterPath()
                path.moveTo(px, py)
                path.cubicTo(px, (py + cy) / 2, cx, (py + cy) / 2, cx, cy)
                painter.drawPath(path)
            if node.right and node.right in positions:
                cx, cy = positions[node.right]
                path = QPainterPath()
                path.moveTo(px, py)
                path.cubicTo(px, (py + cy) / 2, cx, (py + cy) / 2, cx, cy)
                painter.drawPath(path)

        # Pass 2 — node circles
        for node, (nx, ny) in positions.items():
            highlighted = highlight_val is not None and node.val == highlight_val
            if highlighted:
                if self.mode == MODE_AVL:
                    base_color = QColor(COLOURS["avl_highlight"])
                else:
                    base_color = QColor(COLOURS["node_delete_highlight"])
            elif self.mode == MODE_AVL:
                base_color = QColor(COLOURS["node_avl_fill"])
            elif getattr(node, "colour", None) == "RED":
                base_color = QColor(COLOURS["node_red_fill"])
            else:
                base_color = QColor(COLOURS["node_fill"])

            # Drop Shadow (offset + 4)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(82, 64, 50, 45))  # Warm Umber shadow
            painter.drawEllipse(QPointF(nx, ny + 4), r, r)

            # Gradient setup
            darker_color = base_color.darker(120)
            gradient = QLinearGradient(nx, ny - r, nx, ny + r)
            gradient.setColorAt(0.0, base_color)
            gradient.setColorAt(1.0, darker_color)

            painter.setBrush(QBrush(gradient))
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
            self.nodes_lbl.hide()
            self.height_lbl.hide()
            self.root_bf_lbl.hide()
        else:
            count = self._tree_count(bst_root)
            self.nodes_lbl.setText(f"Nodes: {count}")
            self.height_lbl.setText(f"Height: {bst_root.height}")

            if self.mode == MODE_AVL:
                m_bf = self._max_bf(bst_root)
                self.root_bf_lbl.setText(f"Max BF: {m_bf}")
            else:
                bh = self._black_height(bst_root)
                self.root_bf_lbl.setText(f"Black Height: {bh}")

            self.nodes_lbl.show()
            self.height_lbl.show()
            self.root_bf_lbl.show()
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
        # Slight bounce (easeOutBack)
        t = frame / total_frames
        t -= 1.0
        t = 1.0 + 2.70158 * (t * t * t) + 1.70158 * (t * t)

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

    def _max_bf(self, node):
        if not node:
            return 0
        lh = node.left.height if node.left else 0
        rh = node.right.height if node.right else 0
        bf = lh - rh
        return max(abs(bf), self._max_bf(node.left), self._max_bf(node.right))

    def _black_height(self, node):
        # Follow left spine (for a valid RB tree all paths are equal)
        bh = 0
        curr = node
        while curr is not None:
            if getattr(curr, "colour", None) in (None, "BLACK"):
                bh += 1
            curr = curr.left
        # leaf nodes are implicitly black
        return bh + 1
