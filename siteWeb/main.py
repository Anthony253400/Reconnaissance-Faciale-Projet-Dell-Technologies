import cv2
import io
import threading
from concurrent.futures import ThreadPoolExecutor
import sys
import time
import datetime
import os

sys.path.append('../')

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
from bodyDetection import BodyDetect_from_frame

from mtcnn import MTCNN
from  mtcnn.utils.images  import  load_image

app = FastAPI()

# MODELE
model_mediapipe = load_model("blazeface_full",  False)
model_arcface = load_model("arcface",  False)
model_yolo = load_model("yolo",False)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CameraStream:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        self.lock_raw   = threading.Lock()
        self.lock_out   = threading.Lock()
        self._new_frame = threading.Event()

        self.raw_frame   = None
        self.latest_frame = None
        self.running     = True

        # Executor créé une seule fois
        self._executor = ThreadPoolExecutor(max_workers=2)

        self._t_capture = threading.Thread(target=self._capture_loop, daemon=True)
        self._t_ai      = threading.Thread(target=self._ai_loop,      daemon=True)
        self._t_capture.start()
        self._t_ai.start()
    
    def _capture_loop(self): 
        while self.running: 
            ok, frame = self.cap.read() 
            if not ok: 
                continue 
            with self.lock_raw: 
                self.raw_frame = frame 
            self._new_frame.set() 



    def _ai_loop(self):
        import time # S'assurer que le module est bien importé

        while self.running:
            if not self._new_frame.wait(timeout=0.1):
                continue
            self._new_frame.clear()

            with self.lock_raw:
                frame = self.raw_frame
            if frame is None:
                continue

            try:
                # ==========================================
                # DÉMARRAGE DU CYCLE D'OBSERVATION
                # ==========================================
                t_start_loop = time.perf_counter()

                # --- 1. Lancement asynchrone des modèles ---
                fut_face = self._executor.submit(
                    FacesDetects_from_bytes,
                    frame, "mediapipe", model_mediapipe, numpy=True
                )
                fut_body = self._executor.submit(
                    BodyDetect_from_frame,
                    frame, model_yolo
                )

                # --- 2. Collecte des résultats (Synchronisation) ---
                t_wait_face = time.perf_counter()
                try:
                    boxes_face, result, image_rgb = fut_face.result(timeout=2.0)
                except Exception as e:
                    boxes_face, result, image_rgb = [], None, frame
                t_detection_face_total = (time.perf_counter() - t_wait_face) * 1000

                t_wait_body = time.perf_counter()
                try:
                    boxes_body, confidence = fut_body.result(timeout=2.0)
                except Exception as e:
                    boxes_body, confidence = [], []
                t_detection_body = (time.perf_counter() - t_wait_body) * 1000


                # ==========================================
                # PIPELINE BIOMÉTRIQUE (Séquentiel)
                # ==========================================
                labels = []
                t_alignement = 0.0
                t_embedding = 0.0
                t_recherche = 0.0

                if result and result.detections:
                    # -- Alignement et Crop --
                    t_align_start = time.perf_counter()
                    crops = align_crop(image_rgb, result, "mediapipe")
                    t_alignement = (time.perf_counter() - t_align_start) * 1000

                    # -- Traitement de chaque visage détecté --
                    for face_cropped in crops:
                        # Embedding (ArcFace)
                        t_embed_start = time.perf_counter()
                        embedding = get_embedding(face_cropped, model_arcface)
                        t_embedding += (time.perf_counter() - t_embed_start) * 1000

                        # Recherche Vectorielle / Matching
                        t_search_start = time.perf_counter()
                        name, score = search_embedding(embedding)
                        t_recherche += (time.perf_counter() - t_search_start) * 1000
                        
                        labels.append(f"{name} ({score:.2f})" if name else "inconnu")

                # ==========================================
                # RENDU ET ENCODAGE
                # ==========================================
                t_draw_start = time.perf_counter()
                
                image_boxed = DrawBox(image_rgb, boxes_face, 'green', labels=labels)
                image_boxed = DrawBox(image_boxed, boxes_body, 'red')
                _, buf = cv2.imencode('.jpg', image_boxed, [cv2.IMWRITE_JPEG_QUALITY, 80])

                with self.lock_out:
                    self.latest_frame = buf.tobytes()

                t_formatage_final = (time.perf_counter() - t_draw_start) * 1000

                # ==========================================
                # CLÔTURE ET AFFICHAGE TÉLÉMÉTRIE
                # ==========================================
                t_total = (time.perf_counter() - t_start_loop) * 1000

                print(
                    f"Face:{t_detection_face_total:.1f}ms "
                    f"Body:{t_detection_body:.1f}ms "
                    f"Align:{t_alignement:.1f}ms "
                    f"Embed:{t_embedding:.1f}ms "
                    f"Search:{t_recherche:.1f}ms "
                    f"Draw:{t_formatage_final:.1f}ms "
                    f"TOTAL:{t_total:.1f}ms"
                )

            except Exception as e:
                print(f"[ERREUR] Échec du pipeline: {e}")









    def release(self):
        self.running = False
        self._executor.shutdown(wait=False)
        self.cap.release()

    def get_frame(self) -> bytes | None:
        with self.lock_out:
            return self.latest_frame

    def release(self):
        self.running = False
        self.cap.release()

camera = CameraStream(src=0)

#frame
@app.get("/frame")
def get_frame():
    frame = camera.get_frame()
    if frame is None:
        return Response(status_code=503)
    return Response(content=frame, media_type="image/jpeg")


#ADD people ad bd
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