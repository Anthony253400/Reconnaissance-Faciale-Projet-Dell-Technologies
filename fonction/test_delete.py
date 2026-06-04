from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import UpdateStatus



client = QdrantClient(url="http://localhost:6333")

def delete_qdrant_vector_byname(client: QdrantClient, COLLECTION_NAME: str, CIBLE) -> bool:
    operation_info = client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="name",
                        match=models.MatchValue(value=CIBLE),
                    )
                ]
            )
        ),
    )



def delete_qdrant_vector(client: QdrantClient, collection_name: str, vector_id: int | str) -> bool:
    """
    Supprime un point (vecteur + payload) d'une collection Qdrant à partir de son ID.
    
    Args:
        client: L'instance active du QdrantClient.
        collection_name: Le nom de la collection contenant la donnée.
        vector_id: L'identifiant unique de la donnée (entier non signé ou UUID).
        
    Returns:
        bool: True si l'opération est confirmée sur le cluster, False en cas d'échec.
    """
    try:
        operation_info = client.delete(
            collection_name=collection_name,
            points_selector=[vector_id],
            wait=True 
        )
        
        # Vérification du statut de l'opération
        if operation_info.status == UpdateStatus.COMPLETED:
            print(f"[SUCCÈS] Vecteur {vector_id} neutralisé avec succès.")
            return True
        else:
            print(f"[AVERTISSEMENT] Statut de suppression inattendu : {operation_info.status}")
            return False
            
    except Exception as e:
        print(f"[ERREUR SYSTÈME] Échec de la suppression du vecteur {vector_id} : {e}")
        return False


if __name__ == "__main__":
    qdrant_client = QdrantClient(host="localhost", port=6333)
    CIBLE = "florient marchal" 

    COLLECTION_NAME = "face"
    TARGET_ID = "dbdad662-5575-4dcf-87c7-a156a8d96a5b"
    delete_qdrant_vector(qdrant_client,COLLECTION_NAME , TARGET_ID)
    

