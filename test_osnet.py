import torch
import cv2
import numpy as np
import torchreid
from bodyEmbeddings import preprocessing, get_body_embedding
from bodyDetection import BodyDetect_from_bytes
from bodyAlignment import body_crop

# carica modello
model = torchreid.models.build_model(
    name='osnet_x0_25',
    num_classes=751,
    pretrained=False
)
torchreid.utils.load_pretrained_weights(model, "model/osnet_x0_25_market.pth")
model.eval()

# carica immagine
with open("images/ste1.jpg", "rb") as f:
    image_bytes = f.read()

net = cv2.dnn.readNetFromONNX("model/yolov8n.onnx")
boxes, confidences, img_rgb = BodyDetect_from_bytes(image_bytes, net)
crops = body_crop(img_rgb, boxes)

# test raw output
tensor = preprocessing(crops[0])
with torch.no_grad():
    raw_output = model(tensor)

print(f"Raw output mean: {raw_output.mean().item():.4f}")
print(f"Raw output std:  {raw_output.std().item():.4f}")
print(f"Raw output min:  {raw_output.min().item():.4f}")
print(f"Raw output max:  {raw_output.max().item():.4f}")