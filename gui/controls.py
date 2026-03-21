"""
ControlPanel — buttons, slider, status bar.
Migrated to CustomTkinter widgets for modern styling.
"""

import tkinter as tk
import customtkinter as ctk

from gui.constants import (COLOURS, ANIM_DELAY_MS, CARD_CORNER_RADIUS,
                          SECTION_PAD_X, SECTION_PAD_Y,
                          FONT_HEADER, FONT_BODY, FONT_BUTTON, FONT_BUTTON_BOLD,
                          FONT_MONO, FONT_EDITOR)
from gui.tooltip import ToolTip


class ControlPanel:
    """Control panel with tree operations, script controls, and status bar."""

    def __init__(self, parent, *, on_insert, on_delete, on_run_script,
                 on_step_forward, on_step_back, on_clear, on_reset,
                 on_speed_change, on_export=None):
        """
        Build the control panel and add it to *parent* (a PanedWindow).

        All button actions are provided as callback parameters so the
        panel stays decoupled from the application logic.
        """
        self._parent = parent
        self._on_speed_change = on_speed_change

        outer = ctk.CTkFrame(parent, fg_color=COLOURS["bg_surface"], corner_radius=0)

        self._build_tree_ops(outer, on_insert, on_delete)
        self._add_separator(outer)
        self._build_script_controls(outer, on_run_script, on_step_forward, on_step_back)
        self._add_separator(outer)
        self._build_tree_management(outer, on_clear, on_reset, on_export)
        self._build_status_bar(outer)

        parent.add(outer, minsize=120)

    # ---- Separator ----

    def _add_separator(self, parent):
        """Add a thin horizontal divider between sections."""
        sep = ctk.CTkFrame(
            parent, fg_color=COLOURS["separator"],
            height=1, corner_radius=0,
        )
        sep.pack(fill=tk.X, padx=20, pady=8)

    # ---- Section Header ----

    def _section_header(self, parent, text):
        """Create a styled section header with accent colour."""
        header = ctk.CTkLabel(
            parent, text=text,
            font=FONT_HEADER,
            text_color=COLOURS["header_accent"],
        )
        header.pack(fill=tk.X, padx=SECTION_PAD_X, pady=(SECTION_PAD_Y + 4, 6))

    # ---- Tree Operations ----

    def _build_tree_ops(self, outer, on_insert, on_delete):
        self._section_header(outer, "🌳  Tree Operations")

        tree_ops = ctk.CTkFrame(
            outer, fg_color=COLOURS["bg_card"],
            corner_radius=CARD_CORNER_RADIUS,
        )
        tree_ops.pack(fill=tk.X, padx=SECTION_PAD_X, pady=(0, 6))

        insert_row = ctk.CTkFrame(tree_ops, fg_color=COLOURS["bg_card"])
        insert_row.pack(fill=tk.X, padx=SECTION_PAD_X, pady=SECTION_PAD_Y)

        ctk.CTkLabel(
            insert_row, text="Value:",
            text_color=COLOURS["fg_text"], font=FONT_BODY,
        ).pack(side=tk.LEFT, padx=(0, 4))

        self.insert_entry = ctk.CTkEntry(
            insert_row, width=80,
            fg_color=COLOURS["entry_bg"], text_color=COLOURS["entry_fg"],
            font=FONT_EDITOR,
            border_color=COLOURS["border"],
            border_width=1,
            corner_radius=8,
            placeholder_text="e.g. 42",
            placeholder_text_color=COLOURS["fg_gutter"],
        )
        self.insert_entry.pack(side=tk.LEFT, padx=(0, 6))
        ToolTip(self.insert_entry, "Enter an integer value to insert")

        self.insert_btn = ctk.CTkButton(
            insert_row, text="Insert Node", command=on_insert,
            fg_color=COLOURS["btn_bg"], hover_color=COLOURS["btn_hover"],
            text_color=COLOURS["btn_fg"], font=FONT_BUTTON,
            corner_radius=8, height=42,
        )
        self.insert_btn.pack(side=tk.LEFT, padx=(0, 6))
        ToolTip(self.insert_btn, "Insert the value into the tree")

        self.delete_btn = ctk.CTkButton(
            insert_row, text="Delete Node", command=on_delete,
            fg_color=COLOURS["btn_danger"], hover_color=COLOURS["btn_danger_hover"],
            text_color=COLOURS["btn_fg"], font=FONT_BUTTON,
            corner_radius=8, height=42,
        )
        self.delete_btn.pack(side=tk.LEFT)
        ToolTip(self.delete_btn, "Delete the value from the tree")

    # ---- Script Controls ----

    def _build_script_controls(self, outer, on_run_script, on_step_forward, on_step_back):
        self._section_header(outer, "⚡  Script Controls")

        script_ops = ctk.CTkFrame(
            outer, fg_color=COLOURS["bg_card"],
            corner_radius=CARD_CORNER_RADIUS,
        )
        script_ops.pack(fill=tk.X, padx=SECTION_PAD_X, pady=(0, 6))

        script_row = ctk.CTkFrame(script_ops, fg_color=COLOURS["bg_card"])
        script_row.pack(fill=tk.X, padx=SECTION_PAD_X, pady=SECTION_PAD_Y)

        self.run_btn = ctk.CTkButton(
            script_row, text="▶ Run Script", command=on_run_script,
            fg_color=COLOURS["btn_primary"], hover_color=COLOURS["btn_primary_hover"],
            text_color=COLOURS["btn_fg"], font=FONT_BUTTON_BOLD,
            corner_radius=8, height=42,
        )
        self.run_btn.pack(side=tk.LEFT, padx=(0, 6))
        ToolTip(self.run_btn, "Run the DSL script on the current tree  (Ctrl+Enter)")

        self.step_fwd_btn = ctk.CTkButton(
            script_row, text="Step ▶▶", command=on_step_forward,
            fg_color=COLOURS["btn_bg"], hover_color=COLOURS["btn_hover"],
            text_color=COLOURS["btn_fg"], font=FONT_BUTTON,
            corner_radius=8, height=42,
        )
        self.step_fwd_btn.pack(side=tk.LEFT, padx=(0, 6))
        ToolTip(self.step_fwd_btn, "Advance one balancing step")

        self.step_back_btn = ctk.CTkButton(
            script_row, text="◀◀ Step", command=on_step_back,
            fg_color=COLOURS["btn_neutral"], hover_color=COLOURS["btn_neutral_hover"],
            text_color=COLOURS["btn_fg"], font=FONT_BUTTON,
            corner_radius=8, height=42,
        )
        self.step_back_btn.pack(side=tk.LEFT)
        ToolTip(self.step_back_btn, "Go back one balancing step")

        # Speed slider row
        speed_row = ctk.CTkFrame(script_ops, fg_color=COLOURS["bg_card"])
        speed_row.pack(fill=tk.X, padx=SECTION_PAD_X, pady=(0, SECTION_PAD_Y))

        ctk.CTkLabel(
            speed_row, text="Animation Delay (ms):",
            text_color=COLOURS["fg_text"], font=("Segoe UI", 11),
        ).pack(side=tk.LEFT, padx=(0, 4))

        self.speed_slider = ctk.CTkSlider(
            speed_row, from_=1, to=150,
            fg_color=COLOURS["border"],
            progress_color=COLOURS["btn_bg"],
            button_color=COLOURS["focus_ring"],
            button_hover_color=COLOURS["btn_hover"],
            command=self._on_speed_slider,
        )
        self.speed_slider.set(ANIM_DELAY_MS)
        self.speed_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

    # ---- Tree Management ----

    def _build_tree_management(self, outer, on_clear, on_reset, on_export):
        self._section_header(outer, "🔧  Tree Management")

        mgmt_ops = ctk.CTkFrame(
            outer, fg_color=COLOURS["bg_card"],
            corner_radius=CARD_CORNER_RADIUS,
        )
        mgmt_ops.pack(fill=tk.X, padx=SECTION_PAD_X, pady=(0, SECTION_PAD_Y))

        mgmt_row = ctk.CTkFrame(mgmt_ops, fg_color=COLOURS["bg_card"])
        mgmt_row.pack(fill=tk.X, padx=SECTION_PAD_X, pady=SECTION_PAD_Y)

        self.clear_btn = ctk.CTkButton(
            mgmt_row, text="Clear Tree", command=on_clear,
            fg_color=COLOURS["btn_danger"], hover_color=COLOURS["btn_danger_hover"],
            text_color=COLOURS["btn_fg"], font=FONT_BUTTON,
            corner_radius=8, height=42,
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 6))
        ToolTip(self.clear_btn, "Remove all nodes from the tree")

        self.reset_btn = ctk.CTkButton(
            mgmt_row, text="Reset View", command=on_reset,
            fg_color=COLOURS["btn_neutral"], hover_color=COLOURS["btn_neutral_hover"],
            text_color=COLOURS["btn_fg"], font=FONT_BUTTON,
            corner_radius=8, height=34,
        )
        self.reset_btn.pack(side=tk.LEFT)
        ToolTip(self.reset_btn, "Reset canvas zoom and position")

        if on_export:
            self.export_btn = ctk.CTkButton(
                mgmt_row, text="Export CSV", command=on_export,
                fg_color=COLOURS["btn_neutral"], hover_color=COLOURS["btn_neutral_hover"],
                text_color=COLOURS["btn_fg"], font=FONT_BUTTON,
                corner_radius=8, height=42,
            )
            self.export_btn.pack(side=tk.LEFT, padx=(6, 0))
            ToolTip(self.export_btn, "Export tree data to CSV")

    # ---- Status Bar ----

    def _build_status_bar(self, outer):
        # Status bar with accent stripe
        status_frame = ctk.CTkFrame(outer, fg_color=COLOURS["status_bg"], corner_radius=0)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Top border for separation
        border_line = ctk.CTkFrame(
            status_frame, fg_color=COLOURS["separator"],
            height=1, corner_radius=0,
        )
        border_line.pack(fill=tk.X)

        # Left accent stripe
        accent = ctk.CTkFrame(
            status_frame, fg_color=COLOURS["btn_primary"],
            width=4, corner_radius=0,
        )
        accent.pack(side=tk.LEFT, fill=tk.Y)

        self._status_var = tk.StringVar(value="Ready")
        self.status_bar = ctk.CTkLabel(
            status_frame, textvariable=self._status_var, anchor=tk.W,
            fg_color="transparent", text_color=COLOURS["status_fg"],
            font=FONT_BODY, corner_radius=0,
        )
        self.status_bar.pack(fill=tk.X, padx=(10, 6), pady=4)

    # ---- public helpers ----

    def set_status(self, message: str):
        """Update the status bar text."""
        self._status_var.set(message)

    def get_insert_value(self) -> str:
        """Return the current insert entry text, stripped."""
        return self.insert_entry.get().strip()

    def clear_insert_entry(self):
        """Clear the insert entry field."""
        self.insert_entry.delete(0, tk.END)

    # ---- internal ----

    def _on_speed_slider(self, val):
        """Forward slider changes to the app callback."""
        self._on_speed_change(int(float(val)))
