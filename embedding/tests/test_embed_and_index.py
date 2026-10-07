from unittest.mock import patch, MagicMock
import pytest
from embed_and_index import embed_chunks


SAMPLE_ROWS = [
    {
        "paper_id": "2301.00001",
        "title": "Test Paper",
        "category": "cs.AI",
        "chunk_index": 0,
        "embed_text": "Test Paper This is a test abstract about machine learning.",
    }
]


def test_embed_chunks_returns_count():
    mock_collection = MagicMock()
    mock_chroma_client = MagicMock()
    mock_chroma_client.get_or_create_collection.return_value = mock_collection

    with patch("embed_and_index.chromadb.HttpClient", return_value=mock_chroma_client), \
         patch("embed_and_index.SentenceTransformer") as mock_st:
        import numpy as np
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1] * 384])
        mock_st.return_value = mock_model

        count = embed_chunks(SAMPLE_ROWS, chroma_host="localhost", chroma_port=8000)

    assert count == 1
    assert mock_collection.upsert.called


def test_embed_chunks_empty_input():
    with patch("embed_and_index.chromadb.HttpClient"), \
         patch("embed_and_index.SentenceTransformer"):
        count = embed_chunks([], chroma_host="localhost", chroma_port=8000)
    assert count == 0
