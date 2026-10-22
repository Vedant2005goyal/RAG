import os
from openai import OpenAI 
from dotenv import load_dotenv
from embedding import embedding_model,client

load_dotenv()

client1=OpenAI(
    base_url=os.getenv("MODEL_URL"),
    api_key=os.getenv("API_KEY")
)

message=[]
message.append(
    {
        "role":"system",
        "content":"You are an SRE investigating a production incident. Do very cautious of what claims You are making and keep the conten in under 100 words"
    }
)

while True:
    user_query=input("Describe the incident: ")
    if user_query.lower() in ["machuda", "exit", "chup", "quit", "bye"]:
        break

    user_query_embedding=embedding_model.encode(user_query).tolist()
    retrieved_context=client.query_points(
        collection_name="payment_service",
        query=user_query_embedding,
        limit=5,
        with_payload=True
    ).points
    
    context=""
    for result in retrieved_context:
        context+=f"{result.payload}\n"
    prompt=f"User query:{user_query} context: {context}"
    
    message.append(
        {
            "role":"user",
            "content":prompt
        }
    )
    response=client1.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=message
    )
    print(response.choices[0].message.content)
    
