"""
Integration smoke test — requires all Docker services running.
Run with: docker compose up -d && make seed && pytest tests/test_e2e_smoke.py -v
"""
import pytest
import requests

API_URL = "http://localhost:8080"


def test_api_health():
    resp = requests.get(f"{API_URL}/health", timeout=5)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_query_returns_non_empty_answer():
    resp = requests.post(
        f"{API_URL}/query",
        json={"question": "What is attention mechanism in neural networks?"},
        timeout=30,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert len(data["answer"]) > 10
    assert "sources" in data
    assert len(data["sources"]) >= 1


def test_query_sources_have_arxiv_urls():
    resp = requests.post(
        f"{API_URL}/query",
        json={"question": "Explain BERT pre-training"},
        timeout=30,
    )
    assert resp.status_code == 200
    sources = resp.json()["sources"]
    for s in sources:
        assert s["arxiv_url"].startswith("https://arxiv.org/abs/")
        assert "paper_id" in s
        assert "title" in s


def test_query_missing_field_returns_422():
    resp = requests.post(f"{API_URL}/query", json={}, timeout=5)
    assert resp.status_code == 422
