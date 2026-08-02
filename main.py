from fastapi import FastAPI
from pydantic import BaseModel

from rag_pipeline import get_collections, ingest, init_collection, query

app = FastAPI()


class QuerySchema(BaseModel):
    query: str
    n_results: int = 2


collection = init_collection(path="./chroma_db", name="obsidian_notes")


@app.get("/")
def root():
    return {"message": "Hello from RAG Microservice"}


@app.get("/health")
def get_health():
    return {"status": "ok"}


@app.get("/query")
def query_api(q: str, n: int = 2, source: str | None = None):
    return query(collection, q, n, source)


@app.post("/ingest")
def ingest_api(file_path: str):
    return ingest(collection, file_path)


@app.get("/collections")
def collections_api():
    return {"collections": get_collections()}