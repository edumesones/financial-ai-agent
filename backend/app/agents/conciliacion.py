# backend/app/agents/conciliacion.py
"""Agente especializado en conciliación bancaria."""

from typing import TypedDict
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from langgraph.graph import StateGraph, END
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseAgent, AgentState
from app.models.transaccion import Transaccion
from app.models.clasificacion import Conciliacion
from app.models.empresa import CuentaBancaria


class ConciliacionState(AgentState):
    """Estado del agente de conciliación."""
    empresa_id: str
    periodo_inicio: str
    periodo_fin: str
    transacciones: list[dict]
    asientos: list[dict]
    matches_exactos: list[dict]
    matches_fuzzy: list[dict]
    propuestas: list[dict]
    discrepancias: list[dict]
    auto_approve_threshold: float


class ConciliacionAgent(BaseAgent):
    """
    Agente de conciliación bancaria.
    
    Flujo:
    1. load_data -> exact_match -> fuzzy_match -> prepare_review
    2. [CHECKPOINT si hay propuestas para revisar]
    3. apply_decisions -> generate_summary -> END
    """
    
    def build_graph(self) -> StateGraph:
        graph = StateGraph(ConciliacionState)
        
        # Nodos
        graph.add_node("load_data", self.load_data)
        graph.add_node("exact_match", self.exact_match)
        graph.add_node("fuzzy_match", self.fuzzy_match)
        graph.add_node("prepare_review", self.prepare_review)
        graph.add_node("apply_decisions", self.apply_decisions)
        graph.add_node("generate_summary", self.generate_summary)
        
        # Edges
        graph.add_edge("load_data", "exact_match")
        graph.add_edge("exact_match", "fuzzy_match")
        graph.add_edge("fuzzy_match", "prepare_review")
        
        # Conditional: si hay propuestas para revisar, pausar
        graph.add_conditional_edges(
            "prepare_review",
            self._should_pause_for_review,
            {
                "pause": END,
                "continue": "apply_decisions",
            }
        )
        
        graph.add_edge("apply_decisions", "generate_summary")
        graph.add_edge("generate_summary", END)
        
        graph.set_entry_point("load_data")
        
        return graph
    
    def _should_pause_for_review(self, state: ConciliacionState) -> str:
        """Decidir si pausar para revisión humana."""
        threshold = state.get("auto_approve_threshold", 0.95)
        propuestas_pendientes = [
            p for p in state.get("propuestas", [])
            if p.get("confianza", 0) < threshold
        ]
        
        if propuestas_pendientes and not state.get("human_feedback"):
            return "pause"
        return "continue"
    
    async def load_data(self, state: ConciliacionState) -> dict:
        """Cargar transacciones del periodo."""
        self.log_step("load_data", state)
        
        empresa_id = state["empresa_id"]
        periodo_inicio = date.fromisoformat(state["periodo_inicio"])
        periodo_fin = date.fromisoformat(state["periodo_fin"])
        
        # Query transacciones
        stmt = (
            select(Transaccion)
            .join(CuentaBancaria)
            .where(
                CuentaBancaria.empresa_id == UUID(empresa_id),
                Transaccion.fecha >= periodo_inicio,
                Transaccion.fecha <= periodo_fin,
            )
            .order_by(Transaccion.fecha)
        )
        
        result = await self.db.execute(stmt)
        transacciones = result.scalars().all()
        
        return {
            **state,
            "transacciones": [
                {
                    "id": str(t.id),
                    "fecha": t.fecha.isoformat(),
                    "concepto": t.concepto or "",
                    "importe": float(t.importe),
                    "embedding": t.embedding,
                }
                for t in transacciones
            ],
            "matches_exactos": [],
            "matches_fuzzy": [],
            "propuestas": [],
            "discrepancias": [],
            "status": "processing",
        }
    
    async def exact_match(self, state: ConciliacionState) -> dict:
        """Buscar matches exactos entre transacciones y asientos."""
        self.log_step("exact_match", state)
        # TODO: Implementar matching exacto por fecha, importe y concepto
        return {**state, "matches_exactos": []}
    
    async def fuzzy_match(self, state: ConciliacionState) -> dict:
        """Buscar matches aproximados usando embeddings."""
        self.log_step("fuzzy_match", state)
        # TODO: Implementar fuzzy matching con embeddings y similitud
        return {**state, "matches_fuzzy": []}
    
    async def prepare_review(self, state: ConciliacionState) -> dict:
        """Preparar propuestas de conciliación para revisión."""
        self.log_step("prepare_review", state)
        
        threshold = state.get("auto_approve_threshold", 0.95)
        all_matches = state.get("matches_exactos", []) + state.get("matches_fuzzy", [])
        
        auto_approved = [
            {**m, "estado": "auto_aprobado"} 
            for m in all_matches 
            if m.get("confianza", 0) >= threshold
        ]
        needs_review = [
            {**m, "estado": "pendiente_revision"} 
            for m in all_matches 
            if m.get("confianza", 0) < threshold
        ]
        
        matched_tx_ids = {m["transaccion_id"] for m in all_matches}
        discrepancias = [
            {"transaccion_id": tx["id"], "tipo": "sin_match", "concepto": tx.get("concepto", "")}
            for tx in state.get("transacciones", []) 
            if tx["id"] not in matched_tx_ids
        ]
        
        return {
            **state, 
            "propuestas": auto_approved + needs_review,
            "discrepancias": discrepancias,
            "requires_human": len(needs_review) > 0,
            "status": "review" if needs_review else "processing",
        }
    
    async def apply_decisions(self, state: ConciliacionState) -> dict:
        self.log_step("apply_decisions", state)
        feedback = state.get("human_feedback") or {}
        aprobadas = set(feedback.get("aprobadas", []))
        rechazadas = set(feedback.get("rechazadas", []))
        
        for propuesta in state.get("propuestas", []):
            if propuesta["transaccion_id"] in aprobadas:
                propuesta["estado"] = "validado"
            elif propuesta["transaccion_id"] in rechazadas:
                propuesta["estado"] = "rechazado"
            elif propuesta["estado"] == "auto_aprobado":
                propuesta["estado"] = "validado"
        
        for propuesta in state.get("propuestas", []):
            if propuesta["estado"] == "validado":
                conciliacion = Conciliacion(
                    transaccion_id=propuesta["transaccion_id"],
                    asiento_id=propuesta.get("asiento_id"),
                    confianza=Decimal(str(propuesta["confianza"])),
                    estado="validado", match_type=propuesta["metodo"],
                    match_details={"razones": propuesta.get("razones", [])},
                )
                self.db.add(conciliacion)
        await self.db.commit()
        return {**state, "status": "completing"}
    
    async def generate_summary(self, state: ConciliacionState) -> dict:
        self.log_step("generate_summary", state)
        total = len(state.get("transacciones", []))
        conciliadas = len([p for p in state.get("propuestas", []) if p.get("estado") == "validado"])
        pendientes = len(state.get("discrepancias", []))
        
        return {
            **state, "status": "completed",
            "results": {
                "total_transacciones": total, "conciliadas": conciliadas,
                "pendientes": pendientes,
                "tasa_conciliacion": round(conciliadas / total * 100, 1) if total > 0 else 0,
                "propuestas": state.get("propuestas", []),
                "discrepancias": state.get("discrepancias", []),
            },
        }
