import os
import warnings
from datasets import Dataset
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI
from qdrant_client import QdrantClient
from ragas import evaluate
from ragas.metrics import Faithfulness, LLMContextPrecisionWithReference,LLMContextRecall
from ragas.llms import llm_factory
from constants import SYSTEM_PROMPT
from embedding import get_embedding_model,get_qdrant_client   
from helpers import require_env

load_dotenv()

test_cases = [
    {
        "question": "The payment service response time has increased significantly, but the service is still running. What could be causing the latency, and what evidence supports your diagnosis?",
        "ground_truth": "The available historical GitHub records do not establish the cause of increased payment-service latency. Issue #1749 reports missing payment-service traces, while PR #3276 fixes span lifecycle and exception attribution. Neither proves a latency cause. Request-duration metrics, distributed traces, and application logs are needed for further diagnosis.",
    },
    {
        "question": "Why does the checkout API return HTTP 500 when the paymentFailure feature flag is set to 100%?",
        "ground_truth": "Issue #3737 reports that when paymentFailure is configured to 100%, a valid checkout request returns HTTP 500 instead of a structured application error. Errors from the upstream payment service propagate through the checkout endpoint without being translated into an application-level response.",
    },
    {
        "question": "What problem does PR #3276 fix in the payment service?",
        "ground_truth": "PR #3276 fixes span lifecycle and exception attribution in the charge() method. It ensures span.end() is called on validation-error paths, records the exception and error status where the failure originates, and removes duplicate exception attribution from the gRPC span.",
    },                           
]


def main():
    embedding_model = get_embedding_model()
    qdrant_client   = get_qdrant_client() 

    llm = OpenAI(base_url=require_env("MODEL_URL"), api_key=require_env("API_KEY"))
    
    eval_client = AsyncOpenAI(base_url=require_env("MODEL_URL"), api_key=require_env("API_KEY"))
    evaluator_llm = llm_factory(require_env("MODEL"), provider="openai", client=eval_client)
    data = {"user_input": [], "reference": [], "response": [], "retrieved_contexts": []}

    for case in test_cases:
        q = case["question"]
        gt = case["ground_truth"]

        results = qdrant_client.query_points(
            collection_name=require_env("COLLECTION_NAME"),
            query=embedding_model.encode(q).tolist(),
            limit=5,
            with_payload=True,
        ).points

        contexts = [str(point.payload or {}) for point in results]

        response = llm.chat.completions.create(
            model=require_env("MODEL"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"User query: {q}\nContext: {' '.join(contexts)}"},
            ],
        ).choices[0].message.content
        
        data["user_input"].append(q)
        data["reference"].append(case["ground_truth"])
        data["response"].append(response)
        data["retrieved_contexts"].append(contexts)
        
    result = evaluate(
        dataset=Dataset.from_dict(data),
        metrics=[Faithfulness(), LLMContextPrecisionWithReference(), LLMContextRecall()],
        llm=evaluator_llm
    )

    print(result)


if __name__ == "__main__":
    main()
