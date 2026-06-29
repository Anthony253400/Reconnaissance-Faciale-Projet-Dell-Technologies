"""
main.py — FastAPI worker (one instance per GPU via Docker)
==========================================================
Chaque conteneur reçoit CUDA_VISIBLE_DEVICES=N via docker-compose,
donc ici device_id=0 désigne toujours le GPU physique assigné au
conteneur courant. Les modèles sont chargés une seule fois au
démarrage (lifespan), en dehors de toute requête.

Architecture multi-GPU :
  • 4 workers (un par GPU) tournent chacun sur :8000 en interne
  • nginx_lb.conf distribue les connexions WebSocket / REST entrantes
    sur ces 4 workers via l'upstream « inference »
  • Un seul port est exposé vers l'extérieur : 8001 → nginx → workers
"""

import asyncio
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import List

import cv2
import numpy as np

sys.path.append("../")

from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from fonction.bodyAlignment import body_crop
from fonction.bodyDetection import BodyDetect_from_frame
from fonction.faceAlignment import align_crop
from fonction.faceDetection import FacesDetects_from_frame
from fonction.faceEmbeddings import get_embedding
from fonction.identity_smoother import SmootherBank
from fonction.loadModel import load_model
from fonction.qdrant_db import create_collection, save_embedding, search_embedding
from fonction.tracker import BodyTracker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COLLECTION   = "face"
QDRANT_HOST  = os.getenv("qdrant_host", "localhost")
QDRANT_PORT  = int(os.getenv("Qdrant_port", 6333))
GPU_ID       = os.getenv("CUDA_VISIBLE_DEVICES", "?")

# Nombre de threads pour l'inférence :
# • ONNX Runtime gère déjà son propre pool interne
# • 2 threads suffisent pour overlapper face + body en même temps
INFERENCE_THREADS = int(os.getenv("INFERENCE_THREADS", 2))

# ---------------------------------------------------------------------------
# Lifespan : chargement des modèles UNE SEULE FOIS au démarrage du worker
# ---------------------------------------------------------------------------

models: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Charge les modèles IA et le client Qdrant au démarrage du processus."""

    # ── Diagnostic GPU ───────────────────────────────────────────────────────
    print(f"\n{'='*50}")
    print(f"[Worker] GPU assigné (CUDA_VISIBLE_DEVICES) : {GPU_ID}")

    try:
        import torch
        if torch.cuda.is_available():
            print(f"[Worker] PyTorch voit    : {torch.cuda.get_device_name(0)}")
            print(f"[Worker] VRAM libre      : "
                  f"{torch.cuda.mem_get_info(0)[0] / 1e9:.1f} GB")
        else:
            print("[Worker] PyTorch : CPU seulement")
    except Exception:
        pass

    import onnxruntime as ort
    avail = ort.get_available_providers()
    gpu_ok = "CUDAExecutionProvider" in avail
    print(f"[Worker] ONNX providers  : {avail}")
    print(f"[Worker] ONNX utilise    : {'GPU (CUDA)' if gpu_ok else 'CPU'}")
    print("=" * 50 + "\n")

    # ── Chargement des modèles ────────────────────────────────────────────────
    # use_gpu=True → CUDA si dispo, sinon fallback CPU automatique (voir loadModel.py)
    print("[Worker] Chargement BlazeFace …")
    models["blazeface"] = load_model("blazeface_short", use_gpu=False)  # MediaPipe CPU

    print("[Worker] Chargement ArcFace …")
    models["arcface"] = load_model("arcface", use_gpu=gpu_ok)

    print("[Worker] Chargement YOLOv8 …")
    models["yolo"] = load_model("yolo", use_gpu=gpu_ok)

    # ── Client Qdrant ─────────────────────────────────────────────────────────
    from qdrant_client import QdrantClient
    models["qdrant"] = QdrantClient(
        host=QDRANT_HOST, port=QDRANT_PORT, prefer_grpc=True
    )
    create_collection()

    # ── Thread pool pour l'inférence CPU/GPU bound ────────────────────────────
    models["executor"] = ThreadPoolExecutor(max_workers=INFERENCE_THREADS)

    print(f"[Worker] Prêt  (GPU {GPU_ID}, {INFERENCE_THREADS} threads d'inférence)\n")

    yield  # ← l'application tourne ici

    # ── Nettoyage ─────────────────────────────────────────────────────────────
    models["executor"].shutdown(wait=False)
    print(f"[Worker] Arrêt propre (GPU {GPU_ID})")


# ---------------------------------------------------------------------------
# Application FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# WebSocket — Détection temps réel
# ---------------------------------------------------------------------------

@app.websocket("/ws/detect")
async def ws_detect(websocket: WebSocket):
    """
    Reçoit des frames JPEG via WebSocket, renvoie les boîtes + identités en JSON.

    Pipeline par frame :
      1. Décodage JPEG → RGB
      2. Détection visages (BlazeFace) + corps (YOLOv8) en parallèle
      3. Alignement & embedding ArcFace pour chaque visage
      4. Recherche Qdrant (cosine similarity)
      5. Lissage temporel des identités (SmootherBank)
      6. Tracking corps (BodyTracker)
      7. Envoi JSON au client
    """
    await websocket.accept()
    loop     = asyncio.get_event_loop()
    executor = models["executor"]
    tracker  = BodyTracker(iou_threshold=0.1, max_distance=80, max_lost_frames=90)
    smoother = SmootherBank(window=8, min_votes=3, min_score=0.55, score_hold=5)

    try:
        while True:
            # ── 1. Réception & décodage ──────────────────────────────────────
            data      = await websocket.receive_bytes()
            arr       = np.frombuffer(data, np.uint8)
            frame_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame_bgr is None:
                continue
            frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

            # ── 2. Détection visages + corps en parallèle ────────────────────
            face_fut = loop.run_in_executor(
                executor,
                lambda f=frame: FacesDetects_from_frame(
                    f, "mediapipe", models["blazeface"]
                ),
            )
            body_fut = loop.run_in_executor(
                executor,
                lambda f=frame: BodyDetect_from_frame(f, models["yolo"]),
            )
            (boxes_face, result, _), (boxes_body, _) = await asyncio.gather(
                face_fut, body_fut
            )

            # ── 3-5. Embedding + Qdrant + lissage ───────────────────────────
            names, scores, clean_names = [], [], []

            if result and result.detections:
                crops = align_crop(frame, result, "mediapipe")

                for i, crop in enumerate(crops):
                    emb = await loop.run_in_executor(
                        executor,
                        lambda c=crop: get_embedding(c, models["arcface"]),
                    )
                    raw_name, raw_score = await loop.run_in_executor(
                        executor,
                        lambda e=emb: search_embedding(e),
                    )
                    name, score = smoother.update(i, raw_name, raw_score)
                    clean = name if (name and name != "unknown") else ""
                    clean_names.append(clean)
                    names.append(clean or "inconnu")
                    scores.append(round(float(score), 2) if score else 0.0)

                smoother.prune(len(boxes_face))

            # Complète les listes si moins d'embeddings que de boîtes détectées
            while len(names) < len(boxes_face):
                names.append("inconnu")
                scores.append(0.0)
                clean_names.append("")

            # ── 6. Tracking corps ────────────────────────────────────────────
            crops_body = body_crop(frame, boxes_body) if boxes_body else []
            body_names = tracker.update(boxes_face, boxes_body, clean_names, crops_body)

            # ── 7. Réponse JSON ──────────────────────────────────────────────
            await websocket.send_json({
                "faces":      [[int(v) for v in b] for b in boxes_face],
                "names":      names,
                "scores":     scores,
                "body":       [[int(v) for v in b] for b in boxes_body],
                "body_names": body_names,
            })

    except WebSocketDisconnect:
        print(f"[ws/detect] client déconnecté (GPU {GPU_ID})")
    except Exception as exc:
        print(f"[ws/detect] erreur (GPU {GPU_ID}): {exc}")
        await websocket.close()


# ---------------------------------------------------------------------------
# REST — Enregistrement d'une personne
# ---------------------------------------------------------------------------

@app.post("/add")
async def add_person(
    firstName: str               = Form(...),
    lastName:  str               = Form(...),
    photos:    List[UploadFile]  = File(...),
):
    """
    Reçoit N frames JPEG, extrait un embedding par frame valide et
    les stocke dans Qdrant sous le nom '{prénom} {nom}'.
    """
    t_start = time.perf_counter()
    person  = f"{firstName} {lastName}".strip().lower()
    saved   = 0

    print(f"\n[/add] {person} | {len(photos)} frames reçues (GPU {GPU_ID})")

    for i, photo in enumerate(photos):
        contents = await photo.read()
        try:
            arr = np.frombuffer(contents, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                continue
            image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            _, result, image = FacesDetects_from_frame(
                image, "mediapipe", models["blazeface"]
            )
            if not result or not result.detections:
                continue

            crops = align_crop(image, result, "mediapipe")
            if not crops:
                continue

            embedding = get_embedding(crops[0], models["arcface"])
            save_embedding(person, embedding, models["qdrant"], COLLECTION)
            saved += 1

        except Exception as exc:
            print(f"[/add] frame {i} ignorée : {exc}")

    if saved == 0:
        return Response(status_code=422, content="Aucune frame valide trouvée.")

    elapsed = (time.perf_counter() - t_start) * 1000
    print(f"[/add] {saved}/{len(photos)} embeddings sauvegardés en {elapsed:.0f} ms")
    return {"status": "ok", "frames_used": saved, "total_frames": len(photos)}


# ---------------------------------------------------------------------------
# Fichiers statiques (optionnel, pour servir le front en dev)
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory=".", html=True), name="static")