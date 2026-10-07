from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_query_returns_answer():
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [["chunk text about transformers"]],
        "metadatas": [[{"paper_id": "2301.00001", "title": "Attention Is All You Need", "category": "cs.AI", "chunk_index": 0}]],
    }

    mock_anthropic = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Transformers use self-attention mechanisms.")]
    mock_anthropic.messages.create.return_value = mock_message

    with patch("rag.get_chroma_collection", return_value=mock_collection), \
         patch("rag.get_anthropic_client", return_value=mock_anthropic), \
         patch("rag.get_embedding_model") as mock_model_fn:
        import numpy as np
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1] * 384])
        mock_model_fn.return_value = mock_model

        response = client.post("/query", json={"question": "What are transformers?"})

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert len(data["sources"]) >= 1
    assert data["sources"][0]["paper_id"] == "2301.00001"


def test_query_handles_chromadb_error():
    with patch("rag.get_chroma_collection", side_effect=Exception("connection refused")):
        response = client.post("/query", json={"question": "What are transformers?"})
    assert response.status_code == 503
    assert "error" in response.json()


def test_query_missing_question():
    response = client.post("/query", json={})
    assert response.status_code == 422
