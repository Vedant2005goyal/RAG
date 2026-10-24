import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from pathlib import Path
from embedding import client,embedding_model
import hashlib
from schema import LocalDocument
from qdrant_client.models import PointStruct


source_map={} #used for storing file path hash so that we cant add the same file again and again

text_splitter=RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)

def extract_text(path:Path)->str:
    reader=PdfReader(path)
    extracted_pages=[]
    for page in  reader.pages:
        page_text=page.extract_text()
        if page_text:
            extracted_pages.append(page_text)
    return "\n".join(extracted_pages) # it converts all the nested lists to a single string ending wiht \n 

def chunk_text(text:str)->list[str]:
    if not text.strip(): # it handles the case where the string is either empty or filled with whitespaces only
        return []
    return text_splitter.split_text(text)

def get_file_id(path:Path)->str:
    return hashlib.sha256(path.as_uri().encode()).hexdigest()

def ingest_file(file_path:str|Path):
    path=Path(file_path).expanduser().resolve()
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    source_uri=path.as_uri()
    source_id=get_file_id(path)

    if source_id in source_map:
        print(f"{path.name} has already been indexed.")
        return 0

    text=extract_text(path)
    chunks=chunk_text(text)
    
    if not chunks:
        print(f"No extractable text found in {path.name}.")
        return 0
    
    documents=[]
    for index,chunk in enumerate(chunks):
        doc=LocalDocument(
            source_uri=source_uri,
            title=path.name,
            content=chunk,
            chunk_index=index,
        )
        documents.append(doc)

    embeddings=[]
    for doc in documents:
        embedding=embedding_model.encode(doc.content)
        embeddings.append(embedding)

    points=[]

    for i,item in enumerate(documents):
        point=PointStruct(
            id=i,
            vector=embeddings[i].tolist(),
            payload={
               **item.model_dump() 
            }
        )
        points.append(point)

    client.upsert(
        collection_name=os.getenv("COLLECTION_NAME"),
        points=points
    )
    print("done")

if __name__=="__main__":
    file_path=input("Enter the path of file").strip().strip("'\"")
    ingest_file(file_path)
