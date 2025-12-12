# backend/app/models/usuario.py
"""Modelo Usuario."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from .tenant import Tenant


class Usuario(Base, UUIDMixin, TimestampMixin):
    """Usuario del sistema (empleado de gestoría)."""
    
    __tablename__ = "usuario"
    
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    nombre: Mapped[str] = mapped_column(String(100))
    apellidos: Mapped[str | None] = mapped_column(String(200))
    rol: Mapped[str] = mapped_column(String(20), default="gestor")  # admin, gestor, viewer
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="usuarios")
