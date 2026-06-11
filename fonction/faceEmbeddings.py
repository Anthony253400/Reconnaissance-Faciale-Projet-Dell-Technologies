import onnxruntime as ort
import cv2
import os
import numpy as np


def preprocessing(img):
    """
    Preprocess a face crop for ArcFace.

    The crop comes in RGB (that is what align_crop returns and what the live
    pipeline feeds). ArcFace ONNX here expects BGR, so we convert once,
    consistently, for BOTH registration and detection — this is what keeps the
    stored embeddings and the live embeddings comparable.

    Args:
        img (numpy.ndarray): face crop, RGB, any size.
    Returns:
        numpy.ndarray: (1, 112, 112, 3) float32, normalized to ~[-1, 1].
    """
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    resized = cv2.resize(bgr, (112, 112))
    normalized = (resized.astype(np.float32) - 127.5) / 128.0
    return normalized[np.newaxis, :].astype(np.float32)


def get_embedding(image, model):
    """
    Generate a normalized 512-d ArcFace embedding for a face crop.

    Args:
        image (numpy.ndarray): face crop in RGB.
        model: a loaded onnxruntime InferenceSession (ArcFace).
    Returns:
        numpy.ndarray: L2-normalized embedding, shape (512,).
    """
    img = preprocessing(image)
    input_name = model.get_inputs()[0].name
    embedding = model.run(None, {input_name: img})[0]
    embedding = embedding[0]                       # (1, 512) -> (512,)
    embedding = embedding / np.linalg.norm(embedding)
    return embedding