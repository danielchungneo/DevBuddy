"""Gaming-style XP HUD: hex level (overlaps bar) + slanted XP bar + rank / XP row."""

from __future__ import annotations

import math
import tkinter as tk

import customtkinter as ctk

from devbuddy.theme import BG, HUD_TEXT_MUTED, NEON_CYAN, TEXT_PRIMARY

_BAR_FILL = "#00d4ff"
_HEX_FILL = "#0a1220"
_HEX_OUTLINE = "#8b93a8"
_BAR_TRACK = "#15151f"
_BAR_EDGE = "#2a2a38"

_BADGE_W = 100
_BADGE_H = 108
_HEX_CX = _BADGE_W / 2
_HEX_CY = _BADGE_H / 2 + 2
_HEX_R = 30
_BAR_H = 22
# Horizontal inset so the bar starts under the overlapping badge
_BAR_LEFT_PAD = 46
_OVERLAP_ROW_H = 56


class FocusXpHud(ctk.CTkFrame):
    """Large hex level badge overlapping the left of the XP bar; rank + XP below."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._bar_fill = 0.0
        self._last_bar_wh: tuple[int, int] | None = None

        self.grid_columnconfigure(0, weight=1)

        stack = ctk.CTkFrame(self, fg_color="transparent")
        stack.grid(row=0, column=0, sticky="ew")

        overlap = ctk.CTkFrame(stack, fg_color="transparent", height=_OVERLAP_ROW_H)
        overlap.pack(fill="x", pady=(0, 6))
        overlap.pack_propagate(False)

        self._bar_canvas = tk.Canvas(
            overlap,
            height=_BAR_H,
            bg=BG,
            highlightthickness=0,
            bd=0,
        )
        self._bar_canvas.pack(fill="x", padx=(_BAR_LEFT_PAD, 0), pady=(17, 17))
        self._bar_canvas.bind("<Configure>", self._on_bar_configure)

        self._badge_host = ctk.CTkFrame(overlap, fg_color="transparent", width=_BADGE_W, height=_BADGE_H)
        self._badge_host.place(x=4, y=2, anchor="nw")
        self._badge_host.lift()

        self._badge_canvas = tk.Canvas(
            self._badge_host,
            width=_BADGE_W,
            height=_BADGE_H,
            bg=BG,
            highlightthickness=0,
            bd=0,
        )
        self._badge_canvas.pack()
        self._hex_points = self._flat_top_hex_points(_HEX_CX, _HEX_CY, _HEX_R)
        self._draw_hex_static()
        self._level_text_ids: list[int] = []

        bot = ctk.CTkFrame(stack, fg_color="transparent")
        bot.pack(fill="x")
        self._rank_lbl = ctk.CTkLabel(
            bot,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        self._rank_lbl.pack(side="left", padx=(_BAR_LEFT_PAD - 8, 0))
        self._next_lbl = ctk.CTkLabel(
            bot,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=HUD_TEXT_MUTED,
            anchor="e",
        )
        self._next_lbl.pack(side="right")

        self.after_idle(self._badge_host.lift)

    @staticmethod
    def _flat_top_hex_points(cx: float, cy: float, R: float) -> list[float]:
        cos30 = math.cos(math.radians(30))
        sin30 = math.sin(math.radians(30))
        hw = R * cos30
        v = R * sin30
        return [
            cx - hw,
            cy - v,
            cx + hw,
            cy - v,
            cx + R,
            cy,
            cx + hw,
            cy + v,
            cx - hw,
            cy + v,
            cx - R,
            cy,
        ]

    def _draw_hex_static(self) -> None:
        c = self._badge_canvas
        c.create_polygon(*self._hex_points, fill=_HEX_FILL, outline=_HEX_OUTLINE, width=2, smooth=False)

    def _set_level_number(self, level: int) -> None:
        c = self._badge_canvas
        for tid in self._level_text_ids:
            try:
                c.delete(tid)
            except tk.TclError:
                pass
        self._level_text_ids.clear()
        t = str(level)
        font = ("Segoe UI", 32, "bold")
        s = c.create_text(
            _HEX_CX + 1,
            _HEX_CY + 1,
            text=t,
            fill="#000814",
            font=font,
            anchor="center",
        )
        self._level_text_ids.append(s)
        top = c.create_text(
            _HEX_CX,
            _HEX_CY,
            text=t,
            fill=NEON_CYAN,
            font=font,
            anchor="center",
        )
        self._level_text_ids.append(top)

    def _on_bar_configure(self, event: tk.Event) -> None:
        if event.width < 40 or event.height < 10:
            return
        key = (event.width, event.height)
        if key == self._last_bar_wh and self._bar_canvas.find_withtag("track"):
            return
        self._last_bar_wh = key
        self._redraw_bar()

    def _redraw_bar(self) -> None:
        c = self._bar_canvas
        c.delete("track", "fill")
        w = max(40, c.winfo_width())
        h = max(12, c.winfo_height())
        skew = min(10, max(5, h // 2 + 1))
        track = [skew, 0, w, 0, w - skew, h, 0, h]
        c.create_polygon(*track, fill=_BAR_TRACK, outline=_BAR_EDGE, width=1, tags="track")

        p = max(0.0, min(1.0, self._bar_fill))
        if p <= 0:
            return

        L = w - skew
        x2 = skew + p * L
        x3 = p * (w - skew)
        # Sub-pixel seam between fill and track: extend fill 1px when not full (no white edge line).
        if p < 1.0:
            x2 = min(w - 0.5, x2 + 1.0)
            x3 = min(w - skew - 0.5, x3 + 1.0)

        c.create_polygon(
            skew,
            0,
            x2,
            0,
            x3,
            h,
            0,
            h,
            fill=_BAR_FILL,
            outline="",
            tags="fill",
        )

    def set_state(self, level: int, rank_name: str, xp_into: int, xp_cap: int, fill: float) -> None:
        self._set_level_number(level)
        self._rank_lbl.configure(text=rank_name.upper())
        self._next_lbl.configure(text=f"{xp_into} / {xp_cap} XP")
        self._bar_fill = max(0.0, min(1.0, float(fill)))
        self._last_bar_wh = None
        self._redraw_bar()
