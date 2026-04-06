"""Add / edit a music playlist entry."""

from tkinter import messagebox

import customtkinter as ctk

from devbuddy.playlists import normalize_playlist_url, playlist_source_from_url
from devbuddy.theme import BG, HEADER_BG, NEON_PURPLE, TEXT_DIM
from devbuddy.widgets import neon_button, styled_entry, subtle_button


class PlaylistDialog(ctk.CTkToplevel):
    def __init__(self, parent, playlist=None):
        super().__init__(parent)
        self.result = None
        self.playlist = playlist or {"name": "", "url": ""}

        self.title("Edit Playlist" if playlist else "Add Playlist")
        self.geometry("520x360")
        self.minsize(480, 340)
        self.resizable(True, True)
        self.configure(fg_color=BG)
        self.grab_set()

        title_bar = ctk.CTkFrame(self, fg_color=HEADER_BG, corner_radius=0, height=52)
        title_bar.pack_propagate(False)
        ctk.CTkLabel(
            title_bar,
            text="Edit Playlist" if playlist else "Add Playlist",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=NEON_PURPLE,
        ).pack(side="left", padx=20, pady=14)

        line = ctk.CTkFrame(self, fg_color=NEON_PURPLE, height=2, corner_radius=0)

        body = ctk.CTkFrame(self, fg_color=BG)

        ctk.CTkLabel(
            body,
            text="Display name",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=NEON_PURPLE,
        ).pack(anchor="w", pady=(0, 6))
        self.name_entry = styled_entry(body, placeholder="e.g. Focus coding", width=460)
        self.name_entry.pack(anchor="w", pady=(0, 16))
        self.name_entry.insert(0, self.playlist.get("name", ""))

        ctk.CTkLabel(
            body,
            text="Playlist URL (Spotify or YouTube)",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=NEON_PURPLE,
        ).pack(anchor="w", pady=(0, 6))
        self.url_entry = styled_entry(
            body,
            placeholder="https://open.spotify.com/playlist/… or https://youtube.com/playlist?list=…",
            width=460,
        )
        self.url_entry.pack(anchor="w", pady=(0, 8))
        self.url_entry.insert(0, self.playlist.get("url", ""))

        ctk.CTkLabel(
            body,
            text="Paste a Spotify or YouTube playlist link. It will open in your browser (or the Spotify app for spotify: links).",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_DIM,
            wraplength=460,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        footer = ctk.CTkFrame(self, fg_color=HEADER_BG, corner_radius=0, height=56)
        footer.pack_propagate(False)
        neon_button(footer, "Save", self._save, color=NEON_PURPLE, width=100).pack(
            side="right", padx=20, pady=12
        )
        subtle_button(footer, "Cancel", self.destroy, width=90, height=34).pack(side="right", pady=12)

        footer.pack(side="bottom", fill="x")
        title_bar.pack(side="top", fill="x")
        line.pack(side="top", fill="x")
        body.pack(fill="both", expand=True, padx=24, pady=20)

        self.name_entry.bind("<Return>", lambda e: self._save())
        self.url_entry.bind("<Return>", lambda e: self._save())

        self.after(100, self.lift)

    def _save(self):
        name = self.name_entry.get().strip()
        url = normalize_playlist_url(self.url_entry.get())
        if not url:
            messagebox.showwarning("Missing URL", "Please enter a playlist URL.", parent=self)
            return
        src = playlist_source_from_url(url)
        if src is None:
            messagebox.showwarning(
                "Unsupported URL",
                "Use a Spotify playlist (open.spotify.com or spotify:…) or a YouTube playlist (youtube.com / youtu.be).",
                parent=self,
            )
            return
        if not name:
            name = "Playlist"
        self.result = {"name": name, "url": url, "source": src}
        self.destroy()
