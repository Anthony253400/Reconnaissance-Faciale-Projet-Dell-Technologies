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
model_arcface = load_model("arcface",  False)
model_yolo = load_model("yolo",  False)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Capture caméra partagée ───────────────────────────────────────────────────
class CameraStream:
    """
    Thread dédié à la lecture de la webcam.
    Stocke la dernière frame traitée (JPEG bytes) accessible par tous les clients.
    """
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.lock = threading.Lock()
        self.latest_frame: bytes | None = None
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        while self.running:
            t_start_total = time.perf_counter()

            # --- 1. Capture Caméra ---
            t0 = time.perf_counter()
            ok, frame = self.cap.read()
            t_capture = (time.perf_counter() - t0) * 1000
            
            if not ok:
                continue

            try:
                # --- 2. Formatage initial (encodage jpg) ---
                t0 = time.perf_counter()
                _, img_bytes = cv2.imencode('.jpg', frame)
                t_encodage_init = (time.perf_counter() - t0) * 1000

                # --- 3. Détection de visages ---
                t0 = time.perf_counter()
                boxes_face, result, image_rgb = FacesDetects_from_bytes(
                    img_bytes.tobytes(), "mediapipe", model_mediapipe
                )
                t_detection = (time.perf_counter() - t0) * 1000

                # ── Reconnaissance ────────────────────────────────────────
                labels = []
                t_alignement = 0
                t_embedding = 0
                t_recherche = 0

                if result and result.detections:
                    # --- 4. Alignement / Redressement ---
                    t0 = time.perf_counter()
                    crops = align_crop(image_rgb, result)
                    t_alignement = (time.perf_counter() - t0) * 1000

                    for face_cropped in crops:
                        # --- 5. Embedding (Extraction de caractéristiques) ---
                        t1 = time.perf_counter()
                        embedding = get_embedding(face_cropped, model_arcface)
                        t_embedding += (time.perf_counter() - t1) * 1000

                        # --- 6. Recherche en base de données ---
                        t2 = time.perf_counter()
                        name, score = search_embedding(embedding)
                        t_recherche += (time.perf_counter() - t2) * 1000
                        
                        labels.append(f"{name} ({score:.2f})" if name else "inconnu")
                # ─────────────────────────────────────────────────────────

                # --- 7. Dessin des boxes et formatage final ---
                t0 = time.perf_counter()
                image_boxed = DrawBox(image_rgb, boxes_face, 'green', labels=labels)
                bgr = cv2.cvtColor(image_boxed, cv2.COLOR_RGB2BGR)
                _, buf = cv2.imencode('.jpg', bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
                t_formatage_final = (time.perf_counter() - t0) * 1000

                with self.lock:
                    self.latest_frame = buf.tobytes()

                t_total = (time.perf_counter() - t_start_total) * 1000

                # ── AFFICHAGE DES TEMPS DANS LA CONSOLE ──
                print(f"[LOOP] Total: {t_total:.1f}ms | Cap: {t_capture:.1f}ms | Enc1: {t_encodage_init:.1f}ms | Det: {t_detection:.1f}ms | Ali: {t_alignement:.1f}ms | Emb: {t_embedding:.1f}ms | Rech: {t_recherche:.1f}ms | Dessin/Enc2: {t_formatage_final:.1f}ms")

            except Exception as e:
                print(f"Erreur dans _loop : {e}")
                _, buf = cv2.imencode('.jpg', frame)
                with self.lock:
                    self.latest_frame = buf.tobytes()

    def get_frame(self) -> bytes | None:
        with self.lock:
            return self.latest_frame

    def release(self):
        self.running = False
        self.cap.release()


camera = CameraStream(src=0)   # 0 = webcam par défaut


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