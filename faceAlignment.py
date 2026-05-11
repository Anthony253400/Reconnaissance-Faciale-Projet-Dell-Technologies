import cv2
import numpy as np
from detecVisage import FacesDetects_from_bytes
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np



def align_crop(image, listFace):
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
    for detection in listFace.detections:
        keypoints = detection.keypoints
        
        # 0:  left, 1: right, 
        left_eye = keypoints[0]
        right_eye = keypoints[1]

        # Transformation en pixels (im_width et im_height de ton image d'origine)
        left_eye_px = (int(left_eye.x * im_width), int(left_eye.y * im_height))
        right_eye_px = (int(right_eye.x * im_width), int(right_eye.y * im_height))
        dY = right_eye_px[1] - left_eye_px[1]
        dX = right_eye_px[0] - left_eye_px[0]            
        angle = np.degrees(np.arctan2(dY, dX))

        eye_center = ((left_eye_px[0] + right_eye_px[0]) / 2, (right_eye_px[1] + right_eye_px[1]) / 2)

        #rotation 
        M = cv2.getRotationMatrix2D(eye_center, angle, scale=1.0)
        rotated_img = cv2.warpAffine(image, M, (im_width, im_height), flags=cv2.INTER_CUBIC)

        #crop
        bbox = detection.bounding_box
        x, y, bw, bh = int(bbox.origin_x), int(bbox.origin_y), int(bbox.width), int(bbox.height)
    
        face_crop = rotated_img[max(0, y):min(im_height, y+bh), max(0, x):min(im_width, x+bw)]

        face_final = cv2.resize(face_crop, (112, 112))
        face_final_bgr = cv2.cvtColor(face_final, cv2.COLOR_RGB2BGR)
        succes = cv2.imwrite("images/resultats/crop/penche.jpg", face_final_bgr)
        return face_final_bgr






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