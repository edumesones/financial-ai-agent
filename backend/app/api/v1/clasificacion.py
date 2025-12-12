# backend/app/api/v1/clasificacion.py
"""Endpoints de clasificación de transacciones."""

from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user, TokenPayload
from app.services.hf_inference import HFInferenceService
from app.agents.clasificacion import ClasificacionAgent
from app.models.transaccion import Transaccion
from app.models.clasificacion import ReglaClasificacion
from app.schemas.clasificacion import ClasificacionValidate, ReglaCreate, ReglaResponse

router = APIRouter(prefix="/clasificacion", tags=["clasificacion"])

_sessions: dict[str, dict] = {}


class ClasificacionBatchRequest(BaseModel):
    transaccion_ids: list[str]
    review_threshold: float = 0.75


@router.post("/batch")
async def clasificar_batch(
    request: ClasificacionBatchRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clasificar batch de transacciones."""
    session_id = str(uuid4())
    
    hf_service = HFInferenceService()
    agent = ClasificacionAgent(db, hf_service)
    
    initial_state = {
        "tenant_id": current_user.tenant_id,
        "session_id": session_id,
        "transaccion_ids": request.transaccion_ids,
        "review_threshold": request.review_threshold,
    }
    
    result = await agent.run(initial_state)
    
    if result.get("status") == "review":
        _sessions[session_id] = result
    
    return {
        "session_id": session_id,
        "status": result.get("status"),
        "requires_human": result.get("requires_human", False),
        "clasificaciones": result.get("clasificaciones", []),
        "pendientes_revision": result.get("pendientes_revision", []),
        "results": result.get("results"),
    }


@router.post("/{session_id}/validar")
async def validar_clasificaciones(
    session_id: str,
    correcciones: dict[str, str],  # transaccion_id -> categoria_pgc
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Validar/corregir clasificaciones (human-in-the-loop)."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    state = _sessions[session_id]
    if state.get("tenant_id") != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    state["human_feedback"] = {
        "correcciones": correcciones,
        "validado_por": current_user.sub,
    }
    
    hf_service = HFInferenceService()
    agent = ClasificacionAgent(db, hf_service)
    result = await agent.run(state)
    
    if result.get("status") == "completed":
        del _sessions[session_id]
    
    return {
        "session_id": session_id,
        "status": result.get("status"),
        "results": result.get("results"),
    }


# === Reglas de clasificación ===

@router.get("/reglas", response_model=list[ReglaResponse])
async def list_reglas(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Listar reglas de clasificación del tenant."""
    stmt = (
        select(ReglaClasificacion)
        .where(ReglaClasificacion.tenant_id == UUID(current_user.tenant_id))
        .order_by(ReglaClasificacion.prioridad.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/reglas", response_model=ReglaResponse)
async def create_regla(
    data: ReglaCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Crear regla de clasificación."""
    regla = ReglaClasificacion(
        tenant_id=UUID(current_user.tenant_id),
        empresa_id=data.empresa_id,
        nombre=data.nombre,
        descripcion=data.descripcion,
        condicion=data.condicion,
        categoria_pgc=data.categoria_pgc,
        prioridad=data.prioridad,
    )
    db.add(regla)
    await db.commit()
    await db.refresh(regla)
    return regla


@router.delete("/reglas/{regla_id}")
async def delete_regla(
    regla_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Eliminar regla de clasificación."""
    stmt = select(ReglaClasificacion).where(
        ReglaClasificacion.id == regla_id,
        ReglaClasificacion.tenant_id == UUID(current_user.tenant_id),
    )
    result = await db.execute(stmt)
    regla = result.scalar_one_or_none()
    
    if not regla:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    
    await db.delete(regla)
    await db.commit()
    return {"message": "Regla eliminada"}
