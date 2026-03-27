"""
Run this once to create a Desktop shortcut for Dev Launcher.
After it's on your Desktop, right-click it and choose "Pin to taskbar".
"""
import os
import subprocess

APP_DIR   = os.path.dirname(os.path.abspath(__file__))
MAIN_PY   = os.path.join(APP_DIR, "main.py")
ICON_ICO  = os.path.join(APP_DIR, "icon.ico")
# Ask Windows directly where the Desktop actually is (handles OneDrive-synced desktops)
import ctypes.wintypes
buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
ctypes.windll.shell32.SHGetFolderPathW(0, 0x0000, 0, 0, buf)  # CSIDL_DESKTOP = 0
DESKTOP  = buf.value or os.path.join(os.path.expanduser("~"), "Desktop")
SHORTCUT = os.path.join(DESKTOP, "Dev Launcher.lnk")

# Find pythonw.exe (runs without a console window)
import sys
pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
if not os.path.exists(pythonw):
    pythonw = sys.executable  # fallback

ps_script = f"""
$shell    = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut("{SHORTCUT}")
$shortcut.TargetPath       = "{pythonw}"
$shortcut.Arguments        = '"{MAIN_PY}"'
$shortcut.WorkingDirectory = "{APP_DIR}"
$shortcut.IconLocation     = "{ICON_ICO}"
$shortcut.Description      = "Dev Launcher"
$shortcut.Save()
"""

subprocess.run(["powershell", "-Command", ps_script], check=True)
print(f"Shortcut created on your Desktop: {SHORTCUT}")
print()
print("To pin to taskbar:")
print("  1. Find 'Dev Launcher' on your Desktop")
print("  2. Right-click it → 'Pin to taskbar'")
