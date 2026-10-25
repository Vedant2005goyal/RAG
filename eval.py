import os
import warnings

# Suppress the Ragas deprecation warnings to keep the console output clean
warnings.filterwarnings("ignore", category=DeprecationWarning)

from datasets import Dataset
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI
from qdrant_client import QdrantClient
from ragas import evaluate
from ragas.llms import llm_factory
from ragas.run_config import RunConfig

# Back to your ORIGINAL working imports
from ragas.metrics import (
    Faithfulness,
    LLMContextPrecisionWithReference,
    LLMContextRecall,
)

from constants import SYSTEM_PROMPT
from embedding import get_embedding_model
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
    model_name = require_env("MODEL")
    collection_name = require_env("COLLECTION_NAME")
    base_url = require_env("MODEL_URL")
    api_key = require_env("API_KEY")

    embedding_model = get_embedding_model(
        os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    )
    qdrant = QdrantClient(path="./qdrant_db")

    llm = OpenAI(base_url=base_url, api_key=api_key)
    evaluator_client = AsyncOpenAI(base_url=base_url, api_key=api_key)
    
    # Using your original working factory setup
    evaluator_llm = llm_factory(
        model_name, provider="openai", client=evaluator_client
    )

    user_inputs, references, responses, retrieved_contexts = [], [], [], []

    for case in test_cases:
        q = case["question"]
        gt = case["ground_truth"]

        results = qdrant.query_points(
            collection_name=collection_name,
            query=embedding_model.encode(q).tolist(),
            limit=5,
            with_payload=True,
        ).points

        contexts = [str(point.payload or {}) for point in results]

        response = llm.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"User query: {q}\nContext: {' '.join(contexts)}"},
            ],
        ).choices[0].message.content

        print(f"\nQuestion: {q}\nAnswer: {response}")

        user_inputs.append(q)
        references.append(gt)
        responses.append(response)
        retrieved_contexts.append(contexts)

    dataset = Dataset.from_dict({
        "question": user_inputs,
        "answer": responses,
        "contexts": retrieved_contexts,
        "ground_truth": references,
    })

    
    scores = evaluate(
        dataset,
        # Your original working metric initializations
        metrics=[
            Faithfulness(llm=evaluator_llm),
            LLMContextPrecisionWithReference(llm=evaluator_llm),
            LLMContextRecall(llm=evaluator_llm),
        ],
        # THIS is the magic line that stops the 429 Rate Limit Errors
        run_config=RunConfig(max_workers=1, max_retries=10),
        raise_exceptions=False,
    )

    df = scores.to_pandas()
    print(df)
    df.to_csv("ragas_results.csv", index=False)


if __name__ == "__main__":
    main()
