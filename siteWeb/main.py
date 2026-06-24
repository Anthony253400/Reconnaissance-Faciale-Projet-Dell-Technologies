import os  # <-- AJOUTÉ pour lire l'environnement Docker
from unicodedata import name

import cv2
import sys
import time
import numpy as np

sys.path.append('../')

from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.models import FilterSelector, PointStruct, VectorParams, Distance, PointIdsList, Filter, FieldCondition, MatchValue
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fonction.loadModel import load_model
from fonction.faceDetection import FacesDetects_from_frame
from fonction.faceAlignment import align_crop
from fonction.faceEmbeddings import get_embedding
from fonction.qdrant_db import save_embedding, create_collection, search_embedding
from fonction.bodyDetection import BodyDetect_from_frame
from fonction.tracker import BodyTracker
from fonction.bodyAlignment import body_crop
from fonction.identity_smoother import SmootherBank

COLLECTION = 'face'
app = FastAPI()

QDRANT_HOST = os.getenv("qdrant_host", "localhost")
QDRANT_PORT = int(os.getenv("Qdrant_port", 6333))

qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, prefer_grpc=True)

# Models (loaded once at startup)
model_mediapipe = load_model("blazeface_short", False)
model_arcface   = load_model("arcface", True)
model_yolo      = load_model("yolo", True)

create_collection() 
import torch

print("\n" + "="*40)
if torch.cuda.is_available():
    print(f"🔥 GPU DÉTECTÉ PAR PYTORCH : {torch.cuda.get_device_name(0)}")
    print(f"Nombre de GPU dispos : {torch.cuda.device_count()}")
else:
    print("⚠️ ATTENTION : PyTorch ne voit AUCUN GPU. Inférence sur CPU.")
print("="*40 + "\n")
import onnxruntime as ort

print("\n" + "="*40)
providers = ort.get_available_providers()
print(f"Moteurs d'exécution ONNX dispo : {providers}")
if 'CUDAExecutionProvider' in providers:
    print("🔥 ONNX RUNTIME UTILISE LE GPU (CUDA) !")
else:
    print("⚠️ ATTENTION : ONNX se rabat sur le CPU.")
print("="*40 + "\n")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



# Pool dédié à l'inférence (1 thread par worker suffit, ONNX gère ses propres threads)
_executor = ThreadPoolExecutor(max_workers=2)

@app.websocket("/ws/detect")
async def ws_detect(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_event_loop()
    tracker  = BodyTracker(iou_threshold=0.1, max_distance=80, max_lost_frames=90)
    smoothers = SmootherBank(window=8, min_votes=3, min_score=0.55, score_hold=5)

    try:
        while True:
            data      = await websocket.receive_bytes()
            arr       = np.frombuffer(data, np.uint8)
            frame_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame_bgr is None:
                continue
            frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

            # détection en parallèle (les deux sont CPU/GPU bound)
            face_future = loop.run_in_executor(
                _executor,
                lambda: FacesDetects_from_frame(frame, "mediapipe", model_mediapipe)
            )
            body_future = loop.run_in_executor(
                _executor,
                lambda: BodyDetect_from_frame(frame, model_yolo)
            )
            (boxes_face, result, _), (boxes_body, _) = await asyncio.gather(
                face_future, body_future
            )

            names, scores, clean_names = [], [], []
            if result and result.detections:
                crops = align_crop(frame, result, "mediapipe")
                for i, face_cropped in enumerate(crops):
                    # embedding non-bloquant
                    embedding = await loop.run_in_executor(
                        _executor, get_embedding, face_cropped, model_arcface
                    )
                    raw_name, raw_score = await loop.run_in_executor(
                        _executor, search_embedding, embedding
                    )
                    name, score = smoothers.update(i, raw_name, raw_score)
                    clean = name if (name and name != "unknown") else ""
                    clean_names.append(clean)
                    names.append(clean or "inconnu")
                    scores.append(round(float(score), 2) if score else 0.0)
                smoothers.prune(len(boxes_face))

            while len(names) < len(boxes_face):
                names.append("inconnu"); scores.append(0.0); clean_names.append("")

            crops_body = body_crop(frame, boxes_body) if boxes_body else []
            body_names = tracker.update(boxes_face, boxes_body, clean_names, crops_body)

            await websocket.send_json({
                "faces":      [[int(v) for v in b] for b in boxes_face],
                "names":      names,
                "scores":     scores,
                "body":       [[int(v) for v in b] for b in boxes_body],
                "body_names": body_names,
            })

    except WebSocketDisconnect:
        print("[ws/detect] disconnected")
    except Exception as e:
        print(f"[ws/detect] error: {e}")
        await websocket.close()


# ============================================================================
#  Register a person
# ============================================================================
@app.post("/add")
async def add_person(
    firstName: str = Form(...),
    lastName:  str = Form(...),
    photos:    List[UploadFile] = File(...)
):
    print(f"\n[/add] start: {firstName} {lastName} | {len(photos)} frames")
    t_start = time.perf_counter()

    saved = 0
    name = f"{firstName} {lastName}".strip().lower()

    for i, photo in enumerate(photos):
        contents = await photo.read()
        try:
            # decode uploaded bytes -> RGB (same color path as detection)
            arr = np.frombuffer(contents, np.uint8)
            image_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if image_bgr is None:
                continue
            image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

            boxes_face, result, image = FacesDetects_from_frame(
                image, "mediapipe", model_mediapipe)
            if not result or not result.detections:
                continue

            crops = align_crop(image, result, "mediapipe")
            if not crops:
                continue

            embedding = get_embedding(crops[0], model_arcface)

            # Utilisation du client globalisé et configuré pour Docker
            save_embedding(name, embedding, qdrant_client, COLLECTION)
            saved += 1

        except Exception as e:
            print(f"[/add] skipped frame {i}: {e}")
            continue

    if saved == 0:
        return Response(status_code=422, content="No valid frames found.")

    print(f"[/add] {saved}/{len(photos)} embeddings saved | "
          f"{(time.perf_counter() - t_start) * 1000:.1f} ms")
    return {"status": "ok", "frames_used": saved, "total_frames": len(photos)}


app.mount("/static", StaticFiles(directory=".", html=True), name="static")