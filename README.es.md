# 🤖 Agente Financiero IA

> Sistema multi-agente para gestorías españolas  
> Transforma procesadores administrativos en asesores financieros estratégicos  
> **Ahora con análisis inteligente de documentos (PDF, Excel, CSV, Imágenes)**

**🌐 [English](README.md)** | Español

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)

---

## 🎯 Métricas Clave

| Métrica | Valor | Notas |
|---------|-------|-------|
| **Latencia p95** (Clasificación) | ~2.5s | Clasificación de cuentas PGC |
| **Latencia p95** (Embeddings) | ~0.8s | Búsqueda semántica |
| **Latencia p95** (Parser CSV) | ~0.1s | Detección flexible de columnas |
| **Latencia p95** (Parser PDF OCR) | ~5-12s | Vision AI + parsing LLM |
| **Coste por clasificación** | $0.003 | Llama-3.1-8B vía HuggingFace |
| **Coste por PDF** (escaneado) | ~$0.05 | OCR Vision + LLM |
| **Precisión clasificación** | 95%+ | Con interpretación LLM |
| **Formatos de documento** | 6 tipos | CSV, Excel, OFX, PDF, JPG, PNG |
| **Throughput** | ~50 req/min | Instancia única |
| **Concurrencia** | 20 workers | AsyncIO + FastAPI |

> 📊 Ver [METRICS.md](docs/METRICS.md) para benchmarks detallados

---

## 🏗️ Arquitectura

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Extracto   │───▶│   Parser    │───▶│ PostgreSQL  │
│  CSV/OFX    │    │  (detect)   │    │  + pgvector │
└─────────────┘    └─────────────┘    └─────────────┘
                                             │
┌─────────────┐    ┌─────────────┐           ▼
│   Frontend  │◀──▶│   FastAPI   │◀───┬─────────────┐
│   React     │    │   Gateway   │    │  LangGraph  │
└─────────────┘    └─────────────┘    │   Agentes   │
                          │           └─────────────┘
                          ▼                  │
                   ┌─────────────┐           ▼
                   │    Redis    │    ┌─────────────┐
                   │   (caché)   │    │  Mixtral    │
                   └─────────────┘    │  (HF API)   │
                                      └─────────────┘
```

> 🏛️ Ver [ARCHITECTURE.md](docs/ARCHITECTURE.md) para análisis detallado

---

## ✨ Novedades

### 🎉 Fase 3: Parser Universal de Documentos (COMPLETO)
- ✅ **Smart Parser Agent**: IA interpreta cualquier estructura de documento
- ✅ **Soporte PDF**: Extracción de texto nativo + OCR fallback
- ✅ **Soporte Imágenes**: Procesa fotos de extractos (JPG, PNG)
- ✅ **Vision AI**: Qwen3-VL-8B para OCR inteligente
- ✅ **Sin columnas hardcoded**: LLM entiende cualquier formato bancario
- ✅ **Debe/Haber**: Combinación automática de débito/crédito

### 📖 Documentación
- [Guía Smart Parser](docs/SMART_PARSER.md) - Detalles técnicos completos
- [Postmortem](docs/POSTMORTEM.md) - Problemas resueltos
- [Métricas](docs/METRICS.md) - Resultados de benchmarks

---

## 🚀 Inicio Rápido

### Requisitos Previos
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 16 (o usar Docker)
- Token API de HuggingFace

### 1. Clonar y Configurar

```bash
git clone https://github.com/edumesones/financial-ai-agent.git
cd financial-ai-agent

# Copiar variables de entorno
cp .env.template .env
# Editar .env y añadir tu HF_TOKEN
```

### 2. Iniciar Infraestructura

```bash
docker-compose up -d
```

Esto inicia:
- PostgreSQL 16 + pgvector (puerto 5432)
- Redis 7 (puerto 6379)

### 3. Instalar Dependencias

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r backend/requirements.txt
```

### 4. Ejecutar Migraciones

```bash
cd backend
alembic upgrade head
```

### 5. Generar Datos de Prueba (Opcional)

```bash
python scripts/generate_synthetic.py
```

### 6. Iniciar API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API disponible en: http://localhost:8000  
Documentación: http://localhost:8000/docs

### 7. Iniciar Frontend (Opcional)

```bash
cd frontend
npm install
npm run dev
```

Frontend disponible en: http://localhost:5173

---

## 📧 Credenciales de Prueba

```
Email:    admin@gestoria.es
Password: admin123
```

---

## 🧠 Características Principales

### 1. **Clasificación Inteligente** 
Categorización automática de transacciones usando PGC español
- LLM con contexto
- Aprendizaje de histórico
- Validación humana en el bucle

### 2. **Conciliación Bancaria**
Sistema multi-agente para conciliación banco-contabilidad
- Matching exacto + matching fuzzy (embeddings)
- Umbrales de auto-aprobación
- Detección de discrepancias

### 3. **Proyección de Tesorería**
Proyecciones de tesorería con IA
- Análisis de series temporales
- Patrones estacionales
- Alertas de riesgo

### 4. **Parsing de Documentos**
Parser universal para extractos bancarios
- Formatos CSV, OFX, PDF
- Auto-detección
- Soporte multi-banco

---

## 🛠️ Stack Tecnológico

### Backend
- **FastAPI** 0.109 - Framework async moderno
- **PostgreSQL** 16 + **pgvector** - Búsqueda vectorial
- **LangGraph** - Orquestación multi-agente
- **SQLAlchemy** 2.0 - ORM async
- **Alembic** - Migraciones de BD
- **Redis** - Caché y cola de tareas
- **Celery** - Workers en background

### IA/ML
- **Mixtral-8x7B** (vía HuggingFace) - LLM para clasificación
- **BGE-M3** - Embeddings multilingües
- **HuggingFace Inference API** - Router compatible con OpenAI

### Frontend
- **React** 18 + **Vite** - SPA moderno
- **TailwindCSS** - Estilos utility-first
- **Recharts** - Visualización de datos

### DevOps
- **Docker** & **Docker Compose** - Contenedorización
- **GitHub Actions** - CI/CD
- **Prometheus** - Métricas
- **Structlog** - Logging estructurado

---

## 📊 Decisiones de Diseño del Sistema

### ¿Por qué LangGraph en lugar de LangChain puro?
- **Checkpointing**: Pausar agentes para intervención humana
- **Gestión de estado**: Transiciones explícitas
- **Debugging**: Visualización clara del grafo de ejecución
- **Escalabilidad**: Fácil añadir/quitar agentes

### ¿Por qué PostgreSQL + pgvector en lugar de Pinecone?
- **Coste**: Auto-hospedado = $0 almacenamiento vectorial
- **Latencia**: Consultas locales < 50ms vs 200ms+ en la nube
- **Privacidad**: Datos financieros on-premise
- **Trade-off**: Escalado manual vs auto-escalado de Pinecone

### ¿Por qué HuggingFace en lugar de OpenAI?
- **Coste**: 10x más barato para calidad similar
- **Cumplimiento UE**: HF puede ejecutarse en regiones UE
- **Flexibilidad de modelos**: Fácil cambiar modelos
- **Trade-off**: Mayor latencia (2.5s vs 0.8s)

> 📖 Ver [POSTMORTEM.md](docs/POSTMORTEM.md) para problemas y soluciones

---

## 🔧 Qué se Rompió y Cómo lo Arreglé

### 1. **Migraciones de Alembic fallaban: puerto incorrecto**
**Problema**: Alembic no encontraba `.env`, usaba URL DB incorrecta  
**Solución**: Búsqueda multi-ruta de `.env` en `config.py`

### 2. **Deprecación de API de HuggingFace**
**Problema**: `InferenceClient` cambió API, parámetros antiguos fallaban  
**Solución**: Migración a router compatible con OpenAI (`/v1/chat/completions`)

### 3. **Conflictos de versión bcrypt/passlib**
**Problema**: Instalación de `passlib[bcrypt]` fallaba en Windows  
**Solución**: Uso directo de `bcrypt`, eliminado wrapper passlib

### 4. **Validación Pydantic EmailStr**
**Problema**: `EmailStr` requiere `email-validator` pero no estaba en requirements  
**Solución**: Añadido `email-validator==2.2.0` explícitamente

> Detalles completos en [POSTMORTEM.md](docs/POSTMORTEM.md)

---

## 🧪 Testing

```bash
# Ejecutar tests unitarios
pytest backend/tests/

# Ejecutar con cobertura
pytest --cov=app --cov-report=html

# Ejecutar benchmarks
python scripts/benchmark.py
```

---

## 📚 Endpoints de la API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v1/auth/token` | POST | Login y obtener JWT |
| `/api/v1/empresas/` | GET | Listar empresas |
| `/api/v1/extractos/upload` | POST | Subir extracto bancario |
| `/api/v1/clasificacion/batch` | POST | Clasificar transacciones (agente LangGraph) |
| `/api/v1/conciliacion/iniciar` | POST | Iniciar proceso de conciliación |
| `/api/v1/tesoreria/{empresa_id}/snapshot` | GET | Snapshot de tesorería |
| `/api/v1/chat/` | POST | Interfaz conversacional IA |
| `/health` | GET | Health check |
| `/docs` | GET | Documentación OpenAPI |

---

## 📂 Estructura del Proyecto

```
financial-ai-agent/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # Endpoints REST
│   │   ├── agents/         # Agentes LangGraph
│   │   ├── core/           # Config, DB, Security
│   │   ├── models/         # Modelos SQLAlchemy
│   │   ├── schemas/        # Schemas Pydantic
│   │   ├── services/       # HF Inference, Parsers
│   │   └── tasks/          # Workers Celery
│   ├── alembic/            # Migraciones BD
│   └── requirements.txt
├── frontend/               # SPA React
├── scripts/
│   ├── benchmark.py        # Testing de rendimiento
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

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor:
1. Haz fork del repo
2. Crea una rama de feature (`git checkout -b feature/increible`)
3. Commit los cambios (`git commit -m 'Añadir feature increíble'`)
4. Push a la rama (`git push origin feature/increible`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está licenciado bajo **Apache License 2.0** - ver el archivo [LICENSE](LICENSE) para detalles.

---

## 👤 Autor

**Eduardo Glez-Mesones**  
📧 [e.gzlzmesones@gmail.com](mailto:e.gzlzmesones@gmail.com)  
🔗 [LinkedIn](https://www.linkedin.com/in/eduardo-gonzalez-mesones-de-la-sierra-65b2a3140/)

---

## 🙏 Agradecimientos

- FastAPI por el increíble framework async
- HuggingFace por inferencia LLM accesible
- Equipo LangGraph por orquestación multi-agente
- Contribuidores de pgvector por búsqueda vectorial en PostgreSQL

---

**⭐ Si este proyecto te ayudó, ¡considera darle una estrella!**

