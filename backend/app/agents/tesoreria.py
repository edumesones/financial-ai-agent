# backend/app/agents/tesoreria.py
"""Agente de análisis de tesorería y cash flow."""

from typing import TypedDict
from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict
from uuid import UUID

from langgraph.graph import StateGraph, END
from sqlalchemy import select

from .base import BaseAgent, AgentState
from app.models.transaccion import Transaccion
from app.models.empresa import CuentaBancaria


class TesoreriaState(AgentState):
    """Estado del agente de tesorería."""
    empresa_id: str
    periodo_dias: int
    transacciones: list[dict]
    metricas: dict
    patrones: dict
    proyeccion: dict
    alertas: list[str]
    recomendaciones: list[str]


class TesoreriaAgent(BaseAgent):
    """Agente de análisis financiero (sin human-in-the-loop)."""
    
    def build_graph(self) -> StateGraph:
        graph = StateGraph(TesoreriaState)
        
        graph.add_node("load_data", self.load_data)
        graph.add_node("calculate_metrics", self.calculate_metrics)
        graph.add_node("analyze_patterns", self.analyze_patterns)
        graph.add_node("project_cashflow", self.project_cashflow)
        graph.add_node("generate_alerts", self.generate_alerts)
        graph.add_node("compile_report", self.compile_report)
        
        graph.add_edge("load_data", "calculate_metrics")
        graph.add_edge("calculate_metrics", "analyze_patterns")
        graph.add_edge("analyze_patterns", "project_cashflow")
        graph.add_edge("project_cashflow", "generate_alerts")
        graph.add_edge("generate_alerts", "compile_report")
        graph.add_edge("compile_report", END)
        graph.set_entry_point("load_data")
        
        return graph
    
    async def load_data(self, state: TesoreriaState) -> dict:
        self.log_step("load_data", state)
        fecha_inicio = date.today() - timedelta(days=state.get("periodo_dias", 90))
        
        stmt = (
            select(Transaccion).join(CuentaBancaria)
            .where(CuentaBancaria.empresa_id == UUID(state["empresa_id"]), Transaccion.fecha >= fecha_inicio)
            .order_by(Transaccion.fecha)
        )
        result = await self.db.execute(stmt)
        transacciones = result.scalars().all()
        
        return {
            **state,
            "transacciones": [
                {"id": str(t.id), "fecha": t.fecha.isoformat(), "importe": float(t.importe),
                 "tipo": t.tipo, "concepto": t.concepto or "", "cuenta_id": str(t.cuenta_id)}
                for t in transacciones
            ],
            "status": "processing",
        }
    
    async def calculate_metrics(self, state: TesoreriaState) -> dict:
        self.log_step("calculate_metrics", state)
        transacciones = state.get("transacciones", [])
        
        ingresos = sum(t["importe"] for t in transacciones if t["importe"] > 0)
        gastos = abs(sum(t["importe"] for t in transacciones if t["importe"] < 0))
        
        saldos = defaultdict(float)
        for t in transacciones:
            saldos[t["cuenta_id"]] += t["importe"]
        saldo_total = sum(saldos.values())
        
        dias = state.get("periodo_dias", 90)
        meses = dias / 30
        burn_rate = gastos / meses if meses > 0 else 0
        runway = saldo_total / burn_rate if burn_rate > 0 else float('inf')
        
        metricas = {
            "saldo_total": round(saldo_total, 2),
            "saldos_por_cuenta": dict(saldos),
            "ingresos_periodo": round(ingresos, 2),
            "gastos_periodo": round(gastos, 2),
            "resultado_periodo": round(ingresos - gastos, 2),
            "burn_rate_mensual": round(burn_rate, 2),
            "runway_meses": round(runway, 1) if runway != float('inf') else None,
            "ratio_ingresos_gastos": round(ingresos / gastos, 2) if gastos > 0 else None,
        }
        return {**state, "metricas": metricas}
    
    async def analyze_patterns(self, state: TesoreriaState) -> dict:
        self.log_step("analyze_patterns", state)
        transacciones = state.get("transacciones", [])
        
        por_mes = defaultdict(lambda: {"ingresos": 0, "gastos": 0})
        for t in transacciones:
            mes = t["fecha"][:7]
            if t["importe"] > 0:
                por_mes[mes]["ingresos"] += t["importe"]
            else:
                por_mes[mes]["gastos"] += abs(t["importe"])
        
        gastos = [t for t in transacciones if t["importe"] < 0]
        importes_vistos = defaultdict(list)
        for g in gastos:
            importes_vistos[round(abs(g["importe"]), -1)].append(g)
        
        recurrentes = [
            {"importe_aprox": importe, "frecuencia": len(lista), "concepto_ejemplo": lista[0]["concepto"][:50]}
            for importe, lista in importes_vistos.items() if len(lista) >= 2
        ][:10]
        
        from collections import Counter
        dias = Counter(int(t["fecha"].split("-")[2]) for t in transacciones)
        peak_days = [{"dia": d, "movimientos": c} for d, c in dias.most_common(5)]
        
        patrones = {"evolucion_mensual": dict(por_mes), "gastos_recurrentes": recurrentes, "dias_pico": peak_days}
        return {**state, "patrones": patrones}
    
    async def project_cashflow(self, state: TesoreriaState) -> dict:
        self.log_step("project_cashflow", state)
        saldo_actual = state.get("metricas", {}).get("saldo_total", 0)
        burn_rate_diario = state.get("metricas", {}).get("burn_rate_mensual", 0) / 30
        
        def proyectar(dias: int) -> dict:
            return {
                "optimista": round(saldo_actual - (burn_rate_diario * 0.8 * dias), 2),
                "base": round(saldo_actual - (burn_rate_diario * dias), 2),
                "pesimista": round(saldo_actual - (burn_rate_diario * 1.2 * dias), 2),
            }
        
        proyeccion = {"30d": proyectar(30), "60d": proyectar(60), "90d": proyectar(90)}
        return {**state, "proyeccion": proyeccion}
    
    async def generate_alerts(self, state: TesoreriaState) -> dict:
        self.log_step("generate_alerts", state)
        alertas, recomendaciones = [], []
        metricas = state.get("metricas", {})
        proyeccion = state.get("proyeccion", {})
        
        if metricas.get("saldo_total", 0) < metricas.get("burn_rate_mensual", 0):
            alertas.append("⚠️ CRÍTICO: Saldo actual menor a un mes de gastos")
            recomendaciones.append("Revisar opciones de financiación urgente")
        
        if metricas.get("runway_meses") and metricas["runway_meses"] < 3:
            alertas.append(f"⚠️ Runway de solo {metricas['runway_meses']} meses")
            recomendaciones.append("Acelerar cobros pendientes")
        
        if metricas.get("ratio_ingresos_gastos") and metricas["ratio_ingresos_gastos"] < 1:
            alertas.append("📉 Gastos superiores a ingresos en el periodo")
            recomendaciones.append("Revisar estructura de costes")
        
        if proyeccion.get("60d", {}).get("base", 0) < 0:
            alertas.append("🔴 Proyección de saldo negativo en 60 días")
            recomendaciones.append("Negociar plazos de pago con proveedores")
        
        return {**state, "alertas": alertas, "recomendaciones": recomendaciones}
    
    async def compile_report(self, state: TesoreriaState) -> dict:
        self.log_step("compile_report", state)
        return {
            **state, "status": "completed", "requires_human": False,
            "results": {
                "metricas": state.get("metricas", {}),
                "patrones": state.get("patrones", {}),
                "proyeccion": state.get("proyeccion", {}),
                "alertas": state.get("alertas", []),
                "recomendaciones": state.get("recomendaciones", []),
            },
        }
