"""Lightweight tooltip helper bound to any Tk/CTk widget."""

import tkinter as tk

from gui.constants import FONT_TOOLTIP


class ToolTip:
    """Modern tooltip with rounded styling, bound to a widget."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)
        widget.bind("<FocusIn>", self._show)
        widget.bind("<FocusOut>", self._hide)

    def _show(self, _event=None):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        # Remove window shadow on Windows
        tw.attributes("-transparentcolor", "")

        frame = tk.Frame(
            tw, bg="#21262D", bd=0,
            highlightthickness=1, highlightbackground="#30363D",
        )
        frame.pack()

        label = tk.Label(
            frame, text=self.text, justify=tk.LEFT,
            background="#21262D", foreground="#E6EDF3",
            font=FONT_TOOLTIP, padx=8, pady=5,
        )
        label.pack()

    def _hide(self, _event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
