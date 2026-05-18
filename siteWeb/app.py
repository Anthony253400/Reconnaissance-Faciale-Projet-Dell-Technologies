import sys
import io
import cv2
import asyncio        # ← ajouté
import base64         # ← ajouté
import numpy as np    # ← ajouté
sys.path.append('../')

from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse

from loadModel import load_model

from faceAlignment import align_crop
from embeddings import get_embedding
from qdrant_db import save_embedding, create_collection, search_embedding
from DrawBox import  DrawBox , color_name_to_rgb
from bodyDetection import BodyDetect_from_bytes
from bodyAlignment import body_crop
from tracker import BodyTracker
from detecVisage import FacesDetects_from_bytes


# create the FastAPI application
app = FastAPI()

#MODEL
model_yolo = load_model("yolo",False)
model_blazeface = load_model("blazeface",False)
model_arcface = load_model("arcface",False)

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
    boxes_face, result, image = FacesDetects_from_bytes(contents, "mediapipe", model_blazeface)

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
    save_embedding(f"{firstName} {lastName}".strip().lower(), embedding)

    # sends image to browser
    return StreamingResponse(io.BytesIO(image_bytes), media_type="image/jpeg")

# ── HELPER : traitement d'une frame ──
def process_frame(frame_bgr: np.ndarray, tracker: BodyTracker):
    _, buf    = cv2.imencode('.jpg', frame_bgr)
    raw_bytes = buf.tobytes()

    boxes_face, result, image_rgb = FacesDetects_from_bytes(raw_bytes, "mediapipe", model_blazeface)
    boxes_body, confidence, _     = BodyDetect_from_bytes(raw_bytes, model_yolo)

    names       = [""] * len(boxes_face)
    clean_names = [""] * len(boxes_face)

    if result and result.detections:
        crops = align_crop(image_rgb, result)
        for i, face_cropped in enumerate(crops):
            embedding   = get_embedding(face_cropped)
            name, score = search_embedding(embedding)
            score_str   = f"{score:.2f}" if score else "?"
            names[i]       = f"{name} ({score_str})"
            clean_names[i] = name

    crops_body = body_crop(image_rgb, boxes_body) if boxes_body else []
    body_names = tracker.update(boxes_face, boxes_body, clean_names, crops_body)

    annotated = DrawBox(image_rgb, boxes_face, 'green')
    annotated = DrawBox(annotated,  boxes_body,  'blue')

    for i, box in enumerate(boxes_face):
        if names[i]:
            cv2.putText(annotated, names[i],
                        (int(box[0]), max(int(box[1]) - 10, 0)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
    for i, box in enumerate(boxes_body):
        label = body_names[i] if i < len(body_names) else ""
        if label:
            cv2.putText(annotated, label,
                        (int(box[0]), max(int(box[1]) - 10, 0)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 180, 255), 2)

    annotated_bgr = cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
    return annotated_bgr, {"faces": boxes_face, "body": boxes_body,
                           "names": names, "body_names": body_names}


@app.websocket("/ws/stream")
async def stream_video(websocket: WebSocket):
    await websocket.accept()
 
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        await websocket.send_json({"error": "Cannot open webcam"})
        await websocket.close()
        return

    tracker = BodyTracker()
 
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                await websocket.send_json({"error": "Failed to read frame"})
                break
 
            # Run detection + recognition (blocking — runs in the event loop;
            # move to a thread-pool executor if you need true async)
            annotated_bgr, meta = await asyncio.get_event_loop().run_in_executor(
                None, process_frame, frame, tracker
            )
 
            # Encode the annotated frame as JPEG → base64 string
            _, buf      = cv2.imencode('.jpg', annotated_bgr, [cv2.IMWRITE_JPEG_QUALITY, 75])
            jpg_b64     = base64.b64encode(buf.tobytes()).decode('utf-8')
 
            # Send frame + metadata in one message
            await websocket.send_json({
                "frame":      jpg_b64,   # base64 JPEG — display with <img src="data:image/jpeg;base64,...">
                "faces":      meta["faces"],
                "body":       meta["body"],
                "names":      meta["names"],
                "body_names": meta["body_names"],
            })
 
            # Small sleep to yield to the event loop / avoid hammering the CPU
            await asyncio.sleep(0.01)
 
    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        cap.release()
        print("Webcam released")   



app.mount("/static", StaticFiles(directory=".", html=True), name="static")