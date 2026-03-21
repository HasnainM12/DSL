"""
ControlPanel — tree operations, script controls, speed slider (PyQt6 version).
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QSlider, QFrame,
)
from PyQt6.QtCore import Qt

from gui.constants import COLOURS, ANIM_DELAY_MS


def _label(text: str, bold=False) -> QLabel:
    lbl = QLabel(text)
    weight = "bold" if bold else "normal"
    lbl.setStyleSheet(f"""
        color: {COLOURS["fg_text"]};
        font-family: Inter;
        font-size: 13px;
        font-weight: {weight};
    """)
    return lbl


def _section_header(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        color: {COLOURS["header_accent"]};
        font-family: Inter;
        font-size: 14px;
        font-weight: bold;
        padding: 6px 12px 2px 12px;
    """)
    return lbl


def _separator() -> QFrame:
    sep = QFrame()
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background: {COLOURS['separator']}; margin: 0 16px;")
    return sep


def _btn(text: str, color: str, hover: str, tooltip: str = "") -> QPushButton:
    b = QPushButton(text)
    b.setFixedHeight(36)
    b.setStyleSheet(f"""
        QPushButton {{
            background-color: {color};
            color: {COLOURS["btn_fg"]};
            border: none;
            border-radius: 8px;
            padding: 0 14px;
            font-family: Inter;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
        QPushButton:pressed {{
            opacity: 0.85;
        }}
    """)
    if tooltip:
        b.setToolTip(tooltip)
    return b


class ControlPanel(QWidget):
    """Control panel with tree operations, script controls, and status bar."""

    def __init__(
        self, parent=None, *,
        on_insert, on_delete, on_run_script,
        on_step_forward, on_step_back, on_clear, on_reset,
        on_speed_change, on_export=None,
    ):
        super().__init__(parent)
        self._on_speed_change = on_speed_change

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(4)

        self._build_tree_ops(layout, on_insert, on_delete)
        layout.addWidget(_separator())
        self._build_script_controls(layout, on_run_script, on_step_forward, on_step_back)
        layout.addWidget(_separator())
        self._build_management(layout, on_clear, on_reset, on_export)

        layout.addStretch()

    # ── sections ─────────────────────────────────────────────────────────

    def _build_tree_ops(self, layout: QVBoxLayout, on_insert, on_delete):
        layout.addWidget(_section_header("🌳  Tree Operations"))

        row = QHBoxLayout()
        row.setContentsMargins(12, 4, 12, 4)
        row.setSpacing(8)

        row.addWidget(_label("Value:"))

        self._insert_entry = QLineEdit()
        self._insert_entry.setPlaceholderText("e.g. 42")
        self._insert_entry.setFixedWidth(90)
        self._insert_entry.setFixedHeight(36)
        self._insert_entry.setStyleSheet(f"""
            QLineEdit {{
                background: {COLOURS["entry_bg"]};
                color: {COLOURS["entry_fg"]};
                border: 1px solid {COLOURS["border"]};
                border-radius: 8px;
                padding: 0 8px;
                font-family: "Cascadia Code";
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border-color: {COLOURS["focus_ring"]};
            }}
        """)
        self._insert_entry.setToolTip("Enter an integer value")
        row.addWidget(self._insert_entry)

        self._insert_btn = _btn(
            "Insert", COLOURS["btn_bg"], COLOURS["btn_hover"],
            "Insert the value into the tree",
        )
        self._insert_btn.clicked.connect(on_insert)
        row.addWidget(self._insert_btn)

        self._delete_btn = _btn(
            "Delete", COLOURS["btn_danger"], COLOURS["btn_danger_hover"],
            "Delete the value from the tree",
        )
        self._delete_btn.clicked.connect(on_delete)
        row.addWidget(self._delete_btn)

        row.addStretch()
        layout.addLayout(row)

    def _build_script_controls(self, layout, on_run, on_fwd, on_back):
        layout.addWidget(_section_header("⚡  Script Controls"))

        row = QHBoxLayout()
        row.setContentsMargins(12, 4, 12, 4)
        row.setSpacing(8)

        run_btn = _btn(
            "▶  Run Script", COLOURS["btn_primary"], COLOURS["btn_primary_hover"],
            "Run DSL script on the current tree  (Ctrl+Enter)",
        )
        run_btn.clicked.connect(on_run)
        row.addWidget(run_btn)

        fwd_btn = _btn(
            "Step ▶▶", COLOURS["btn_bg"], COLOURS["btn_hover"],
            "Advance one balancing step",
        )
        fwd_btn.clicked.connect(on_fwd)
        row.addWidget(fwd_btn)

        back_btn = _btn(
            "◀◀ Step", COLOURS["btn_neutral"], COLOURS["btn_neutral_hover"],
            "Go back one balancing step",
        )
        back_btn.clicked.connect(on_back)
        row.addWidget(back_btn)

        row.addStretch()
        layout.addLayout(row)

        # Speed slider
        speed_row = QHBoxLayout()
        speed_row.setContentsMargins(12, 2, 12, 4)
        speed_row.setSpacing(8)
        speed_row.addWidget(_label("Animation delay (ms):"))

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(1, 150)
        self._slider.setValue(ANIM_DELAY_MS)
        self._slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {COLOURS["border"]};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {COLOURS["btn_bg"]};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {COLOURS["focus_ring"]};
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }}
        """)
        self._slider.valueChanged.connect(lambda v: self._on_speed_change(v))
        speed_row.addWidget(self._slider)

        val_lbl = _label(str(ANIM_DELAY_MS))
        val_lbl.setFixedWidth(28)
        self._slider.valueChanged.connect(lambda v: val_lbl.setText(str(v)))
        speed_row.addWidget(val_lbl)

        layout.addLayout(speed_row)

    def _build_management(self, layout, on_clear, on_reset, on_export):
        layout.addWidget(_section_header("🔧  Tree Management"))

        row = QHBoxLayout()
        row.setContentsMargins(12, 4, 12, 4)
        row.setSpacing(8)

        clear_btn = _btn(
            "Clear Tree", COLOURS["btn_danger"], COLOURS["btn_danger_hover"],
            "Remove all nodes from the tree",
        )
        clear_btn.clicked.connect(on_clear)
        row.addWidget(clear_btn)

        reset_btn = _btn(
            "Reset View", COLOURS["btn_neutral"], COLOURS["btn_neutral_hover"],
            "Recompute and redraw the tree",
        )
        reset_btn.clicked.connect(on_reset)
        row.addWidget(reset_btn)

        if on_export:
            export_btn = _btn(
                "Export CSV", COLOURS["btn_neutral"], COLOURS["btn_neutral_hover"],
                "Export tree data to CSV",
            )
            export_btn.clicked.connect(on_export)
            row.addWidget(export_btn)

        row.addStretch()
        layout.addLayout(row)

    # ── public API ────────────────────────────────────────────────────────

    def get_insert_value(self) -> str:
        return self._insert_entry.text().strip()

    def clear_insert_entry(self):
        self._insert_entry.clear()
