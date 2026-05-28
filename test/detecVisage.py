from mtcnn import MTCNN
from mtcnn.utils.images import load_image
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import cv2
from DrawBox import DrawBox


def FacesDetects_mtcnn(url_img: str):
    """
    Detects faces in an image using the MTCNN algorithm.

    Args:
        url_img (str): The local path to the image file.

    Returns:
        tuple:
            - box (list): A list of list in the format [x1, y1, x2, y2].
            - result (list): List of dicts with 'box', 'confidence', 'keypoints'.
            - image (numpy.ndarray): The loaded image in RGB format.
    """
    detector = MTCNN(device="CPU:0")
    image = load_image(url_img)
    result = detector.detect_faces(image)
    box = [
        [f['box'][0], f['box'][1], f['box'][0] + f['box'][2], f['box'][1] + f['box'][3]]
        for f in result
    ]
    return box, result, image


def FacesDetects_mediapipe(url_img: str, model_path='model/blaze_face_short_range.tflite'):
    """
    Detects faces in an image using BlazeFace (MediaPipe).

    Args:
        url_img (str): The local path to the image file.

    Returns:
        tuple:
            - box (list): A list of list in the format [x1, y1, x2, y2].
            - result: Raw MediaPipe detection object.
            - image (numpy.ndarray): The loaded image in RGB format.
    """
    image = load_image(url_img)
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.FaceDetectorOptions(base_options=base_options)
    box = []

    with vision.FaceDetector.create_from_options(options) as detector:
        mp_image = mp.Image.create_from_file(url_img)
        detection_result = detector.detect(mp_image)
        if detection_result.detections:
            for d in detection_result.detections:
                bbox = d.bounding_box
                box.append([
                    bbox.origin_x,
                    bbox.origin_y,
                    bbox.origin_x + bbox.width,
                    bbox.origin_y + bbox.height
                ])
        return box, detection_result, image


def FacesDetects_from_bytes(image_bytes, method, detector, numpy=False):
    """
    Detects faces from bytes or numpy array.

    Args:
        image_bytes: Raw bytes or numpy BGR array (si numpy=True).
        method (str): 'mtcnn' ou 'mediapipe'.
        detector: Instance pré-initialisée du détecteur.
        numpy (bool): Si True, image_bytes est déjà un numpy array BGR.

    Returns:
        tuple:
            - box (list): [x1, y1, x2, y2] par visage détecté.
            - result: Objet natif MTCNN ou MediaPipe.
            - image_rgb (numpy.ndarray): Image en RGB format.
    """
    # --- Décodage ---
    if numpy:
        image_bgr = image_bytes  # déjà un numpy array BGR
    else:
        nparr = np.frombuffer(image_bytes, np.uint8)
        image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # FIX : conversion BGR → RGB correcte (était: image_rgb = image_bytes, bug critique)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    box = []

    if method == "mtcnn":
        result = detector.detect_faces(image_rgb)
        box = [
            [f['box'][0], f['box'][1], f['box'][0] + f['box'][2], f['box'][1] + f['box'][3]]
            for f in result
        ]
        return box, result, image_rgb

    elif method == "mediapipe":
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        detection_result = detector.detect(mp_image)
        if detection_result.detections:
            for d in detection_result.detections:
                bbox = d.bounding_box
                box.append([
                    bbox.origin_x,
                    bbox.origin_y,
                    bbox.origin_x + bbox.width,
                    bbox.origin_y + bbox.height
                ])
        return box, detection_result, image_rgb

    return None, None, None


if __name__ == "__main__":
    url = "images/foule.jpg"
    box_mtcnn, _, image = FacesDetects_mtcnn(url)
    box_mediapipe, _, image = FacesDetects_mediapipe(url)

    image_mtcnn = DrawBox(image, box_mtcnn, 'red')
    image_mediapipe = DrawBox(image, box_mediapipe, 'red')

    image_mtcnn = cv2.cvtColor(image_mtcnn, cv2.COLOR_RGB2BGR)
    image_mediapipe = cv2.cvtColor(image_mediapipe, cv2.COLOR_RGB2BGR)

    cv2.imwrite("images/resultats/anthony_mtcnn.jpg", image_mtcnn)
    cv2.imwrite("images/resultats/anthony_mediapipe.jpg", image_mediapipe)
