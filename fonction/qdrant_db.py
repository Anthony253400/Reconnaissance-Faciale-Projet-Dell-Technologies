from qdrant_client import QdrantClient
from qdrant_client.models import FilterSelector, PointStruct, VectorParams, Distance, PointIdsList, Filter, FieldCondition, MatchValue
import uuid
import os

#anthony
#client = QdrantClient(host="10.233.220.118", port=6333)

#dell_guest
#client = QdrantClient(host="172.19.89.254", port=225)

#client = QdrantClient(host="localhost", port=6333 , prefer_grpc=True)
client = QdrantClient(path="..//qdrant_data")
"""
client = QdrantClient(host = os.getenv("qdrant_host" , 'localhost'),
                      port = int(os.getenv("Qdrant_port", 6333)),
                      prefer_grpc=True
                      )
"""
COLLECTION = "face"


def create_collection():
    """
    Creates a collection in the Qdrant vector database if it doesn't already exist.
    The collection is configured to store 512-dimensional vectors and use cosine distance for similarity search.
    """
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

#def save_embedding(name, embedding , client , COLLECTION):
def save_embedding(name, embedding):

    """
    Saves a face embedding in the Qdrant vector database with the person's name as payload.
    Args:
        name (str): The name of the person corresponding to the embedding.
        embedding (numpy.ndarray): The face embedding vector to be saved.
    
     The embedding is stored as a point in the specified collection, with a unique ID and the name as payload.
     The embedding vector is converted to a list before being stored in the database.
     """
    client.upsert(
        collection_name=COLLECTION,
        points=[PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding.tolist(),
            payload={"name": name}
        )]
    )

def search_embedding(embedding, threshold=0.5):
    """
    Searches for a face embedding in the Qdrant vector database.
    Args:
        embedding (numpy.ndarray): The face embedding vector to search for.
        threshold (float): The similarity threshold for matching.
    Returns:
        tuple: A tuple containing the name of the matched person and their similarity score, or ("unknown", None) if no match is found.
    """
    results = client.query_points(
        collection_name=COLLECTION,
        query=embedding.tolist(),
        limit=1
    ).points
    if results:
        #print(f"Score : {results[0].score}")  
        if results[0].score >= threshold:
            return results[0].payload["name"], results[0].score
    return "unknown", None

def delete_person(name):
    """
    Deletes all entries for a given person from the Qdrant vector database.
    Args:
        name (str): The name of the person whose entries should be deleted.
    
    The function uses a filter to identify all points in the collection that have a payload matching the specified name and deletes them from the database.
    """
    client.delete(
        collection_name=COLLECTION,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="name",
                        match=MatchValue(value=name)
                    )
                ]
            )
        )
    )
    print(f"Deleted all entries for: {name}")

