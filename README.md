# 🤖 Financial AI Agent

> Multi-agent system for Spanish accounting firms (gestorías)  
> Transforms administrative processors into strategic financial advisors

**🌐 [Español](README.es.md)**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)

---

## 🎯 Key Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **p95 Latency** (Classification) | ~2.5s | PGC account classification |
| **p95 Latency** (Embeddings) | ~0.8s | Semantic search |
| **p95 Latency** (Smart Parser CSV) | ~0.1s | Flexible column detection |
| **p95 Latency** (Smart Parser PDF OCR) | ~5-12s | Vision AI + LLM parsing |
| **Cost per classification** | $0.003 | Llama-3.1-8B via HuggingFace |
| **Cost per PDF** (scanned) | ~$0.05 | Vision OCR + LLM |
| **Classification accuracy** | 95%+ | With LLM structure interpretation |
| **Document formats** | 6 types | CSV, Excel, OFX, PDF, JPG, PNG |
| **Throughput** | ~50 req/min | Single instance |
| **Concurrency** | 20 workers | AsyncIO + FastAPI |

> 📊 See [METRICS.md](docs/METRICS.md) for detailed benchmarks

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────┐
│  Universal Document Ingestion (Smart Parser)    │
│  CSV | Excel | OFX | PDF ✅ | Images ✅          │
└───────────────────┬──────────────────────────────┘
                    │
       ┌────────────┴────────────┐
       │  SmartParserAgent       │
       │  (LangGraph - AI-Powered)│
       │                         │
       │  1. Detect Format       │
       │  2. Extract Raw/Vision  │ ← Vision API for PDFs/images
       │  3. LLM Interprets      │ ← AI understands columns
       │  4. Extract ALL Data    │
       │  5. Validate & Clean    │
       └────────────┬────────────┘
                    │
                    ▼
         ┌─────────────────┐
         │   PostgreSQL    │
         │   + pgvector    │
         └─────────────────┘

✅ Phase 3 Complete: Vision API + PDF OCR
                                             │
┌─────────────┐    ┌─────────────┐           ▼
│   Frontend  │◀──▶│   FastAPI   │◀───┬─────────────┐
│   React     │    │   Gateway   │    │  LangGraph  │
└─────────────┘    └─────────────┘    │   Agents    │
                          │           └─────────────┘
                          ▼                  │
                   ┌─────────────┐           ▼
                   │    Redis    │    ┌─────────────┐
                   │   (cache)   │    │    Meta         │
                   └─────────────┘    │  (HF API)   │
                                      └─────────────┘
```

> 🏛️ See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for deep dive

---

## ✨ What's New

### Phase 3: Universal Document Parser ✅
- **Smart Parser Agent**: AI-powered document understanding
- **PDF Support**: Native text + OCR for scanned documents
- **Image Support**: Process bank statement photos
- **Vision AI**: Qwen3-VL-8B for OCR
- **Flexible parsing**: No hardcoded column names
- **Multi-format**: CSV, Excel, OFX, PDF, JPG, PNG

### Phase 2: LLM Structure Interpretation ✅
- **Intelligent column detection**: LLM understands any column layout
- **Debe/Haber handling**: Automatic debit/credit combination
- **Fallback mechanism**: Keywords → LLM for maximum flexibility

### Phase 1: Core System ✅
- Multi-agent architecture with LangGraph
- PostgreSQL + pgvector for embeddings
- FastAPI backend + React frontend
- Real-time classification and conciliation

---

## ✨ What's New

### 🎉 Phase 3: Universal Document Parser (COMPLETE)
- ✅ **Smart Parser Agent**: AI interprets any document structure
- ✅ **PDF Support**: Native text extraction + OCR fallback
- ✅ **Image Support**: Process bank statement photos (JPG, PNG)
- ✅ **Vision AI**: Qwen3-VL-8B for intelligent OCR
- ✅ **No hardcoded columns**: LLM understands any bank format
- ✅ **Debe/Haber**: Automatic debit/credit combination

### 📖 Documentation
- [Smart Parser Guide](docs/SMART_PARSER.md) - Full technical details
- [Postmortem](docs/POSTMORTEM.md) - Problems solved
- [Metrics](docs/METRICS.md) - Benchmark results

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 16 (or use Docker)
- HuggingFace API token

### 1. Clone & Setup

```bash
git clone https://github.com/edumesones/financial-ai-agent.git
cd financial-ai-agent

# Copy environment variables
cp .env.template .env
# Edit .env and add your HF_TOKEN
```

### 2. Start Infrastructure

```bash
docker-compose up -d
```

This starts:
- PostgreSQL 16 + pgvector (port 5432)
- Redis 7 (port 6379)

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 4. Run Migrations

```bash
cd backend
alembic upgrade head
```

### 5. Generate Test Data (Optional)

```bash
python scripts/generate_synthetic.py
```

### 6. Start API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API available at: http://localhost:8000  
Documentation: http://localhost:8000/docs

### 7. Start Frontend (Optional)

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: http://localhost:5173

---

## 📧 Test Credentials

```
Email:    admin@gestoria.es
Password: admin123
```

---

## 🧠 Core Features

### 1. **Intelligent Classification** 
Automatic transaction categorization using Spanish PGC (Plan General Contable)
- LLM-powered with context awareness
- Historical learning
- Human-in-the-loop validation

### 2. **Bank Reconciliation**
Multi-agent system for bank-accounting reconciliation
- Exact matching + fuzzy matching (embeddings)
- Auto-approval thresholds
- Discrepancy detection

### 3. **Cash Flow Forecasting**
AI-powered treasury projections
- Time series analysis
- Seasonal patterns
- Risk alerts

### 4. **Document Parsing**
Universal parser for bank statements
- CSV, OFX, PDF formats
- Auto-detection
- Multi-bank support

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** 0.109 - Modern async API framework
- **PostgreSQL** 16 + **pgvector** - Vector similarity search
- **LangGraph** - Multi-agent orchestration
- **SQLAlchemy** 2.0 - Async ORM
- **Alembic** - Database migrations
- **Redis** - Caching & task queue
- **Celery** - Background workers

### AI/ML
- **Mixtral-8x7B** (via HuggingFace) - LLM for classification
- **BGE-M3** - Multilingual embeddings
- **HuggingFace Inference API** - OpenAI-compatible router

### Frontend
- **React** 18 + **Vite** - Modern SPA
- **TailwindCSS** - Utility-first styling
- **Recharts** - Data visualization

### DevOps
- **Docker** & **Docker Compose** - Containerization
- **GitHub Actions** - CI/CD
- **Prometheus** - Metrics
- **Structlog** - Structured logging

---

## 📊 System Design Decisions

### Why LangGraph over raw LangChain?
- **Checkpointing**: Pause agents for human-in-the-loop
- **State management**: Explicit state transitions
- **Debugging**: Clear execution graph visualization
- **Scaling**: Easy to add/remove agents

### Why PostgreSQL + pgvector over Pinecone?
- **Cost**: Self-hosted = $0 vector storage
- **Latency**: Local queries < 50ms vs 200ms+ for cloud
- **Privacy**: Financial data stays on-premise
- **Trade-off**: Manual scaling vs Pinecone's auto-scaling

### Why HuggingFace over OpenAI?
- **Cost**: 10x cheaper for similar quality
- **EU compliance**: HF can run in EU regions
- **Model flexibility**: Easy to swap models
- **Trade-off**: Higher latency (2.5s vs 0.8s)

> 📖 See [POSTMORTEM.md](docs/POSTMORTEM.md) for things that broke and how they were fixed

---

## 🔧 What Broke & How I Fixed It

### 1. **Alembic migrations failed: port mismatch**
**Problem**: Alembic couldn't find `.env`, used wrong DB URL  
**Solution**: Multi-path `.env` search in `config.py`

### 2. **HuggingFace API deprecation**
**Problem**: `InferenceClient` changed API, old `text_generation` params failed  
**Solution**: Migrated to OpenAI-compatible router (`/v1/chat/completions`)

### 3. **bcrypt/passlib version conflicts**
**Problem**: `passlib[bcrypt]` installation failed on Windows  
**Solution**: Direct `bcrypt` usage, removed passlib wrapper

### 4. **Pydantic EmailStr validation**
**Problem**: `EmailStr` requires `email-validator` but wasn't in requirements  
**Solution**: Added `email-validator==2.2.0` explicitly

> Full details in [POSTMORTEM.md](docs/POSTMORTEM.md)

---

## 🧪 Testing

```bash
# Run unit tests
pytest backend/tests/

# Run with coverage
pytest --cov=app --cov-report=html

# Run benchmarks
python scripts/benchmark.py
```

---

## 📚 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/token` | POST | Login & get JWT |
| `/api/v1/empresas/` | GET | List companies |
| `/api/v1/extractos/upload` | POST | Upload bank statement |
| `/api/v1/clasificacion/batch` | POST | Classify transactions (LangGraph agent) |
| `/api/v1/conciliacion/iniciar` | POST | Start reconciliation process |
| `/api/v1/tesoreria/{empresa_id}/snapshot` | GET | Treasury snapshot |
| `/api/v1/chat/` | POST | Conversational AI interface |
| `/health` | GET | Health check |
| `/docs` | GET | OpenAPI documentation |

---

## 📂 Project Structure

```
financial-ai-agent/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # REST endpoints
│   │   ├── agents/         # LangGraph agents
│   │   ├── core/           # Config, DB, Security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # HF Inference, Parsers
│   │   └── tasks/          # Celery workers
│   ├── alembic/            # DB migrations
│   └── requirements.txt
├── frontend/               # React SPA
├── scripts/
│   ├── benchmark.py        # Performance testing
│   └── generate_synthetic.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── POSTMORTEM.md
│   ├── METRICS.md
│   └── images/
├── tests/
├── docker-compose.yml
├── LICENSE
└── README.md
```

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Eduardo Glez-Mesones**  
📧 [e.gzlzmesones@gmail.com](mailto:e.gzlzmesones@gmail.com)  
🔗 [LinkedIn](https://www.linkedin.com/in/eduardo-gonzalez-mesones-de-la-sierra-65b2a3140/)

---

## 🙏 Acknowledgments

- FastAPI for the incredible async framework
- HuggingFace for accessible LLM inference
- LangGraph team for multi-agent orchestration
- pgvector contributors for PostgreSQL vector search

---

**⭐ If this project helped you, consider giving it a star!**
