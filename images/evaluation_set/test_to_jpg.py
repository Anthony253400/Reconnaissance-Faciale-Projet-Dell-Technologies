from pathlib import Path
from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()

def process_folder(folder_path: str, quality: int = 90):
    folder = Path(folder_path)
    heic_files = list(folder.glob("*.heic")) + list(folder.glob("*.HEIC"))

    if not heic_files:
        print(f"Nessun file HEIC trovato in {folder}")
        return

    for heic_path in heic_files:
        jpeg_path = heic_path.with_suffix(".jpg")

        if jpeg_path.exists():
            heic_path.unlink(missing_ok=True)  # non dà errore se il file non c'è già
            print(f"🗑 JPEG già esistente, eliminato HEIC: {heic_path.name}")
        else:
            try:
                Image.open(heic_path).convert("RGB").save(jpeg_path, "JPEG", quality=quality)
                heic_path.unlink()
                print(f"Convertito ed eliminato: {heic_path.name}")
            except Exception as e:
                print(f"Errore su {heic_path.name}: {e}")

folders = [
    "images/evaluation_set/robin henry/"
]

for f in folders:
    print(f"\n{f}")
    process_folder(f)