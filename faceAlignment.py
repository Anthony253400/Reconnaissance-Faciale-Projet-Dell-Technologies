import cv2
import numpy as np
from detecVisage import FacesDetects_from_bytes
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

def align_crop(image, result, method="mediapipe"):
    crops = []

    if method == "mtcnn":
        for face in result:
            kp = face['keypoints']
            left_eye  = kp['left_eye']
            right_eye = kp['right_eye']
            box = face['box']  # [x, y, w, h]

            # ton alignement existant avec ces coordonnées
            crop = _do_alignment(image, left_eye, right_eye, box)
            crops.append(crop)

    elif method == "mediapipe":
        for d in result.detections:
            # ton code actuel MediaPipe
            ...

    return crops




def align_crop(image, listFace, method):
    """
    aligns and cuts out the face
    Args:
        image_bytes : Raw image data
        listFace (list): The raw object returned by MediaPipe library. Containing the native detection data, bounding boxes, and scores.

    Returns:
        tuple: 
            - face_final_bgr (numpy.ndarray): face align and crop.
    """
    im_height, im_width = image.shape[:2]
    crops = []
    if method == "mtcnn":
        for face in result:
            kp = face['keypoints']
            left_eye  = kp['left_eye']
            right_eye = kp['right_eye']
            box = face['box']

            crop = _do_alignment(image, left_eye, right_eye, box)
            crops.append(crop)


    if method == "mediapipe":
        for detection in listFace.detections:
            keypoints = detection.keypoints
            bbox = detection.bounding_box
            
            # 1. On calcule d'abord la boîte de délimitation (sans appliquer l'échelle si elle a déjà été appliquée avant)
            x, y, bw, bh = int(bbox.origin_x), int(bbox.origin_y), int(bbox.width), int(bbox.height)
            
            # 2. On ajoute une marge confortable (ex: 20%) pour ne pas couper le visage pendant la rotation
            margin_x = int(bw * 0.2)
            margin_y = int(bh * 0.2)
            
            crop_x1 = max(0, x - margin_x)
            crop_y1 = max(0, y - margin_y)
            crop_x2 = min(im_width, x + bw + margin_x)
            crop_y2 = min(im_height, y + bh + margin_y)

            # 3. ON ROGNE AVANT LA ROTATION (L'image passe de 1920x1080 à par exemple 200x200)
            face_region = image[crop_y1:crop_y2, crop_x1:crop_x2]
            
            if face_region.size == 0:
                continue

            # 4. On ajuste les coordonnées des yeux pour qu'elles correspondent au petit crop
            left_eye_px = (int(keypoints[0].x * im_width) - crop_x1, int(keypoints[0].y * im_height) - crop_y1)
            right_eye_px = (int(keypoints[1].x * im_width) - crop_x1, int(keypoints[1].y * im_height) - crop_y1)

            # 5. Calcul de l'angle
            dY = right_eye_px[1] - left_eye_px[1]
            dX = right_eye_px[0] - left_eye_px[0]
            angle = np.degrees(np.arctan2(dY, dX))
            
            # 6. Rotation uniquement du petit patch (Très rapide, et INTER_LINEAR suffit amplement)
            eye_center = ((left_eye_px[0] + right_eye_px[0]) / 2, (left_eye_px[1]  + right_eye_px[1]) / 2)
            M = cv2.getRotationMatrix2D(eye_center, angle, scale=1.0)
            
            patch_h, patch_w = face_region.shape[:2]
            rotated_patch = cv2.warpAffine(face_region, M, (patch_w, patch_h), flags=cv2.INTER_LINEAR)

            # 7. Recadrage final pour enlever la marge (on recentre sur la taille d'origine du visage)
            final_x1 = max(0, int(left_eye_px[0] - bw/2))
            final_y1 = max(0, int(left_eye_px[1] - bh/2)) # Approximatif, basé sur les yeux
            
            # Pour faire simple et robuste, on utilise les dimensions originales bw, bh sur le centre des yeux rotatés
            center_x, center_y = patch_w // 2, patch_h // 2
            half_w, half_h = bw // 2, bh // 2
            
            face_final = rotated_patch[max(0, center_y - half_h):min(patch_h, center_y + half_h), 
                                       max(0, center_x - half_w):min(patch_w, center_x + half_w)]

            # Redimensionnement et conversion pour ArcFace
            if face_final.size > 0:
                face_final = cv2.resize(face_final, (112, 112))
                face_final_bgr = cv2.cvtColor(face_final, cv2.COLOR_RGB2BGR)
                crops.append(face_final_bgr)

    return crops






if __name__ == "__main__" :
    model_path_blazeface='model/blaze_face_short_range.tflite'

    base_options = python.BaseOptions(model_asset_path=model_path_blazeface)
    options = vision.FaceDetectorOptions(base_options=base_options)
    my_global_detector = vision.FaceDetector.create_from_options(options)

    with open("images/penche.jpg", "rb") as f:
        image_bytes = f.read()

    boxes, result, img_rgb = FacesDetects_from_bytes(image_bytes, method="mediapipe" , detector=my_global_detector # <-- L'ajout crucial est ici
    )
    align_crop(img_rgb , result)
    print("TOto")