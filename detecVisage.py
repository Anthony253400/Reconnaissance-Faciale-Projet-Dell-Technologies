import cv2
from mtcnn import MTCNN
from  mtcnn.utils.images  import  load_image
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
import numpy as np


def FacesDetects_mtcnn(url_img : str ):
    """
    Detects faces in an image using the MTCNN algorithm.

    Args:
        url_img (str): The local path to the image file.

    Returns:
        tuple: 
            - box (list): A list of list in the format [x1, y1, x2, y2] which contains the rectangles of the face.
            - result (list): A list of dictionaries returned by MTCNN. Each dictionary contains 
              'box', 'confidence', and 'keypoints' for each detected face.
            - image (numpy.ndarray): The loaded image data in RGB format.
    """
    detector  =  MTCNN ( device = "CPU:0" )
    image  =  load_image ( url_img )
    result  =  detector.detect_faces ( image )
    box = [[f['box'][0], f['box'][1], f['box'][0] + f['box'][2], f['box'][1] + f['box'][3]] for f in result]
    return box , result , image

def FacesDetects_mediapipe(url_img : str , model_path='model/blaze_face_short_range.tflite'):
    """
    Detects faces in an image using the blazeFace(Mediapipe) model.

    Args:
        url_img (str): The local path to the image file.

    Returns:
        tuple: 
            - box (list): A list of list in the format [x1, y1, x2, y2] which contains the rectangles of the face.
            - result (list): The raw object returned by MediaPipe containing the native detection data, bounding boxes, and scores.
            - image (numpy.ndarray): The loaded image data in RGB format.
    """
    image  =  load_image ( url_img )
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
        return box , detection_result , image
    
def FacesDetects_from_bytes(image_bytes, method , detector):
    """
    Détecte les visages à partir de bytes en choisissant la méthode.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    
    box = []
    if method == "mtcnn":
        detector = MTCNN(device="CPU:0")
        result = detector.detect_faces(image_rgb)
        box = [[f['box'][0], f['box'][1], f['box'][0] + f['box'][2], f['box'][1] + f['box'][3]] for f in result]
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
    else:
        return None, None, None

def FacesDraw(image, list_boxes):
    """
    Draws bounding boxes around detected faces on the image.
    
    Args:
        - image (numpy.ndarray): The original image data in RGB format.
        - list_boxes (list): A list of list in the format [x1, y1, x2, y2] which contains the rectangles of the face.

    Returns:
        - img_copy (numpy.ndarray): A copy of the input image with bounding boxes drawn.

    """
    img_copy = image.copy()
    for box in list_boxes:
        x1, y1, x2, y2 = box
        cv2.rectangle(img_copy, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
    return img_copy





if __name__ == "__main__" :
    url = "images/anthony.jpg" 
    box_mtcnn , y , image = FacesDetects_mtcnn(url)
    box_mediapipe , y , image = FacesDetects_mediapipe(url)

    image_mtcnn =  FacesDraw(image , box_mtcnn)
    image_mediapipe =  FacesDraw(image , box_mediapipe)

    image_mtcnn = cv2.cvtColor(image_mtcnn, cv2.COLOR_RGB2BGR)
    image_mediapipe = cv2.cvtColor(image_mediapipe, cv2.COLOR_RGB2BGR)

    succes = cv2.imwrite("images/resultats/anthony_mtcnn.jpg", image_mtcnn)
    succes = cv2.imwrite("images/resultats/anthony_mediapipe.jpg", image_mediapipe)

    # Byte
    model_path_blazeface='model/blaze_face_short_range.tflite'

    base_options = python.BaseOptions(model_asset_path=model_path_blazeface)
    options = vision.FaceDetectorOptions(base_options=base_options)
    my_global_detector = vision.FaceDetector.create_from_options(options)

    with open("images/anthony.jpg", "rb") as f:
        image_bytes = f.read()

    boxes, result, img_rgb = FacesDetects_from_bytes(image_bytes, method="mediapipe" , detector=my_global_detector # <-- L'ajout crucial est ici
    )

    if img_rgb is not None:
        img_avec_cadres_rgb = FacesDraw(img_rgb, boxes)
    
        img_final_bgr = cv2.cvtColor(img_avec_cadres_rgb, cv2.COLOR_RGB2BGR)
    
        output_path = "images/resultats/anthony_bytes_test.jpg"
        cv2.imwrite(output_path, img_final_bgr)

