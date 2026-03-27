from PIL import Image, ImageDraw, ImageFilter
import os

ICON_PATH = os.path.join(os.path.dirname(__file__), "icon.ico")

# Theme colors
BG_COLOR     = (10, 10, 18)
CYAN         = (0, 212, 255)
PURPLE       = (123, 47, 255)
PURPLE_DARK  = (70, 15, 160)
ORANGE       = (255, 107, 53)
YELLOW       = (255, 215, 60)
WHITE        = (255, 255, 255)
SCREEN_BG    = (8, 8, 22)


def _glow(draw, shape_fn, color, radius=8, steps=5):
    """Fake a glow by drawing the shape multiple times with decreasing alpha."""
    r, g, b = color
    for i in range(steps, 0, -1):
        alpha = int(60 * (i / steps))
        expand = i * (radius // steps)
        shape_fn(draw, expand, (r, g, b, alpha))


def generate_icon():
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ── Background ──────────────────────────────────────────────────────────
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=44,
                           fill=(*BG_COLOR, 255))

    # ── Stars ────────────────────────────────────────────────────────────────
    stars = [(32, 28), (80, 18), (130, 38), (52, 72), (22, 108),
             (210, 55), (235, 100), (220, 160), (170, 22), (245, 195)]
    for sx, sy in stars:
        r = 2
        draw.ellipse([sx - r, sy - r, sx + r, sy + r],
                     fill=(*WHITE, 180))

    # ── Monitor ──────────────────────────────────────────────────────────────
    mx1, my1, mx2, my2 = 16, 142, 182, 220

    # Glow layer
    glow_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    glow_draw.rounded_rectangle([mx1 - 6, my1 - 6, mx2 + 6, my2 + 6],
                                radius=14, fill=(*CYAN, 50))
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=6))
    img = Image.alpha_composite(img, glow_img)
    draw = ImageDraw.Draw(img)

    # Screen
    draw.rounded_rectangle([mx1, my1, mx2, my2], radius=9,
                           outline=(*CYAN, 255), width=4, fill=(*SCREEN_BG, 255))

    # Code lines inside screen
    line_data = [(157, 100), (171, 76), (185, 88), (199, 60)]
    for y, w in line_data:
        line_glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        lg_draw = ImageDraw.Draw(line_glow)
        lg_draw.rounded_rectangle([mx1 + 10, y, mx1 + 10 + w, y + 7],
                                  radius=3, fill=(*CYAN, 160))
        img = Image.alpha_composite(img, line_glow)
    draw = ImageDraw.Draw(img)

    # Stand
    cx = (mx1 + mx2) // 2
    draw.rectangle([cx - 7, my2, cx + 7, my2 + 14], fill=(*CYAN, 230))
    draw.rounded_rectangle([cx - 24, my2 + 12, cx + 24, my2 + 22],
                           radius=4, fill=(*CYAN, 230))

    # ── Rocket ───────────────────────────────────────────────────────────────
    rx = 192   # horizontal center
    tip_y = 32

    # Flame glow
    flame_glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fg_draw = ImageDraw.Draw(flame_glow)
    fg_draw.polygon([(rx - 20, tip_y + 112), (rx, tip_y + 160), (rx + 20, tip_y + 112)],
                    fill=(*ORANGE, 80))
    flame_glow = flame_glow.filter(ImageFilter.GaussianBlur(radius=10))
    img = Image.alpha_composite(img, flame_glow)
    draw = ImageDraw.Draw(img)

    # Nose cone
    draw.polygon([(rx, tip_y), (rx - 18, tip_y + 38), (rx + 18, tip_y + 38)],
                 fill=(*PURPLE, 255))

    # Body
    draw.rectangle([rx - 18, tip_y + 36, rx + 18, tip_y + 100],
                   fill=(*PURPLE, 255))

    # Left fin
    draw.polygon([(rx - 18, tip_y + 78), (rx - 36, tip_y + 108), (rx - 18, tip_y + 100)],
                 fill=(*PURPLE_DARK, 255))

    # Right fin
    draw.polygon([(rx + 18, tip_y + 78), (rx + 36, tip_y + 108), (rx + 18, tip_y + 100)],
                 fill=(*PURPLE_DARK, 255))

    # Porthole
    draw.ellipse([rx - 11, tip_y + 46, rx + 11, tip_y + 68],
                 fill=(*SCREEN_BG, 255), outline=(*CYAN, 255), width=2)
    draw.ellipse([rx - 6, tip_y + 51, rx + 6, tip_y + 63],
                 fill=(*CYAN, 180))

    # Outer flame
    draw.polygon([(rx - 14, tip_y + 100), (rx, tip_y + 140), (rx + 14, tip_y + 100)],
                 fill=(*ORANGE, 255))

    # Inner flame
    draw.polygon([(rx - 8, tip_y + 100), (rx, tip_y + 125), (rx + 8, tip_y + 100)],
                 fill=(*YELLOW, 255))

    # ── Rocket body glow overlay ─────────────────────────────────────────────
    body_glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(body_glow)
    bg_draw.rounded_rectangle([rx - 22, tip_y - 4, rx + 22, tip_y + 104],
                              radius=22, fill=(*PURPLE, 30))
    body_glow = body_glow.filter(ImageFilter.GaussianBlur(radius=8))
    img = Image.alpha_composite(img, body_glow)

    # ── Save as .ico with multiple sizes ─────────────────────────────────────
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = [img.resize(s, Image.LANCZOS) for s in sizes]
    icons[0].save(ICON_PATH, format="ICO", sizes=sizes,
                  append_images=icons[1:])

    return ICON_PATH


if __name__ == "__main__":
    path = generate_icon()
    print(f"Icon saved to: {path}")
