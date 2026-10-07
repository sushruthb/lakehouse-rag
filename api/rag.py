import os
from functools import lru_cache

import anthropic
import chromadb
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "arxiv_chunks"
TOP_K = 5


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


@lru_cache(maxsize=1)
def get_chroma_collection():
    host = os.environ.get("CHROMADB_HOST", "localhost")
    port = int(os.environ.get("CHROMADB_PORT", "8000"))
    client = chromadb.HttpClient(host=host, port=port)
    return client.get_or_create_collection(COLLECTION_NAME)


@lru_cache(maxsize=1)
def get_anthropic_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def query(question: str) -> dict:
    model = get_embedding_model()
    collection = get_chroma_collection()
    claude = get_anthropic_client()

    question_embedding = model.encode([question], show_progress_bar=False).tolist()
    results = collection.query(
        query_embeddings=question_embedding,
        n_results=TOP_K,
        include=["documents", "metadatas"],
    )

    chunks = results["documents"][0]
    metas = results["metadatas"][0]

    context = "\n\n".join(
        f"[{m['title']} ({m['paper_id']})]\n{chunk}"
        for chunk, m in zip(chunks, metas)
    )

    prompt = (
        f"You are a research assistant. Answer the question using only the context below.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer concisely, citing paper titles where relevant."
    )

    message = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    answer = message.content[0].text

    seen = set()
    sources = []
    for m in metas:
        pid = m["paper_id"]
        if pid not in seen:
            seen.add(pid)
            sources.append({
                "paper_id": pid,
                "title": m["title"],
                "arxiv_url": f"https://arxiv.org/abs/{pid}",
            })

    return {"answer": answer, "sources": sources}
