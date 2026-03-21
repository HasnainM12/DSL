"""
DSLVisualizerApp — main orchestrator.
Wires together EditorPanel, CanvasRenderer, and ControlPanel.
"""

import copy
import tkinter as tk
import customtkinter as ctk
from lark.exceptions import UnexpectedInput

from tree import BST
from interpreter import DSLInterpreter

from gui.constants import COLOURS, ANIM_FRAMES, ANIM_DELAY_MS
from gui.editor import EditorPanel
from gui.canvas_renderer import CanvasRenderer
from gui.controls import ControlPanel
from gui.ast_panel import ASTPanel


class DSLVisualizerApp:
    """CustomTkinter-based DSL Tree Visualiser with animated BST rendering."""

    def __init__(self):
        self.root = ctk.CTk()
        self._configure_root()

        # --- Data model ---
        self.bst = BST()
        for val in [50, 25, 75, 10, 30, 60, 80]:
            self.bst.insert(val)

        self.interpreter = DSLInterpreter()

        # --- Animation state ---
        self.animation_queue = []
        self._current_positions = {}
        self._animating = False
        self._anim_delay = ANIM_DELAY_MS

        # --- Undo history ---
        self._history_stack = []  # list of deep-copied BST roots

        # --- Step counter ---
        self._total_steps = 0
        self._steps_done = 0

        # --- Build UI ---
        self._build_layout()
        self._bind_shortcuts()

    # ---- root window ----

    def _configure_root(self):
        self.root.title("DSL Tree Visualizer")
        self.root.geometry("1200x800")
        self.root.minsize(800, 500)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Allow the root grid cell to stretch with window resize
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

    # ---- layout ----

    def _build_layout(self):
        # Outer horizontal PanedWindow: left panel | canvas
        self.h_pane = tk.PanedWindow(
            self.root, orient=tk.HORIZONTAL,
            bg=COLOURS["border"], sashwidth=3, sashrelief=tk.FLAT,
        )
        self.h_pane.grid(row=0, column=0, sticky="nsew")

        # Left: vertical PanedWindow (editor on top, controls on bottom)
        self.v_pane = tk.PanedWindow(
            self.h_pane, orient=tk.VERTICAL,
            bg=COLOURS["border"], sashwidth=3, sashrelief=tk.FLAT,
        )

        # Build each zone
        self.editor_panel = EditorPanel(self.v_pane)
        self.ast_panel = ASTPanel(self.v_pane)
        self.control_panel = ControlPanel(
            self.v_pane,
            on_insert=self._on_insert_node,
            on_delete=self._on_delete_node,
            on_run_script=self._on_run_script,
            on_step_forward=self._on_step_forward,
            on_step_back=self._on_step_back,
            on_clear=self._on_clear_tree,
            on_reset=self._on_reset_view,
            on_speed_change=self._on_speed_change,
            on_export=self._on_export,
        )
        self.renderer = CanvasRenderer(self.h_pane, self.root)

        # Redraw tree whenever canvas is resized
        self.renderer.canvas.bind("<Configure>", self._on_canvas_resize)

        # Add panes with size hints
        self.h_pane.add(self.v_pane, minsize=320, width=460)
        self.h_pane.add(self.renderer.canvas_frame, minsize=300)

        # Wire real-time validation
        self.editor_panel._on_validate_callback = self._validate_script

    # ---- event handlers ----

    def _on_canvas_resize(self, event=None):
        """Redraw the tree when the canvas is resized."""
        self.renderer.draw_tree(self.bst.root, self._current_positions, event)

    def _on_step_forward(self):
        """Pop the next action from the queue, apply it, and animate."""
        if self._animating:
            return
        if not self.animation_queue:
            self._status("Status: No more steps in the queue.")
            return

        action = self.animation_queue.pop(0)

        # --- Handle highlight actions (deletion flash) ---
        if isinstance(action, dict) and action.get("type") == "highlight":
            self._animating = True
            self.renderer.highlight_node(
                action["node_val"],
                self._current_positions,
                callback=lambda: (
                    self._set_animating(False),
                    self._on_step_forward(),
                ),
            )
            return

        # Save undo snapshot before mutating
        self._history_stack.append(copy.deepcopy(self.bst.root))

        start_positions = dict(self._current_positions)
        action()  # mutate BST

        targets = self.renderer.capture_target_positions(self.bst.root)
        self._animating = True
        self.renderer.animate_frame(
            start_positions, targets, 1, ANIM_FRAMES,
            self._anim_delay, self._current_positions,
            self.animation_queue, self._on_step_forward,
            self._set_animating,
        )

        self._steps_done += 1
        self._status(f"Step {self._steps_done}/{self._total_steps} — {self._describe_action(action)}")
        self.renderer.draw_stats(self.bst.root)

    def _on_step_back(self):
        """Undo the last mutation by restoring a BST snapshot."""
        if self._animating:
            return
        if not self._history_stack:
            self._status("Status: Nothing to undo.")
            return

        # Restore previous BST root
        start_positions = dict(self._current_positions)
        self.bst.root = self._history_stack.pop()

        targets = self.renderer.capture_target_positions(self.bst.root)
        self._animating = True
        self.renderer.animate_frame(
            start_positions, targets, 1, ANIM_FRAMES,
            self._anim_delay, self._current_positions,
            self.animation_queue, self._on_step_forward,
            self._set_animating,
        )
        self._status(f"Undone. {len(self._history_stack)} undo step(s) remaining.")
        self.renderer.draw_stats(self.bst.root)

    def _on_insert_node(self):
        """Validate entry, queue an insert, and kick off animation."""
        raw = self.control_panel.get_insert_value()
        try:
            val = int(raw)
        except ValueError:
            self._status("Status: Please enter a valid integer.")
            return
        if self.bst.contains(val):
            self._status(f"Status: Node {val} already exists.")
            return

        self.animation_queue.clear()  # Flush stale animations

        self.animation_queue.append(lambda v=val: self.bst.insert(v))
        self._on_step_forward()
        self.control_panel.clear_insert_entry()
        self._status(f"Inserted {val}.")
        self.renderer.draw_stats(self.bst.root)

    def _on_delete_node(self):
        """Validate entry, queue a highlight + delete, and kick off animation."""
        raw = self.control_panel.get_insert_value()
        try:
            val = int(raw)
        except ValueError:
            self._status("Status: Please enter a valid integer.")
            return
        if not self.bst.contains(val):
            self._status(f"Status: Node {val} not found.")
            return

        self.animation_queue.clear()

        # Phase 1: flash the node red
        self.animation_queue.append({"type": "highlight", "node_val": val})
        # Phase 2: actually remove it
        self.animation_queue.append(lambda v=val: self.bst.delete(v))

        self._on_step_forward()
        self.control_panel.clear_insert_entry()
        
        script = self.editor_panel.get_script()
        if "COLOUR" in script.upper():
            self._status(f"Warning: Deleting nodes with a Red-Black script loaded may corrupt invariants! Deleting {val}…")
        else:
            self._status(f"Deleting {val}…")

    def _on_clear_tree(self):
        """Queue a tree clear and animate."""
        self.animation_queue.clear()  # Flush stale animations
        self.animation_queue.append(lambda: setattr(self.bst, 'root', None))
        self._on_step_forward()
        self._status("Tree cleared.")
        self.renderer.draw_stats(self.bst.root)

    def _on_run_script(self):
        """Parse the editor DSL, simulate to count steps, then queue them."""
        self.editor_panel.clear_error()

        script = self.editor_panel.get_script()
        if not script:
            self._status("Status: Editor is empty — nothing to run.")
            return

        # Parse once
        try:
            parsed_tree = self.interpreter.parser.parse(script)
        except UnexpectedInput as exc:
            self.editor_panel.set_error(exc.line, exc.column, str(exc))
            self._status(f"Syntax Error at line {exc.line}, col {exc.column}.")
            self.ast_panel.clear()
            return

        # Show AST in the viewer panel
        self.ast_panel.update(parsed_tree)

        # Detect IF…THEN rules by walking the AST directly
        # (execute_script evaluates against None, so conditions are always
        #  False and no rotation strings are produced for rule-only scripts)
        has_balance_rules = any(
            sub.data == "rule"
            for sub in parsed_tree.iter_subtrees()
        )

        # Execute script to get flat action list (INSERT/DELETE tuples)
        try:
            actions = self.interpreter.execute_script(script)
        except Exception as exc:
            self._status(f"Runtime Error: {exc}")
            return

        # Collect direct commands (INSERT / DELETE tuples)
        direct_commands = [a for a in actions if isinstance(a, tuple)]

        if not direct_commands and not has_balance_rules:
            self._status("Status: Script produced no actions.")
            return

        self.animation_queue.clear()

        for cmd, val in direct_commands:
            if cmd == "INSERT":
                self.animation_queue.append(lambda v=val: self.bst.insert(v))
            elif cmd == "DELETE":
                self.animation_queue.append(lambda v=val: self.bst.delete(v))

        # If the script contains IF…THEN rules,
        # simulate balance steps and queue them after the inserts/deletes.
        if has_balance_rules and self.bst.root is not None:
            sim_root = copy.deepcopy(self.bst.root)
            # Apply any pending inserts/deletes to the simulation copy
            for cmd, val in direct_commands:
                sim_bst = BST()
                sim_bst.root = sim_root
                if cmd == "INSERT":
                    sim_bst.insert(val)
                elif cmd == "DELETE":
                    sim_bst.delete(val)
                sim_root = sim_bst.root

            try:
                steps = 0
                while True:
                    sim_root, changed = self.interpreter.balance_step(sim_root, parsed_tree)
                    if not changed:
                        break
                    steps += 1
                    if steps > 50:
                        self._status("Status: Stopped after 50 steps (possible infinite loop).")
                        break
            except Exception as exc:
                self._status(str(exc))
                return

            for _ in range(steps):
                self.animation_queue.append(
                    lambda p=parsed_tree: setattr(
                        self.bst, 'root',
                        self.interpreter.balance_step(self.bst.root, p)[0],
                    )
                )

        total = len(self.animation_queue)
        if total == 0:
            self._status("Status: Tree is already balanced — no actions needed.")
            return

        self._total_steps = total
        self._steps_done = 0

        self._on_step_forward()
        self._status(f"Queued {total} step(s). Animating…")

    # ---- helpers ----

    def _status(self, message: str):
        """Update the control panel status bar."""
        self.control_panel.set_status(message)

    def _on_reset_view(self):
        """Recompute node positions and redraw from scratch."""
        self.renderer.draw_tree(self.bst.root, self._current_positions)
        self.renderer.draw_stats(self.bst.root)
        self._status("Status: View reset.")

    def _on_export(self):
        """Export current tree data to a CSV file."""
        import csv
        import tkinter.filedialog as fd
        path = fd.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return
        rows = []
        self._collect_rows(self.bst.root, rows)
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["val", "height", "balance_factor", "colour"],
            )
            writer.writeheader()
            writer.writerows(rows)
        self._status(f"Exported to {path}")

    def _collect_rows(self, node, rows):
        """Recursively collect tree node data into a list of dicts."""
        if not node:
            return
        lh = node.left.height if node.left else 0
        rh = node.right.height if node.right else 0
        rows.append({
            "val": node.val,
            "height": node.height,
            "balance_factor": lh - rh,
            "colour": node.colour,
        })
        self._collect_rows(node.left, rows)
        self._collect_rows(node.right, rows)

    def _describe_action(self, action) -> str:
        """Return a human-readable description of an animation action."""
        if callable(action):
            return "Applying tree mutation"
        if isinstance(action, dict):
            return f"Highlighting node {action.get('node_val')}"
        return str(action)

    def _validate_script(self, script: str):
        """Real-time syntax check called by the editor's debounced timer."""
        if not script:
            self.editor_panel.clear_error()
            self._status("")
            return
        try:
            self.interpreter.parser.parse(script)
        except UnexpectedInput as exc:
            self.editor_panel.set_error(exc.line, exc.column, str(exc))
            self._status(f"Syntax Error at line {exc.line}, col {exc.column}.")
        except Exception:
            # Non-syntax errors (e.g. partially typed line) — ignore
            pass
        else:
            self.editor_panel.clear_error()
            self._status("✓ Script valid")

    def _set_animating(self, value: bool):
        """Setter callback for the animation guard flag."""
        self._animating = value

    def _on_speed_change(self, value: int):
        """Update the animation delay from the slider."""
        self._anim_delay = value

    # ---- keyboard shortcuts ----

    def _bind_shortcuts(self):
        self.root.bind("<Control-Return>", lambda e: self._on_run_script())
        self.root.bind("<Control-l>", self._clear_editor)

    def _clear_editor(self, _event=None):
        self.editor_panel.clear()
        self._status("Status: Editor cleared  (Ctrl+L)")
        return "break"  # prevent default behaviour

    # ---- entry point ----

    def run(self):
        """Start the Tk main loop."""
        self.root.mainloop()
