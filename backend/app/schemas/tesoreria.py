# backend/app/schemas/tesoreria.py
"""Schemas de Tesorería."""

from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class MetricasTesoreria(BaseModel):
    """Métricas de tesorería."""
    saldo_total: Decimal
    ingresos_periodo: Decimal
    gastos_periodo: Decimal
    resultado_periodo: Decimal
    burn_rate_mensual: Decimal
    runway_meses: float | None
    ratio_ingresos_gastos: float | None


class SaldoCuenta(BaseModel):
    """Saldo por cuenta."""
    cuenta_id: str
    banco: str | None
    alias: str | None
    saldo: Decimal


class TesoreriaSnapshot(BaseModel):
    """Snapshot de tesorería actual."""
    empresa_id: str
    fecha: date
    metricas: MetricasTesoreria
    saldos_por_cuenta: list[SaldoCuenta]


class ProyeccionEscenario(BaseModel):
    """Proyección por escenario."""
    optimista: Decimal
    base: Decimal
    pesimista: Decimal


class TesoreriaProyeccion(BaseModel):
    """Proyección de cash flow."""
    empresa_id: str
    fecha_calculo: date
    proyeccion_30d: ProyeccionEscenario
    proyeccion_60d: ProyeccionEscenario
    proyeccion_90d: ProyeccionEscenario


class TesoreriaAlerta(BaseModel):
    """Alerta de tesorería."""
    tipo: str  # saldo_bajo, runway_corto, gasto_anomalo
    severidad: str  # info, warning, critical
    mensaje: str
    valor_actual: Decimal | None = None
    umbral: Decimal | None = None


class AnalisisTesoreriaResponse(BaseModel):
    """Respuesta completa de análisis de tesorería."""
    snapshot: TesoreriaSnapshot
    proyeccion: TesoreriaProyeccion
    alertas: list[TesoreriaAlerta]
    recomendaciones: list[str]
