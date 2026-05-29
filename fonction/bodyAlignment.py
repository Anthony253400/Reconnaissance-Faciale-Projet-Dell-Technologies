import cv2
import numpy as np

def body_crop(image, boxes):
    """ Crops detected bodies from the image based on provided bounding boxes.
    Args:
        image (numpy.ndarray): The input image in RGB format.
        boxes (list): A list of bounding boxes in the format [x1, y1, x2, y2].
    Returns:
        list: A list of cropped body images in BGR format, resized to (128, 256).
    """

    im_height, im_width = image.shape[:2]
    crops = []

    for box in boxes:
        x1, y1, x2, y2 = box
        crop = image[max(0, y1):min(im_height, y2), max(0, x1):min(im_width, x2)]
        crop_resized = cv2.resize(crop, (128, 256))
        crop_bgr = cv2.cvtColor(crop_resized, cv2.COLOR_RGB2BGR)
        crops.append(crop_bgr)

    return crops 
