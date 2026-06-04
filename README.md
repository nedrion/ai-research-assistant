# AI Research Assistant

Local RAG (Retrieval-Augmented Generation) system for querying PDF documents via CLI and REST API.

## Architecture

```
┌─────────────────────────────────────────────┐
│          Presentation Layer                  │
│  CLI (src/ui/cli.py)   API (src/api/)        │
└─────────────────────┬───────────────────────┘
                      │ calls
┌─────────────────────┴───────────────────────┐
│           Business Layer                     │
│  src/qa/pipeline.py  (RAGPipeline)           │
│  src/config.py                               │
└─────────────────────┬───────────────────────┘
                      │ orchestrates
┌─────────────────────┴───────────────────────┐
│            Data Layer                        │
│  src/ingestion/    src/embeddings/           │
│  src/vector_store/ src/qa/llm_client.py      │
└─────────────────────────────────────────────┘
```

![Architecture diagram](screenshots/architecture.svg)

**Ingestion** — PDF → chunk → embed → store in ChromaDB

**Query** — question → embed → vector search → retrieve chunks → build prompt → LLM → answer

## Screenshots

| Command | Preview |
|---------|---------|
| `python -m src.main status` | ![status](screenshots/status.svg) |
| `python -m src.main models` | ![models](screenshots/models.svg) |
| `python -m src.main ingest doc.pdf` | ![ingest](screenshots/ingest.svg) |
| `python -m src.main ask "..."` | ![ask](screenshots/ask.svg) |
| `python -m src.main --help` | ![help](screenshots/help.svg) |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # or: copy .env.example .env
```

### Prerequisites

- **Ollama** running locally with a model pulled (`ollama pull llama3.2`)
- Python 3.10+

## CLI

```bash
python -m src.main serve       # Start the FastAPI server
python -m src.main ingest doc.pdf
python -m src.main ask "question"
python -m src.main chat
python -m src.main status
python -m src.main remove doc.pdf
python -m src.main clear
python -m src.main models
```

## API

Start the server:

```bash
python -m src.main serve
# Listening on http://127.0.0.1:8000
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/documents` | Ingest a PDF by URL or local path (JSON body) |
| `POST` | `/documents/upload` | Ingest a PDF by file upload (multipart) |
| `GET` | `/documents` | List ingested documents with chunk counts |
| `DELETE` | `/documents` | Clear all documents |
| `DELETE` | `/documents/{filename}` | Remove a specific document |
| `POST` | `/query` | Ask a question (session-based) |
| `GET` | `/status` | Vector store stats |
| `GET` | `/models` | Available Ollama models |
| `GET` | `/docs` | Interactive Swagger UI |

### Examples

```bash
# Upload a PDF
curl -X POST -F "file=@paper.pdf" http://127.0.0.1:8000/documents/upload

# Ingest from URL
curl -X POST -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/paper.pdf"}' \
  http://127.0.0.1:8000/documents

# Ask a question (returns session_id for follow-ups)
curl -X POST -H "Content-Type: application/json" \
  -d '{"question": "What is the main finding?"}' \
  http://127.0.0.1:8000/query

# Follow-up in the same conversation
curl -X POST -H "Content-Type: application/json" \
  -d '{"question": "Tell me more", "session_id": "<id from previous>"}' \
  http://127.0.0.1:8000/query

# Check store
curl http://127.0.0.1:8000/status

# List models
curl http://127.0.0.1:8000/models

# Remove a document
curl -X DELETE http://127.0.0.1:8000/documents/paper.pdf

# Clear everything
curl -X DELETE http://127.0.0.1:8000/documents
```

## Configuration

Edit `.env` to tune:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MODEL` | `llama3.2` | Ollama model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | sentence-transformers model |
| `CHUNK_SIZE` | `500` | Characters per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |
| `TOP_K` | `5` | Retrieved chunks per query |
| `COLLECTION_NAME` | `documents` | ChromaDB collection name |
| `API_HOST` | `127.0.0.1` | API server bind address |
| `API_PORT` | `8000` | API server port |

Model switching is done at runtime — change `LLM_MODEL` in `.env` and restart. The system validates the model exists in Ollama before proceeding.

## Project Structure

```
src/
├── api/            # Presentation Layer — FastAPI routes, schemas, DI
│   ├── app.py
│   ├── schemas.py
│   ├── dependencies.py
│   └── routes/
│       ├── documents.py
│       ├── query.py
│       └── status.py
├── ingestion/      # Data Layer — PDF loading & text chunking
├── embeddings/     # Data Layer — Vector embedding generation
├── vector_store/   # Data Layer — ChromaDB persistence & search
├── qa/             # Business Layer — LLM client & RAG pipeline
├── ui/             # Presentation Layer — Rich CLI interface
├── config.py       # Settings
└── main.py         # Entry point (CLI + serve)
data/
├── chroma/         # Vector store persistence (gitignored)
screenshots/
├── architecture.svg
├── status.svg
├── models.svg
├── ingest.svg
├── ask.svg
└── help.svg
```
