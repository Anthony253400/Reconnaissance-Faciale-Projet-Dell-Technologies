import sys
import io
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
from bodyAlignment import body_crop
from tracker import BodyTracker

# create the FastAPI application
app = FastAPI()

#path to the face detection model (blazeface) and body detection model (yolov8n)
model_path_blazeface='../model/blaze_face_short_range.tflite'
model_path_yolov = cv2.dnn.readNetFromONNX("../model/yolov8n.onnx")

#initialize the mediapipe face detectore with the blazeface model
base_options = python.BaseOptions(model_asset_path=model_path_blazeface)
options = vision.FaceDetectorOptions(base_options=base_options)
detector = vision.FaceDetector.create_from_options(options)

# allows the browser to send requests to FastAPI
# without this, the browser blocks requests for security reasons
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ADD PERSON
@app.websocket("/ws/add")
async def add_person(websocket: WebSocket):
    """
    websocket endpoint for registration of a new person in the database

    arguments:
    - receives a JSON message with 'firstName' and 'lastName'
    - then receives webcam frames as bytes through the websocket

    process:
    - receives the person's name as a JSON message
    - for each received frame, detects the face using mediapipe and extracts the aligned face crop
    - computes the embedding of the face crop using a pre-trained model
    - saves the embedding in the Qdrant vector database with the person's name as payload
    returns:
    - a confirmation message through the websocket once the embedding is saved

    """
    await websocket.accept()
    meta = await websocket.receive_json()
    firstName = meta["firstName"]
    lastName  = meta["lastName"]
    create_collection()

    try:
        while True:
            data = await websocket.receive_bytes()
            boxes_face, result, image = FacesDetects_from_bytes(data, "mediapipe", detector)
            if result and result.detections:
                crops = align_crop(image, result)
                for face_cropped in crops:
                    embedding = get_embedding(face_cropped)
                    save_embedding(f"{firstName} {lastName}".strip().lower(), embedding)
            await websocket.send_json({"status": "ok"})
    except Exception:
        pass

# DETECTION
@app.websocket("/ws/detect")
async def detec_video(websocket: WebSocket):
    """
    websocket endpoint for real-time face and body detection and recognition

    arguments:
    - receives webcam frames as bytes through the websocket

    process:
    - receives webcam frames as bytes through the websocket
    - detects faces and bodies in the frames using mediapipe and yolov8n
    - for each detected face, extracts the aligned face crop and computes its embedding
    - searches the embedding in the Qdrant database to find the best matching name (if above threshold)
    - assigns names to detected bodies based on their proximity to detected faces and embedding similarity (tracker.update)
    - sends back the detection results (face boxes, body boxes, names, scores) through
        the websocket for display on the frontend
    """
    await websocket.accept()
    tracker = BodyTracker()
    while True:
        data = await websocket.receive_bytes()
        boxes_face ,result, image = FacesDetects_from_bytes(data,"mediapipe",detector)
        boxes_body, confidence, image = BodyDetect_from_bytes(data, model_path_yolov)

        names = [""] * len(boxes_face)
        clean_names = [""] * len(boxes_face)
        scores = [0.0] * len(boxes_face)        

        if result and result.detections:
            crops = align_crop(image, result)
            
            for i, face_cropped in enumerate(crops):
                embedding = get_embedding(face_cropped)
                name, score = search_embedding(embedding)
                score_str = f"{score:.2f}" if score else "?"
                names[i] = f"{name} ({score_str})"
                clean_names[i] = name
                scores[i] = score
        crops_body = body_crop(image, boxes_body) if boxes_body else []
        body_names = tracker.update(boxes_face, boxes_body, clean_names, crops_body)
        #print(f"body_names: {body_names}")
        #print(f"clean_names: {clean_names}")
        await websocket.send_json({
            "faces": boxes_face , 
            "body":boxes_body ,  
            "names": names,
            "body_names": body_names,
            "scores": scores
        })





app.mount("/static", StaticFiles(directory=".", html=True), name="static")

