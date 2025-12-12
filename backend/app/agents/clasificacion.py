# backend/app/agents/clasificacion.py
"""Agente de clasificación de gastos/ingresos."""

from typing import TypedDict
from decimal import Decimal
from uuid import UUID

from langgraph.graph import StateGraph, END
from sqlalchemy import select

from .base import BaseAgent, AgentState
from app.models.transaccion import Transaccion
from app.models.clasificacion import Clasificacion, ReglaClasificacion


class ClasificacionState(AgentState):
    """Estado del agente de clasificación."""
    empresa_id: str
    transaccion_ids: list[str]
    transacciones: list[dict]
    reglas: list[dict]
    clasificaciones: list[dict]
    pendientes_revision: list[dict]
    review_threshold: float


class ClasificacionAgent(BaseAgent):
    """Agente de clasificación en cascada: reglas -> histórico -> LLM."""
    
    def build_graph(self) -> StateGraph:
        graph = StateGraph(ClasificacionState)
        
        graph.add_node("load_data", self.load_data)
        graph.add_node("apply_rules", self.apply_rules)
        graph.add_node("check_history", self.check_history)
        graph.add_node("llm_classify", self.llm_classify)
        graph.add_node("prepare_review", self.prepare_review)
        graph.add_node("save_results", self.save_results)
        
        graph.add_edge("load_data", "apply_rules")
        graph.add_edge("apply_rules", "check_history")
        graph.add_edge("check_history", "llm_classify")
        graph.add_edge("llm_classify", "prepare_review")
        graph.add_conditional_edges(
            "prepare_review",
            lambda s: "pause" if s.get("requires_human") and not s.get("human_feedback") else "continue",
            {"pause": END, "continue": "save_results"}
        )
        graph.add_edge("save_results", END)
        graph.set_entry_point("load_data")
        
        return graph
    
    async def load_data(self, state: ClasificacionState) -> dict:
        self.log_step("load_data", state)
        
        tx_ids = [UUID(tid) for tid in state.get("transaccion_ids", [])]
        if not tx_ids:
            return {**state, "transacciones": [], "reglas": [], "clasificaciones": [], "status": "processing"}
        
        stmt = select(Transaccion).where(Transaccion.id.in_(tx_ids))
        result = await self.db.execute(stmt)
        transacciones = result.scalars().all()
        
        stmt_reglas = (
            select(ReglaClasificacion)
            .where(ReglaClasificacion.tenant_id == UUID(state["tenant_id"]), ReglaClasificacion.activa == True)
            .order_by(ReglaClasificacion.prioridad.desc())
        )
        result_reglas = await self.db.execute(stmt_reglas)
        reglas = result_reglas.scalars().all()
        
        return {
            **state,
            "transacciones": [
                {"id": str(t.id), "concepto": t.concepto or "", "importe": float(t.importe)}
                for t in transacciones
            ],
            "reglas": [
                {"id": str(r.id), "condicion": r.condicion, "categoria_pgc": r.categoria_pgc}
                for r in reglas
            ],
            "clasificaciones": [], "status": "processing",
        }
    
    async def apply_rules(self, state: ClasificacionState) -> dict:
        self.log_step("apply_rules", state)
        clasificaciones, clasificadas_ids = [], set()
        
        for tx in state.get("transacciones", []):
            for regla in state.get("reglas", []):
                if self._match_rule(tx, regla["condicion"]):
                    clasificaciones.append({
                        "transaccion_id": tx["id"], "categoria_pgc": regla["categoria_pgc"],
                        "confianza": 0.99, "metodo": "regla", "explicacion": f"Regla: {regla['id']}"
                    })
                    clasificadas_ids.add(tx["id"])
                    break
        
        pendientes = [t for t in state.get("transacciones", []) if t["id"] not in clasificadas_ids]
        return {**state, "clasificaciones": clasificaciones, "transacciones": pendientes}
    
    def _match_rule(self, tx: dict, condicion: dict) -> bool:
        campo = condicion.get("campo", "concepto")
        operador = condicion.get("operador", "contains")
        valor = condicion.get("valor", "").lower()
        tx_valor = str(tx.get(campo, "")).lower()
        
        if operador == "contains":
            return valor in tx_valor
        elif operador == "equals":
            return valor == tx_valor
        elif operador == "startswith":
            return tx_valor.startswith(valor)
        return False
    
    async def check_history(self, state: ClasificacionState) -> dict:
        self.log_step("check_history", state)
        clasificaciones = state.get("clasificaciones", []).copy()
        clasificadas_ids = {c["transaccion_id"] for c in clasificaciones}
        pendientes = []
        
        for tx in state.get("transacciones", []):
            if tx["id"] in clasificadas_ids:
                continue
            
            stmt = (
                select(Clasificacion).join(Transaccion)
                .where(Transaccion.concepto.ilike(f"%{tx['concepto'][:20]}%"), Clasificacion.validado_por.isnot(None))
                .limit(5)
            )
            result = await self.db.execute(stmt)
            historico = result.scalars().all()
            
            if historico:
                categorias = [h.categoria_pgc for h in historico]
                categoria_comun = max(set(categorias), key=categorias.count)
                frecuencia = categorias.count(categoria_comun) / len(categorias)
                clasificaciones.append({
                    "transaccion_id": tx["id"], "categoria_pgc": categoria_comun,
                    "confianza": round(0.85 * frecuencia, 2), "metodo": "historico",
                    "explicacion": f"Basado en {len(historico)} clasificaciones similares"
                })
                clasificadas_ids.add(tx["id"])
            else:
                pendientes.append(tx)
        
        return {**state, "clasificaciones": clasificaciones, "transacciones": pendientes}
    
    async def llm_classify(self, state: ClasificacionState) -> dict:
        self.log_step("llm_classify", state, pending=len(state.get("transacciones", [])))
        clasificaciones = state.get("clasificaciones", []).copy()
        
        for tx in state.get("transacciones", []):
            result = await self.hf.classify_transaction(concepto=tx["concepto"], importe=tx["importe"])
            clasificaciones.append({
                "transaccion_id": tx["id"], "categoria_pgc": result["categoria_pgc"],
                "confianza": result["confianza"], "metodo": "llm", "explicacion": result.get("explicacion", "")
            })
        
        return {**state, "clasificaciones": clasificaciones, "transacciones": []}
    
    async def prepare_review(self, state: ClasificacionState) -> dict:
        self.log_step("prepare_review", state)
        threshold = state.get("review_threshold", 0.75)
        pendientes = [c for c in state.get("clasificaciones", []) if c["confianza"] < threshold]
        
        return {
            **state, "pendientes_revision": pendientes,
            "requires_human": len(pendientes) > 0,
            "status": "review" if pendientes else "completing",
        }
    
    async def save_results(self, state: ClasificacionState) -> dict:
        self.log_step("save_results", state)
        feedback = state.get("human_feedback") or {}
        correcciones = feedback.get("correcciones", {})
        
        for clasif in state.get("clasificaciones", []):
            if clasif["transaccion_id"] in correcciones:
                clasif["categoria_pgc"] = correcciones[clasif["transaccion_id"]]
                clasif["metodo"] = "manual"
                clasif["confianza"] = 1.0
            
            clasificacion = Clasificacion(
                transaccion_id=clasif["transaccion_id"],
                categoria_pgc=clasif["categoria_pgc"],
                confianza=Decimal(str(clasif["confianza"])),
                metodo=clasif["metodo"],
                explicacion=clasif.get("explicacion"),
            )
            self.db.add(clasificacion)
        
        await self.db.commit()
        return {
            **state, "status": "completed",
            "results": {"total": len(state.get("clasificaciones", [])), "clasificaciones": state.get("clasificaciones", [])},
        }
