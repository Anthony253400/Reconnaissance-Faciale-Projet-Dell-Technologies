import onnxruntime as ort
import cv2
import os
import numpy as np


def preprocessing(img):
    """
    aligns and cuts out the face.
    Args:
        image (numpy.ndarray): The input image in RGB format.
    Returns:
        tuple:
            - face_final (numpy.ndarray): face align and crop in format RGB.
    
    """
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