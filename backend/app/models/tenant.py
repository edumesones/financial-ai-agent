# backend/app/models/tenant.py
"""Modelo Tenant (gestoría)."""

from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from .usuario import Usuario
    from .empresa import Empresa


class Tenant(Base, UUIDMixin, TimestampMixin):
    """Representa una gestoría (cliente del SaaS)."""
    
    __tablename__ = "tenant"
    
    nombre: Mapped[str] = mapped_column(String(255))
    cif: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    telefono: Mapped[str | None] = mapped_column(String(20))
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    usuarios: Mapped[list["Usuario"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    empresas: Mapped[list["Empresa"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
