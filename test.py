from ultralytics import YOLO

# 1. Charge ton modèle PyTorch de base (YOLOv8 nano ou autre)
model = YOLO("yolov8n.pt") 

# 2. Exporte-le en forçant la taille d'entrée à 320x320
# Tu peux aussi forcer l'optimisation dynamique (dynamic=True) mais le 320 fixe est plus rapide
model.export(format="onnx", imgsz=320, opset=12)


