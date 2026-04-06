"""Circular countdown ring around the focus panda while a session runs."""

import tkinter as tk

import customtkinter as ctk

from devbuddy.theme import BG, FOCUS_MODULE_ACCENT, INPUT_BORDER


class FocusSessionRing(ctk.CTkFrame):
    """
    Full track arc plus a second arc showing remaining session time (clockwise from 12 o'clock).
    Arcs are redrawn from the canvas's real size so the ring stays centered (HiDPI / CTk sizing).
    Place the panda in ``center_frame``; call ``lift()`` so it stacks above the canvas.
    ``center_rely`` nudges the sprite: sprite art usually sits low in the frame vs. geometric center.
    """

    def __init__(
        self,
        parent,
        diameter: int = 620,
        inset: int = 22,
        line_width: int = 14,
        center_rely: float = 0.535,
    ):
        super().__init__(parent, fg_color=BG, width=diameter, height=diameter)
        self.pack_propagate(False)
        self._inset = inset
        self._lw = line_width
        self._center_rely = center_rely
        self._frac = 1.0
        self._last_wh: tuple[int, int] | None = None

        self._canvas = tk.Canvas(
            self,
            width=diameter,
            height=diameter,
            bg=BG,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        self.center_frame = ctk.CTkFrame(self, fg_color=BG)
        self.center_frame.place(relx=0.5, rely=self._center_rely, anchor="center")
        self.center_frame.lift()

    def _on_canvas_configure(self, event: tk.Event) -> None:
        if event.width < 24 or event.height < 24:
            return
        key = (event.width, event.height)
        if key == self._last_wh:
            return
        self._last_wh = key
        self._redraw_arcs()

    def _arc_bbox(self) -> tuple[float, float, float, float] | None:
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w < 24 or h < 24:
            return None
        side = min(w, h)
        ox = (w - side) / 2.0
        oy = (h - side) / 2.0
        p = float(self._inset)
        return (ox + p, oy + p, ox + side - p, oy + side - p)

    def _redraw_arcs(self) -> None:
        bbox = self._arc_bbox()
        if bbox is None:
            return
        self._canvas.delete("track")
        self._canvas.delete("progress")
        self._canvas.create_arc(
            *bbox,
            start=90,
            extent=-360,
            style=tk.ARC,
            outline=INPUT_BORDER,
            width=self._lw,
            tags="track",
        )
        frac = max(0.0, min(1.0, float(self._frac)))
        if frac > 0:
            self._canvas.create_arc(
                *bbox,
                start=90,
                extent=-360 * frac,
                style=tk.ARC,
                outline=FOCUS_MODULE_ACCENT,
                width=self._lw,
                tags="progress",
            )
            try:
                self._canvas.tag_raise("progress", "track")
            except tk.TclError:
                pass

    def set_remaining_fraction(self, frac: float) -> None:
        """1.0 = all time remaining, 0 = none (ring gap)."""
        self._frac = max(0.0, min(1.0, float(frac)))
        self._redraw_arcs()
