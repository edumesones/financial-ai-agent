# backend/app/api/v1/__init__.py
"""API v1 routers."""

from .auth import router as auth_router
from .empresas import router as empresas_router
from .extractos import router as extractos_router
from .conciliacion import router as conciliacion_router
from .clasificacion import router as clasificacion_router
from .tesoreria import router as tesoreria_router
from .debug import router as debug_router
from .chat import router as chat_router

__all__ = [
    "auth_router",
    "empresas_router",
    "extractos_router",
    "conciliacion_router",
    "clasificacion_router",
    "tesoreria_router",
    "debug_router",
    "chat_router",
]
