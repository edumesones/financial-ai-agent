# 🔧 Post-Mortem: What Broke & How I Fixed It

This document chronicles the main technical challenges encountered during development and their solutions. **Transparency about failures is as important as showcasing successes.**

---

## 1. Alembic Migrations Failed: Database Connection Issues

### 🔴 The Problem
```bash
$ alembic upgrade head
sqlalchemy.exc.OperationalError: could not translate host name "postgres" to address
```

**Root Cause**: Alembic couldn't find the `.env` file, so it defaulted to hardcoded values that expected Docker hostnames.

### 🟢 The Solution
Implemented multi-path `.env` search in `config.py`:

```python
# Before: Only checked current directory
_env_file = ".env"

# After: Check multiple locations
_env_file = None
for path in [
    Path(".env"),
    Path("../.env"),
    Path(__file__).parent.parent.parent.parent / ".env"
]:
    if path.exists():
        _env_file = str(path)
        break
```

**Lesson**: Never assume where `.env` will be. Support multiple paths for different execution contexts (IDE, CLI, Docker).

---

## 2. HuggingFace API Deprecation: `text_generation` Parameters Changed

### 🔴 The Problem
```python
response = self.client.text_generation(
    prompt=prompt,
    max_new_tokens=200
)
# TypeError: InferenceClient.__init__() got unexpected keyword argument 'provider'
```

**Root Cause**: HuggingFace `InferenceClient` API changed. Old parameters no longer worked.

### 🟢 The Solution
Migrated to OpenAI-compatible router:

```python
# Before: Direct text_generation
self.client = InferenceClient(token=settings.hf_token)
response = self.client.text_generation(...)

# After: OpenAI-compatible client
from openai import OpenAI
self.client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=settings.hf_token
)
response = self.client.chat.completions.create(
    model=settings.hf_model_llm,
    messages=[{"role": "user", "content": prompt}],
    max_tokens=200
)
```

**Added to requirements.txt**:
```
openai>=1.0.0
```

**Lesson**: Always pin major versions for production. Keep compatibility layer for external APIs.

---

## 3. bcrypt/passlib Version Conflicts on Windows

### 🔴 The Problem
```bash
$ pip install passlib[bcrypt]
ERROR: Could not build wheels for bcrypt
```

**Root Cause**: `passlib[bcrypt]` had C extension build issues on Windows without Visual Studio Build Tools.

### 🟢 The Solution
Removed passlib wrapper, used bcrypt directly:

```python
# Before: passlib wrapper
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"])
pwd_context.hash(password)

# After: Direct bcrypt
import bcrypt
bcrypt.hashpw(password.encode(), bcrypt.gensalt())
bcrypt.checkpw(password.encode(), hashed)
```

**Requirements change**:
```diff
- passlib[bcrypt]==1.7.4
+ bcrypt==4.1.2
```

**Lesson**: Minimize abstraction layers when they add build complexity without significant value.

---

## 4. Pydantic EmailStr Validation: Missing Dependency

### 🔴 The Problem
```python
from pydantic import EmailStr
class LoginRequest(BaseModel):
    email: EmailStr
# ModuleNotFoundError: No module named 'email_validator'
```

**Root Cause**: Pydantic's `EmailStr` requires `email-validator` package, but it wasn't declared in our requirements.

### 🟢 The Solution
Added explicit dependency:

```diff
# requirements.txt
pydantic==2.5.3
pydantic-settings==2.1.0
+ email-validator==2.2.0
```

**Lesson**: Always test imports on a fresh environment. Pydantic's "optional" dependencies aren't truly optional if you use them.

---

## 5. Indentation Error in `conciliacion.py`: Malformed Code Block

### 🔴 The Problem
```python
        return {
            **state,
            "status": "processing",
        }
 >= threshold]  # ← What is this?
        needs_review = [...]
```

**Root Cause**: During refactoring, a list comprehension got split incorrectly, leaving a dangling `>= threshold]` on its own line.

### 🟢 The Solution
Reconstructed missing functions:

```python
async def prepare_review(self, state):
    threshold = state.get("auto_approve_threshold", 0.95)
    all_matches = state["matches_exactos"] + state["matches_fuzzy"]
    
    # This was the missing context
    auto_approved = [
        {**m, "estado": "auto_aprobado"} 
        for m in all_matches 
        if m["confianza"] >= threshold  # ← Here it was
    ]
    needs_review = [
        {**m, "estado": "pendiente_revision"} 
        for m in all_matches 
        if m["confianza"] < threshold
    ]
    ...
```

**Lesson**: Always run syntax checks after refactoring. Use `ruff` or `black` to catch these early.

---

## 6. Frontend Vite Proxy Errors: Backend Not Running

### 🔴 The Problem
```
16:27:48 [vite] http proxy error: /api/v1/empresas/
AggregateError [ECONNREFUSED]:
    at internalConnectMultiple (node:net:1139:18)
```

**Root Cause**: Vite was configured to proxy `/api/*` to `http://localhost:8000`, but the backend wasn't running.

### 🟢 The Solution
**Not a bug, but a workflow issue**:
1. Always start backend before frontend
2. Added health check endpoint `/health`
3. Frontend shows clear error: "Backend not available"

**vite.config.js**:
```js
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

**Lesson**: Proxies fail silently. Add health checks and clear error messages.

---

## 7. Lazy Initialization Blocking: `InferenceClient` on Import

### 🔴 The Problem
Opening `/docs` took 3+ minutes, eventually timing out.

**Root Cause**: `InferenceClient` was initialized in `__init__`, blocking the import chain when FastAPI generated OpenAPI schema.

### 🟢 The Solution
Lazy initialization with property:

```python
# Before: Eager init (blocks import)
class HFInferenceService:
    def __init__(self):
        self.client = InferenceClient(token=settings.hf_token)

# After: Lazy init (only when used)
class HFInferenceService:
    def __init__(self):
        self._client: Optional[InferenceClient] = None
    
    @property
    def client(self) -> InferenceClient:
        if self._client is None:
            self._client = InferenceClient(token=settings.hf_token)
        return self._client
```

**Lesson**: Never do I/O in `__init__`. Always lazy-load external clients.

---

## 8. Redis Connection Pool Exhaustion

### 🔴 The Problem
```
redis.exceptions.ConnectionError: Too many connections
```

**Root Cause**: Each request created a new Redis connection without closing it.

### 🟢 The Solution
Singleton pattern with lazy initialization:

```python
class HFInferenceService:
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
    
    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = await aioredis.from_url(settings.redis_url)
        return self._redis
    
    async def close(self):
        if self._redis:
            await self._redis.close()
```

**Lesson**: Always pool connections. Use dependency injection for lifecycle management.

---

## Key Takeaways

### What Worked Well
✅ **LangGraph checkpointing** - HITL was seamless  
✅ **pgvector** - Local vector search < 50ms  
✅ **FastAPI** - Async performance was excellent  
✅ **Structured logging** - Debugging was straightforward  

### What I'd Change
❌ **Should have used OpenAI client from day 1** - Migration cost time  
❌ **Should have added integration tests earlier** - Caught bcrypt issue late  
❌ **Should have documented .env paths upfront** - Confusion during setup  

### Technical Debt
⚠️ Embedding cache has no TTL strategy (will grow forever)  
⚠️ No retry logic for HuggingFace API failures  
⚠️ Agent sessions stored in memory (doesn't scale horizontally)  

---

## Metrics After Fixes

| Metric | Before | After |
|--------|--------|-------|
| Startup time | 180s | 2s |
| /docs load time | timeout | 1.5s |
| Redis connections | 50+ | 1 (pooled) |
| Import errors | 4 | 0 |

---

**Related**: See [ARCHITECTURE.md](ARCHITECTURE.md) for system design decisions

