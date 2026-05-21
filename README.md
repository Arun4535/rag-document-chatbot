# DocSense + ResearchAgent

[![Live Demo](https://img.shields.io/badge/live-demo-2D7DD2)](https://docsense-frontend.onrender.com)
[![GitHub](https://img.shields.io/badge/github-repo-white)](https://github.com/Arun4535/rag-document-chatbot)

Production-style AI document Q&A and research assistant built with FastAPI, Claude, Voyage embeddings, ChromaDB, PostgreSQL, vanilla HTML/CSS/JS, and Docker.

## Screenshot

Add a screenshot after deploying:

```text
docs/screenshot.png
```

## Features

- Upload PDF or TXT documents
- Background ingestion with status polling
- Recursive text chunking with source metadata
- `voyage-3` embeddings through Voyage AI
- Persistent ChromaDB vector storage
- Hybrid retrieval: semantic search + BM25 keyword search
- Reciprocal Rank Fusion for merged retrieval ranking
- Claude answer generation with source citations
- Research agent with Claude tool use, web search, page fetch, and report sections
- Eval dashboard with query logs, source counts, and thumbs up/down feedback
- Docker Compose for local deployment
- Render Blueprint for cloud deployment

## Architecture

```text
Browser
  |
  v
Nginx Frontend
  |
  v
FastAPI Backend
  |
  +-------------------+-------------------+
  |                   |                   |
  v                   v                   v
ChromaDB          PostgreSQL          Claude API
  ^
  |
Voyage-3 Embeddings
```

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | HTML, CSS, vanilla JavaScript |
| API | FastAPI, Uvicorn |
| LLM | Claude via Anthropic API |
| Embeddings | Voyage AI `voyage-3` |
| Vector store | ChromaDB persistent storage |
| Keyword search | BM25 via `rank-bm25` |
| Database | PostgreSQL + SQLAlchemy |
| Deployment | Docker Compose, Render Blueprint |

## Local Setup

```bash
git clone https://github.com/Arun4535/rag-document-chatbot.git
cd rag-document-chatbot
cp .env.example .env
```

Edit `.env`:

```text
ANTHROPIC_API_KEY=your_anthropic_key
VOYAGE_API_KEY=your_voyage_key
POSTGRES_PASSWORD=choose_a_password
```

Run:

```bash
docker compose up --build
```

Open:

```text
http://localhost
```

## API Endpoints

### Health

```http
GET /api/health
```

### Ingest Document

```http
POST /api/ingest
Content-Type: multipart/form-data
```

Accepts PDF or TXT file upload. Returns immediately:

```json
{
  "doc_id": "uuid",
  "status": "processing"
}
```

### Ingest Status

```http
GET /api/ingest/status/{doc_id}
```

```json
{
  "doc_id": "uuid",
  "status": "processing|complete|failed",
  "chunk_count": 12
}
```

### Query Document

```http
POST /api/query
```

```json
{
  "question": "What is the refund policy?",
  "doc_id": "uuid",
  "session_id": "browser-session-id"
}
```

Returns:

```json
{
  "answer": "Answer with citations.",
  "sources": [
    {
      "text": "retrieved chunk",
      "score": 0.031,
      "page": 2,
      "filename": "policy.pdf"
    }
  ],
  "session_id": "browser-session-id",
  "eval_id": "uuid"
}
```

### Research Agent

```http
GET /api/agent/research/stream?topic=...
```

Streams Server-Sent Events for tool calls and the final report.

### Evals Dashboard

```http
GET /api/evals
POST /api/evals/{eval_id}/feedback
```

## Deployment

See [DEPLOY.md](DEPLOY.md).

## Interview Talking Points

### Why hybrid search over pure semantic search?

Semantic search is strong for meaning, but it can miss exact names, IDs, dates, or policy terms. BM25 keyword search catches exact lexical matches. Combining both improves retrieval reliability.

### Why Reciprocal Rank Fusion?

RRF merges multiple ranked lists without needing scores to be on the same scale. A chunk that ranks well in both semantic and keyword retrieval gets boosted, which is useful because cosine similarity and BM25 scores are not directly comparable.

### Why BackgroundTasks for ingestion?

PDF extraction, chunking, embedding, and indexing can take several seconds. Background ingestion lets the API return a `doc_id` immediately while the frontend polls status. That keeps the app responsive.

### How does the agentic loop work?

Claude receives tool definitions for web search, page retrieval, and saving report sections. During each loop, Claude decides which tool to call, the backend executes it, returns the result, and Claude continues until the report is complete or the iteration limit is reached.

## Notes

Voyage embeddings require a `VOYAGE_API_KEY`. Claude generation and agent tool use require an `ANTHROPIC_API_KEY`.
