import math

def distance_box(box1, box2):
    """
    Calculate the distance between the centers of two bounding boxes.
    
    Args:        box1/box2 : A list or tuple representing the first bounding box (x1, y1, x2, y2).
    Returns:     (float) : The distance between the centers of the two bounding boxes.
    """
    cx1 = (box1[0] + box1[2]) / 2
    cy1 = (box1[1] + box1[3]) / 2
    cx2 = (box2[0] + box2[2]) / 2
    cy2 = (box2[1] + box2[3]) / 2

    return math.hypot(cx1 - cx2, cy1 - cy2)