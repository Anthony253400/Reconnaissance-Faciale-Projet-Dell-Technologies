from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import uuid

client = QdrantClient(host="10.233.220.118", port=6333)
COLLECTION = "face"

def create_collection():
    existing = client.get_collections().collections
    names = [c.name for c in existing]
    if COLLECTION not in names:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(
                size=512,
                distance=Distance.COSINE
            )
        )

def save_embedding(name, embedding):
    client.upsert(
        collection_name=COLLECTION,
        points=[PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding.tolist(),
            payload={"name": name}
        )]
    )

def search_embedding(embedding, threshold=0.7):
    results = client.search(
        collection_name=COLLECTION,
        query_vector=embedding.tolist(),
        limit=1
    )
    if results and results[0].score >= threshold:
        return results[0].payload["name"], results[0].score
    return "Inconnu", None