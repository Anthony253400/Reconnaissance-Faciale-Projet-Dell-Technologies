from ultralytics import YOLO

def export_yolo26():
    print("[Export] Téléchargement et chargement de YOLO26n...")
    model = YOLO("yolo26n.pt")  # Le modèle PyTorch sera téléchargé s'il n'est pas présent
    
    print("[Export] Conversion en ONNX FP16 Simplifié...")
    # L'argument simplify=True fait appel à onnxsim pour fusionner les opérations
    # L'argument half=True active le FP16
    model.export(
        format="onnx", 
        simplify=True, 
        half=True, 
        device=0 # Force l'export sur le GPU
    )
    print("[Export] Terminé ! Fichier yolo26n.onnx généré.")

if __name__ == "__main__":
    export_yolo26()

