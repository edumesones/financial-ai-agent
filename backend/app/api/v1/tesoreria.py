# backend/app/api/v1/tesoreria.py
"""Endpoints de análisis de tesorería."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user, TokenPayload
from app.services.hf_inference import HFInferenceService
from app.agents.tesoreria import TesoreriaAgent
from app.schemas.tesoreria import AnalisisTesoreriaResponse

router = APIRouter(prefix="/tesoreria", tags=["tesoreria"])


class TesoreriaRequest(BaseModel):
    empresa_id: str
    periodo_dias: int = 90


@router.post("/analisis")
async def analizar_tesoreria(
    request: TesoreriaRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ejecutar análisis completo de tesorería.
    
    Incluye:
    - Métricas actuales (saldo, burn rate, runway)
    - Patrones de gasto
    - Proyección de cash flow (30/60/90 días)
    - Alertas y recomendaciones
    """
    hf_service = HFInferenceService()
    agent = TesoreriaAgent(db, hf_service)
    
    initial_state = {
        "tenant_id": current_user.tenant_id,
        "empresa_id": request.empresa_id,
        "periodo_dias": request.periodo_dias,
    }
    
    result = await agent.run(initial_state)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "Error en análisis"))
    
    return result.get("results", {})


@router.get("/{empresa_id}/snapshot")
async def get_snapshot(
    empresa_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtener snapshot rápido de tesorería (últimos 30 días)."""
    hf_service = HFInferenceService()
    agent = TesoreriaAgent(db, hf_service)
    
    initial_state = {
        "tenant_id": current_user.tenant_id,
        "empresa_id": str(empresa_id),
        "periodo_dias": 30,
    }
    
    result = await agent.run(initial_state)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    results = result.get("results", {})
    return {
        "metricas": results.get("metricas", {}),
        "alertas": results.get("alertas", []),
    }


@router.get("/{empresa_id}/proyeccion")
async def get_proyeccion(
    empresa_id: UUID,
    dias: int = 90,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Obtener proyección de cash flow."""
    hf_service = HFInferenceService()
    agent = TesoreriaAgent(db, hf_service)
    
    initial_state = {
        "tenant_id": current_user.tenant_id,
        "empresa_id": str(empresa_id),
        "periodo_dias": dias,
    }
    
    result = await agent.run(initial_state)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    results = result.get("results", {})
    return {
        "proyeccion": results.get("proyeccion", {}),
        "recomendaciones": results.get("recomendaciones", []),
    }
