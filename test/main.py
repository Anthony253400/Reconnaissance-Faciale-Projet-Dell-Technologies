import cv2
import io
import threading
import sys
import time
import os
from concurrent.futures import ThreadPoolExecutor

sys.path.append('../')

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, Response

from loadModel import load_model
from detecVisage import FacesDetects_from_bytes
from faceAlignment import align_crop
from embeddings import get_embedding, get_embeddings_batch
from qdrant_db import save_embedding, create_collection, search_embedding
from DrawBox import DrawBox
from bodyDetection import BodyDetect_from_frame

app = FastAPI()

# ---------------------------------------------------------------------------
# Chargement des modèles (une seule fois au démarrage)
# ---------------------------------------------------------------------------
model_mediapipe = load_model("blazeface_full", True)
model_arcface   = load_model("arcface",        True)
model_yolo      = load_model("yolo",           True)

# Initialisation de la collection Qdrant une seule fois
# (était appelée à chaque POST /add — inutile et coûteux)
create_collection()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# CameraStream optimisé
# ---------------------------------------------------------------------------
class CameraStream:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        print(f"[Camera] {self.cap.get(cv2.CAP_PROP_FRAME_WIDTH):.0f}x"
              f"{self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT):.0f} "
              f"@ {self.cap.get(cv2.CAP_PROP_FPS):.0f}fps")

        self.lock_raw = threading.Lock()
        self.lock_out = threading.Lock()

        self.raw_frame    = None
        self.latest_frame = None
        self.running      = True

        # Event pour éviter le busy-loop CPU dans _ai_loop
        # (remplace le while frame is None: continue)
        self._new_frame_event = threading.Event()

        # Executor persistant — créé une seule fois, partagé entre les frames
        # 2 workers suffisent pour face + body en parallèle
        self._executor = ThreadPoolExecutor(max_workers=2)

        self._t_capture = threading.Thread(target=self._capture_loop, daemon=True)
        self._t_ai      = threading.Thread(target=self._ai_loop,      daemon=True)
        self._t_capture.start()
        self._t_ai.start()

    # -----------------------------------------------------------------------
    def _capture_loop(self):
        """Lit la caméra aussi vite que possible — aucune IA ici."""
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                continue
            with self.lock_raw:
                self.raw_frame = frame
            # Signale qu'une nouvelle frame est disponible
            self._new_frame_event.set()

    # -----------------------------------------------------------------------
    def _ai_loop(self):
        """Pipeline IA — prend la dernière frame dispo et la traite."""
        while self.running:
            # Attend une nouvelle frame (timeout 100ms pour re-vérifier running)
            # Remplace le busy-loop qui consommait 100% CPU quand frame=None
            if not self._new_frame_event.wait(timeout=0.1):
                continue
            self._new_frame_event.clear()

            with self.lock_raw:
                frame = self.raw_frame
            if frame is None:
                continue

            try:
                t_start = time.perf_counter()

                # --------------------------------------------------------
                # DÉTECTION PARALLÈLE : face + body sont indépendants,
                # on les soumet simultanément avant d'attendre quoi que ce soit.
                # Sur GPU léger (BlazeFace + YOLOv8n), gain ~10-30ms selon la charge.
                # --------------------------------------------------------
                fut_face = self._executor.submit(
                    FacesDetects_from_bytes,
                    frame, "mediapipe", model_mediapipe, True  # numpy=True
                )
                fut_body = self._executor.submit(
                    BodyDetect_from_frame,
                    frame, model_yolo
                )

                # Récupération avec timeout de sécurité (évite un freeze silencieux)
                try:
                    boxes_face, result, image_rgb = fut_face.result(timeout=2.0)
                except Exception as e:
                    print(f"[FACE] Erreur détection : {e}")
                    boxes_face, result, image_rgb = [], None, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                try:
                    boxes_body, confidence = fut_body.result(timeout=2.0)
                except Exception as e:
                    print(f"[BODY] Erreur détection : {e}")
                    boxes_body, confidence = [], []

                t_detection = (time.perf_counter() - t_start) * 1000

                # --------------------------------------------------------
                # EMBEDDING BATCH : toutes les crops en une seule inférence ArcFace
                # au lieu d'une boucle for (N fois plus rapide avec N > 1 visage)
                # --------------------------------------------------------
                labels = []
                t_align = t_embed = t_search = 0.0

                if result and result.detections:
                    t0 = time.perf_counter()
                    crops = align_crop(image_rgb, result, "mediapipe")
                    t_align = (time.perf_counter() - t0) * 1000

                    if crops:
                        # Un seul appel ONNX pour tous les visages
                        t0 = time.perf_counter()
                        embeddings = get_embeddings_batch(crops, model_arcface)
                        t_embed = (time.perf_counter() - t0) * 1000

                        # Recherches Qdrant en parallèle (une par visage)
                        t0 = time.perf_counter()
                        with ThreadPoolExecutor(max_workers=len(embeddings)) as search_pool:
                            search_results = list(search_pool.map(search_embedding, embeddings))
                        t_search = (time.perf_counter() - t0) * 1000

                        labels = [
                            f"{name} ({score:.2f})" if name and score is not None else "inconnu"
                            for name, score in search_results
                        ]

                # --------------------------------------------------------
                # Dessin & encodage final
                # --------------------------------------------------------
                t0 = time.perf_counter()
                image_boxed = DrawBox(image_rgb, boxes_face, 'green', labels=labels)
                image_boxed = DrawBox(image_boxed, boxes_body, 'red')
                _, buf = cv2.imencode('.jpg', image_boxed, [cv2.IMWRITE_JPEG_QUALITY, 80])
                t_draw = (time.perf_counter() - t0) * 1000

                with self.lock_out:
                    self.latest_frame = buf.tobytes()

                t_total = (time.perf_counter() - t_start) * 1000
                print(
                    f"Total:{t_total:.1f}ms;"
                    f"Detection(//):{t_detection:.1f}ms;"
                    f"Align:{t_align:.1f}ms;"
                    f"EmbedBatch:{t_embed:.1f}ms;"
                    f"Search(//):{t_search:.1f}ms;"
                    f"Draw:{t_draw:.1f}ms"
                )

            except Exception as e:
                print(f"[AI_LOOP] Erreur : {e}")
                _, buf = cv2.imencode('.jpg', frame)
                with self.lock_out:
                    self.latest_frame = buf.tobytes()

    # -----------------------------------------------------------------------
    def get_frame(self) -> bytes | None:
        with self.lock_out:
            return self.latest_frame

    def release(self):
        self.running = False
        self._executor.shutdown(wait=False)
        self.cap.release()


# ---------------------------------------------------------------------------
# Instance caméra
# ---------------------------------------------------------------------------
camera = CameraStream(src=0)


# ---------------------------------------------------------------------------
# Routes FastAPI
# ---------------------------------------------------------------------------
@app.get("/frame")
def get_frame():
    frame = camera.get_frame()
    if frame is None:
        return Response(status_code=503)
    return Response(content=frame, media_type="image/jpeg")


@app.post("/add")
async def add_person(
    firstName: str       = Form(...),
    lastName:  str       = Form(...),
    photo:     UploadFile = File(...)
):
    print(f"\n--- AJOUT : {firstName} {lastName} ---")
    t_start = time.perf_counter()
    contents = await photo.read()

    # Détection
    t0 = time.perf_counter()
    boxes_face, result, image = FacesDetects_from_bytes(
        contents, "mediapipe", model_mediapipe
    )
    print(f"[/add] Détection    : {(time.perf_counter()-t0)*1000:.1f} ms")

    # Alignement
    t0 = time.perf_counter()
    crops = align_crop(image, result, "mediapipe")
    print(f"[/add] Alignement   : {(time.perf_counter()-t0)*1000:.1f} ms")

    # Batch embedding (même si une seule photo, cohérence avec le pipeline live)
    t0 = time.perf_counter()
    embeddings = get_embeddings_batch(crops, model_arcface)
    print(f"[/add] Embedding    : {(time.perf_counter()-t0)*1000:.1f} ms")

    # Sauvegarde
    t0 = time.perf_counter()
    name_key = f"{firstName} {lastName}".strip().lower()
    for emb in embeddings:
        save_embedding(name_key, emb)
    print(f"[/add] Sauvegarde   : {(time.perf_counter()-t0)*1000:.1f} ms")

    # Retourne la photo avec les boîtes dessinées
    t0 = time.perf_counter()
    image_boxed = DrawBox(image, boxes_face, 'green')
    bgr = cv2.cvtColor(image_boxed, cv2.COLOR_RGB2BGR)
    _, buf = cv2.imencode('.jpg', bgr)
    print(f"[/add] Draw+Encode  : {(time.perf_counter()-t0)*1000:.1f} ms")
    print(f"--- FIN (total : {(time.perf_counter()-t_start)*1000:.1f} ms) ---\n")

    return StreamingResponse(io.BytesIO(buf.tobytes()), media_type="image/jpeg")


app.mount("/static", StaticFiles(directory=".", html=True), name="static")
