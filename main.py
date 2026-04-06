"""Entry point: run Dev Buddy from the repo root (python main.py)."""

import customtkinter as ctk

from devbuddy.app import DevLauncherApp

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

if __name__ == "__main__":
    app = DevLauncherApp()
    app.mainloop()
