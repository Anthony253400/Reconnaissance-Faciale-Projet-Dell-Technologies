from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
import numpy as np
from DrawBox import DrawBox



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

def BodyDetect_from_bytes(image_bytes, detector):
    """
    Detects human bodies from raw image bytes using a YOLOv8 ONNX model.

    Args:
        image_bytes: Raw image data (bytes received from API).
        detector: Pre-initialized cv2.dnn network (YOLOv8 ONNX).

    Returns:
        tuple:
            - boxes (list): A list of lists in the format [x1, y1, x2, y2].
            - final_confidences (list): Confidence scores for each detected body.
            - img_rgb (numpy.ndarray): The loaded image in RGB format.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # BGR
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
            if class_id == 0:
                cx, cy, rw, rh = row[0:4]
                x1 = int((cx - rw/2) * (w / 640))
                y1 = int((cy - rh/2) * (h / 640))
                width = int(rw * (w / 640))
                height = int(rh * (h / 640))

                box.append([x1, y1, width, height])
                confidences.append(float(score))

    indices = cv2.dnn.NMSBoxes(box, confidences, score_threshold=0.7, nms_threshold=0.4)

    boxes = []
    final_confidences = []
    for i in indices:
        x, y, bw, bh = box[i]
        boxes.append([x, y, x + bw, y + bh])
        final_confidences.append(confidences[i])

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return boxes, final_confidences, img_rgb



if __name__ == "__main__" :
        net = cv2.dnn.readNetFromONNX("model/yolov8n.onnx")
        image_path = 'images/anthony_body2.jpg'
        output_path =('images/resultats/anthony_body_detecte_BYTES.jpg')

        box ,confidences ,image =BodyDetect(image_path,net)
        image_draw =  DrawBox(image , box)
        image_draw = cv2.cvtColor(image_draw, cv2.COLOR_RGB2BGR)
        succes = cv2.imwrite(output_path, image_draw)

        #BYTE
        with open("images/anthony_body3.jpg", "rb") as f:
            image_bytes = f.read()

        boxes, confidences, image = BodyDetect_from_bytes(image_bytes, net)

        image_draw = DrawBox(image, boxes)
        image_draw = cv2.cvtColor(image_draw, cv2.COLOR_RGB2BGR)
        cv2.imwrite(output_path, image_draw)
  


