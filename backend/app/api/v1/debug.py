# backend/app/api/v1/debug.py
"""Endpoints de debug para ver raw data."""

from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, TokenPayload
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.empresa import Empresa, CuentaBancaria
from app.models.transaccion import Transaccion
from app.models.clasificacion import Clasificacion, ReglaClasificacion

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/stats")
async def get_stats(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Estadísticas generales del tenant."""
    tenant_id = UUID(current_user.tenant_id)
    
    empresas = await db.scalar(select(func.count(Empresa.id)).where(Empresa.tenant_id == tenant_id))
    
    # Contar transacciones a través de cuentas de empresas del tenant
    tx_count = await db.scalar(
        select(func.count(Transaccion.id))
        .join(CuentaBancaria)
        .join(Empresa)
        .where(Empresa.tenant_id == tenant_id)
    )
    
    reglas = await db.scalar(select(func.count(ReglaClasificacion.id)).where(ReglaClasificacion.tenant_id == tenant_id))
    
    return {
        "tenant_id": str(tenant_id),
        "empresas": empresas,
        "transacciones": tx_count,
        "reglas_clasificacion": reglas,
    }


@router.get("/transacciones")
async def get_transacciones(
    empresa_id: UUID = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ver transacciones raw con paginación."""
    tenant_id = UUID(current_user.tenant_id)
    
    query = (
        select(Transaccion)
        .join(CuentaBancaria)
        .join(Empresa)
        .where(Empresa.tenant_id == tenant_id)
        .order_by(Transaccion.fecha.desc())
        .offset(offset)
        .limit(limit)
    )
    
    if empresa_id:
        query = query.where(Empresa.id == empresa_id)
    
    result = await db.execute(query)
    transacciones = result.scalars().all()
    
    return {
        "total": len(transacciones),
        "offset": offset,
        "limit": limit,
        "data": [
            {
                "id": str(t.id),
                "fecha": t.fecha.isoformat(),
                "concepto": t.concepto,
                "importe": float(t.importe),
                "tipo": t.tipo,
                "cuenta_id": str(t.cuenta_id),
            }
            for t in transacciones
        ]
    }


@router.get("/transacciones/resumen")
async def get_transacciones_resumen(
    empresa_id: UUID = None,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resumen de transacciones por tipo y mes."""
    tenant_id = UUID(current_user.tenant_id)
    
    query = (
        select(Transaccion)
        .join(CuentaBancaria)
        .join(Empresa)
        .where(Empresa.tenant_id == tenant_id)
    )
    
    if empresa_id:
        query = query.where(Empresa.id == empresa_id)
    
    result = await db.execute(query)
    transacciones = result.scalars().all()
    
    # Agrupar por mes
    por_mes = {}
    for t in transacciones:
        mes = t.fecha.strftime("%Y-%m")
        if mes not in por_mes:
            por_mes[mes] = {"ingresos": 0, "gastos": 0, "count": 0}
        
        if t.importe > 0:
            por_mes[mes]["ingresos"] += float(t.importe)
        else:
            por_mes[mes]["gastos"] += abs(float(t.importe))
        por_mes[mes]["count"] += 1
    
    # Totales
    total_ingresos = sum(t.importe for t in transacciones if t.importe > 0)
    total_gastos = sum(abs(t.importe) for t in transacciones if t.importe < 0)
    
    return {
        "total_transacciones": len(transacciones),
        "total_ingresos": float(total_ingresos),
        "total_gastos": float(total_gastos),
        "balance": float(total_ingresos - total_gastos),
        "por_mes": dict(sorted(por_mes.items())),
    }
