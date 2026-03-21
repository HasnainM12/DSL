"""
EditorPanel — code editor zone with line-number gutter.
Uses tk.Text for the editor (CTk has no equivalent with tag support).
"""

import tkinter as tk
import customtkinter as ctk

from gui.constants import COLOURS, FONT_HEADER, FONT_EDITOR, FONT_GUTTER


class EditorPanel:
    """Code editor with a synced line-number gutter and title header."""

    def __init__(self, parent):
        """Build the editor zone and add it to *parent* (a PanedWindow)."""
        self._parent = parent
        self._frame = ctk.CTkFrame(parent, fg_color=COLOURS["bg_dark"], corner_radius=0)

        # Validation callback — set externally by the app
        self._on_validate_callback = None
        self._validate_timer = None  # after() id for debouncing

        self._build_header()
        self._build_body()
        self._insert_placeholder()

        parent.add(self._frame, minsize=150, height=420)

    # ---- construction helpers ----

    def _build_header(self):
        """Title bar with label and accent underline."""
        header_frame = ctk.CTkFrame(self._frame, fg_color=COLOURS["bg_dark"], corner_radius=0)
        header_frame.pack(fill=tk.X)

        ctk.CTkLabel(
            header_frame, text="DSL Script Editor",
            font=FONT_HEADER,
            text_color=COLOURS["header_accent"],
        ).pack(side=tk.LEFT, padx=12, pady=(8, 2))

        # Accent underline
        accent_line = ctk.CTkFrame(
            self._frame, fg_color=COLOURS["header_accent"],
            height=2, corner_radius=0,
        )
        accent_line.pack(fill=tk.X, padx=10, pady=(0, 4))

    def _build_body(self):
        """Build gutter, scrollbar, and editor within a body frame."""
        body = ctk.CTkFrame(self._frame, fg_color=COLOURS["bg_dark"], corner_radius=0)
        body.pack(fill=tk.BOTH, expand=True)

        self._build_gutter(body)
        self._build_gutter_separator(body)
        self._build_scrollbar(body)
        self._build_editor(body)

    def _build_gutter(self, parent):
        self.gutter = tk.Text(
            parent, width=4, padx=4, pady=6,
            bg=COLOURS["bg_gutter"], fg=COLOURS["fg_gutter"],
            font=FONT_GUTTER, relief=tk.FLAT,
            state=tk.DISABLED, takefocus=0,
            borderwidth=0, highlightthickness=0,
            cursor="arrow",
        )
        self.gutter.pack(side=tk.LEFT, fill=tk.Y)

    def _build_gutter_separator(self, parent):
        """Thin vertical line between gutter and editor."""
        sep = ctk.CTkFrame(
            parent, fg_color=COLOURS["separator"],
            width=1, corner_radius=0,
        )
        sep.pack(side=tk.LEFT, fill=tk.Y)

    def _build_scrollbar(self, parent):
        self._scrollbar = ctk.CTkScrollbar(
            parent, orientation="vertical",
            fg_color=COLOURS["bg_dark"],
            button_color=COLOURS["border"],
            button_hover_color=COLOURS["fg_gutter"],
        )
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_editor(self, parent):
        self.editor = tk.Text(
            parent, wrap=tk.NONE, undo=True,
            bg=COLOURS["bg_dark"], fg=COLOURS["fg_text"],
            insertbackground=COLOURS["focus_ring"],
            selectbackground=COLOURS["focus_ring"],
            selectforeground="#FFFFFF",
            font=FONT_EDITOR, padx=8, pady=6,
            relief=tk.FLAT, borderwidth=0,
            highlightthickness=2,
            highlightcolor=COLOURS["focus_ring"],
            highlightbackground=COLOURS["bg_dark"],
            yscrollcommand=self._sync_scroll,
            tabs="4c",
        )
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scrollbar.configure(command=self._on_scrollbar)

        # Sync line numbers on every change
        self.editor.bind("<<Modified>>", self._on_editor_modified)
        self.editor.bind("<KeyRelease>", self._on_key_release)
        self.editor.bind("<MouseWheel>", lambda _: self.editor.after(10, self.update_gutter))

    def _insert_placeholder(self):
        placeholder = (
            "# AVL balancing rules (order matters)\n"
            "IF balance_factor > 1 AND left_child_balance < 0 THEN ROTATE_LEFT_RIGHT\n"
            "IF balance_factor < -1 AND right_child_balance > 0 THEN ROTATE_RIGHT_LEFT\n"
            "IF balance_factor > 1 THEN ROTATE_RIGHT\n"
            "IF balance_factor < -1 THEN ROTATE_LEFT\n"
        )
        self.editor.insert("1.0", placeholder)
        self.update_gutter()

    # ---- public helpers ----

    def get_script(self) -> str:
        """Return the editor content as a stripped string."""
        return self.editor.get("1.0", tk.END).strip()

    def clear(self):
        """Clear all editor text and refresh the gutter."""
        self.editor.delete("1.0", tk.END)
        self.update_gutter()

    def update_gutter(self):
        """Redraw line numbers to match the editor's current line count."""
        self.gutter.config(state=tk.NORMAL)
        self.gutter.delete("1.0", tk.END)
        line_count = int(self.editor.index("end-1c").split(".")[0])
        numbers = "\n".join(str(i) for i in range(1, line_count + 1))
        self.gutter.insert("1.0", numbers)
        self.gutter.config(state=tk.DISABLED)
        # Align gutter scroll position with editor
        self.gutter.yview_moveto(self.editor.yview()[0])

    # ---- scroll synchronisation ----

    def _sync_scroll(self, *args):
        """Called when the editor text scrolls — keep scrollbar + gutter in sync."""
        self._scrollbar.set(*args)
        self.gutter.yview_moveto(args[0])

    def _on_scrollbar(self, *args):
        """Called when the user drags the scrollbar."""
        self.editor.yview(*args)
        self.gutter.yview(*args)

    def _on_editor_modified(self, _event=None):
        if self.editor.edit_modified():
            self.update_gutter()
            self.editor.edit_modified(False)

    def _on_key_release(self, _event=None):
        """Update gutter and schedule debounced validation."""
        self.update_gutter()
        # Cancel any pending validation timer
        if self._validate_timer is not None:
            self.editor.after_cancel(self._validate_timer)
        # Schedule validation 500ms from now
        self._validate_timer = self.editor.after(500, self._run_validation)

    def _run_validation(self):
        """Call the external validation callback if set."""
        self._validate_timer = None
        if self._on_validate_callback:
            script = self.get_script()
            self._on_validate_callback(script)

    # ---- error display ----

    def set_error(self, line: int, col: int, message: str):
        """Highlight an error at the given line/col with red background."""
        self.clear_error()
        start_idx = f"{line}.0"
        end_idx = f"{line}.end"
        self.editor.tag_add("error", start_idx, end_idx)
        self.editor.tag_config(
            "error",
            background="#8B0000",
            foreground="white",
            underline=True,
        )

    def clear_error(self):
        """Remove all error highlighting."""
        self.editor.tag_remove("error", "1.0", tk.END)
