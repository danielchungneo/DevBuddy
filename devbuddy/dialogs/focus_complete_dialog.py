"""Modal summary after a focus session completes."""

import customtkinter as ctk

from devbuddy.theme import (
    BG,
    BTN_SUBTLE,
    FOCUS_MODULE_ACCENT,
    HEADER_BG,
    INPUT_BORDER,
    TEXT_DIM,
    TEXT_PRIMARY,
)
from devbuddy.widgets import neon_button


class FocusCompleteDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        rows: list[tuple[str, str]],
        on_dismiss,
    ):
        super().__init__(parent)
        self._on_dismiss = on_dismiss

        self.title("Focus complete")
        self.geometry("460x420")
        self.minsize(400, 340)
        self.resizable(True, True)
        self.configure(fg_color=BG)
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._dismiss)
        self.bind("<Escape>", lambda e: self._dismiss())

        title_bar = ctk.CTkFrame(self, fg_color=HEADER_BG, corner_radius=0, height=52)
        title_bar.pack_propagate(False)
        ctk.CTkLabel(
            title_bar,
            text="Focus complete",
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            text_color=FOCUS_MODULE_ACCENT,
        ).pack(side="left", padx=20, pady=14)

        ctk.CTkFrame(self, fg_color=FOCUS_MODULE_ACCENT, height=2, corner_radius=0).pack(fill="x")

        body = ctk.CTkScrollableFrame(
            self,
            fg_color=BG,
            scrollbar_button_color=BTN_SUBTLE,
            scrollbar_button_hover_color=INPUT_BORDER,
        )
        body.pack(fill="both", expand=True, padx=24, pady=(20, 16))

        for kind, text in rows:
            font, color, pady = self._style_for(kind)
            ctk.CTkLabel(
                body,
                text=text,
                font=font,
                text_color=color,
                anchor="w",
                justify="left",
                wraplength=380,
            ).pack(fill="x", pady=pady)

        footer = ctk.CTkFrame(self, fg_color=HEADER_BG, corner_radius=0, height=64)
        footer.pack_propagate(False)
        footer.pack(side="bottom", fill="x")
        neon_button(
            footer,
            "Continue",
            self._dismiss,
            color=FOCUS_MODULE_ACCENT,
            width=140,
            height=36,
        ).pack(side="right", padx=20, pady=14)

        self.after(100, self.lift)

    def _style_for(self, kind: str) -> tuple[ctk.CTkFont, str, tuple[int, int]]:
        if kind == "title":
            return (
                ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
                TEXT_PRIMARY,
                (0, 10),
            )
        if kind == "xp":
            return (
                ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
                FOCUS_MODULE_ACCENT,
                (4, 14),
            )
        if kind == "levelup":
            return (
                ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                FOCUS_MODULE_ACCENT,
                (8, 6),
            )
        if kind in ("meta", "level"):
            return (
                ctk.CTkFont(family="Segoe UI", size=13),
                TEXT_DIM,
                (2, 4),
            )
        if kind == "total":
            return (
                ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                TEXT_PRIMARY,
                (12, 4),
            )
        return (
            ctk.CTkFont(family="Segoe UI", size=13),
            TEXT_PRIMARY,
            (2, 4),
        )

    def _dismiss(self):
        cb = self._on_dismiss
        self._on_dismiss = None
        self.grab_release()
        self.destroy()
        if cb is not None:
            cb()
