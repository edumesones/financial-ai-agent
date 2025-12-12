# backend/app/api/v1/empresas.py
"""Endpoints de gestión de empresas."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db, set_tenant_context
from app.core.security import get_current_user, TokenPayload
from app.models.empresa import Empresa, CuentaBancaria
from app.schemas.empresa import EmpresaCreate, EmpresaResponse, CuentaBancariaCreate, CuentaBancariaResponse

router = APIRouter(prefix="/empresas", tags=["empresas"])


@router.get("/", response_model=list[EmpresaResponse])
async def list_empresas(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Listar empresas del tenant."""
    await set_tenant_context(db, current_user.tenant_id)
    
    stmt = (
        select(Empresa)
        .where(Empresa.tenant_id == UUID(current_user.tenant_id), Empresa.activo == True)
        .options(selectinload(Empresa.cuentas))
        .order_by(Empresa.nombre)
    )
    result = await db.execute(stmt)
    empresas = result.scalars().all()
    return empresas


@router.post("/", response_model=EmpresaResponse, status_code=status.HTTP_201_CREATED)
async def create_empresa(
    data: EmpresaCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Crear nueva empresa."""
    empresa = Empresa(
        tenant_id=UUID(current_user.tenant_id),
        nombre=data.nombre,
        cif=data.cif,
        sector=data.sector,
        direccion=data.direccion,
    )
    
    for cuenta_data in data.cuentas:
        cuenta = CuentaBancaria(
            banco=cuenta_data.banco,
            iban=cuenta_data.iban,
            alias=cuenta_data.alias,
        )
        empresa.cuentas.append(cuenta)
    
    db.add(empresa)
    await db.commit()
    await db.refresh(empresa)
    
    return empresa


@router.get("/{empresa_id}", response_model=EmpresaResponse)
async def get_empresa(
    empresa_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtener empresa por ID."""
    stmt = (
        select(Empresa)
        .where(Empresa.id == empresa_id, Empresa.tenant_id == UUID(current_user.tenant_id))
        .options(selectinload(Empresa.cuentas))
    )
    result = await db.execute(stmt)
    empresa = result.scalar_one_or_none()
    
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    return empresa


@router.post("/{empresa_id}/cuentas", response_model=CuentaBancariaResponse)
async def add_cuenta(
    empresa_id: UUID,
    data: CuentaBancariaCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Añadir cuenta bancaria a empresa."""
    stmt = select(Empresa).where(
        Empresa.id == empresa_id, Empresa.tenant_id == UUID(current_user.tenant_id)
    )
    result = await db.execute(stmt)
    empresa = result.scalar_one_or_none()
    
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    cuenta = CuentaBancaria(
        empresa_id=empresa.id,
        banco=data.banco,
        iban=data.iban,
        alias=data.alias,
    )
    db.add(cuenta)
    await db.commit()
    await db.refresh(cuenta)
    
    return cuenta
