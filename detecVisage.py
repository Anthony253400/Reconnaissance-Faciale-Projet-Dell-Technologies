import cv2
from mtcnn import MTCNN
from  mtcnn.utils.images  import  load_image


def deteceterVisage(url_img ):
    detector  =  MTCNN ( device = "CPU:0" )
    image  =  load_image ( url_img )
    result  =  detector.detect_faces ( image )
    return result , image

def dessinVisage(img, liste_visage):
    img_copy = img.copy()
    for visage in liste_visage:
        x, y, w, h = visage['box']
        cv2.rectangle(img_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return img_copy


url = "images/foule.jpg"
result , image =deteceterVisage(url)
image_cadree = dessinVisage(image , result)

image_bgr = cv2.cvtColor(image_cadree, cv2.COLOR_RGB2BGR)

chemin_enregistrement = "images/resultats/resultat_detection.jpg"
succes = cv2.imwrite(chemin_enregistrement, image_bgr)