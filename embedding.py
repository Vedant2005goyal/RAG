from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
from qdrant_client.models import PointStruct
from github import load_github_data

issues, prs = load_github_data()

def get_embedding_model(
        model_name : str = "BAAI/bge-small-en-v1.5"
    ) -> SentenceTransformer:
    """ Returns the embedding model to be used by the RAG. """
    
    return SentenceTransformer(model_name)

def create_and_setup_qdrant_client(
        embedding_model : SentenceTransformer,
        path            : str = "./qdrant_db"
    ) -> QdrantClient:
    """ Sets up Qdrant Client with inital embeddings. """

    client = QdrantClient(path=path)
    embedding_text = []

    for issue in issues:
        embedding_text.append({
            "text":f"Title: {issue.title}. Description: {issue.body}",
            "metadata":{
                "source_type":"issue",
                "number":issue.number,
                "url":issue.html_url,
                "author":issue.user,
                "created_at":issue.created_at
            }
        })

    for pr in prs:
        embedding_text.append({
            "text":f"Title: {pr.title}. Description: {pr.body}",
            "metadata":{
                "source_type":"pull_request",
                "number":pr.number,
                "url":pr.html_url,
                "author":pr.user,
                "created_at":pr.created_at,
                "merged_at":pr.merged_at
            }
        })

    embeddings = []

    for i in range(len(embedding_text)):
        text = embedding_text[i]["text"]
        embedding = embedding_model.encode(text)
        embeddings.append(embedding)

    if not client.collection_exists("payment_service"):
        client.create_collection(
            collection_name="payment_service",
            vectors_config=models.VectorParams(size=384,distance=models.Distance.COSINE)
        )

    points=[]

    for i,item in enumerate(embedding_text):
        point=PointStruct(
            id=i,
            vector=embeddings[i].tolist(),
            payload={
                "content":item["text"],
                **item["metadata"]
            }
        )

        points.append(point)

    client.upsert(
        collection_name="payment_service",
        points=points
    )

    return client

if __name__ == "__main__":
    embedding_model = get_embedding_model()
    client = create_and_setup_qdrant_client(embedding_model)
    client.close()
