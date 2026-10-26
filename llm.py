import os
from dotenv import load_dotenv
from openai import OpenAI
from embedding import get_embedding_model, get_qdrant_client
from helpers import require_env
from constants import SYSTEM_PROMPT
from schema import AgentResponse

SCORE_THRESHOLD=0.60

load_dotenv()

def agent_loop(user_query:str, embedding_model, qdrant_client, llm_client)->AgentResponse:
    """ Runs the main conversation loop """
    message=[{
        "role":"system",
        "content": SYSTEM_PROMPT
    }]

    user_query_embedding = embedding_model.encode(user_query).tolist()
        
    retrieved_context = qdrant_client.query_points(
        collection_name=os.getenv("COLLECTION_NAME"),
        query=user_query_embedding,
        limit=5,
        with_payload=True
    ).points
       
    retrieved_context = [result for result in retrieved_context 
        if result.score is not None and result.score >= SCORE_THRESHOLD
    ]
        
    context=""
    sources=[]
    for result in retrieved_context:
        context+=f"{result.payload}\n"
        sources.append({
            "score": result.score,
            "source": (
                result.payload.get("url")
                or result.payload.get("source_uri")
            ),
        })

    prompt=f"User query:{user_query} context: {context}"
        
    message.append(
        {
            "role":"user",
            "content":prompt
        }
    )
    response=llm_client.chat.completions.create(
        model=require_env("MODEL"),
        messages=message
    )

    llm_reply = response.choices[0].message.content

    if not llm_reply:
        raise RuntimeError("LLM Response is empty.")

    message.append({
        "role": "assistant",
        "content": llm_reply
    })
    return AgentResponse(
        incident=user_query,
        answer=llm_reply,
        sources=sources,
    )
    
if __name__ == "__main__":
    embedding_model = get_embedding_model()
    qdrant_client   = get_qdrant_client() 

    llm_client = OpenAI(
        base_url = require_env("MODEL_URL"),
        api_key  = require_env("API_KEY")
    )
    # although i have added a FastAPI endpoint but just in case if I want 
    # to run only python3 llm.py for that case i have kept below code 
    user_query=input("Describe the incident: ")
    agent_loop(user_query, embedding_model, qdrant_client, llm_client)
