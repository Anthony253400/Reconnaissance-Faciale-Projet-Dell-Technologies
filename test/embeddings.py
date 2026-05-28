import numpy as np


def preprocessing(img):
    """Normalise une image (112x112, RGB ou BGR) pour ArcFace."""
    normalized = (img - 127.5) / 128.0
    # NCHW : (1, 3, 112, 112)
    img_t = np.transpose(normalized, (2, 0, 1))
    return img_t.astype(np.float32)


def get_embedding(image, model):
    """
    Calcule l'embedding pour une seule image.

    Args:
        image (numpy.ndarray): Image (112, 112, 3).
        model: Session ONNX ArcFace.

    Returns:
        numpy.ndarray: Vecteur normalisé (512,).
    """
    img = preprocessing(image)[np.newaxis, :]  # (1, 3, 112, 112)
    input_name = model.get_inputs()[0].name
    embedding = model.run(None, {input_name: img})[0][0]
    return embedding / np.linalg.norm(embedding)


def get_embeddings_batch(images, model):
    """
    Calcule les embeddings pour N images en une seule inférence ONNX.
    Beaucoup plus efficace que N appels à get_embedding() en boucle.

    Args:
        images (list[numpy.ndarray]): Liste d'images (112, 112, 3).
        model: Session ONNX ArcFace.

    Returns:
        numpy.ndarray: Matrice (N, 512) de vecteurs normalisés.
                       Retourne un tableau vide (0, 512) si images est vide.
    """
    if not images:
        return np.empty((0, 512), dtype=np.float32)

    # Stack en un seul batch (N, 3, 112, 112)
    batch = np.stack([preprocessing(img) for img in images], axis=0)

    input_name = model.get_inputs()[0].name
    embeddings = model.run(None, {input_name: batch})[0]  # (N, 512)

    # Normalisation L2 ligne par ligne
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)  # évite division par zéro
    return embeddings / norms
