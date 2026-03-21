"""
ASTPanel — displays the parsed Lark AST as indented text.
"""

import tkinter as tk
import customtkinter as ctk
from gui.constants import COLOURS, FONT_EDITOR, FONT_HEADER


class ASTPanel:
    """Read-only panel that renders a Lark parse tree as indented text."""

    def __init__(self, parent):
        self._frame = ctk.CTkFrame(parent, fg_color=COLOURS["bg_dark"], corner_radius=0)
        ctk.CTkLabel(
            self._frame, text="AST Viewer",
            font=FONT_HEADER, text_color=COLOURS["header_accent"],
        ).pack(fill=tk.X, padx=12, pady=(8, 4))

        self._text = tk.Text(
            self._frame, wrap=tk.WORD, state=tk.DISABLED,
            bg=COLOURS["bg_dark"], fg=COLOURS["fg_text"],
            font=FONT_EDITOR, relief=tk.FLAT,
            highlightthickness=0, padx=8, pady=6,
        )
        self._text.pack(fill=tk.BOTH, expand=True)
        parent.add(self._frame, minsize=80)

    def update(self, lark_tree):
        """Render a Lark parse tree as indented text."""
        self._text.config(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        if lark_tree:
            self._text.insert("1.0", lark_tree.pretty())
        self._text.config(state=tk.DISABLED)

    def clear(self):
        """Clear the AST display."""
        self.update(None)
