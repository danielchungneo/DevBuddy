"""Focus session animation: custom image sequence / GIF, or built-in canvas fallback."""

from __future__ import annotations

import glob
import math
import os
import re
import tkinter as tk

import customtkinter as ctk

from devbuddy.theme import BG

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FOCUS_PANDA_DIR = os.path.join(_ROOT, "assets", "focus_panda")
PANDA_IDLE_PATH = os.path.join(_ROOT, "assets", "panda-idle.png")


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    s = h.strip().lstrip("#")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def _replace_near_black_with_bg(rgba, bg_hex: str, threshold: int = 18) -> None:
    """
    In-place: sprite sheet backdrops are often #000; swap those pixels for app BG
    so the panel does not show a black rectangle. Threshold keeps dark hoodie shades.
    """
    br, bg, bb = _hex_to_rgb(bg_hex)
    px = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 140 and r <= threshold and g <= threshold and b <= threshold:
                px[x, y] = (br, bg, bb, 255)


def load_focus_idle_photo(tk_master, target_w: int, target_h: int):
    """
    Static panda shown before the focus timer starts (``assets/panda-idle.png``).
    Same size and black→BG treatment as the animated sprite. Returns PhotoImage or None.
    """
    if not os.path.isfile(PANDA_IDLE_PATH):
        return None
    try:
        from PIL import Image, ImageTk

        im = Image.open(PANDA_IDLE_PATH).convert("RGBA")
        im = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
        _replace_near_black_with_bg(im, BG)
        return ImageTk.PhotoImage(im, master=tk_master)
    except Exception:
        return None


def _natural_sort_key(path: str):
    base = os.path.basename(path)
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", base)]


def _slice_sprite_sheet(
    path: str,
    target_w: int,
    target_h: int,
    cols: int,
    rows: int,
    tk_master,
) -> list:
    """
    Cut a grid sprite sheet into frames in row-major order (left→right, top→bottom).
    ``tk_master`` must be a Tk/CTk widget so ImageTk can attach to a root window.
    """
    from PIL import Image, ImageTk

    im = Image.open(path).convert("RGBA")
    iw, ih = im.size
    fw = max(1, iw // cols)
    fh = max(1, ih // rows)
    frames = []
    for row in range(rows):
        for col in range(cols):
            box = (col * fw, row * fh, (col + 1) * fw, (row + 1) * fh)
            cell = im.crop(box)
            cell = cell.resize((target_w, target_h), Image.Resampling.LANCZOS)
            _replace_near_black_with_bg(cell, BG)
            frames.append(ImageTk.PhotoImage(cell, master=tk_master))
    return frames


def _load_frames_from_disk(tk_master, target_w: int, target_h: int) -> list:
    """Return list of ImageTk.PhotoImage frames, or empty to use canvas fallback."""
    try:
        from PIL import Image, ImageSequence, ImageTk
    except ImportError:
        return []

    # 1) Sprite sheet (5×5 = 25 frames) — single PNG, no need to split files
    for path in (
        os.path.join(_ROOT, "assets", "sprite-max-px-25.png"),
        os.path.join(FOCUS_PANDA_DIR, "sprite-max-px-25.png"),
        os.path.join(FOCUS_PANDA_DIR, "sprite.png"),
        os.path.join(FOCUS_PANDA_DIR, "sprite_sheet.png"),
    ):
        if os.path.isfile(path):
            try:
                frames = _slice_sprite_sheet(path, target_w, target_h, 5, 5, tk_master)
                if len(frames) >= 1:
                    return frames
            except Exception:
                continue

    if not os.path.isdir(FOCUS_PANDA_DIR):
        return []

    # Prefer a single animated GIF if present
    for name in ("focus.gif", "panda.gif", "anim.gif", "animation.gif"):
        gif_path = os.path.join(FOCUS_PANDA_DIR, name)
        if not os.path.isfile(gif_path):
            continue
        try:
            im = Image.open(gif_path)
            frames = []
            for frame in ImageSequence.Iterator(im):
                rgba = frame.convert("RGBA")
                rgba = rgba.resize((target_w, target_h), Image.Resampling.LANCZOS)
                _replace_near_black_with_bg(rgba, BG)
                frames.append(ImageTk.PhotoImage(rgba, master=tk_master))
            if frames:
                return frames
        except Exception:
            continue

    # PNG / WebP sequence (same size recommended; we resize to target)
    paths = sorted(
        glob.glob(os.path.join(FOCUS_PANDA_DIR, "*.png"))
        + glob.glob(os.path.join(FOCUS_PANDA_DIR, "*.webp")),
        key=_natural_sort_key,
    )
    if len(paths) < 1:
        return []

    frames = []
    for p in paths:
        try:
            rgba = Image.open(p).convert("RGBA")
            rgba = rgba.resize((target_w, target_h), Image.Resampling.LANCZOS)
            _replace_near_black_with_bg(rgba, BG)
            frames.append(ImageTk.PhotoImage(rgba, master=tk_master))
        except Exception:
            continue
    return frames if len(frames) >= 1 else []


class PandaFocusAnimation(ctk.CTkFrame):
    """
    Loads animation in this order:

    1. **Sprite sheet** — ``assets/sprite-max-px-25.png`` (5×5 grid, 25 frames, row-major),
       or ``assets/focus_panda/sprite.png`` / ``sprite_sheet.png`` / same filename there.
    2. **GIF** in ``assets/focus_panda/`` (focus.gif, panda.gif, …).
    3. **PNG/WebP sequence** in ``assets/focus_panda/``, sorted by filename.
    4. Built-in canvas drawing if nothing else is available.
    """

    def __init__(self, parent, width: int = 340, height: int = 240):
        super().__init__(parent, fg_color=BG, width=width, height=height)
        self._cw = width
        self._ch = height
        self._running = False
        self._tick = 0
        self._job = None

        self._frames: list = _load_frames_from_disk(self.winfo_toplevel(), width, height)
        self._frame_index = 0
        self._img_label: tk.Label | None = None

        if self._frames:
            self._img_label = tk.Label(self, bg=BG, bd=0, highlightthickness=0)
            self._img_label.pack(fill="both", expand=True)
            self._img_label.configure(image=self._frames[0])
        else:
            self._canvas = ctk.CTkCanvas(
                self,
                width=width,
                height=height,
                bg=BG,
                highlightthickness=0,
                bd=0,
            )
            self._canvas.pack(fill="both", expand=True)
            self._draw_canvas_frame(0, idle=True)

    def start(self):
        if self._running:
            return
        self._running = True
        self._tick = 0
        self._loop()

    def stop(self):
        self._running = False
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        if self._frames and self._img_label is not None:
            self._img_label.configure(image=self._frames[0])
        else:
            self._draw_canvas_frame(0, idle=True)

    def _loop(self):
        if not self._running:
            return
        self._tick += 1
        if self._frames and self._img_label is not None:
            # ~8–12 fps depending on frame count
            idx = (self._tick // 2) % len(self._frames)
            self._img_label.configure(image=self._frames[idx])
        else:
            self._draw_canvas_frame(self._tick, idle=False)
        self._job = self.after(45, self._loop)

    def _draw_canvas_frame(self, t: int, idle: bool):
        c = self._canvas
        c.delete("all")
        w, h = self._cw, self._ch
        c.create_rectangle(0, 0, w, h, fill=BG, outline="")

        bob = 0 if idle else math.sin(t * 0.12) * 4
        type_phase = 0 if idle else math.sin(t * 0.35) * 6

        cx = w * 0.5
        cy = h * 0.42 + bob

        lap_x0, lap_y0 = cx - 72, cy + 58
        lap_x1, lap_y1 = cx + 72, cy + 92
        c.create_rectangle(lap_x0, lap_y0, lap_x1, lap_y1, fill="#1a1a28", outline="#2e2e44", width=2)
        c.create_rectangle(lap_x0 + 8, lap_y0 + 4, lap_x1 - 8, lap_y1 - 28, fill="#0e1520", outline="#00d4ff", width=1)
        c.create_line(lap_x0 + 14, lap_y1 - 10, lap_x1 - 14, lap_y1 - 10, fill="#00d4ff", width=2)

        c.create_oval(cx - 78, cy + 12, cx + 78, cy + 110, fill="#2c3e64", outline="#3d5280", width=2)
        c.create_arc(cx - 62, cy - 18, cx + 62, cy + 70, start=200, extent=140, style=tk.CHORD, fill="#354a72", outline="#4a6194", width=2)

        c.create_oval(cx - 52, cy - 72, cx + 52, cy + 28, fill="#f2f2f2", outline="#222", width=2)
        c.create_oval(cx - 68, cy - 78, cx - 28, cy - 38, fill="#1a1a1a", outline="#111", width=1)
        c.create_oval(cx + 28, cy - 78, cx + 68, cy - 38, fill="#1a1a1a", outline="#111", width=1)
        c.create_oval(cx - 44, cy - 28, cx - 12, cy + 4, fill="#1a1a1a", outline="")
        c.create_oval(cx + 12, cy - 28, cx + 44, cy + 4, fill="#1a1a1a", outline="")
        c.create_oval(cx - 34, cy - 14, cx - 22, cy - 4, fill="#fff", outline="")
        c.create_oval(cx + 22, cy - 14, cx + 34, cy - 4, fill="#fff", outline="")
        c.create_oval(cx - 30, cy - 12, cx - 24, cy - 8, fill="#111", outline="")
        c.create_oval(cx + 24, cy - 12, cx + 30, cy - 8, fill="#111", outline="")
        c.create_oval(cx - 6, cy + 6, cx + 6, cy + 16, fill="#333", outline="")

        band_y = cy - 62
        c.create_arc(cx - 58, band_y - 8, cx + 58, cy - 8, start=0, extent=180, style=tk.ARC, outline="#5a6a88", width=5)
        c.create_rectangle(cx - 62, cy - 48, cx - 44, cy - 12, fill="#3a4558", outline="#00d4ff", width=2)
        c.create_rectangle(cx + 44, cy - 48, cx + 62, cy - 12, fill="#3a4558", outline="#00d4ff", width=2)

        arm_y = cy + 38
        lx = cx - 48 + type_phase
        rx = cx + 48 - type_phase
        c.create_line(cx - 40, arm_y, lx, lap_y0 + 8, fill="#354a72", width=8, capstyle=tk.ROUND)
        c.create_line(cx + 40, arm_y, rx, lap_y0 + 8, fill="#354a72", width=8, capstyle=tk.ROUND)
        c.create_oval(lx - 10, lap_y0 - 2, lx + 10, lap_y0 + 14, fill="#f2f2f2", outline="#222", width=1)
        c.create_oval(rx - 10, lap_y0 - 2, rx + 10, lap_y0 + 14, fill="#f2f2f2", outline="#222", width=1)

        if not idle:
            for i in range(4):
                phase = (t * 0.08 + i * 1.7) % (2 * math.pi)
                nx = cx + 90 + math.sin(phase + i) * 12
                ny = cy - 30 - (t * 0.6 + i * 18) % 90
                hues = ("#5ac8ff", "#7b2fff", "#39e6a8", "#f0c860")
                c.create_text(nx, ny, text="\u266a", fill=hues[i % 4], font=("Segoe UI", 14 + i % 3))

        c.create_line(16, h - 28, w - 16, h - 28, fill="#1e1e3a", width=2)
