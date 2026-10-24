import pydantic
import os 
from dotenv import load_dotenv
from github import issues,prs 
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
from qdrant_client.models import PointStruct
import uuid

load_dotenv()

embedding_text=[]
client=QdrantClient(path="./qdrant_db")

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

embeddings=[]
embedding_model=SentenceTransformer(os.getenv("EMBEDDING_MODEL"))
for i in range(len(embedding_text)):
    text=embedding_text[i]["text"]
    embedding=embedding_model.encode(text)
    embeddings.append(embedding)
print(len(embeddings))

if not client.collection_exists(os.getenv("COLLECTION_NAME")):
    client.create_collection(
        collection_name=os.getenv("COLLECTION_NAME"),
        vectors_config=models.VectorParams(size=384,distance=models.Distance.COSINE)
    )

points=[]
for i,item in enumerate(embedding_text):
    metadata=item["metadata"]
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
    collection_name=os.getenv("COLLECTION_NAME"),
    points=points
)


