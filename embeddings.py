import onnxruntime as ort
import cv2
import os 
import numpy as np


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
session = ort.InferenceSession(os.path.join(BASE_DIR, "model", "arc.onnx"))
def preprocessing(img):
    """
    Preprocesses a cropped image for embedding generation.
    Args:
        img (numpy.ndarray): The cropped image in BGR format.
    Returns:
        numpy.ndarray: The preprocessed image ready for embedding generation.
    """
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    resized_img = cv2.resize(rgb_img, (112, 112))
    normalized_img = (resized_img - 127.5) / 128.0
   
    img = normalized_img[np.newaxis, :]
    return img.astype(np.float32)


def get_embedding(image):
    """Generates a body embedding for a given cropped image.
    Args:
        image (numpy.ndarray): The cropped image in BGR format.
    Returns:
        numpy.ndarray: The generated body embedding.
    """
    img = preprocessing(image)
    input_name = session.get_inputs()[0].name
    embedding = session.run(None, {input_name: img})[0]
    embedding = embedding[0]                           # (1, 512) → (512,)
    embedding = embedding / np.linalg.norm(embedding)
    return embedding