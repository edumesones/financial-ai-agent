# backend/app/schemas/tenant.py
"""Schemas de Tenant."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr


class TenantCreate(BaseModel):
    """Schema para crear tenant."""
    nombre: str
    cif: str | None = None
    email: EmailStr | None = None
    telefono: str | None = None


class TenantUpdate(BaseModel):
    """Schema para actualizar tenant."""
    nombre: str | None = None
    cif: str | None = None
    email: EmailStr | None = None
    telefono: str | None = None
    config: dict | None = None


class TenantResponse(BaseModel):
    """Schema de respuesta de tenant."""
    id: UUID
    nombre: str
    cif: str | None
    email: str | None
    telefono: str | None
    config: dict
    activo: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
