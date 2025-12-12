# ARCHITECT.md: Agente Financiero IA

> **Versión:** 1.0  
> **Fecha:** Diciembre 2024  
> **Estado:** Draft  
> **Autor:** GLEMES FFT

---

## 1. Visión General de Arquitectura

### 1.1 Principios Arquitectónicos

| Principio | Descripción | Implicación |
|-----------|-------------|-------------|
| **Multi-agente especializado** | Cada agente tiene una responsabilidad única | Escalabilidad horizontal, mantenibilidad |
| **Human-in-the-loop** | Toda decisión crítica requiere validación humana | UX de revisión, estados intermedios |
| **Auditable** | Cada acción del sistema es trazable | Logging exhaustivo, explicabilidad |
| **Multi-tenant** | Aislamiento completo de datos entre clientes | Row-level security, tenant_id en todo |
| **Event-driven** | Comunicación asíncrona entre componentes | Colas de mensajes, resiliencia |

### 1.2 Diagrama de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTE (Browser)                               │
│                         React + TailwindCSS + Recharts                       │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ HTTPS
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY                                     │
│                    FastAPI + JWT Auth + Rate Limiting                        │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
│    FILE PROCESSOR     │ │   AGENT ORCHESTRATOR  │ │    REPORT GENERATOR   │
│  (Upload, Parse, OCR) │ │   (LangGraph/Custom)  │ │    (PDF, Dashboard)   │
└───────────┬───────────┘ └───────────┬───────────┘ └───────────┬───────────┘
            │                         │                         │
            │              ┌──────────┼──────────┐              │
            │              ▼          ▼          ▼              │
            │      ┌───────────┐ ┌─────────┐ ┌─────────┐        │
            │      │  AGENTE   │ │ AGENTE  │ │ AGENTE  │        │
            │      │CONCILIACIÓN│ │CLASIFIC.│ │TESORERÍA│        │
            │      └─────┬─────┘ └────┬────┘ └────┬────┘        │
            │            │            │           │             │
            └────────────┴────────────┴───────────┴─────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
│      PostgreSQL       │ │     Redis (Cache)     │ │    S3 (Documents)     │
│   (Data + Vectors)    │ │    + Task Queue       │ │    + Reports          │
└───────────────────────┘ └───────────────────────┘ └───────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │    HUGGING FACE INFERENCE API   │
                    │   (LLM + Embeddings + Vision)   │
                    └─────────────────────────────────┘
```

---

## 2. Stack Tecnológico

### 2.1 Backend

| Componente | Tecnología | Justificación |
|------------|------------|---------------|
| **Framework API** | FastAPI | Async nativo, OpenAPI auto, tipado fuerte |
| **Orquestación Agentes** | LangGraph | Grafos de estado, checkpoints, human-in-loop nativo |
| **Task Queue** | Celery + Redis | Procesamiento batch, retry automático |
| **ORM** | SQLAlchemy 2.0 | Async support, type hints, migrations con Alembic |
| **Validación** | Pydantic v2 | Schemas estrictos, serialización eficiente |

### 2.2 IA/ML

| Componente | Tecnología | Modelo Sugerido |
|------------|------------|-----------------|
| **LLM Principal** | HuggingFace Inference | `mistralai/Mixtral-8x7B-Instruct-v0.1` |
| **LLM Rápido** | HuggingFace Inference | `mistralai/Mistral-7B-Instruct-v0.2` |
| **Embeddings** | HuggingFace Inference | `BAAI/bge-m3` (multilingüe) |
| **OCR/Vision** | HuggingFace Inference | `microsoft/trocr-large-printed` |
| **Clasificación** | Fine-tuned local | `distilbert-base-multilingual` |

### 2.3 Frontend

| Componente | Tecnología | Justificación |
|------------|------------|---------------|
| **Framework** | React 18 + TypeScript | Ecosistema maduro, tipado |
| **Styling** | TailwindCSS | Utility-first, consistencia |
| **State** | Zustand | Simple, sin boilerplate |
| **Data Fetching** | TanStack Query | Cache, invalidation, optimistic updates |
| **Charts** | Recharts | Declarativo, responsive |
| **Tables** | TanStack Table | Sorting, filtering, virtualización |

### 2.4 Infraestructura

| Componente | Tecnología | Justificación |
|------------|------------|---------------|
| **Base de Datos** | PostgreSQL 16 + pgvector | Vector search nativo, RLS |
| **Cache** | Redis 7 | Session, rate limit, task queue |
| **Storage** | MinIO / S3 | Documentos, reportes generados |
| **Contenedores** | Docker + Docker Compose | Dev parity, despliegue consistente |
| **CI/CD** | GitHub Actions | Integración con repo |

---

## 3. Arquitectura de Agentes

### 3.1 Patrón de Diseño: Agente Especializado

Cada agente sigue el patrón:

```
┌─────────────────────────────────────────────────────┐
│                    AGENTE X                          │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   PARSER    │  │   REASONER  │  │   FORMATTER │  │
│  │  (Input)    │──│    (LLM)    │──│  (Output)   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│         │                │                │         │
│         ▼                ▼                ▼         │
│  ┌─────────────────────────────────────────────┐   │
│  │              STATE MANAGER                   │   │
│  │   (Checkpoint, Memory, Tool Results)         │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 3.2 Agente de Conciliación Bancaria

**Responsabilidad:** Proponer matches entre transacciones bancarias y asientos contables.

```python
# Pseudocódigo del flujo
class ConciliacionAgent:
    """
    Estados:
    - LOADING: Cargando datos
    - MATCHING: Ejecutando algoritmos de match
    - REVIEW: Esperando validación humana
    - COMPLETED: Conciliación finalizada
    """
    
    tools = [
        ExactMatchTool,      # Match por importe + fecha exacta
        FuzzyMatchTool,      # Match por similitud de concepto
        PatternMatchTool,    # Match por patrones aprendidos
        AnomalyDetectorTool, # Detección de discrepancias
    ]
    
    def run(self, bank_transactions, accounting_entries):
        # Paso 1: Match exacto (alta confianza)
        exact_matches = self.exact_match(transactions, entries)
        
        # Paso 2: Match fuzzy para pendientes
        remaining = self.get_unmatched(transactions, exact_matches)
        fuzzy_matches = self.fuzzy_match(remaining, entries)
        
        # Paso 3: Proponer para revisión humana
        proposals = self.prepare_proposals(exact_matches, fuzzy_matches)
        
        # Paso 4: HUMAN-IN-THE-LOOP checkpoint
        return AgentState(
            status="REVIEW",
            proposals=proposals,
            requires_human=True
        )
```

**Algoritmo de Matching:**

```
┌─────────────────────────────────────────────────────────────┐
│                    MATCHING PIPELINE                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. EXACT MATCH (Confianza: 95-100%)                        │
│     ├─ Importe exacto                                        │
│     ├─ Fecha exacta o ±1 día                                 │
│     └─ Output: matches automáticos                           │
│                                                              │
│  2. FUZZY MATCH (Confianza: 70-94%)                         │
│     ├─ Importe exacto                                        │
│     ├─ Fecha ±3 días                                         │
│     ├─ Similitud concepto > 0.7 (embeddings)                 │
│     └─ Output: propuestas para revisión                      │
│                                                              │
│  3. PATTERN MATCH (Confianza: 50-69%)                       │
│     ├─ Histórico de matches previos del cliente              │
│     ├─ Reglas aprendidas (proveedor → cuenta)                │
│     └─ Output: sugerencias con explicación                   │
│                                                              │
│  4. ANOMALY DETECTION                                        │
│     ├─ Transacciones sin match candidato                     │
│     ├─ Posibles duplicados                                   │
│     └─ Output: alertas para investigación                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Agente de Clasificación de Gastos

**Responsabilidad:** Categorizar transacciones según PGC y reglas del cliente.

```python
class ClasificacionAgent:
    """
    Estrategia de clasificación en cascada:
    1. Reglas explícitas del cliente (prioridad máxima)
    2. Histórico del mismo proveedor/concepto
    3. Modelo ML de clasificación
    4. LLM para casos ambiguos
    """
    
    tools = [
        RuleEngineTool,       # Reglas configuradas por usuario
        HistoryLookupTool,    # Buscar clasificaciones previas
        MLClassifierTool,     # Modelo entrenado
        LLMClassifierTool,    # Fallback inteligente
    ]
    
    classification_hierarchy = {
        "RULE": {"confidence": 0.99, "requires_review": False},
        "HISTORY": {"confidence": 0.90, "requires_review": False},
        "ML_HIGH": {"confidence": 0.85, "requires_review": False},
        "ML_MEDIUM": {"confidence": 0.70, "requires_review": True},
        "LLM": {"confidence": 0.60, "requires_review": True},
    }
```

**Taxonomía de Clasificación (simplificada PGC):**

```yaml
categorias_gasto:
  - codigo: "600"
    nombre: "Compras de mercaderías"
    subcategorias:
      - "6000": "Compras de mercaderías A"
      - "6001": "Compras de mercaderías B"
  
  - codigo: "621"
    nombre: "Arrendamientos y cánones"
    keywords: ["alquiler", "renting", "leasing"]
  
  - codigo: "622"
    nombre: "Reparaciones y conservación"
    keywords: ["mantenimiento", "reparación", "servicio técnico"]
  
  - codigo: "623"
    nombre: "Servicios profesionales"
    keywords: ["asesoría", "consultoría", "honorarios", "abogado"]
  
  - codigo: "624"
    nombre: "Transportes"
    keywords: ["envío", "mensajería", "logística", "flete"]
  
  - codigo: "625"
    nombre: "Primas de seguros"
    keywords: ["seguro", "póliza", "prima"]
  
  - codigo: "626"
    nombre: "Servicios bancarios"
    keywords: ["comisión", "transferencia", "mantenimiento cuenta"]
  
  - codigo: "627"
    nombre: "Publicidad y propaganda"
    keywords: ["marketing", "ads", "google", "meta", "publicidad"]
  
  - codigo: "628"
    nombre: "Suministros"
    keywords: ["luz", "agua", "gas", "electricidad", "teléfono"]
  
  - codigo: "629"
    nombre: "Otros servicios"
    keywords: []  # Catch-all
```

### 3.4 Agente de Tesorería

**Responsabilidad:** Analizar posición de caja, proyectar cash flow, detectar patrones.

```python
class TesoreriaAgent:
    """
    Análisis financiero basado en datos de transacciones
    y clasificaciones previas.
    """
    
    tools = [
        CashPositionTool,      # Saldo actual por cuenta
        TrendAnalysisTool,     # Evolución temporal
        ProjectionTool,        # Forecast basado en patrones
        AnomalyAlertTool,      # Detección de anomalías
        ReportGeneratorTool,   # Generación de informes
    ]
    
    def analyze(self, tenant_id, period):
        # Obtener datos consolidados
        transactions = self.get_classified_transactions(tenant_id, period)
        
        # Calcular métricas
        metrics = {
            "saldo_actual": self.calculate_balance(transactions),
            "ingresos_periodo": self.sum_by_type(transactions, "ingreso"),
            "gastos_periodo": self.sum_by_type(transactions, "gasto"),
            "burn_rate": self.calculate_burn_rate(transactions),
            "runway_days": self.estimate_runway(transactions),
        }
        
        # Análisis de patrones
        patterns = {
            "gastos_recurrentes": self.identify_recurring(transactions),
            "estacionalidad": self.detect_seasonality(transactions),
            "anomalias": self.detect_anomalies(transactions),
        }
        
        # Proyección
        projection = self.project_cashflow(
            transactions, 
            horizon_days=90,
            scenarios=["optimista", "base", "pesimista"]
        )
        
        return TesoreriaAnalysis(metrics, patterns, projection)
```

---

## 4. Modelo de Datos

### 4.1 Diagrama Entidad-Relación

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     TENANT      │     │      USER       │     │    EMPRESA      │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │────<│ id (PK)         │     │ id (PK)         │
│ nombre          │     │ tenant_id (FK)  │     │ tenant_id (FK)  │
│ config (JSONB)  │     │ email           │     │ nombre          │
│ created_at      │     │ rol             │     │ cif             │
└─────────────────┘     └─────────────────┘     │ sector          │
                                                 └────────┬────────┘
                                                          │
        ┌─────────────────────────────────────────────────┼─────────────────────────────────────────────────┐
        │                                                 │                                                 │
        ▼                                                 ▼                                                 ▼
┌─────────────────┐                             ┌─────────────────┐                             ┌─────────────────┐
│ CUENTA_BANCARIA │                             │  TRANSACCION    │                             │ CLASIFICACION   │
├─────────────────┤                             ├─────────────────┤                             ├─────────────────┤
│ id (PK)         │                             │ id (PK)         │                             │ id (PK)         │
│ empresa_id (FK) │                             │ cuenta_id (FK)  │                             │ transaccion_id  │
│ banco           │                             │ fecha           │                             │ categoria_pgc   │
│ iban            │                             │ importe         │                             │ confianza       │
│ alias           │                             │ concepto        │                             │ metodo          │
└─────────────────┘                             │ tipo            │                             │ validado_por    │
                                                │ hash (unique)   │                             │ validado_at     │
                                                └────────┬────────┘                             └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  CONCILIACION   │
                                                ├─────────────────┤
                                                │ id (PK)         │
                                                │ transaccion_id  │
                                                │ asiento_id      │
                                                │ confianza       │
                                                │ estado          │
                                                │ validado_por    │
                                                └─────────────────┘
```

### 4.2 Schemas Principales (Pydantic)

```python
from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

class TipoTransaccion(str, Enum):
    INGRESO = "ingreso"
    GASTO = "gasto"
    TRANSFERENCIA = "transferencia"

class EstadoConciliacion(str, Enum):
    PENDIENTE = "pendiente"
    PROPUESTO = "propuesto"
    VALIDADO = "validado"
    RECHAZADO = "rechazado"
    MANUAL = "manual"

class MetodoClasificacion(str, Enum):
    REGLA = "regla"
    HISTORICO = "historico"
    ML = "ml"
    LLM = "llm"
    MANUAL = "manual"

# === Schemas de Entrada ===

class TransaccionCreate(BaseModel):
    cuenta_id: UUID
    fecha: date
    fecha_valor: Optional[date] = None
    importe: Decimal = Field(..., decimal_places=2)
    concepto: str = Field(..., max_length=500)
    tipo: TipoTransaccion
    referencia: Optional[str] = None
    metadata: Optional[dict] = None

class ExtractoBancarioUpload(BaseModel):
    cuenta_id: UUID
    formato: str = Field(..., pattern="^(csv|ofx|pdf)$")
    archivo_url: str
    periodo_inicio: date
    periodo_fin: date

# === Schemas de Respuesta ===

class TransaccionResponse(BaseModel):
    id: UUID
    cuenta_id: UUID
    fecha: date
    importe: Decimal
    concepto: str
    tipo: TipoTransaccion
    clasificacion: Optional["ClasificacionResponse"] = None
    conciliacion: Optional["ConciliacionResponse"] = None
    created_at: datetime

class ClasificacionResponse(BaseModel):
    id: UUID
    categoria_pgc: str
    categoria_nombre: str
    confianza: float = Field(..., ge=0, le=1)
    metodo: MetodoClasificacion
    validado: bool
    explicacion: Optional[str] = None

class ConciliacionResponse(BaseModel):
    id: UUID
    transaccion_id: UUID
    asiento_id: Optional[UUID]
    confianza: float = Field(..., ge=0, le=1)
    estado: EstadoConciliacion
    match_details: Optional[dict] = None

class PropuestaConciliacion(BaseModel):
    """Propuesta de match para revisión humana"""
    transaccion: TransaccionResponse
    candidatos: list["CandidatoMatch"]
    mejor_match: Optional["CandidatoMatch"]
    requiere_revision: bool

class CandidatoMatch(BaseModel):
    asiento_id: UUID
    confianza: float
    razones: list[str]
    diferencia_importe: Optional[Decimal] = None
    diferencia_dias: Optional[int] = None

# === Schemas de Análisis ===

class TesoreriaSnapshot(BaseModel):
    fecha: date
    saldo_total: Decimal
    saldos_por_cuenta: dict[UUID, Decimal]
    ingresos_mes: Decimal
    gastos_mes: Decimal
    variacion_mes: Decimal
    variacion_porcentaje: float

class CashFlowProjection(BaseModel):
    periodo: str  # "30d", "60d", "90d"
    escenario: str  # "optimista", "base", "pesimista"
    proyeccion_diaria: list[dict]  # [{fecha, saldo_proyectado}]
    dias_runway: Optional[int]
    alertas: list[str]

class InformeEjecutivo(BaseModel):
    empresa_id: UUID
    periodo: str
    generado_at: datetime
    resumen: dict
    metricas_clave: dict
    graficos_data: dict
    alertas: list[str]
    recomendaciones: list[str]
    pdf_url: Optional[str] = None
```

### 4.3 Migraciones SQL (Alembic)

```sql
-- Migración inicial: Estructura base multi-tenant

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Tabla de tenants (gestorías)
CREATE TABLE tenant (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    config JSONB DEFAULT '{}',
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de usuarios
CREATE TABLE usuario (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenant(id),
    email VARCHAR(255) NOT NULL,
    nombre VARCHAR(255),
    rol VARCHAR(50) NOT NULL DEFAULT 'usuario',
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, email)
);

-- Tabla de empresas (clientes de la gestoría)
CREATE TABLE empresa (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenant(id),
    nombre VARCHAR(255) NOT NULL,
    cif VARCHAR(20),
    sector VARCHAR(100),
    config JSONB DEFAULT '{}',
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de cuentas bancarias
CREATE TABLE cuenta_bancaria (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    banco VARCHAR(100),
    iban VARCHAR(34),
    alias VARCHAR(100),
    activa BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(empresa_id, iban)
);

-- Tabla de transacciones
CREATE TABLE transaccion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cuenta_id UUID NOT NULL REFERENCES cuenta_bancaria(id),
    fecha DATE NOT NULL,
    fecha_valor DATE,
    importe DECIMAL(15,2) NOT NULL,
    concepto TEXT,
    tipo VARCHAR(20) NOT NULL,
    referencia VARCHAR(100),
    hash VARCHAR(64) NOT NULL,  -- Para detectar duplicados
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1024),  -- Para búsqueda semántica
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(cuenta_id, hash)
);

-- Tabla de clasificaciones
CREATE TABLE clasificacion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaccion_id UUID NOT NULL REFERENCES transaccion(id),
    categoria_pgc VARCHAR(10) NOT NULL,
    confianza DECIMAL(3,2) NOT NULL,
    metodo VARCHAR(20) NOT NULL,
    explicacion TEXT,
    validado_por UUID REFERENCES usuario(id),
    validado_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de conciliaciones
CREATE TABLE conciliacion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaccion_id UUID NOT NULL REFERENCES transaccion(id),
    asiento_id UUID,  -- Referencia externa al ERP
    confianza DECIMAL(3,2) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    match_details JSONB,
    validado_por UUID REFERENCES usuario(id),
    validado_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de reglas de clasificación
CREATE TABLE regla_clasificacion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenant(id),
    empresa_id UUID REFERENCES empresa(id),  -- NULL = aplica a todo el tenant
    nombre VARCHAR(100) NOT NULL,
    condicion JSONB NOT NULL,  -- {"campo": "concepto", "operador": "contains", "valor": "AMAZON"}
    categoria_pgc VARCHAR(10) NOT NULL,
    prioridad INTEGER DEFAULT 0,
    activa BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_transaccion_cuenta_fecha ON transaccion(cuenta_id, fecha);
CREATE INDEX idx_transaccion_embedding ON transaccion USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_clasificacion_transaccion ON clasificacion(transaccion_id);
CREATE INDEX idx_conciliacion_transaccion ON conciliacion(transaccion_id);
CREATE INDEX idx_empresa_tenant ON empresa(tenant_id);

-- Row Level Security para multi-tenant
ALTER TABLE empresa ENABLE ROW LEVEL SECURITY;
ALTER TABLE cuenta_bancaria ENABLE ROW LEVEL SECURITY;
ALTER TABLE transaccion ENABLE ROW LEVEL SECURITY;
ALTER TABLE clasificacion ENABLE ROW LEVEL SECURITY;
ALTER TABLE conciliacion ENABLE ROW LEVEL SECURITY;

-- Políticas RLS (ejemplo para empresa)
CREATE POLICY tenant_isolation_empresa ON empresa
    USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

---

## 5. APIs y Contratos

### 5.1 API REST Principal

```yaml
openapi: 3.0.3
info:
  title: Agente Financiero IA API
  version: 1.0.0

paths:
  # === Extractos Bancarios ===
  /api/v1/extractos/upload:
    post:
      summary: Subir extracto bancario
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                cuenta_id:
                  type: string
                  format: uuid
                archivo:
                  type: string
                  format: binary
                formato:
                  type: string
                  enum: [csv, ofx, pdf]
      responses:
        '202':
          description: Procesamiento iniciado
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskResponse'

  /api/v1/extractos/{task_id}/status:
    get:
      summary: Estado del procesamiento
      responses:
        '200':
          description: Estado actual
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskStatus'

  # === Conciliación ===
  /api/v1/conciliacion/iniciar:
    post:
      summary: Iniciar proceso de conciliación
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                empresa_id:
                  type: string
                  format: uuid
                periodo_inicio:
                  type: string
                  format: date
                periodo_fin:
                  type: string
                  format: date
      responses:
        '202':
          description: Conciliación iniciada

  /api/v1/conciliacion/{session_id}/propuestas:
    get:
      summary: Obtener propuestas de match
      responses:
        '200':
          description: Lista de propuestas
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/PropuestaConciliacion'

  /api/v1/conciliacion/{session_id}/validar:
    post:
      summary: Validar propuestas (human-in-the-loop)
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                aprobadas:
                  type: array
                  items:
                    type: string
                    format: uuid
                rechazadas:
                  type: array
                  items:
                    type: string
                    format: uuid
      responses:
        '200':
          description: Validación procesada

  # === Clasificación ===
  /api/v1/clasificacion/batch:
    post:
      summary: Clasificar transacciones en batch
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                transaccion_ids:
                  type: array
                  items:
                    type: string
                    format: uuid
      responses:
        '202':
          description: Clasificación iniciada

  /api/v1/clasificacion/{transaccion_id}:
    put:
      summary: Corregir clasificación manualmente
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                categoria_pgc:
                  type: string
                crear_regla:
                  type: boolean
                  default: false
      responses:
        '200':
          description: Clasificación actualizada

  # === Tesorería ===
  /api/v1/tesoreria/{empresa_id}/snapshot:
    get:
      summary: Posición de tesorería actual
      responses:
        '200':
          description: Snapshot de tesorería
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TesoreriaSnapshot'

  /api/v1/tesoreria/{empresa_id}/proyeccion:
    get:
      summary: Proyección de cash flow
      parameters:
        - name: horizonte
          in: query
          schema:
            type: string
            enum: [30d, 60d, 90d]
      responses:
        '200':
          description: Proyección de cash flow
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CashFlowProjection'

  # === Informes ===
  /api/v1/informes/ejecutivo:
    post:
      summary: Generar informe ejecutivo
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                empresa_id:
                  type: string
                  format: uuid
                periodo:
                  type: string
                  enum: [mensual, trimestral]
                formato:
                  type: string
                  enum: [pdf, dashboard]
      responses:
        '202':
          description: Generación iniciada
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskResponse'

components:
  schemas:
    TaskResponse:
      type: object
      properties:
        task_id:
          type: string
          format: uuid
        status:
          type: string
          enum: [pending, processing, completed, failed]
        created_at:
          type: string
          format: date-time

    TaskStatus:
      type: object
      properties:
        task_id:
          type: string
          format: uuid
        status:
          type: string
        progress:
          type: integer
          minimum: 0
          maximum: 100
        result:
          type: object
        error:
          type: string
```

### 5.2 WebSocket para Updates en Tiempo Real

```python
# Eventos WebSocket
WEBSOCKET_EVENTS = {
    # Procesamiento de extractos
    "extracto.processing": "Procesando extracto bancario",
    "extracto.completed": "Extracto procesado",
    "extracto.error": "Error en procesamiento",
    
    # Conciliación
    "conciliacion.started": "Conciliación iniciada",
    "conciliacion.proposals_ready": "Propuestas listas para revisión",
    "conciliacion.completed": "Conciliación completada",
    
    # Clasificación
    "clasificacion.batch_progress": "Progreso de clasificación",
    "clasificacion.completed": "Clasificación completada",
    "clasificacion.review_needed": "Requiere revisión manual",
    
    # Informes
    "informe.generating": "Generando informe",
    "informe.ready": "Informe disponible",
}

# Formato de mensaje
{
    "event": "conciliacion.proposals_ready",
    "data": {
        "session_id": "uuid",
        "total_propuestas": 45,
        "alta_confianza": 38,
        "requiere_revision": 7
    },
    "timestamp": "2024-12-08T10:30:00Z"
}
```

---

## 6. Flujos de Datos

### 6.1 Flujo: Carga y Procesamiento de Extracto

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Usuario │     │   API   │     │  Queue  │     │ Worker  │     │   DB    │
└────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘
     │               │               │               │               │
     │ POST /upload  │               │               │               │
     │──────────────>│               │               │               │
     │               │               │               │               │
     │               │ Guardar S3    │               │               │
     │               │───────────────────────────────────────────────>│
     │               │               │               │               │
     │               │ Encolar task  │               │               │
     │               │──────────────>│               │               │
     │               │               │               │               │
     │  202 Accepted │               │               │               │
     │<──────────────│               │               │               │
     │               │               │               │               │
     │               │               │ Dequeue       │               │
     │               │               │──────────────>│               │
     │               │               │               │               │
     │               │               │               │ Parse file    │
     │               │               │               │──────────────>│
     │               │               │               │               │
     │               │               │               │ Detectar dupl.│
     │               │               │               │──────────────>│
     │               │               │               │               │
     │               │               │               │ Insert trans. │
     │               │               │               │──────────────>│
     │               │               │               │               │
     │               │               │               │ Gen embeddings│
     │               │               │               │──────────────>│
     │               │               │               │               │
     │  WS: completed│               │               │               │
     │<──────────────────────────────────────────────│               │
     │               │               │               │               │
```

### 6.2 Flujo: Conciliación con Human-in-the-Loop

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Usuario │     │   API   │     │  Agent  │     │   LLM   │     │   DB    │
└────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘
     │               │               │               │               │
     │ POST /iniciar │               │               │               │
     │──────────────>│               │               │               │
     │               │               │               │               │
     │               │ Start agent   │               │               │
     │               │──────────────>│               │               │
     │               │               │               │               │
     │               │               │ Get data      │               │
     │               │               │──────────────────────────────>│
     │               │               │               │               │
     │               │               │ Exact match   │               │
     │               │               │──────────────────────────────>│
     │               │               │               │               │
     │               │               │ Fuzzy match   │               │
     │               │               │──────────────>│               │
     │               │               │               │               │
     │               │               │ Save proposals│               │
     │               │               │──────────────────────────────>│
     │               │               │               │               │
     │ WS: proposals │               │ CHECKPOINT    │               │
     │<──────────────────────────────│ (human-in-loop)               │
     │               │               │               │               │
     │ GET /propuestas               │               │               │
     │──────────────>│               │               │               │
     │               │               │               │               │
     │ [propuestas]  │               │               │               │
     │<──────────────│               │               │               │
     │               │               │               │               │
     │ POST /validar │               │               │               │
     │──────────────>│               │               │               │
     │               │               │               │               │
     │               │ Resume agent  │               │               │
     │               │──────────────>│               │               │
     │               │               │               │               │
     │               │               │ Apply decisions               │
     │               │               │──────────────────────────────>│
     │               │               │               │               │
     │ WS: completed │               │               │               │
     │<──────────────────────────────│               │               │
     │               │               │               │               │
```

---

## 7. Integraciones

### 7.1 Hugging Face Inference API

```python
from huggingface_hub import InferenceClient

class HFInferenceService:
    def __init__(self, api_key: str):
        self.client = InferenceClient(token=api_key)
    
    async def classify_transaction(
        self, 
        concepto: str, 
        importe: float,
        historico: list[dict]
    ) -> dict:
        """Clasificar transacción usando LLM"""
        
        prompt = f"""Clasifica la siguiente transacción bancaria según el Plan General Contable español.

Transacción:
- Concepto: {concepto}
- Importe: {importe}€

Historial de clasificaciones similares del cliente:
{self._format_historico(historico)}

Responde SOLO con un JSON:
{{"categoria_pgc": "XXX", "nombre_categoria": "...", "confianza": 0.XX, "explicacion": "..."}}
"""
        
        response = await self.client.text_generation(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            prompt=prompt,
            max_new_tokens=200,
            temperature=0.1,
        )
        
        return self._parse_response(response)
    
    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generar embeddings para búsqueda semántica"""
        
        embeddings = await self.client.feature_extraction(
            model="BAAI/bge-m3",
            inputs=texts,
        )
        
        return embeddings
    
    async def extract_invoice_data(self, image_base64: str) -> dict:
        """Extraer datos de factura usando vision model"""
        
        response = await self.client.image_to_text(
            model="microsoft/trocr-large-printed",
            image=image_base64,
        )
        
        # Post-procesar con LLM para estructurar
        structured = await self._structure_invoice_text(response)
        
        return structured
```

### 7.2 Parsers de Extractos Bancarios

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
import csv
import re

@dataclass
class TransaccionRaw:
    fecha: str
    concepto: str
    importe: float
    saldo: float | None = None
    referencia: str | None = None

class BankParser(ABC):
    @abstractmethod
    def parse(self, content: bytes) -> list[TransaccionRaw]:
        pass

class CSVGenericParser(BankParser):
    """Parser genérico CSV con detección de columnas"""
    
    COLUMN_PATTERNS = {
        "fecha": r"fecha|date|f\.|valor",
        "concepto": r"concepto|descripcion|description|detalle",
        "importe": r"importe|amount|cantidad|cargo|abono",
        "saldo": r"saldo|balance",
    }
    
    def parse(self, content: bytes) -> list[TransaccionRaw]:
        text = content.decode("utf-8-sig")
        
        # Detectar delimitador
        dialect = csv.Sniffer().sniff(text[:2000])
        
        reader = csv.DictReader(text.splitlines(), dialect=dialect)
        
        # Mapear columnas
        column_map = self._detect_columns(reader.fieldnames)
        
        transactions = []
        for row in reader:
            tx = TransaccionRaw(
                fecha=row[column_map["fecha"]],
                concepto=row[column_map["concepto"]],
                importe=self._parse_importe(row[column_map["importe"]]),
                saldo=self._parse_importe(row.get(column_map.get("saldo"))),
            )
            transactions.append(tx)
        
        return transactions

class SantanderParser(BankParser):
    """Parser específico para Santander"""
    pass

class BBVAParser(BankParser):
    """Parser específico para BBVA"""
    pass

class CaixaBankParser(BankParser):
    """Parser específico para CaixaBank"""
    pass

class OFXParser(BankParser):
    """Parser para formato OFX/QFX estándar"""
    
    def parse(self, content: bytes) -> list[TransaccionRaw]:
        from ofxparse import OfxParser as OFX
        
        ofx = OFX.parse(io.BytesIO(content))
        
        transactions = []
        for account in ofx.accounts:
            for tx in account.statement.transactions:
                transactions.append(TransaccionRaw(
                    fecha=tx.date.strftime("%Y-%m-%d"),
                    concepto=tx.memo or tx.payee,
                    importe=float(tx.amount),
                    referencia=tx.id,
                ))
        
        return transactions
```

---

## 8. Seguridad y Compliance

### 8.1 Autenticación y Autorización

```python
# JWT con tenant_id embebido
{
    "sub": "user-uuid",
    "tenant_id": "tenant-uuid",
    "email": "usuario@gestoria.com",
    "rol": "admin",
    "exp": 1702000000,
    "iat": 1701900000
}

# Middleware de tenant isolation
async def tenant_middleware(request: Request, call_next):
    token = extract_token(request)
    payload = verify_jwt(token)
    
    # Setear tenant para RLS de PostgreSQL
    async with get_db() as db:
        await db.execute(
            f"SET app.current_tenant = '{payload['tenant_id']}'"
        )
    
    request.state.tenant_id = payload["tenant_id"]
    request.state.user_id = payload["sub"]
    
    return await call_next(request)
```

### 8.2 Cifrado de Datos

| Dato | En tránsito | En reposo |
|------|-------------|-----------|
| Extractos bancarios | TLS 1.3 | AES-256 (S3 SSE) |
| Datos personales (CIF, nombres) | TLS 1.3 | AES-256 (DB TDE) |
| Tokens de API | TLS 1.3 | Hashed (bcrypt) |
| Backups | TLS 1.3 | AES-256 + GPG |

### 8.3 GDPR Compliance (Ver COMPLIANCE.md)

- Minimización de datos
- Derecho al olvido implementado
- Logs de acceso auditables
- DPA con subprocesadores

---

## 9. Observabilidad

### 9.1 Logging Estructurado

```python
import structlog

logger = structlog.get_logger()

# Ejemplo de log de agente
logger.info(
    "agent_action",
    agent="conciliacion",
    action="match_proposed",
    tenant_id=tenant_id,
    transaccion_id=str(tx_id),
    confianza=0.87,
    metodo="fuzzy",
    duracion_ms=234,
)
```

### 9.2 Métricas (Prometheus)

```python
from prometheus_client import Counter, Histogram, Gauge

# Métricas de negocio
transacciones_procesadas = Counter(
    "transacciones_procesadas_total",
    "Total de transacciones procesadas",
    ["tenant_id", "tipo"]
)

conciliaciones_validadas = Counter(
    "conciliaciones_validadas_total",
    "Conciliaciones validadas por humano",
    ["tenant_id", "resultado"]  # aprobada, rechazada
)

precision_clasificacion = Gauge(
    "precision_clasificacion",
    "Precisión de clasificación automática",
    ["tenant_id", "metodo"]
)

# Métricas técnicas
latencia_llm = Histogram(
    "latencia_llm_seconds",
    "Latencia de llamadas a LLM",
    ["modelo", "operacion"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

tareas_en_cola = Gauge(
    "tareas_en_cola",
    "Número de tareas pendientes en cola",
    ["tipo_tarea"]
)
```

### 9.3 Trazabilidad (OpenTelemetry)

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def conciliar_transaccion(tx_id: UUID):
    with tracer.start_as_current_span("conciliar_transaccion") as span:
        span.set_attribute("transaccion_id", str(tx_id))
        
        with tracer.start_span("buscar_candidatos"):
            candidatos = await buscar_candidatos(tx_id)
        
        with tracer.start_span("calcular_matching"):
            matches = await calcular_matching(tx_id, candidatos)
        
        with tracer.start_span("guardar_propuesta"):
            await guardar_propuesta(tx_id, matches)
        
        span.set_attribute("candidatos_encontrados", len(candidatos))
        span.set_attribute("match_confianza", matches[0].confianza if matches else 0)
```

---

## 10. Decisiones de Diseño (ADRs)

### ADR-001: LangGraph vs Framework Custom

**Contexto:** Necesitamos orquestar múltiples agentes con checkpoints para human-in-the-loop.

**Decisión:** Usar LangGraph.

**Razones:**
- Checkpointing nativo para pausar/resumir
- Integración con LangChain ecosystem
- Grafos de estado visualizables
- Comunidad activa

**Alternativas descartadas:**
- AutoGen: Demasiado orientado a chat multi-agente
- Custom: Mayor tiempo de desarrollo

### ADR-002: PostgreSQL + pgvector vs Vector DB dedicada

**Contexto:** Necesitamos búsqueda vectorial para matching semántico.

**Decisión:** PostgreSQL con pgvector.

**Razones:**
- Una sola base de datos a mantener
- Transacciones ACID con datos relacionales
- RLS para multi-tenant funciona igual
- Performance suficiente para volúmenes esperados

**Alternativas descartadas:**
- Pinecone: Coste adicional, complejidad de sync
- Weaviate: Overhead de infraestructura

### ADR-003: Modelo de Clasificación

**Contexto:** Decidir entre fine-tuning propio vs LLM API.

**Decisión:** Híbrido - ML local para casos comunes, LLM para ambiguos.

**Razones:**
- Coste: ML local es gratis post-entrenamiento
- Latencia: ML local ~10ms vs LLM ~500ms
- Precisión: LLM mejor en casos edge
- Explicabilidad: Ambos pueden explicar

**Implementación:**
1. Reglas explícitas (100% confianza)
2. Histórico del proveedor (90% confianza)
3. Modelo DistilBERT fine-tuned (70-85% confianza)
4. LLM fallback (60-80% confianza)

---

## 11. Estructura del Repositorio

```
agente-financiero-ia/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Settings
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py             # Dependencies
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── extractos.py
│   │   │   │   ├── conciliacion.py
│   │   │   │   ├── clasificacion.py
│   │   │   │   ├── tesoreria.py
│   │   │   │   └── informes.py
│   │   │   └── websocket.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Base agent class
│   │   │   ├── conciliacion.py
│   │   │   ├── clasificacion.py
│   │   │   ├── tesoreria.py
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       ├── matching.py
│   │   │       ├── classification.py
│   │   │       └── analysis.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py
│   │   │   ├── database.py
│   │   │   └── cache.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── tenant.py
│   │   │   ├── empresa.py
│   │   │   ├── transaccion.py
│   │   │   └── conciliacion.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── transaccion.py
│   │   │   ├── conciliacion.py
│   │   │   └── informe.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── hf_inference.py
│   │   │   ├── pdf_generator.py
│   │   │   └── parsers/
│   │   │       ├── __init__.py
│   │   │       ├── base.py
│   │   │       ├── csv_parser.py
│   │   │       ├── ofx_parser.py
│   │   │       └── pdf_parser.py
│   │   └── tasks/
│   │       ├── __init__.py
│   │       ├── celery_app.py
│   │       └── workers.py
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_api/
│   │   ├── test_agents/
│   │   └── test_services/
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── stores/
│   │   ├── services/
│   │   └── types/
│   ├── package.json
│   └── Dockerfile
├── ml/
│   ├── notebooks/
│   │   ├── 01_eda_transacciones.ipynb
│   │   ├── 02_train_classifier.ipynb
│   │   └── 03_eval_models.ipynb
│   ├── data/
│   │   └── .gitkeep
│   └── models/
│       └── .gitkeep
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   └── k8s/
│       ├── deployment.yaml
│       └── service.yaml
├── docs/
│   ├── PRD.md
│   ├── ARCHITECT.md
│   ├── PROMPT.md
│   └── COMPLIANCE.md
├── scripts/
│   ├── seed_data.py
│   ├── generate_synthetic.py
│   └── run_migrations.sh
├── .env.example
├── .gitignore
├── README.md
└── Makefile
```

---

## Apéndice A: Configuración de Desarrollo

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: agente
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: agente_financiero
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - miniodata:/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://agente:dev_password@db:5432/agente_financiero
      REDIS_URL: redis://redis:6379
      S3_ENDPOINT: http://minio:9000
      HF_API_KEY: ${HF_API_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
      - minio

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.tasks.celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://agente:dev_password@db:5432/agente_financiero
      REDIS_URL: redis://redis:6379
    depends_on:
      - db
      - redis

volumes:
  pgdata:
  miniodata:
```

---

## Apéndice B: Variables de Entorno

```bash
# .env.example

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/agente_financiero

# Redis
REDIS_URL=redis://localhost:6379

# S3/MinIO
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=agente-documents

# Hugging Face
HF_API_KEY=hf_xxxxxxxxxxxxx

# JWT
JWT_SECRET=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# App
APP_ENV=development
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
```
