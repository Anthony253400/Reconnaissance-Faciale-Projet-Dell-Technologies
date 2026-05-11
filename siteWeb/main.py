import sys
import io
import cv2
sys.path.append('../')  # add parent directory to path to import detecVisage
from fastapi import FastAPI, UploadFile, File, Form, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from detecVisage import FacesDetects_from_bytes, FacesDraw
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import mediapipe as mp
from faceAlignment import align_crop
from embeddings import get_embedding
from qdrant_db import save_embedding, create_collection, search_embedding



# create the FastAPI application
app = FastAPI()

model_path_blazeface='../model/blaze_face_short_range.tflite'

base_options = python.BaseOptions(model_asset_path=model_path_blazeface)
options = vision.FaceDetectorOptions(base_options=base_options)
detector = vision.FaceDetector.create_from_options(options)

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
    box, result, image = FacesDetects_from_bytes(contents,"mediapipe",detector)
    image_boxed = FacesDraw(image, box)

    # convert the boxed image to bytes
    image_boxes_bgr = cv2.cvtColor(image_boxed, cv2.COLOR_RGB2BGR)
    _, buffer = cv2.imencode('.jpg', image_boxes_bgr)
    image_bytes = buffer.tobytes()

    print(f"Received: {firstName} {lastName}, file: {photo.filename}")
    face_cropped = align_crop(image, result)

    embedding = get_embedding(face_cropped)
    print(f"Embedding shape: {embedding.shape}")

    create_collection()
    save_embedding(f"{firstName} {lastName}", embedding)

    # sends image to browser
    return StreamingResponse(io.BytesIO(image_bytes), media_type="image/jpeg")

@app.websocket("/ws/detect")
async def detec_video(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_bytes()
        box ,result, image = FacesDetects_from_bytes(data,"mediapipe",detector)

        names = []
        if result and result.detections:
            face_cropped = align_crop(image, result)
            if face_cropped is not None:
                embedding = get_embedding(face_cropped)
                name, score = search_embedding(embedding)
                score_str = f"{score:.2f}" if score else "?"
                names.append(f"{name} ({score_str})")

        await websocket.send_json({"faces": box, "names": names})


app.mount("/static", StaticFiles(directory=".", html=True), name="static")

