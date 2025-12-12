# backend/app/schemas/clasificacion.py
"""Schemas de Clasificacion, Conciliacion, Reglas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel


class ClasificacionResponse(BaseModel):
    """Schema de respuesta de clasificación."""
    id: UUID
    transaccion_id: UUID
    categoria_pgc: str
    subcuenta: str | None
    confianza: Decimal
    metodo: str
    explicacion: str | None
    validado_por: UUID | None
    validado_at: datetime | None
    
    class Config:
        from_attributes = True


class ClasificacionValidate(BaseModel):
    """Schema para validar clasificación."""
    clasificacion_id: UUID
    aprobado: bool
    categoria_pgc: str | None = None  # Para corrección manual
    comentario: str | None = None


class ConciliacionResponse(BaseModel):
    """Schema de respuesta de conciliación."""
    id: UUID
    transaccion_id: UUID
    asiento_id: str | None
    confianza: Decimal
    estado: str
    match_type: str
    match_details: dict | None
    validado_por: UUID | None
    validado_at: datetime | None
    
    class Config:
        from_attributes = True


class ConciliacionValidate(BaseModel):
    """Schema para validar conciliación."""
    propuestas: list[UUID]  # IDs de propuestas a aprobar
    rechazadas: list[UUID] = []  # IDs de propuestas a rechazar


class ReglaCreate(BaseModel):
    """Schema para crear regla de clasificación."""
    nombre: str
    descripcion: str | None = None
    condicion: dict
    categoria_pgc: str
    empresa_id: UUID | None = None
    prioridad: int = 0


class ReglaResponse(BaseModel):
    """Schema de respuesta de regla."""
    id: UUID
    tenant_id: UUID
    empresa_id: UUID | None
    nombre: str
    descripcion: str | None
    condicion: dict
    categoria_pgc: str
    prioridad: int
    activa: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
