"""
DSLVisualizerApp — main orchestrator (PyQt6 version).

Replaces tkinter / customtkinter with QMainWindow + QSplitter.
All root.after() calls are replaced with QTimer.singleShot().
"""

import copy
import csv

from lark.exceptions import UnexpectedInput
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from gui.ast_panel import ASTPanel
from gui.canvas_renderer import CanvasRenderer
from gui.constants import (
    ANIM_DELAY_MS,
    ANIM_FRAMES,
    COLOURS,
    MODE_AVL,
    MODE_RB,
    TEMPLATES,
)
from gui.controls import ControlPanel
from gui.editor import EditorPanel
from interpreter import DSLInterpreter
from tree import BST

_STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLOURS["bg_dark"]};
    color: {COLOURS["fg_text"]};
    font-family: "Inter", sans-serif;
}}
QSplitter::handle:horizontal {{
    background: transparent;
    width: 6px;
}}
QSplitter::handle:vertical {{
    background: transparent;
    height: 6px;
}}
#PanelCard {{
    background-color: rgba(252, 250, 245, 0.85);
    border: 1px solid #DDCBB7;
    border-radius: 12px;
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
    font-family: "Inter", sans-serif;
    font-size: 12px;
}}
QStatusBar {{
    background-color: {COLOURS["status_bg"]};
    color: {COLOURS["status_fg"]};
    font-family: "Inter", sans-serif;
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
        self._steps_done = 0

        self.current_mode = MODE_AVL

        self._build_layout()
        self._bind_shortcuts()

        # Defer first draw until the window has been shown and sized.
        QTimer.singleShot(0, self._initial_draw)

    # ── layout ──────────────────────────────────────────────────────────

    def _create_card(self, widget):
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)

        card = QFrame()
        card.setObjectName("PanelCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(0)
        card_layout.addWidget(widget)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(QColor(82, 64, 50, 31))
        card.setGraphicsEffect(shadow)

        container_layout.addWidget(card)
        return container

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
        v_split.setMinimumWidth(340)

        self.editor_panel = EditorPanel(v_split)
        self.ast_panel = ASTPanel(v_split)
        self.control_panel = ControlPanel(
            v_split,
            on_insert=self._on_insert_node,
            on_delete=self._on_delete_node,
            on_run_script=self._on_run_script,
            on_step_forward=self._on_step_forward,
            on_step_back=self._on_step_back,
            on_clear=self._on_clear_tree,
            on_reset=self._on_reset_view,
            on_speed_change=self._on_speed_change,
            on_mode_change=self._on_mode_change,
            on_export=self._on_export,
        )
        v_split.addWidget(self._create_card(self.editor_panel))
        v_split.addWidget(self._create_card(self.ast_panel))
        v_split.addWidget(self._create_card(self.control_panel))
        v_split.setSizes([340, 140, 280])

        self.renderer = CanvasRenderer(on_resize=self._on_canvas_resize)

        h_split.addWidget(v_split)
        h_split.addWidget(self.renderer)
        h_split.setSizes([340, 860])  # ~28/72 ratio for 1200 width

        root_layout.addWidget(h_split)

        # Status bar
        self.statusBar().showMessage("Ready")

        # Wire real-time validation
        self.editor_panel.set_validate_callback(self._validate_script)

    def _initial_draw(self):
        self._on_mode_change(self.current_mode)  # Initialize editor and canvas state
        self.renderer.draw_tree(self.bst.root, self._current_positions)
        self.renderer.draw_stats(self.bst.root)

    def _on_canvas_resize(self):
        self.renderer.draw_tree(self.bst.root, self._current_positions)

    # ── event handlers ───────────────────────────────────────────────────

    def _on_mode_change(self, new_mode: str):
        self.current_mode = new_mode
        self.renderer.set_mode(new_mode)

        # Handle Template logic
        current_script = self.editor_panel.get_script().strip()
        from gui.editor import _PLACEHOLDER

        is_untouched = (
            (current_script == "")
            or (current_script == _PLACEHOLDER.strip())
            or any(current_script == tpl.strip() for tpl in TEMPLATES.values())
        )

        if is_untouched:
            self.editor_panel.editor.setPlainText(TEMPLATES[new_mode])

        # Recolor tree if needed
        self._recolor_tree(self.bst.root, new_mode)

        self.animation_queue.clear()
        self._on_reset_view()

    def _recolor_tree(self, node, mode: str):
        if not node:
            return
        if mode == MODE_AVL:
            if hasattr(node, "colour"):
                delattr(node, "colour")
        else:
            if getattr(node, "colour", None) not in ("RED", "BLACK"):
                node.colour = "RED"

        self._recolor_tree(node.left, mode)
        self._recolor_tree(node.right, mode)

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

        # Highlight script line
        if isinstance(action, dict) and action.get("type") == "highlight_line":
            self.editor_panel.set_active_line(action["line"])
            self._on_step_forward()
            return

        # Snapshot for undo
        self._history_stack.append(copy.deepcopy(self.bst.root))

        start_positions = dict(self._current_positions)
        action()  # mutate BST

        targets = self.renderer.capture_target_positions(self.bst.root)
        self._animating = True
        self.renderer.animate_frame(
            start_positions,
            targets,
            1,
            ANIM_FRAMES,
            self._anim_delay,
            self._current_positions,
            self.animation_queue,
            self._on_step_forward,
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
            start_positions,
            targets,
            1,
            ANIM_FRAMES,
            self._anim_delay,
            self._current_positions,
            self.animation_queue,
            self._on_step_forward,
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

        # For Red-Black mode, immediately queue the balancing steps so that
        # each GUI delete is fixed up on the spot — mirroring what the DSL
        # script runner does — instead of leaving the tree in a broken state.
        if self.current_mode == MODE_RB:
            script = self.editor_panel.get_script()
            if script:
                try:
                    parsed_tree = self.interpreter.parser.parse(script)
                    has_balance_rules = any(
                        sub.data == "rule"
                        for sub in parsed_tree.iter_subtrees()
                    )
                    if has_balance_rules:
                        # Simulate the delete on a deep copy of the current
                        # tree to count the required balance steps without
                        # touching the live BST.
                        sim_root = copy.deepcopy(self.bst.root)
                        sim_bst = BST()
                        sim_bst.root = sim_root
                        sim_bst.delete(val)
                        sim_root = sim_bst.root

                        balance_steps = 0
                        try:
                            while True:
                                sim_root, changed = self.interpreter.balance_step(
                                    sim_root, parsed_tree
                                )
                                if not changed:
                                    break
                                balance_steps += 1
                                if balance_steps > 50:
                                    self._status(
                                        "Status: Stopped after 50 steps "
                                        "(possible infinite loop)."
                                    )
                                    break
                        except Exception as exc:
                            self._status(f"Balance simulation error: {exc}")

                        for _ in range(balance_steps):
                            self.animation_queue.append(
                                lambda p=parsed_tree: setattr(
                                    self.bst,
                                    "root",
                                    self.interpreter.balance_step(
                                        self.bst.root, p
                                    )[0],
                                )
                            )
                except Exception:
                    # Invalid / empty script — delete without balancing
                    pass

        total = len(self.animation_queue)
        self._total_steps = total
        self._steps_done = 0
        self._on_step_forward()
        self.control_panel.clear_insert_entry()
        balance_note = (
            f" + {total - 2} balance step(s)" if total > 2 else ""
        )
        self._status(f"Deleting {val}{balance_note}…")

    def _on_clear_tree(self):
        self.animation_queue.clear()
        self.animation_queue.append(lambda: setattr(self.bst, "root", None))
        self._on_step_forward()
        self._status("Tree cleared.")
        self.renderer.draw_stats(self.bst.root)
        self.editor_panel.clear_active_line()

    def _on_run_script(self):
        self.editor_panel.clear_error()
        self.editor_panel.clear_active_line()

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

        if has_balance_rules:
            sim_root = copy.deepcopy(self.bst.root)  # may be None if tree is empty
            for cmd, val in direct_commands:
                sim_bst = BST()
                sim_bst.root = sim_root
                if cmd == "INSERT":
                    sim_bst.insert(val)
                elif cmd == "DELETE":
                    sim_bst.delete(val)
                sim_root = sim_bst.root

            if sim_root is not None:
                try:
                    steps = 0
                    while True:
                        sim_root, changed = self.interpreter.balance_step(
                            sim_root, parsed_tree
                        )
                        if not changed:
                            break
                        steps += 1
                        if steps > 50:
                            self._status(
                                "Status: Stopped after 50 steps (possible infinite loop)."
                            )
                            break
                except Exception as exc:
                    self._status(str(exc))
                    return

                for _ in range(steps):
                    self.animation_queue.append(
                        lambda p=parsed_tree: setattr(
                            self.bst,
                            "root",
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

    def _on_reset_view(self):
        self.renderer.draw_tree(self.bst.root, self._current_positions)
        self.renderer.draw_stats(self.bst.root)
        self.editor_panel.clear_active_line()
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
        lh = node.left.height if node.left else 0
        rh = node.right.height if node.right else 0
        rows.append(
            {
                "val": node.val,
                "height": node.height,
                "balance_factor": lh - rh,
                "colour": node.colour,
            }
        )
        self._collect_rows(node.left, rows)
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
            if action.get("type") == "highlight":
                return f"Highlighting node {action.get('node_val')}"
            elif action.get("type") == "highlight_line":
                return f"Executing rule on line {action.get('line')}"
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
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(
            self._on_run_script
        )
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self._clear_editor)

    def _clear_editor(self):
        self.editor_panel.clear()
        self._status("Status: Editor cleared  (Ctrl+L)")

    # ── entry point (backwards-compat) ───────────────────────────────────

    def run(self):
        """Deprecated — use gui.main() which handles QApplication.exec()."""
        pass
