# backend/app/agents/base.py
"""Clase base para todos los agentes usando LangGraph."""

from abc import ABC, abstractmethod
from typing import TypedDict, Any
from uuid import uuid4

import structlog
from langgraph.graph import StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.hf_inference import HFInferenceService

logger = structlog.get_logger()


class AgentState(TypedDict, total=False):
    """Estado base compartido por todos los agentes."""
    tenant_id: str
    session_id: str
    status: str  # loading, processing, review, completed, error
    messages: list[dict]
    results: dict
    requires_human: bool
    human_feedback: dict | None
    error: str | None


class BaseAgent(ABC):
    """
    Agente base con checkpointing y logging.
    
    Todos los agentes heredan de esta clase e implementan build_graph().
    """
    
    def __init__(self, db: AsyncSession, hf_service: HFInferenceService):
        self.db = db
        self.hf = hf_service
        self.agent_name = self.__class__.__name__
    
    @abstractmethod
    def build_graph(self) -> StateGraph:
        """Construir grafo de estados del agente."""
        pass
    
    async def run(self, initial_state: dict) -> dict:
        """Ejecutar agente hasta completion o checkpoint."""
        # Asegurar session_id
        if "session_id" not in initial_state:
            initial_state["session_id"] = str(uuid4())
        
        graph = self.build_graph()
        app = graph.compile()
        
        logger.info(
            "agent_started",
            agent=self.agent_name,
            session_id=initial_state.get("session_id"),
        )
        
        try:
            result = await app.ainvoke(initial_state)
            
            logger.info(
                "agent_completed",
                agent=self.agent_name,
                session_id=initial_state.get("session_id"),
                status=result.get("status"),
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "agent_error",
                agent=self.agent_name,
                session_id=initial_state.get("session_id"),
                error=str(e),
            )
            return {
                **initial_state,
                "status": "error",
                "error": str(e),
            }
    
    def log_step(self, step_name: str, state: dict, **extra: Any) -> None:
        """Log de cada paso del agente."""
        logger.info(
            "agent_step",
            agent=self.agent_name,
            step=step_name,
            session_id=state.get("session_id"),
            **extra,
        )
