from fonction.qdrant_db import client, COLLECTION
from qdrant_client.models import Filter, FieldCondition, MatchValue, FilterSelector

#delete_person("lea carminati")

results = client.scroll(
    collection_name=COLLECTION,
    limit=100,
    with_payload=True,
    with_vectors=False
)

for point in results[0]:
    print(point.id, point.payload)