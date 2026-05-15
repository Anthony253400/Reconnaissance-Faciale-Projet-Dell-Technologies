import onnxruntime as ort
import cv2
CUDA_AVAILABLE = "CUDAExecutionProvider" in ort.get_available_providers()



def load_arcface(model_path: str = "../model/arc.onnx", use_gpu: bool = CUDA_AVAILABLE):
    """
    Charge ArcFace (ONNX).
    use_gpu=True  → CUDAExecutionProvider
    use_gpu=False → CPUExecutionProvider
    """
    if use_gpu:
        try:
            session = ort.InferenceSession(
                model_path,
                providers=[
                    ("CUDAExecutionProvider", {"device_id": 0}),
                    "CPUExecutionProvider",
                ]
            )
            print("[ModelLoader] ArcFace chargé sur GPU ✅")
            return session
        except Exception as e:
            print(f"[ModelLoader] ArcFace GPU échoué ({e}), fallback CPU")
    else:
        session = ort.InferenceSession(
        model_path,
        providers=["CPUExecutionProvider"])
        print("[ModelLoader] ArcFace chargé sur CPU ✅")
        return session


def load_yolo(model_path: str = "../model/yolov8n.onnx", use_gpu: bool = CUDA_AVAILABLE):
    """
    Charge YOLOv8.
    use_gpu=True  → Ultralytics + CUDA
    use_gpu=False → OpenCV DNN CPU
    Retourne un tuple ('ultralytics'|'opencv', model)
    """
    if use_gpu:
        try:
            from ultralytics import YOLO
            model = YOLO(model_path)
            model.to('cuda')
            print("[ModelLoader] YOLOv8 chargé sur GPU ✅")
            return ('ultralytics', model)
        except Exception as e:
            print(f"[ModelLoader] YOLOv8 GPU échoué ({e}), fallback CPU")

    model = cv2.dnn.readNetFromONNX(model_path.replace('.pt', '.onnx'))
    print("[ModelLoader] YOLOv8 chargé sur CPU ✅")
    return ('opencv', model)


def load_blazeface(model_path: str="../model/blaze_face_short_range.tflite", use_gpu: bool = CUDA_AVAILABLE):
    """
    Charge BlazeFace (MediaPipe).
    use_gpu=True  → Delegate GPU
    use_gpu=False → CPU
    """
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

    base_options = python.BaseOptions(model_asset_path=model_path)
    options      = vision.FaceDetectorOptions(base_options=base_options)
    detector     = vision.FaceDetector.create_from_options(options)
    print("[ModelLoader] BlazeFace chargé sur CPU ✅")
    return detector

def load_model(name : str , use_gpu : bool):
    if name == "yolo":
        _, model = load_yolo(use_gpu = use_gpu)
        return model
    if name == "arcface":
        return load_arcface(use_gpu = use_gpu)
    if name == "blazeface":
        return load_blazeface(use_gpu=use_gpu)
    else:
        raise ValueError(f"Modèle inconnu : '{name}'. Choix valides : yolo, arcface, blazeface")