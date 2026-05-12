import cv2

def DrawBox(image, list_boxes):
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
        cv2.rectangle(img_copy, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
    return img_copy
