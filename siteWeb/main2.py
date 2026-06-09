import cv2
import io
import threading
import sys
import time
from datetime import datetime
import os
import numpy as np


sys.path.append('../')


from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, Response


from fonction.loadModel import load_model
from fonction.faceDetection import FacesDetects_from_frame
from fonction.faceAlignment import align_crop
from fonction.faceEmbeddings import get_embedding
from fonction.qdrant_db import save_embedding, create_collection, search_embedding
from fonction.DrawBox import DrawBox
from fonction.bodyDetection import BodyDetect_from_frame
from fonction.bodyAlignment import body_crop
from fonction.tracker import BodyTracker




app = FastAPI()


# ── Modèles ──────────────────────────────────────────────────────────────────
model_mediapipe = load_model("blazeface_short", False)
model_arcface   = load_model("arcface",         True)
model_yolo      = load_model("yolo",            True)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)




class CameraStream:
    """
    3 threads indépendants :


      _capture_loop     → lit la caméra brute aussi vite que possible
      _detection_loop   → détection visage + corps CHAQUE frame (BlazeFace + YOLOv8)
                          + dessin avec le cache d'identités
      _recognition_loop → embedding + Qdrant toutes les N frames (ArcFace)
                          → met à jour identity_cache


    Données partagées entre threads :
      raw_frame        : dernière frame brute          (capture → détection)
      detection_state  : boîtes + crops du dernier run (détection → reco)
      identity_cache   : {face_index: (nom, score)}    (reco → détection/dessin)
      latest_frame     : JPEG final annoté             (détection → /frame)
    """


    RECO_EVERY_N = 10   # reconnaissance toutes les N frames de détection


    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.cap.set(cv2.CAP_PROP_FPS, 30)


        print(f"Résolution : "
              f"{self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x"
              f"{self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")


        # ── Locks ───────────────────────────────────────────────────────────
        self.lock_raw       = threading.Lock()
        self.lock_detection = threading.Lock()
        self.lock_identity  = threading.Lock()
        self.lock_out       = threading.Lock()


        # ── État partagé ─────────────────────────────────────────────────────
        self.raw_frame       = None   # frame BGR→RGB brute
        self.latest_frame    = None   # JPEG final
        self.detection_state = None   # dict avec boîtes, crops, image_rgb
        self.identity_cache  = {}     # {face_idx: (nom, score)}
        self.running         = True


        # ── Debug crops ──────────────────────────────────────────────────────
        self.DEBUG_SAVE    = True
        self.DEBUG_DIR     = "debug_crops"
        self.frame_counter = 0
        os.makedirs(self.DEBUG_DIR, exist_ok=True)


        # ── Tracker corps ─────────────────────────────────────────────────────
        self.tracker = BodyTracker(
            iou_threshold=0.1,
            max_distance=80,
            max_lost_frames=1800,
            reentry_threshold=0.75,
        )


        # ── Compteur de frames de détection ──────────────────────────────────
        self._det_count = 0


        # ── Événement : signal du thread détection vers thread reco ──────────
        self._reco_event = threading.Event()


        # ── Démarrage threads ─────────────────────────────────────────────────
        self._t_capture = threading.Thread(target=self._capture_loop,     daemon=True)
        self._t_det     = threading.Thread(target=self._detection_loop,   daemon=True)
        self._t_reco    = threading.Thread(target=self._recognition_loop,  daemon=True)


        self._t_capture.start()
        self._t_det.start()
        self._t_reco.start()


    # =========================================================================
    # Thread 1 — Capture brute
    # =========================================================================
    def _capture_loop(self):
        """Lit la caméra le plus vite possible. Aucune IA."""
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                continue
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            with self.lock_raw:
                self.raw_frame = frame


    # =========================================================================
    # Thread 2 — Détection CHAQUE frame + dessin
    # =========================================================================
    def _detection_loop(self):
        """
        Chaque itération :
          1. Détection visages (BlazeFace) + corps (YOLOv8)
          2. Alignement & crop des visages
          3. Crop des corps
          4. Mise à jour detection_state  → signale le thread reco toutes les N frames
          5. Lecture du cache d'identités (résultat du thread reco)
          6. Tracker corps (liaison face↔body + re-id)
          7. Dessin + encodage JPEG
        """
        while self.running:
            t_start = time.perf_counter()


            with self.lock_raw:
                frame = self.raw_frame
            if frame is None:
                continue


            try:
                # 1a. Détection visages
                t0 = time.perf_counter()
                boxes_face, result, image_rgb = FacesDetects_from_frame(
                    frame, "mediapipe", model_mediapipe
                )
                t_face = (time.perf_counter() - t0) * 1000


                # 1b. Détection corps
                t0 = time.perf_counter()
                boxes_body, _ = BodyDetect_from_frame(frame, model_yolo)
                t_body = (time.perf_counter() - t0) * 1000


                # 2. Alignement & crop visages
                face_crops = []
                if result and result.detections:
                    face_crops = align_crop(frame, result, "mediapipe")


                # 3. Crop corps
                body_crops = body_crop(image_rgb, boxes_body) if boxes_body else []


                # 4. Mise à jour detection_state + signal reco si nécessaire
                with self.lock_detection:
                    self.detection_state = {
                        "boxes_face" : boxes_face,
                        "boxes_body" : boxes_body,
                        "face_crops" : face_crops,
                        "body_crops" : body_crops,
                        "image_rgb"  : image_rgb,
                    }


                self._det_count += 1
                if self._det_count % self.RECO_EVERY_N == 0:
                    self._reco_event.set()  # réveille _recognition_loop


                # 5. Lecture du cache identités (thread-safe, non bloquant)
                with self.lock_identity:
                    id_cache = dict(self.identity_cache)


                # Construction labels visages depuis le cache
                face_labels            = []
                face_names_for_tracker = []
                for i in range(len(boxes_face)):
                    entry = id_cache.get(i)
                    if entry:
                        name, score = entry
                        if name and name != "unknown":
                            label = f"{name} ({score:.2f})" if score is not None else name
                            face_labels.append(label)
                            face_names_for_tracker.append(name)
                        else:
                            face_labels.append("")
                            face_names_for_tracker.append("")
                    else:
                        face_labels.append("")
                        face_names_for_tracker.append("")


                # 6. Tracker corps
                t0 = time.perf_counter()
                body_names = self.tracker.update(
                    face_boxes = boxes_face,
                    body_boxes = boxes_body,
                    face_names = face_names_for_tracker,
                    body_crops = body_crops,
                )
                t_tracker = (time.perf_counter() - t0) * 1000


                # 7. Dessin + encodage
                t0  = time.perf_counter()
                out = DrawBox(image_rgb, boxes_face, 'green', labels=face_labels)
                out = DrawBox(out,       boxes_body, 'red',   labels=body_names)
                out = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
                _, buf = cv2.imencode('.jpg', out, [cv2.IMWRITE_JPEG_QUALITY, 80])
                t_draw = (time.perf_counter() - t0) * 1000


                with self.lock_out:
                    self.latest_frame = buf.tobytes()


                t_total = (time.perf_counter() - t_start) * 1000
                print(
                    f"[DET #{self._det_count}] "
                    f"Total:{t_total:.0f}ms | "
                    f"Face:{t_face:.0f}ms | "
                    f"Body:{t_body:.0f}ms | "
                    f"Tracker:{t_tracker:.0f}ms | "
                    f"Draw:{t_draw:.0f}ms | "
                    f"IDs:{id_cache}"
                )


            except Exception as e:
                print(f"[DET] Erreur : {e}")
                import traceback; traceback.print_exc()
                try:
                    _, buf = cv2.imencode(
                        '.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    )
                    with self.lock_out:
                        self.latest_frame = buf.tobytes()
                except Exception:
                    pass


    # =========================================================================
    # Thread 3 — Reconnaissance toutes les N frames
    # =========================================================================
    def _recognition_loop(self):
        """
        Attend le signal du thread détection.
        Calcule les embeddings ArcFace et interroge Qdrant.
        Met à jour identity_cache avec les nouveaux résultats.
        Le thread détection continue de tourner pendant ce temps
        et affiche le DERNIER cache connu.
        """
        while self.running:
            # Attend le signal (timeout 1s pour vérifier self.running)
            if not self._reco_event.wait(timeout=1.0):
                continue
            self._reco_event.clear()


            # Snapshot thread-safe
            with self.lock_detection:
                state = self.detection_state
            if state is None or not state["face_crops"]:
                continue


            face_crops = state["face_crops"]
            t_start    = time.perf_counter()
            new_cache  = {}


            for i, face_cropped in enumerate(face_crops):


                # Debug : sauvegarde 1 crop sur 10
                self.frame_counter += 1
                if self.DEBUG_SAVE and self.frame_counter % 10 == 0:
                    ts   = datetime.now().strftime("%H%M%S_%f")
                    path = os.path.join(
                        self.DEBUG_DIR,
                        f"f{self.frame_counter:06d}_face{i}_{ts}.jpg"
                    )
                    cv2.imwrite(path, cv2.cvtColor(face_cropped, cv2.COLOR_RGB2BGR))


                # Embedding ArcFace
                t0        = time.perf_counter()
                embedding = get_embedding(face_cropped, model_arcface)
                t_embed   = (time.perf_counter() - t0) * 1000


                # Recherche Qdrant
                t0          = time.perf_counter()
                name, score = search_embedding(embedding)
                t_search    = (time.perf_counter() - t0) * 1000


                new_cache[i] = (name, score)


                score_str = f"{score:.3f}" if score is not None else "None"
                print(
                    f"[RECO] face {i} → {name} (score={score_str}) | "
                    f"embed:{t_embed:.0f}ms | search:{t_search:.0f}ms"
                )


            # Mise à jour atomique du cache
            with self.lock_identity:
                self.identity_cache = new_cache


            print(
                f"[RECO] ✓ {len(face_crops)} visage(s) en "
                f"{(time.perf_counter()-t_start)*1000:.0f}ms"
            )


    # =========================================================================
    # API
    # =========================================================================
    def get_frame(self) -> bytes | None:
        with self.lock_out:
            return self.latest_frame


    def release(self):
        self.running = False
        self.cap.release()




# ── Instanciation ─────────────────────────────────────────────────────────────
camera = CameraStream(src=0)




# ── Routes ────────────────────────────────────────────────────────────────────


@app.get("/frame")
def get_frame():
    frame = camera.get_frame()
    if frame is None:
        return Response(status_code=503)
    return Response(content=frame, media_type="image/jpeg")




@app.post("/add")
async def add_person(
    firstName: str        = Form(...),
    lastName:  str        = Form(...),
    photo:     UploadFile = File(...)
):
    print(f"\n--- AJOUT : {firstName} {lastName} ---")
    t_start  = time.perf_counter()
    contents = await photo.read()


    nparr   = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    image   = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)


    t0 = time.perf_counter()
    boxes_face, result, image = FacesDetects_from_frame(
        image, "mediapipe", model_mediapipe
    )
    print(f"[/add] Détection : {(time.perf_counter()-t0)*1000:.1f} ms")


    t0    = time.perf_counter()
    crops = align_crop(image, result, "mediapipe")
    print(f"[/add] Alignement : {(time.perf_counter()-t0)*1000:.1f} ms")


    create_collection()


    for face_cropped in crops:
        t0        = time.perf_counter()
        embedding = get_embedding(face_cropped, model_arcface)
        print(f"[/add] Embedding : {(time.perf_counter()-t0)*1000:.1f} ms")


        t0 = time.perf_counter()
        save_embedding(f"{firstName} {lastName}".strip().lower(), embedding)
        print(f"[/add] Sauvegarde : {(time.perf_counter()-t0)*1000:.1f} ms")


    image_boxed = DrawBox(image, boxes_face, 'green')
    bgr         = cv2.cvtColor(image_boxed, cv2.COLOR_RGB2BGR)
    _, buf      = cv2.imencode('.jpg', bgr)
    print(f"--- FIN ({(time.perf_counter()-t_start)*1000:.1f} ms) ---\n")


    return StreamingResponse(io.BytesIO(buf.tobytes()), media_type="image/jpeg")




app.mount("/static", StaticFiles(directory=".", html=True), name="static")




