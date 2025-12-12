# backend/app/schemas/transaccion.py
"""Schemas de Transaccion."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel


class TransaccionCreate(BaseModel):
    """Schema para crear transacción."""
    cuenta_id: UUID
    fecha: date
    fecha_valor: date | None = None
    importe: Decimal
    concepto: str | None = None
    tipo: str  # ingreso, gasto, transferencia
    referencia: str | None = None


class TransaccionResponse(BaseModel):
    """Schema de respuesta de transacción."""
    id: UUID
    cuenta_id: UUID
    fecha: date
    fecha_valor: date | None
    importe: Decimal
    concepto: str | None
    tipo: str
    referencia: str | None
    hash: str
    created_at: datetime
    
    # Relaciones opcionales
    clasificacion: "ClasificacionResponse | None" = None
    conciliacion: "ConciliacionResponse | None" = None
    
    class Config:
        from_attributes = True


class TransaccionBatch(BaseModel):
    """Schema para batch de transacciones."""
    transacciones: list[TransaccionCreate]
    cuenta_id: UUID


# Forward reference
from .clasificacion import ClasificacionResponse, ConciliacionResponse
TransaccionResponse.model_rebuild()
