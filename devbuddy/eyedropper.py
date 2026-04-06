"""Fullscreen frozen screenshot: click to sample RGB (plain Tk + Canvas for 1:1 pixels)."""

import ctypes
import sys
import tkinter as tk


class EyedropperOverlay(tk.Toplevel):
    """
    Frozen screenshot at 1:1 pixels. Uses plain Tk + Canvas (not CTk) so HiDPI
    scaling does not stretch the image vs. click coordinates.
    """

    def __init__(self, master, pil_image, offset_xy, on_done):
        super().__init__(master)
        self.pil_image = pil_image
        self.ox, self.oy = offset_xy
        self.on_done = on_done
        from PIL import ImageTk

        self._photo = ImageTk.PhotoImage(pil_image)
        w, h = pil_image.size
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.geometry(f"{w}x{h}+{self.ox}+{self.oy}")
        self.configure(bg="#000000")

        self._canvas = tk.Canvas(
            self,
            width=w,
            height=h,
            highlightthickness=0,
            borderwidth=0,
            bg="#000000",
        )
        self._canvas.pack(fill="both", expand=False)
        self._canvas.create_image(0, 0, anchor="nw", image=self._photo)
        self._canvas.bind("<Button-1>", self._click)
        self._canvas.bind("<Escape>", self._cancel)
        self._canvas.bind("<Button-3>", self._cancel)
        self._canvas.config(cursor="crosshair")
        self.bind("<Escape>", self._cancel)
        self.bind("<Button-3>", self._cancel)
        self.grab_set()
        self.focus_force()

    def _click(self, event):
        if sys.platform == "win32":

            class _Pt(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

            pt = _Pt()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            ix = int(pt.x - self.ox)
            iy = int(pt.y - self.oy)
        else:
            ix, iy = event.x, event.y
        ix = max(0, min(self.pil_image.width - 1, ix))
        iy = max(0, min(self.pil_image.height - 1, iy))
        px = self.pil_image.getpixel((ix, iy))
        if isinstance(px, int):
            rgb = (px, px, px)
        else:
            rgb = tuple(int(c) for c in px[:3])
        self.grab_release()
        self.destroy()
        self.on_done(rgb)

    def _cancel(self, event=None):
        self.grab_release()
        self.destroy()
        self.on_done(None)
