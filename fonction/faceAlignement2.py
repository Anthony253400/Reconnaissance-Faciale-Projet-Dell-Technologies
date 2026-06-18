import cv2
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# ArcFace canonical 5-point template for a 112x112 crop
# order: left eye, right eye, nose, left mouth corner, right mouth corner
_ARC_TEMPLATE_5 = np.array([
    [38.2946, 51.6963],
    [73.5318, 51.5014],
    [56.0252, 71.7366],
    [41.5493, 92.3655],
    [70.7299, 92.2041],
], dtype=np.float32)

# 4-point template used with MediaPipe, which only provides the mouth center
# (not the two mouth corners): left eye, right eye, nose, mouth center.
_ARC_TEMPLATE_4 = np.array(
    [_ARC_TEMPLATE_5[0], _ARC_TEMPLATE_5[1], _ARC_TEMPLATE_5[2],
     (_ARC_TEMPLATE_5[3] + _ARC_TEMPLATE_5[4]) / 2.0],
    dtype=np.float32,
)


def align_crop(image, listFace, method):
    """
    Aligns and crops each detected face onto the ArcFace 112x112 template.

    Args:
        image (numpy.ndarray): The source image (RGB).
        listFace: The raw detection object returned by MediaPipe.
        method (str): "mtcnn" or "mediapipe".

    Returns:
        list[numpy.ndarray]: aligned 112x112 face crops, kept in the SAME color
        space as the input image (RGB). No RGB<->BGR conversion is done here;
        channel consistency is handled at load time and in get_embedding.
    """
    im_height, im_width = image.shape[:2]
    crops = []

    if method == "mediapipe":
        for detection in listFace.detections:
            keypoints = detection.keypoints

            # MediaPipe FaceDetector keypoint order:
            # 0 = right eye, 1 = left eye, 2 = nose, 3 = mouth, 4/5 = ears
            eye_a = (keypoints[0].x * im_width, keypoints[0].y * im_height)
            eye_b = (keypoints[1].x * im_width, keypoints[1].y * im_height)
            nose  = (keypoints[2].x * im_width, keypoints[2].y * im_height)
            mouth = (keypoints[3].x * im_width, keypoints[3].y * im_height)

            # The eye with the smaller x must map to the LEFT template point.
            # Otherwise the transform would need a horizontal mirror, which a
            # similarity transform cannot do, so it applies a 180 rotation
            # instead -> upside-down face -> collapsed embeddings.
            eye_left, eye_right = (eye_a, eye_b) if eye_a[0] <= eye_b[0] else (eye_b, eye_a)

            # Guard against degenerate cases (eyes detected at the same point).
            eye_dist = float(np.hypot(eye_right[0] - eye_left[0],
                                      eye_right[1] - eye_left[1]))
            if eye_dist < 1.0:
                continue

            # Similarity transform (rotation + uniform scale + translation)
            # from the detected landmarks to the canonical ArcFace template.
            src = np.array([eye_left, eye_right, nose, mouth], dtype=np.float32)
            M, _ = cv2.estimateAffinePartial2D(src, _ARC_TEMPLATE_4)
            if M is None:
                continue

            # Warp directly onto the 112x112 template. Output stays in the input
            # color space (RGB).
            face_final = cv2.warpAffine(image, M, (112, 112), borderValue=0)
            crops.append(face_final)

    return crops