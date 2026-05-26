import cv2
from embeddings import get_embedding
from qdrant_db import search_embedding
from detecVisage import FacesDetects_from_bytes
from faceAlignment import align_crop
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# initialize mediapipe
model_path = "model/blaze_face_short_range.tflite"
base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.FaceDetectorOptions(base_options=base_options)
detector = vision.FaceDetector.create_from_options(options)

# load test image and convert to bytes
with open("images/lea1.jpg", "rb") as f:
    image_bytes = f.read()

# same pipeline as /add
box, result, image = FacesDetects_from_bytes(image_bytes, "mediapipe", detector)
face_cropped = align_crop(image, result)
embedding = get_embedding(face_cropped)

name, score = search_embedding(embedding, threshold=0.65)
print(f"Face found: {name}, score: {score}")