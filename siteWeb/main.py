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


from fonction.loadModel import load_model
from fonction.faceDetection import FacesDetects_from_frame
from fonction.faceAlignment import align_crop
from fonction.faceEmbeddings import get_embedding
from fonction.qdrant_db import save_embedding, create_collection, search_embedding
from fonction.DrawBox import DrawBox
from fonction.bodyDetection import BodyDetect_from_frame



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
                        t_embedding += (time.perf_counter() - t1) * 1000


                        # Recherche BDD
                        t2 = time.perf_counter()
                        name, score = search_embedding(embedding)
                        t_recherche += (time.perf_counter() - t2) * 1000


                        labels.append(f"{name} ({score:.2f})" if name and score is not None else "inconnu")


                # Dessin & Encodage final
                t0 = time.perf_counter()
                image_boxed = DrawBox(image_rgb, boxes_face, 'green', labels=labels)
                image_boxed = DrawBox(image_boxed, boxes_body, 'red', labels=labels)
                _, buf = cv2.imencode('.jpg', image_boxed, [cv2.IMWRITE_JPEG_QUALITY, 80])
                t_formatage_final = (time.perf_counter() - t0) * 1000


                with self.lock_out:
                    self.latest_frame = buf.tobytes()


                t_total = (time.perf_counter() - t_start_total) * 1000
               
                # Affichage dans le terminal séparé par des ';'
                print(
                    f"Total:{t_total:.1f}ms | "
                    f"Decodage:{t_decode:.1f}ms | "
                    f"ConvColor:{t_cv_color:.1f}ms | "
                    f"InferFace:{t_infer_face:.1f}ms | "
                    f"DetFaceTotal:{t_detection_face_total:.1f}ms | "
                    f"DetBody:{t_detection_body:.1f}ms | "
                    f"Alignement:{t_alignement:.1f}ms | "
                    f"Embedding:{t_embedding:.1f}ms | "
                    f"Recherche:{t_recherche:.1f}ms | "
                    f"DessinEnc:{t_formatage_final:.1f}ms"
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
    boxes_face, result, image = FacesDetects_from_frame(contents, "mediapipe", model_mediapipe)
    print(f"[/add] Détection : {(time.perf_counter() - t0) * 1000:.1f} ms")


    # Alignement
    t0 = time.perf_counter()
    crops = align_crop(image, result)
    print(f"[/add] Alignement : {(time.perf_counter() - t0) * 1000:.1f} ms")


    """
    await websocket.accept()
    meta = await websocket.receive_json()
    firstName = meta["firstName"]
    lastName  = meta["lastName"]
    create_collection()
"""

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



