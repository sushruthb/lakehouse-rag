# lakehouse-rag

> An enterprise-grade RAG platform built on Lakehouse architecture — the same stack used at scale in production, running fully locally via Docker.

---

## The Problem

Enterprises want AI on their data. Most RAG demos skip the hard part: **governed, reliable data pipelines**. This project shows how a properly architected Lakehouse — with Medallion layers, Delta Lake, dbt, and lineage tracking — becomes the backbone of a production-ready AI system.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                       │
│  arXiv API → Python Ingestion Script → MinIO (Bronze)   │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                 TRANSFORMATION LAYER                     │
│  Bronze (raw JSON) → dbt → Silver (cleaned Parquet)     │
│                         → Gold (enriched, chunked text) │
│                    Delta Lake tables throughout          │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                   EMBEDDING LAYER                        │
│  Gold table → sentence-transformers → ChromaDB           │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                    SERVING LAYER                         │
│  FastAPI (RAG endpoint) → Claude API (answer synthesis)  │
│  Streamlit UI (Q&A interface + lineage panel)            │
└─────────────────────────────────────────────────────────┘
```

| Layer | What it does |
|---|---|
| **Ingestion** | Fetches arXiv AI/ML papers via public API, writes raw JSON to MinIO, registers a Bronze Delta table with governance metadata |
| **Transformation** | dbt models clean (Silver) and chunk (Gold) the data — deduplication, LaTeX stripping, 200-word chunking |
| **Embedding** | Reads Gold Delta table, embeds with `all-MiniLM-L6-v2` locally, upserts into ChromaDB |
| **Serving** | FastAPI retrieves top-5 chunks, sends to Claude for answer synthesis; Streamlit exposes Q&A + lineage UI |

---

## Tech Stack

| Component | Technology |
|---|---|
| Object store | MinIO (S3-compatible) |
| Table format | Delta Lake via delta-rs (no JVM) |
| Transformation | dbt-core + dbt-duckdb |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (local, free) |
| Vector store | ChromaDB |
| LLM | Claude (`claude-sonnet-4-6`) via Anthropic API |
| API | FastAPI + Uvicorn |
| UI | Streamlit |
| Orchestration | Docker Compose |

---

## Run It Yourself

**Prerequisites:** Docker Desktop, an [Anthropic API key](https://console.anthropic.com)

```bash
# 1. Clone and configure
git clone https://github.com/sushruthb/lakehouse-rag
cd lakehouse-rag
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 2. Start infrastructure
make up

# 3. Run the full pipeline (fetch → transform → embed)
make seed

# 4. Open the UI
open http://localhost:8501
```

---

## Governance

Every transformation step writes a lineage event to a `governance.lineage` Delta table on MinIO:

- Which source table was read
- Which target table was written
- Which dbt model produced the transformation
- Timestamp of the run

In the Streamlit UI → **Data Lineage** tab, enter any `paper_id` to trace its journey from Bronze → Silver → Gold.

---

## About

Built by **Sushruth Bharath H.G** — Data Architect with 20+ years in enterprise data platforms (SAP Labs, Brocade, Yahoo). This project demonstrates how Lakehouse architecture — Medallion pipelines, Delta Lake, dbt, governance — becomes the foundation for enterprise AI.

[LinkedIn](https://linkedin.com/in/sushruthbharath) · [GitHub](https://github.com/sushruthb)
