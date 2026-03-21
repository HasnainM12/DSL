"""
CanvasRenderer — tree drawing and animation engine.
Uses tk.Canvas directly (CustomTkinter has no canvas equivalent).
"""

import tkinter as tk

from gui.constants import (COLOURS, NODE_RADIUS, Y_START, Y_SPACING, FONT_NODE,
                           FONT_BODY, HIGHLIGHT_DURATION_MS)



class CanvasRenderer:
    """Handles BST visualisation: layout calculation, drawing, and animation."""

    # Dot-grid settings
    _GRID_SPACING = 28
    _GRID_DOT_SIZE = 1

    def __init__(self, parent, root_window):
        """
        Build the canvas zone and add it to *parent* (a PanedWindow).

        Parameters
        ----------
        parent : tk.PanedWindow
            The horizontal pane that holds this canvas.
        root_window : ctk.CTk
            The root window, used for ``after()`` scheduling.
        """
        self._root = root_window

        self.canvas_frame = tk.Frame(parent, bg=COLOURS["bg_medium"])
        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg=COLOURS["bg_medium"], highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Track canvas size so grid ovals are only redrawn on resize
        self._grid_size = (0, 0)

    # ---- background grid ----

    def _draw_dot_grid(self):
        """Draw a subtle dot-grid pattern across the canvas background.

        Grid ovals are tagged ``"grid"`` and only recreated when the
        canvas size changes, so they persist across animation frames.
        """
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 2 or h < 2:
            return

        # Skip if the grid is already drawn at this size
        if (w, h) == self._grid_size:
            return

        self._grid_size = (w, h)
        self.canvas.delete("grid")

        dot_colour = COLOURS["grid_dot"]
        s = self._GRID_SPACING
        r = self._GRID_DOT_SIZE

        for x in range(0, w, s):
            for y in range(0, h, s):
                self.canvas.create_oval(
                    x - r, y - r, x + r, y + r,
                    fill=dot_colour, outline="",
                    tags="grid",
                )

    # ---- coordinate calculation ----

    def calculate_positions(self, node, depth, left, right, positions):
        """
        Recursively assign (x, y) coordinates to every node.

        *left* and *right* define the horizontal slot for this node.
        The node is placed at the midpoint; children get the left and
        right halves respectively, producing a centred layout.
        """
        if node is None:
            return

        x = (left + right) / 2
        y = Y_START + depth * Y_SPACING
        positions[node] = (x, y)

        self.calculate_positions(node.left,  depth + 1, left,  x, positions)
        self.calculate_positions(node.right, depth + 1, x, right, positions)

    def capture_target_positions(self, bst_root):
        """Return {TreeNode: (x, y)} based on current BST structure."""
        canvas_w = self.canvas.winfo_width()
        targets = {}
        self.calculate_positions(bst_root, 0, 0, canvas_w, targets)
        return targets

    # ---- drawing ----

    def draw_at_positions(self, positions, highlight_val=None):
        """
        Clear the canvas and draw the tree at the given positions.

        Drawing order: grid → edges → shadows → circles → labels.
        If *highlight_val* is set, that node is drawn with a red fill.
        """
        self.canvas.delete("tree")

        # Background dot-grid
        self._draw_dot_grid()

        if not positions:
            return

        r = NODE_RADIUS
        edge_colour   = COLOURS["edge_colour"]
        canvas_bg     = COLOURS["bg_medium"]
        node_outline  = COLOURS["node_outline"]
        text_colour   = COLOURS["node_text"]
        hl_fill       = COLOURS["node_delete_highlight"]

        # Pass 1: edges
        for node, (px, py) in positions.items():
            if node.left and node.left in positions:
                cx, cy = positions[node.left]
                self.canvas.create_line(
                    px, py, cx, cy,
                    fill=edge_colour, width=2, smooth=True,
                    tags="tree",
                )
            if node.right and node.right in positions:
                cx, cy = positions[node.right]
                self.canvas.create_line(
                    px, py, cx, cy,
                    fill=edge_colour, width=2, smooth=True,
                    tags="tree",
                )

        # Pass 2: node circles
        for node, (nx, ny) in positions.items():
            is_highlighted = (highlight_val is not None and node.val == highlight_val)
            if is_highlighted:
                fill = hl_fill
                outline = hl_fill
            elif getattr(node, 'colour', None) == "RED":
                fill = COLOURS["node_red_fill"]
                outline = COLOURS["node_red_outline"]
            else:
                fill = COLOURS["node_fill"]
                outline = node_outline
            self.canvas.create_oval(
                nx - r, ny - r, nx + r, ny + r,
                fill=fill, outline=outline, width=3,
                tags="tree",
            )

        # Pass 3: labels
        for node, (nx, ny) in positions.items():
            self.canvas.create_text(
                nx, ny,
                text=str(node.val),
                fill=text_colour, font=FONT_NODE,
                tags="tree",
            )

    def highlight_node(self, node_val, positions, callback):
        """Flash a node red, then call *callback* after the highlight fades."""
        self.draw_at_positions(positions, highlight_val=node_val)
        self._root.after(HIGHLIGHT_DURATION_MS, callback)

    # ---- animation ----

    def animate_frame(self, start, targets, frame, total_frames,
                      anim_delay, current_positions, animation_queue,
                      on_step_forward, animating_setter):
        """
        Lerp every node from *start* toward *targets* by t = frame/total_frames.

        Newly-inserted nodes (in targets but not start) animate from
        their parent's start position so they appear to "drop in".
        """
        # Ease-in-out (smoothstep): slow → fast → slow
        t = frame / total_frames
        t = t * t * (3.0 - 2.0 * t)

        interpolated = {}
        for node, (tx, ty) in targets.items():
            if node in start:
                sx, sy = start[node]
            else:
                # New node — find parent position as origin
                sx, sy = self._find_parent_start(node, start, targets)
            interpolated[node] = (sx + (tx - sx) * t,
                                  sy + (ty - sy) * t)

        self.draw_at_positions(interpolated)

        if frame < total_frames:
            self._root.after(
                anim_delay,
                self.animate_frame, start, targets, frame + 1, total_frames,
                anim_delay, current_positions, animation_queue,
                on_step_forward, animating_setter,
            )
        else:
            # Animation complete — lock in final positions
            current_positions.clear()
            current_positions.update(targets)
            animating_setter(False)

            # Auto-drain the queue to prevent stalls and auto-play scripts
            if animation_queue:
                self._root.after(10, on_step_forward)

    def _find_parent_start(self, child, start, targets):
        """Locate the start position of *child*'s parent for drop-in animation."""
        for node in targets:
            if node.left is child or node.right is child:
                if node in start:
                    return start[node]
                # parent is also new (unlikely but safe fallback)
                return targets[node]
        # Fallback: centre top
        return (self.canvas.winfo_width() / 2, Y_START)

    # ---- static / resize draw ----

    def draw_tree(self, bst_root, current_positions, event=None):
        """
        Clear the canvas and redraw the BST at its computed positions.
        Also snapshots *current_positions* so future animations start
        from the correct coordinates.
        """
        if bst_root is None:
            self.canvas.delete("tree")
            self._draw_dot_grid()
            current_positions.clear()
            return

        positions = self.capture_target_positions(bst_root)
        self.draw_at_positions(positions)
        current_positions.clear()
        current_positions.update(positions)

    # ---- stats overlay ----

    def draw_stats(self, bst_root):
        """Draw a small stats box in the top-right corner of the canvas."""
        self.canvas.delete("stats")
        if not bst_root:
            return

        height = self._tree_height(bst_root)
        count  = self._tree_count(bst_root)
        bf     = self._balance_factor(bst_root)

        text = f"Nodes: {count}   Height: {height}   Root BF: {bf}"
        w = self.canvas.winfo_width()
        self.canvas.create_text(
            w - 10, 10,
            text=text, anchor="ne",
            fill=COLOURS["fg_text"], font=FONT_BODY,
            tags="stats",
        )

    def _tree_height(self, node):
        return node.height if node else 0

    def _tree_count(self, node):
        if not node:
            return 0
        return 1 + self._tree_count(node.left) + self._tree_count(node.right)

    def _balance_factor(self, node):
        if not node:
            return 0
        lh = node.left.height if node.left else 0
        rh = node.right.height if node.right else 0
        return lh - rh
