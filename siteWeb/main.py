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
import threading

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

# Models (loaded once at startup)
model_mediapipe = load_model("blazeface_short", False)
model_arcface   = load_model("arcface", True)
model_yolo      = load_model("yolo", True)

create_collection()   # ensure the 'face' collection exists

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ClientInferenceNode:
    """
    Unité de traitement asynchrone assignée à une cible (client) spécifique.
    Sépare la réception réseau à haute fréquence de l'inférence IA plus lente.
    """
    def __init__(self):
        self.lock_raw = threading.Lock()
        self.lock_out = threading.Lock()

        self.raw_frame = None
        self.latest_telemetry = {
            "faces": [], "names": [], "scores": [],
            "body": [], "body_names": []
        }
        self.running = True

        # Trackers et lisseurs isolés pour ce client
        self.tracker = BodyTracker(iou_threshold=0.1, max_distance=80, max_lost_frames=90)
        self.smoothers = SmootherBank(window=8, min_votes=3, min_score=0.55, score_hold=5)

        # Déploiement du thread d'analyse
        self._thread = threading.Thread(target=self._ai_loop, daemon=True)
        self._thread.start()

    def update_frame(self, frame_bytes):
        """Décode et stocke la dernière trame optique reçue."""
        arr = np.frombuffer(frame_bytes, np.uint8)
        frame_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame_bgr is not None:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            with self.lock_raw:
                self.raw_frame = frame_rgb

    def get_telemetry(self):
        """Exfiltre les dernières coordonnées identifiées."""
        with self.lock_out:
            return self.latest_telemetry

    def stop(self):
        """Termine proprement les opérations du thread."""
        self.running = False
        self._thread.join(timeout=1.0)

    def _ai_loop(self):
        """Boucle d'inférence principale. Tourne à sa propre fréquence."""
        while self.running:
            with self.lock_raw:
                frame = self.raw_frame

            # Si aucune donnée, on temporise pour préserver le CPU
            if frame is None:
                time.sleep(0.01)
                continue

            try:
                # 1. Détection des cibles
                boxes_face, result, _ = FacesDetects_from_frame(frame, "mediapipe", model_mediapipe)
                boxes_body, _ = BodyDetect_from_frame(frame, model_yolo)

                # 2. Extraction et identification
                names, scores, clean_names = [], [], []
                if result and result.detections:
                    crops = align_crop(frame, result, "mediapipe")
                    for i, face_cropped in enumerate(crops):
                        embedding = get_embedding(face_cropped, model_arcface)
                        raw_name, raw_score = search_embedding(embedding)
                        name, score = self.smoothers.update(i, raw_name, raw_score)

                        clean = name if (name and name != "unknown") else ""
                        clean_names.append(clean)
                        names.append(clean if clean else "inconnu")
                        scores.append(round(float(score), 2) if score is not None else 0.0)
                    self.smoothers.prune(len(boxes_face))

                # Alignement des listes si des visages de profil ont été ignorés
                while len(names) < len(boxes_face):
                    names.append("inconnu")
                    scores.append(0.0)
                    clean_names.append("")

                # 3. Suivi dynamique des corps
                crops_body = body_crop(frame, boxes_body) if boxes_body else []
                body_names = self.tracker.update(boxes_face, boxes_body, clean_names, crops_body)

                # 4. Verrouillage et mise à jour de la télémétrie
                with self.lock_out:
                    self.latest_telemetry = {
                        "faces": [[int(v) for v in b] for b in boxes_face],
                        "names": names,
                        "scores": scores,
                        "body": [[int(v) for v in b] for b in boxes_body],
                        "body_names": body_names,
                    }

            except Exception as e:
                print(f"[Thread IA] Erreur d'inférence : {e}")
                time.sleep(0.05)


@app.websocket("/ws/detect")
async def ws_detect(websocket: WebSocket):
    await websocket.accept()
    print("[Opérationnel] Liaison client établie.")

    # Attribution d'un nœud d'inférence dédié
    node = ClientInferenceNode()

    try:
        while True:
            # 1. Réception de la trame brute
            data = await websocket.receive_bytes()
            node.update_frame(data)

            # 2. Renvoi immédiat du dernier JSON (aucune attente de l'IA)
            telemetry = node.get_telemetry()
            await websocket.send_json(telemetry)

    except WebSocketDisconnect:
        print("[Terminé] Rupture de la liaison cible.")
        node.stop()
    except Exception as e:
        print(f"[Alerte] Erreur de communication : {e}")
        node.stop()
        await websocket.close()

app.mount("/static", StaticFiles(directory=".", html=True), name="static")