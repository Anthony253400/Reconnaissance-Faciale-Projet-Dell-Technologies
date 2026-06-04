# Third-Party Licenses & Credits

This document lists the third-party libraries, machine learning models, and open-source technologies used in this project.

**Context of Use:** This project is developed for strictly educational and academic purposes as part of a university curriculum, with technical mentoring from Dell Technologies teams. It has no commercial purpose and will not be deployed for industrial production.

---

### 1. Artificial Intelligence Models & Weights

* **YOLOv8 (Ultralytics)**
    * **Role:** Object and person detection model.
    * **Files:** `yolov8n.onnx`, `yolov8n_320.onnx`, `yolo26n.pt`
    * **License:** [AGPL-3.0](https://github.com/ultralytics/ultralytics/blob/main/LICENSE) (Use authorized within this strictly educational and non-profit framework).
    * **Source:** [Ultralytics GitHub](https://github.com/ultralytics/ultralytics)

* **ArcFace (InsightFace)**
    * **Role:** Facial feature extraction (embeddings generation).
    * **File:** `arc.onnx`
    * **License:** Source code under MIT License / Model weights under **Non-Commercial Research Use Only** clause. Use complies with the scope of this student research project.
    * **Source:** [InsightFace GitHub](https://github.com/deepinsight/insightface)

* **BlazeFace (Google MediaPipe)**
    * **Role:** Face detection (short and full range).
    * **Files:** `blaze_face_short_range.tflite`, `blaze_face_full_range.tflite`
    * **License:** [Apache License 2.0](https://github.com/google/mediapipe/blob/master/LICENSE)
    * **Source:** [MediaPipe GitHub](https://github.com/google/mediapipe)

* **OSNet (Torchreid)**
    * **Role:** Person Re-identification (ReID).
    * **Files:** `osnet_x0_25_imagenet.pth`, `osnet_x0_25_market.pth`
    * **License:** [MIT License](https://github.com/KaiyangZhou/deep-person-reid/blob/master/LICENSE)
    * **Source:** [Deep-Person-ReID GitHub](https://github.com/KaiyangZhou/deep-person-reid)

---

### 2. Infrastructure & Database

* **Qdrant**
    * **Role:** Vector Database for storing and rapidly comparing facial embeddings.
    * **License:** [Apache License 2.0](https://github.com/qdrant/qdrant/blob/master/LICENSE)
    * **Source:** [Qdrant GitHub](https://github.com/qdrant/qdrant)

---

**Note on model files:** In accordance with version control best practices and distribution license compliance, the model weight files (`.pt`, `.onnx`, `.tflite`, `.pth`) are not included in this source repository. They must be downloaded from their respective official sources to run the project locally.


