# Enterprise RAG Pipeline with Semantic Caching

A production-grade, decoupled microservice architecture that solves real-world LLM scaling problems: expensive API calls, synchronous ingestion timeouts, and strict multi-tenant data isolation.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Streamlit  │────▶│  FastAPI Gateway  │────▶│  Redis Vector Stack │
│   Frontend  │     │    (main.py)      │     │  (Semantic Cache)   │
└─────────────┘     └──────────────────┘     └─────────────────────┘
                             │                          ▲
                             │                          │
                             ▼                          │
                    ┌─────────────────┐                 │
                    │  Celery Worker  │─────────────────┘
                    │   (tasks.py)    │  stores chunks
                    └─────────────────┘
                             │
                    ┌─────────────────┐
                    │  Ollama (local) │
                    │  nomic-embed-   │
                    │      text       │
                    └─────────────────┘
```

## Features

- **Semantic Cache (Fast Path)**: Identical or semantically similar queries are served from Redis in <50ms, bypassing the LLM entirely
- **Multi-Tenant Isolation**: The `department` field is a declared Redis tag field — isolation is enforced at the vector index level, not in application code
- **Async Ingestion**: Document uploads are handed off to a Celery worker immediately (202 Accepted), preventing HTTP timeouts on large files
- **Cache TTL**: All entries expire after 1 hour to ensure data freshness
- **Department Allowlist**: The API validates `X-Department` against a fixed set (`general`, `engineering`, `hr`) to prevent arbitrary tag injection

## Stack

| Component | Technology |
|---|---|
| Vector Store | Redis Stack (RediSearch) |
| Embeddings | Ollama (`nomic-embed-text`) |
| Cache Layer | RedisVL `SemanticCache` |
| API Gateway | FastAPI |
| Task Queue | Celery + Redis broker |
| Frontend | Streamlit |

## Setup

### 1. Start infrastructure

```bash
docker compose up -d
```

Pull the embedding model into Ollama:

```bash
docker exec ollama-engine ollama pull nomic-embed-text
```

### 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the services

**API server:**
```bash
uvicorn main:app --reload --port 8000
```

**Celery worker** (in a separate terminal):
```bash
celery -A tasks.celery_app worker --loglevel=info
```

**Streamlit frontend** (in a separate terminal):
```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

## Project Structure

```
.
├── cache.py          # Shared SemanticCache instance with department TagField schema
├── orchestrator.py   # Fast path / slow path query logic
├── main.py           # FastAPI gateway (query + document upload endpoints)
├── tasks.py          # Celery worker (document ingestion → Redis)
├── app.py            # Streamlit UI
├── benchmark.py      # Latency benchmark script
├── init_cache.py     # One-time cache initialisation helper
├── storage/          # Document files for ingestion
└── docker-compose.yml
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/query` | Submit a query; returns answer + telemetry |
| `POST` | `/v1/documents` | Trigger async document ingestion |
| `GET` | `/healthz` | Health check |

### Query example

```bash
curl -X POST http://localhost:8000/v1/query \
  -H "Content-Type: application/json" \
  -H "X-Department: engineering" \
  -d '{"prompt": "What is the corporate holiday policy?"}'
```

### Document upload example

```bash
curl -X POST "http://localhost:8000/v1/documents?file_name=security_policy.txt&department=general"
```

## Running the Benchmark

```bash
python benchmark.py
```

Runs 6 semantically grouped queries and prints a latency table showing cache hits vs misses.
