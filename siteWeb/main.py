import cv2
import io
import threading
import sys
import time  # <-- Ajout du module time
sys.path.append('../')  # add parent directory to path to import detecVisage

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, HTMLResponse, Response
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from loadModel import load_model

from detecVisage import FacesDetects_from_bytes
from faceAlignment import align_crop
from embeddings import get_embedding
from qdrant_db import save_embedding, create_collection, search_embedding
from DrawBox import DrawBox


app = FastAPI()

cap = cv2.VideoCapture(0)
print("Ouvert :", cap.isOpened())
ok, frame = cap.read()
print("Frame lue :", ok, frame.shape if ok else "ÉCHEC")
cap.release()

# MODELE
model_mediapipe = load_model("blazeface",  False)
model_arcface = load_model("arcface",  True)
model_yolo = load_model("yolo",  False)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CameraStream:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.lock_raw = threading.Lock()
        self.lock_out = threading.Lock()
        
        self.raw_frame = None        # frame brute (mise à jour à 30fps)
        self.latest_frame = None     # frame annotée (mise à jour à ~2fps)
        self.running = True

        # Thread 1 : capture pure, ultra rapide
        self._t_capture = threading.Thread(target=self._capture_loop, daemon=True)
        # Thread 2 : pipeline IA, lent mais indépendant
        self._t_ai = threading.Thread(target=self._ai_loop, daemon=True)

        self._t_capture.start()
        self._t_ai.start()

    def _capture_loop(self):
        """Lit la caméra aussi vite que possible — aucune IA ici"""
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                continue
            with self.lock_raw:
                self.raw_frame = frame   # toujours la frame la plus récente

    def _ai_loop(self):
        """Pipeline IA — prend la dernière frame dispo et la traite"""
        while self.running:
            # Récupère la dernière frame brute
            with self.lock_raw:
                frame = self.raw_frame
            if frame is None:
                continue

            try:
                _, img_bytes = cv2.imencode('.jpg', frame)
                boxes_face, result, image_rgb = FacesDetects_from_bytes(
                    img_bytes.tobytes(), "mediapipe", model_mediapipe
                )

                labels = []
                if result and result.detections:
                    crops = align_crop(image_rgb, result)
                    for face_cropped in crops:
                        embedding = get_embedding(face_cropped, model_arcface)
                        name, score = search_embedding(embedding)
                        labels.append(f"{name} ({score:.2f})" if name else "inconnu")

                image_boxed = DrawBox(image_rgb, boxes_face, 'green', labels=labels)
                bgr = cv2.cvtColor(image_boxed, cv2.COLOR_RGB2BGR)
                _, buf = cv2.imencode('.jpg', bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])

                with self.lock_out:
                    self.latest_frame = buf.tobytes()

            except Exception as e:
                print(f"Erreur _ai_loop : {e}")

    def get_frame(self) -> bytes | None:
        with self.lock_out:
            return self.latest_frame


camera = CameraStream(src=0)


# ── Générateur MJPEG ──────────────────────────────────────────────────────────
def mjpeg_generator():
    """Génère un flux MJPEG consommable par un <img> HTML."""
    boundary = b"--frame"
    while True:
        frame = camera.get_frame()
        if frame is None:
            continue
        yield (
            boundary + b"\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            frame + b"\r\n"
        )


# ── ROUTE /frame ──────────────────────────────────────────────────────────────
@app.get("/frame")
def get_frame():
    frame = camera.get_frame()
    if frame is None:
        return Response(status_code=503)
    return Response(content=frame, media_type="image/jpeg")


# ── ROUTE /add ────────────────────────────────────────────────────────────────
@app.post("/add")
async def add_person(
    firstName: str = Form(...),
    lastName:  str = Form(...),
    photo:     UploadFile = File(...)
):
    print(f"\n--- DEBUT AJOUT PERSONNE : {firstName} {lastName} ---")
    t_start = time.perf_counter()
    contents = await photo.read()

    # Détection
    t0 = time.perf_counter()
    boxes_face, result, image = FacesDetects_from_bytes(contents, "mediapipe", model_mediapipe)
    print(f"[/add] Détection : {(time.perf_counter() - t0) * 1000:.1f} ms")

    # Alignement
    t0 = time.perf_counter()
    crops = align_crop(image, result)
    print(f"[/add] Alignement : {(time.perf_counter() - t0) * 1000:.1f} ms")

    create_collection()

    for face_cropped in crops:
        # Embedding
        t0 = time.perf_counter()
        embedding = get_embedding(face_cropped, model_arcface)
        print(f"[/add] Embedding : {(time.perf_counter() - t0) * 1000:.1f} ms")

        # Sauvegarde
        t0 = time.perf_counter()
        save_embedding(f"{firstName} {lastName}".strip().lower(), embedding)
        print(f"[/add] Sauvegarde BDD : {(time.perf_counter() - t0) * 1000:.1f} ms")

    # Retourne la photo uploadée avec les boîtes dessinées
    t0 = time.perf_counter()
    image_boxed = DrawBox(image, boxes_face, 'green')
    bgr = cv2.cvtColor(image_boxed, cv2.COLOR_RGB2BGR)
    _, buf = cv2.imencode('.jpg', bgr)
    print(f"[/add] Dessin & Formatage final : {(time.perf_counter() - t0) * 1000:.1f} ms")
    print(f"--- FIN AJOUT PERSONNE (Temps total : {(time.perf_counter() - t_start) * 1000:.1f} ms) ---\n")

    return StreamingResponse(io.BytesIO(buf.tobytes()), media_type="image/jpeg")


app.mount("/static", StaticFiles(directory=".", html=True), name="static")