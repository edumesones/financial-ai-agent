# backend/app/schemas/empresa.py
"""Schemas de Empresa y CuentaBancaria."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class CuentaBancariaCreate(BaseModel):
    """Schema para crear cuenta bancaria."""
    banco: str | None = None
    iban: str | None = None
    alias: str | None = None


class CuentaBancariaResponse(BaseModel):
    """Schema de respuesta de cuenta bancaria."""
    id: UUID
    empresa_id: UUID
    banco: str | None
    iban: str | None
    alias: str | None
    activa: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmpresaCreate(BaseModel):
    """Schema para crear empresa."""
    nombre: str
    cif: str | None = None
    sector: str | None = None
    direccion: str | None = None
    cuentas: list[CuentaBancariaCreate] = []


class EmpresaResponse(BaseModel):
    """Schema de respuesta de empresa."""
    id: UUID
    tenant_id: UUID
    nombre: str
    cif: str | None
    sector: str | None
    direccion: str | None
    activo: bool
    created_at: datetime
    cuentas: list[CuentaBancariaResponse] = []
    
    class Config:
        from_attributes = True
