# backend/app/models/clasificacion.py
"""Modelos Clasificacion, Conciliacion, ReglaClasificacion."""

from typing import TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import String, Numeric, JSON, ForeignKey, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from .transaccion import Transaccion


class Clasificacion(Base, UUIDMixin, TimestampMixin):
    """Clasificación de una transacción según PGC."""
    
    __tablename__ = "clasificacion"
    
    transaccion_id: Mapped[UUID] = mapped_column(
        ForeignKey("transaccion.id", ondelete="CASCADE"), unique=True, index=True
    )
    categoria_pgc: Mapped[str] = mapped_column(String(10))
    subcuenta: Mapped[str | None] = mapped_column(String(20))
    confianza: Mapped[Decimal] = mapped_column(Numeric(3, 2))
    metodo: Mapped[str] = mapped_column(String(20))  # regla, historico, ml, llm, manual
    explicacion: Mapped[str | None] = mapped_column(String(500))
    validado_por: Mapped[UUID | None] = mapped_column(ForeignKey("usuario.id"))
    validado_at: Mapped[datetime | None] = mapped_column(DateTime)
    
    # Relationships
    transaccion: Mapped["Transaccion"] = relationship(back_populates="clasificacion")


class Conciliacion(Base, UUIDMixin, TimestampMixin):
    """Conciliación de transacción bancaria con asiento contable."""
    
    __tablename__ = "conciliacion"
    
    transaccion_id: Mapped[UUID] = mapped_column(
        ForeignKey("transaccion.id", ondelete="CASCADE"), unique=True, index=True
    )
    asiento_id: Mapped[str | None] = mapped_column(String(100))  # Referencia externa
    confianza: Mapped[Decimal] = mapped_column(Numeric(3, 2))
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    match_type: Mapped[str] = mapped_column(String(20))  # exact, fuzzy, pattern, manual
    match_details: Mapped[dict | None] = mapped_column(JSON)
    validado_por: Mapped[UUID | None] = mapped_column(ForeignKey("usuario.id"))
    validado_at: Mapped[datetime | None] = mapped_column(DateTime)
    
    # Relationships
    transaccion: Mapped["Transaccion"] = relationship(back_populates="conciliacion")


class ReglaClasificacion(Base, UUIDMixin, TimestampMixin):
    """Regla personalizada de clasificación."""
    
    __tablename__ = "regla_clasificacion"
    
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), index=True
    )
    empresa_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("empresa.id", ondelete="CASCADE")
    )
    nombre: Mapped[str] = mapped_column(String(100))
    descripcion: Mapped[str | None] = mapped_column(String(500))
    condicion: Mapped[dict] = mapped_column(JSON)
    categoria_pgc: Mapped[str] = mapped_column(String(10))
    prioridad: Mapped[int] = mapped_column(Integer, default=0)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
