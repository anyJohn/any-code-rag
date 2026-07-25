from pathlib import Path

import chromadb
from fastapi import FastAPI
from pydantic import BaseModel

from rag_pipeline import chunk_text

app = FastAPI()


class QuerySchema(BaseModel):
    query: str
    n_results: int = 2


client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="obsidian_notes")


@app.get("/")
def root():
    return {"message": "Hello from RAG Microservice"}


@app.get("/query")
def query(q: str, n: int = 2, source: str | None = None):
    if source:
        results = collection.query(
            query_texts=[q], n_results=n, where={"source": source}
        )
    else:
        results = collection.query(query_texts=[q], n_results=n)
    return {
        "query": q,
        "results": results["documents"][0],
        "distances": results["distances"][0],
    }


@app.post("/ingest")
def ingest(file_path: str):
    content = Path(file_path).read_text(encoding="utf-8")
    chunks = chunk_text(content, 100)
    collection.add(
        documents=chunks,
        ids=[f"{file_path}_{i}" for i in range(len(chunks))],
        metadatas=[{"source": file_path, "chunk_index": i} for i in range(len(chunks))],
    )
    return len(chunks)
