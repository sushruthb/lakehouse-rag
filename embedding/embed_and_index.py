import os

import chromadb
from deltalake import DeltaTable
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "arxiv_chunks"
BATCH_SIZE = 128


def _storage_options(endpoint: str, access_key: str, secret_key: str) -> dict:
    return {
        "AWS_ENDPOINT_URL": endpoint,
        "AWS_ACCESS_KEY_ID": access_key,
        "AWS_SECRET_ACCESS_KEY": secret_key,
        "AWS_ALLOW_HTTP": "true",
        "AWS_REGION": "us-east-1",
    }


def embed_chunks(rows: list[dict], chroma_host: str, chroma_port: int) -> int:
    if not rows:
        return 0

    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
    collection = client.get_or_create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    texts = [r["embed_text"] for r in rows]
    ids = [f"{r['paper_id']}_{r['chunk_index']}" for r in rows]
    metadatas = [
        {
            "paper_id": r["paper_id"],
            "title": r["title"],
            "category": r["category"],
            "chunk_index": int(r["chunk_index"]),
        }
        for r in rows
    ]

    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i : i + BATCH_SIZE]
        batch_ids = ids[i : i + BATCH_SIZE]
        batch_meta = metadatas[i : i + BATCH_SIZE]
        embeddings = model.encode(batch_texts, show_progress_bar=False).tolist()
        collection.upsert(
            ids=batch_ids,
            embeddings=embeddings,
            documents=batch_texts,
            metadatas=batch_meta,
        )

    return len(rows)


if __name__ == "__main__":
    minio_endpoint = os.environ["MINIO_ENDPOINT"]
    access_key = os.environ["MINIO_ACCESS_KEY"]
    secret_key = os.environ["MINIO_SECRET_KEY"]
    chroma_host = os.environ.get("CHROMADB_HOST", "localhost")
    chroma_port = int(os.environ.get("CHROMADB_PORT", "8000"))

    storage_options = _storage_options(minio_endpoint, access_key, secret_key)
    dt = DeltaTable("s3://gold/delta/arxiv_chunks", storage_options=storage_options)
    df = dt.to_pandas()
    rows = df.to_dict(orient="records")

    count = embed_chunks(rows, chroma_host=chroma_host, chroma_port=chroma_port)
    print(f"Upserted {count} vectors into ChromaDB")
