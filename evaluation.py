import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

 
from detecVisage import FacesDetects_from_bytes
from faceAlignment import align_crop
from embeddings import get_embedding
from qdrant_client import QdrantClient


EVAL_DIR = "images/evaluation_set"
UNKNOWN_LABEL = "unknown"
MODEL_PATH = "model/blaze_face_short_range.tflite"
THRESHOLD = np.arange(0.0, 1.01, 0.01) 
client = QdrantClient(host="10.233.220.118", port=6333)

#mediapipe initialization
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.FaceDetectorOptions(base_options=base_options)
detector = vision.FaceDetector.create_from_options(options)

# run pipeline on evaluation set
results=[]
for person_name in os.listdir(EVAL_DIR):
    person_dir = os.path.join(EVAL_DIR, person_name)
    if not os.path.isdir(person_dir):
        continue

    for img_name in os.listdir(person_dir):
        if not img_name.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        img_path = os.path.join(person_dir, img_name)
        with open(img_path, "rb") as f:
            image_bytes = f.read()

        boxes_face, detection_result, image = FacesDetects_from_bytes(image_bytes,"mediapipe",detector)
        if not detection_result or not detection_result.detections:
            print(f"Aucun visage détecté : {img_name}")
            continue

        crops = align_crop(image, detection_result)

        #compute embedding with Arcface
        embedding = get_embedding(crops[0])

        #search in Qdrant to get raw score and predicted name
        raw = client.query_points(
                    collection_name="face",
                    query=embedding.tolist(),
                    limit=1
                ).points

        if not raw:
            score = 0.0
            predicted_name = "unknown"
        else:
            score = raw[0].score
            predicted_name = raw[0].payload["name"]

        results.append({
            "label_true": person_name, #folder name, true label
            "predicted_name": predicted_name, # system prediction
            "score": score, #cosine similarity score
            "is_genuine": person_name != UNKNOWN_LABEL, # True if it's a registered person, False if it's an impostor (unknown)
            "photo": img_name
        })


#separate genuine and impostor results for metric calculations
genuine_results  = [r for r in results if r["is_genuine"]]
impostor_results = [r for r in results if not r["is_genuine"]]

print(f"Total photos processed : {len(results)}")
print(f"  Genuine   : {len(genuine_results)}")
print(f"  Impostors : {len(impostor_results)}")

#metric calculations
def true_accept_rate(t):
    """TAR = fraction of genuine attempts correctly accepted at threshold t"""
    right= 0
    for r in genuine_results:
        if r["score"] >= t and r["predicted_name"] == r["label_true"]:
            right += 1
    tar = right / len(genuine_results) 
    return tar

def false_accept_rate(t):
    """FAR = fraction of impostor attempts incorrectly accepted at threshold t"""
    wrong= 0
    for r in impostor_results:
        if r["score"] >= t:
            wrong += 1
    far = wrong / len(impostor_results) 
    return far

def false_reject_rate(t):
    """FRR = fraction of genuine attempts incorrectly rejected at threshold t"""
    wrong= 0
    for r in genuine_results:
        if r["score"] < t: 
            wrong += 1
    frr = wrong / len(genuine_results) 
    return frr


#compute metrics for each thresholds
tar_list = []
far_list = []
frr_list = []

for t in THRESHOLD:
    tar_list.append(true_accept_rate(t))
    far_list.append(false_accept_rate(t))
    frr_list.append(false_reject_rate(t))

tar_list = np.array(tar_list)
far_list = np.array(far_list)
frr_list = np.array(frr_list)

#calculate EER (Equal Error Rate)
#EER is the point where FAR and FRR are equal (or as close as possible)

eer_idx = np.argmin(np.abs(far_list - frr_list))
eer_threshold = THRESHOLD[eer_idx]
eer_value = (far_list[eer_idx] + frr_list[eer_idx]) / 2

print(f"EER        : {eer_value*100:.2f}%")
print(f"Seuil EER  : {eer_threshold:.2f}")
print(f"TAR @ EER  : {tar_list[eer_idx]*100:.2f}%")

print(f"\n── Results ──────────────────────")
print(f"EER                     : {eer_value*100:.2f}%")
print(f"Optimal threshold (EER) : {eer_threshold:.2f}")
print(f"TAR @ EER               : {tar_list[eer_idx]*100:.2f}%")
print(f"AUC (ROC)               : {auc(far_list, tar_list):.4f}")

print("\n── Debug genuine results ──")
for r in genuine_results:
    status = "✅" if r["predicted_name"] == r["label_true"] else "❌"
    print(f"{status} label: '{r['label_true']}' | predicted: '{r['predicted_name']}' | score: {r['score']:.3f}")
#visualization roc curve and FAR/FRR curve
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# ──────────────────────────────────────────────
# BENCHMARK PAR CONDITION
# ──────────────────────────────────────────────
from collections import defaultdict

# groupe les résultats genuine par condition (extrait du nom du fichier)
# ex: "lea_glasses1.jpg" → condition = "glasses"
condition_results = defaultdict(list)

for r in genuine_results:
    filename = r["photo"]  # on a besoin du nom du fichier
    try:
        condition = filename.split("_")[1].split(".")[0].rstrip("0123456789")
    except:
        condition = "unknown"
    condition_results[condition].append(r)

print("\n── Benchmark par condition ──────────────────────")
print(f"{'Condition':<15} {'Photos':>8} {'TAR (seuil 0.5)':>16} {'Score moyen':>12}")
print("-" * 55)

for condition, res in sorted(condition_results.items()):
    accepted = sum(1 for r in res if r["score"] >= 0.5 and r["predicted_name"] == r["label_true"])
    tar_cond = accepted / len(res) * 100
    avg_score = np.mean([r["score"] for r in res])
    print(f"{condition:<15} {len(res):>8} {tar_cond:>15.1f}% {avg_score:>11.3f}")

# — Courbe ROC —
axes[0].plot(far_list, tar_list, color="steelblue", lw=2, label=f"ROC (AUC = {auc(far_list, tar_list):.3f})")
axes[0].plot([0, 1], [0, 1], "k--", lw=1, label="Aléatoire")
axes[0].scatter(far_list[eer_idx], tar_list[eer_idx], color="red", zorder=5, label=f"EER = {eer_value:.3f}")
axes[0].set_xlabel("FAR (False Accept Rate)")
axes[0].set_ylabel("TAR (True Accept Rate)")
axes[0].set_title("Courbe ROC")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# — Courbe FAR / FRR —
axes[1].plot(THRESHOLD, far_list, color="tomato",    lw=2, label="FAR")
axes[1].plot(THRESHOLD, frr_list, color="steelblue", lw=2, label="FRR")
axes[1].axvline(eer_threshold, color="green", linestyle="--", lw=1.5, label=f"Seuil EER = {eer_threshold:.2f}")
axes[1].scatter(eer_threshold, eer_value, color="green", zorder=5)
axes[1].set_xlabel("Seuil de similarité cosinus")
axes[1].set_ylabel("Taux d'erreur")
axes[1].set_title("FAR / FRR selon le seuil")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
