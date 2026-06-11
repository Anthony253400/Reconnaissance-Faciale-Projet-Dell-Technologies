import cv2
import matplotlib.pyplot as plt
import numpy as np
import time
import sys 
sys.path.append('../')

from fonction.DrawBox import DrawBox ,color_name_to_rgb



def BodyDetect(url_img : str , detector ):
    """
    Detects human bodies in an image using a YOLOv8 ONNX model.

    Args:
        url_img (str): Path to the input image.
        detector: Pre-initialized cv2.dnn network (YOLOv8 ONNX).

    Returns:
        tuple:
            - boxes (list): A list of lists in the format [x1, y1, x2, y2].
            - final_confidences (list): Confidence scores for each detected body.
            - img_rgb (numpy.ndarray): The loaded image in RGB format.
    """
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




def BodyDetect_from_frame(image, model):
    """
    Detects bodies (class 0 = person) in an RGB frame using YOLOv8 ONNX.

    Returns:
        tuple:
            - boxes (list): bounding boxes [x1, y1, x2, y2] in the ORIGINAL
              image coordinate space.
            - final_confidences (list): confidence per detection.
    """
    t_start = time.perf_counter()

    backend, session = model
    h, w, _ = image.shape

    # YOLO input size used here
    INPUT = 320
    img_resized = cv2.resize(image, (INPUT, INPUT))
    blob = img_resized.astype(np.float32) / 255.0
    blob = np.transpose(blob, (2, 0, 1))
    blob = np.expand_dims(blob, axis=0)

    if backend == 'onnx':
        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: blob})
        predictions = np.squeeze(outputs[0]).T
    elif backend == 'opencv':
        blob_cv = cv2.dnn.blobFromImage(image, 1/255.0, (INPUT, INPUT), swapRB=True, crop=False)
        session.setInput(blob_cv)
        outputs = session.forward()
        predictions = np.squeeze(outputs[0]).T

    # scale factors from the INPUT grid back to the original frame
    sx = w / INPUT
    sy = h / INPUT

    box = []
    confidences = []
    for row in predictions:
        score = row[4:].max()
        if score > 0.5:
            class_id = row[4:].argmax()
            if class_id == 0:  # person
                cx, cy, rw, rh = row[0:4]
                x1 = int((cx - rw / 2) * sx)
                y1 = int((cy - rh / 2) * sy)
                bw = int(rw * sx)
                bh = int(rh * sy)
                box.append([x1, y1, bw, bh])
                confidences.append(float(score))

    indices = cv2.dnn.NMSBoxes(box, confidences, score_threshold=0.5, nms_threshold=0.4)

    boxes = []
    final_confidences = []
    if len(indices) > 0:
        for i in indices.flatten():
            x, y, bw, bh = box[i]
            boxes.append([x, y, x + bw, y + bh])
            final_confidences.append(confidences[i])

    print(f"[Timer] BodyDetect : {(time.perf_counter() - t_start)*1000:.1f} ms")
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
