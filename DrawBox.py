import cv2

def color_name_to_rgb(color_name: str):
    """
    Converts a color name to its RGB tuple.

    Args:
        color_name (str): Color name in English .

    Returns:
        tuple: RGB color tuple (R, G, B). Returns white (255, 255, 255) if not found.
    """
    colors = {
        "red":     (255, 0, 0),
        "green":   (0, 255, 0),
        "blue":    (0, 0, 255),
        "yellow":  (255, 255, 0),
        "orange":  (255, 165, 0),
        "purple":  (128, 0, 128),
        "pink":    (255, 192, 203),
        "cyan":    (0, 255, 255),
        "white":   (255, 255, 255),
        "black":   (0, 0, 0),
        "gray":    (128, 128, 128),
        "brown":   (165, 42, 42),
    }
    return colors.get(color_name.lower(), (255, 255, 255))

def DrawBox(image, list_boxes, color, labels=None):
    """
    Draws bounding boxes and optional labels above each box.

    Args:
        - image (numpy.ndarray): Image in RGB format.
        - list_boxes (list): List of [x1, y1, x2, y2].
        - color (str): Box color name.
        - labels (list[str], optional): Names to display above each box.

    Returns:
        - img_copy (numpy.ndarray): Image with boxes and labels drawn.
    """
    img_copy = image.copy()
    rgb = color_name_to_rgb(color)

    for i, box in enumerate(list_boxes):
        x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])

        # Boîte
        cv2.rectangle(img_copy, (x1, y1), (x2, y2), rgb, 2)

        # Label
        if labels and i < len(labels) and labels[i]:
            label = labels[i]
            font       = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness  = 1

            (tw, th), baseline = cv2.getTextSize(label, font, font_scale, thickness)

            # Fond coloré derrière le texte
            pad = 4
            ty = y1 - th - pad * 2  # position du fond
            if ty < 0:              # si trop haut, passe sous la boîte
                ty = y2 + pad

            cv2.rectangle(img_copy,
                          (x1, ty),
                          (x1 + tw + pad * 2, ty + th + pad * 2),
                          rgb, -1)  # rempli

            # Texte en noir pour contraste
            cv2.putText(img_copy, label,
                        (x1 + pad, ty + th + pad),
                        font, font_scale, (0, 0, 0), thickness, cv2.LINE_AA)

    return img_copy