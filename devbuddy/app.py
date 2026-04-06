"""Main Dev Buddy window: launcher, music, color picker."""

import os
import sys
import time
import webbrowser
import tkinter as tk
from tkinter import colorchooser, messagebox

import customtkinter as ctk

from icon_gen import ICON_PATH

from devbuddy.config import load_config, save_config
from devbuddy.focus_gamify import (
    clamp_minutes,
    clamp_seconds,
    level_from_total_xp,
    normalize_focus_stats,
    rank_title,
    reward_summary_rows,
    streak_after_session,
    xp_bar_values,
    xp_for_session,
)
from devbuddy.focus_panda import PandaFocusAnimation, load_focus_idle_photo
from devbuddy.focus_ring import FocusSessionRing
from devbuddy.focus_xp_hud import FocusXpHud
from devbuddy.dialogs import FocusCompleteDialog, PlaylistDialog, ProjectDialog
from devbuddy.eyedropper import EyedropperOverlay
from devbuddy.launcher_ops import (
    close_cursor_for_repo,
    close_visual_studio_for_sln,
    open_in_cursor,
    open_in_visual_studio,
)
from devbuddy.playlists import (
    MUSIC_SPOTIFY_ACCENT,
    MUSIC_YOUTUBE_ACCENT,
    normalize_playlist_url,
    playlist_source_from_url,
)
from devbuddy.theme import (
    BG,
    CARD_BG,
    CARD_BORDER,
    CARD_CORNER_RADIUS,
    CARD_PAD_BOTTOM,
    CARD_PAD_X,
    CARD_PALETTE,
    COLOR_MODULE_ACCENT,
    HEADER_BG,
    TODO_MODULE_ACCENT,
    FOCUS_MODULE_ACCENT,
    HUD_TEXT_MUTED,
    INPUT_BORDER,
    NAV_ICON_MUTED,
    NEON_CYAN,
    NEON_DANGER,
    NEON_PURPLE,
    SIDEBAR_BG,
    SIDEBAR_HOVER,
    SIDEBAR_WIDTH,
    TEXT_DIM,
    TEXT_PRIMARY,
    BTN_SUBTLE,
)
from devbuddy.utils import hex_to_rgb_tuple, lighten, rgb_tuple_to_hex, virtual_screen_bbox
from devbuddy.widgets import danger_button, neon_button, subtle_button, styled_entry


class DevLauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dev Buddy — Code Launcher")
        self.geometry("1080x840")
        self.minsize(980, 660)
        self.configure(fg_color=BG)
        self._active_module = "launcher"
        self._nav_rail_btn = {}
        self._picker_syncing = False
        self._focus_running = False
        self._focus_end_mono = 0.0
        self._focus_tick_job = None
        self._focus_planned_seconds = 0
        self._set_icon()
        self.config_data = load_config()
        self._build_ui()

    def _set_icon(self):
        self.after(250, self._apply_icon)

    def _apply_icon(self):
        try:
            self.iconbitmap(ICON_PATH)
        except Exception:
            pass

    def _build_ui(self):
        root_row = ctk.CTkFrame(self, fg_color="transparent")
        root_row.pack(fill="both", expand=True)

        sidebar = ctk.CTkFrame(
            root_row, width=SIDEBAR_WIDTH, fg_color=SIDEBAR_BG, corner_radius=0,
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        nav_pad = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_pad.pack(fill="x", padx=8, pady=(16, 12))

        self._nav_rail_btn["launcher"] = self._nav_rail_button(
            nav_pad, key="launcher", label="</>",
            font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
        )
        self._nav_rail_btn["launcher"].pack(pady=(0, 8))

        self._nav_rail_btn["music"] = self._nav_rail_button(
            nav_pad,
            key="music",
            label="\u266a",  # ♪
            font=ctk.CTkFont(family="Segoe UI", size=18),
        )
        self._nav_rail_btn["music"].pack(pady=(0, 8))

        self._nav_rail_btn["todo"] = self._nav_rail_button(
            nav_pad,
            key="todo",
            label="\u2713",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
        )
        self._nav_rail_btn["todo"].pack(pady=(0, 8))

        self._nav_rail_btn["focus"] = self._nav_rail_button(
            nav_pad,
            key="focus",
            label="\u23f1",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
        )
        self._nav_rail_btn["focus"].pack(pady=(0, 8))

        self._nav_rail_btn["color"] = self._nav_rail_button(
            nav_pad,
            key="color",
            label="\u25D0",
            font=ctk.CTkFont(family="Segoe UI", size=16),
        )
        self._nav_rail_btn["color"].pack(pady=0)

        self.content_host = ctk.CTkFrame(root_row, fg_color=BG)
        self.content_host.pack(side="left", fill="both", expand=True)

        self.launcher_frame = ctk.CTkFrame(self.content_host, fg_color=BG)
        self.music_frame = ctk.CTkFrame(self.content_host, fg_color=BG)
        self.todo_frame = ctk.CTkFrame(self.content_host, fg_color=BG)
        self.focus_frame = ctk.CTkFrame(self.content_host, fg_color=BG)
        self.color_frame = ctk.CTkFrame(self.content_host, fg_color=BG)

        self._build_launcher_module(self.launcher_frame)
        self._build_music_module(self.music_frame)
        self._build_todo_module(self.todo_frame)
        self._build_focus_module(self.focus_frame)
        self._build_color_module(self.color_frame)

        self._select_module("launcher")

    def _nav_rail_button(self, parent, key, label, font):
        return ctk.CTkButton(
            parent,
            text=label,
            width=40,
            height=40,
            corner_radius=8,
            fg_color="transparent",
            hover_color=SIDEBAR_HOVER,
            text_color=NAV_ICON_MUTED,
            font=font,
            border_width=0,
            command=lambda: self._select_module(key),
        )

    def _select_module(self, key):
        self._active_module = key

        titles = {
            "launcher": "Dev Buddy — Code Launcher",
            "music": "Dev Buddy — Music",
            "todo": "Dev Buddy — To-do",
            "focus": "Dev Buddy — Focus",
            "color": "Dev Buddy — Color Picker",
        }
        self.title(titles.get(key, "Dev Buddy"))

        for k, btn in self._nav_rail_btn.items():
            if k == key:
                btn.configure(
                    fg_color=NEON_CYAN,
                    hover_color=lighten(NEON_CYAN),
                    text_color="#0a0a12",
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    hover_color=SIDEBAR_HOVER,
                    text_color=NAV_ICON_MUTED,
                )

        self.launcher_frame.pack_forget()
        self.music_frame.pack_forget()
        self.todo_frame.pack_forget()
        self.focus_frame.pack_forget()
        self.color_frame.pack_forget()
        if key == "launcher":
            self.launcher_frame.pack(fill="both", expand=True)
        elif key == "music":
            self.music_frame.pack(fill="both", expand=True)
        elif key == "todo":
            self.todo_frame.pack(fill="both", expand=True)
        elif key == "focus":
            self.focus_frame.pack(fill="both", expand=True)
        else:
            self.color_frame.pack(fill="both", expand=True)

    def _build_launcher_module(self, parent):
        header = ctk.CTkFrame(parent, fg_color=HEADER_BG, corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="CODE LAUNCHER",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=NEON_CYAN,
        ).pack(side="left", padx=20, pady=18)

        neon_button(header, "+ New Project", self._new_project,
                    color=NEON_PURPLE, width=130, height=34).pack(side="right", padx=20, pady=15)

        ctk.CTkFrame(parent, fg_color=NEON_CYAN, height=2, corner_radius=0).pack(fill="x")

        self.project_list = ctk.CTkScrollableFrame(
            parent, fg_color=BG,
            scrollbar_button_color=BTN_SUBTLE,
            scrollbar_button_hover_color=INPUT_BORDER,
            label_text="",
        )
        self.project_list.pack(fill="both", expand=True, padx=16, pady=16)

        self._render_projects()

    def _build_music_module(self, parent):
        header = ctk.CTkFrame(parent, fg_color=HEADER_BG, corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="MUSIC",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=NEON_PURPLE,
        ).pack(side="left", padx=20, pady=18)

        neon_button(
            header,
            "+ Add playlist",
            self._add_playlist_dialog,
            color=NEON_PURPLE,
            width=130,
            height=34,
        ).pack(side="right", padx=20, pady=15)

        ctk.CTkFrame(parent, fg_color=NEON_PURPLE, height=2, corner_radius=0).pack(fill="x")

        self.music_list = ctk.CTkScrollableFrame(
            parent,
            fg_color=BG,
            scrollbar_button_color=BTN_SUBTLE,
            scrollbar_button_hover_color=INPUT_BORDER,
            label_text="",
        )
        self.music_list.pack(fill="both", expand=True, padx=16, pady=16)

        self._render_music_playlists()

    def _build_todo_module(self, parent):
        header = ctk.CTkFrame(parent, fg_color=HEADER_BG, corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="TO-DO",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=TODO_MODULE_ACCENT,
        ).pack(side="left", padx=20, pady=18)

        danger_button(
            header,
            "Clear all",
            self._clear_all_todos,
            width=100,
            height=34,
        ).pack(side="right", padx=20, pady=15)

        ctk.CTkFrame(parent, fg_color=TODO_MODULE_ACCENT, height=2, corner_radius=0).pack(fill="x")

        self.todo_list = ctk.CTkScrollableFrame(
            parent,
            fg_color=BG,
            scrollbar_button_color=BTN_SUBTLE,
            scrollbar_button_hover_color=INPUT_BORDER,
            label_text="",
        )
        self.todo_list.pack(fill="both", expand=True, padx=16, pady=(16, 8))

        bottom = ctk.CTkFrame(parent, fg_color=BG)
        bottom.pack(fill="x", padx=16, pady=(0, 16))

        self._todo_entry = styled_entry(bottom, placeholder="Add a task…", width=380)
        self._todo_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        neon_button(
            bottom,
            "Add",
            self._add_todo_from_entry,
            color=TODO_MODULE_ACCENT,
            width=88,
            height=34,
        ).pack(side="left")
        self._todo_entry.bind("<Return>", lambda e: self._add_todo_from_entry())

        self._render_todo_items()

    def _build_focus_module(self, parent):
        header = ctk.CTkFrame(parent, fg_color=HEADER_BG, corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="FOCUS",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=FOCUS_MODULE_ACCENT,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkFrame(parent, fg_color=FOCUS_MODULE_ACCENT, height=2, corner_radius=0).pack(fill="x")

        body = ctk.CTkFrame(parent, fg_color=BG)
        body.pack(fill="both", expand=True, padx=20, pady=16)
        scroll = ctk.CTkScrollableFrame(
            body,
            fg_color=BG,
            scrollbar_button_color=BTN_SUBTLE,
            scrollbar_button_hover_color=INPUT_BORDER,
        )
        scroll.pack(fill="both", expand=True)

        center_col = ctk.CTkFrame(scroll, fg_color=BG)
        center_col.pack(fill="x")
        center_col.grid_columnconfigure(0, weight=1)

        self._focus_stats_block = ctk.CTkFrame(center_col, fg_color=BG)
        self._focus_stats_block.grid(row=0, column=0, padx=16, pady=(0, 12), sticky="ew")
        self._focus_stats_block.grid_columnconfigure(0, weight=1)
        self._focus_xp_hud = FocusXpHud(self._focus_stats_block)
        self._focus_xp_hud.grid(row=0, column=0, sticky="ew")
        self._focus_stats_label = ctk.CTkLabel(
            self._focus_stats_block,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=HUD_TEXT_MUTED,
            justify="center",
            anchor="center",
            wraplength=960,
        )
        self._focus_stats_label.grid(row=1, column=0, pady=(10, 0), sticky="ew")
        self._refresh_focus_stats_display()

        # Animated sprite sheet: fixed size (square-ish cells on sheet)
        _fp_w, _fp_h = 480, 540
        # Idle still is landscape — wider than the 480px sprite panel; same height for layout rhythm
        _idle_w, _idle_h = 980, 556
        self._focus_session_ring = FocusSessionRing(
            center_col,
            diameter=640,
            inset=24,
            line_width=16,
            center_rely=0.54,
        )
        self._focus_anim = PandaFocusAnimation(
            self._focus_session_ring.center_frame,
            width=_fp_w,
            height=_fp_h,
        )
        self._focus_anim.pack()

        self._focus_idle_photo = load_focus_idle_photo(self.winfo_toplevel(), _idle_w, _idle_h)
        self._focus_idle_wrap = None
        if self._focus_idle_photo is not None:
            self._focus_idle_wrap = ctk.CTkFrame(center_col, fg_color=BG)
            idle_lbl = tk.Label(
                self._focus_idle_wrap,
                image=self._focus_idle_photo,
                bg=BG,
                bd=0,
                highlightthickness=0,
            )
            idle_lbl.pack()

        self._focus_timer_label = ctk.CTkLabel(
            center_col,
            text="--:--",
            font=ctk.CTkFont(family="Segoe UI", size=56, weight="bold"),
            text_color=TEXT_PRIMARY,
            anchor="center",
        )

        self._focus_ctrl_holder = ctk.CTkFrame(center_col, fg_color="transparent")
        self._focus_ctrl_holder.grid_columnconfigure(0, weight=1)
        self._focus_ctrl_holder.grid_columnconfigure(2, weight=1)
        ctrl_inner = ctk.CTkFrame(self._focus_ctrl_holder, fg_color="transparent")
        ctrl_inner.grid(row=0, column=1)

        ctk.CTkLabel(
            ctrl_inner,
            text="Min",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=FOCUS_MODULE_ACCENT,
        ).pack(side="left", padx=(0, 6))

        self._focus_minutes_entry = styled_entry(ctrl_inner, placeholder="25", width=56)
        self._focus_minutes_entry.pack(side="left", padx=(0, 10))
        self._focus_minutes_entry.insert(0, "25")

        ctk.CTkLabel(
            ctrl_inner,
            text="Sec",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=FOCUS_MODULE_ACCENT,
        ).pack(side="left", padx=(0, 6))

        self._focus_seconds_entry = styled_entry(ctrl_inner, placeholder="0", width=52)
        self._focus_seconds_entry.pack(side="left", padx=(0, 12))
        self._focus_seconds_entry.insert(0, "0")

        self._focus_start_btn = neon_button(
            ctrl_inner,
            "Start",
            self._focus_start,
            color=FOCUS_MODULE_ACCENT,
            width=96,
            height=34,
        )
        self._focus_start_btn.pack(side="left", padx=(0, 8))

        self._focus_stop_btn = subtle_button(
            ctrl_inner,
            "Stop",
            self._focus_stop,
            width=80,
            height=34,
        )
        self._focus_stop_btn.pack(side="left")
        self._focus_stop_btn.configure(state="disabled")

        self._focus_hint_label = ctk.CTkLabel(
            center_col,
            text="Stay on task until the timer ends to earn XP and keep your streak.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_DIM,
            wraplength=960,
            justify="center",
            anchor="center",
        )

        self._focus_relayout_idle()

    def _focus_relayout_idle(self):
        """Hide session ring; show idle art if present; stack timer → controls → hint."""
        try:
            self._focus_session_ring.grid_remove()
        except tk.TclError:
            pass
        if self._focus_idle_wrap is not None:
            self._focus_idle_wrap.grid(row=1, column=0, padx=0, pady=(0, 8))
            t_row, c_row, h_row = 2, 3, 4
        else:
            t_row, c_row, h_row = 1, 2, 3
        self._focus_timer_label.grid(row=t_row, column=0, padx=16, pady=(4, 14))
        self._focus_ctrl_holder.grid(row=c_row, column=0, pady=(0, 12))
        self._focus_hint_label.grid(row=h_row, column=0, padx=20, pady=(0, 8))

    def _focus_relayout_running(self):
        """Hide idle still; show ring + animated panda between stats and timer."""
        if self._focus_idle_wrap is not None:
            self._focus_idle_wrap.grid_remove()
        self._focus_session_ring.grid(row=1, column=0, padx=0, pady=(0, 8))
        self._focus_session_ring.center_frame.lift()
        self._focus_timer_label.grid(row=2, column=0, padx=16, pady=(4, 12))
        self._focus_ctrl_holder.grid(row=3, column=0, pady=(0, 12))
        self._focus_hint_label.grid(row=4, column=0, padx=20, pady=(0, 8))

    def _refresh_focus_stats_display(self):
        fs = normalize_focus_stats(self.config_data.get("focus_stats", {}))
        self.config_data["focus_stats"] = fs
        lv = level_from_total_xp(fs["total_xp"])
        into, cap, fill = xp_bar_values(fs["total_xp"])
        self._focus_xp_hud.set_state(lv, rank_title(lv), into, cap, fill)
        self._focus_stats_label.configure(
            text=(
                f"Total XP: {fs['total_xp']}    ·    Sessions: {fs['sessions_completed']}"
                f"\nFocus time: {fs['total_focus_minutes']} min    ·    Streak: {fs['streak_days']} day(s)"
            )
        )

    def _focus_start(self):
        if self._focus_running:
            return
        m = clamp_minutes(self._focus_minutes_entry.get())
        s = clamp_seconds(self._focus_seconds_entry.get())
        total = m * 60 + s
        if total <= 0:
            messagebox.showwarning(
                "Focus",
                "Set a duration of at least 1 second (minutes and seconds, max 240:59).",
                parent=self,
            )
            return
        self._focus_planned_seconds = total
        self._focus_running = True
        self._focus_end_mono = time.monotonic() + float(total)
        self._focus_minutes_entry.configure(state="disabled")
        self._focus_seconds_entry.configure(state="disabled")
        self._focus_start_btn.configure(state="disabled")
        self._focus_stop_btn.configure(state="normal")
        self._focus_relayout_running()
        self.update_idletasks()
        self._focus_session_ring.set_remaining_fraction(1.0)
        self._focus_anim.start()
        self._focus_tick()

    def _focus_tick(self):
        if not self._focus_running:
            return
        remain = self._focus_end_mono - time.monotonic()
        if remain <= 0:
            self._focus_complete()
            return
        total_s = int(remain + 0.999)
        mm = total_s // 60
        ss = total_s % 60
        self._focus_timer_label.configure(text=f"{mm:02d}:{ss:02d}")
        planned = max(1, self._focus_planned_seconds)
        self._focus_session_ring.set_remaining_fraction(max(0.0, remain / float(planned)))
        self._focus_tick_job = self.after(250, self._focus_tick)

    def _focus_complete(self):
        if self._focus_tick_job is not None:
            try:
                self.after_cancel(self._focus_tick_job)
            except Exception:
                pass
            self._focus_tick_job = None

        self._focus_running = False
        self._focus_anim.stop()
        self._focus_relayout_idle()
        self._focus_stop_btn.configure(state="disabled")
        self._focus_timer_label.configure(text="--:--")

        planned = self._focus_planned_seconds
        minutes = max(1, (planned + 59) // 60)
        fs = normalize_focus_stats(self.config_data.get("focus_stats", {}))
        old_lv = level_from_total_xp(fs["total_xp"])
        new_streak, last_d = streak_after_session(fs)
        xp = xp_for_session(minutes, new_streak)
        fs["total_xp"] = fs["total_xp"] + xp
        fs["total_focus_minutes"] = fs["total_focus_minutes"] + minutes
        fs["sessions_completed"] = fs["sessions_completed"] + 1
        fs["streak_days"] = new_streak
        fs["last_focus_date"] = last_d
        new_lv = level_from_total_xp(fs["total_xp"])
        self.config_data["focus_stats"] = fs
        save_config(self.config_data)
        self._refresh_focus_stats_display()

        rows = reward_summary_rows(
            minutes,
            xp,
            fs["total_xp"],
            new_streak,
            old_lv,
            new_lv,
        )

        def _unlock_focus_after_summary():
            self._focus_minutes_entry.configure(state="normal")
            self._focus_seconds_entry.configure(state="normal")
            self._focus_start_btn.configure(state="normal")

        FocusCompleteDialog(self, rows, on_dismiss=_unlock_focus_after_summary)

    def _focus_stop(self):
        if not self._focus_running:
            return
        if self._focus_tick_job is not None:
            try:
                self.after_cancel(self._focus_tick_job)
            except Exception:
                pass
            self._focus_tick_job = None
        self._focus_running = False
        self._focus_anim.stop()
        self._focus_relayout_idle()
        self._focus_minutes_entry.configure(state="normal")
        self._focus_seconds_entry.configure(state="normal")
        self._focus_start_btn.configure(state="normal")
        self._focus_stop_btn.configure(state="disabled")
        self._focus_timer_label.configure(text="--:--")

    def _build_color_module(self, parent):
        header = ctk.CTkFrame(parent, fg_color=HEADER_BG, corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="COLOR PICKER",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLOR_MODULE_ACCENT,
        ).pack(side="left", padx=20, pady=18)

        hdr_btns = ctk.CTkFrame(header, fg_color="transparent")
        hdr_btns.pack(side="right", padx=20, pady=15)
        subtle_button(
            hdr_btns,
            "Eyedropper",
            self._picker_start_eyedropper,
            width=110,
            height=34,
        ).pack(side="left", padx=(0, 8))
        subtle_button(
            hdr_btns,
            "System picker…",
            self._picker_open_native,
            width=120,
            height=34,
        ).pack(side="left")

        ctk.CTkFrame(parent, fg_color=COLOR_MODULE_ACCENT, height=2, corner_radius=0).pack(
            fill="x"
        )

        body = ctk.CTkFrame(parent, fg_color=BG)
        body.pack(fill="both", expand=True, padx=20, pady=16)

        start = hex_to_rgb_tuple(NEON_CYAN) or (0, 212, 255)
        self._picker_rgb = list(start)

        self._picker_preview = ctk.CTkFrame(
            body,
            fg_color=rgb_tuple_to_hex(self._picker_rgb),
            corner_radius=12,
            border_width=2,
            border_color=CARD_BORDER,
            height=140,
        )
        self._picker_preview.pack(fill="x", pady=(0, 20))
        self._picker_preview.pack_propagate(False)

        ctk.CTkLabel(
            body,
            text=(
                "Adjust RGB or hex, or use Eyedropper: Dev Buddy minimizes briefly, then click a pixel on "
                "the frozen screen snapshot (Windows uses the exact cursor position). "
                "System picker opens the OS color dialog. Copy hex when ready."
            ),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_DIM,
            wraplength=480,
            justify="left",
        ).pack(anchor="w", pady=(0, 16))

        def row_slider(label, channel_idx, color):
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(
                row,
                text=label,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=color,
                width=24,
            ).pack(side="left", padx=(0, 8))
            sl = ctk.CTkSlider(
                row,
                from_=0,
                to=255,
                number_of_steps=255,
                fg_color=INPUT_BORDER,
                progress_color=color,
                button_color=color,
                button_hover_color=lighten(color),
                command=lambda _v: self._picker_on_slider_moved(),
            )
            sl.pack(side="left", fill="x", expand=True, padx=(0, 12))
            lbl = ctk.CTkLabel(
                row,
                text=str(self._picker_rgb[channel_idx]),
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=TEXT_PRIMARY,
                width=36,
            )
            lbl.pack(side="right")
            return sl, lbl

        self._picker_slider_r, self._picker_lbl_r = row_slider("R", 0, NEON_DANGER)
        self._picker_slider_g, self._picker_lbl_g = row_slider("G", 1, "#00cc66")
        self._picker_slider_b, self._picker_lbl_b = row_slider("B", 2, NEON_CYAN)

        self._picker_syncing = True
        self._picker_slider_r.set(self._picker_rgb[0])
        self._picker_slider_g.set(self._picker_rgb[1])
        self._picker_slider_b.set(self._picker_rgb[2])
        self._picker_syncing = False

        hex_row = ctk.CTkFrame(body, fg_color="transparent")
        hex_row.pack(fill="x", pady=(8, 0))

        ctk.CTkLabel(
            hex_row,
            text="Hex",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_MODULE_ACCENT,
        ).pack(side="left", padx=(0, 10))

        self._picker_hex = styled_entry(hex_row, placeholder="#00d4ff", width=200)
        self._picker_hex.pack(side="left", padx=(0, 12))
        self._picker_hex.insert(0, rgb_tuple_to_hex(self._picker_rgb))
        self._picker_hex.bind("<Return>", self._picker_on_hex_commit)
        self._picker_hex.bind("<FocusOut>", self._picker_on_hex_commit)

        neon_button(
            hex_row,
            "Copy hex",
            self._picker_copy_hex,
            color=COLOR_MODULE_ACCENT,
            width=110,
            height=34,
        ).pack(side="left")

    def _picker_on_slider_moved(self, _=None):
        if self._picker_syncing:
            return
        self._picker_rgb = [
            int(round(self._picker_slider_r.get())),
            int(round(self._picker_slider_g.get())),
            int(round(self._picker_slider_b.get())),
        ]
        h = rgb_tuple_to_hex(self._picker_rgb)
        self._picker_preview.configure(fg_color=h)
        self._picker_lbl_r.configure(text=str(self._picker_rgb[0]))
        self._picker_lbl_g.configure(text=str(self._picker_rgb[1]))
        self._picker_lbl_b.configure(text=str(self._picker_rgb[2]))
        self._picker_syncing = True
        self._picker_hex.delete(0, "end")
        self._picker_hex.insert(0, h)
        self._picker_syncing = False

    def _picker_on_hex_commit(self, event=None):
        if self._picker_syncing:
            return
        raw = self._picker_hex.get().strip()
        if raw.startswith("#"):
            test = raw
        else:
            test = "#" + raw
        t = hex_to_rgb_tuple(test)
        if t is None:
            messagebox.showwarning(
                "Invalid color",
                "Use #RRGGBB (six hex digits), e.g. #00d4ff.",
                parent=self,
            )
            self._picker_syncing = True
            self._picker_hex.delete(0, "end")
            self._picker_hex.insert(0, rgb_tuple_to_hex(self._picker_rgb))
            self._picker_syncing = False
            return
        self._picker_rgb = list(t)
        h = rgb_tuple_to_hex(self._picker_rgb)
        self._picker_preview.configure(fg_color=h)
        self._picker_syncing = True
        self._picker_slider_r.set(self._picker_rgb[0])
        self._picker_slider_g.set(self._picker_rgb[1])
        self._picker_slider_b.set(self._picker_rgb[2])
        self._picker_lbl_r.configure(text=str(self._picker_rgb[0]))
        self._picker_lbl_g.configure(text=str(self._picker_rgb[1]))
        self._picker_lbl_b.configure(text=str(self._picker_rgb[2]))
        self._picker_hex.delete(0, "end")
        self._picker_hex.insert(0, h)
        self._picker_syncing = False

    def _picker_copy_hex(self):
        raw = self._picker_hex.get().strip()
        if not raw.startswith("#"):
            raw = "#" + raw
        t = hex_to_rgb_tuple(raw)
        if t is None:
            messagebox.showwarning("Invalid color", "Fix the hex value before copying.", parent=self)
            return
        self.clipboard_clear()
        self.clipboard_append(raw if raw.startswith("#") else "#" + raw)
        self.update()

    def _picker_apply_rgb_tuple(self, rgb_tuple, hex_str=None):
        self._picker_rgb = [int(max(0, min(255, round(x)))) for x in rgb_tuple]
        h = hex_str or rgb_tuple_to_hex(self._picker_rgb)
        if isinstance(h, str):
            h = h.lower()
        self._picker_preview.configure(fg_color=h)
        self._picker_syncing = True
        self._picker_slider_r.set(self._picker_rgb[0])
        self._picker_slider_g.set(self._picker_rgb[1])
        self._picker_slider_b.set(self._picker_rgb[2])
        self._picker_lbl_r.configure(text=str(self._picker_rgb[0]))
        self._picker_lbl_g.configure(text=str(self._picker_rgb[1]))
        self._picker_lbl_b.configure(text=str(self._picker_rgb[2]))
        self._picker_hex.delete(0, "end")
        self._picker_hex.insert(0, h)
        self._picker_syncing = False

    def _picker_start_eyedropper(self):
        try:
            from PIL import ImageGrab
        except ImportError:
            messagebox.showinfo(
                "Eyedropper",
                "Install Pillow to use the eyedropper:\npip install Pillow",
            )
            return

        def finish_eyedropper(rgb):
            try:
                self.deiconify()
            except Exception:
                pass
            self.lift()
            self.focus_force()
            if rgb is None:
                return
            self._picker_apply_rgb_tuple(rgb)

        def grab_and_show():
            try:
                if sys.platform == "win32":
                    l, t, w, h = virtual_screen_bbox()
                    if w > 0:
                        pil_img = ImageGrab.grab(bbox=(l, t, l + w, t + h))
                        ox, oy = l, t
                    else:
                        pil_img = ImageGrab.grab(all_screens=True)
                        ox, oy = 0, 0
                else:
                    pil_img = ImageGrab.grab(all_screens=True)
                    ox, oy = 0, 0
            except Exception as e:
                try:
                    self.deiconify()
                except Exception:
                    pass
                messagebox.showerror("Eyedropper", str(e), parent=self)
                return

            EyedropperOverlay(self, pil_img, (ox, oy), finish_eyedropper)

        # Minimize Dev Buddy so the capture is not dominated by this window; short delay for WM.
        self.iconify()
        self.after(400, grab_and_show)

    def _picker_open_native(self):
        res = colorchooser.askcolor(
            color=rgb_tuple_to_hex(self._picker_rgb),
            parent=self,
            title="Choose color",
        )
        if not res or not res[0]:
            return
        h = res[1] or rgb_tuple_to_hex([int(round(x)) for x in res[0]])
        self._picker_apply_rgb_tuple(res[0], h)

    def _render_music_playlists(self):
        for widget in self.music_list.winfo_children():
            widget.destroy()

        playlists = self.config_data.get("music_playlists", [])
        if not playlists:
            ctk.CTkLabel(
                self.music_list,
                text="No playlists yet.\nClick  + Add playlist  and paste a Spotify or YouTube playlist URL.",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=TEXT_DIM,
                justify="center",
            ).pack(pady=60)
            return

        for i, pl in enumerate(playlists):
            self._render_playlist_card(i, pl)

    def _render_playlist_card(self, index, pl):
        src = pl.get("source") or playlist_source_from_url(pl.get("url", ""))
        accent = MUSIC_SPOTIFY_ACCENT if src == "spotify" else MUSIC_YOUTUBE_ACCENT
        badge = "Spotify" if src == "spotify" else "YouTube"

        card = ctk.CTkFrame(
            self.music_list,
            fg_color=CARD_BG,
            corner_radius=CARD_CORNER_RADIUS,
            border_width=1,
            border_color=CARD_BORDER,
        )
        card.pack(fill="x", pady=6, padx=2)

        ctk.CTkFrame(card, fg_color=accent, height=3, corner_radius=0).pack(fill="x")

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=CARD_PAD_X, pady=(8, 4))

        ctk.CTkLabel(
            top,
            text=badge,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=accent,
            width=56,
            anchor="w",
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            top,
            text=pl.get("name") or "Playlist",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        danger_button(
            top, "✕", lambda i=index: self._delete_music_playlist(i), width=28, height=28
        ).pack(side="right", padx=(4, 0))
        subtle_button(
            top, "Edit", lambda i=index: self._edit_music_playlist(i), width=54, height=28
        ).pack(side="right", padx=(0, 4))
        neon_button(
            top,
            "▶  Open",
            lambda u=pl.get("url", ""): self._open_playlist_url(u),
            color=accent,
            width=100,
            height=30,
        ).pack(side="right", padx=(0, 8))

        url_disp = pl.get("url", "")
        if len(url_disp) > 72:
            url_disp = url_disp[:69] + "…"
        ctk.CTkLabel(
            card,
            text=url_disp,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_DIM,
            anchor="w",
        ).pack(anchor="w", padx=CARD_PAD_X, pady=(0, 10))

    def _open_playlist_url(self, url):
        url = normalize_playlist_url(url)
        if not url:
            messagebox.showwarning("Missing URL", "No URL saved for this playlist.")
            return
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Could not open", str(e))

    def _add_playlist_dialog(self):
        dialog = PlaylistDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self.config_data.setdefault("music_playlists", []).append(dialog.result)
            save_config(self.config_data)
            self._render_music_playlists()

    def _edit_music_playlist(self, index):
        playlists = self.config_data.get("music_playlists", [])
        if index < 0 or index >= len(playlists):
            return
        cur = dict(playlists[index])
        dialog = PlaylistDialog(self, playlist=cur)
        self.wait_window(dialog)
        if dialog.result:
            playlists[index] = dialog.result
            save_config(self.config_data)
            self._render_music_playlists()

    def _delete_music_playlist(self, index):
        playlists = self.config_data.get("music_playlists", [])
        if index < 0 or index >= len(playlists):
            return
        name = playlists[index].get("name", "Playlist")
        if messagebox.askyesno("Remove playlist", f"Remove '{name}' from the list?"):
            playlists.pop(index)
            save_config(self.config_data)
            self._render_music_playlists()

    def _render_todo_items(self):
        for widget in self.todo_list.winfo_children():
            widget.destroy()

        items = self.config_data.get("todo_items", [])
        if not items:
            ctk.CTkLabel(
                self.todo_list,
                text="No tasks yet.\nType below and press Add or Enter.",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=TEXT_DIM,
                justify="center",
            ).pack(pady=40)
            return

        for i, it in enumerate(items):
            self._render_todo_row(i, it)

    def _render_todo_row(self, index, it):
        row = ctk.CTkFrame(
            self.todo_list,
            fg_color=CARD_BG,
            corner_radius=8,
            border_width=1,
            border_color=CARD_BORDER,
        )
        row.pack(fill="x", pady=4)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=8, pady=6)

        done = bool(it.get("done"))
        var = ctk.BooleanVar(value=done)

        def make_toggle(i, v):
            def _toggle():
                lst = self.config_data.get("todo_items", [])
                if 0 <= i < len(lst):
                    lst[i]["done"] = v.get()
                    save_config(self.config_data)
                    self._render_todo_items()

            return _toggle

        ctk.CTkCheckBox(
            inner,
            text="",
            width=24,
            variable=var,
            command=make_toggle(index, var),
            fg_color=TODO_MODULE_ACCENT,
            hover_color=lighten(TODO_MODULE_ACCENT),
        ).pack(side="left", padx=(0, 8))

        txt = it.get("text") or ""
        strike = bool(it.get("done"))
        ctk.CTkLabel(
            inner,
            text=txt if len(txt) <= 200 else txt[:197] + "…",
            font=ctk.CTkFont(family="Segoe UI", size=13, overstrike=strike),
            text_color=TEXT_DIM if strike else TEXT_PRIMARY,
            anchor="w",
            wraplength=420,
            justify="left",
        ).pack(side="left", fill="x", expand=True)

        danger_button(
            inner,
            "✕",
            lambda i=index: self._delete_todo_item(i),
            width=28,
            height=28,
        ).pack(side="right")

    def _add_todo_from_entry(self):
        text = self._todo_entry.get().strip()
        if not text:
            return
        self.config_data.setdefault("todo_items", []).append({"text": text, "done": False})
        self._todo_entry.delete(0, "end")
        save_config(self.config_data)
        self._render_todo_items()

    def _delete_todo_item(self, index):
        items = self.config_data.get("todo_items", [])
        if index < 0 or index >= len(items):
            return
        items.pop(index)
        save_config(self.config_data)
        self._render_todo_items()

    def _clear_all_todos(self):
        items = self.config_data.get("todo_items", [])
        if not items:
            return
        if messagebox.askyesno(
            "Clear all tasks",
            "Remove every item from your to-do list?\n\nThis cannot be undone.",
        ):
            self.config_data["todo_items"] = []
            save_config(self.config_data)
            self._render_todo_items()

    def _render_projects(self):
        for widget in self.project_list.winfo_children():
            widget.destroy()

        projects = self.config_data.get("projects", [])
        if not projects:
            ctk.CTkLabel(
                self.project_list,
                text="No projects yet.\nClick  + New Project  to get started.",
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=TEXT_DIM, justify="center",
            ).pack(pady=60)
            return

        for i, project in enumerate(projects):
            self._render_card(i, project)

    def _move_project(self, index, delta):
        projects = self.config_data.get("projects", [])
        j = index + delta
        if j < 0 or j >= len(projects):
            return
        projects[index], projects[j] = projects[j], projects[index]
        save_config(self.config_data)
        self._render_projects()

    def _render_card(self, index, project):
        color = project.get("accent")
        if color not in CARD_PALETTE:
            color = CARD_PALETTE[index % len(CARD_PALETTE)]

        card = ctk.CTkFrame(
            self.project_list,
            fg_color=CARD_BG, corner_radius=CARD_CORNER_RADIUS,
            border_width=1, border_color=CARD_BORDER,
        )
        card.pack(fill="x", pady=6, padx=2)

        n = len(self.config_data.get("projects", []))

        # Neon top edge
        ctk.CTkFrame(card, fg_color=color, height=3, corner_radius=0).pack(fill="x")

        # Header row
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=CARD_PAD_X, pady=(8, 4))

        ctk.CTkLabel(
            top, text=project["name"],
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        danger_button(top, "✕", lambda i=index: self._delete_project(i), width=28, height=28).pack(side="right", padx=(4, 0))
        subtle_button(top, "Edit", lambda i=index: self._edit_project(i), width=54, height=28).pack(side="right", padx=(0, 4))

        move_row = ctk.CTkFrame(top, fg_color="transparent")
        btn_up = subtle_button(
            move_row, "\u2191", lambda i=index: self._move_project(i, -1), width=28, height=28,
        )
        btn_down = subtle_button(
            move_row, "\u2193", lambda i=index: self._move_project(i, 1), width=28, height=28,
        )
        btn_up.pack(side="left")
        btn_down.pack(side="left", padx=(4, 0))
        move_row.pack(side="right", padx=(0, 8))
        if index == 0:
            btn_up.configure(state="disabled")
        if index >= n - 1:
            btn_down.configure(state="disabled")

        # Clickable resource pills
        repos = project.get("repos", [])
        sln = project.get("sln", "")

        has_resources = repos or (sln and sln.get("path"))
        if has_resources:
            pills_frame = ctk.CTkFrame(card, fg_color="transparent")
            pills_frame.pack(fill="x", padx=CARD_PAD_X, pady=(0, 6))

            for repo in repos:
                display = repo.get("name") or os.path.basename(repo["path"].rstrip("/\\"))
                self._make_pill(pills_frame, "⬡  " + display, color,
                                lambda p=repo["path"]: open_in_cursor(p))

            if sln and sln.get("path"):
                sln_label = sln.get("name") or os.path.basename(sln["path"])
                self._make_pill(pills_frame, "◈  " + sln_label, NEON_PURPLE,
                                lambda s=sln["path"]: open_in_visual_studio(s))
        else:
            ctk.CTkLabel(
                card, text="No resources configured",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=TEXT_DIM,
            ).pack(anchor="w", padx=CARD_PAD_X, pady=(0, 6))

        # Separator
        ctk.CTkFrame(card, fg_color=CARD_BORDER, height=1).pack(fill="x", padx=CARD_PAD_X, pady=0)

        # Action buttons row
        btn_row = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0)
        btn_row.pack(fill="x", padx=CARD_PAD_X, pady=(0, CARD_PAD_BOTTOM))

        ctk.CTkButton(
            btn_row,
            text="▶  Launch All",
            height=28,
            fg_color="#0d1a2e",
            hover_color="#0a2040",
            text_color=color,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            corner_radius=0,
            border_width=0,
            command=lambda p=project: self._launch_all(p),
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkFrame(btn_row, fg_color=CARD_BORDER, width=1, height=1).pack(side="left", fill="y")

        ctk.CTkButton(
            btn_row,
            text="■  Close All",
            height=28,
            fg_color="#1a0d0d",
            hover_color="#2a0a0a",
            text_color=NEON_DANGER,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            corner_radius=0,
            border_width=0,
            command=lambda p=project: self._close_all(p),
        ).pack(side="left", fill="x", expand=True)

    def _make_pill(self, parent, text, color, command):
        """A clickable pill badge that opens a single resource."""
        btn = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            fg_color="#0d0d1e",
            hover_color=CARD_BORDER,
            text_color=color,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=6,
            border_width=1,
            border_color=color,
            height=26,
            anchor="w",
        )
        btn.pack(side="left", padx=(0, 6), pady=2)

    def _launch_all(self, project):
        repos = project.get("repos", [])
        sln = project.get("sln", "")

        if not repos and not (sln and sln.get("path")):
            messagebox.showinfo("No Resources", f"'{project['name']}' has no repos or solution configured.")
            return

        missing = [r["path"] for r in repos if not os.path.isdir(r["path"])]
        if missing:
            msg = "These repo paths don't exist:\n\n" + "\n".join(missing)
            if not messagebox.askyesno("Missing Paths", msg + "\n\nOpen the rest anyway?"):
                return

        for repo in repos:
            if os.path.isdir(repo["path"]):
                open_in_cursor(repo["path"])

        if sln and sln.get("path"):
            open_in_visual_studio(sln["path"])

    def _close_all(self, project):
        repos = project.get("repos", [])
        sln   = project.get("sln", {})

        if not repos and not (sln and sln.get("path")):
            messagebox.showinfo("No Resources", f"'{project['name']}' has no resources configured.")
            return

        total = 0
        for repo in repos:
            total += close_cursor_for_repo(repo["path"])
        if sln and sln.get("path"):
            total += close_visual_studio_for_sln(sln["path"])

        if total == 0:
            messagebox.showinfo(
                "Nothing Closed",
                f"No running processes found for '{project['name']}'.\n\n"
                "They may already be closed, or couldn't be matched.",
            )

    def _new_project(self):
        dialog = ProjectDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            n = len(self.config_data["projects"])
            dialog.result["accent"] = CARD_PALETTE[n % len(CARD_PALETTE)]
            self.config_data["projects"].append(dialog.result)
            save_config(self.config_data)
            self._render_projects()

    def _edit_project(self, index):
        project = self.config_data["projects"][index]
        prev_accent = project.get("accent")
        dialog = ProjectDialog(self, project=dict(project))
        self.wait_window(dialog)
        if dialog.result:
            self.config_data["projects"][index] = dialog.result
            if prev_accent in CARD_PALETTE:
                self.config_data["projects"][index]["accent"] = prev_accent
            save_config(self.config_data)
            self._render_projects()

    def _delete_project(self, index):
        name = self.config_data["projects"][index]["name"]
        if messagebox.askyesno("Delete Project", f"Delete '{name}'?"):
            self.config_data["projects"].pop(index)
            save_config(self.config_data)
            self._render_projects()

