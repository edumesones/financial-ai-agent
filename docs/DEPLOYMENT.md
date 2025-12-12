# 🚀 Deployment Guide

## Table of Contents
1. [Development Setup](#development-setup)
2. [Production Deployment](#production-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Monitoring & Observability](#monitoring--observability)
6. [Backup & Recovery](#backup--recovery)

---

## Development Setup

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/edumesones/financial-ai-agent.git
cd financial-ai-agent

# 2. Start infrastructure
docker-compose up -d

# 3. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 4. Install dependencies
pip install -r backend/requirements.txt

# 5. Configure environment
cp .env.template .env
# Edit .env and add your HF_TOKEN

# 6. Run migrations
cd backend
alembic upgrade head

# 7. Generate test data (optional)
python scripts/generate_synthetic.py

# 8. Start backend
uvicorn app.main:app --reload --port 8000

# 9. Start frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Production Deployment

### Prerequisites
- Ubuntu 20.04+ or similar Linux distribution
- Python 3.11+
- PostgreSQL 16 with pgvector extension
- Redis 7+
- Nginx
- SSL certificate (Let's Encrypt recommended)

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv postgresql-16 redis-server nginx certbot

# Install pgvector
sudo apt install -y postgresql-16-pgvector
```

### Step 2: Database Setup

```bash
# Create database user
sudo -u postgres psql
CREATE USER agente_prod WITH PASSWORD 'your-secure-password';
CREATE DATABASE agente_financiero OWNER agente_prod;
\c agente_financiero
CREATE EXTENSION vector;
GRANT ALL PRIVILEGES ON DATABASE agente_financiero TO agente_prod;
\q
```

### Step 3: Application Deployment

```bash
# Create application user
sudo useradd -m -s /bin/bash agente
sudo su - agente

# Clone repository
git clone https://github.com/your-username/financial-ai-agent.git
cd financial-ai-agent

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
pip install gunicorn

# Configure environment
cp .env.template .env
nano .env  # Edit with production values
```

### Step 4: Systemd Service

Create `/etc/systemd/system/financial-ai-agent.service`:

```ini
[Unit]
Description=Financial AI Agent API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=agente
Group=agente
WorkingDirectory=/home/agente/financial-ai-agent/backend
Environment="PATH=/home/agente/financial-ai-agent/.venv/bin"
ExecStart=/home/agente/financial-ai-agent/.venv/bin/gunicorn \
    -k uvicorn.workers.UvicornWorker \
    -w 4 \
    -b 0.0.0.0:8000 \
    --access-logfile /var/log/financial-ai-agent/access.log \
    --error-logfile /var/log/financial-ai-agent/error.log \
    app.main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Create log directory
sudo mkdir -p /var/log/financial-ai-agent
sudo chown agente:agente /var/log/financial-ai-agent

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable financial-ai-agent
sudo systemctl start financial-ai-agent
sudo systemctl status financial-ai-agent
```

### Step 5: Nginx Configuration

Create `/etc/nginx/sites-available/financial-ai-agent`:

```nginx
upstream backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Logging
    access_log /var/log/nginx/financial-ai-agent-access.log;
    error_log /var/log/nginx/financial-ai-agent-error.log;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=50r/m;
    limit_req zone=api_limit burst=20 nodelay;
    
    # Proxy settings
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files (if serving frontend from same domain)
    location /static {
        alias /home/agente/financial-ai-agent/frontend/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/financial-ai-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d api.yourdomain.com
```

---

## Docker Deployment

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: agente_financiero
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - backend

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    restart: unless-stopped
    networks:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@db:5432/agente_financiero
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      HF_TOKEN: ${HF_TOKEN}
      JWT_SECRET: ${JWT_SECRET}
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.tasks.celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@db:5432/agente_financiero
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/1
      HF_TOKEN: ${HF_TOKEN}
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - backend

volumes:
  pgdata:

networks:
  backend:
```

### Production Dockerfile

Create `backend/Dockerfile.prod`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 agente && chown -R agente:agente /app
USER agente

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run with gunicorn
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "app.main:app"]
```

---

## Kubernetes Deployment

### Kubernetes Manifests

`k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: financial-ai-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: financial-ai-agent
  template:
    metadata:
      labels:
        app: financial-ai-agent
    spec:
      containers:
      - name: backend
        image: your-registry/financial-ai-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: HF_TOKEN
          valueFrom:
            secretKeyRef:
              name: hf-secret
              key: token
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## Monitoring & Observability

### Prometheus Metrics

Add to FastAPI app:

```python
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('request_duration_seconds', 'Request duration')

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Logging

Configure structured logging:

```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)
```

---

## Backup & Recovery

### Database Backups

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgresql"
pg_dump -U agente_prod agente_financiero | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

### Restore

```bash
gunzip < backup_20241211_120000.sql.gz | psql -U agente_prod agente_financiero
```

---

**Security Checklist**:
- [ ] Use strong passwords
- [ ] Enable SSL/TLS
- [ ] Configure firewall (ufw)
- [ ] Set up fail2ban
- [ ] Regular security updates
- [ ] Monitor logs
- [ ] Backup database daily
- [ ] Use secrets management (Vault, AWS Secrets Manager)

