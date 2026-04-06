"""Open repos in Cursor, solutions in Visual Studio, and close matching processes."""

import os
import subprocess

import psutil
from tkinter import messagebox


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
        f"Could not find Cursor. Make sure it's installed or add it to your PATH.\n\nRepo: {repo_path}",
    )
