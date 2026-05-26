# eval_utils.py

import cv2
import numpy as np
from collections import defaultdict
from sklearn.metrics import auc


# ── Pipeline ──

def numpy_to_bytes(img_array):
    """Convert a float32 numpy image (LFW format) to JPEG bytes."""
    img_uint8 = (img_array * 255).astype(np.uint8)
    img_bgr = cv2.cvtColor(img_uint8, cv2.COLOR_RGB2BGR)
    _, buffer = cv2.imencode('.jpg', img_bgr)
    return buffer.tobytes()


def run_pipeline(image_bytes, detector, client, collection_name, label_true, is_genuine,
                 align_crop_fn, get_embedding_fn, FacesDetects_fn):
    """
    Run the full recognition pipeline on a single image.
    Returns a result dict or None if no face is detected.
    """
    boxes, detection_result, image = FacesDetects_fn(image_bytes, "mediapipe", detector)

    if not detection_result or not detection_result.detections:
        return None

    crops = align_crop_fn(image, detection_result)
    if not crops:
        return None

    embedding = get_embedding_fn(crops[0])

    raw = client.query_points(
        collection_name=collection_name,
        query=embedding.tolist(),
        limit=1
    ).points

    if not raw:
        score, predicted_name = 0.0, "unknown"
    else:
        score = raw[0].score
        predicted_name = raw[0].payload["name"]

    return {
        "label_true": label_true,
        "predicted_name": predicted_name,
        "score": score,
        "is_genuine": is_genuine,
    }


# ── Metrics ──

def true_accept_rate(genuine_results, t):
    """TAR = fraction of genuine attempts correctly accepted at threshold t."""
    correct = sum(1 for r in genuine_results
                  if r["score"] >= t and r["predicted_name"] == r["label_true"])
    return correct / len(genuine_results)


def false_accept_rate(impostor_results, t):
    """FAR = fraction of impostor attempts incorrectly accepted at threshold t."""
    wrong = sum(1 for r in impostor_results if r["score"] >= t)
    return wrong / len(impostor_results)


def false_reject_rate(genuine_results, t):
    """FRR = fraction of genuine attempts incorrectly rejected at threshold t."""
    wrong = sum(1 for r in genuine_results if r["score"] < t)
    return wrong / len(genuine_results)


def compute_metrics(genuine_results, impostor_results, thresholds):
    """
    Compute TAR, FAR, FRR and EER over a range of thresholds.
    Returns a dict with arrays and EER info.
    """
    tar_list = np.array([true_accept_rate(genuine_results, t) for t in thresholds])
    far_list = np.array([false_accept_rate(impostor_results, t) for t in thresholds])
    frr_list = np.array([false_reject_rate(genuine_results, t) for t in thresholds])

    eer_idx       = np.argmin(np.abs(far_list - frr_list))
    eer_value     = (far_list[eer_idx] + frr_list[eer_idx]) / 2
    eer_threshold = thresholds[eer_idx]

    return {
        "tar": tar_list,
        "far": far_list,
        "frr": frr_list,
        "eer_value": eer_value,
        "eer_threshold": eer_threshold,
        "eer_idx": eer_idx,
        "auc": auc(far_list, tar_list)
    }