"""
CanvasRenderer — tree drawing and animation engine.
Uses tk.Canvas directly (CustomTkinter has no canvas equivalent).
"""

import tkinter as tk
from PIL import Image, ImageDraw, ImageTk

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
        
        # Keep references to PIL PhotoImages so they aren't garbage collected
        self._edge_images = []

        # Generate smooth PIL images for nodes
        self._generate_node_images()

    def _generate_node_images(self):
        """Create super-sampled AA circular images to replace jagged Tkinter ovals."""
        self.img_default = self._create_aa_circle(
            NODE_RADIUS, COLOURS["node_fill"], 
            COLOURS["node_outline"], COLOURS["node_shadow"]
        )
        self.img_red = self._create_aa_circle(
            NODE_RADIUS, COLOURS["node_red_fill"], 
            COLOURS["node_red_outline"], COLOURS["node_shadow"]
        )
        self.img_highlight = self._create_aa_circle(
            NODE_RADIUS, COLOURS["node_delete_highlight"], 
            COLOURS["node_delete_highlight"], COLOURS["node_shadow"]
        )

    def _create_aa_circle(self, radius, fill_color, outline_color, shadow_color):
        """Super-sample (4x) a circle with a drop shadow, then downscale for perfect AA."""
        scale = 4
        r = radius * scale
        pad = 8 * scale  # padding for shadow blur/offset
        size = r * 2 + pad * 2
        
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        shadow_offset_x = 0
        shadow_offset_y = 4 * scale
        
        # Draw Shadow
        shadow_box = [pad + shadow_offset_x, pad + shadow_offset_y, 
                      pad + r * 2 + shadow_offset_x, pad + r * 2 + shadow_offset_y]
        draw.ellipse(shadow_box, fill=shadow_color)
        
        # Draw Outline (bottom layer)
        box = [pad, pad, pad + r * 2, pad + r * 2]
        draw.ellipse(box, fill=outline_color)
        
        # Draw Fill (top layer) - simulated border radius
        border_w = 3 * scale
        inner_box = [pad + border_w, pad + border_w, 
                     pad + r * 2 - border_w, pad + r * 2 - border_w]
        draw.ellipse(inner_box, fill=fill_color)
        
        # Downscale
        final_size = size // scale
        img = img.resize((final_size, final_size), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)

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
        self._edge_images = []

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

        # Pass 1: edges (Modern S-curves with Faux Anti-Aliasing)
        for node, (px, py) in positions.items():
            if node.left and node.left in positions:
                cx, cy = positions[node.left]
                self._draw_aa_edge(px, py, cx, cy)
            if node.right and node.right in positions:
                cx, cy = positions[node.right]
                self._draw_aa_edge(px, py, cx, cy)

        # Pass 2: perfectly rounded node sprites
        for node, (nx, ny) in positions.items():
            is_highlighted = (highlight_val is not None and node.val == highlight_val)
            if is_highlighted:
                img = self.img_highlight
            elif getattr(node, 'colour', None) == "RED":
                img = self.img_red
            else:
                img = self.img_default
                
            # Place the pre-rendered AA image
            self.canvas.create_image(nx, ny, image=img, tags="tree")

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

    def _draw_aa_edge(self, px, py, cx, cy):
        """Draw perfect anti-aliased S-curves via super-sampled PIL images."""
        scale = 3  # 3x supersampling is enough for great AA and fast performance
        
        # Calculate bounding box
        min_x, max_x = min(px, cx), max(px, cx)
        min_y, max_y = min(py, cy), max(py, cy)
        
        pad = 6  # padding for line width/shadows
        width = int(max_x - min_x + 2 * pad)
        height = int(max_y - min_y + 2 * pad)
        
        if width <= 0 or height <= 0: return

        img = Image.new('RGBA', (width * scale, height * scale), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Local coordinates mapped to the image
        loc_px = (px - min_x + pad) * scale
        loc_py = (py - min_y + pad) * scale
        loc_cx = (cx - min_x + pad) * scale
        loc_cy = (cy - min_y + pad) * scale

        loc_cy_mid = (loc_py + loc_cy) / 2

        # Generate S-curve points (Cubic Bezier)
        steps = max(15, int(abs(py - cy) / 4)) # Adaptive steps based on length
        curve_points = []
        for i in range(steps + 1):
            t = i / steps
            u = 1 - t
            # P0=(loc_px, loc_py), P1=(loc_px, loc_cy_mid), P2=(loc_cx, loc_cy_mid), P3=(loc_cx, loc_cy)
            x = (u**3)*loc_px + 3*(u**2)*t*loc_px + 3*u*(t**2)*loc_cx + (t**3)*loc_cx
            y = (u**3)*loc_py + 3*(u**2)*t*loc_cy_mid + 3*u*(t**2)*loc_cy_mid + (t**3)*loc_cy
            curve_points.append((x, y))

        # Draw the main line. Add a slightly darker shadow line underneath for depth.
        draw.line(curve_points, fill="#0f172a", width=6 * scale, joint='curve') # shadow/border (Slate 900)
        draw.line(curve_points, fill=COLOURS["edge_colour"], width=2 * scale, joint='curve') # core
        
        # Downscale
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self._edge_images.append(photo)

        # Place on canvas
        self.canvas.create_image(min_x - pad, min_y - pad, image=photo, anchor="nw", tags="tree")

    # ---- animation ----

    def animate_frame(self, start, targets, frame, total_frames,
                      anim_delay, current_positions, animation_queue,
                      on_step_forward, animating_setter):
        """
        Lerp every node from *start* toward *targets* by t = frame/total_frames.

        Newly-inserted nodes (in targets but not start) animate from
        their parent's start position so they appear to "drop in".
        """
        # Back Ease Out (milder overshoot/spring effect)
        t = frame / total_frames
        s = 0.8
        t -= 1.0
        t = t * t * ((s + 1) * t + s) + 1.0

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
