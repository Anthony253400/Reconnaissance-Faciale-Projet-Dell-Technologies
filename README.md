# Reconnaissance Faciale Projet Dell Technologies

>Internship project 2026 - Léa Carminati & Anthony Miranda

>Dell Technologies Montpellier

This project consists of the design and deployment of an AI inference chain for facial recognition of a video stream in real time. The application integrates face detection, embedding extraction, and vector indexing to compare them with a set of reference photos provided by the user. A web interface allows managing the upload of the database, visualizing the live camera stream, and displaying the predicted identity. 

## Web Interface Features
* Live Video Stream Management:  Selection of available cameras and real-time display of the facial recognition system and person tracking.
* Database Administration: Updates to the face reference database directly from the web interface (adding, deleting, or modifying people to detect).


## Technical Stack & Architecture

| Component | Technology |
| :--- | :--- |
| **Frontend** | HTML / CSS / JS |
| **Backend** | FastAPI + Uvicorn |
| **Face Detection** | MediaPipe BlazeFace |
| **Alignment** | OpenCV (eye keypoint rotation) |
| **Face Embedding** | ArcFace (ONNX, 512-D) |
| **Body Detection** | YOLOv8n (ONNX, class 0) |
| **Re-identification** | OSNet x0.25 (torchreid) |
| **Tracker** | Hungarian Algorithm (scipy) + IoU + centroid distance |
| **Vector Database** | Qdrant (cosine similarity) |


## Author
Léa Carminati (@lea-c21)
Miranda Anthony (@Anthony253400)
