import os
import sys

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from governance.lineage_tracker import get_lineage
import rag as rag_module

app = FastAPI(title="Lakehouse RAG API")


class QueryRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query")
def query(req: QueryRequest):
    try:
        return rag_module.query(req.question)
    except Exception:
        return JSONResponse(status_code=503, content={"error": "Service temporarily unavailable"})


@app.get("/lineage/{paper_id}")
def lineage(paper_id: str):
    events = get_lineage(
        paper_id,
        minio_endpoint=os.environ.get("MINIO_ENDPOINT", "http://localhost:9000"),
        access_key=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.environ.get("MINIO_SECRET_KEY", "minioadmin"),
    )
    return {"paper_id": paper_id, "events": events}
