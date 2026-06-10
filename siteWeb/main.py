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




app = FastAPI()

register_statistics_routes(app) 

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
        """Pipeline IA — prend la dernière frame dispo et la traite"""
        while self.running:
            t_start_total = time.perf_counter()


            with self.lock_raw:
                frame = self.raw_frame
            if frame is None:
                continue


            try:               
                # Face Detection
                t0 = time.perf_counter()
                boxes_face, result, image_rgb = FacesDetects_from_frame(frame, "mediapipe", model_mediapipe)
                t_detection_face_total = (time.perf_counter() - t0) * 1000


                # Body Detection
                t0 = time.perf_counter()
                boxes_body, confidence = BodyDetect_from_frame(frame, model_yolo)
                t_detection_body = (time.perf_counter() - t0) * 1000

                """
                names = [""] * len(boxes_face)
                clean_names = [""] * len(boxes_face)
                if result and result.detections:
                    crops = align_crop(frame, result,"mediapipe")
                    for i, face_cropped in enumerate(crops):
                        embedding = get_embedding(face_cropped,model_arcface)
                        name, score = search_embedding(embedding)
                        score_str = f"{score:.2f}" if score else "?"
                        names[i] = f"{name} ({score_str})"
                        clean_names[i] = name
                crops_body = body_crop(frame, boxes_body) if boxes_body else []
                body_names = tracker.update(boxes_face, boxes_body, clean_names, crops_body)

                image_boxed = DrawBox(image_rgb, boxes_face, 'green', labels=name)
                image_boxed = DrawBox(image_boxed, boxes_body, 'red',   labels=body_names)
                """
                
                labels = []
                if result and result.detections:
                    # Alignment
                    t0 = time.perf_counter()
                    crops = align_crop(frame, result , "mediapipe")
                    t_alignement = (time.perf_counter() - t0) * 1000


                    for face_cropped in crops:
                        # Embedding
                        t1 = time.perf_counter()
                        embedding = get_embedding(face_cropped, model_arcface)
                        #t_embedding += (time.perf_counter() - t1) * 1000


                        # Recherche BDD
                        t2 = time.perf_counter()
                        name, score = search_embedding(embedding)
                        print(name)
                        #t_recherche += (time.perf_counter() - t2) * 1000


                        labels.append(f"{name} ({score:.2f})" if name and score is not None else "inconnu")


                # Dessin & Encodage final
                t0 = time.perf_counter()

                image_boxed = DrawBox(image_rgb, boxes_face, 'green', labels=labels)
                image_boxed = DrawBox(image_boxed, boxes_body, 'red',   labels=labels)
                image_boxed = cv2.cvtColor(image_boxed,cv2.COLOR_BGR2RGB)
                _, buf = cv2.imencode('.jpg', image_boxed, [cv2.IMWRITE_JPEG_QUALITY, 80])
                t_formatage_final = (time.perf_counter() - t0) * 1000


                with self.lock_out:
                    self.latest_frame = buf.tobytes()


                t_total = (time.perf_counter() - t_start_total) * 1000
               
                # Affichage dans le terminal séparé par des ';'
                print(
                    f"Total:{t_total:.1f}ms | "
                    #f"Decodage:{t_decode:.1f}ms | "
                    #f"ConvColor:{t_cv_color:.1f}ms | "
                    #f"InferFace:{t_infer_face:.1f}ms | "
                    f"DetFaceTotal:{t_detection_face_total:.1f}ms | "
                    f"DetBody:{t_detection_body:.1f}ms | "
                    f"Alignement:{t_alignement:.1f}ms | "
                   # f"Embedding:{t_embedding:.1f}ms | "
                   # f"Recherche:{t_recherche:.1f}ms | "
                   # f"DessinEnc:{t_formatage_final:.1f}ms"
                )


            except Exception as e:
                print(f"Erreur _ai_loop : {e}")
                _, buf = cv2.imencode('.jpg', frame)
                with self.lock_out:
                    self.latest_frame = buf.tobytes()


    def get_frame(self) -> bytes | None:
        with self.lock_out:
            return self.latest_frame


    def release(self):
        self.running = False
        self.cap.release()


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



