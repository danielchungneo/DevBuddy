"""Small helpers: color math, screen bounds."""

import ctypes
import sys


def lighten(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"#{min(255, r + 30):02x}{min(255, g + 30):02x}{min(255, b + 30):02x}"


def hex_to_rgb_tuple(h):
    h = (h or "").strip().lstrip("#")
    if len(h) == 6 and all(c in "0123456789abcdefABCDEF" for c in h):
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return None


def rgb_tuple_to_hex(rgb):
    r, g, b = rgb
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def virtual_screen_bbox():
    """(left, top, width, height) of the virtual screen (all monitors) on Windows."""
    if sys.platform != "win32":
        return 0, 0, 0, 0
    u = ctypes.windll.user32
    return (
        u.GetSystemMetrics(76),
        u.GetSystemMetrics(77),
        u.GetSystemMetrics(78),
        u.GetSystemMetrics(79),
    )
