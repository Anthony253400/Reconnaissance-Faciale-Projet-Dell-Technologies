from qdrant_db import client, COLLECTION
from qdrant_client.models import Filter, FieldCondition, MatchValue, FilterSelector

def delete_person(name):
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

#delete_person("lea carminati")

results = client.scroll(
    collection_name=COLLECTION,
    limit=100,
    with_payload=True,
    with_vectors=False
)

for point in results[0]:
    print(point.id, point.payload)