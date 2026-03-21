"""
DSLVisualizerApp — main orchestrator (PyQt6 version).

Replaces tkinter / customtkinter with QMainWindow + QSplitter.
All root.after() calls are replaced with QTimer.singleShot().
"""

import copy
import csv

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout,
    QFileDialog, QStatusBar,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence

from lark.exceptions import UnexpectedInput

from tree import BST
from interpreter import DSLInterpreter

from gui.constants import COLOURS, ANIM_FRAMES, ANIM_DELAY_MS
from gui.editor import EditorPanel
from gui.canvas_renderer import CanvasRenderer
from gui.controls import ControlPanel
from gui.ast_panel import ASTPanel


_STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLOURS["bg_dark"]};
    color: {COLOURS["fg_text"]};
    font-family: Inter;
}}
QSplitter::handle:horizontal {{
    background: {COLOURS["border"]};
    width: 3px;
}}
QSplitter::handle:vertical {{
    background: {COLOURS["border"]};
    height: 3px;
}}
QScrollBar:vertical {{
    background: {COLOURS["bg_dark"]};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {COLOURS["border"]};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {COLOURS["fg_gutter"]}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {COLOURS["bg_dark"]};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {COLOURS["border"]};
    border-radius: 4px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{ background: {COLOURS["fg_gutter"]}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QToolTip {{
    background-color: {COLOURS["bg_card"]};
    color: {COLOURS["fg_text"]};
    border: 1px solid {COLOURS["border"]};
    padding: 4px 8px;
    font-family: Inter;
    font-size: 12px;
}}
QStatusBar {{
    background-color: {COLOURS["status_bg"]};
    color: {COLOURS["status_fg"]};
    font-family: Inter;
    font-size: 13px;
    padding: 2px 10px;
}}
"""


class DSLVisualizerApp(QMainWindow):
    """CustomTkinter → PyQt6 rewrite of the DSL Tree Visualiser."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DSL Tree Visualizer")
        self.resize(1200, 800)
        self.setMinimumSize(800, 500)
        self.setStyleSheet(_STYLESHEET)

        # ── data model ───────────────────────────────────────────────────
        self.bst = BST()
        for val in [50, 25, 75, 10, 30, 60, 80]:
            self.bst.insert(val)

        self.interpreter = DSLInterpreter()

        # ── animation state ───────────────────────────────────────────────
        self.animation_queue: list = []
        self._current_positions: dict = {}
        self._animating = False
        self._anim_delay = ANIM_DELAY_MS

        # ── undo history ──────────────────────────────────────────────────
        self._history_stack: list = []

        # ── step counter ──────────────────────────────────────────────────
        self._total_steps = 0
        self._steps_done  = 0

        self._build_layout()
        self._bind_shortcuts()

        # Defer first draw until the window has been shown and sized.
        QTimer.singleShot(0, self._initial_draw)

    # ── layout ──────────────────────────────────────────────────────────

    def _build_layout(self):
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Horizontal: left panel | canvas
        h_split = QSplitter(Qt.Orientation.Horizontal)

        # Vertical left panel: editor | AST | controls
        v_split = QSplitter(Qt.Orientation.Vertical)
        v_split.setMinimumWidth(320)

        self.editor_panel  = EditorPanel(v_split)
        self.ast_panel     = ASTPanel(v_split)
        self.control_panel = ControlPanel(
            v_split,
            on_insert       = self._on_insert_node,
            on_delete       = self._on_delete_node,
            on_run_script   = self._on_run_script,
            on_step_forward = self._on_step_forward,
            on_step_back    = self._on_step_back,
            on_clear        = self._on_clear_tree,
            on_reset        = self._on_reset_view,
            on_speed_change = self._on_speed_change,
            on_export       = self._on_export,
        )
        v_split.setSizes([320, 120, 260])
        v_split.addWidget(self.editor_panel)
        v_split.addWidget(self.ast_panel)
        v_split.addWidget(self.control_panel)

        self.renderer = CanvasRenderer(on_resize=self._on_canvas_resize)

        h_split.addWidget(v_split)
        h_split.addWidget(self.renderer)
        h_split.setSizes([460, 740])

        root_layout.addWidget(h_split)

        # Status bar
        self.statusBar().showMessage("Ready")

        # Wire real-time validation
        self.editor_panel.set_validate_callback(self._validate_script)

    def _initial_draw(self):
        self.renderer.draw_tree(self.bst.root, self._current_positions)
        self.renderer.draw_stats(self.bst.root)

    def _on_canvas_resize(self):
        self.renderer.draw_tree(self.bst.root, self._current_positions)

    # ── event handlers ───────────────────────────────────────────────────

    def _on_step_forward(self):
        if self._animating:
            return
        if not self.animation_queue:
            self._status("Status: No more steps in the queue.")
            return

        action = self.animation_queue.pop(0)

        # Highlight (deletion flash)
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

        # Snapshot for undo
        self._history_stack.append(copy.deepcopy(self.bst.root))

        start_positions = dict(self._current_positions)
        action()                                              # mutate BST

        targets = self.renderer.capture_target_positions(self.bst.root)
        self._animating = True
        self.renderer.animate_frame(
            start_positions, targets, 1, ANIM_FRAMES,
            self._anim_delay, self._current_positions,
            self.animation_queue, self._on_step_forward,
            self._set_animating,
        )

        self._steps_done += 1
        self._status(
            f"Step {self._steps_done}/{self._total_steps} — {self._describe_action(action)}"
        )
        self.renderer.draw_stats(self.bst.root)

    def _on_step_back(self):
        if self._animating:
            return
        if not self._history_stack:
            self._status("Status: Nothing to undo.")
            return

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
        raw = self.control_panel.get_insert_value()
        try:
            val = int(raw)
        except ValueError:
            self._status("Status: Please enter a valid integer.")
            return
        if self.bst.contains(val):
            self._status(f"Status: Node {val} already exists.")
            return

        self.animation_queue.clear()
        self.animation_queue.append(lambda v=val: self.bst.insert(v))
        self._on_step_forward()
        self.control_panel.clear_insert_entry()
        self._status(f"Inserted {val}.")
        self.renderer.draw_stats(self.bst.root)

    def _on_delete_node(self):
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
        self.animation_queue.append({"type": "highlight", "node_val": val})
        self.animation_queue.append(lambda v=val: self.bst.delete(v))
        self._on_step_forward()
        self.control_panel.clear_insert_entry()

        script = self.editor_panel.get_script()
        if "COLOUR" in script.upper():
            self._status(
                f"Warning: Deleting nodes with a Red-Black script may corrupt invariants! Deleting {val}…"
            )
        else:
            self._status(f"Deleting {val}…")

    def _on_clear_tree(self):
        self.animation_queue.clear()
        self.animation_queue.append(lambda: setattr(self.bst, "root", None))
        self._on_step_forward()
        self._status("Tree cleared.")
        self.renderer.draw_stats(self.bst.root)

    def _on_run_script(self):
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

        # Show AST
        self.ast_panel.update(parsed_tree)

        has_balance_rules = any(
            sub.data == "rule" for sub in parsed_tree.iter_subtrees()
        )

        try:
            actions = self.interpreter.execute_script(script)
        except Exception as exc:
            self._status(f"Runtime Error: {exc}")
            return

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

        if has_balance_rules and self.bst.root is not None:
            sim_root = copy.deepcopy(self.bst.root)
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
                        self.bst, "root",
                        self.interpreter.balance_step(self.bst.root, p)[0],
                    )
                )

        total = len(self.animation_queue)
        if total == 0:
            self._status("Status: Tree is already balanced — no actions needed.")
            return

        self._total_steps = total
        self._steps_done  = 0
        self._on_step_forward()
        self._status(f"Queued {total} step(s). Animating…")

    def _on_reset_view(self):
        self.renderer.draw_tree(self.bst.root, self._current_positions)
        self.renderer.draw_stats(self.bst.root)
        self._status("Status: View reset.")

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Tree CSV", "", "CSV files (*.csv)"
        )
        if not path:
            return
        rows: list[dict] = []
        self._collect_rows(self.bst.root, rows)
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["val", "height", "balance_factor", "colour"]
            )
            writer.writeheader()
            writer.writerows(rows)
        self._status(f"Exported to {path}")

    def _collect_rows(self, node, rows):
        if not node:
            return
        lh = node.left.height  if node.left  else 0
        rh = node.right.height if node.right else 0
        rows.append({
            "val": node.val,
            "height": node.height,
            "balance_factor": lh - rh,
            "colour": node.colour,
        })
        self._collect_rows(node.left,  rows)
        self._collect_rows(node.right, rows)

    # ── helpers ─────────────────────────────────────────────────────────

    def _status(self, message: str):
        self.statusBar().showMessage(message)

    def _set_animating(self, value: bool):
        self._animating = value

    def _on_speed_change(self, value: int):
        self._anim_delay = value

    def _describe_action(self, action) -> str:
        if callable(action):
            return "Applying tree mutation"
        if isinstance(action, dict):
            return f"Highlighting node {action.get('node_val')}"
        return str(action)

    def _validate_script(self, script: str):
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
            pass
        else:
            self.editor_panel.clear_error()
            self._status("✓ Script valid")

    # ── keyboard shortcuts ───────────────────────────────────────────────

    def _bind_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self._on_run_script)
        QShortcut(QKeySequence("Ctrl+L"),      self).activated.connect(self._clear_editor)

    def _clear_editor(self):
        self.editor_panel.clear()
        self._status("Status: Editor cleared  (Ctrl+L)")

    # ── entry point (backwards-compat) ───────────────────────────────────

    def run(self):
        """Deprecated — use gui.main() which handles QApplication.exec()."""
        pass
