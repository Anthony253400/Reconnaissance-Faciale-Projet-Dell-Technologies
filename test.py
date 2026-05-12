from ultralytics import YOLO

model = YOLO('yolov8n.pt')
model.export(format='onnx', imgsz=640) # Génère 'yolov8n.onnx'