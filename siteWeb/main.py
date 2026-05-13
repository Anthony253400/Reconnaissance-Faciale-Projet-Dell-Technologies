import sys
import io
import time
import cv2
sys.path.append('../')  # add parent directory to path to import detecVisage
from fastapi import FastAPI, UploadFile, File, Form, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from detecVisage import FacesDetects_from_bytes
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import mediapipe as mp
from faceAlignment import align_crop
from embeddings import get_embedding
from qdrant_db import save_embedding, create_collection, search_embedding
from DrawBox import  DrawBox , color_name_to_rgb
from bodyDetection import BodyDetect_from_bytes
<<<<<<< Updated upstream
from distanceBox import distance_box
import asyncio

=======
from load_model import load_model
>>>>>>> Stashed changes


# create the FastAPI application
app = FastAPI()

<<<<<<< Updated upstream
model_path_blazeface='../model/blaze_face_short_range.tflite'
model_yolov = cv2.dnn.readNetFromONNX("../model/yolov8n.onnx")
=======

model_yolo = load_model("yolo",False)
model_blazeface = load_model("blazeface",False)
model_arcface = load_model("arcface",False)

>>>>>>> Stashed changes

#Carte graphique
#model_yolov.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
#'model_yolov.setPreferableTarget(cv2.dnn.DNN_BACKEND_CUDA)


recognition_interval = 2 #en secondes
distane_threshold = 20  #en pixel

# CORS — allows the browser to send requests to FastAPI
# without this, the browser blocks requests for security reasons
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── ROUTE /add ──
# receives : firstName (text) + lastName (text) + photo (file)
# returns  : a confirmation message
@app.post("/add")
async def add_person(
    firstName: str = Form(...),
    lastName:  str = Form(...),
    photo:     UploadFile = File(...)
):
    contents = await photo.read()
    boxes_face, result, image = FacesDetects_from_bytes(contents,"mediapipe",model_blazeface)

    image_boxed = DrawBox(image, boxes_face, 'green')

    # convert the boxed image to bytes
    image_boxes_bgr = cv2.cvtColor(image_boxed, cv2.COLOR_RGB2BGR)
    _, buffer = cv2.imencode('.jpg', image_boxes_bgr)
    image_bytes = buffer.tobytes()

    #print(f"Received: {firstName} {lastName}, file: {photo.filename}")
    crops = align_crop(image, result)
    create_collection()

    for face_cropped in crops:
        embedding = get_embedding(face_cropped)
        #print(f"Embedding shape: {embedding.shape}")
    save_embedding(f"{firstName} {lastName}", embedding)

    # sends image to browser
    return StreamingResponse(io.BytesIO(image_bytes), media_type="image/jpeg")

@app.websocket("/ws/detect")
async def detec_video(websocket: WebSocket):
    await websocket.accept()
    #tread
    loop = asyncio.get_event_loop()

    tracked_faces = [] 
    while True:
        data = await websocket.receive_bytes()
<<<<<<< Updated upstream
        current_time = time.time()
        #boxes_face ,result, image = FacesDetects_from_bytes(data,"mediapipe",detector)
        #boxes_body, confidence, image = BodyDetect_from_bytes(data, model_yolov)
        task_face = loop.run_in_executor(None, FacesDetects_from_bytes, data, "mediapipe", detector)
        task_body = loop.run_in_executor(None, BodyDetect_from_bytes, data, model_yolov)
        (boxes_face, result, image), (boxes_body, confidence, _) = await asyncio.gather(task_face, task_body)
=======
        boxes_face ,result, image = FacesDetects_from_bytes(data,"mediapipe",model_blazeface)
        boxes_body, confidence, image = BodyDetect_from_bytes(data, model_yolo)
>>>>>>> Stashed changes

        names = []
        current_tracked_faces = []
        if result and result.detections:
            crops = align_crop(image, result)
            """
            for face_cropped in crops:
<<<<<<< Updated upstream
                embedding =  await loop.run_in_executor(None, get_embedding, face_cropped)
                name, score = await loop.run_in_executor(None, search_embedding, embedding)
=======
                embedding = get_embedding(face_cropped,model_arcface)
                name, score = search_embedding(embedding)
>>>>>>> Stashed changes
                score_str = f"{score:.2f}" if score else "?"
                names.append(f"{name} ({score_str})")
            """ 
            for i, face_cropped in enumerate(crops):
                box = boxes_face[i]
               
                # --- LOGIQUE DE TRACKING ET CACHE ---
                matched_face = None
                
                # On cherche si on connaît déjà ce visage (s'il était là à la frame précédente)
                for t_face in tracked_faces:
                    if distance_box(box, t_face["box"]) < distane_threshold:
                        matched_face = t_face
                        break
                
                # Si on l'a reconnu récemment (moins de X secondes)
                if matched_face and (current_time - matched_face["last_pred_time"]) < recognition_interval:
                    # On utilise le CACHE, on ne fait AUCUN calcul lourd !
                    name = matched_face["name"]
                    score = matched_face["score"]
                    last_pred_time = matched_face["last_pred_time"]
                
                # Si c'est un nouveau visage OU que le délai X est dépassé
                else:
                    # On lance la PRÉDICTION lourde (Embedding + Qdrant)
                    embedding = await loop.run_in_executor(None, get_embedding, face_cropped)
                    name, score = await loop.run_in_executor(None, search_embedding, embedding)
                    last_pred_time = current_time # On met à jour le chronomètre
                
                # On enregistre l'état actuel pour la prochaine frame
                current_tracked_faces.append({
                    "box": box,
                    "name": name,
                    "score": score,
                    "last_pred_time": last_pred_time
                })

                score_str = f"{score:.2f}" if score else "?"
                names.append(f"{name} ({score_str})")

        # Mise à jour de la mémoire pour la frame suivante
        tracked_faces = current_tracked_faces

        await websocket.send_json({"faces": boxes_face , "body":boxes_body ,  "names": names})





app.mount("/static", StaticFiles(directory=".", html=True), name="static")

