import onnxruntime as ort
import cv2
CUDA_AVAILABLE = "CUDAExecutionProvider" in ort.get_available_providers()


def load_arcface(model_path: str = "../model/arc.onnx", use_gpu: bool = CUDA_AVAILABLE ):
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


def load_yolo(model_path: str = "../model/yolov8n_320.onnx", use_gpu: bool = True, processeur_intel: bool = False):
    """
    Charge YOLOv8 au format ONNX.
    Retourne un tuple ('onnx'|'opencv', model_instance)
    """
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
                print("[ModelLoader] ⚠️ CUDA ignoré, ONNX a basculé silencieusement sur CPU.")
            else:
                print("[ModelLoader] YOLOv8 chargé sur GPU (ONNX) ✅")
               
            # On retourne 'onnx' au lieu de 'ultralytics' car c'est une session ort
            return ('onnx', session)
           
        except Exception as e:
            print(f"[ModelLoader] YOLOv8 GPU échoué ({e}), fallback vers CPU OpenCV")


    # --- Bloc CPU (OpenCV) ---
    print("[ModelLoader] Initialisation de YOLOv8 via OpenCV...")
    net = cv2.dnn.readNetFromONNX(model_path)
   
    if processeur_intel:
        # Optimisation spécifique pour processeurs Intel (nécessite OpenVINO compilé avec OpenCV)
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_INFERENCE_ENGINE)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    else:
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
       
    print("[ModelLoader] YOLOv8 chargé sur CPU (OpenCV) ✅")
    return ('opencv', net)






def load_blazeface(model_path: str="../model/blaze_face_short_range.tflite", use_gpu: bool = CUDA_AVAILABLE):
    """
    Charge BlazeFace (MediaPipe).
    use_gpu=True  → Delegate GPU
    use_gpu=False → CPU
    """
    if model_path =='blazeface_short':
        model_path = '../model/blaze_face_short_range.tflite'
    else:
        model_path = '../model/blaze_face_full_range.tflite'


    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision


    base_options = python.BaseOptions(model_asset_path=model_path)
    options      = vision.FaceDetectorOptions(base_options=base_options)
    detector     = vision.FaceDetector.create_from_options(options)
    print("[ModelLoader] BlazeFace chargé sur CPU ✅")
    return detector


def load_model(name : str , use_gpu : bool , processeur_intel :bool = False):
    if name == "yolo":
        return load_yolo(use_gpu = use_gpu, processeur_intel = processeur_intel)
       
    if name == "arcface":
        return load_arcface(use_gpu = use_gpu)
    if name == "blazeface_short":
        return load_blazeface(use_gpu=use_gpu)
    if name == "blazeface_full":
        return load_blazeface(model_path = name , use_gpu=use_gpu)
    else:
        raise ValueError(f"Modèle inconnu : '{name}'. Choix valides : yolo, arcface, blazeface")
   
if __name__ == "__main__" :
    model = load_model("yolo",True)
    backend , session = model


    print(ort.get_all_providers())

