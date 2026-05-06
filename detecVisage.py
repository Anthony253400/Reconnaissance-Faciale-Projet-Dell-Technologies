import cv2
from mtcnn import MTCNN
from  mtcnn.utils.images  import  load_image
import time
import numpy as np


def FacesDetects(url_img : str ):
    """
    Detects faces in an image using the MTCNN algorithm.

    Args:
        url_img (str): The local path to the image file.

    Returns:
        tuple: 
            - result (list): A list of dictionaries returned by MTCNN. Each dictionary contains 
              'box', 'confidence', and 'keypoints' for each detected face.
            - image (numpy.ndarray): The loaded image data in RGB format.
    """
    detector  =  MTCNN ( device = "CPU:0" )
    image  =  load_image ( url_img )
    result  =  detector.detect_faces ( image )
    return result , image

def FacesDetects_from_bytes(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    detector = MTCNN()
    result = detector.detect_faces(image_rgb)
    
    return result, image_rgb

def FacesDraw(image, list_faces):
    """
    Draws bounding boxes around detected faces on the image.
    
    Args:
        - image (numpy.ndarray): The original image data in RGB format.
        - result (list): A list of dictionaries returned by MTCNN. Each dictionary contains 
        'box', 'confidence', and 'keypoints' for each detected face.

    Returns:
        - img_copy (numpy.ndarray): A copy of the input image with bounding boxes drawn.

    """
    img_copy = image.copy()
    for face in list_faces:
        x, y, w, h = face['box']
        cv2.rectangle(img_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return img_copy


url = "images/anthony.jpg" 
x  = time.time()
result , image =FacesDetects(url)
image_cadree =  FacesDraw(image , result)

image_bgr = cv2.cvtColor(image_cadree, cv2.COLOR_RGB2BGR)

chemin_enregistrement = "images/resultats/anthony.jpg"
succes = cv2.imwrite(chemin_enregistrement, image_bgr)
print(time.time()-x)
