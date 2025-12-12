# backend/app/main.py
"""FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.config import get_settings
from app.core.database import engine
from app.core.logging import setup_logging
from app.api.v1 import (
    auth_router,
    empresas_router,
    extractos_router,
    conciliacion_router,
    clasificacion_router,
    tesoreria_router,
    debug_router,
    chat_router,
)

settings = get_settings()
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting Agente Financiero IA API", env=settings.app_env)
    yield
    await engine.dispose()
    logger.info("Shutting down API")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="Agente Financiero IA",
        description="API para automatización de análisis financiero en gestorías",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Routers
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(empresas_router, prefix="/api/v1")
    app.include_router(extractos_router, prefix="/api/v1")
    app.include_router(conciliacion_router, prefix="/api/v1")
    app.include_router(clasificacion_router, prefix="/api/v1")
    app.include_router(tesoreria_router, prefix="/api/v1")
    app.include_router(debug_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    
    # Health check
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "1.0.0"}
    
    @app.get("/")
    async def root():
        return {
            "name": "Agente Financiero IA",
            "version": "1.0.0",
            "docs": "/docs",
        }
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"},
        )
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
