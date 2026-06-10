"""
test_crop.py
============
Test diagnostico per la pipeline di riconoscimento facciale.

Posizione: questo file sta in  <root>/fonction/test_crop.py
Struttura attesa delle immagini (una sottocartella per persona):
    <root>/images/evaluation_set/
        robin henry/   img1.jpg ...
        lea carminati/ img1.jpg ...
L'identita' di ogni foto = nome della sua cartella.

Cosa fa:
  1. Carica i modelli (detector MediaPipe + ArcFace) tramite load_model.
  2. Per ogni foto: detection -> align_crop (CORRETTA) -> embedding.
  3. Salva i crop allineati in <root>/images/test_pipelines/ per l'ispezione.
  4. Calcola le similarita' coseno GENUINE vs IMPOSTOR direttamente (no Qdrant).

Lancia (da qualsiasi cartella):  python fonction/test_crop.py
"""

import os
import sys
from itertools import combinations

import cv2
import numpy as np

# ----------------------------------------------------------------------
# PATH  --  ancorati alla posizione del file, non alla cartella di lancio
# ----------------------------------------------------------------------
_HERE        = os.path.dirname(os.path.abspath(__file__))   # .../fonction
PROJECT_ROOT = os.path.dirname(_HERE)                       # .../ (root progetto)

EVAL_ROOT    = os.path.join(PROJECT_ROOT, "images", "evaluation_set")
OUT_CROPS    = os.path.join(PROJECT_ROOT, "images", "test_pipelines")

INPUT_IS_RGB   = True       # True se FacesDetects_from_bytes restituisce RGB
MAX_PER_PERSON = 100          # max foto per persona (per tenere il test veloce)
DEBUG_KP       = True       # stampa i keypoint della primissima faccia
# ----------------------------------------------------------------------

sys.path.insert(0, PROJECT_ROOT)
from fonction.loadModel import load_model
from fonction.faceDetection import FacesDetects_from_bytes


# ======================================================================
# ALIGN_CROP  --  similarity transform sul template ArcFace
# ======================================================================

_DST5 = np.array([
    [38.2946, 51.6963],   # occhio sx
    [73.5318, 51.5014],   # occhio dx
    [56.0252, 71.7366],   # naso
    [41.5493, 92.3655],   # bocca sx
    [70.7299, 92.2041],   # bocca dx
], dtype=np.float32)
_DST4 = np.array(
    [_DST5[0], _DST5[1], _DST5[2], (_DST5[3] + _DST5[4]) / 2.0],
    dtype=np.float32,
)

# Indici keypoint MediaPipe (confermati dal debug):
# 0=occhio dx, 1=occhio sx, 2=naso, 3=bocca, 4=orecchio dx, 5=orecchio sx
KP_EYE_R, KP_EYE_L, KP_NOSE, KP_MOUTH = 0, 1, 2, 3

_debug_done = False


def align_crop(image, listFace, method="mediapipe", size=112):
    global _debug_done
    crops = []
    h, w = image.shape[:2]

    if method != "mediapipe":
        raise NotImplementedError("Questo test gestisce solo 'mediapipe'.")

    for det in listFace.detections:
        kp = det.keypoints

        if DEBUG_KP and not _debug_done:
            print("  [DEBUG] keypoint della prima faccia (x_px, y_px):")
            for idx, k in enumerate(kp):
                print(f"    kp[{idx}] = ({k.x * w:.0f}, {k.y * h:.0f})")
            _debug_done = True

        eye_a = (kp[KP_EYE_R].x * w, kp[KP_EYE_R].y * h)
        eye_b = (kp[KP_EYE_L].x * w, kp[KP_EYE_L].y * h)
        nose  = (kp[KP_NOSE].x  * w, kp[KP_NOSE].y  * h)
        mouth = (kp[KP_MOUTH].x * w, kp[KP_MOUTH].y * h)

        # L'occhio con x minore va al template SINISTRO (dst[0]).
        # Cosi' evitiamo un mirroring che la similarity transform
        # "compensa" con una rotazione di 180 (= volto capovolto).
        eye_left, eye_right = (eye_a, eye_b) if eye_a[0] <= eye_b[0] else (eye_b, eye_a)
        src = np.array([eye_left, eye_right, nose, mouth], dtype=np.float32)
        M, _ = cv2.estimateAffinePartial2D(src, _DST4)
        if M is None:
            continue

        aligned = cv2.warpAffine(image, M, (size, size), borderValue=0)
        crops.append(aligned)

    return crops


# ======================================================================
# EMBEDDING  --  auto NHWC/NCHW, L2-norm
# ======================================================================

def _detect_layout(model):
    shape = model.get_inputs()[0].shape
    if len(shape) == 4 and shape[1] == 3:
        return "NCHW"
    return "NHWC"


def get_embedding(crop, model):
    img = (crop.astype(np.float32) - 127.5) / 128.0
    img = img[np.newaxis, :]                      # (1,112,112,3)
    if _detect_layout(model) == "NCHW":
        img = np.transpose(img, (0, 3, 1, 2))     # -> (1,3,112,112)
    input_name = model.get_inputs()[0].name
    emb = model.run(None, {input_name: img.astype(np.float32)})[0][0]
    return emb / np.linalg.norm(emb)


# ======================================================================
# UTILS
# ======================================================================

def to_bgr_for_save(crop):
    return cv2.cvtColor(crop, cv2.COLOR_RGB2BGR) if INPUT_IS_RGB else crop


def collect_images(root, max_per_person):
    """Ritorna lista di (identita', path). Identita' = nome della sottocartella,
    TRANNE per 'unknown', dove ogni foto e' una persona diversa (identita' unica)."""
    items = []
    exts = (".jpg", ".jpeg", ".png")
    if not os.path.isdir(root):
        return items
    for person in sorted(os.listdir(root)):
        pdir = os.path.join(root, person)
        if not os.path.isdir(pdir):
            continue
        is_unknown = person.strip().lower() == "unknown"
        photos = sorted(f for f in os.listdir(pdir) if f.lower().endswith(exts))
        for fname in photos[:max_per_person]:
            if is_unknown:
                # ogni sconosciuto = identita' a se' -> mai "genuine" con un altro
                identity = f"unknown_{os.path.splitext(fname)[0]}"
            else:
                identity = person.strip().lower()
            items.append((identity, os.path.join(pdir, fname)))
    return items


# ======================================================================
# MAIN
# ======================================================================

def main():
    print(f"PROJECT_ROOT : {PROJECT_ROOT}")
    print(f"EVAL_ROOT    : {EVAL_ROOT}")
    os.makedirs(OUT_CROPS, exist_ok=True)

    print("\nCarico i modelli...")
    detector = load_model("blazeface_short", False)
    arcface  = load_model("arcface", True)
    print(f"  Layout input ArcFace : {_detect_layout(arcface)} "
          f"(shape {arcface.get_inputs()[0].shape})")

    items = collect_images(EVAL_ROOT, MAX_PER_PERSON)
    if not items:
        print(f"Nessuna immagine trovata sotto {EVAL_ROOT}")
        return

    n_people = len(set(i for i, _ in items))
    print(f"\nTrovate {len(items)} foto di {n_people} persone. Processo...")

    embeddings = []   # (identita', path, embedding)
    for identity, path in items:
        with open(path, "rb") as fh:
            data = fh.read()
        try:
            _, result, image = FacesDetects_from_bytes(data, "mediapipe", detector)
        except Exception as e:
            print(f"  [{identity}/{os.path.basename(path)}] errore: {e}")
            continue
        if not result or not result.detections:
            print(f"  [{identity}/{os.path.basename(path)}] nessun volto")
            continue
        crops = align_crop(image, result, "mediapipe")
        if not crops:
            continue
        crop = crops[0]
        if not embeddings:   # solo il primo crop: diagnosi del range pixel
            print(f"  [DEBUG] crop dtype={crop.dtype} "
                  f"min={crop.min()} max={crop.max()} shape={crop.shape}")
        save_name = f"{identity}__{os.path.basename(path)}".replace(" ", "_")
        cv2.imwrite(os.path.join(OUT_CROPS, save_name), to_bgr_for_save(crop))
        embeddings.append((identity, path, get_embedding(crop, arcface)))

    print(f"\nEmbedding calcolati: {len(embeddings)}")
    if len(embeddings) < 2:
        print("Servono almeno 2 embedding.")
        return

    # confronto genuine vs impostor
    genuine, impostor = [], []
    for (ia, _, ea), (ib, _, eb) in combinations(embeddings, 2):
        cos = float(np.dot(ea, eb))
        (genuine if ia == ib else impostor).append(cos)

    print("\n" + "=" * 60)
    print("RISULTATI  (similarita' coseno)")
    print("=" * 60)
    if genuine:
        g = np.array(genuine)
        print(f"GENUINE  (stessa persona)  : n={len(g):4d} | media={g.mean():.3f} "
              f"| min={g.min():.3f} | max={g.max():.3f}")
    if impostor:
        im = np.array(impostor)
        print(f"IMPOSTOR (persone diverse) : n={len(im):4d} | media={im.mean():.3f} "
              f"| min={im.min():.3f} | max={im.max():.3f}")

    if genuine and impostor:
        gap = g.mean() - im.mean()
        print(f"\nSeparazione (media_genuine - media_impostor) = {gap:+.3f}")
        thr = (g.mean() + im.mean()) / 2
        print(f"Soglia indicativa suggerita ~ {thr:.2f}")
        if gap > 0.30:
            print("==> PIPELINE OK: ottima separazione delle identita'.")
        elif gap > 0.15:
            print("==> DISCRETA: separa, ma controlla i crop e l'orientamento.")
        else:
            print("==> DEBOLE/ROTTA: guarda i crop salvati.")

    print(f"\nCrop salvati in: {OUT_CROPS}")

    pairs = []
    for (ia, pa, ea), (ib, pb, eb) in combinations(embeddings, 2):
        pairs.append((float(np.dot(ea, eb)), ia, os.path.basename(pa), ib, os.path.basename(pb)))

    print("\nGENUINE peggiori (stessa persona, coseno basso):")
    for c, ia, fa, ib, fb in sorted(p for p in pairs if p[1] == p[3])[:5]:
        print(f"  {c:+.3f}  {ia}: {fa} <-> {fb}")

    print("\nIMPOSTOR migliori (persone diverse, falsi match):")
    for c, ia, fa, ib, fb in sorted((p for p in pairs if p[1] != p[3]), reverse=True)[:5]:
        print(f"  {c:+.3f}  {ia}/{fa} <-> {ib}/{fb}")

    # vista realistica: solo foto frontali "normal"
    emb_normal = [(i, p, e) for (i, p, e) in embeddings if "normal" in os.path.basename(p).lower()]
    gn, imn = [], []
    for (ia, _, ea), (ib, _, eb) in combinations(emb_normal, 2):
        (gn if ia == ib else imn).append(float(np.dot(ea, eb)))
    if gn and imn:
        print(f"\n[SOLO NORMAL] genuine media={np.mean(gn):.3f} | "
              f"impostor media={np.mean(imn):.3f} | gap={np.mean(gn)-np.mean(imn):+.3f}")
        
        
if __name__ == "__main__":
    main()