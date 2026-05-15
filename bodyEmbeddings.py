import torch
import torchreid
import cv2
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model = torchreid.models.build_model(
    name='osnet_x0_25',
    num_classes=751,
    pretrained=False
)
weights_path = os.path.join(BASE_DIR, "model", "osnet_x0_25_market.pth")
torchreid.utils.load_pretrained_weights(model, weights_path)
model.eval()

def preprocessing(crop_bgr):
    rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (128, 256))
    normalized = resized.astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406])
    std  = np.array([0.229, 0.224, 0.225])
    normalized = (normalized - mean) / std
    tensor = torch.tensor(normalized).permute(2, 0, 1).unsqueeze(0).float()
    return tensor

def get_body_embedding(crop_bgr):
    tensor = preprocessing(crop_bgr)
    with torch.no_grad():
        embedding = model(tensor)
    embedding = embedding.numpy().flatten()
    embedding = embedding / np.linalg.norm(embedding)
    return embedding


if __name__ == "__main__":
    import cv2
    from bodyDetection import BodyDetect_from_bytes
    from bodyAlignment import body_crop

    net = cv2.dnn.readNetFromONNX("model/yolov8n.onnx")

    with open("images/ste1.jpg", "rb") as f:
        image_bytes = f.read()

    boxes, confidences, img_rgb = BodyDetect_from_bytes(image_bytes, net)
    print(f"bodies detected: {len(boxes)}")

    crops = body_crop(img_rgb, boxes)
    print(f"crops obtained: {len(crops)}")

    for i, crop in enumerate(crops):
        embedding = get_body_embedding(crop)
        print(f"Body {i}: embedding shape={embedding.shape}, norm={np.linalg.norm(embedding):.4f}")
    
    
    with open("images/lino2.jpg", "rb") as f:
        image_bytes2 = f.read()

    boxes2, confidences2, img_rgb2 = BodyDetect_from_bytes(image_bytes2, net)
    crops2 = body_crop(img_rgb2, boxes2)

    embedding2 = get_body_embedding(crops2[0])

    # similarità coseno (già normalizzati, basta il dot product)
    similarity = np.dot(embedding, embedding2)
    print(f"similarity: {similarity:.4f}")

    # test: embedding di due immagini identiche
    embedding_a = get_body_embedding(crops[0])
    embedding_b = get_body_embedding(crops[0])  # stessa immagine
    print(f"Stessa immagine: {np.dot(embedding_a, embedding_b):.4f}")

    # test: embedding di rumore casuale
    noise = np.random.randint(0, 255, (256, 128, 3), dtype=np.uint8)
    embedding_noise = get_body_embedding(noise)
    print(f"Immagine vs rumore: {np.dot(embedding_a, embedding_noise):.4f}")