import cv2
import numpy as np
import time

INPUT_SIZE = 320  # taille d'entrée du modèle ONNX (yolov8n_320.onnx)


def BodyDetect(url_img: str, detector):
    img = cv2.imread(url_img)
    h, w, _ = img.shape

    blob = cv2.dnn.blobFromImage(img, 1 / 255.0, (640, 640), swapRB=True, crop=False)
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
                x1 = int((cx - rw / 2) * (w / 640))
                y1 = int((cy - rh / 2) * (h / 640))
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


def BodyDetect_from_frame(img, model):
    t_start = time.perf_counter()

    backend, session = model
    h, w, _ = img.shape

    # 1. Préparation du blob
    img_resized = cv2.resize(img, (INPUT_SIZE, INPUT_SIZE))
    blob = img_resized.astype(np.float32) / 255.0   # [0, 1]
    blob = blob[..., ::-1]                           # BGR → RGB
    blob = np.transpose(blob, (2, 0, 1))             # HWC → CHW
    blob = np.expand_dims(blob, axis=0)              # CHW → NCHW

    # 2. Inférence
    if backend == 'onnx':
        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: blob})
        predictions = np.squeeze(outputs[0]).T

    elif backend == 'opencv':
        blob_cv = cv2.dnn.blobFromImage(img, 1 / 255.0, (INPUT_SIZE, INPUT_SIZE), swapRB=True, crop=False)
        session.setInput(blob_cv)
        outputs = session.forward()
        predictions = np.squeeze(outputs[0]).T

    # 3. Filtrage — FIX : scale propre via INPUT_SIZE, suppression du hack *2
    box = []
    confidences = []
    scale_x = w / INPUT_SIZE
    scale_y = h / INPUT_SIZE

    for row in predictions:
        score = row[4:].max()
        if score > 0.5:
            class_id = row[4:].argmax()
            if class_id == 0:
                cx, cy, rw, rh = row[0:4]
                x1 = int((cx - rw / 2) * scale_x)
                y1 = int((cy - rh / 2) * scale_y)
                bw = int(rw * scale_x)
                bh = int(rh * scale_y)
                box.append([x1, y1, bw, bh])
                confidences.append(float(score))

    # 4. NMS
    boxes = []
    final_confidences = []
    if len(box) > 0:
        indices = cv2.dnn.NMSBoxes(box, confidences, score_threshold=0.5, nms_threshold=0.4)
        if len(indices) > 0:
            for i in indices.flatten():
                x, y, bw, bh = box[i]
                boxes.append([x, y, x + bw, y + bh])
                final_confidences.append(confidences[i])

    t_end = time.perf_counter()
    print(f"[BodyDetect] {(t_end - t_start)*1000:.1f}ms — {len(boxes)} personne(s)")

    return boxes, final_confidences
