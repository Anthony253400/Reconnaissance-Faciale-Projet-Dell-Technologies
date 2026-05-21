import cv2
import matplotlib.pyplot as plt
import numpy as np
from DrawBox import DrawBox ,color_name_to_rgb



def BodyDetect(url_img : str , detector ):
    img = cv2.imread(url_img)
    h, w, _ = img.shape

    blob = cv2.dnn.blobFromImage(img, 1/255.0, (640, 640), swapRB=True, crop=False)
    detector.setInput(blob)
    outputs = detector.forward()
    predictions = np.squeeze(outputs[0]).T

    box = []
    confidences = []
    
    for row in predictions:
        score = row[4:].max() 
        if score > 0.7:
            class_id = row[4:].argmax()
            if class_id == 0: # Classe 0 = Personne
                cx, cy, rw, rh = row[0:4]
                x1 = int((cx - rw/2) * (w / 640))
                y1 = int((cy - rh/2) * (h / 640))
                width = int(rw * (w / 640))
                height = int(rh * (h / 640))
                
                box.append([x1, y1, width, height])
                confidences.append(float(score))
    #supr box qui ce chevauche            
    indices = cv2.dnn.NMSBoxes(box, confidences, score_threshold=0.7, nms_threshold=0.4)
    #[x1, y1, x2, y2]
    boxes = []
    final_confidences = []
    for i in indices:
        x, y, bw, bh = box[i]
        boxes.append([x, y, x + bw, y + bh])
        final_confidences.append(confidences[i])
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) 
    return boxes, final_confidences ,img_rgb
import cv2
import numpy as np
import time  # Ne pas oublier cet import

def BodyDetect_from_frame(img, detector):
    # Démarrage du chronomètre global
    t_start = time.perf_counter()

    # 1. Préparation de l'image (Blob)
    h, w, _ = img.shape
    blob = cv2.dnn.blobFromImage(img, 1/255.0, (640, 640), swapRB=True, crop=False)
    detector.setInput(blob)
    
    t_blob = time.perf_counter()
    print(f"[Timer] 1. Préparation du blob : {(t_blob - t_start) * 1000:.2f} ms")

    # 2. L'inférence (Le réseau de neurones)
    outputs = detector.forward()
    predictions = np.squeeze(outputs[0]).T
    
    t_infer = time.perf_counter()
    print(f"[Timer] 2. Inférence YOLO (forward) : {(t_infer - t_blob) * 1000:.2f} ms")

    # 3. Le tri des propositions
    box = []
    confidences = []
    for row in predictions:
        score = row[4:].max()
        if score > 0.5:
            class_id = row[4:].argmax()
            if class_id == 0:
                cx, cy, rw, rh = row[0:4]
                x1 = int((cx - rw/2) * (w / 640))
                y1 = int((cy - rh/2) * (h / 640))
                width = int(rw * (w / 640))
                height = int(rh * (h / 640))
                box.append([x1, y1, width, height])
                confidences.append(float(score))
                
    t_loop = time.perf_counter()
    print(f"[Timer] 3. Tri et filtrage : {(t_loop - t_infer) * 1000:.2f} ms")

    # 4. Le nettoyage (NMS)
    indices = cv2.dnn.NMSBoxes(box, confidences, score_threshold=0.5, nms_threshold=0.4)
    
    t_nms = time.perf_counter()
    print(f"[Timer] 4. Nettoyage NMS : {(t_nms - t_loop) * 1000:.2f} ms")

    # 5. Formatage final et conversion de couleur
    boxes = []
    final_confidences = []
    if len(indices) > 0:
        for i in indices.flatten():
            x, y, bw, bh = box[i]
            boxes.append([x, y, x + bw, y + bh])
            final_confidences.append(confidences[i])
    
    t_end = time.perf_counter()
    print(f"[Timer] 5. Formatage et conv. RGB : {(t_end - t_nms) * 1000:.2f} ms")
    
    # Temps total
    print(f"[Timer] ---> TEMPS TOTAL DE LA FONCTION : {(t_end - t_start) * 1000:.2f} ms")
    print("-" * 50) # Ligne de séparation pour y voir clair dans la console

    return boxes, final_confidences





if __name__ == "__main__" :
        net = cv2.dnn.readNetFromONNX("model/yolov8n.onnx")
        image_path = 'images/anthony_body2.jpg'
        output_path =('images/resultats/anthony_body_detecte_NOIR.jpg')

        box ,confidences ,image =BodyDetect(image_path,net)
        image_draw =  DrawBox(image , box ,"black")
        image_draw = cv2.cvtColor(image_draw, cv2.COLOR_RGB2BGR)
        succes = cv2.imwrite(output_path, image_draw)

        #BYTE
        with open("images/anthony_body3.jpg", "rb") as f:
            image_bytes = f.read()

        boxes, confidences, image = BodyDetect_from_bytes(image_bytes, net)

        image_draw = DrawBox(image, boxes, "green")
        image_draw = cv2.cvtColor(image_draw, cv2.COLOR_RGB2BGR)
        cv2.imwrite('images/resultats/anthony_body_detecte_BYTES.jpg', image_draw)
  


