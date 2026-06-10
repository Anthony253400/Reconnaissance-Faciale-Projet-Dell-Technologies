import cv2
import numpy as np

# Color palette: vivid but clean (the pipeline works in RGB)
_COLORS = {
    "green": (16, 185, 129),   # face — emerald green
    "red":   (239, 68, 68),    # body — coral red
}
_DARK = (15, 15, 15)
_WHITE = (255, 255, 255)


def DrawBox(image, boxes, color="green", labels=None):
    """
    Drop-in replacement, same signature as before:
        DrawBox(image_rgb, boxes, 'green'|'red', labels=[...])

    Simple, highly visible style:
    - clean rectangle, medium thickness, 1px dark shadow for contrast
    - label: solid square-cornered tag in the box color, white text
    """
    if boxes is None or len(boxes) == 0:
        return image

    c = _COLORS.get(color, _COLORS["green"])
    h, w = image.shape[:2]
    t = max(2, round(min(h, w) / 380))   # line thickness scales with resolution
    out = image.copy()

    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = [int(v) for v in box]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w - 1, x2), min(h - 1, y2)

        # 1px shadow under the line, then the colored line: contrast without bulk
        cv2.rectangle(out, (x1 + 1, y1 + 1), (x2 + 1, y2 + 1), _DARK, t)
        cv2.rectangle(out, (x1, y1), (x2, y2), c, t, cv2.LINE_AA)

        label = labels[i] if labels and i < len(labels) and labels[i] else ""
        if not label:
            continue

        # font size scales with box width
        fs = float(np.clip((x2 - x1) / 300.0, 0.5, 0.8))
        ft = max(1, int(round(fs * 2)))
        (tw, th), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, fs, ft)
        pad_x = max(8, int(10 * fs))
        pad_y = max(5, int(7 * fs))

        # label above the box if there is room, otherwise inside at the top
        if y1 - th - 2 * pad_y - baseline - 4 >= 0:
            by2 = y1 - 4
            by1 = by2 - th - 2 * pad_y - baseline
        else:
            by1 = y1 + t + 3
            by2 = by1 + th + 2 * pad_y + baseline
        bx1 = x1
        bx2 = min(w - 1, bx1 + tw + 2 * pad_x)

        # solid tag (92% opacity) with a 1px shadow
        overlay = out.copy()
        cv2.rectangle(overlay, (bx1 + 1, by1 + 1), (bx2 + 1, by2 + 1), _DARK, -1)
        cv2.rectangle(overlay, (bx1, by1), (bx2, by2), c, -1)
        out = cv2.addWeighted(overlay, 0.92, out, 0.08, 0)

        org = (bx1 + pad_x, by2 - pad_y - baseline // 2)
        cv2.putText(out, label, org, cv2.FONT_HERSHEY_SIMPLEX,
                    fs, _WHITE, ft, cv2.LINE_AA)

    return out