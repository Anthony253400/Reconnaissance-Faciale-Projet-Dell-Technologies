import cv2
import numpy as np
from DrawBox import DrawBox, color_name_to_rgb

# Détecte automatiquement si CUDA est dispo
try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    CUDA_AVAILABLE = False

print(f"[BodyDetection] GPU disponible : {CUDA_AVAILABLE}")


def load_yolo(model_path: str, use_gpu: bool = CUDA_AVAILABLE):
    """
    Charge YOLOv8 sur GPU ou CPU selon use_gpu.
    Détecte automatiquement si aucun paramètre n'est passé.
    """
    if use_gpu:
        try:
            from ultralytics import YOLO
            model = YOLO(model_path)
            model.to('cuda')
            print(f"[BodyDetection] YOLOv8 chargé sur GPU ✅")
            return ('ultralytics', model)
        except Exception as e:
            print(f"[BodyDetection] Échec GPU ({e}), fallback CPU")

    # Fallback CPU — ton code OpenCV original
    model = cv2.dnn.readNetFromONNX(model_path.replace('.pt', '.onnx'))
    print(f"[BodyDetection] YOLOv8 chargé sur CPU ✅")
    return ('opencv', model)


def BodyDetect_from_bytes(image_bytes, detector):
    """
    detector = ce que load_yolo() retourne : tuple ('ultralytics'|'opencv', model)
    """
    backend, model = detector

    nparr = np.frombuffer(image_bytes, np.uint8)
    img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    h, w, _ = img.shape

    # ── GPU : Ultralytics ──
    if backend == 'ultralytics':
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results  = model(img_rgb, device='cuda', verbose=False, classes=[0])

        boxes, confidences = [], []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                boxes.append([x1, y1, x2, y2])
                confidences.append(float(box.conf[0]))

        return boxes, confidences, img_rgb

    # ── CPU : OpenCV DNN (ton code original) ──
    else:
        blob = cv2.dnn.blobFromImage(img, 1/255.0, (640, 640), swapRB=True, crop=False)
        model.setInput(blob)
        outputs     = model.forward()
        predictions = np.squeeze(outputs[0]).T

        box, confidences = [], []
        for row in predictions:
            score = row[4:].max()
            if score > 0.7:
                class_id = row[4:].argmax()
                if class_id == 0:
                    cx, cy, rw, rh = row[0:4]
                    x1     = int((cx - rw/2) * (w / 640))
                    y1     = int((cy - rh/2) * (h / 640))
                    width  = int(rw * (w / 640))
                    height = int(rh * (h / 640))
                    box.append([x1, y1, width, height])
                    confidences.append(float(score))

        indices          = cv2.dnn.NMSBoxes(box, confidences, score_threshold=0.7, nms_threshold=0.4)
        boxes, final_confidences = [], []
        for i in indices:
            x, y, bw, bh = box[i]
            boxes.append([x, y, x + bw, y + bh])
            final_confidences.append(confidences[i])

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return boxes, final_confidences, img_rgb
    


    model_yolov = load_yolo("../model/yolov8n.pt")
