#!/usr/bin/env python3
"""Render accumulating on-screen bullet overlays (1080x1920 RGBA, transparent) for the
AI-brain-rot Short. Two lists: navigator recommendations + AI recommendations. Each PNG
shows the list-so-far with the newest item highlighted (bright white + red marker) and
prior items dimmed. A soft bottom scrim keeps text legible over the talking-head footage.
Face sits upper-center, so the list lives in the lower third."""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
OUTDIR = os.path.join(os.path.dirname(__file__), "assets", "bullets")
os.makedirs(OUTDIR, exist_ok=True)

# A bold sans-serif TTF. Falls back across Linux/macOS/Windows; override BOLD if none match.
BOLD = next((p for p in [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",  # Linux (sudo apt install fonts-liberation)
    "/Library/Fonts/Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",  # macOS
    "C:\\Windows\\Fonts\\arialbd.ttf",  # Windows
] if os.path.exists(p)), "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf")
RED = (214, 28, 28)
WHITE = (255, 255, 255)
DIM = (235, 235, 235)

NAV = ["Build the route yourself", "Study the route before you drive", "Use paper maps"]
AI = ["Think how you would solve the problem yourself", "Write the first draft yourself", "Read books"]

START_Y = 1300      # y of first bullet (lower third, below the face/torso)
SPACING = 156
MAXW = 920          # max text width before auto-shrink
DOT_R = 13
GAP = 26            # dot -> text gap


def fit_font(text, size=62):
    while size > 38:
        f = ImageFont.truetype(BOLD, size)
        if f.getlength(text) <= MAXW:
            return f
        size -= 2
    return ImageFont.truetype(BOLD, size)


def wrap(text, font):
    """Greedy word-wrap to lines that each fit MAXW."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.getlength(t) <= MAXW or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def scrim():
    """Soft dark gradient over the lower ~55% for legibility."""
    g = Image.new("L", (1, H), 0)
    px = g.load()
    top = int(H * 0.46)
    for y in range(H):
        if y < top:
            px[0, y] = 0
        else:
            t = (y - top) / (H - top)
            px[0, y] = int(190 * (t ** 1.4))
    alpha = g.resize((W, H))
    layer = Image.new("RGBA", (W, H), (8, 8, 10, 0))
    layer.putalpha(alpha)
    return layer


def render(items, active, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.alpha_composite(scrim())
    d = ImageDraw.Draw(img)
    for i, text in enumerate(items):
        y = START_Y + i * SPACING
        is_active = (i == active)
        f = fit_font(text)
        tw = f.getlength(text)
        total = DOT_R * 2 + GAP + tw
        x = (W - total) / 2
        # marker dot
        cy = y + f.getbbox("Ag")[3] // 2
        dot_col = RED if is_active else (150, 150, 150)
        d.ellipse([x, cy - DOT_R, x + DOT_R * 2, cy + DOT_R], fill=dot_col)
        # text (subtle shadow for legibility, then fill)
        tx = x + DOT_R * 2 + GAP
        col = WHITE if is_active else DIM + (0,)
        col = WHITE if is_active else (220, 220, 220)
        alpha = 255 if is_active else 150
        d.text((tx + 3, y + 3), text, font=f, fill=(0, 0, 0, 160))
        d.text((tx, y), text, font=f, fill=col + (alpha,))
        # red underline accent on the active line
        if is_active:
            d.rectangle([tx, y + f.size + 12, tx + tw, y + f.size + 18], fill=RED + (255,))
    img.save(path)
    print("wrote", path)


def render_wrapped(items, active, path, size):
    """Like render() but every item uses one uniform font size and long items wrap to
    multiple lines (keeps the list visually consistent instead of auto-shrinking)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.alpha_composite(scrim())
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(BOLD, size)
    LH = int(size * 1.2)
    ITEM_GAP = SPACING - LH      # keep single-line item-to-item spacing ~= SPACING
    y = START_Y
    for i, text in enumerate(items):
        is_active = (i == active)
        lines = wrap(text, f)
        maxw = max(f.getlength(ln) for ln in lines)
        total = DOT_R * 2 + GAP + maxw
        x = (W - total) / 2
        cy = y + f.getbbox("Ag")[3] // 2
        d.ellipse([x, cy - DOT_R, x + DOT_R * 2, cy + DOT_R],
                  fill=RED if is_active else (150, 150, 150))
        tx = x + DOT_R * 2 + GAP
        col = WHITE if is_active else (220, 220, 220)
        alpha = 255 if is_active else 150
        ly = y
        for ln in lines:
            d.text((tx + 3, ly + 3), ln, font=f, fill=(0, 0, 0, 160))
            d.text((tx, ly), ln, font=f, fill=col + (alpha,))
            ly += LH
        if is_active:
            uy = y + (len(lines) - 1) * LH + f.size + 12
            d.rectangle([tx, uy, tx + f.getlength(lines[-1]), uy + 6], fill=RED + (255,))
        y += len(lines) * LH + ITEM_GAP
    img.save(path)
    print("wrote", path)


for k in range(len(NAV)):                      # navigator list: unchanged (single-line auto-fit)
    render(NAV[: k + 1], k, os.path.join(OUTDIR, f"nav{k+1}.png"))
for k in range(len(AI)):                        # AI list: uniform size, long first bullet wraps to 2 lines
    render_wrapped(AI[: k + 1], k, os.path.join(OUTDIR, f"ai{k+1}.png"), size=60)
