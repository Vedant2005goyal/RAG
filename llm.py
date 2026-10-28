import os
from dotenv import load_dotenv
from openai import OpenAI
from embedding import get_embedding_model, get_qdrant_client
from helpers import require_env
from constants import SYSTEM_PROMPT
from schema import AgentResponse

load_dotenv()

SCORE_THRESHOLD = 0.60


def agent_loop(user_query: str, embedding_client, qdrant_client, llm_client)->AgentResponse:
    """Runs the main conversation loop."""

    message = [{
        "role": "system",
        "content": SYSTEM_PROMPT
    }]

    response = embedding_client.embeddings.create(
        model=require_env("EMBEDDING_MODEL"),
        input=f"search_query: {user_query}"
    )

    user_query_embedding = response.data[0].embedding

    retrieved_context = qdrant_client.query_points(
        collection_name=require_env("COLLECTION_NAME"),
        query=user_query_embedding,
        limit=5,
        with_payload=True
    ).points

    retrieved_context = [
        result for result in retrieved_context
        if result.score is not None
        and result.score >= SCORE_THRESHOLD
    ]

    context = ""
    sources = []

    for result in retrieved_context:
        payload = result.payload or {}

        context += f"{payload.get('content', '')}\n"

        sources.append({
            "score": result.score,
            "source": payload.get("url") or payload.get("source_uri")
        })

    prompt = f"User query: {user_query}\n\nContext:\n{context}"

    message.append({
        "role": "user",
        "content": prompt
    })

    # Generate the final answer using your LLM
    response = llm_client.chat.completions.create(
        model=require_env("MODEL"),
        messages=message
    )

    llm_reply = response.choices[0].message.content

    if not llm_reply:
        raise RuntimeError("LLM response is empty.")

    return AgentResponse(
        incident=user_query,
        answer=llm_reply,
        sources=sources,
    )


if __name__ == "__main__":
    embedding_client = get_embedding_model()
    qdrant_client = get_qdrant_client()

    llm_client = OpenAI(
        base_url=require_env("MODEL_URL"),
        api_key=require_env("API_KEY")
    )

    try:
        user_query = input("Describe the incident: ")
        result = agent_loop(
            user_query,
            embedding_client,
            qdrant_client,
            llm_client
        )
        print(result)

    finally:
        embedding_client.close()
        qdrant_client.close()
        llm_client.close()
