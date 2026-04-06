"""Reusable CustomTkinter-styled controls."""

import customtkinter as ctk

from devbuddy.theme import (
    BTN_SUBTLE,
    BTN_SUBTLE_H,
    INPUT_BG,
    INPUT_BORDER,
    NEON_CYAN,
    NEON_PURPLE,
    TEXT_DIM,
    TEXT_PRIMARY,
)
from devbuddy.utils import lighten


def neon_button(parent, text, command, color=NEON_CYAN, width=120, height=36):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=height,
        fg_color=color,
        hover_color=lighten(color),
        text_color="#000000",
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        corner_radius=8,
    )


def subtle_button(parent, text, command, width=80, height=30):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=height,
        fg_color=BTN_SUBTLE,
        hover_color=BTN_SUBTLE_H,
        text_color=TEXT_PRIMARY,
        font=ctk.CTkFont(family="Segoe UI", size=11),
        corner_radius=6,
        border_width=1,
        border_color=INPUT_BORDER,
    )


def danger_button(parent, text, command, width=30, height=30):
    from devbuddy.theme import NEON_DANGER

    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=height,
        fg_color=BTN_SUBTLE,
        hover_color=NEON_DANGER,
        text_color=TEXT_DIM,
        font=ctk.CTkFont(family="Segoe UI", size=11),
        corner_radius=6,
    )


def styled_entry(parent, placeholder="", width=380):
    return ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        width=width,
        fg_color=INPUT_BG,
        border_color=INPUT_BORDER,
        border_width=1,
        text_color=TEXT_PRIMARY,
        placeholder_text_color=TEXT_DIM,
        font=ctk.CTkFont(family="Segoe UI", size=12),
        corner_radius=6,
    )


def section_label(parent, text):
    return ctk.CTkLabel(
        parent,
        text=text,
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        text_color=NEON_PURPLE,
    )
