import sys
import io
import cv2
sys.path.append('../') 
from fastapi import FastAPI, UploadFile, File, Form, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import mediapipe as mp

from fonction.detecVisage import FacesDetects_from_bytes
from fonction.faceAlignment import align_crop
from fonction.embeddings import get_embedding
from fonction.qdrant_db import save_embedding, create_collection, search_embedding
from fonction.DrawBox import  DrawBox
from fonction.bodyDetection import BodyDetect_from_bytes
from fonction.bodyAlignment import body_crop
from fonction.tracker import BodyTracker
from fonction.loadModel import load_model



#API
app = FastAPI()

#Model
model_mediapipe = load_model("blazeface_full",  True)
model_arcface = load_model("arcface",  True)
model_yolo = load_model("yolo",True)

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
    boxes_face, result, image = FacesDetects_from_bytes(contents,"mediapipe",detector)

    image_boxed = DrawBox(image, boxes_face, 'green')

    # convert the boxed image to bytes
    image_boxes_bgr = cv2.cvtColor(image_boxed, cv2.COLOR_RGB2BGR)
    _, buffer = cv2.imencode('.jpg', image_boxes_bgr)
    image_bytes = buffer.tobytes()

    #print(f"Received: {firstName} {lastName}, file: {photo.filename}")
    crops = align_crop(image, result)
    print(f"Crops trovati: {len(crops)} per {firstName} {lastName}")

    create_collection()

    for face_cropped in crops:
        embedding = get_embedding(face_cropped)
        #print(f"Embedding shape: {embedding.shape}")
        save_embedding(f"{firstName} {lastName}".strip().lower(), embedding)

    # sends image to browser
    return StreamingResponse(io.BytesIO(image_bytes), media_type="image/jpeg")

@app.websocket("/ws/detect")
async def detec_video(websocket: WebSocket):
    await websocket.accept()
    tracker = BodyTracker()
    while True:
        data = await websocket.receive_bytes()
        boxes_face ,result, image = FacesDetects_from_bytes(data,"mediapipe",detector)
        boxes_body, confidence, image = BodyDetect_from_bytes(data, model_path_yolov)

        names = [""] * len(boxes_face)
        clean_names = [""] * len(boxes_face)
        if result and result.detections:
            crops = align_crop(image, result)
            
            for i, face_cropped in enumerate(crops):
                embedding = get_embedding(face_cropped)
                name, score = search_embedding(embedding)
                score_str = f"{score:.2f}" if score else "?"
                names[i] = f"{name} ({score_str})"
                clean_names[i] = name
        crops_body = body_crop(image, boxes_body) if boxes_body else []
        body_names = tracker.update(boxes_face, boxes_body, clean_names, crops_body)
        #print(f"body_names: {body_names}")
        #print(f"clean_names: {clean_names}")
        await websocket.send_json({
            "faces": boxes_face , 
            "body":boxes_body ,  
            "names": names,
            "body_names": body_names
        })





app.mount("/static", StaticFiles(directory=".", html=True), name="static")

