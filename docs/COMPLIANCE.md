# COMPLIANCE.md: Cumplimiento Normativo

> **Versión:** 1.0  
> **Fecha:** Diciembre 2024  
> **Estado:** Placeholder - Requiere revisión legal  
> **Proyecto:** Agente Financiero IA

---

## ⚠️ AVISO IMPORTANTE

Este documento es un **placeholder** con las consideraciones técnicas de compliance. Antes de producción, debe ser revisado por un profesional legal especializado en protección de datos y normativa financiera.

---

## 1. GDPR (Reglamento General de Protección de Datos)

### 1.1 Datos Tratados

| Categoría | Datos | Base Legal | Retención |
|-----------|-------|------------|-----------|
| Identificativos empresa | CIF, razón social, dirección | Ejecución contrato | Duración contrato + 5 años |
| Financieros | Transacciones, saldos, facturas | Ejecución contrato | Según normativa fiscal (6 años) |
| Usuarios | Email, nombre, contraseña hash | Ejecución contrato | Duración contrato |
| Logs técnicos | IPs, user agents, acciones | Interés legítimo | 90 días |

### 1.2 Medidas Técnicas Implementadas

**Minimización de datos:**
- Solo se recopilan datos necesarios para el servicio
- No se almacenan datos personales de terceros innecesarios
- Anonimización en entornos de desarrollo/testing

**Cifrado:**
- En tránsito: TLS 1.3 obligatorio
- En reposo: AES-256 para documentos (S3 SSE)
- Passwords: bcrypt con salt

**Control de acceso:**
- Autenticación JWT con expiración
- RBAC (Role-Based Access Control)
- Row-Level Security en PostgreSQL por tenant

**Auditoría:**
- Logging de todas las acciones sobre datos
- Retención de logs de acceso 90 días
- Trazabilidad de quién accedió a qué

### 1.3 Derechos de los Interesados

| Derecho | Implementación |
|---------|----------------|
| Acceso | Endpoint `/api/v1/gdpr/export` para descarga de datos |
| Rectificación | Edición desde UI + API |
| Supresión | Endpoint `/api/v1/gdpr/delete` + proceso de purga |
| Portabilidad | Export en formato JSON/CSV estándar |
| Oposición | Flag de opt-out en perfil |

### 1.4 Transferencias Internacionales

- Infraestructura en EU (AWS eu-west-1 o similar)
- Hugging Face Inference: verificar ubicación de servidores
- No se transfieren datos a terceros países sin garantías adecuadas

---

## 2. Normativa Financiera

### 2.1 Ley de Prevención del Blanqueo de Capitales

**No aplicable directamente** - El sistema no realiza operaciones financieras, solo análisis de datos ya existentes. Sin embargo:

- No se facilita el acceso a datos entre diferentes clientes
- Aislamiento estricto de datos por tenant
- Logs de auditoría disponibles para inspección

### 2.2 Secreto Profesional

Las gestorías tienen obligación de secreto profesional sobre datos de sus clientes. El sistema:

- Implementa aislamiento total entre tenants
- No permite acceso cruzado entre gestorías
- Personal de soporte no tiene acceso a datos de clientes

---

## 3. Multi-tenancy y Aislamiento

### 3.1 Arquitectura de Aislamiento

```
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE APLICACIÓN                        │
│                                                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│   │  Tenant A   │  │  Tenant B   │  │  Tenant C   │        │
│   │  (JWT: A)   │  │  (JWT: B)   │  │  (JWT: C)   │        │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│          │                │                │                │
└──────────┼────────────────┼────────────────┼────────────────┘
           │                │                │
           ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE DATOS                             │
│                                                              │
│   PostgreSQL con Row-Level Security                          │
│   ┌─────────────────────────────────────────────────────┐   │
│   │ SET app.current_tenant = 'tenant_id_from_jwt'       │   │
│   │                                                      │   │
│   │ Policy: WHERE tenant_id = current_setting(...)      │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Controles de Aislamiento

- **Nivel aplicación:** tenant_id extraído de JWT, inyectado en todas las queries
- **Nivel base de datos:** RLS policies que filtran por tenant_id
- **Nivel storage:** Prefijos de bucket por tenant (s3://bucket/tenant_id/...)
- **Nivel caché:** Prefijos de key por tenant (redis: tenant:A:key)

### 3.3 Testing de Aislamiento

```python
# Test obligatorio en CI/CD
def test_tenant_isolation():
    """Verificar que tenant A no puede ver datos de tenant B"""
    # Crear datos en tenant A
    # Intentar acceder desde tenant B
    # Debe fallar o devolver vacío
```

---

## 4. Seguridad de la Información

### 4.1 Autenticación

- JWT con firma HS256/RS256
- Expiración configurable (default: 60 min)
- Refresh tokens con rotación
- Rate limiting en endpoints de auth

### 4.2 Autorización

```python
ROLES = {
    "admin": ["*"],  # Todo
    "gestor": ["read", "write", "validate"],
    "viewer": ["read"],
}
```

### 4.3 Seguridad de APIs

- CORS restringido a orígenes conocidos
- Rate limiting por IP y por usuario
- Validación estricta de inputs (Pydantic)
- Sanitización de outputs
- Headers de seguridad (CSP, HSTS, etc.)

### 4.4 Gestión de Secretos

- Variables de entorno para configuración sensible
- No hardcoding de credenciales en código
- Rotación periódica de API keys
- Secretos diferentes por entorno (dev/staging/prod)

---

## 5. Backup y Recuperación

### 5.1 Política de Backups

| Tipo | Frecuencia | Retención | Ubicación |
|------|------------|-----------|-----------|
| Full DB | Diario | 30 días | S3 (otra región) |
| Incremental | Cada 6h | 7 días | S3 |
| WAL archiving | Continuo | 7 días | S3 |
| Documentos S3 | Versionado | 90 días | S3 |

### 5.2 RTO/RPO

- **RPO (Recovery Point Objective):** < 6 horas
- **RTO (Recovery Time Objective):** < 4 horas

### 5.3 Procedimiento de Recuperación

1. Restaurar último backup full
2. Aplicar WAL hasta punto de recuperación
3. Verificar integridad de datos
4. Restaurar documentos desde S3
5. Validar funcionamiento de aplicación

---

## 6. Logging y Auditoría

### 6.1 Eventos Auditados

```python
AUDIT_EVENTS = [
    "user.login",
    "user.logout",
    "user.password_change",
    "data.export",
    "data.delete",
    "conciliacion.validate",
    "clasificacion.manual_override",
    "informe.generate",
    "admin.user_create",
    "admin.config_change",
]
```

### 6.2 Formato de Log de Auditoría

```json
{
    "timestamp": "2024-12-08T10:30:00Z",
    "event": "conciliacion.validate",
    "tenant_id": "uuid",
    "user_id": "uuid",
    "user_email": "usuario@gestoria.com",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "resource_type": "conciliacion",
    "resource_id": "uuid",
    "action": "approve",
    "details": {"propuestas_aprobadas": 15}
}
```

### 6.3 Retención de Logs

- Logs operativos: 30 días en hot storage, 90 días en cold
- Logs de auditoría: 2 años (requisito legal para datos financieros)
- Logs de seguridad: 1 año

---

## 7. Gestión de Incidentes

### 7.1 Clasificación

| Severidad | Descripción | Tiempo Respuesta |
|-----------|-------------|------------------|
| P1 - Crítico | Breach de datos, sistema caído | < 1 hora |
| P2 - Alto | Funcionalidad crítica afectada | < 4 horas |
| P3 - Medio | Funcionalidad menor afectada | < 24 horas |
| P4 - Bajo | Mejora/bug menor | < 1 semana |

### 7.2 Proceso de Notificación de Breach (GDPR Art. 33-34)

1. **Detección:** Alertas automáticas + monitorización
2. **Contención:** Aislar sistemas afectados
3. **Evaluación:** Determinar alcance y datos afectados
4. **Notificación AEPD:** < 72 horas si aplica
5. **Notificación usuarios:** Sin dilación si alto riesgo
6. **Documentación:** Registro completo del incidente
7. **Remediación:** Corregir causa raíz
8. **Post-mortem:** Análisis y mejoras

---

## 8. Checklist Pre-Producción

### 8.1 Técnico

- [ ] TLS 1.3 configurado en todos los endpoints
- [ ] Cifrado en reposo activo en DB y S3
- [ ] RLS habilitado y testeado
- [ ] Rate limiting configurado
- [ ] Logs de auditoría funcionando
- [ ] Backups automáticos verificados
- [ ] Monitorización y alertas activas
- [ ] Penetration test realizado

### 8.2 Legal/Compliance

- [ ] Política de privacidad publicada
- [ ] Términos de servicio publicados
- [ ] DPA (Data Processing Agreement) con subprocesadores
- [ ] Registro de actividades de tratamiento
- [ ] DPIA (Data Protection Impact Assessment) si aplica
- [ ] Designación de DPO si aplica
- [ ] Inscripción en registro AEPD si aplica

### 8.3 Operacional

- [ ] Procedimiento de onboarding de clientes
- [ ] Procedimiento de offboarding (eliminación de datos)
- [ ] Plan de respuesta a incidentes documentado
- [ ] Contacto de seguridad publicado
- [ ] SLA documentado

---

## 9. Subprocesadores

| Proveedor | Servicio | Ubicación | DPA |
|-----------|----------|-----------|-----|
| AWS / GCP / Azure | Infraestructura | EU | ✅ |
| Hugging Face | Inference API | Verificar | Pendiente |
| SendGrid / SES | Email transaccional | US (SCCs) | ✅ |

---

## Apéndice: Contactos

- **Responsable de Seguridad:** [email]
- **DPO (si designado):** [email]
- **Soporte técnico:** [email]
- **Incidentes de seguridad:** security@[dominio]
