import os
import onnxruntime as ort
import cv2

CUDA_AVAILABLE = "CUDAExecutionProvider" in ort.get_available_providers()

# ---------------------------------------------------------------------------
# Absolute path to the project root (folder that CONTAINS the "model/" dir).
# This file is in fonction/, so the root is its parent's parent.
# Using absolute paths makes model loading independent of the current working
# directory (uvicorn can be launched from anywhere).
# ---------------------------------------------------------------------------
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODEL_DIR = os.path.join(_ROOT, "model")


def load_arcface(model_path: str = None, use_gpu: bool = CUDA_AVAILABLE):
    """
    Charge ArcFace (ONNX).
    use_gpu=True  → CUDAExecutionProvider
    use_gpu=False → CPUExecutionProvider
    """
    if model_path is None:
        model_path = os.path.join(_MODEL_DIR, "arc.onnx")

    if use_gpu:
        try:
            session = ort.InferenceSession(
                model_path,
                providers=[
                    ("CUDAExecutionProvider", {"device_id": 0}),
                    "CPUExecutionProvider",
                ]
            )
            print("[ModelLoader] ArcFace chargé sur GPU")
            return session
        except Exception as e:
            print(f"[ModelLoader] ArcFace GPU échoué ({e}), fallback CPU")
    else:
        session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"])
        print("[ModelLoader] ArcFace chargé sur CPU")
        return session


def load_yolo(model_path: str = None, use_gpu: bool = True, processeur_intel: bool = False):
    """
    Charge YOLOv8 au format ONNX.
    Retourne un tuple ('onnx'|'opencv', model_instance)
    """
    if model_path is None:
        model_path = os.path.join(_MODEL_DIR, "yolov8n_320.onnx")

    if use_gpu:
        try:
            providers = [
                ('CUDAExecutionProvider', {
                    'device_id': 0,
                    'arena_extend_strategy': 'kNextPowerOfTwo',
                    'cudnn_conv_algo_search': 'EXHAUSTIVE',
                    'do_copy_in_default_stream': True,
                }),
                'CPUExecutionProvider'
            ]

            # Utilisation de model_path et non du chemin en dur
            session = ort.InferenceSession(model_path, providers=providers)

            # Vérification vitale : ONNX a-t-il vraiment pris le GPU ?
            if session.get_providers()[0] != 'CUDAExecutionProvider':
                print("[ModelLoader]  CUDA ignoré, ONNX a basculé silencieusement sur CPU.")
            else:
                print("[ModelLoader] YOLOv8 chargé sur GPU (ONNX)")

            # On retourne 'onnx' au lieu de 'ultralytics' car c'est une session ort
            return ('onnx', session)

        except Exception as e:
            print(f"[ModelLoader] YOLOv8 GPU échoué ({e}), fallback vers CPU OpenCV")

    net = cv2.dnn.readNetFromONNX(model_path)

    if processeur_intel:
        # Optimisation spécifique pour processeurs Intel (nécessite OpenVINO compilé avec OpenCV)
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_INFERENCE_ENGINE)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    else:
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

    print("[ModelLoader] YOLOv8 chargé sur CPU (OpenCV) ")
    return ('opencv', net)


def load_blazeface(variant: str = "blazeface_short", use_gpu: bool = CUDA_AVAILABLE):
    """
    Charge BlazeFace (MediaPipe).
    variant = "blazeface_short" → modèle short range
    variant = "blazeface_full"  → modèle full range
    """
    # pick the right file from the variant name, then build an absolute path
    if variant == "blazeface_full":
        filename = "blaze_face_full_range.tflite"
    else:
        filename = "blaze_face_short_range.tflite"
    model_path = os.path.join(_MODEL_DIR, filename)

    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

    base_options = python.BaseOptions(model_asset_path=model_path)
    options      = vision.FaceDetectorOptions(base_options=base_options)
    detector     = vision.FaceDetector.create_from_options(options)
    print(f"[ModelLoader] BlazeFace ({filename}) chargé sur CPU ")
    return detector


def load_model(name: str, use_gpu: bool, processeur_intel: bool = False):
    if name == "yolo":
        return load_yolo(use_gpu=use_gpu, processeur_intel=processeur_intel)
    if name == "arcface":
        return load_arcface(use_gpu=use_gpu)
    if name == "blazeface_short":
        return load_blazeface(variant="blazeface_short", use_gpu=use_gpu)
    if name == "blazeface_full":
        return load_blazeface(variant="blazeface_full", use_gpu=use_gpu)
    else:
        raise ValueError(f"Modèle inconnu : '{name}'. Choix valides : yolo, arcface, blazeface")


if __name__ == "__main__":
    model = load_model("yolo", True)
    backend, session = model
    print(ort.get_all_providers())