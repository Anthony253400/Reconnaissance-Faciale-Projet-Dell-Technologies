import cv2
from mtcnn import MTCNN
from  mtcnn.utils.images  import  load_image


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


url = "images/foule.jpg"
result , image =FacesDetects(url)
image_cadree =  FacesDraw(image , result)

image_bgr = cv2.cvtColor(image_cadree, cv2.COLOR_RGB2BGR)

chemin_enregistrement = "images/resultats/resultat_detection.jpg"
succes = cv2.imwrite(chemin_enregistrement, image_bgr)