# PRD: Agente Financiero IA

> **Versión:** 1.0  
> **Fecha:** Diciembre 2024  
> **Estado:** Draft  
> **Autor:** GLEMES FFT

---

## 1. Resumen Ejecutivo

**Agente Financiero IA** es un sistema multi-agente que automatiza tareas repetitivas de análisis financiero para gestorías, transformándolas de tramitadores a asesores estratégicos.

### Propuesta de Valor

Las gestorías tienen acceso a todos los datos financieros de sus clientes pero carecen de tiempo y herramientas para convertirlos en valor. El 73% de las PYMEs españolas no reciben asesoramiento financiero real, solo tramitación.

**Nuestra solución:** Un sistema de agentes especializados que automatiza conciliación bancaria, clasificación de gastos y análisis de tesorería, generando informes ejecutivos en minutos en lugar de horas.

---

## 2. Problema

### 2.1 Contexto de Mercado

| Métrica | Valor | Fuente |
|---------|-------|--------|
| Gestorías en España | +15.000 | AECEM 2024 |
| PYMEs en España | +3 millones | INE 2024 |
| % microempresas en sector | 80% | Wolters Kluwer 2023 |
| % sin asesoramiento real | 73% | Barómetro Asesoría 2023 |

### 2.2 Pain Points Identificados

#### P1: Conciliación Bancaria Manual
- **Tiempo invertido:** 4-8 horas/mes por cliente mediano
- **Tasa de error:** 15-20% en procesos manuales
- **Impacto:** Retrasos en cierres contables, errores en declaraciones

#### P2: Clasificación de Gastos/Ingresos
- **Problema:** Categorización manual de cientos de transacciones
- **Inconsistencia:** Diferentes criterios entre empleados
- **Impacto:** Análisis financieros poco fiables, oportunidades fiscales perdidas

#### P3: Falta de Análisis de Tesorería
- **Realidad:** Las gestorías contabilizan pero no analizan
- **Consecuencia:** Clientes sin visibilidad de cash flow
- **Impacto:** Decisiones de negocio a ciegas, sorpresas de liquidez

### 2.3 Consecuencia Competitiva

> *"La gestoría que solo tramita, compite por precio. La que asesora, fideliza."*

Sin diferenciación de valor, las gestorías entran en guerra de precios con márgenes cada vez más comprimidos. Los clientes se van cuando encuentran una opción más barata.

---

## 3. Solución

### 3.1 Visión del Producto

Un sistema SaaS multi-tenant que despliega agentes IA especializados para automatizar el trabajo repetitivo de análisis financiero, liberando tiempo para que los profesionales de gestoría se enfoquen en asesoramiento de valor.

### 3.2 Principios de Diseño

| Principio | Descripción |
|-----------|-------------|
| **Human-in-the-loop** | La IA propone, el humano valida y decide |
| **Auditable** | Cada decisión del agente es trazable y explicable |
| **Modular** | Agentes independientes que pueden activarse según necesidad |
| **Incremental** | Valor desde el día 1, sin necesidad de migración completa |

### 3.3 Arquitectura de Agentes (MVP)

```
┌─────────────────────────────────────────────────────────────┐
│                    ORQUESTADOR PRINCIPAL                     │
│            (Routing, Context Management, Memory)             │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│    AGENTE     │ │    AGENTE     │ │    AGENTE     │
│ CONCILIACIÓN  │ │CLASIFICACIÓN  │ │  TESORERÍA    │
│   BANCARIA    │ │    GASTOS     │ │   CASH FLOW   │
└───────────────┘ └───────────────┘ └───────────────┘
```

---

## 4. Usuarios Target

### 4.1 Persona Principal: Gestor/a Contable

**Nombre:** María García  
**Rol:** Responsable de contabilidad en gestoría de 8 empleados  
**Edad:** 35-50 años  
**Clientes a cargo:** 40-60 empresas (mayoría PYMEs)

**Día típico:**
- 60% tiempo en tareas repetitivas (conciliación, clasificación)
- 30% en cumplimiento fiscal
- 10% en asesoramiento real

**Frustraciones:**
- "Paso más tiempo cuadrando números que analizándolos"
- "Mis clientes no entienden el valor de lo que hago"
- "No tengo tiempo de profundizar en cada empresa"

**Motivaciones:**
- Ofrecer más valor a sus clientes
- Reducir el estrés de los cierres mensuales
- Diferenciarse de la competencia

### 4.2 Persona Secundaria: Director/a de Gestoría

**Nombre:** Antonio Ruiz  
**Rol:** Socio director de gestoría  
**Empleados:** 5-15 personas  
**Preocupaciones:** Rentabilidad, retención de clientes, atracción de talento

**Necesidades:**
- Aumentar ingresos por cliente sin aumentar plantilla
- Ofrecer servicios premium diferenciadores
- Mejorar márgenes operativos

---

## 5. User Stories (MVP)

### 5.1 Épica: Conciliación Bancaria Automatizada

#### US-101: Carga de Extractos Bancarios
**Como** gestor contable  
**Quiero** cargar extractos bancarios en múltiples formatos (CSV, OFX, PDF)  
**Para** no tener que convertir manualmente los archivos  

**Criterios de aceptación:**
- [ ] Soporta CSV con detección automática de delimitador
- [ ] Soporta OFX/QFX estándar bancario
- [ ] Extrae datos de PDFs de extractos comunes (Santander, BBVA, CaixaBank, Sabadell)
- [ ] Valida integridad de datos antes de procesar
- [ ] Muestra preview de transacciones detectadas

#### US-102: Matching Automático de Transacciones
**Como** gestor contable  
**Quiero** que el sistema proponga coincidencias entre banco y contabilidad  
**Para** reducir el tiempo de conciliación de horas a minutos  

**Criterios de aceptación:**
- [ ] Match exacto por importe + fecha (±3 días)
- [ ] Match fuzzy por concepto/descripción
- [ ] Propone matches con score de confianza (alto/medio/bajo)
- [ ] Permite configurar tolerancia de fechas
- [ ] Agrupa transacciones relacionadas (ej: factura con múltiples pagos)

#### US-103: Revisión y Validación Humana
**Como** gestor contable  
**Quiero** revisar y aprobar/rechazar las propuestas del sistema  
**Para** mantener el control y la responsabilidad sobre la conciliación  

**Criterios de aceptación:**
- [ ] Vista de propuestas pendientes con filtros
- [ ] Aprobación individual o en lote
- [ ] Posibilidad de match manual para casos no detectados
- [ ] Registro de quién aprobó cada match
- [ ] Exportación de informe de conciliación

#### US-104: Detección de Discrepancias
**Como** gestor contable  
**Quiero** que el sistema identifique automáticamente las partidas sin conciliar  
**Para** enfocar mi atención solo en los problemas reales  

**Criterios de aceptación:**
- [ ] Lista de transacciones bancarias sin match
- [ ] Lista de asientos contables sin contrapartida bancaria
- [ ] Sugerencias de posibles causas (duplicado, error importe, etc.)
- [ ] Alerta de antigüedad de partidas pendientes

---

### 5.2 Épica: Clasificación Inteligente de Gastos

#### US-201: Categorización Automática de Transacciones
**Como** gestor contable  
**Quiero** que el sistema clasifique automáticamente gastos e ingresos  
**Para** no tener que revisar cada transacción manualmente  

**Criterios de aceptación:**
- [ ] Clasificación según Plan General Contable (PGC)
- [ ] Aprendizaje del histórico del cliente
- [ ] Propuesta con nivel de confianza
- [ ] Soporte para categorías personalizadas por cliente
- [ ] Detección de transacciones atípicas para revisión

#### US-202: Extracción de Datos de Facturas
**Como** gestor contable  
**Quiero** que el sistema extraiga datos clave de facturas PDF  
**Para** automatizar la contabilización de compras y ventas  

**Criterios de aceptación:**
- [ ] Extracción de: emisor, CIF, fecha, base imponible, IVA, total
- [ ] Detección de tipo de factura (ordinaria, rectificativa, simplificada)
- [ ] Validación de CIF contra base de datos
- [ ] Propuesta de asiento contable
- [ ] Soporte para facturas escaneadas (OCR)

#### US-203: Reglas de Clasificación Personalizadas
**Como** gestor contable  
**Quiero** definir reglas específicas para clientes concretos  
**Para** que el sistema aprenda las particularidades de cada negocio  

**Criterios de aceptación:**
- [ ] Creación de reglas basadas en concepto/descripción
- [ ] Reglas por proveedor recurrente
- [ ] Herencia de reglas (plantilla → cliente)
- [ ] Priorización de reglas (específica > general)
- [ ] Importación/exportación de reglas entre clientes similares

---

### 5.3 Épica: Análisis de Tesorería y Cash Flow

#### US-301: Dashboard de Tesorería en Tiempo Real
**Como** gestor contable  
**Quiero** ver la posición de tesorería actual de mis clientes  
**Para** detectar problemas de liquidez antes de que ocurran  

**Criterios de aceptación:**
- [ ] Saldo actual por cuenta bancaria
- [ ] Evolución últimos 30/60/90 días
- [ ] Comparativa con mismo período año anterior
- [ ] Alertas configurables (saldo mínimo, variación brusca)
- [ ] Vista consolidada multi-empresa (para el gestor)

#### US-302: Proyección de Cash Flow
**Como** gestor contable  
**Quiero** una proyección de tesorería a 30/60/90 días  
**Para** anticipar necesidades de financiación de mis clientes  

**Criterios de aceptación:**
- [ ] Proyección basada en patrones históricos
- [ ] Inclusión de pagos/cobros programados conocidos
- [ ] Escenarios (optimista/base/pesimista)
- [ ] Identificación de "valles" de liquidez
- [ ] Sugerencias de acciones (adelantar cobros, negociar pagos)

#### US-303: Análisis de Patrones de Gasto
**Como** gestor contable  
**Quiero** identificar tendencias y anomalías en los gastos de mis clientes  
**Para** ofrecer recomendaciones de optimización  

**Criterios de aceptación:**
- [ ] Desglose de gastos por categoría (% sobre total)
- [ ] Evolución mensual por categoría
- [ ] Detección de gastos recurrentes
- [ ] Identificación de incrementos anómalos
- [ ] Benchmark vs sector (si hay datos disponibles)

#### US-304: Generación de Informe Ejecutivo
**Como** gestor contable  
**Quiero** generar un informe PDF para enviar a mi cliente  
**Para** demostrar el valor del análisis que realizo  

**Criterios de aceptación:**
- [ ] Informe de 2-4 páginas, formato profesional
- [ ] Resumen ejecutivo con KPIs clave
- [ ] Gráficos de evolución y composición
- [ ] Alertas y recomendaciones destacadas
- [ ] Personalizable con logo de la gestoría
- [ ] Exportación a PDF y opción de dashboard interactivo

---

## 6. Priorización (MoSCoW)

### Must Have (MVP)
- US-101: Carga de extractos bancarios
- US-102: Matching automático de transacciones
- US-103: Revisión y validación humana
- US-201: Categorización automática de transacciones
- US-301: Dashboard de tesorería en tiempo real
- US-304: Generación de informe ejecutivo

### Should Have (v1.1)
- US-104: Detección de discrepancias
- US-202: Extracción de datos de facturas
- US-302: Proyección de cash flow

### Could Have (v1.2)
- US-203: Reglas de clasificación personalizadas
- US-303: Análisis de patrones de gasto

### Won't Have (this release)
- Integración directa con ERPs (A3, Sage, Holded)
- Multi-idioma
- App móvil nativa

---

## 7. Métricas de Éxito

### 7.1 Métricas de Producto

| Métrica | Baseline | Target MVP | Target v1.0 |
|---------|----------|------------|-------------|
| Tiempo conciliación mensual | 4-8 horas | < 1 hora | < 30 min |
| Precisión matching automático | N/A | > 80% | > 90% |
| Precisión clasificación gastos | N/A | > 75% | > 85% |
| Tiempo generación informe | 2-4 horas | < 5 min | < 2 min |

### 7.2 Métricas de Negocio

| Métrica | Target 6 meses | Target 12 meses |
|---------|----------------|-----------------|
| Gestorías piloto | 5 | 20 |
| NPS usuarios | > 40 | > 50 |
| Retención mensual | > 85% | > 90% |
| Empresas gestionadas | 200 | 1.000 |

### 7.3 Métricas Técnicas

| Métrica | Target |
|---------|--------|
| Disponibilidad | 99.5% |
| Tiempo respuesta API (p95) | < 2s |
| Tiempo procesamiento batch | < 5 min/100 transacciones |
| Cobertura tests | > 80% |

---

## 8. Fuera de Alcance (MVP)

- **Integración bidireccional con ERPs:** Solo lectura de datos exportados
- **Presentación automática de impuestos:** El sistema analiza, no presenta
- **Asesoramiento fiscal automatizado:** Solo detección de oportunidades
- **Gestión documental completa:** Solo facturas relacionadas con flujo de caja
- **Multi-país:** Solo España (PGC español, formato NIF/CIF)

---

## 9. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Precisión insuficiente del matching | Media | Alto | Human-in-the-loop obligatorio, umbrales conservadores |
| Resistencia al cambio de usuarios | Alta | Medio | Onboarding guiado, ROI visible desde día 1 |
| Variabilidad formatos bancarios | Alta | Medio | Parsers específicos por banco, fallback manual |
| Coste de inferencia LLM | Media | Medio | Caché agresivo, modelos pequeños para tareas simples |
| Cumplimiento GDPR | Baja | Alto | Datos en EU, cifrado, aislamiento por tenant |

---

## 10. Dependencias

### 10.1 Técnicas
- Hugging Face Inference API (modelos LLM)
- Servicio OCR para extracción de PDFs
- Base de datos PostgreSQL
- Almacenamiento S3-compatible

### 10.2 De Negocio
- Acceso a datos de prueba de gestorías piloto
- Feedback continuo de usuarios durante desarrollo
- Validación legal de tratamiento de datos

---

## 11. Timeline Propuesto

| Fase | Duración | Entregables |
|------|----------|-------------|
| **Discovery** | 2-3 semanas | Arquitectura detallada, contratos API, diseño UI |
| **MVP Development** | 8-10 semanas | Agentes core, UI básica, informe PDF |
| **Piloto** | 4-6 semanas | 3-5 gestorías reales, iteración basada en feedback |
| **Producción** | Ongoing | Despliegue comercial, soporte, evolución |

---

## Apéndice A: Glosario

| Término | Definición |
|---------|------------|
| **Conciliación bancaria** | Proceso de verificar que los registros contables coinciden con los extractos bancarios |
| **PGC** | Plan General de Contabilidad, normativa contable española |
| **Tenant** | Cada gestoría cliente del sistema, con datos aislados |
| **Match** | Correspondencia entre una transacción bancaria y un asiento contable |
| **RAG** | Retrieval-Augmented Generation, técnica de IA para respuestas basadas en documentos |

---

## Apéndice B: Referencias

- Barómetro de la Asesoría 2023 (Wolters Kluwer)
- Informe de digitalización de PYMEs 2024 (ONTSI)
- Década Digital España 2024 (Comisión Europea)
- Estado de la digitalización en asesorías (Revista Byte TI, Mayo 2024)
