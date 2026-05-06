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


import cv2
import numpy as np
import mediapipe as mp

# 1. INITIALISER MEDIAPIPE (UNE SEULE FOIS AU DÉMARRAGE)
mp_face_detection = mp.solutions.face_detection
# model_selection=0 est optimisé pour les visages proches (caméra d'ordinateur à < 2 mètres)
# model_selection=1 est pour les visages lointains
face_detection = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)


def FacesDetects_from_bytes(image_bytes):
    """
    Lit une image en bytes, l'envoie à MediaPipe et renvoie les visages détectés
    au même format que MTCNN pour assurer la compatibilité.
    """
    # 1. Décoder l'image
    nparr = np.frombuffer(image_bytes, np.uint8)
    image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # 2. Convertir BGR (OpenCV) en RGB (Requis par MediaPipe)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    # 3. Détection avec MediaPipe
    results = face_detection.process(image_rgb)
    
    list_faces = []
    
    # 4. Formater les résultats
    if results.detections:
        h_img, w_img, _ = image_bgr.shape
        
        for detection in results.detections:
            # MediaPipe renvoie des pourcentages (0.0 à 1.0) de la taille de l'image.
            # Il faut les multiplier par la largeur/hauteur réelle en pixels.
            bboxC = detection.location_data.relative_bounding_box
            x = int(bboxC.xmin * w_img)
            y = int(bboxC.ymin * h_img)
            w = int(bboxC.width * w_img)
            h = int(bboxC.height * h_img)
            
            # On recrée un dictionnaire identique à celui de MTCNN
            list_faces.append({
                'box': [x, y, w, h],
                'confidence': detection.score[0]
            })

    return list_faces, image_bgr


def FacesDraw(image, list_faces):
    """
    Dessine les rectangles sur l'image.
    """
    img_copy = image.copy()
    
    for face in list_faces:
        x, y, w, h = face['box']
        
        # MediaPipe peut parfois donner des coordonnées négatives si le visage sort du cadre
        # On s'assure de ne pas avoir de bugs d'affichage
        x, y = max(0, x), max(0, y)
        
        # Dessiner le rectangle vert
        cv2.rectangle(img_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Bonus : Afficher le score de confiance au-dessus du rectangle
        conf = int(face['confidence'] * 100)
        cv2.putText(img_copy, f"{conf}%", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
    return img_copy


url = "images/foule.jpg" 
x  = time.time()
result , image =FacesDetects(url)
image_cadree =  FacesDraw(image , result)

image_bgr = cv2.cvtColor(image_cadree, cv2.COLOR_RGB2BGR)

chemin_enregistrement = "images/resultats/foule.jpg"
succes = cv2.imwrite(chemin_enregistrement, image_bgr)
print(time.time()-x)
