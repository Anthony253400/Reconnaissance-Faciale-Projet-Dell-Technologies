import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Color palette: vivid but clean (the pipeline works in RGB)
_COLORS = {
    "green": (16, 185, 129),   # face — emerald green
    "red":   (239, 68, 68),    # body — coral red
}
_DARK = (15, 15, 15)
_WHITE = (255, 255, 255)

# Extra named colors for backward compatibility with other modules
_EXTRA_COLORS = {
    "blue":   (59, 130, 246),
    "yellow": (250, 204, 21),
    "white":  _WHITE,
    "black":  (0, 0, 0),
    "gray":   (128, 128, 128),
    "orange": (249, 115, 22),
}

# TrueType font for label text. Unlike cv2.putText (ASCII only), this renders
# accented characters (é, è, à, ç, ñ ...) correctly. Falls back gracefully.
_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arialbd.ttf",   # Windows (workstation / laptop)
    "C:/Windows/Fonts/arial.ttf",
]


def _load_font(size):
    """Load a TrueType font at the given size, with fallbacks."""
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()   # last resort (no scaling, ASCII-ish)


# small cache so we don't reload the font file on every frame
_FONT_CACHE = {}


def _get_font(size):
    if size not in _FONT_CACHE:
        _FONT_CACHE[size] = _load_font(size)
    return _FONT_CACHE[size]


def color_name_to_rgb(name):
    """Map a color name to an RGB tuple (defaults to green if unknown)."""
    name = (name or "").lower()
    return _COLORS.get(name) or _EXTRA_COLORS.get(name) or _COLORS["green"]


def DrawBox(image, boxes, color="green", labels=None):
    """
    Drop-in replacement, same signature as before:
        DrawBox(image_rgb, boxes, 'green'|'red', labels=[...])

    Simple, highly visible style:
    - clean rectangle, medium thickness, 1px dark shadow for contrast
    - label: solid square-cornered tag in the box color, white text
    - label text is drawn with PIL so accents (é, è, à...) render correctly
    """
    if boxes is None or len(boxes) == 0:
        return image

    c = color_name_to_rgb(color)
    h, w = image.shape[:2]
    t = max(2, round(min(h, w) / 380))   # line thickness scales with resolution

    # --- 1. rectangles drawn with OpenCV (fast) ---
    out = image.copy()
    label_jobs = []   # (text, font_size, bx1, by1, bx2, by2) for the PIL pass

    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = [int(v) for v in box]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w - 1, x2), min(h - 1, y2)

        cv2.rectangle(out, (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), _DARK, t)
        cv2.rectangle(out, (x1, y1), (x2, y2), c, t, cv2.LINE_AA)

        label = labels[i] if labels and i < len(labels) and labels[i] else ""
        if not label:
            continue

        # font size scales with box width (clamped)
        fsize = int(np.clip((x2 - x1) * 0.11, 16, 34))
        font = _get_font(fsize)
        tw = int(font.getlength(label))
        th = fsize
        pad_x = max(8, fsize // 2)
        pad_y = max(4, fsize // 4)

        # label above the box if there is room, otherwise inside at the top
        if y1 - th - 2 * pad_y - 4 >= 0:
            by2 = y1 - 4
            by1 = by2 - th - 2 * pad_y
        else:
            by1 = y1 + t + 3
            by2 = by1 + th + 2 * pad_y
        bx1 = x1
        bx2 = min(w - 1, bx1 + tw + 2 * pad_x)

        # solid tag (92% opacity) with a 1px shadow, drawn now with OpenCV
        overlay = out.copy()
        cv2.rectangle(overlay, (bx1 + 1, by1 + 1), (bx2 + 1, by2 + 1), _DARK, -1)
        cv2.rectangle(overlay, (bx1, by1), (bx2, by2), c, -1)
        out = cv2.addWeighted(overlay, 0.92, out, 0.08, 0)

        label_jobs.append((label, fsize, bx1 + pad_x, by1 + pad_y))

    # --- 2. text drawn with PIL in one pass (handles accents) ---
    if label_jobs:
        pil = Image.fromarray(out)            # out is RGB → PIL RGB, no conversion
        draw = ImageDraw.Draw(pil)
        for text, fsize, tx, ty in label_jobs:
            draw.text((tx, ty), text, font=_get_font(fsize), fill=_WHITE)
        out = np.array(pil)

    return out