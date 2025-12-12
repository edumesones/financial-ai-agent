# PROMPT.md: Instrucciones para Generación de Código

> **Versión:** 1.0  
> **Fecha:** Diciembre 2024  
> **Proyecto:** Agente Financiero IA

---

## 🎯 CONTEXTO DEL PROYECTO

Eres un ingeniero de software senior especializado en sistemas de IA y Python. Tu tarea es implementar **Agente Financiero IA**, un sistema multi-agente SaaS para gestorías que automatiza:

1. **Conciliación bancaria** - Matching automático banco ↔ contabilidad
2. **Clasificación de gastos** - Categorización según Plan General Contable
3. **Análisis de tesorería** - Dashboard y proyección de cash flow

### Documentos de Referencia
- **PRD.md**: Requisitos funcionales y user stories
- **ARCHITECT.md**: Arquitectura técnica, stack, y modelo de datos

### Principios Fundamentales
1. **Human-in-the-loop**: Toda decisión crítica requiere validación humana
2. **Auditable**: Cada acción del sistema es trazable
3. **Multi-tenant**: Aislamiento completo de datos entre clientes
4. **Modular**: Agentes independientes y desacoplados

---

## 📁 ESTRUCTURA DEL PROYECTO

```
agente-financiero-ia/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/v1/
│   │   ├── agents/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── tasks/
│   ├── alembic/
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   └── src/
├── ml/
├── infra/
├── docs/
└── scripts/
```

---

## 🔧 STACK TECNOLÓGICO

### Backend (Python 3.11+)
```toml
[project]
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "celery[redis]>=5.3.0",
    "redis>=5.0.0",
    "langgraph>=0.0.40",
    "langchain>=0.1.0",
    "huggingface-hub>=0.19.0",
    "boto3>=1.33.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.6",
    "ofxparse>=0.21",
    "pandas>=2.1.0",
    "numpy>=1.26.0",
    "structlog>=23.2.0",
    "prometheus-client>=0.19.0",
    "opentelemetry-api>=1.21.0",
    "opentelemetry-sdk>=1.21.0",
    "reportlab>=4.0.0",
    "jinja2>=3.1.0",
    "httpx>=0.25.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "black>=23.11.0",
    "ruff>=0.1.6",
    "mypy>=1.7.0",
    "pre-commit>=3.6.0",
]
```

### Frontend (Node 20+)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.3.0",
    "@tanstack/react-query": "^5.8.0",
    "@tanstack/react-table": "^8.10.0",
    "zustand": "^4.4.0",
    "recharts": "^2.10.0",
    "tailwindcss": "^3.3.0",
    "axios": "^1.6.0",
    "react-router-dom": "^6.20.0",
    "date-fns": "^2.30.0"
  }
}
```

---

## 📋 ORDEN DE IMPLEMENTACIÓN

Implementa en este orden estricto. Cada fase debe estar completa y testeada antes de continuar.

### FASE 1: Infraestructura Base (Semana 1)

#### 1.1 Configuración del Proyecto
```bash
mkdir -p backend/app/{api/v1,agents,core,models,schemas,services,tasks}
mkdir -p backend/{alembic/versions,tests}
mkdir -p frontend/src/{components,pages,hooks,stores,services,types}
mkdir -p {ml/notebooks,ml/data,ml/models}
mkdir -p {infra,docs,scripts}
```

#### 1.2 Backend Core (`backend/app/`)

**Archivo: `config.py`**
```python
"""
Configuración centralizada usando pydantic-settings.
Variables de entorno con valores por defecto para desarrollo.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://agente:dev@localhost:5432/agente_financiero"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # S3/MinIO
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "agente-documents"
    
    # Hugging Face
    hf_api_key: str = ""
    hf_model_llm: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    hf_model_embeddings: str = "BAAI/bge-m3"
    
    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    
    # App
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Archivo: `core/database.py`**
```python
"""
Conexión async a PostgreSQL con SQLAlchemy 2.0.
Incluye middleware para tenant isolation via RLS.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from contextlib import asynccontextmanager
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    pool_size=20,
    max_overflow=10,
)

async_session_maker = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def set_tenant_context(session: AsyncSession, tenant_id: str):
    """Establecer contexto de tenant para RLS"""
    await session.execute(f"SET app.current_tenant = '{tenant_id}'")
```

**Archivo: `core/security.py`**
```python
"""
JWT authentication y password hashing.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

class TokenPayload(BaseModel):
    sub: str  # user_id
    tenant_id: str
    email: str
    rol: str
    exp: datetime

def create_access_token(
    user_id: UUID,
    tenant_id: UUID, 
    email: str,
    rol: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "email": email,
        "rol": rol,
        "exp": expire
    }
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def verify_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return TokenPayload(**payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    return verify_token(token)

def require_role(allowed_roles: list[str]):
    def decorator(current_user: TokenPayload = Depends(get_current_user)):
        if current_user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes"
            )
        return current_user
    return decorator
```

**Archivo: `main.py`**
```python
"""
FastAPI application factory.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.config import get_settings
from app.core.database import engine
from app.api.v1 import extractos, conciliacion, clasificacion, tesoreria, informes

settings = get_settings()
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Agente Financiero IA API")
    yield
    # Shutdown
    await engine.dispose()
    logger.info("Shutting down API")

def create_app() -> FastAPI:
    app = FastAPI(
        title="Agente Financiero IA",
        description="API para automatización de análisis financiero en gestorías",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Routers
    app.include_router(extractos.router, prefix="/api/v1")
    app.include_router(conciliacion.router, prefix="/api/v1")
    app.include_router(clasificacion.router, prefix="/api/v1")
    app.include_router(tesoreria.router, prefix="/api/v1")
    app.include_router(informes.router, prefix="/api/v1")
    
    # Health check
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "1.0.0"}
    
    # Exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"}
        )
    
    return app

app = create_app()
```

#### 1.3 Modelos de Base de Datos (`backend/app/models/`)

**Archivo: `base.py`**
```python
"""Base model con campos comunes."""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

class UUIDMixin:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
```

**Archivo: `tenant.py`**
```python
"""Modelo Tenant (gestoría)."""
from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, UUIDMixin, TimestampMixin

class Tenant(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tenant"
    
    nombre: Mapped[str] = mapped_column(String(255))
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="tenant")
    empresas: Mapped[list["Empresa"]] = relationship(back_populates="tenant")
```

**Archivo: `empresa.py`**
```python
"""Modelos Empresa y CuentaBancaria."""
from uuid import UUID
from sqlalchemy import String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, UUIDMixin, TimestampMixin

class Empresa(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "empresa"
    
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenant.id"), index=True)
    nombre: Mapped[str] = mapped_column(String(255))
    cif: Mapped[str | None] = mapped_column(String(20))
    sector: Mapped[str | None] = mapped_column(String(100))
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="empresas")
    cuentas: Mapped[list["CuentaBancaria"]] = relationship(back_populates="empresa")

class CuentaBancaria(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cuenta_bancaria"
    
    empresa_id: Mapped[UUID] = mapped_column(ForeignKey("empresa.id"), index=True)
    banco: Mapped[str | None] = mapped_column(String(100))
    iban: Mapped[str | None] = mapped_column(String(34))
    alias: Mapped[str | None] = mapped_column(String(100))
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    empresa: Mapped["Empresa"] = relationship(back_populates="cuentas")
    transacciones: Mapped[list["Transaccion"]] = relationship(back_populates="cuenta")
```

**Archivo: `transaccion.py`**
```python
"""Modelo Transaccion con embedding vectorial."""
from datetime import date
from decimal import Decimal
from uuid import UUID
from sqlalchemy import String, Date, Numeric, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from .base import Base, UUIDMixin, TimestampMixin

class Transaccion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "transaccion"
    
    cuenta_id: Mapped[UUID] = mapped_column(ForeignKey("cuenta_bancaria.id"), index=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    fecha_valor: Mapped[date | None] = mapped_column(Date)
    importe: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    concepto: Mapped[str | None] = mapped_column(String(500))
    tipo: Mapped[str] = mapped_column(String(20))  # ingreso, gasto, transferencia
    referencia: Mapped[str | None] = mapped_column(String(100))
    hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024))
    
    # Relationships
    cuenta: Mapped["CuentaBancaria"] = relationship(back_populates="transacciones")
    clasificacion: Mapped["Clasificacion | None"] = relationship(back_populates="transaccion", uselist=False)
    conciliacion: Mapped["Conciliacion | None"] = relationship(back_populates="transaccion", uselist=False)
    
    __table_args__ = (
        Index("idx_transaccion_cuenta_fecha", "cuenta_id", "fecha"),
    )
```

**Archivo: `clasificacion.py`**
```python
"""Modelos Clasificacion, Conciliacion, ReglaClasificacion."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from sqlalchemy import String, Numeric, JSON, ForeignKey, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, UUIDMixin, TimestampMixin

class Clasificacion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "clasificacion"
    
    transaccion_id: Mapped[UUID] = mapped_column(ForeignKey("transaccion.id"), index=True)
    categoria_pgc: Mapped[str] = mapped_column(String(10))
    confianza: Mapped[Decimal] = mapped_column(Numeric(3, 2))
    metodo: Mapped[str] = mapped_column(String(20))  # regla, historico, ml, llm, manual
    explicacion: Mapped[str | None] = mapped_column(String(500))
    validado_por: Mapped[UUID | None] = mapped_column(ForeignKey("usuario.id"))
    validado_at: Mapped[datetime | None] = mapped_column(DateTime)
    
    # Relationships
    transaccion: Mapped["Transaccion"] = relationship(back_populates="clasificacion")

class Conciliacion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conciliacion"
    
    transaccion_id: Mapped[UUID] = mapped_column(ForeignKey("transaccion.id"), index=True)
    asiento_id: Mapped[UUID | None] = mapped_column()  # Referencia externa
    confianza: Mapped[Decimal] = mapped_column(Numeric(3, 2))
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    match_details: Mapped[dict | None] = mapped_column(JSON)
    validado_por: Mapped[UUID | None] = mapped_column(ForeignKey("usuario.id"))
    validado_at: Mapped[datetime | None] = mapped_column(DateTime)
    
    # Relationships
    transaccion: Mapped["Transaccion"] = relationship(back_populates="conciliacion")

class ReglaClasificacion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "regla_clasificacion"
    
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenant.id"), index=True)
    empresa_id: Mapped[UUID | None] = mapped_column(ForeignKey("empresa.id"))
    nombre: Mapped[str] = mapped_column(String(100))
    condicion: Mapped[dict] = mapped_column(JSON)
    categoria_pgc: Mapped[str] = mapped_column(String(10))
    prioridad: Mapped[int] = mapped_column(Integer, default=0)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
```

---

### FASE 2: Servicios Core (Semana 2)

#### 2.1 Servicio de Hugging Face (`backend/app/services/hf_inference.py`)

```python
"""
Cliente para Hugging Face Inference API.
"""
from typing import Optional
import asyncio
import hashlib
import json

from huggingface_hub import InferenceClient
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()
logger = structlog.get_logger()

class HFInferenceService:
    def __init__(self):
        self.client = InferenceClient(token=settings.hf_api_key)
        self.redis = redis.from_url(settings.redis_url)
        self.embedding_cache_ttl = 86400 * 7  # 7 días
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def classify_transaction(
        self, 
        concepto: str, 
        importe: float,
        historico: Optional[list[dict]] = None
    ) -> dict:
        """Clasificar transacción usando LLM."""
        
        historico_text = ""
        if historico:
            historico_text = "\n".join([
                f"- {h['concepto']}: {h['categoria']} ({h['confianza']})"
                for h in historico[:5]
            ])
        
        prompt = f"""Clasifica la siguiente transacción bancaria según el Plan General Contable español (PGC).

Transacción:
- Concepto: {concepto}
- Importe: {importe}€
- Tipo: {"GASTO" if importe < 0 else "INGRESO"}

{f"Clasificaciones similares previas del cliente:{chr(10)}{historico_text}" if historico_text else ""}

Categorías principales de gastos (600-629):
- 600: Compras de mercaderías
- 621: Arrendamientos y cánones
- 622: Reparaciones y conservación
- 623: Servicios profesionales independientes
- 624: Transportes
- 625: Primas de seguros
- 626: Servicios bancarios y similares
- 627: Publicidad, propaganda y relaciones públicas
- 628: Suministros
- 629: Otros servicios

Responde SOLO con un JSON válido (sin markdown):
{{"categoria_pgc": "XXX", "nombre_categoria": "...", "confianza": 0.XX, "explicacion": "..."}}
"""
        
        try:
            response = await asyncio.to_thread(
                self.client.text_generation,
                model=settings.hf_model_llm,
                prompt=prompt,
                max_new_tokens=200,
                temperature=0.1,
            )
            
            # Parsear respuesta JSON
            result = json.loads(response.strip())
            logger.info("classification_completed", concepto=concepto[:50], categoria=result["categoria_pgc"])
            return result
            
        except json.JSONDecodeError as e:
            logger.error("classification_parse_error", error=str(e), response=response[:200])
            return {
                "categoria_pgc": "629",
                "nombre_categoria": "Otros servicios",
                "confianza": 0.5,
                "explicacion": "No se pudo clasificar automáticamente"
            }
    
    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generar embeddings con caché."""
        
        results = []
        texts_to_compute = []
        cache_keys = []
        
        # Verificar caché
        for text in texts:
            cache_key = f"emb:{hashlib.md5(text.encode()).hexdigest()}"
            cache_keys.append(cache_key)
            
            cached = await self.redis.get(cache_key)
            if cached:
                results.append(json.loads(cached))
            else:
                results.append(None)
                texts_to_compute.append((len(results) - 1, text))
        
        # Computar embeddings faltantes
        if texts_to_compute:
            indices, batch_texts = zip(*texts_to_compute)
            
            embeddings = await asyncio.to_thread(
                self.client.feature_extraction,
                model=settings.hf_model_embeddings,
                inputs=list(batch_texts),
            )
            
            # Guardar en caché y resultados
            for idx, embedding in zip(indices, embeddings):
                results[idx] = embedding
                await self.redis.setex(
                    cache_keys[idx],
                    self.embedding_cache_ttl,
                    json.dumps(embedding)
                )
        
        return results
    
    async def compute_similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """Calcular similitud coseno entre dos embeddings."""
        import numpy as np
        
        a = np.array(embedding1)
        b = np.array(embedding2)
        
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
```

#### 2.2 Parsers de Extractos (`backend/app/services/parsers/`)

**Archivo: `base.py`**
```python
"""Clase base para parsers de extractos bancarios."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from datetime import date
import hashlib

@dataclass
class TransaccionRaw:
    fecha: date
    concepto: str
    importe: Decimal
    saldo: Decimal | None = None
    referencia: str | None = None
    
    def compute_hash(self) -> str:
        """Hash único para detectar duplicados."""
        data = f"{self.fecha.isoformat()}|{self.concepto}|{float(self.importe)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

class BankParser(ABC):
    @abstractmethod
    def parse(self, content: bytes) -> list[TransaccionRaw]:
        """Parsear contenido y devolver transacciones."""
        pass
    
    @abstractmethod
    def detect(self, content: bytes) -> bool:
        """Detectar si este parser puede manejar el contenido."""
        pass
    
    @staticmethod
    def normalize_amount(value: str) -> Decimal:
        """Normalizar importe desde string."""
        # Eliminar espacios y símbolos de moneda
        cleaned = value.strip().replace("€", "").replace("EUR", "").strip()
        
        # Detectar formato español (1.234,56) vs internacional (1,234.56)
        if "," in cleaned and "." in cleaned:
            if cleaned.rindex(",") > cleaned.rindex("."):
                # Formato español
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                # Formato internacional
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")
        
        return Decimal(cleaned)
    
    @staticmethod
    def parse_date(value: str) -> date:
        """Parsear fecha desde múltiples formatos."""
        from datetime import datetime
        
        formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d.%m.%Y",
            "%d/%m/%y",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
        
        raise ValueError(f"Formato de fecha no reconocido: {value}")
```

**Archivo: `csv_parser.py`**
```python
"""Parser genérico CSV con detección automática."""
import csv
import re
import io
from .base import BankParser, TransaccionRaw

class CSVGenericParser(BankParser):
    """Parser genérico CSV con detección automática de columnas."""
    
    COLUMN_PATTERNS = {
        "fecha": re.compile(r"fecha|date|f\.|valor|fec", re.IGNORECASE),
        "concepto": re.compile(r"concepto|descripcion|description|detalle|movimiento", re.IGNORECASE),
        "importe": re.compile(r"importe|amount|cantidad|cargo|abono|€", re.IGNORECASE),
        "saldo": re.compile(r"saldo|balance", re.IGNORECASE),
    }
    
    def detect(self, content: bytes) -> bool:
        """Detectar si es CSV válido."""
        try:
            text = content.decode("utf-8-sig")[:2000]
            dialect = csv.Sniffer().sniff(text)
            return True
        except:
            return False
    
    def parse(self, content: bytes) -> list[TransaccionRaw]:
        """Parsear CSV genérico."""
        # Detectar encoding
        text = content.decode("utf-8-sig")
        
        # Detectar delimitador
        dialect = csv.Sniffer().sniff(text[:2000])
        
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        
        # Mapear columnas
        column_map = self._detect_columns(reader.fieldnames)
        
        transactions = []
        for row in reader:
            try:
                tx = TransaccionRaw(
                    fecha=self.parse_date(row[column_map["fecha"]]),
                    concepto=row[column_map["concepto"]].strip(),
                    importe=self.normalize_amount(row[column_map["importe"]]),
                    saldo=self.normalize_amount(row[column_map["saldo"]]) if column_map.get("saldo") else None,
                )
                transactions.append(tx)
            except (KeyError, ValueError) as e:
                continue  # Skip filas con errores
        
        return transactions
    
    def _detect_columns(self, fieldnames: list[str]) -> dict[str, str]:
        """Detectar columnas por nombre."""
        column_map = {}
        
        for field in fieldnames:
            for col_type, pattern in self.COLUMN_PATTERNS.items():
                if pattern.search(field) and col_type not in column_map:
                    column_map[col_type] = field
                    break
        
        # Validar columnas requeridas
        required = ["fecha", "concepto", "importe"]
        missing = [r for r in required if r not in column_map]
        if missing:
            raise ValueError(f"Columnas requeridas no encontradas: {missing}")
        
        return column_map
```

**Archivo: `ofx_parser.py`**
```python
"""Parser para formato OFX/QFX."""
import io
from ofxparse import OfxParser as OFX
from .base import BankParser, TransaccionRaw
from decimal import Decimal

class OFXParser(BankParser):
    """Parser para formato OFX/QFX estándar bancario."""
    
    def detect(self, content: bytes) -> bool:
        """Detectar si es OFX válido."""
        text = content.decode("utf-8", errors="ignore")[:500]
        return "OFXHEADER" in text or "<OFX>" in text
    
    def parse(self, content: bytes) -> list[TransaccionRaw]:
        """Parsear OFX."""
        ofx = OFX.parse(io.BytesIO(content))
        
        transactions = []
        for account in ofx.accounts:
            for tx in account.statement.transactions:
                transactions.append(TransaccionRaw(
                    fecha=tx.date.date(),
                    concepto=(tx.memo or tx.payee or "").strip(),
                    importe=Decimal(str(tx.amount)),
                    referencia=tx.id,
                ))
        
        return transactions
```

**Archivo: `factory.py`**
```python
"""Factory para seleccionar parser correcto."""
from .base import BankParser
from .csv_parser import CSVGenericParser
from .ofx_parser import OFXParser

PARSERS = [
    OFXParser(),
    CSVGenericParser(),
]

def get_parser(formato: str, content: bytes) -> BankParser:
    """Obtener parser apropiado para el contenido."""
    
    if formato.lower() in ("ofx", "qfx"):
        return OFXParser()
    
    # Auto-detect
    for parser in PARSERS:
        if parser.detect(content):
            return parser
    
    raise ValueError(f"No se encontró parser para el contenido")
```

---

### FASE 3: Sistema de Agentes (Semanas 3-4)

#### 3.1 Base Agent (`backend/app/agents/base.py`)

```python
"""Clase base para todos los agentes usando LangGraph."""
from abc import ABC, abstractmethod
from typing import TypedDict, Annotated, Any
from uuid import UUID
import structlog

from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.hf_inference import HFInferenceService

logger = structlog.get_logger()

class AgentState(TypedDict):
    """Estado base compartido por todos los agentes."""
    tenant_id: str
    session_id: str
    status: str  # loading, processing, review, completed, error
    messages: list[dict]
    results: dict
    requires_human: bool
    human_feedback: dict | None
    error: str | None

class BaseAgent(ABC):
    """
    Agente base con checkpointing y logging.
    """
    
    def __init__(self, db: AsyncSession, hf_service: HFInferenceService):
        self.db = db
        self.hf = hf_service
    
    @abstractmethod
    def build_graph(self) -> StateGraph:
        """Construir grafo de estados del agente."""
        pass
    
    async def run(self, initial_state: dict) -> dict:
        """Ejecutar agente hasta completion o checkpoint."""
        graph = self.build_graph()
        app = graph.compile()
        
        logger.info(
            "agent_started",
            agent=self.__class__.__name__,
            session_id=initial_state.get("session_id")
        )
        
        try:
            result = await app.ainvoke(initial_state)
            
            logger.info(
                "agent_completed",
                agent=self.__class__.__name__,
                session_id=initial_state.get("session_id"),
                status=result.get("status")
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "agent_error",
                agent=self.__class__.__name__,
                error=str(e)
            )
            raise
    
    def log_step(self, step_name: str, state: dict, **extra):
        """Log de cada paso del agente."""
        logger.info(
            "agent_step",
            agent=self.__class__.__name__,
            step=step_name,
            session_id=state.get("session_id"),
            **extra
        )
```

#### 3.2 Agente de Conciliación (`backend/app/agents/conciliacion.py`)

```python
"""Agente especializado en conciliación bancaria."""
from typing import TypedDict
from uuid import UUID
from decimal import Decimal
from datetime import timedelta

from langgraph.graph import StateGraph, END
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseAgent, AgentState
from app.models.transaccion import Transaccion
from app.models.clasificacion import Conciliacion
from app.services.hf_inference import HFInferenceService

class ConciliacionState(AgentState):
    empresa_id: str
    periodo_inicio: str
    periodo_fin: str
    transacciones: list[dict]
    asientos: list[dict]
    matches_exactos: list[dict]
    matches_fuzzy: list[dict]
    propuestas: list[dict]
    discrepancias: list[dict]
    auto_approve_threshold: float

class ConciliacionAgent(BaseAgent):
    """
    Agente de conciliación bancaria.
    
    Flujo:
    1. load_data -> exact_match -> fuzzy_match -> prepare_review
    2. [CHECKPOINT si hay propuestas para revisar]
    3. apply_decisions -> generate_summary -> END
    """
    
    def build_graph(self) -> StateGraph:
        graph = StateGraph(ConciliacionState)
        
        # Nodos
        graph.add_node("load_data", self.load_data)
        graph.add_node("exact_match", self.exact_match)
        graph.add_node("fuzzy_match", self.fuzzy_match)
        graph.add_node("prepare_review", self.prepare_review)
        graph.add_node("apply_decisions", self.apply_decisions)
        graph.add_node("generate_summary", self.generate_summary)
        
        # Edges
        graph.add_edge("load_data", "exact_match")
        graph.add_edge("exact_match", "fuzzy_match")
        graph.add_edge("fuzzy_match", "prepare_review")
        
        # Conditional: si hay propuestas para revisar, pausar
        graph.add_conditional_edges(
            "prepare_review",
            self._should_pause_for_review,
            {
                "pause": END,  # Pausar para revisión humana
                "continue": "apply_decisions"
            }
        )
        
        graph.add_edge("apply_decisions", "generate_summary")
        graph.add_edge("generate_summary", END)
        
        graph.set_entry_point("load_data")
        
        return graph
    
    def _should_pause_for_review(self, state: ConciliacionState) -> str:
        """Decidir si pausar para revisión humana."""
        propuestas_pendientes = [
            p for p in state["propuestas"]
            if p["confianza"] < state.get("auto_approve_threshold", 0.95)
        ]
        
        if propuestas_pendientes and not state.get("human_feedback"):
            return "pause"
        return "continue"
    
    async def load_data(self, state: ConciliacionState) -> dict:
        """Cargar transacciones del periodo."""
        self.log_step("load_data", state)
        
        # Query transacciones
        stmt = select(Transaccion).where(
            Transaccion.cuenta_id.in_(
                select(CuentaBancaria.id).where(
                    CuentaBancaria.empresa_id == state["empresa_id"]
                )
            ),
            Transaccion.fecha >= state["periodo_inicio"],
            Transaccion.fecha <= state["periodo_fin"]
        )
        
        result = await self.db.execute(stmt)
        transacciones = result.scalars().all()
        
        return {
            **state,
            "transacciones": [
                {
                    "id": str(t.id),
                    "fecha": t.fecha.isoformat(),
                    "concepto": t.concepto,
                    "importe": float(t.importe),
                    "embedding": t.embedding,
                }
                for t in transacciones
            ],
            "status": "processing"
        }
    
    async def exact_match(self, state: ConciliacionState) -> dict:
        """Match exacto por importe y fecha."""
        self.log_step("exact_match", state, count=len(state["transacciones"]))
        
        matches = []
        matched_tx_ids = set()
        matched_asiento_ids = set()
        
        for tx in state["transacciones"]:
            if tx["id"] in matched_tx_ids:
                continue
                
            for asiento in state.get("asientos", []):
                if asiento["id"] in matched_asiento_ids:
                    continue
                
                # Match exacto: mismo importe
                if abs(tx["importe"] - asiento["importe"]) < 0.01:
                    # Fecha dentro de ±1 día
                    from datetime import date
                    tx_date = date.fromisoformat(tx["fecha"])
                    as_date = date.fromisoformat(asiento["fecha"])
                    
                    if abs((tx_date - as_date).days) <= 1:
                        matches.append({
                            "transaccion_id": tx["id"],
                            "asiento_id": asiento["id"],
                            "confianza": 0.98,
                            "metodo": "exact",
                            "razones": ["Importe exacto", "Fecha coincide"]
                        })
                        matched_tx_ids.add(tx["id"])
                        matched_asiento_ids.add(asiento["id"])
                        break
        
        return {
            **state,
            "matches_exactos": matches,
        }
    
    async def fuzzy_match(self, state: ConciliacionState) -> dict:
        """Match fuzzy usando embeddings."""
        self.log_step("fuzzy_match", state)
        
        # Obtener transacciones sin match exacto
        matched_ids = {m["transaccion_id"] for m in state["matches_exactos"]}
        pending_tx = [t for t in state["transacciones"] if t["id"] not in matched_ids]
        
        matches = []
        
        for tx in pending_tx:
            if not tx.get("embedding"):
                continue
            
            best_match = None
            best_score = 0
            
            for asiento in state.get("asientos", []):
                if asiento["id"] in {m["asiento_id"] for m in state["matches_exactos"]}:
                    continue
                
                if not asiento.get("embedding"):
                    continue
                
                # Calcular similitud
                similarity = await self.hf.compute_similarity(
                    tx["embedding"],
                    asiento["embedding"]
                )
                
                # Combinar con similitud de importe
                importe_diff = abs(tx["importe"] - asiento["importe"]) / max(abs(tx["importe"]), 1)
                importe_score = max(0, 1 - importe_diff)
                
                combined_score = (similarity * 0.6) + (importe_score * 0.4)
                
                if combined_score > best_score and combined_score > 0.7:
                    best_score = combined_score
                    best_match = asiento
            
            if best_match:
                matches.append({
                    "transaccion_id": tx["id"],
                    "asiento_id": best_match["id"],
                    "confianza": round(best_score, 2),
                    "metodo": "fuzzy",
                    "razones": [
                        f"Similitud semántica: {similarity:.0%}",
                        f"Similitud importe: {importe_score:.0%}"
                    ]
                })
        
        return {
            **state,
            "matches_fuzzy": matches,
        }
    
    async def prepare_review(self, state: ConciliacionState) -> dict:
        """Preparar propuestas para revisión humana."""
        self.log_step("prepare_review", state)
        
        # Combinar todos los matches
        all_matches = state["matches_exactos"] + state["matches_fuzzy"]
        
        # Separar por confianza
        auto_approved = []
        needs_review = []
        threshold = state.get("auto_approve_threshold", 0.95)
        
        for match in all_matches:
            if match["confianza"] >= threshold:
                auto_approved.append({**match, "estado": "auto_aprobado"})
            else:
                needs_review.append({**match, "estado": "pendiente_revision"})
        
        # Identificar discrepancias (sin match)
        matched_tx_ids = {m["transaccion_id"] for m in all_matches}
        discrepancias = [
            {"transaccion_id": tx["id"], "tipo": "sin_match"}
            for tx in state["transacciones"]
            if tx["id"] not in matched_tx_ids
        ]
        
        return {
            **state,
            "propuestas": auto_approved + needs_review,
            "discrepancias": discrepancias,
            "requires_human": len(needs_review) > 0,
            "status": "review" if needs_review else "processing"
        }
    
    async def apply_decisions(self, state: ConciliacionState) -> dict:
        """Aplicar decisiones del humano."""
        self.log_step("apply_decisions", state)
        
        feedback = state.get("human_feedback", {})
        aprobadas = set(feedback.get("aprobadas", []))
        rechazadas = set(feedback.get("rechazadas", []))
        
        # Actualizar propuestas según feedback
        for propuesta in state["propuestas"]:
            if propuesta["transaccion_id"] in aprobadas:
                propuesta["estado"] = "validado"
            elif propuesta["transaccion_id"] in rechazadas:
                propuesta["estado"] = "rechazado"
            elif propuesta["estado"] == "auto_aprobado":
                propuesta["estado"] = "validado"
        
        # Guardar conciliaciones en DB
        for propuesta in state["propuestas"]:
            if propuesta["estado"] == "validado":
                conciliacion = Conciliacion(
                    transaccion_id=propuesta["transaccion_id"],
                    asiento_id=propuesta.get("asiento_id"),
                    confianza=propuesta["confianza"],
                    estado="validado",
                    match_details={"metodo": propuesta["metodo"], "razones": propuesta["razones"]}
                )
                self.db.add(conciliacion)
        
        await self.db.commit()
        
        return {
            **state,
            "status": "completing"
        }
    
    async def generate_summary(self, state: ConciliacionState) -> dict:
        """Generar resumen de conciliación."""
        self.log_step("generate_summary", state)
        
        total = len(state["transacciones"])
        conciliadas = len([p for p in state["propuestas"] if p["estado"] == "validado"])
        pendientes = len(state["discrepancias"])
        
        return {
            **state,
            "status": "completed",
            "results": {
                "total_transacciones": total,
                "conciliadas": conciliadas,
                "pendientes": pendientes,
                "tasa_conciliacion": round(conciliadas / total * 100, 1) if total > 0 else 0,
                "propuestas": state["propuestas"],
                "discrepancias": state["discrepancias"]
            }
        }
```

#### 3.3 Agente de Clasificación (`backend/app/agents/clasificacion.py`)

```python
"""Agente de clasificación de gastos/ingresos."""
from typing import TypedDict
from langgraph.graph import StateGraph, END
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseAgent, AgentState
from app.models.transaccion import Transaccion
from app.models.clasificacion import Clasificacion, ReglaClasificacion

class ClasificacionState(AgentState):
    empresa_id: str
    transaccion_ids: list[str]
    transacciones: list[dict]
    reglas: list[dict]
    clasificaciones: list[dict]
    pendientes_revision: list[dict]
    review_threshold: float

class ClasificacionAgent(BaseAgent):
    """
    Agente de clasificación en cascada:
    1. Reglas explícitas -> 99% confianza
    2. Histórico -> 90% confianza
    3. ML -> 70-85% confianza
    4. LLM -> 60-80% confianza
    """
    
    def build_graph(self) -> StateGraph:
        graph = StateGraph(ClasificacionState)
        
        graph.add_node("load_data", self.load_data)
        graph.add_node("apply_rules", self.apply_rules)
        graph.add_node("check_history", self.check_history)
        graph.add_node("llm_classify", self.llm_classify)
        graph.add_node("prepare_review", self.prepare_review)
        graph.add_node("save_results", self.save_results)
        
        graph.add_edge("load_data", "apply_rules")
        graph.add_edge("apply_rules", "check_history")
        graph.add_edge("check_history", "llm_classify")
        graph.add_edge("llm_classify", "prepare_review")
        
        graph.add_conditional_edges(
            "prepare_review",
            lambda s: "pause" if s["requires_human"] and not s.get("human_feedback") else "continue",
            {"pause": END, "continue": "save_results"}
        )
        
        graph.add_edge("save_results", END)
        graph.set_entry_point("load_data")
        
        return graph
    
    async def load_data(self, state: ClasificacionState) -> dict:
        """Cargar transacciones y reglas."""
        self.log_step("load_data", state)
        
        # Cargar transacciones
        stmt = select(Transaccion).where(
            Transaccion.id.in_(state["transaccion_ids"])
        )
        result = await self.db.execute(stmt)
        transacciones = result.scalars().all()
        
        # Cargar reglas del tenant
        stmt_reglas = select(ReglaClasificacion).where(
            ReglaClasificacion.tenant_id == state["tenant_id"],
            ReglaClasificacion.activa == True
        ).order_by(ReglaClasificacion.prioridad.desc())
        
        result_reglas = await self.db.execute(stmt_reglas)
        reglas = result_reglas.scalars().all()
        
        return {
            **state,
            "transacciones": [
                {"id": str(t.id), "concepto": t.concepto, "importe": float(t.importe)}
                for t in transacciones
            ],
            "reglas": [
                {"id": str(r.id), "condicion": r.condicion, "categoria_pgc": r.categoria_pgc}
                for r in reglas
            ],
            "clasificaciones": [],
            "status": "processing"
        }
    
    async def apply_rules(self, state: ClasificacionState) -> dict:
        """Aplicar reglas configuradas."""
        self.log_step("apply_rules", state)
        
        clasificaciones = []
        clasificadas_ids = set()
        
        for tx in state["transacciones"]:
            for regla in state["reglas"]:
                if self._match_rule(tx, regla["condicion"]):
                    clasificaciones.append({
                        "transaccion_id": tx["id"],
                        "categoria_pgc": regla["categoria_pgc"],
                        "confianza": 0.99,
                        "metodo": "regla",
                        "explicacion": f"Regla: {regla['id']}"
                    })
                    clasificadas_ids.add(tx["id"])
                    break
        
        # Filtrar transacciones pendientes
        pendientes = [t for t in state["transacciones"] if t["id"] not in clasificadas_ids]
        
        return {
            **state,
            "clasificaciones": clasificaciones,
            "transacciones": pendientes  # Solo las pendientes
        }
    
    def _match_rule(self, tx: dict, condicion: dict) -> bool:
        """Evaluar si transacción cumple condición de regla."""
        campo = condicion.get("campo", "concepto")
        operador = condicion.get("operador", "contains")
        valor = condicion.get("valor", "").lower()
        
        tx_valor = str(tx.get(campo, "")).lower()
        
        if operador == "contains":
            return valor in tx_valor
        elif operador == "equals":
            return valor == tx_valor
        elif operador == "startswith":
            return tx_valor.startswith(valor)
        
        return False
    
    async def check_history(self, state: ClasificacionState) -> dict:
        """Buscar en histórico de clasificaciones similares."""
        self.log_step("check_history", state)
        
        clasificaciones = state["clasificaciones"].copy()
        clasificadas_ids = {c["transaccion_id"] for c in clasificaciones}
        pendientes = []
        
        for tx in state["transacciones"]:
            if tx["id"] in clasificadas_ids:
                continue
            
            # Buscar clasificaciones previas con concepto similar
            # (simplificado - en producción usar embeddings)
            stmt = select(Clasificacion).join(Transaccion).where(
                Transaccion.concepto.ilike(f"%{tx['concepto'][:20]}%"),
                Clasificacion.validado_por.isnot(None)  # Solo validadas por humano
            ).limit(5)
            
            result = await self.db.execute(stmt)
            historico = result.scalars().all()
            
            if historico:
                # Usar la clasificación más común
                categorias = [h.categoria_pgc for h in historico]
                categoria_comun = max(set(categorias), key=categorias.count)
                frecuencia = categorias.count(categoria_comun) / len(categorias)
                
                clasificaciones.append({
                    "transaccion_id": tx["id"],
                    "categoria_pgc": categoria_comun,
                    "confianza": round(0.85 * frecuencia, 2),
                    "metodo": "historico",
                    "explicacion": f"Basado en {len(historico)} clasificaciones similares"
                })
                clasificadas_ids.add(tx["id"])
            else:
                pendientes.append(tx)
        
        return {
            **state,
            "clasificaciones": clasificaciones,
            "transacciones": pendientes
        }
    
    async def llm_classify(self, state: ClasificacionState) -> dict:
        """Clasificar con LLM las transacciones restantes."""
        self.log_step("llm_classify", state, pending=len(state["transacciones"]))
        
        clasificaciones = state["clasificaciones"].copy()
        
        for tx in state["transacciones"]:
            result = await self.hf.classify_transaction(
                concepto=tx["concepto"],
                importe=tx["importe"]
            )
            
            clasificaciones.append({
                "transaccion_id": tx["id"],
                "categoria_pgc": result["categoria_pgc"],
                "confianza": result["confianza"],
                "metodo": "llm",
                "explicacion": result["explicacion"]
            })
        
        return {
            **state,
            "clasificaciones": clasificaciones,
            "transacciones": []
        }
    
    async def prepare_review(self, state: ClasificacionState) -> dict:
        """Preparar clasificaciones para revisión."""
        self.log_step("prepare_review", state)
        
        threshold = state.get("review_threshold", 0.75)
        
        pendientes = [
            c for c in state["clasificaciones"]
            if c["confianza"] < threshold
        ]
        
        return {
            **state,
            "pendientes_revision": pendientes,
            "requires_human": len(pendientes) > 0,
            "status": "review" if pendientes else "completing"
        }
    
    async def save_results(self, state: ClasificacionState) -> dict:
        """Guardar clasificaciones en DB."""
        self.log_step("save_results", state)
        
        feedback = state.get("human_feedback", {})
        correcciones = feedback.get("correcciones", {})
        
        for clasif in state["clasificaciones"]:
            # Aplicar correcciones si existen
            if clasif["transaccion_id"] in correcciones:
                clasif["categoria_pgc"] = correcciones[clasif["transaccion_id"]]
                clasif["metodo"] = "manual"
                clasif["confianza"] = 1.0
            
            clasificacion = Clasificacion(
                transaccion_id=clasif["transaccion_id"],
                categoria_pgc=clasif["categoria_pgc"],
                confianza=clasif["confianza"],
                metodo=clasif["metodo"],
                explicacion=clasif.get("explicacion")
            )
            self.db.add(clasificacion)
        
        await self.db.commit()
        
        return {
            **state,
            "status": "completed",
            "results": {
                "total": len(state["clasificaciones"]),
                "clasificaciones": state["clasificaciones"]
            }
        }
```

#### 3.4 Agente de Tesorería (`backend/app/agents/tesoreria.py`)

```python
"""Agente de análisis de tesorería y cash flow."""
from typing import TypedDict
from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict

from langgraph.graph import StateGraph, END
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseAgent, AgentState
from app.models.transaccion import Transaccion
from app.models.empresa import CuentaBancaria

class TesoreriaState(AgentState):
    empresa_id: str
    periodo_dias: int
    transacciones: list[dict]
    metricas: dict
    patrones: dict
    proyeccion: dict
    alertas: list[str]
    recomendaciones: list[str]

class TesoreriaAgent(BaseAgent):
    """
    Agente de análisis financiero (sin human-in-the-loop).
    """
    
    def build_graph(self) -> StateGraph:
        graph = StateGraph(TesoreriaState)
        
        graph.add_node("load_data", self.load_data)
        graph.add_node("calculate_metrics", self.calculate_metrics)
        graph.add_node("analyze_patterns", self.analyze_patterns)
        graph.add_node("project_cashflow", self.project_cashflow)
        graph.add_node("generate_alerts", self.generate_alerts)
        graph.add_node("compile_report", self.compile_report)
        
        graph.add_edge("load_data", "calculate_metrics")
        graph.add_edge("calculate_metrics", "analyze_patterns")
        graph.add_edge("analyze_patterns", "project_cashflow")
        graph.add_edge("project_cashflow", "generate_alerts")
        graph.add_edge("generate_alerts", "compile_report")
        graph.add_edge("compile_report", END)
        
        graph.set_entry_point("load_data")
        
        return graph
    
    async def load_data(self, state: TesoreriaState) -> dict:
        """Cargar transacciones del periodo."""
        self.log_step("load_data", state)
        
        fecha_inicio = date.today() - timedelta(days=state.get("periodo_dias", 90))
        
        stmt = select(Transaccion).join(CuentaBancaria).where(
            CuentaBancaria.empresa_id == state["empresa_id"],
            Transaccion.fecha >= fecha_inicio
        ).order_by(Transaccion.fecha)
        
        result = await self.db.execute(stmt)
        transacciones = result.scalars().all()
        
        return {
            **state,
            "transacciones": [
                {
                    "id": str(t.id),
                    "fecha": t.fecha.isoformat(),
                    "importe": float(t.importe),
                    "tipo": t.tipo,
                    "concepto": t.concepto,
                    "cuenta_id": str(t.cuenta_id)
                }
                for t in transacciones
            ],
            "status": "processing"
        }
    
    async def calculate_metrics(self, state: TesoreriaState) -> dict:
        """Calcular métricas financieras."""
        self.log_step("calculate_metrics", state)
        
        transacciones = state["transacciones"]
        
        # Calcular por tipo
        ingresos = sum(t["importe"] for t in transacciones if t["importe"] > 0)
        gastos = abs(sum(t["importe"] for t in transacciones if t["importe"] < 0))
        
        # Saldo por cuenta
        saldos = defaultdict(float)
        for t in transacciones:
            saldos[t["cuenta_id"]] += t["importe"]
        
        # Calcular saldo actual (suma de todos los movimientos)
        saldo_total = sum(saldos.values())
        
        # Burn rate (gastos mensuales promedio)
        dias = state.get("periodo_dias", 90)
        meses = dias / 30
        burn_rate = gastos / meses if meses > 0 else 0
        
        # Runway (meses de vida con saldo actual)
        runway = saldo_total / burn_rate if burn_rate > 0 else float('inf')
        
        metricas = {
            "saldo_total": round(saldo_total, 2),
            "saldos_por_cuenta": dict(saldos),
            "ingresos_periodo": round(ingresos, 2),
            "gastos_periodo": round(gastos, 2),
            "resultado_periodo": round(ingresos - gastos, 2),
            "burn_rate_mensual": round(burn_rate, 2),
            "runway_meses": round(runway, 1) if runway != float('inf') else None,
            "ratio_ingresos_gastos": round(ingresos / gastos, 2) if gastos > 0 else None
        }
        
        return {**state, "metricas": metricas}
    
    async def analyze_patterns(self, state: TesoreriaState) -> dict:
        """Detectar patrones en transacciones."""
        self.log_step("analyze_patterns", state)
        
        transacciones = state["transacciones"]
        
        # Agrupar por mes
        por_mes = defaultdict(lambda: {"ingresos": 0, "gastos": 0})
        for t in transacciones:
            mes = t["fecha"][:7]  # YYYY-MM
            if t["importe"] > 0:
                por_mes[mes]["ingresos"] += t["importe"]
            else:
                por_mes[mes]["gastos"] += abs(t["importe"])
        
        # Detectar gastos recurrentes (mismo importe ±5%, mismo día ±3)
        gastos = [t for t in transacciones if t["importe"] < 0]
        recurrentes = []
        
        importes_vistos = defaultdict(list)
        for g in gastos:
            importe_key = round(abs(g["importe"]), -1)  # Redondear a decenas
            importes_vistos[importe_key].append(g)
        
        for importe, lista in importes_vistos.items():
            if len(lista) >= 2:
                recurrentes.append({
                    "importe_aprox": importe,
                    "frecuencia": len(lista),
                    "concepto_ejemplo": lista[0]["concepto"][:50]
                })
        
        patrones = {
            "evolucion_mensual": dict(por_mes),
            "gastos_recurrentes": recurrentes[:10],
            "dias_con_mas_movimientos": self._get_peak_days(transacciones)
        }
        
        return {**state, "patrones": patrones}
    
    def _get_peak_days(self, transacciones: list) -> list:
        """Obtener días del mes con más movimientos."""
        from collections import Counter
        dias = Counter(int(t["fecha"].split("-")[2]) for t in transacciones)
        return [{"dia": d, "movimientos": c} for d, c in dias.most_common(5)]
    
    async def project_cashflow(self, state: TesoreriaState) -> dict:
        """Proyectar cash flow a futuro."""
        self.log_step("project_cashflow", state)
        
        saldo_actual = state["metricas"]["saldo_total"]
        burn_rate_diario = state["metricas"]["burn_rate_mensual"] / 30
        
        # Proyección simple: saldo - burn_rate * días
        proyeccion = {
            "30d": {
                "optimista": round(saldo_actual - (burn_rate_diario * 0.8 * 30), 2),
                "base": round(saldo_actual - (burn_rate_diario * 30), 2),
                "pesimista": round(saldo_actual - (burn_rate_diario * 1.2 * 30), 2)
            },
            "60d": {
                "optimista": round(saldo_actual - (burn_rate_diario * 0.8 * 60), 2),
                "base": round(saldo_actual - (burn_rate_diario * 60), 2),
                "pesimista": round(saldo_actual - (burn_rate_diario * 1.2 * 60), 2)
            },
            "90d": {
                "optimista": round(saldo_actual - (burn_rate_diario * 0.8 * 90), 2),
                "base": round(saldo_actual - (burn_rate_diario * 90), 2),
                "pesimista": round(saldo_actual - (burn_rate_diario * 1.2 * 90), 2)
            }
        }
        
        return {**state, "proyeccion": proyeccion}
    
    async def generate_alerts(self, state: TesoreriaState) -> dict:
        """Generar alertas basadas en análisis."""
        self.log_step("generate_alerts", state)
        
        alertas = []
        recomendaciones = []
        metricas = state["metricas"]
        proyeccion = state["proyeccion"]
        
        # Alerta: saldo bajo
        if metricas["saldo_total"] < metricas["burn_rate_mensual"]:
            alertas.append("⚠️ CRÍTICO: Saldo actual menor a un mes de gastos")
            recomendaciones.append("Revisar opciones de financiación urgente")
        
        # Alerta: runway corto
        if metricas["runway_meses"] and metricas["runway_meses"] < 3:
            alertas.append(f"⚠️ Runway de solo {metricas['runway_meses']} meses")
            recomendaciones.append("Acelerar cobros pendientes")
        
        # Alerta: ratio malo
        if metricas["ratio_ingresos_gastos"] and metricas["ratio_ingresos_gastos"] < 1:
            alertas.append("📉 Gastos superiores a ingresos en el periodo")
            recomendaciones.append("Revisar estructura de costes")
        
        # Alerta: proyección negativa
        if proyeccion["60d"]["base"] < 0:
            alertas.append("🔴 Proyección de saldo negativo en 60 días")
            recomendaciones.append("Negociar plazos de pago con proveedores")
        
        return {
            **state,
            "alertas": alertas,
            "recomendaciones": recomendaciones
        }
    
    async def compile_report(self, state: TesoreriaState) -> dict:
        """Compilar informe final."""
        self.log_step("compile_report", state)
        
        return {
            **state,
            "status": "completed",
            "requires_human": False,
            "results": {
                "metricas": state["metricas"],
                "patrones": state["patrones"],
                "proyeccion": state["proyeccion"],
                "alertas": state["alertas"],
                "recomendaciones": state["recomendaciones"]
            }
        }
```

---

### FASE 4: API Endpoints (Semana 5)

Ver ARCHITECT.md sección 5 para especificaciones OpenAPI completas.

Implementar los siguientes routers en `backend/app/api/v1/`:

- `extractos.py` - Upload y procesamiento de extractos
- `conciliacion.py` - Flujo de conciliación con human-in-the-loop
- `clasificacion.py` - Clasificación batch y correcciones
- `tesoreria.py` - Dashboard y análisis
- `informes.py` - Generación de PDFs

---

### FASE 5-7: Tasks, Frontend, Testing

Ver secciones correspondientes en ARCHITECT.md.

---

## ✅ CRITERIOS DE ACEPTACIÓN

- [ ] `docker-compose up` levanta todo el stack
- [ ] Migraciones ejecutan sin errores
- [ ] Health check de API responde 200
- [ ] Parser CSV detecta columnas automáticamente
- [ ] Agente conciliación pausa en checkpoint
- [ ] Precisión de matching > 80% en datos de test
- [ ] Cobertura de tests > 80%

---

## 🚫 ANTI-PATRONES A EVITAR

1. **No hardcodear tenant_id** - Siempre obtener del JWT
2. **No llamar a LLM sin caché** - Usar Redis para embeddings
3. **No bloquear event loop** - Usar async para I/O
4. **No confiar ciegamente en LLM** - Siempre parsear y validar
5. **No exponer stack traces** - Errores genéricos al cliente

---

## 🎯 PROMPT PARA CONTINUAR

```
Continúo implementando Agente Financiero IA.

Ya implementé: [lista]
Siguiente: [fase/componente]

Genera el código completo siguiendo PRD.md, ARCHITECT.md y PROMPT.md.
```
