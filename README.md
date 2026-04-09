<<<<<<< HEAD
# Evaluate AI — Automated Evaluation of Handwritten Student Answer Sheets

A production-grade system that accepts scanned handwritten answer sheets, extracts text using OCR, processes it through NLP and RAG pipelines, evaluates answers using LLMs, and presents results through a premium dashboard.

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────────┐
│   Frontend   │────▶│              Backend (FastAPI)               │
│  HTML/CSS/JS │     │                                              │
│              │     │  ┌─────┐  ┌─────┐  ┌─────┐  ┌──────────┐   │
│  • Login     │     │  │ OCR │─▶│ NLP │─▶│ RAG │─▶│ Evaluate │   │
│  • Teacher   │     │  │QWEN │  │spaCy│  │pgvec│  │  Ollama  │   │
│  • Student   │     │  └─────┘  └─────┘  └─────┘  └──────────┘   │
└─────────────┘     └───────────────┬──────────────────────────────┘
                                    │
                          ┌─────────▼─────────┐
                          │  PostgreSQL 17     │
                          │  + pgvector        │
                          └───────────────────┘
```

## 🧠 Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11+, FastAPI |
| OCR | QWEN V3 (Hugging Face Transformers) |
| NLP | NLTK, spaCy, Sentence-BERT |
| RAG | LangChain, pgvector |
| LLM | Ollama (local inference) |
| Database | PostgreSQL 17 + pgvector |
| Frontend | Vanilla HTML, CSS, JavaScript |

## 👥 User Roles

- **Teacher**: Upload answer sheets + model answers, trigger evaluation, view all student scores
- **Student**: View own marks and detailed explainable feedback

## 📁 Project Structure

```
evaluate-ai-capstone/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── core/                # Config, security, exceptions
│   │   ├── api/                 # API routes & dependencies
│   │   │   └── endpoints/       # upload, process, evaluate, results, auth, knowledge
│   │   ├── modules/             # Business logic modules
│   │   │   ├── ocr/             # Image preprocessing → QWEN extraction → segmentation
│   │   │   ├── nlp/             # Text cleaning → tokenization → POS/NER → embeddings
│   │   │   ├── rag/             # Document chunking → indexing → vector search
│   │   │   ├── evaluation/      # Semantic comparison → LLM scoring → feedback
│   │   │   └── ingestion/       # Document parsing → preprocessing
│   │   ├── models/              # SQLAlchemy ORM models & Pydantic schemas
│   │   ├── services/            # Pipeline orchestration, storage, results
│   │   └── utils/               # File, image, text helpers
│   ├── tests/                   # Pytest test suite
│   ├── alembic/                 # Database migrations
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html               # Login/Register page
│   ├── teacher.html             # Teacher dashboard
│   ├── student.html             # Student results view
│   ├── css/                     # Design system (variables, base, layout, components, pages)
│   └── js/                      # App logic (api, auth, upload, dashboard, results, utils)
├── docker-compose.yml
└── README.md
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL 17
- Ollama (for local LLM)
- Git

### 1. Clone & Setup Backend

```bash
git clone <repo-url>
cd evaluate-ai-capstone/backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Download NLP models
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('wordnet')"
```

### 2. Configure Database

```bash
# Create database
psql -U postgres -c "CREATE DATABASE evaluate_ai;"

# Install pgvector extension
psql -U postgres -d evaluate_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Copy and edit environment config
copy .env.example .env
# Edit .env with your PostgreSQL password
```

### 3. Setup Ollama

```bash
# Install Ollama from https://ollama.com
# Pull a model
ollama pull llama3.1:8b
```

### 4. Start Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: `http://localhost:8000/docs`

### 5. Start Frontend

```bash
# Serve frontend (from project root)
python -m http.server 3000 --directory frontend
```

Open `http://localhost:3000` in your browser.

## 🔌 API Endpoints

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | Public | Register user |
| POST | `/api/v1/auth/login` | Public | Login |
| POST | `/api/v1/upload/` | Teacher | Upload answer sheet |
| POST | `/api/v1/process/` | Teacher | Trigger OCR + NLP |
| POST | `/api/v1/evaluate/` | Teacher | Trigger evaluation |
| GET | `/api/v1/results/` | Teacher | List all results |
| GET | `/api/v1/results/my-results` | Student | Get own results |
| GET | `/api/v1/results/{id}` | Both | Get evaluation detail |
| GET | `/api/v1/results/dashboard` | Teacher | Dashboard stats |
| POST | `/api/v1/knowledge/ingest` | Teacher | Ingest reference docs |

## 🔁 Processing Pipeline

```
Upload → OCR (QWEN V3) → NLP (spaCy/BERT) → RAG (pgvector) → LLM (Ollama) → Results
```

## 📝 License

MIT License
=======
# ai-conclave
>>>>>>> 74b75cb52712aa2d5306a9a0f484011352a21a75
