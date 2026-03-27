import json
import os
import subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox
from icon_gen import generate_icon, ICON_PATH
import psutil

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

BG           = "#0a0a12"
CARD_BG      = "#111120"
CARD_BORDER  = "#1e1e3a"
HEADER_BG    = "#0d0d1a"
NEON_CYAN    = "#00d4ff"
NEON_PURPLE  = "#7b2fff"
NEON_DANGER  = "#ff3366"

CARD_PALETTE = [
    "#00d4ff",  # electric cyan
    "#00ff88",  # neon mint
    "#ff3cac",  # neon pink
    "#f7c948",  # neon amber
    "#a259ff",  # neon violet
    "#ff6b35",  # neon orange
]
TEXT_PRIMARY  = "#e8e8ff"
TEXT_DIM      = "#4a4a6a"
INPUT_BG     = "#0d0d1a"
INPUT_BORDER = "#2a2a4a"
BTN_SUBTLE   = "#1a1a2e"
BTN_SUBTLE_H = "#22223a"


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def normalize_repo(repo):
    """Ensure repo is always a {name, path} dict (handles legacy string format)."""
    if isinstance(repo, str):
        return {"name": "", "path": repo}
    return repo


def normalize_sln(sln):
    """Ensure sln is always a {name, path} dict (handles legacy string format)."""
    if isinstance(sln, str):
        return {"name": "", "path": sln}
    return sln


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"projects": []}
    with open(CONFIG_PATH, "r") as f:
        data = json.load(f)
    for project in data.get("projects", []):
        project["repos"] = [normalize_repo(r) for r in project.get("repos", [])]
        if "sln" in project:
            project["sln"] = normalize_sln(project["sln"])
    return data


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


# ---------------------------------------------------------------------------
# Launch helpers
# ---------------------------------------------------------------------------

def open_in_visual_studio(sln_path):
    if not os.path.isfile(sln_path):
        messagebox.showerror("File Not Found", f"Solution file not found:\n{sln_path}")
        return
    os.startfile(sln_path)


def _normalize_path(p):
    return p.replace("\\", "/").lower()


def close_cursor_for_repo(repo_path):
    """Terminate Cursor processes associated with this repo path."""
    target = _normalize_path(repo_path)
    folder_name = os.path.basename(repo_path.rstrip("/\\")).lower()
    closed = 0
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (proc.info["name"] or "").lower()
            if "cursor" not in name:
                continue
            cmdline = _normalize_path(" ".join(proc.info["cmdline"] or []))
            if target in cmdline or folder_name in cmdline:
                proc.terminate()
                closed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return closed


def close_visual_studio_for_sln(sln_path):
    """Terminate Visual Studio processes associated with this solution."""
    target = _normalize_path(sln_path)
    sln_name = os.path.splitext(os.path.basename(sln_path))[0].lower()
    closed = 0
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (proc.info["name"] or "").lower()
            if "devenv" not in name:
                continue
            cmdline = _normalize_path(" ".join(proc.info["cmdline"] or []))
            if target in cmdline or sln_name in cmdline:
                proc.terminate()
                closed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return closed


def open_in_cursor(repo_path):
    try:
        subprocess.Popen(["cursor", repo_path])
        return
    except FileNotFoundError:
        pass
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    cursor_exe = os.path.join(local_app_data, "Programs", "cursor", "Cursor.exe")
    if os.path.exists(cursor_exe):
        subprocess.Popen([cursor_exe, repo_path])
        return
    messagebox.showerror(
        "Cursor Not Found",
        f"Could not find Cursor. Make sure it's installed or add it to your PATH.\n\nRepo: {repo_path}"
    )


# ---------------------------------------------------------------------------
# Reusable styled widgets
# ---------------------------------------------------------------------------

def neon_button(parent, text, command, color=NEON_CYAN, width=120, height=36):
    return ctk.CTkButton(
        parent, text=text, command=command,
        width=width, height=height,
        fg_color=color, hover_color=_lighten(color),
        text_color="#000000",
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        corner_radius=8,
    )


def subtle_button(parent, text, command, width=80, height=30):
    return ctk.CTkButton(
        parent, text=text, command=command,
        width=width, height=height,
        fg_color=BTN_SUBTLE, hover_color=BTN_SUBTLE_H,
        text_color=TEXT_PRIMARY,
        font=ctk.CTkFont(family="Segoe UI", size=11),
        corner_radius=6, border_width=1, border_color=INPUT_BORDER,
    )


def danger_button(parent, text, command, width=30, height=30):
    return ctk.CTkButton(
        parent, text=text, command=command,
        width=width, height=height,
        fg_color=BTN_SUBTLE, hover_color=NEON_DANGER,
        text_color=TEXT_DIM,
        font=ctk.CTkFont(family="Segoe UI", size=11),
        corner_radius=6,
    )


def styled_entry(parent, placeholder="", width=380):
    return ctk.CTkEntry(
        parent, placeholder_text=placeholder, width=width,
        fg_color=INPUT_BG, border_color=INPUT_BORDER, border_width=1,
        text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_DIM,
        font=ctk.CTkFont(family="Segoe UI", size=12),
        corner_radius=6,
    )


def section_label(parent, text):
    return ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        text_color=NEON_PURPLE,
    )


def _lighten(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"#{min(255,r+30):02x}{min(255,g+30):02x}{min(255,b+30):02x}"


# ---------------------------------------------------------------------------
# Edit Project Dialog
# ---------------------------------------------------------------------------

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
        # Title bar
        title_bar = ctk.CTkFrame(self, fg_color=HEADER_BG, corner_radius=0, height=56)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        title_text = "Edit Project" if self.project["name"] else "New Project"
        ctk.CTkLabel(
            title_bar, text=title_text,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=NEON_CYAN,
        ).pack(side="left", padx=20, pady=16)

        ctk.CTkFrame(self, fg_color=NEON_PURPLE, height=2, corner_radius=0).pack(fill="x")

        # Body
        body = ctk.CTkScrollableFrame(self, fg_color=BG, scrollbar_button_color=BTN_SUBTLE)
        body.pack(fill="both", expand=True)

        inner = ctk.CTkFrame(body, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        # Project name
        section_label(inner, "PROJECT NAME").pack(anchor="w", pady=(0, 6))
        self.name_entry = styled_entry(inner, placeholder="e.g. Safeguard", width=570)
        self.name_entry.pack(anchor="w", pady=(0, 20))
        self.name_entry.insert(0, self.project["name"])

        # Repos
        section_label(inner, "CURSOR REPOS").pack(anchor="w", pady=(0, 4))

        # Column headers
        col_headers = ctk.CTkFrame(inner, fg_color="transparent")
        col_headers.pack(fill="x", padx=2, pady=(0, 4))
        ctk.CTkLabel(col_headers, text="Display Name  (optional)",
                     font=ctk.CTkFont(family="Segoe UI", size=10),
                     text_color=TEXT_DIM).pack(side="left", padx=(10, 0))
        ctk.CTkLabel(col_headers, text="Folder Path",
                     font=ctk.CTkFont(family="Segoe UI", size=10),
                     text_color=TEXT_DIM).pack(side="left", padx=(148, 0))

        self.repo_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self.repo_frame.pack(fill="x", pady=(0, 8))

        self.repo_rows = []
        for repo in self.project.get("repos", []):
            self._add_repo_row(repo)

        neon_button(inner, "+ Add Repo", self._add_repo_row,
                    color=NEON_PURPLE, width=130, height=32).pack(anchor="w", pady=(0, 20))

        # Divider
        ctk.CTkFrame(inner, fg_color=CARD_BORDER, height=1).pack(fill="x", pady=(0, 16))

        # Solution file
        section_label(inner, "VISUAL STUDIO SOLUTION  ·  optional").pack(anchor="w", pady=(0, 4))

        sln_col_headers = ctk.CTkFrame(inner, fg_color="transparent")
        sln_col_headers.pack(fill="x", padx=2, pady=(0, 4))
        ctk.CTkLabel(sln_col_headers, text="Display Name  (optional)",
                     font=ctk.CTkFont(family="Segoe UI", size=10),
                     text_color=TEXT_DIM).pack(side="left", padx=(10, 0))
        ctk.CTkLabel(sln_col_headers, text=".sln File Path",
                     font=ctk.CTkFont(family="Segoe UI", size=10),
                     text_color=TEXT_DIM).pack(side="left", padx=(148, 0))

        sln_row = ctk.CTkFrame(inner, fg_color=CARD_BG,
                               corner_radius=8, border_width=1, border_color=CARD_BORDER)
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

        # Footer
        ctk.CTkFrame(self, fg_color=CARD_BORDER, height=1, corner_radius=0).pack(fill="x")
        footer = ctk.CTkFrame(self, fg_color=HEADER_BG, corner_radius=0, height=60)
        footer.pack(fill="x")
        footer.pack_propagate(False)

        neon_button(footer, "Save", self._save, color=NEON_CYAN, width=110).pack(side="right", padx=20, pady=12)
        subtle_button(footer, "Cancel", self.destroy, width=90, height=36).pack(side="right", pady=12)

    def _add_repo_row(self, repo=None):
        if repo is None:
            repo = {"name": "", "path": ""}

        row = ctk.CTkFrame(self.repo_frame, fg_color=CARD_BG,
                           corner_radius=8, border_width=1, border_color=CARD_BORDER)
        row.pack(fill="x", pady=4)

        name_entry = styled_entry(row, placeholder="Name", width=140)
        name_entry.pack(side="left", padx=(10, 6), pady=8)
        name_entry.insert(0, repo.get("name", ""))

        path_entry = styled_entry(row, placeholder="Repo folder path", width=260)
        path_entry.pack(side="left", padx=(0, 6), pady=8)
        path_entry.insert(0, repo.get("path", ""))

        subtle_button(row, "Browse", lambda e=path_entry: self._browse_folder(e), width=65, height=28).pack(side="left", padx=(0, 6))
        danger_button(row, "✕", lambda r=row: self._remove_row(r), width=28, height=28).pack(side="left", padx=(0, 8))

        self.repo_rows.append((row, name_entry, path_entry))

    def _browse_folder(self, entry):
        path = filedialog.askdirectory(title="Select Repo Folder")
        if path:
            entry.delete(0, "end")
            entry.insert(0, path)

    def _browse_sln(self):
        path = filedialog.askopenfilename(title="Select Solution File",
                                          filetypes=[("Solution files", "*.sln"), ("All files", "*.*")])
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
        sln = {"name": self.sln_name_entry.get().strip(), "path": sln_path} if sln_path else {"name": "", "path": ""}
        self.result = {"name": name, "repos": repos, "sln": sln}
        self.destroy()


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------

class DevLauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dev Launcher")
        self.geometry("520x620")
        self.minsize(420, 360)
        self.configure(fg_color=BG)
        self._set_icon()
        self.config_data = load_config()
        self._build_ui()

    def _set_icon(self):
        if not os.path.exists(ICON_PATH):
            generate_icon()
        self.after(250, self._apply_icon)

    def _apply_icon(self):
        try:
            self.iconbitmap(ICON_PATH)
        except Exception:
            pass

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=HEADER_BG, corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="DEV LAUNCHER",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=NEON_CYAN,
        ).pack(side="left", padx=20, pady=18)

        neon_button(header, "+ New Project", self._new_project,
                    color=NEON_PURPLE, width=130, height=34).pack(side="right", padx=20, pady=15)

        ctk.CTkFrame(self, fg_color=NEON_CYAN, height=2, corner_radius=0).pack(fill="x")

        self.project_list = ctk.CTkScrollableFrame(
            self, fg_color=BG,
            scrollbar_button_color=BTN_SUBTLE,
            scrollbar_button_hover_color=INPUT_BORDER,
            label_text="",
        )
        self.project_list.pack(fill="both", expand=True, padx=16, pady=16)

        self._render_projects()

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

    def _render_card(self, index, project):
        color = CARD_PALETTE[index % len(CARD_PALETTE)]

        card = ctk.CTkFrame(
            self.project_list,
            fg_color=CARD_BG, corner_radius=12,
            border_width=1, border_color=CARD_BORDER,
        )
        card.pack(fill="x", pady=6, padx=2)

        # Neon top edge
        ctk.CTkFrame(card, fg_color=color, height=3, corner_radius=0).pack(fill="x")

        # Header row
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(6, 3))

        ctk.CTkLabel(
            top, text=project["name"],
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        danger_button(top, "✕", lambda i=index: self._delete_project(i), width=28, height=28).pack(side="right", padx=(4, 0))
        subtle_button(top, "Edit", lambda i=index: self._edit_project(i), width=54, height=28).pack(side="right", padx=(0, 4))

        # Clickable resource pills
        repos = project.get("repos", [])
        sln = project.get("sln", "")

        has_resources = repos or (sln and sln.get("path"))
        if has_resources:
            pills_frame = ctk.CTkFrame(card, fg_color="transparent")
            pills_frame.pack(fill="x", padx=12, pady=(0, 4))

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
            ).pack(anchor="w", padx=12, pady=(0, 4))

        # Separator
        ctk.CTkFrame(card, fg_color=CARD_BORDER, height=1).pack(fill="x", pady=0)

        # Action buttons row (tight vertical packing — no extra frame padding)
        btn_row = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0)
        btn_row.pack(fill="x", pady=0)

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
            self.config_data["projects"].append(dialog.result)
            save_config(self.config_data)
            self._render_projects()

    def _edit_project(self, index):
        project = self.config_data["projects"][index]
        dialog = ProjectDialog(self, project=dict(project))
        self.wait_window(dialog)
        if dialog.result:
            self.config_data["projects"][index] = dialog.result
            save_config(self.config_data)
            self._render_projects()

    def _delete_project(self, index):
        name = self.config_data["projects"][index]["name"]
        if messagebox.askyesno("Delete Project", f"Delete '{name}'?"):
            self.config_data["projects"].pop(index)
            save_config(self.config_data)
            self._render_projects()


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = DevLauncherApp()
    app.mainloop()
