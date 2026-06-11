import cv2
import io
import threading
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
from mtcnn import MTCNN
from  mtcnn.utils.images  import  load_image
from typing import List



from fonction.loadModel import load_model
from fonction.faceDetection import FacesDetects_from_frame
from fonction.faceAlignment import align_crop
from fonction.faceEmbeddings import get_embedding
from fonction.qdrant_db import save_embedding, create_collection, search_embedding
from fonction.DrawBox import DrawBox
from fonction.bodyDetection import BodyDetect_from_frame
from fonction.tracker import BodyTracker 
from fonction.bodyAlignment import body_crop
from fonction.identity_smoother import SmootherBank




app = FastAPI()

# MODELE
model_mediapipe = load_model("blazeface_short",  False)
model_arcface = load_model("arcface",  True)
model_yolo = load_model("yolo",True)


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
        self.cap.set(cv2.CAP_PROP_FPS,30)

        print(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        print(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.lock_raw = threading.Lock()
        self.lock_out = threading.Lock()
       
        self.raw_frame = None
        self.latest_frame = None
        self.running = True


        self._t_capture = threading.Thread(target=self._capture_loop, daemon=True)
        self._t_ai = threading.Thread(target=self._ai_loop, daemon=True)


        self._t_capture.start()
        self._t_ai.start()


    def _capture_loop(self):
        """Lit la caméra aussi vite que possible — aucune IA ici"""
        while self.running:
            #t0 = time.perf_counter()
            ok, frame = self.cap.read()
            #t_capture = (time.perf_counter() - t0) * 1000
            if not ok:
                continue
            frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)

            with self.lock_raw:
                self.raw_frame = frame


    def _ai_loop(self):
        """AI pipeline thread — grabs the latest available frame and processes it.

        Per frame:
          1. detect faces (MediaPipe) and bodies (YOLO)
          2. for each face: align -> embed -> search Qdrant -> temporal smoothing
          3. feed clean face names to the BodyTracker to label each body
          4. draw boxes (green = face with name+score, red = body with name)
        On any error the raw frame is sent back so the stream never freezes.
        """
        while self.running:
            t_start_total = time.perf_counter()

            with self.lock_raw:
                frame = self.raw_frame
            if frame is None:
                continue

            try:
                # --- Face detection ---
                t0 = time.perf_counter()
                boxes_face, result, image_rgb = FacesDetects_from_frame(
                    frame, "mediapipe", model_mediapipe)
                t_detection_face_total = (time.perf_counter() - t0) * 1000

                # --- Body detection ---
                t0 = time.perf_counter()
                boxes_body, confidence = BodyDetect_from_frame(frame, model_yolo)
                t_detection_body = (time.perf_counter() - t0) * 1000

                # --- Face recognition ---
                labels = []        # decorated labels for FACE boxes: "name  0.83" / "inconnu"
                clean_names = []   # clean names aligned with boxes_face: "lea" / "" if unknown
                t_alignement = 0.0

                if result and result.detections:
                    # Align + crop every detected face (same order as boxes_face)
                    t0 = time.perf_counter()
                    crops = align_crop(frame, result, "mediapipe")
                    t_alignement = (time.perf_counter() - t0) * 1000

                    for i, face_cropped in enumerate(crops):
                        # embed the face and search the vector DB
                        embedding = get_embedding(face_cropped, model_arcface)
                        raw_name, raw_score = search_embedding(embedding)

                        # temporal smoothing: stabilizes the name and freezes the score
                        name, score = smoothers.update(i, raw_name, raw_score)

                        # clean name for the tracker ("" when unknown / no match)
                        clean = name if (name and name != "unknown") else ""
                        clean_names.append(clean)

                        # decorated label for the on-screen green box
                        labels.append(f"{name}  {score:.2f}"
                                      if clean and score is not None else "inconnu")

                    # drop smoothers for faces that left the scene
                    smoothers.prune(len(boxes_face))

                # --- Body tracking ---
                # Link each body to a person: IoU with a known face first,
                # then centroid distance, then body-embedding re-entry.
                crops_body = body_crop(frame, boxes_body) if boxes_body else []
                body_names = tracker.update(boxes_face, boxes_body, clean_names, crops_body)

                # --- Draw & encode ---
                t0 = time.perf_counter()
                image_boxed = DrawBox(image_rgb, boxes_face, 'green', labels=labels)
                image_boxed = DrawBox(image_boxed, boxes_body, 'red', labels=body_names)
                image_boxed = cv2.cvtColor(image_boxed, cv2.COLOR_BGR2RGB)
                _, buf = cv2.imencode('.jpg', image_boxed, [cv2.IMWRITE_JPEG_QUALITY, 80])
                t_formatage_final = (time.perf_counter() - t0) * 1000

                with self.lock_out:
                    self.latest_frame = buf.tobytes()

                # --- Per-stage timing (terminal) ---
                t_total = (time.perf_counter() - t_start_total) * 1000
                print(
                    f"Total:{t_total:.1f}ms | "
                    f"DetFaceTotal:{t_detection_face_total:.1f}ms | "
                    f"DetBody:{t_detection_body:.1f}ms | "
                    f"Alignement:{t_alignement:.1f}ms"
                )

            except Exception as e:
                # keep the stream alive: re-encode the raw frame (RGB->BGR to keep colors)
                print(f"Erreur _ai_loop : {e}")
                _, buf = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                with self.lock_out:
                    self.latest_frame = buf.tobytes()


    def get_frame(self) -> bytes | None:
        with self.lock_out:
            return self.latest_frame


    def release(self):
        self.running = False
        self.cap.release()

smoothers = SmootherBank(window=20, min_votes=10, min_score=0.45, score_hold=15)

camera = CameraStream(src=0)
tracker = BodyTracker(
    iou_threshold=0.1,
    max_distance=80,
    max_lost_frames=1800,
)

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
    photos:    List[UploadFile] = File(...)   # <-- era "photo" singolo
):
    print(f"\n start adding : {firstName} {lastName} | {len(photos)} frame ---")
    t_start = time.perf_counter()

    saved = 0
    name = f"{firstName} {lastName}".strip().lower()

    for i, photo in enumerate(photos):
        contents = await photo.read()

        try:
            boxes_face, result, image = FacesDetects_from_bytes(
                contents, "mediapipe", model_mediapipe)

            if not result or not result.detections:
                continue

            crops = align_crop(image, result, "mediapipe")
            if not crops:
                continue

            embedding = get_embedding(crops[0], model_arcface)
            save_embedding(name, embedding)
            saved += 1

        except Exception as e:
            print(f"[/add] skipped {i} frame: {e}")
            continue

    if saved == 0:
        return Response(status_code=422, content="No valid frames found.")

    print(f"[/add] {saved}/{len(photos)} saved embedding  | "
          f"total time: {(time.perf_counter() - t_start) * 1000:.1f} ms")

    return {"status": "ok", "frames_used": saved, "total_frames": len(photos)}    


app.mount("/static", StaticFiles(directory=".", html=True), name="static")



