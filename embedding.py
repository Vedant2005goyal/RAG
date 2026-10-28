from openai import OpenAI
from qdrant_client import QdrantClient, models
from qdrant_client.models import PointStruct
from github import load_github_data
from helpers import require_env


def get_embedding_model():
    """Returns the OpenAI-compatible client for local Ollama embeddings."""
    return OpenAI(
        base_url=require_env("EMBEDDING_URL"),
        api_key="ollama"
    )


def get_embedding(text: str, embedding_client: OpenAI):
    response = embedding_client.embeddings.create(
        model=require_env("EMBEDDING_MODEL"),
        input=f"search_document: {text}"
    )
    return response.data[0].embedding


def create_and_setup_qdrant_client(embedding_client: OpenAI, path: str = "./qdrant_db") -> QdrantClient:
    """Sets up Qdrant with GitHub issue and PR embeddings."""
    client = QdrantClient(path=path)
    embedding_text = []
    issues, prs = load_github_data()

    for issue in issues:
        embedding_text.append({
            "text": f"Title: {issue.title}. Description: {issue.body or ''}",
            "metadata": {
                "source_type": "issue",
                "number": issue.number,
                "url": issue.html_url,
                "author": issue.user or None,
                "created_at": issue.created_at or None           
            }
        })

    for pr in prs:
        embedding_text.append({
            "text": f"Title: {pr.title}. Description: {pr.body or ''}",
            "metadata": {
                "source_type": "pull_request",
                "number": pr.number,
                "url": pr.html_url,
                "author": pr.user or None,
                "created_at": pr.created_at or None,
                "merged_at": pr.merged_at or None    
            }
        })

    embeddings = []

    for item in embedding_text:
        embedding = get_embedding(item["text"], embedding_client)
        embeddings.append(embedding)

    collection_name = "payment_service"

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=768,
                distance=models.Distance.COSINE
            )
        )

    points = []

    for i, item in enumerate(embedding_text):
        point = PointStruct(
            id=i,
            vector=embeddings[i],
            payload={
                "content": item["text"],
                **item["metadata"]
            }
        )
        points.append(point)

    if points:
        client.upsert(
            collection_name=collection_name,
            points=points
        )

    return client


def get_qdrant_client(path: str = "./qdrant_db") -> QdrantClient:
    """Returns a client for the existing local Qdrant database."""
    return QdrantClient(path=path)


if __name__ == "__main__":
    embedding_client = get_embedding_model()
    client_created=False 
    if client_created==False:
        client = create_and_setup_qdrant_client(embedding_client)
        client_created=True 
    else: 
        print("Client already created!")
        
    client.close()
    embedding_client.close()
