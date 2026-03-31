"""
ControlPanel — tree operations, script controls, speed slider (PyQt6 version).
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QSlider, QFrame, QButtonGroup
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import os

_ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons")

def _icon(name: str) -> QIcon:
    return QIcon(os.path.join(_ICONS_DIR, name))

from gui.constants import COLOURS, ANIM_DELAY_MS, MODE_AVL, MODE_RB


def _label(text: str, bold=False) -> QLabel:
    lbl = QLabel(text)
    weight = "bold" if bold else "normal"
    lbl.setStyleSheet(f"""
        color: {COLOURS["fg_text"]};
        font-family: "Inter", sans-serif;
        font-size: 13px;
        font-weight: {weight};
    """)
    return lbl


def _section_header(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        color: {COLOURS["header_accent"]};
        font-family: "Inter", sans-serif;
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


def _btn(text: str, color: str, hover: str, tooltip: str = "", icon_name: str = "", fg_color: str = None) -> QPushButton:
    if fg_color is None:
        fg_color = COLOURS["btn_fg"]
    b = QPushButton(text)
    if icon_name:
        b.setIcon(_icon(icon_name))
    b.setFixedHeight(36)
    b.setStyleSheet(f"""
        QPushButton {{
            background-color: {color};
            color: {fg_color};
            border: none;
            border-radius: 12px;
            padding: 0 14px;
            font-family: "Inter", sans-serif;
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
        on_speed_change, on_mode_change, on_export=None,
    ):
        super().__init__(parent)
        self._on_speed_change = on_speed_change

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(4)

        self._build_mode_toggle(layout, on_mode_change)
        layout.addWidget(_separator())

        self._build_tree_ops(layout, on_insert, on_delete)
        layout.addWidget(_separator())
        self._build_script_controls(layout, on_run_script, on_step_forward, on_step_back)
        layout.addWidget(_separator())
        self._build_management(layout, on_clear, on_reset, on_export)

        layout.addStretch()

    # ── sections ─────────────────────────────────────────────────────────

    def _build_mode_toggle(self, layout: QVBoxLayout, on_mode_change):
        row = QHBoxLayout()
        row.setContentsMargins(12, 4, 12, 4)
        row.setSpacing(0)  # Buttons flush against each other

        # Container frame for the pill-shape
        pill_frame = QFrame()
        pill_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOURS["entry_bg"]};
                border: 1px solid {COLOURS["border"]};
                border-radius: 14px;
            }}
        """)
        pill_layout = QHBoxLayout(pill_frame)
        pill_layout.setContentsMargins(0, 0, 0, 0)
        pill_layout.setSpacing(0)

        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)

        def make_tab(text, is_checked=False):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setChecked(is_checked)
            btn.setFixedHeight(28)
            # We style checkable buttons to look like a segment in a pill
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLOURS["btn_fg"]};
                    border: none;
                    border-radius: 14px;
                    font-family: "Inter", sans-serif;
                    font-size: 13px;
                    font-weight: bold;
                    padding: 0 16px;
                }}
                QPushButton:checked {{
                    background-color: {COLOURS["btn_primary"]};
                    color: {COLOURS["btn_primary_fg"]};
                }}
                QPushButton:hover:!checked {{
                    background-color: {COLOURS["btn_hover"]};
                }}
            """)
            return btn

        self._btn_avl = make_tab(MODE_AVL, True)
        self._btn_rb  = make_tab(MODE_RB, False)

        self._mode_group.addButton(self._btn_avl)
        self._mode_group.addButton(self._btn_rb)

        pill_layout.addWidget(self._btn_avl)
        pill_layout.addWidget(self._btn_rb)

        # Wire up click handlers
        self._btn_avl.toggled.connect(lambda c: on_mode_change(MODE_AVL) if c else None)
        self._btn_rb.toggled.connect(lambda c: on_mode_change(MODE_RB) if c else None)

        row.addWidget(pill_frame)
        row.addStretch()
        layout.addLayout(row)

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
                padding: 4px 12px;
                font-family: "Inter", sans-serif;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLOURS["border"]};
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
            "trash-2-light.svg",
            COLOURS["btn_danger_fg"]
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
            " Run Script", COLOURS["btn_primary"], COLOURS["btn_primary_hover"],
            "Run DSL script on the current tree  (Ctrl+Enter)",
            "play-light.svg",
            COLOURS["btn_primary_fg"]
        )
        run_btn.clicked.connect(on_run)
        row.addWidget(run_btn)

        fwd_btn = _btn(
            "Step", COLOURS["btn_bg"], COLOURS["btn_hover"],
            "Advance one balancing step",
            "step-forward.svg"
        )
        fwd_btn.clicked.connect(on_fwd)
        row.addWidget(fwd_btn)

        back_btn = _btn(
            "Step", COLOURS["btn_neutral"], COLOURS["btn_neutral_hover"],
            "Go back one balancing step",
            "step-back.svg"
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
            "Clear", COLOURS["btn_danger"], COLOURS["btn_danger_hover"],
            "Remove all nodes from the tree",
            "trash-2-light.svg",
            COLOURS["btn_danger_fg"]
        )
        clear_btn.clicked.connect(on_clear)
        row.addWidget(clear_btn)

        reset_btn = _btn(
            "Reset", COLOURS["btn_neutral"], COLOURS["btn_neutral_hover"],
            "Recompute and redraw the tree",
            "rotate-ccw.svg"
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
