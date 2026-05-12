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

def DrawBox(image, list_boxes , color):
    """
    Draws bounding boxes around detected faces on the image.
    
    Args:
        - image (numpy.ndarray): The original image data in RGB format.
        - list_boxes (list): A list of list in the format [x1, y1, x2, y2] which contains the rectangles of the face or body.

    Returns:
        - img_copy (numpy.ndarray): A copy of the input image with bounding boxes drawn.

    """
    img_copy = image.copy()
    for box in list_boxes:
        x1, y1, x2, y2 = box
        cv2.rectangle(img_copy, (int(x1), int(y1)), (int(x2), int(y2)), color_name_to_rgb(color), 2)
    return img_copy
