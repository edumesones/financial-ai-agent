# backend/app/models/transaccion.py
"""Modelo Transaccion con embedding vectorial."""

from typing import TYPE_CHECKING
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import String, Date, Numeric, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from .base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from .empresa import CuentaBancaria
    from .clasificacion import Clasificacion, Conciliacion


class Transaccion(Base, UUIDMixin, TimestampMixin):
    """Transacción bancaria."""
    
    __tablename__ = "transaccion"
    
    cuenta_id: Mapped[UUID] = mapped_column(
        ForeignKey("cuenta_bancaria.id", ondelete="CASCADE"), index=True
    )
    fecha: Mapped[date] = mapped_column(Date, index=True)
    fecha_valor: Mapped[date | None] = mapped_column(Date)
    importe: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    concepto: Mapped[str | None] = mapped_column(String(500))
    tipo: Mapped[str] = mapped_column(String(20))  # ingreso, gasto, transferencia
    referencia: Mapped[str | None] = mapped_column(String(100))
    hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    metadata_extra: Mapped[dict | None] = mapped_column(JSON, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)
    
    # Relationships
    cuenta: Mapped["CuentaBancaria"] = relationship(back_populates="transacciones")
    clasificacion: Mapped["Clasificacion | None"] = relationship(
        back_populates="transaccion", uselist=False
    )
    conciliacion: Mapped["Conciliacion | None"] = relationship(
        back_populates="transaccion", uselist=False
    )
    
    __table_args__ = (
        Index("idx_transaccion_cuenta_fecha", "cuenta_id", "fecha"),
    )
