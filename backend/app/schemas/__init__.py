# backend/app/schemas/__init__.py
"""Pydantic schemas for API validation."""

from .auth import Token, TokenPayload, LoginRequest
from .tenant import TenantCreate, TenantResponse, TenantUpdate
from .empresa import EmpresaCreate, EmpresaResponse, CuentaBancariaCreate, CuentaBancariaResponse
from .transaccion import TransaccionCreate, TransaccionResponse, TransaccionBatch
from .clasificacion import (
    ClasificacionResponse,
    ClasificacionValidate,
    ConciliacionResponse,
    ConciliacionValidate,
    ReglaCreate,
    ReglaResponse,
)
from .tesoreria import TesoreriaSnapshot, TesoreriaProyeccion, TesoreriaAlerta

__all__ = [
    "Token",
    "TokenPayload", 
    "LoginRequest",
    "TenantCreate",
    "TenantResponse",
    "TenantUpdate",
    "EmpresaCreate",
    "EmpresaResponse",
    "CuentaBancariaCreate",
    "CuentaBancariaResponse",
    "TransaccionCreate",
    "TransaccionResponse",
    "TransaccionBatch",
    "ClasificacionResponse",
    "ClasificacionValidate",
    "ConciliacionResponse",
    "ConciliacionValidate",
    "ReglaCreate",
    "ReglaResponse",
    "TesoreriaSnapshot",
    "TesoreriaProyeccion",
    "TesoreriaAlerta",
]
