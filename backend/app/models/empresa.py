# backend/app/models/empresa.py
"""Modelos Empresa y CuentaBancaria."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from .tenant import Tenant
    from .transaccion import Transaccion


class Empresa(Base, UUIDMixin, TimestampMixin):
    """Empresa cliente de la gestoría."""
    
    __tablename__ = "empresa"
    
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), index=True
    )
    nombre: Mapped[str] = mapped_column(String(255))
    cif: Mapped[str | None] = mapped_column(String(20), index=True)
    sector: Mapped[str | None] = mapped_column(String(100))
    direccion: Mapped[str | None] = mapped_column(String(500))
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="empresas")
    cuentas: Mapped[list["CuentaBancaria"]] = relationship(
        back_populates="empresa", cascade="all, delete-orphan"
    )


class CuentaBancaria(Base, UUIDMixin, TimestampMixin):
    """Cuenta bancaria de una empresa."""
    
    __tablename__ = "cuenta_bancaria"
    
    empresa_id: Mapped[UUID] = mapped_column(
        ForeignKey("empresa.id", ondelete="CASCADE"), index=True
    )
    banco: Mapped[str | None] = mapped_column(String(100))
    iban: Mapped[str | None] = mapped_column(String(34), index=True)
    alias: Mapped[str | None] = mapped_column(String(100))
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    empresa: Mapped["Empresa"] = relationship(back_populates="cuentas")
    transacciones: Mapped[list["Transaccion"]] = relationship(
        back_populates="cuenta", cascade="all, delete-orphan"
    )
