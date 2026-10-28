import os
import uuid  # NEW
import hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from pathlib import Path
from embedding import get_embedding_model, get_qdrant_client  
from schema import LocalDocument
from qdrant_client.models import PointStruct, models  
from helpers import require_env 

source_map = set() 
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)

embedding_client = get_embedding_model()
client = get_qdrant_client()

def extract_text(path: Path) -> str:
    reader = PdfReader(path)
    extracted_pages = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            extracted_pages.append(page_text)

    return "\n".join(extracted_pages)


def chunk_text(text: str) -> list[str]:
    if not text.strip():
        return []

    return text_splitter.split_text(text)


def get_file_id(path: Path) -> str:
    return hashlib.sha256(path.as_uri().encode()).hexdigest()


def ingest_file(file_path: str | Path):
    path = Path(file_path).expanduser().resolve()

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    source_uri = path.as_uri()
    source_id = get_file_id(path)

    if source_id in source_map:
        print(f"{path.name} has already been indexed.")
        return 0

    text = extract_text(path)
    chunks = chunk_text(text)

    if not chunks:
        print(f"No extractable text found in {path.name}.")
        return 0

    documents = []

    for index, chunk in enumerate(chunks):
        doc = LocalDocument(
            source_uri=source_uri,
            title=path.name,
            content=chunk,
            chunk_index=index,
        )
        documents.append(doc)

    embeddings = []

    for doc in documents:
        response = embedding_client.embeddings.create(
            model=require_env("EMBEDDING_MODEL"),
            input=f"search_document: {doc.content}",
        )
        embeddings.append(response.data[0].embedding)

    if not client.collection_exists(require_env("COLLECTION_NAME")):
        client.create_collection(
            collection_name=require_env("COLLECTION_NAME"),
            vectors_config=models.VectorParams(
                size=768,
                distance=models.Distance.COSINE,
            ),
        )

    points = []

    for i, item in enumerate(documents):
        point_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{source_uri}#{item.chunk_index}",
            )
        )

        point = PointStruct(
            id=point_id,  
            vector=embeddings[i],  
            payload={
                **item.model_dump(),
                "source_type": "local_file",  
            },
        )
        points.append(point)

    client.upsert(
        collection_name=require_env("COLLECTION_NAME"),
        points=points,
    )

    source_map.add(source_id)  
    print("done")
    return len(points) 


if __name__ == "__main__":
    file_path = input("Enter the path of file: ").strip().strip("'\"")

    try:
        ingest_file(file_path)
    finally: 
        embedding_client.close()
        client.close()
