import cv2
from mtcnn import MTCNN

def detecter_avec_mtcnn(chemin_image, chemin_sortie):
    image = cv2.imread(chemin_image)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    detector = MTCNN()
    
    resultats = detector.detect_faces(image_rgb)

    for visage in resultats:
        x, y, w, h = visage['box']
        # Dessiner le rectangle (OpenCV utilise BGR)
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)

    # Sauvegarder
    cv2.imwrite(chemin_sortie, image)
    print(f"Terminé. {len(resultats)} visage(s) trouvé(s).")

#detecter_avec_mtcnn('images/test.jpg', 'resultat_mtcnn.jpg')
from qdrant_client import QdrantClient

qdrant_client = QdrantClient(
    url="https://a4f168bd-0645-42cf-bc80-331b5ac315c0.eu-central-1-0.aws.cloud.qdrant.io:6333", 
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6ZDc2ZmY0NzgtYjIxYS00NzNlLWE1MWEtOTA5YTYwMmFlY2MwIn0.usibvJZxauXNXm_1nAlrSzo2ClzOUiwRTGqky0bR1ig",
)

print(qdrant_client.get_collections())