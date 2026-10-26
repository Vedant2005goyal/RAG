import uvicorn
from openai import OpenAI
from helpers import require_env
from embedding import get_embedding_model, get_qdrant_client
from fastapi import FastAPI 
from pydantic import BaseModel
from schema import UserQuery,RetrievedChunk
from llm import agent_loop
    
app=FastAPI(title='RAG')

llm_client=OpenAI(
    base_url=require_env("MODEL_URL"),
    api_key=require_env("API_KEY"),
)
embedding_model=get_embedding_model()
qdrant_client=get_qdrant_client()

@app.get("/health")# that is a very rudimentary code for the health maybe in future would improve it
def health():
    return {"status":"healthy"}


@app.post("/analyze")
def query_rag(request: UserQuery):
    return agent_loop(request.query, embedding_model, qdrant_client, llm_client)

@app.post("/search")
def fetch_data(request: UserQuery):
    query_vector=embedding_model.encode(request.query).tolist()
    results = qdrant_client.query_points(
        collection_name=require_env("COLLECTION_NAME"),
        query=query_vector,
        limit=5,
        with_payload=True,
    ).points
    chunks = []
    for result in results:
        payload = result.payload or {}
        chunks.append(
            RetrievedChunk(
                score=result.score,
                content=payload.get("content", ""),
                source=payload.get("url") or payload.get("source_uri"),
                title=payload.get("title"),
                source_type=payload.get("source_type"),
                number=payload.get("number"),
            )
        )
    return chunks
    


if __name__ == "__main__":
    uvicorn.run(app,host='0.0.0.0',port=8000)
