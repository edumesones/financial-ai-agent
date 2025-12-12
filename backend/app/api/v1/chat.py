# backend/app/api/v1/chat.py
"""Endpoint de chat con IA."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, TokenPayload
from app.services.chat_orchestrator import ChatOrchestrator

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    message: str
    empresa_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    tool_used: str
    data: Optional[dict] = None
    needs_input: bool = False


@router.post("/", response_model=ChatResponse)
async def chat(
    msg: ChatMessage,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Enviar mensaje al asistente IA.
    
    El asistente puede:
    - Analizar tesorería
    - Clasificar transacciones
    - Listar empresas
    - Responder preguntas generales
    
    Ejemplos:
    - "¿Cómo está la tesorería de Construcciones Martínez?"
    - "Lista las empresas"
    - "Clasifica las transacciones pendientes"
    """
    orchestrator = ChatOrchestrator(db, current_user.tenant_id)
    
    context = {}
    if msg.empresa_id:
        context["empresa_id"] = msg.empresa_id
    
    result = await orchestrator.process_message(msg.message, context)
    
    return ChatResponse(
        response=result.get("response", ""),
        tool_used=result.get("tool_used", "unknown"),
        data=result.get("data"),
        needs_input=result.get("needs_input", False),
    )


@router.get("/capabilities")
async def get_capabilities():
    """Lista las capacidades del chat."""
    return {
        "capabilities": [
            {
                "name": "Análisis de Tesorería",
                "description": "Analiza cash flow, métricas, proyecciones y alertas",
                "example": "¿Cómo está la tesorería de [empresa]?"
            },
            {
                "name": "Clasificación de Transacciones", 
                "description": "Clasifica gastos/ingresos según PGC",
                "example": "Clasifica las transacciones pendientes"
            },
            {
                "name": "Información de Empresas",
                "description": "Muestra detalles de empresas",
                "example": "Dame información de [empresa]"
            },
            {
                "name": "Listado de Empresas",
                "description": "Lista todas las empresas disponibles",
                "example": "¿Qué empresas tengo?"
            }
        ],
        "tips": [
            "Puedes mencionar empresas por nombre",
            "Si seleccionas una empresa, las consultas se aplicarán a ella",
            "Pregunta en lenguaje natural"
        ]
    }
