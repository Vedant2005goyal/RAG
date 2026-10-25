import os
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from embedding import get_embedding_model, get_qdrant_client
from helpers import require_env
from constants import SYSTEM_PROMPT, EXIT_COMMANDS
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

SCORE_THRESHOLD=0.60

load_dotenv()

def agent_loop(embedding_model: SentenceTransformer, qdrant_client: QdrantClient, llm_client: OpenAI):
    """ Runs the main conversation loop """
    message: list[ChatCompletionMessageParam] = [
        {
            "role":"system",
            "content": SYSTEM_PROMPT
        }
    ]

    while True:
        user_query = input("Describe the incident: ")
        
        if user_query.lower() in EXIT_COMMANDS:
            break

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

        for result in retrieved_context:
            context+=f"{result.payload}\n"
            print(f"\nScore: {result.score}")
            print(f"Source: {result.payload.get('url') or result.payload.get('source_uri')}")
            print(f"Content: {result.payload.get('content', '')[:300]}")

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

        print(f"Assistant reply: {llm_reply}")

        message.append({
            "role": "assistant",
            "content": llm_reply
        })

    
if __name__ == "__main__":
    embedding_model = get_embedding_model()
    qdrant_client   = get_qdrant_client() 

    llm_client = OpenAI(
        base_url = require_env("MODEL_URL"),
        api_key  = require_env("API_KEY")
    )

    agent_loop(embedding_model, qdrant_client, llm_client)
