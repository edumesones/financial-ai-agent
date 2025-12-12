# Environment Variables

Copy `.env.template` to `.env` and configure:

```bash
cp .env.template .env
```

## Required Variables

### Database
```env
DATABASE_URL=postgresql+asyncpg://agente:agente_dev@localhost:5432/agente_financiero
DATABASE_URL_SYNC=postgresql://agente:agente_dev@localhost:5432/agente_financiero
```

### Redis
```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### Hugging Face API
```env
HF_TOKEN=your_huggingface_token_here
```
Get your token at: https://huggingface.co/settings/tokens

### Models (Optional - defaults provided)
```env
HF_MODEL_LLM=mistralai/Mixtral-8x7B-Instruct-v0.1
HF_MODEL_EMBEDDINGS=BAAI/bge-m3
```

### JWT Configuration
```env
JWT_SECRET=change-this-to-a-random-secret-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

### Application
```env
APP_ENV=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Agent Thresholds
```env
CONCILIACION_AUTO_APPROVE_THRESHOLD=0.95
CLASIFICACION_REVIEW_THRESHOLD=0.75
```

