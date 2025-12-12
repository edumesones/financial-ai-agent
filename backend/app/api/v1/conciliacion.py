# backend/app/api/v1/conciliacion.py
"""Endpoints de conciliación bancaria."""

from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user, TokenPayload
from app.services.hf_inference import HFInferenceService
from app.agents.conciliacion import ConciliacionAgent
from app.schemas.clasificacion import ConciliacionValidate

router = APIRouter(prefix="/conciliacion", tags=["conciliacion"])

# Store para sesiones activas (en producción usar Redis)
_sessions: dict[str, dict] = {}


class ConciliacionRequest(BaseModel):
    empresa_id: str
    periodo_inicio: str  # YYYY-MM-DD
    periodo_fin: str  # YYYY-MM-DD
    asientos: list[dict] = []  # Asientos contables para matching
    auto_approve_threshold: float = 0.95


@router.post("/iniciar")
async def iniciar_conciliacion(
    request: ConciliacionRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Iniciar proceso de conciliación."""
    session_id = str(uuid4())
    
    hf_service = HFInferenceService()
    agent = ConciliacionAgent(db, hf_service)
    
    initial_state = {
        "tenant_id": current_user.tenant_id,
        "session_id": session_id,
        "empresa_id": request.empresa_id,
        "periodo_inicio": request.periodo_inicio,
        "periodo_fin": request.periodo_fin,
        "asientos": request.asientos,
        "auto_approve_threshold": request.auto_approve_threshold,
    }
    
    result = await agent.run(initial_state)
    
    # Guardar estado si requiere revisión
    if result.get("status") == "review":
        _sessions[session_id] = result
    
    return {
        "session_id": session_id,
        "status": result.get("status"),
        "requires_human": result.get("requires_human", False),
        "propuestas": result.get("propuestas", []),
        "discrepancias": result.get("discrepancias", []),
        "results": result.get("results"),
    }


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    current_user: TokenPayload = Depends(get_current_user),
):
    """Obtener estado de sesión de conciliación."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    state = _sessions[session_id]
    if state.get("tenant_id") != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    return {
        "session_id": session_id,
        "status": state.get("status"),
        "propuestas": state.get("propuestas", []),
        "discrepancias": state.get("discrepancias", []),
    }


@router.post("/{session_id}/validar")
async def validar_propuestas(
    session_id: str,
    validacion: ConciliacionValidate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Validar propuestas de conciliación (human-in-the-loop)."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    state = _sessions[session_id]
    if state.get("tenant_id") != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Añadir feedback humano
    state["human_feedback"] = {
        "aprobadas": [str(p) for p in validacion.propuestas],
        "rechazadas": [str(r) for r in validacion.rechazadas],
        "validado_por": current_user.sub,
    }
    
    # Continuar agente
    hf_service = HFInferenceService()
    agent = ConciliacionAgent(db, hf_service)
    result = await agent.run(state)
    
    # Limpiar sesión si completada
    if result.get("status") == "completed":
        del _sessions[session_id]
    
    return {
        "session_id": session_id,
        "status": result.get("status"),
        "results": result.get("results"),
    }
