import onnxruntime as ort
import cv2
import os 
import numpy as np

def preprocessing(img):
    #rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    normalized_img = (img - 127.5) / 128.0
   
    img = normalized_img[np.newaxis, :]
    return img.astype(np.float32)


def get_embedding(image , model):
    img = preprocessing(image)
    input_name = model.get_inputs()[0].name
    embedding = model.run(None, {input_name: img})[0]
    embedding = embedding[0]
    embedding = embedding / np.linalg.norm(embedding)
    return embedding