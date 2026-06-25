from unicodedata import name

import cv2
import sys
import time
import numpy as np

sys.path.append('../')

from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.models import FilterSelector, PointStruct, VectorParams, Distance, PointIdsList, Filter, FieldCondition, MatchValue

from fonction.loadModel import load_model
from fonction.faceDetection import FacesDetects_from_frame
from fonction.faceAlignement2 import align_crop
from fonction.faceEmbeddings import get_embedding
from fonction.qdrant_db import save_embedding, create_collection, search_embedding, delete_person, list_people, rename_person, get_all_embeddings
from fonction.bodyDetection import BodyDetect_from_frame
from fonction.tracker import BodyTracker
from fonction.bodyAlignment import body_crop
from fonction.identity_smoother import SmootherBank

COLLECTION = 'face'
app = FastAPI()

# Models (loaded once at startup)
model_mediapipe = load_model("blazeface_short", False)
model_arcface   = load_model("arcface", True)
model_yolo      = load_model("yolo", True)

create_collection()   # ensure the 'face' collection exists

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
#  WebSocket detection endpoint (browser owns the webcam, server only runs AI)
# ============================================================================
@app.websocket("/ws/detect")
async def ws_detect(websocket: WebSocket):
    await websocket.accept()
    print("[ws/detect] client connected")

    # per-connection state, so identities reset when the page is reopened
    tracker = BodyTracker(iou_threshold=0.1, max_distance=80, frame_h=480)
    smoothers = SmootherBank(window=8, min_votes=3, min_score=0.55, score_hold=5)
    
    try:
        while True:
            # 1. receive one JPEG frame (bytes) from the browser
            data = await websocket.receive_bytes()

            # 2. decode JPEG -> RGB numpy
            arr = np.frombuffer(data, np.uint8)
            frame_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame_bgr is None:
                continue
            frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            print("FRAME SHAPE:", frame.shape)

            # 3. detection
            t0 = time.perf_counter()
            boxes_face, result, _ = FacesDetects_from_frame(frame, "mediapipe", model_mediapipe)
            t1 = time.perf_counter()
            boxes_body, _ = BodyDetect_from_frame(frame, model_yolo)
            t2 = time.perf_counter()

            # 4. recognize each face
            names, scores, clean_names = [], [], []
            if result and result.detections:
                crops = align_crop(frame, result, "mediapipe")
                for i, face_cropped in enumerate(crops):
                    embedding = get_embedding(face_cropped, model_arcface)
                    raw_name, raw_score = search_embedding(embedding)
                    name, score = smoothers.update(i, raw_name, raw_score)

                    clean = name if (name and name != "unknown") else ""
                    clean_names.append(clean)
                    names.append(clean if clean else "inconnu")
                    scores.append(round(float(score), 2) if score is not None else 0.0)
                smoothers.prune(len(boxes_face))
            t3 = time.perf_counter()

            print(f"face={1000*(t1-t0):.0f}ms body={1000*(t2-t1):.0f}ms recog={1000*(t3-t2):.0f}ms")

            # align_crop may drop profile faces: pad to keep lists aligned with boxes_face
            while len(names) < len(boxes_face):
                names.append("inconnu")
                scores.append(0.0)
                clean_names.append("")

            # 5. body tracking
            crops_body = body_crop(frame, boxes_body) if boxes_body else []
            body_names = tracker.update(boxes_face, boxes_body, clean_names, crops_body)

            # 6. reply with a small JSON
            await websocket.send_json({
                "faces":      [[int(v) for v in b] for b in boxes_face],
                "names":      names,
                "scores":     scores,
                "body":       [[int(v) for v in b] for b in boxes_body],
                "body_names": body_names,
            })

    except WebSocketDisconnect:
        print("[ws/detect] client disconnected")
    except Exception as e:
        print(f"[ws/detect] error: {e}")
        await websocket.close()


# ============================================================================
#  Register a person
# ============================================================================
@app.post("/add")
async def add_person(
    firstName: str = Form(...),
    lastName:  str = Form(...),
    photos:    List[UploadFile] = File(...)
):
    print(f"\n[/add] start: {firstName} {lastName} | {len(photos)} frames")
    t_start = time.perf_counter()

    saved = 0
    name = f"{firstName} {lastName}".strip().lower()
    #client = QdrantClient(host="localhost", port=6333 , prefer_grpc=True)
    #client = QdrantClient(path="..//qdrant_data")


    for i, photo in enumerate(photos):
        contents = await photo.read()
        try:
            # decode uploaded bytes -> RGB (same color path as detection)
            arr = np.frombuffer(contents, np.uint8)
            image_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if image_bgr is None:
                continue
            image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

            boxes_face, result, image = FacesDetects_from_frame(
                image, "mediapipe", model_mediapipe)
            if not result or not result.detections:
                continue

            crops = align_crop(image, result, "mediapipe")
            if not crops:
                continue

            embedding = get_embedding(crops[0], model_arcface)

            #save_embedding( name, embedding , client ,COLLECTION)
            save_embedding( name, embedding)

            saved += 1

        except Exception as e:
            print(f"[/add] skipped frame {i}: {e}")
            continue

    if saved == 0:
        return Response(status_code=422, content="No valid frames found.")

    print(f"[/add] {saved}/{len(photos)} embeddings saved | "
          f"{(time.perf_counter() - t_start) * 1000:.1f} ms")
    return {"status": "ok", "frames_used": saved, "total_frames": len(photos)}

@app.get("/people")
async def get_people():
    return {"people": list_people()}


@app.put("/people/{name}")
async def update_person(name: str, new_name: str = Body(..., embed=True)):
    new_name = new_name.strip().lower()
    if not new_name:
        return Response(status_code=422, content="New name is empty.")
    rename_person(name, new_name)
    return {"status": "renamed", "old_name": name, "new_name": new_name}

@app.delete("/people/{name}")
async def remove_person(name: str):
    delete_person(name)
    return {"status": "deleted", "name": name}

@app.on_event("shutdown")
def _close_qdrant():
    from fonction.qdrant_db import client
    client.close()

@app.get("/embeddings_3d")
async def embeddings_3d():
    """
    Projects all stored 512-D face embeddings down to 3 dimensions for
    visualization. Uses t-SNE when there are enough samples, and falls back
    to PCA (more stable) when there are very few points.
    Returns: {"points": [{"name": str, "x": float, "y": float, "z": float}, ...]}
    """
    names, vectors = get_all_embeddings()
    n = len(vectors)
    if n == 0:
        return {"points": []}

    X = np.asarray(vectors, dtype=np.float32)

    if n < 4:
        # too few points for t-SNE: use PCA, padding to 3 dims if needed
        from sklearn.decomposition import PCA
        comps = min(3, n, X.shape[1])
        coords = PCA(n_components=comps).fit_transform(X)
        if coords.shape[1] < 3:
            pad = np.zeros((n, 3 - coords.shape[1]), dtype=np.float32)
            coords = np.hstack([coords, pad])
    else:
        from sklearn.manifold import TSNE
        # perplexity must stay below the number of samples
        perplexity = min(30, max(2, n - 1))
        coords = TSNE(
            n_components=3,
            perplexity=perplexity,
            init="pca",
            random_state=42,
        ).fit_transform(X)

    points = [
        {"name": names[i], "x": float(coords[i, 0]),
         "y": float(coords[i, 1]), "z": float(coords[i, 2])}
        for i in range(n)
    ]
    return {"points": points}

app.mount("/static", StaticFiles(directory=".", html=True), name="static")