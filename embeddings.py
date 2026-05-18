import onnxruntime as ort
import cv2
import os 
import numpy as np


#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#session = ort.InferenceSession(os.path.join(BASE_DIR, "model", "arc.onnx"))
def preprocessing(img):
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    resized_img = cv2.resize(rgb_img, (112, 112))
    normalized_img = (resized_img - 127.5) / 128.0
   
    img = normalized_img[np.newaxis, :]
    return img.astype(np.float32)


def get_embedding(image, model):
    img = preprocessing(image)
    input_name = model.get_inputs()[0].name
    embedding = model.run(None, {input_name: img})[0]
    embedding = embedding[0]
    embedding = embedding / np.linalg.norm(embedding)
    return embedding