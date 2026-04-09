# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Evaluate AI is an automated system for evaluating handwritten student answer sheets. It accepts scanned images, extracts text via OCR, processes it through NLP and RAG pipelines, evaluates answers using an LLM, and presents results through a web dashboard.

## Development Commands

All commands are run from the `backend/` directory with the virtual environment activated.

```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download required NLP models (one-time setup)
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('wordnet')"

# Run the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run all tests
pytest

# Run a single test file
pytest tests/test_auth.py -v

# Run a single test function
pytest tests/test_auth.py::test_login -v

# Apply database migrations
alembic upgrade head

# Generate a new migration
alembic revision --autogenerate -m "description"

# Serve the frontend (from project root)
python -m http.server 3000 --directory frontend
```

## Environment Setup

Copy `backend/.env.example` to `backend/.env` and configure:

- `DATABASE_URL` / `DATABASE_SYNC_URL`: PostgreSQL 17 connection strings
- `SECRET_KEY`: JWT signing key
- `OLLAMA_BASE_URL` / `OLLAMA_MODEL`: LLM inference server (default: `llama3.1:8b`)
- `EMBEDDING_MODEL`: Sentence-BERT model (default: `all-MiniLM-L6-v2`, 384-dim)

Docker Compose starts PostgreSQL with pgvector and Ollama (mapped to port 5433 to avoid conflicts with local Postgres):
```bash
docker-compose up -d
```

## Architecture

### Processing Pipeline

The full pipeline is: **Upload → OCR → NLP → RAG → LLM Evaluation → Results**

Each stage is triggered explicitly via separate API calls:
1. `POST /api/v1/upload/` — stores the file, creates a `Document` record with `status=uploaded`
2. `POST /api/v1/process/` — runs OCR + NLP, saves `extracted_text` and `processed_data` as JSONB on the `Document`, sets `status=processed`
3. `POST /api/v1/evaluate/` — runs RAG retrieval + LLM scoring, creates `Evaluation` and `QuestionResult` records

### Module Responsibilities

**`app/modules/ocr/`** — OCR using Qwen Vision model served via LM Studio at `http://192.168.28.1:1234`. The extractor sends base64-encoded images to the LM Studio OpenAI-compatible API (not Hugging Face directly). It detects diagrams inline using `<diagram>` XML tags.

**`app/modules/nlp/`** — Orchestrated by `NLPService`. Takes OCR JSON output, cleans text (`TextCleaner`), splits into chunks (`TextChunker`), classifies chunk types (`ChunkClassifier`), and generates Sentence-BERT embeddings (`EmbeddingGenerator`). Output is a dict keyed by question ID (`Q1`, `Q2`, …).

**`app/modules/rag/`** — Indexes teacher-uploaded reference documents (model answers) into pgvector (`knowledge_chunks` table). At evaluation time, `QueryService` performs vector similarity search per student answer chunk, retrieving top-K reference passages.

**`app/modules/evaluation/`** — `AnswerScorer` uses LangChain + Ollama to grade each answer against retrieved RAG context. `SemanticComparator` provides cosine similarity as a fallback. `FeedbackGenerator` generates per-question textual feedback.

**`app/services/pipeline_service.py`** — The main orchestrator that chains RAG query → LLM scoring → result aggregation for a complete document evaluation.

### Data Flow Between Stages

OCR output (`extracted_text` JSONB): list of `{question_id, answer, diagram_present, diagram_description}` records.

NLP output (`processed_data` JSONB): dict of `{Q1: {original_answer, chunks: [{chunk_id, chunk, embedding, metadata}]}}`.

The `embedding` field inside `processed_data` chunks is a `List[float]` stored in JSONB (not the pgvector column — those are only in `knowledge_chunks`).

### Authentication & Authorization

JWT-based auth. Two roles: `teacher` and `student`. The `require_teacher` dependency in `app/api/dependencies.py` gates all write/evaluation operations. Students can only read their own results via `student_email` matching on `Document`.

### Database Schema

Key tables: `users`, `documents`, `knowledge_documents`, `knowledge_chunks` (with pgvector `embedding` column, dim=384), `evaluations`, `question_results`. All primary keys are UUIDs. Alembic manages migrations from `backend/alembic/`.

### API Docs

Interactive docs at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.
