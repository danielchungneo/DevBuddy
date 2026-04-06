"""Create / edit a Code Launcher project."""

from tkinter import filedialog, messagebox

import customtkinter as ctk

from devbuddy.theme import (
    BG,
    CARD_BG,
    CARD_BORDER,
    HEADER_BG,
    NEON_CYAN,
    NEON_PURPLE,
    TEXT_DIM,
    BTN_SUBTLE,
)
from devbuddy.widgets import (
    danger_button,
    neon_button,
    section_label,
    styled_entry,
    subtle_button,
)


class ProjectDialog(ctk.CTkToplevel):
    def __init__(self, parent, project=None):
        super().__init__(parent)
        self.result = None
        self.project = project or {"name": "", "repos": [], "sln": {"name": "", "path": ""}}

        self.title("Edit Project" if project else "New Project")
        self.geometry("620x640")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.grab_set()

        self._build_ui()
        self.after(100, self.lift)

    def _build_ui(self):
        title_bar = ctk.CTkFrame(self, fg_color=HEADER_BG, corner_radius=0, height=56)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        title_text = "Edit Project" if self.project["name"] else "New Project"
        ctk.CTkLabel(
            title_bar,
            text=title_text,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=NEON_CYAN,
        ).pack(side="left", padx=20, pady=16)

        ctk.CTkFrame(self, fg_color=NEON_PURPLE, height=2, corner_radius=0).pack(fill="x")

        body = ctk.CTkScrollableFrame(self, fg_color=BG, scrollbar_button_color=BTN_SUBTLE)
        body.pack(fill="both", expand=True)

        inner = ctk.CTkFrame(body, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        section_label(inner, "PROJECT NAME").pack(anchor="w", pady=(0, 6))
        self.name_entry = styled_entry(inner, placeholder="e.g. Safeguard", width=570)
        self.name_entry.pack(anchor="w", pady=(0, 20))
        self.name_entry.insert(0, self.project["name"])

        section_label(inner, "CURSOR REPOS").pack(anchor="w", pady=(0, 4))

        col_headers = ctk.CTkFrame(inner, fg_color="transparent")
        col_headers.pack(fill="x", padx=2, pady=(0, 4))
        ctk.CTkLabel(
            col_headers,
            text="Display Name  (optional)",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_DIM,
        ).pack(side="left", padx=(10, 0))
        ctk.CTkLabel(
            col_headers,
            text="Folder Path",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_DIM,
        ).pack(side="left", padx=(148, 0))

        self.repo_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self.repo_frame.pack(fill="x", pady=(0, 8))

        self.repo_rows = []
        for repo in self.project.get("repos", []):
            self._add_repo_row(repo)

        neon_button(inner, "+ Add Repo", self._add_repo_row, color=NEON_PURPLE, width=130, height=32).pack(
            anchor="w", pady=(0, 20)
        )

        ctk.CTkFrame(inner, fg_color=CARD_BORDER, height=1).pack(fill="x", pady=(0, 16))

        section_label(inner, "VISUAL STUDIO SOLUTION  ·  optional").pack(anchor="w", pady=(0, 4))

        sln_col_headers = ctk.CTkFrame(inner, fg_color="transparent")
        sln_col_headers.pack(fill="x", padx=2, pady=(0, 4))
        ctk.CTkLabel(
            sln_col_headers,
            text="Display Name  (optional)",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_DIM,
        ).pack(side="left", padx=(10, 0))
        ctk.CTkLabel(
            sln_col_headers,
            text=".sln File Path",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_DIM,
        ).pack(side="left", padx=(148, 0))

        sln_row = ctk.CTkFrame(
            inner,
            fg_color=CARD_BG,
            corner_radius=8,
            border_width=1,
            border_color=CARD_BORDER,
        )
        sln_row.pack(fill="x", pady=(0, 20))

        sln = self.project.get("sln", {"name": "", "path": ""})

        self.sln_name_entry = styled_entry(sln_row, placeholder="Name", width=140)
        self.sln_name_entry.pack(side="left", padx=(10, 6), pady=8)
        self.sln_name_entry.insert(0, sln.get("name", "") if isinstance(sln, dict) else "")

        self.sln_path_entry = styled_entry(sln_row, placeholder="Path to .sln file", width=260)
        self.sln_path_entry.pack(side="left", padx=(0, 6), pady=8)
        self.sln_path_entry.insert(0, sln.get("path", "") if isinstance(sln, dict) else sln)

        subtle_button(sln_row, "Browse", self._browse_sln, width=65, height=28).pack(side="left", padx=(0, 6))
        danger_button(sln_row, "✕", self._clear_sln, width=28, height=28).pack(side="left", padx=(0, 8))

        ctk.CTkFrame(self, fg_color=CARD_BORDER, height=1, corner_radius=0).pack(fill="x")
        footer = ctk.CTkFrame(self, fg_color=HEADER_BG, corner_radius=0, height=60)
        footer.pack(fill="x")
        footer.pack_propagate(False)

        neon_button(footer, "Save", self._save, color=NEON_CYAN, width=110).pack(side="right", padx=20, pady=12)
        subtle_button(footer, "Cancel", self.destroy, width=90, height=36).pack(side="right", pady=12)

    def _add_repo_row(self, repo=None):
        if repo is None:
            repo = {"name": "", "path": ""}

        row = ctk.CTkFrame(
            self.repo_frame,
            fg_color=CARD_BG,
            corner_radius=8,
            border_width=1,
            border_color=CARD_BORDER,
        )
        row.pack(fill="x", pady=4)

        name_entry = styled_entry(row, placeholder="Name", width=140)
        name_entry.pack(side="left", padx=(10, 6), pady=8)
        name_entry.insert(0, repo.get("name", ""))

        path_entry = styled_entry(row, placeholder="Repo folder path", width=260)
        path_entry.pack(side="left", padx=(0, 6), pady=8)
        path_entry.insert(0, repo.get("path", ""))

        subtle_button(row, "Browse", lambda e=path_entry: self._browse_folder(e), width=65, height=28).pack(
            side="left", padx=(0, 6)
        )
        danger_button(row, "✕", lambda r=row: self._remove_row(r), width=28, height=28).pack(
            side="left", padx=(0, 8)
        )

        self.repo_rows.append((row, name_entry, path_entry))

    def _browse_folder(self, entry):
        path = filedialog.askdirectory(title="Select Repo Folder")
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)

    def _browse_sln(self):
        path = filedialog.askopenfilename(
            title="Select Solution File",
            filetypes=[("Solution files", "*.sln"), ("All files", "*.*")],
        )
        if path:
            self.sln_path_entry.delete(0, "end")
            self.sln_path_entry.insert(0, path)

    def _clear_sln(self):
        self.sln_name_entry.delete(0, "end")
        self.sln_path_entry.delete(0, "end")

    def _remove_row(self, row_frame):
        self.repo_rows = [(r, n, p) for r, n, p in self.repo_rows if r != row_frame]
        row_frame.destroy()

    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing Name", "Please enter a project name.", parent=self)
            return
        repos = [
            {"name": n.get().strip(), "path": p.get().strip()}
            for _, n, p in self.repo_rows
            if p.get().strip()
        ]
        sln_path = self.sln_path_entry.get().strip()
        sln = (
            {"name": self.sln_name_entry.get().strip(), "path": sln_path}
            if sln_path
            else {"name": "", "path": ""}
        )
        self.result = {"name": name, "repos": repos, "sln": sln}
        self.destroy()
