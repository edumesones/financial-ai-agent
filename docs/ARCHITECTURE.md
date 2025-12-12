# 🏛️ Architecture Deep Dive

## Table of Contents
1. [System Overview](#system-overview)
2. [Data Flow](#data-flow)
3. [Multi-Agent System](#multi-agent-system)
4. [Database Schema](#database-schema)
5. [API Gateway](#api-gateway)
6. [Caching Strategy](#caching-strategy)
7. [Security & Multi-tenancy](#security--multi-tenancy)
8. [Deployment](#deployment)

---

## System Overview

```
                    ┌──────────────────────────────────────┐
                    │         Frontend (React)             │
                    │  - Dashboard                         │
                    │  - Transaction Review                │
                    │  - Cash Flow Charts                  │
                    └────────────┬─────────────────────────┘
                                 │ HTTPS
                                 ▼
                    ┌──────────────────────────────────────┐
                    │      FastAPI Gateway (8000)          │
                    │  - JWT Auth                          │
                    │  - OpenAPI Docs                      │
                    │  - Rate Limiting                     │
                    └─────┬────────────────────────────┬───┘
                          │                            │
        ┌─────────────────┴───────────┐                │
        │                             │                │
        ▼                             ▼                ▼
┌───────────────┐            ┌────────────────┐  ┌──────────┐
│  PostgreSQL   │            │   LangGraph    │  │  Redis   │
│  + pgvector   │            │    Agents      │  │  Cache   │
│               │            │                │  │          │
│ - Tenants     │            │ 1. Classifier  │  │ - Emb    │
│ - Empresas    │            │ 2. Reconcile   │  │ - Session│
│ - Transacciones│            │ 3. Treasury    │  │          │
│ - Embeddings  │            │                │  │          │
└───────┬───────┘            └────────┬───────┘  └──────────┘
        │                             │
        │                             ▼
        │                  ┌──────────────────────┐
        └─────────────────▶│   HuggingFace API    │
                           │  - Mixtral-8x7B      │
                           │  - BGE-M3 Embeddings │
                           └──────────────────────┘
```

---

## Data Flow

### 1. Transaction Classification Flow

```
User uploads CSV
       │
       ▼
┌─────────────────┐
│  Parser Service │  Auto-detect format (CSV/OFX/PDF)
│  (detectFormat) │  Parse rows → Transaction[]
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Store in Postgres│  bulk_insert(transactions)
│ (pending state) │
└────────┬────────┘
         │
         ▼
┌──────────────────────────┐
│  ClasificacionAgent      │
│  (LangGraph workflow)    │
│                          │
│  1. load_pending_tx()    │  SELECT WHERE estado = 'pending'
│  2. generate_embeddings()│  HF: BGE-M3 → vector(1024)
│  3. search_similar()     │  pgvector: cosine similarity
│  4. classify_with_llm()  │  HF: Mixtral-8x7B + context
│  5. validate_results()   │  confianza < 0.75 → human review
│  6. store_classifications│  UPDATE estado = 'classified'
└────────┬─────────────────┘
         │
         ▼
┌─────────────────┐
│  Human Review?  │  If confianza < threshold
│  (HITL)         │  → Pause agent, wait for approval
└────────┬────────┘
         │
         ▼
   ┌────┴─────┐
   │ Approved │ → Continue agent
   └──────────┘
```

### 2. Reconciliation Flow

```
User: "Reconcile Jan 2024"
       │
       ▼
┌──────────────────────────┐
│  ConciliacionAgent       │
│                          │
│  1. load_data()          │  SELECT transacciones, asientos
│  2. exact_match()        │  fecha + importe + concepto
│  3. fuzzy_match()        │  embedding similarity
│  4. prepare_review()     │  auto-approve if confianza >= 0.95
│     ├─ auto_approved     │
│     ├─ needs_review      │
│     └─ discrepancias     │
│  5. [CHECKPOINT]         │  ← Pause for human review
│  6. apply_decisions()    │  User validates matches
│  7. generate_summary()   │  Stats + report
└──────────────────────────┘
```

---

## Multi-Agent System

### Agent Architecture (LangGraph)

```python
# Each agent is a StateGraph with checkpoints

class AgentState(TypedDict):
    tenant_id: str
    session_id: str
    status: str  # processing | review | completed
    error: str | None
    # ... agent-specific fields

graph = StateGraph(AgentState)
graph.add_node("step1", func1)
graph.add_node("step2", func2)
graph.add_conditional_edges("step2", should_pause, {
    "pause": END,  # Human-in-the-loop
    "continue": "step3"
})
```

### Why LangGraph?

**Checkpointing for HITL**:
```python
# Agent pauses here
if needs_human_review:
    return END  # Frontend polls session

# User validates
POST /api/v1/clasificacion/{session_id}/validar
    → Resume agent with human_feedback
```

**State Persistence**:
```python
# Store in Redis or DB
session_store = {
    "session_123": {
        "status": "review",
        "propuestas": [...],
        "last_checkpoint": "prepare_review"
    }
}
```

---

## Database Schema

### Core Tables

```sql
-- Multi-tenancy isolation
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    nombre TEXT,
    config JSONB,
    activo BOOLEAN
);

-- Row Level Security (RLS)
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON tenants
    USING (id = current_setting('app.current_tenant')::UUID);

-- Empresas (companies)
CREATE TABLE empresas (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    nombre TEXT,
    cif TEXT UNIQUE
);

-- Transacciones (bank transactions)
CREATE TABLE transacciones (
    id UUID PRIMARY KEY,
    cuenta_id UUID REFERENCES cuentas_bancarias(id),
    fecha DATE,
    concepto TEXT,
    importe DECIMAL(12,2),
    embedding VECTOR(1024),  -- pgvector for similarity
    estado TEXT  -- pending | classified | conciliated
);

-- Clasificaciones (PGC classifications)
CREATE TABLE clasificaciones (
    id UUID PRIMARY KEY,
    transaccion_id UUID REFERENCES transacciones(id),
    categoria_pgc TEXT,  -- e.g., "628"
    subcuenta TEXT,
    confianza DECIMAL(3,2),  -- 0.00 - 1.00
    metodo TEXT,  -- llm | rule | manual
    validado_por UUID,
    validado_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_tx_embedding ON transacciones 
    USING ivfflat (embedding vector_cosine_ops);
```

### pgvector Queries

```sql
-- Find similar transactions
SELECT id, concepto, 
       1 - (embedding <=> $1) AS similarity
FROM transacciones
WHERE tenant_id = $2
ORDER BY embedding <=> $1
LIMIT 5;
```

---

## API Gateway

### Authentication Flow

```
1. POST /api/v1/auth/token
   Body: { email, password }
   ↓
2. Verify bcrypt hash
   ↓
3. Generate JWT:
   {
     "sub": user_id,
     "tenant_id": uuid,
     "rol": "admin",
     "exp": now() + 60min
   }
   ↓
4. Return { access_token, expires_at }

// Subsequent requests
Headers: { Authorization: "Bearer <token>" }
```

### Middleware Chain

```python
Request
  → CORS (allow localhost:5173)
  → JWT Validation
  → Rate Limiting (50 req/min)
  → Tenant Context (RLS)
  → Endpoint Handler
  → Structured Logging
  → Response
```

---

## Caching Strategy

### Embedding Cache (Redis)

```python
# Cache key: md5(text)
cache_key = f"emb:{hashlib.md5(text.encode()).hexdigest()}"

# Check cache
cached = await redis.get(cache_key)
if cached:
    return json.loads(cached)

# Generate and cache
embedding = await hf_client.feature_extraction(text)
await redis.setex(cache_key, 7_days, json.dumps(embedding))
```

**Cost Savings**:
- Embedding generation: ~$0.0001 per call
- Cache hit rate: ~60% (similar transactions)
- Savings: ~$0.00006 per cached call

### Session Cache

```python
# Store agent states
_sessions[session_id] = {
    "tenant_id": uuid,
    "status": "review",
    "propuestas": [...],
    "created_at": datetime.utcnow()
}
```

---

## Security & Multi-tenancy

### Row Level Security (PostgreSQL RLS)

```sql
-- Set tenant context on each request
SET app.current_tenant = 'uuid-here';

-- All queries automatically filtered
SELECT * FROM empresas;
-- Becomes: SELECT * FROM empresas 
--          WHERE tenant_id = current_setting('app.current_tenant')::UUID;
```

### SQLAlchemy Integration

```python
async def set_tenant_context(session: AsyncSession, tenant_id: str):
    await session.execute(
        text(f"SET app.current_tenant = '{tenant_id}'")
    )

# Middleware
@app.middleware("http")
async def tenant_middleware(request, call_next):
    if user := get_current_user(request):
        async with get_db() as db:
            await set_tenant_context(db, user.tenant_id)
    return await call_next(request)
```

---

## Deployment

### Docker Compose (Development)

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    ports: ["5432:5432"]
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD: dev

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [db, redis]
    environment:
      DATABASE_URL: postgresql+asyncpg://...
      HF_TOKEN: ${HF_TOKEN}
```

### Production Considerations

**Scaling**:
- Horizontal: Multiple FastAPI instances behind load balancer
- Vertical: PostgreSQL read replicas for embeddings search

**Observability**:
- Prometheus metrics (`/metrics`)
- Structlog JSON logs → ELK stack
- Sentry for error tracking

**CI/CD**:
```yaml
# .github/workflows/ci.yml
on: [push]
jobs:
  test:
    - pytest
    - coverage > 80%
  lint:
    - ruff
    - black --check
  deploy:
    if: branch == 'main'
    - docker build
    - kubectl apply
```

---

## Performance Optimizations

### 1. Async Everywhere
```python
# Bad (blocking)
result = requests.get(url)

# Good (async)
async with httpx.AsyncClient() as client:
    result = await client.get(url)
```

### 2. Connection Pooling
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,  # Concurrent connections
    max_overflow=10
)
```

### 3. Batch Processing
```python
# Bad: N+1 queries
for tx in transactions:
    await classify(tx)  # 100 API calls

# Good: Batch
embeddings = await generate_embeddings([tx.concepto for tx in transactions])
```

---

## Trade-offs & Design Decisions

| Decision | Pros | Cons | Rationale |
|----------|------|------|-----------|
| PostgreSQL + pgvector | Free, low latency | Manual scaling | On-premise requirement |
| HuggingFace vs OpenAI | 10x cheaper | 3x slower | Budget constraint |
| LangGraph vs Agents | Checkpointing HITL | Learning curve | Critical for financial |
| Async FastAPI | High concurrency | Complexity | Expected 100+ req/min |

---

**Next**: [POSTMORTEM.md](POSTMORTEM.md) - What broke and how we fixed it

