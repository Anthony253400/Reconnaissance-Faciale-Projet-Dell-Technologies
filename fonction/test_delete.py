from qdrant_client import QdrantClient
from qdrant_client.http import models


client = QdrantClient(url="http://localhost:6333")

COLLECTION_NAME = "face"
CIBLE = "florient marchal" 

operation_info = client.delete(
    collection_name=COLLECTION_NAME,
    points_selector=models.FilterSelector(
        filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="name", # Assurez-vous que la clé correspond à votre payload
                    match=models.MatchValue(value=CIBLE),
                )
            ]
        )
    ),
)